import streamlit as st
import os
import datetime
from src.core.config import (
    get_root_path,
    load_config,
    initialize_authenticator,
    get_data_path,
    get_models_path,
)
from src.ui.components import render_sidebar, load_custom_css, show_gpu_status
from src.core.logging import (
    load_last_usage_log,
    update_session_last_usage,
    setup_logging,
    log_user_action
)

setup_logging()

# 设置页面配置
st.set_page_config(
    page_title="DLC-WebUI",
    page_icon="🐁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加载自定义CSS样式
load_custom_css()

def initialize_app():
    """初始化首页内容 / Initialize Home page content"""
    st.markdown('<h1 class="main-title">🐁 DLC-WebUI</h1>', unsafe_allow_html=True)

    st.markdown(
        """
        ### 欢迎 / Welcome
        基于 DeepLabCut 的小鼠行为分析系统，提供视频预处理、裁剪与多种行为分析流程。
        DeepLabCut-based mouse behavior analysis with preprocessing, cropping, and analysis pipelines.
        """
    )

    st.markdown("---")

    # Status and paths
    st.subheader("📊 系统状态 / System Status")
    col1, col2 = st.columns([1, 1])
    with col1:
        # GPU status + selector
        try:
            show_gpu_status()
        except Exception as e:
            st.info(f"GPU 状态不可用 / GPU status unavailable: {e}")
    with col2:
        st.markdown("#### 路径概览 / Paths Overview")
        root_path = get_root_path()
        data_path = get_data_path() if 'get_data_path' in globals() else os.path.join(root_path, 'data')
        models_path = get_models_path() if 'get_models_path' in globals() else os.path.join(root_path, 'models')
        def path_line(label, p):
            exists = os.path.exists(p)
            icon = "✅" if exists else "❌"
            st.write(f"{icon} {label}: {p}")
        path_line("Root", root_path)
        path_line("Data", data_path)
        path_line("Models", models_path)

    # Recent logs
    st.markdown("---")
    st.subheader("📝 最近活动 / Recent Activity")
    log_file = os.path.join(get_root_path(), 'logs', 'usage.txt')
    last_entry = load_last_usage_log(log_file)
    update_session_last_usage(last_entry)

    user_name = st.session_state.get('name', 'guest')
    if not st.session_state.get('home_page_logged'):
        log_user_action(user_name, 'view_home', log_file)
        st.session_state['home_page_logged'] = True

    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-5:]
            if lines:
                for ln in lines:
                    st.write(f"• {ln.strip()}")
            else:
                st.write("暂无记录 / No entries yet.")
        except Exception as e:
            st.warning(f"读取日志失败 / Failed to read logs: {e}")
    else:
        st.write("未找到日志文件 / Log file not found.")

def main():
    """主函数"""
    # 加载配置和初始化认证器
    config = load_config(os.path.join(get_root_path(), 'src', 'core', 'config', 'config.yaml'))
    authenticator = initialize_authenticator(config)
    
    if authenticator:
        # 将登录组件放置于侧边栏顶部
        authenticator.login(location="sidebar", fields={"Form name": "登录系统 / Login System"})
        
        # 登录状态检查
        if st.session_state["authentication_status"] is False:
            st.error('用户名或密码错误 / Username/password is incorrect')
            st.stop()  # 停止渲染本次执行，等待用户修改输入
        elif st.session_state["authentication_status"] is None:
            st.warning('请输入用户名和密码 / Please enter your username and password')
            st.stop()  # 停止渲染本次执行，也会保持登录表单可继续交互
    
    # 调用功能导航组件，此时登录组件已位于侧边栏顶部
    initialize_app()

if __name__ == "__main__":
    main()
    render_sidebar()
