import streamlit as st
import os
import datetime
from src.core.config import get_root_path, get_data_path, get_models_path, require_authentication
from src.core.helpers.analysis_helper import create_and_start_analysis, fetch_last_lines_of_logs
from src.core.helpers.download_utils import filter_and_zip_files
from src.core.processing.mouse_catch_video_processing import process_mouse_catch_video
from src.core.processing.trajectory_processing import (
    filter_low_likelihood,
    filter_extreme_jumps,
    filter_unreasonable_speed,
    filter_unreasonable_position,
    interpolate_missing_points,
    smooth_trajectory,
    detect_grab_trajectories,
    plot_trajectory_with_events,
    format_timestamp
)
import pandas as pd

# 初始化 session state
if 'name' not in st.session_state:
    st.session_state.name = "Anonymous User"

# 导入共享组件
from src.ui.components import render_sidebar, load_custom_css, show_gpu_status, setup_working_directory

# 设置页面配置
st.set_page_config(
    page_title="Mouse Catch",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置文件上传大小限制为40GB
st.markdown("""
    <style>
        [data-testid="stFileUploader"] {
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)
import streamlit.config as config
config.set_option('server.maxUploadSize', 40960)  # 设置为40GB (40 * 1024 MB)

# 加载样式和侧边栏
load_custom_css()
require_authentication()
render_sidebar()

# 页面标题和说明
st.title("🎯 小鼠抓取行为分析 / Mouse Catch Analysis")

with st.expander("💡 使用说明 / Instructions", expanded=False):
    st.markdown("""
    #### 视频要求 / Video Requirements:
    - 格式：MP4 / Format: MP4
    - 分辨率：500x500像素 / Resolution: 500x500 pixels
    - 帧率：120帧/秒 / Frame Rate: 120 fps
    - 视角：侧面视角，确保可以清晰观察到小鼠的抓取动作 / View: Side view, ensure clear observation of mouse catching behavior
    
    #### 分析参数说明 / Analysis Parameters:
    - 置信度阈值：0.6（可调整）/ Confidence threshold: 0.6 (adjustable)
    - 位置过滤：
        - X坐标范围：199-450像素 / X coordinate range: 199-450 pixels
        - Y坐标范围：220-450像素 / Y coordinate range: 220-450 pixels
    - 抓取检测区域：
        - 挡板右侧区域：(330-450, 250-400) / Barrier region: (330-450, 250-400)
        - 起点区域：(200-300, 350-450) / Start region: (200-300, 350-450)
    - 时间窗口：
        - 向前回溯：0.5秒 / Backward search: 0.5s
        - 向后搜索：0.2秒 / Forward search: 0.2s
        - 最小间隔：0.5秒 / Minimum interval: 0.5s
    
    #### 分析结果 / Analysis Results:
    - 抓取轨迹图：显示所有检测到的抓取轨迹 / Catch trajectories: Shows all detected catch events
    - 速度分析：显示速度分布和时序变化 / Velocity analysis: Shows speed distribution and temporal changes
    - 高度分析：显示抓取高度分布 / Height analysis: Shows lift height distribution
    - 数据文件：
        - catch_analysis_results.csv：包含所有抓取事件的详细参数
        - trajectories/*.csv：每个抓取事件的完整轨迹数据
    """)

# 设置路径和时间
root_directory = os.path.join(get_data_path(), 'mouse_catch')
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
web_log_file_path = os.path.join(get_root_path(), 'logs', 'usage.txt')

# 设置工作目录
folder_path, selected_files = setup_working_directory(root_directory)

# 设置模型
models = {
    "抓取行为分析V1 / Catch-V1": os.path.join(get_models_path(), "ZhangLab-mouse-C57-catch-V1-2025-02-21/config.yaml"),
    "抓取行为分析V2 / Catch-V2": os.path.join(get_models_path(), "ZhangLab-mouse-C57-catch-V2-2025-02-22/config.yaml"),
    "抓取行为分析V3 / Catch-V3": os.path.join(get_models_path(), "ZhangLab-mouse-C57-catch-V3-2025-03-18/config.yaml"),
    "抓取行为分析V4 / Catch-V4": os.path.join(get_models_path(), "ZhangLab-mouse-C57-catch-V4-2025-03-18/config.yaml"),
    "抓取行为分析V5 / Catch-V5": os.path.join(get_models_path(), "ZhangLab-mouse-C57-catch-V5-2025-03-23/config.yaml")
}

# 检查可用的模型
available_models = {}
for name, path in models.items():
    if os.path.exists(path):
        available_models[name] = path

# 显示模型路径信息
with st.expander("🤖 模型路径信息 / Model Path Information", expanded=False):
    st.write(f"模型根目录 / Models root directory: {get_models_path()}")
    for name, path in models.items():
        exists = "✅" if os.path.exists(path) else "❌"
        st.write(f"{exists} {name}: {path}")

tab1, tab2, tab3 = st.tabs([
    "📊 视频分析 / Video Analysis",
    "🔄 数据处理 / Result Process",
    "📥 结果下载 / Download"
])

with tab1:
    # 显示GPU状态
    high_memory_usage, gpu_count, selected_gpus = show_gpu_status()
    
    # 模型选择
    st.subheader("🤖 模型选择 / Model Selection")
    
    if available_models:
        default_index = list(available_models.keys()).index("抓取行为分析V3 / Catch-V3") if "抓取行为分析V3 / Catch-V3" in available_models else 0
        selected_model_name = st.selectbox(
            "选择分析模型 / Choose analysis model",
            list(available_models.keys()),
            index=default_index,
            help="选择适合您的实验对象的模型，V3版本为最新版 / Select the model suitable for your experimental subject, V3 is the latest version"
        )
        config_path = available_models[selected_model_name]
        st.success(f"已选择模型 / Selected model: {selected_model_name}")
    else:
        st.error("❌ 未找到可用的模型文件，请检查模型安装 / No available models found, please check model installation")
        st.stop()
    
    # 分析控制
    if high_memory_usage:
        st.warning("⚠️ GPU显存占用率高，请稍后再试 / High GPU memory usage detected. Please wait before starting analysis.")
    else:
        if folder_path and selected_files:  # 只在有选择文件时显示开始分析按钮
            if st.button("🚀 开始GPU分析 / Start GPU Analysis", use_container_width=True):
                try:
                    user_name = st.session_state.get('name', 'unknown_user')
                    with open(web_log_file_path, "a", encoding='utf-8') as web_log_file:
                        web_log_file.write(f"\n{user_name}, {current_time}\n")
                    create_and_start_analysis(folder_path, selected_files, config_path, gpu_count, current_time, selected_gpus)
                    st.success("✅ 分析已开始！请查看日志了解进度 / Analysis started! Check logs for progress.")
                except Exception as e:
                    st.error(f"❌ 分析启动失败 / Failed to start analysis: {e}")
        else:
            st.info("请选择要分析的视频文件 / Please select video files to analyze")
    
    # 日志显示
    st.subheader("📋 分析日志 / Analysis Logs")
    if st.button("🔄 刷新日志 / Refresh Logs"):
        if folder_path:  # 只在有工作目录时显示日志
            last_log_entries = fetch_last_lines_of_logs(folder_path, gpu_count)
            for gpu, log_entry in last_log_entries.items():
                with st.expander(f"GPU {gpu} 日志 / Log", expanded=True):
                    st.code(log_entry)
        else:
            st.info("请先选择工作目录 / Please select a working directory first")

with tab2:
    st.subheader("🔄 结果处理 / Result Processing")
    if folder_path:
        st.info(f"当前工作目录 / Current working folder: {os.path.basename(folder_path)}")
        st.info(f"当前使用的模型 / Current model: {selected_model_name if 'selected_model_name' in locals() else 'Not selected'}")
        
        # 添加处理参数设置
        with st.expander("⚙️ 处理参数设置 / Processing Parameters", expanded=True):
            likelihood_threshold = st.slider(
                "置信度阈值 / Likelihood threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.05,
                help="关键点检测置信度阈值 / Keypoint detection confidence threshold"
            )
            
            st.info("其他参数已设置为最优默认值 / Other parameters are set to optimal default values")
            st.markdown("""
            #### 默认参数说明 / Default Parameters:
            - 帧率 / Frame Rate: 120 fps
            - 最小持续时间 / Min Duration: 0.17秒 (20帧)
            - 最大持续时间 / Max Duration: 1秒 (120帧)
            - 最小位移阈值 / Min Distance: 20像素
            - 最小高度变化 / Min Height Change: 10像素
            - 最小抬升速度 / Min Lift Speed: 2像素/帧
            """)
        
        # 确保按钮显示
        st.markdown("### 开始处理 / Start Processing")
        
        if st.button("⚡ 处理分析结果 / Process Analysis Results", key="process_results_button", use_container_width=True):
            # 查找所有以010.csv结尾的文件
            csv_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith('010.csv'):
                        csv_files.append(os.path.join(root, file))
            
            if not csv_files:
                st.warning("⚠️ 未找到符合条件的CSV文件 / No matching CSV files found")
            else:
                st.info(f"找到 {len(csv_files)} 个CSV文件需要处理 / Found {len(csv_files)} CSV files to process")
                
                progress_bar = st.progress(0)
                for i, csv_path in enumerate(csv_files):
                    with st.spinner(f"处理文件 / Processing: {os.path.basename(csv_path)}"):
                        # 获取对应的视频文件路径
                        file_basename = os.path.basename(csv_path)
                        # 移除DLC相关部分
                        if 'DLC' in file_basename:
                            video_name = file_basename.split('DLC')[0] + '.mp4'
                        else:
                            # 如果文件名不包含DLC，则直接替换.csv为.mp4
                            video_name = os.path.splitext(file_basename)[0] + '.mp4'
                        
                        video_path = os.path.join(os.path.dirname(csv_path), video_name)
                        
                        try:
                            # 使用新的处理方法
                            process_mouse_catch_video(
                                video_path=video_path,
                                csv_path=csv_path,
                                threshold=likelihood_threshold
                            )
                            
                            # Display analysis results
                            video_dir = os.path.dirname(video_path)
                            video_name = os.path.splitext(os.path.basename(video_path))[0]
                            results_dir = os.path.join(video_dir, f"{video_name}_results")
                            figure_dir = os.path.join(results_dir, "figures")
                            
                            # Display charts and results
                            st.subheader(f"Analysis Results - {video_name}")
                            
                            analysis_png = os.path.join(figure_dir, "catch_analysis.png")
                            if os.path.exists(analysis_png):
                                st.image(analysis_png, caption="Catch Behavior Analysis")
                            
                            results_csv = os.path.join(results_dir, "catch_analysis_results.csv")
                            if os.path.exists(results_csv):
                                results_df = pd.read_csv(results_csv)
                                if not results_df.empty:
                                    st.dataframe(results_df)
                                else:
                                    st.info("No valid catch behaviors detected")
                            
                            st.success(f"✅ Processed: {os.path.basename(csv_path)}")
                        except Exception as e:
                            st.error(f"❌ 处理失败 / Processing failed: {os.path.basename(csv_path)} - {str(e)}")
                        
                        # 更新进度条
                        progress_bar.progress((i + 1) / len(csv_files))
                    
                st.success("✅ 所有文件处理完成 / All files processed")
    else:
        st.warning("⚠️ 请先在分析页面选择工作目录 / Please select a working directory in the analysis tab first")

with tab3:
    st.subheader("📥 结果下载 / Result Download")
    if folder_path:
        st.info(f"当前工作目录 / Current working folder: {os.path.basename(folder_path)}")
        st.info(f"当前使用的模型 / Current model: {selected_model_name if 'selected_model_name' in locals() else 'Not selected'}")
        
        try:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📦 下载所有文件 / Download All Files", use_container_width=True):
                    filter_and_zip_files(folder_path)
            
            with col2:
                if st.button("📄 下载除MP4外的所有文件 / Download All Except MP4", use_container_width=True):
                    filter_and_zip_files(folder_path, excluded_ext=['.mp4'])
            
            with col3:
                if st.button("📊 仅下载CSV文件 / Download Only CSV", use_container_width=True):
                    filter_and_zip_files(folder_path, included_ext=['.csv'])
            
        except Exception as e:
            st.error(f"❌ 文件下载出错 / Error during file download: {e}")
    else:
        st.warning("⚠️ 请先在分析页面选择工作目录 / Please select a working directory in the analysis tab first") 
