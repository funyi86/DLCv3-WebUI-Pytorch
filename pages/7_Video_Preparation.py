import os
import sys

# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import streamlit as st
import datetime
from src.core.config import get_root_path, get_data_path, require_authentication
from src.core.helpers.video_combiner import create_video_combination_script
from src.core.utils.execute_selected_scripts import execute_selected_scripts, fetch_last_lines_of_logs
from src.core.utils.file_utils import list_directories, upload_files, select_video_files
from src.ui.components import render_sidebar, load_custom_css

# 设置页面配置
st.set_page_config(
    page_title="Video Preparation",
    page_icon="📽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加载样式和侧边栏
load_custom_css()
require_authentication()
render_sidebar()

# 页面标题和说明
st.title("📽️ 视频预处理 / Video Preparation")

with st.expander("💡 使用说明 / Instructions", expanded=True):
    st.markdown("""
    #### 视频要求 / Video Requirements:
    - 输入格式：MP4 / Input Format: MP4
    - 输出格式：MP4 / Output Format: MP4
    - 请确保所有视频片段分辨率和帧率一致 / Please ensure all video segments have the same resolution and frame rate
    """)

# 设置路径和时间
root_directory = os.path.join(get_data_path(), 'video_preparation')
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
web_log_file_path = os.path.join(get_root_path(), 'logs', 'usage.txt')

# 创建工作目录
if not os.path.exists(root_directory):
    os.makedirs(root_directory)

# 列出或创建工作目录
directories = list_directories(root_directory)
if directories:
    selected_directory = st.selectbox("选择工作目录 / Choose Directory", directories)
    folder_path = os.path.join(root_directory, selected_directory)
else:
    folder_name = datetime.datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(root_directory, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    st.info(f"已创建新工作目录 / Created new directory: {folder_name}")

st.write(f"当前工作目录 / Current working directory: {folder_path}")

# 上传视频文件
uploaded_files = upload_files(folder_path)

# 选择要合并的视频文件
video_files = select_video_files(folder_path)
if video_files:
    st.write("已选择的视频文件 / Selected video files:", video_files)
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 生成合并脚本 / Generate Combination Script", use_container_width=True):
            try:
                # 记录操作日志
                user_name = st.session_state.get('name', 'unknown_user')
                with open(web_log_file_path, "a", encoding='utf-8') as web_log_file:
                    web_log_file.write(f"\n{user_name}, {current_time}, Generate Video Combination Script\n")
                
                with st.spinner("生成脚本中 / Generating script..."):
                    # 获取第一个和最后一个视频文件的名称（不包含扩展名）
                    first_video = os.path.splitext(os.path.basename(video_files[0]))[0]
                    last_video = os.path.splitext(os.path.basename(video_files[-1]))[0]
                    combined_video_name = f"{first_video}_to_{last_video}_combined.mp4"
                    st.session_state["combined_video_name"] = combined_video_name
                    
                    # 创建合并视频的脚本
                    script_path = create_video_combination_script(
                        folder_path=folder_path,
                        selected_files=video_files,
                        output_directory=folder_path,
                        output_filename=combined_video_name
                    )
                    
                    if script_path:
                        st.success(f"✅ 脚本已生成 / Script generated: {os.path.basename(script_path)}")
                    else:
                        st.error("❌ 创建合并脚本失败 / Failed to create combination script")
                
            except Exception as e:
                st.error(f"❌ 生成脚本失败 / Failed to generate script: {str(e)}")
    
    with col2:
        # 选择要执行的脚本
        script_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
        if script_files:
            selected_scripts = st.multiselect(
                "选择要执行的脚本 / Select scripts to execute",
                script_files,
                help="选择需要执行的合并脚本 / Select combination scripts to execute"
            )
            
            if selected_scripts and st.button("🚀 执行选定脚本 / Execute Selected Scripts", use_container_width=True):
                try:
                    with st.spinner("执行脚本中 / Executing scripts..."):
                        # 执行合并脚本
                        execute_selected_scripts(folder_path, selected_scripts, folder_path)
                        
                        # 创建目标目录（视频裁剪目录下的同名文件夹）
                        target_directory = os.path.join(get_data_path(), 'video_crop', os.path.basename(folder_path))
                        if not os.path.exists(target_directory):
                            os.makedirs(target_directory)
                        
                        # 移动合并后的视频到目标目录
                        if "combine_videos.py" in selected_scripts:
                            combined_video_name = st.session_state.get("combined_video_name")
                            if not combined_video_name and video_files:
                                first_video = os.path.splitext(os.path.basename(video_files[0]))[0]
                                last_video = os.path.splitext(os.path.basename(video_files[-1]))[0]
                                combined_video_name = f"{first_video}_to_{last_video}_combined.mp4"
                            if combined_video_name:
                                combined_video_path = os.path.join(folder_path, combined_video_name)
                                if os.path.exists(combined_video_path):
                                    import shutil
                                    shutil.move(combined_video_path, os.path.join(target_directory, combined_video_name))
                                    st.success(f"✅ 视频已合并并移动到裁剪目录 / Video combined and moved to crop directory: {combined_video_name}")
                                else:
                                    st.error(f"❌ 合并后的视频文件未找到 / Combined video file not found: {combined_video_name}")
                            else:
                                st.error("❌ 未找到合并视频名称 / Combined video name not found")
                        
                except Exception as e:
                    st.error(f"❌ 执行脚本失败 / Failed to execute scripts: {str(e)}")
        else:
            st.info("📝 请先生成合并脚本 / Please generate combination script first")
            
    # 显示日志
    st.subheader("📋 处理日志 / Processing Logs")
    if st.button("🔄 刷新日志 / Refresh Logs"):
        log_entries = fetch_last_lines_of_logs(folder_path)
        if log_entries:
            for log_file, log_content in log_entries.items():
                with st.expander(f"日志文件 / Log file: {log_file}", expanded=True):
                    st.code(log_content)
else:
    st.warning("⚠️ 请先选择要合并的视频文件 / Please select video files to combine first") 
