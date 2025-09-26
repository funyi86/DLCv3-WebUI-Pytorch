import streamlit as st
import os
import datetime
from src.core.config import get_root_path, get_data_path, get_models_path
from src.core.helpers.analysis_helper import create_and_start_analysis, fetch_last_lines_of_logs
from src.core.helpers.download_utils import filter_and_zip_files
from src.core.processing.mouse_scratch_video_processing import process_scratch_files
from src.core.gpu.gpu_utils import display_gpu_usage
from src.core.gpu.gpu_selector import setup_gpu_selection

# 导入共享组件
from src.ui.components import load_custom_css, render_sidebar, show_gpu_status, setup_working_directory

# 设置页面配置
st.set_page_config(
    page_title="Mouse Scratch",
    page_icon="🐁",
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
render_sidebar()

# 页面标题和说明
st.title("🐁 小鼠抓挠行为分析 / Mouse Scratch Behavior Analysis")

with st.expander("💡 使用说明 / Instructions", expanded=True):
    st.markdown("""
    #### 视频要求 / Video Requirements:
    - 格式：MP4 / Format: MP4
    - 分辨率：500x500像素 / Resolution: 500x500 pixels
    - 帧率：30帧/秒 / Frame Rate: 30 fps
    """)

# 设置路径和时间
root_directory = os.path.join(get_data_path(), 'scratch')
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
web_log_file_path = os.path.join(get_root_path(), 'logs', 'usage.txt')

# 设置工作目录
folder_path, selected_files = setup_working_directory(root_directory)

# 设置模型
models = {
    "ICR-DJ-Scratch-V2": os.path.join(get_models_path(), "ABmodels/DJ-scratch-500px-narrow-2024-05-13/config.yaml"),
    "C57-DJ-Scratch-V2": os.path.join(get_models_path(), "ABmodels/C57-Scratch-T2-2024-05-15/config.yaml")
}

# 检查可用的模型
available_models = {}
for name, path in models.items():
    if os.path.exists(path):
        available_models[name] = path

# 创建标签页
tab1, tab2, tab3 = st.tabs([
    "📊 视频分析 / Video Analysis",
    "🔄 数据处理 / Result Process",
    "📥 结果下载 / Download"
])

with tab1:
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
    
    if folder_path:
        # 模型选择
        st.subheader("🤖 模型选择 / Model Selection")
        
        if available_models:
            selected_model_name = st.selectbox(
                "选择分析模型 / Choose analysis model",
                list(available_models.keys()),
                help="选择适合您的实验对象的模型 / Select the model suitable for your experimental subject"
            )
            config_path = available_models[selected_model_name]
            st.success(f"已选择模型 / Selected model: {selected_model_name}")
        else:
            st.error("❌ 未找到可用的模型文件，请检查模型安装 / No available models found, please check model installation")
            st.stop()  # 停止页面执行
        
        # 分析控制
        if high_memory_usage:
            st.warning("⚠️ GPU显存占用率高，请稍后再试 / High GPU memory usage detected. Please wait before starting analysis.")
        elif not selected_files:
            st.warning("⚠️ 请先选择要分析的视频文件 / Please select video files to analyze first")
        else:
            if st.button("🚀 开始GPU分析 / Start GPU Analysis", use_container_width=True):
                try:
                    with open(web_log_file_path, "a", encoding='utf-8') as web_log_file:
                        web_log_file.write(f"\n{st.session_state['name']}, {current_time}\n")
                    
                    with st.spinner("分析中... / Analyzing..."):
                        create_and_start_analysis(folder_path, selected_files, config_path, gpu_count, current_time, selected_gpus)
                        st.success("✅ 分析已开始！请查看日志了解进度 / Analysis started! Check logs for progress.")
                except Exception as e:
                    st.error(f"❌ 分析启动失败 / Failed to start analysis: {e}")
        
        # 日志显示
        st.subheader("📋 分析日志 / Analysis Logs")
        if st.button("🔄 刷新日志 / Refresh Logs"):
            last_log_entries = fetch_last_lines_of_logs(folder_path, gpu_count)
            for gpu, log_entry in last_log_entries.items():
                with st.expander(f"GPU {gpu} 日志 / Log", expanded=True):
                    st.code(log_entry)
                    
        # 自动刷新提示
        st.info('💡 提示：请定期点击"刷新日志"按钮查看分析进度 / Tip: Click "Refresh Logs" periodically to check analysis progress')
    else:
        st.warning("⚠️ 请先选择工作目录 / Please select a working directory first")

with tab2:
    st.subheader("🔄 结果处理 / Result Processing")
    if folder_path:
        # 显示当前工作目录和模型信息
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📂 当前工作目录 / Current working folder: {os.path.basename(folder_path)}")
        with col2:
            if 'selected_model_name' in locals():
                st.info(f"🤖 当前使用的模型 / Current model: {selected_model_name}")
            else:
                st.warning("⚠️ 未选择模型 / No model selected")
        
        # 处理按钮
        if st.button("⚡ 处理分析结果 / Process Analysis Results", use_container_width=True):
            with st.spinner("处理中 / Processing..."):
                process_scratch_files(folder_path, 0.999, 15, 35)
            st.success("✅ 结果处理完成 / Analysis results processed")
    else:
        st.warning("⚠️ 请先在分析页面选择工作目录 / Please select a working directory in the analysis tab first")

with tab3:
    st.subheader("📥 结果下载 / Result Download")
    if folder_path:
        # 显示当前工作目录和模型信息
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📂 当前工作目录 / Current working folder: {os.path.basename(folder_path)}")
        with col2:
            if 'selected_model_name' in locals():
                st.info(f"🤖 当前使用的模型 / Current model: {selected_model_name}")
            else:
                st.warning("⚠️ 未选择模型 / No model selected")
        
        # 下载选项
        st.markdown("### 📦 下载选项 / Download Options")
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