import os
import sys

# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import streamlit as st
import datetime
import cv2
import numpy as np
from pathlib import Path
import subprocess
import tempfile
import shutil
import time
import json
import glob
from typing import List, Tuple, Dict, Any, Optional
from src.core.config import get_root_path, get_data_path, require_authentication
from src.core.helpers.video_helper import (
    crop_video_files,
    get_video_info,
    preview_original_frame,
    preview_cropped_frames,
    create_extract_script,
    create_extract_script_CPU,
    move_selected_files
)
from src.core.helpers.download_utils import filter_and_zip_files
from src.ui.components import render_sidebar, load_custom_css, setup_working_directory
from src.core.gpu.gpu_utils import display_gpu_usage
from src.core.gpu.gpu_selector import setup_gpu_selection
from src.core.utils.execute_selected_scripts import execute_selected_scripts, fetch_last_lines_of_logs

# 设置页面配置
st.set_page_config(
    page_title="Video Crop",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加载样式和侧边栏
load_custom_css()
require_authentication()
render_sidebar()

# 页面标题和说明
st.title("✂️ 视频裁剪 / Video Crop")

with st.expander("💡 使用说明 / Instructions", expanded=True):
    st.markdown("""
    #### 视频要求 / Video Requirements:
    - 输入格式：MP4 / Input Format: MP4
    - 输出格式：MP4 / Output Format: MP4
    - 默认保持原始分辨率和帧率 / Default: Keep original resolution and frame rate
    - 支持自定义输出参数 / Support custom output parameters
    
    #### 使用步骤 / Steps:
    1. 选择工作目录和视频文件 / Select working directory and video files
    2. 设置裁剪参数 / Set crop parameters
    3. 预览视频帧 / Preview video frames
    4. 开始裁剪 / Start cropping
    """)

# 设置路径和时间
root_directory = os.path.join(get_data_path(), 'video_crop')
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
web_log_file_path = os.path.join(get_root_path(), 'logs', 'usage.txt')


def get_invalid_crop_files(files, x_coord, y_coord, crop_width, crop_height):
    invalid = []
    for video_path in files:
        info = get_video_info(video_path)
        if not info:
            invalid.append(os.path.basename(video_path))
            continue
        if (
            x_coord < 0
            or y_coord < 0
            or x_coord + crop_width > info["width"]
            or y_coord + crop_height > info["height"]
        ):
            invalid.append(f"{os.path.basename(video_path)} ({info['width']}x{info['height']})")
    return invalid

# 显示GPU状态和配置
col1, col2 = st.columns(2)
with col1:
    st.subheader("🖥️ GPU 状态 / GPU Status")
    high_memory_usage = display_gpu_usage()
with col2:
    st.subheader("⚙️ GPU 配置 / GPU Configuration")
    gpu_count, selected_gpus = setup_gpu_selection()
    if selected_gpus:
        st.success(f"可用GPU数量 / Available GPUs: {gpu_count}")
        st.info(f"已选择的GPU / Selected GPUs: {selected_gpus}")

# 设置工作目录
folder_path, selected_files = setup_working_directory(root_directory)

# 视频裁剪功能
if folder_path and selected_files:
    # 显示选中视频的信息
    st.subheader("📹 视频信息 / Video Information")
    for video_path in selected_files:
        video_info = get_video_info(video_path)
        if video_info:
            st.info(f"""
            {os.path.basename(video_path)}:
            - 分辨率 / Resolution: {video_info['width']}x{video_info['height']}
            - 帧率 / FPS: {video_info['fps']}
            - 总时长 / Total Duration: {video_info['duration_str']}
            """)
    
    st.subheader("⚙️ 裁剪参数和预览 / Crop Parameters and Preview")
    
    # 创建两列布局
    param_col, preview_col = st.columns([3, 2])
    
    with param_col:
        # 基本参数
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            x = st.number_input("X坐标 / X Coordinate", min_value=0, value=0)
        with col2:
            y = st.number_input("Y坐标 / Y Coordinate", min_value=0, value=0)
        with col3:
            width = st.number_input("宽度 / Width", min_value=1, value=500)
        with col4:
            height = st.number_input("高度 / Height", min_value=1, value=500)

        # 时间参数
        col5, col6 = st.columns(2)
        with col5:
            start_time = st.number_input("开始时间（分钟） / Start Time (minutes)", min_value=0.0, value=0.0)
        with col6:
            end_time = st.number_input("结束时间（分钟） / End Time (minutes)", min_value=0.1, value=1.0)
    
    with preview_col:
        if selected_files:
            # 显示原始帧预览（带裁剪框）
            original_frame = preview_original_frame(
                video_path=selected_files[0],
                x=x, y=y,
                width=width,
                height=height
            )
            if original_frame is not None:
                st.image(original_frame, caption="原始帧（绿框表示裁剪区域）/ Original Frame (green box shows crop area)", use_container_width=True)

    # 裁剪预览标题
    st.subheader("👁️ 裁剪预览 / Crop Preview")
    if selected_files:
        for video_path in selected_files:
            st.write(f"视频文件 / Video file: {os.path.basename(video_path)}")
            preview_cropped_frames(
                video_path=video_path,
                x=x, y=y,
                width=width,
                height=height
            )

    # 裁剪控制
    st.subheader("✂️ 裁剪控制 / Crop Control")
    
    # GPU裁剪
    st.markdown("#### 🖥️ GPU裁剪 / GPU Cropping")
    col7, col8 = st.columns(2)
    with col7:
        if st.button("📝 生成GPU裁剪脚本 / Generate GPU Crop Scripts", use_container_width=True):
            if not selected_gpus:
                st.error("未选择GPU / No GPU selected")
            else:
                if end_time <= start_time:
                    st.error("结束时间必须大于开始时间 / End time must be greater than start time")
                else:
                    invalid_files = get_invalid_crop_files(selected_files, x, y, width, height)
                    if invalid_files:
                        st.error(
                            "裁剪区域超出视频尺寸 / Crop area exceeds frame size: "
                            + ", ".join(invalid_files)
                        )
                    else:
                        try:
                            # 检查session_state中是否存在name
                            user_name = st.session_state.get('name', 'unknown_user')
                            
                            with open(web_log_file_path, "a", encoding='utf-8') as web_log_file:
                                web_log_file.write(f"\n{user_name}, {current_time}, Generate GPU Crop Scripts\n")
                            
                            with st.spinner("生成脚本中 / Generating scripts..."):
                                for video_path in selected_files:
                                    # 创建裁剪脚本
                                    script_path = create_extract_script(
                                        video_path=video_path,
                                        x=x, y=y,
                                        width=width,
                                        height=height,
                                        start=start_time,
                                        end=end_time,
                                        output_directory=folder_path,
                                        deviceID=selected_gpus[0]
                                    )
                                    if script_path:
                                        st.success(f"✅ 脚本已生成 / Script generated: {os.path.basename(script_path)}")
                            st.success("✅ 所有裁剪脚本生成完成 / All crop scripts generated")
                        except Exception as e:
                            st.error(f"❌ 生成脚本失败 / Failed to generate scripts: {str(e)}")
    
    with col8:
        # 选择要执行的脚本
        script_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
        if script_files:
            selected_scripts = st.multiselect(
                "选择要执行的脚本 / Select scripts to execute",
                script_files,
                help="选择需要执行的裁剪脚本 / Select crop scripts to execute"
            )
            
            if selected_scripts and st.button("🚀 执行选定脚本 / Execute Selected Scripts", use_container_width=True):
                try:
                    with st.spinner("执行脚本中 / Executing scripts..."):
                        execute_selected_scripts(folder_path, selected_scripts, folder_path)
                    st.success("✅ 所有选定脚本执行完成 / All selected scripts executed")
                except Exception as e:
                    st.error(f"❌ 执行脚本失败 / Failed to execute scripts: {str(e)}")
        else:
            st.info("📝 请先生成裁剪脚本 / Please generate crop scripts first")
    
    # CPU裁剪
    st.markdown("#### 💻 CPU裁剪 / CPU Cropping")
    col9, col10 = st.columns(2)
    with col9:
        if st.button("📝 生成CPU裁剪脚本 / Generate CPU Crop Scripts", use_container_width=True):
            if end_time <= start_time:
                st.error("结束时间必须大于开始时间 / End time must be greater than start time")
            else:
                invalid_files = get_invalid_crop_files(selected_files, x, y, width, height)
                if invalid_files:
                    st.error(
                        "裁剪区域超出视频尺寸 / Crop area exceeds frame size: "
                        + ", ".join(invalid_files)
                    )
                else:
                    try:
                        # 检查session_state中是否存在name
                        user_name = st.session_state.get('name', 'unknown_user')
                        
                        with open(web_log_file_path, "a", encoding='utf-8') as web_log_file:
                            web_log_file.write(f"\n{user_name}, {current_time}, Generate CPU Crop Scripts\n")
                        
                        with st.spinner("生成脚本中 / Generating scripts..."):
                            for video_path in selected_files:
                                # 创建裁剪脚本
                                script_path = create_extract_script_CPU(
                                    video_path=video_path,
                                    x=x, y=y,
                                    width=width,
                                    height=height,
                                    start=start_time,
                                    end=end_time,
                                    output_directory=folder_path
                                )
                                if script_path:
                                    st.success(f"✅ 脚本已生成 / Script generated: {os.path.basename(script_path)}")
                        st.success("✅ 所有裁剪脚本生成完成 / All crop scripts generated")
                    except Exception as e:
                        st.error(f"❌ 生成脚本失败 / Failed to generate scripts: {str(e)}")
    
    with col10:
        # 选择要执行的脚本
        script_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
        if script_files:
            selected_cpu_scripts = st.multiselect(
                "选择要执行的CPU脚本 / Select CPU scripts to execute",
                script_files,
                help="选择需要执行的CPU裁剪脚本 / Select CPU crop scripts to execute",
                key="cpu_scripts"  # 添加唯一的key以区分GPU脚本选择
            )
            
            if selected_cpu_scripts and st.button("🚀 执行选定CPU脚本 / Execute Selected CPU Scripts", use_container_width=True):
                try:
                    with st.spinner("执行脚本中 / Executing scripts..."):
                        execute_selected_scripts(folder_path, selected_cpu_scripts, folder_path)
                    st.success("✅ 所有选定脚本执行完成 / All selected scripts executed")
                except Exception as e:
                    st.error(f"❌ 执行脚本失败 / Failed to execute scripts: {str(e)}")
        else:
            st.info("📝 请先生成裁剪脚本 / Please generate crop scripts first")

    # 日志显示
    st.subheader("📋 操作日志 / Operation Logs")
    if st.button("🔄 刷新日志 / Refresh Logs"):
        last_log_entries = fetch_last_lines_of_logs(folder_path)
        for log_file, log_entry in last_log_entries.items():
            with st.expander(f"日志文件 / Log File: {log_file}", expanded=True):
                st.code(log_entry)
else:
    st.warning("⚠️ 请选择要裁剪的视频文件 / Please select video files to crop")

# 文件移动功能
st.subheader("📦 文件移动 / File Movement")
if folder_path:  # 只要有工作目录就显示文件移动功能
    video_files = [f for f in os.listdir(folder_path) if '_' in f and f.lower().endswith('.mp4')]
    selected_move_files = st.multiselect('选择要移动的视频文件 / Select video files to move:', video_files)

    if selected_move_files:
        st.write("移动文件到 / Move files to:")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            if st.button("🐭 抓挠 / Scratch"):
                dest_path = os.path.join(get_data_path(), 'mouse_scratch', os.path.basename(folder_path))
                move_selected_files(dest_path, selected_move_files, folder_path)
        with col2:
            if st.button("🐭 理毛 / Grooming"):
                dest_path = os.path.join(get_data_path(), 'mouse_grooming', os.path.basename(folder_path))
                move_selected_files(dest_path, selected_move_files, folder_path)
        with col3:
            if st.button("🏠 三箱 / Three Chamber"):
                dest_path = os.path.join(get_data_path(), 'three_chamber', os.path.basename(folder_path))
                move_selected_files(dest_path, selected_move_files, folder_path)
        with col4:
            if st.button("👥 社交 / Two Social"):
                dest_path = os.path.join(get_data_path(), 'two_social', os.path.basename(folder_path))
                move_selected_files(dest_path, selected_move_files, folder_path)
        with col5:
            if st.button("📍 位置偏好 / CPP"):
                dest_path = os.path.join(get_data_path(), 'mouse_cpp', os.path.basename(folder_path))
                move_selected_files(dest_path, selected_move_files, folder_path)
        with col6:
            if st.button("🐭 游泳 / Swimming"):
                dest_path = os.path.join(get_data_path(), 'mouse_swimming', os.path.basename(folder_path))
                move_selected_files(dest_path, selected_move_files, folder_path)
else:
    st.info("⚠️ 请先选择工作目录 / Please select a working directory first") 
