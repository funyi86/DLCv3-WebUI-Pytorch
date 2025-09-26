import streamlit as st
from src.core.gpu.gpu_utils import display_gpu_usage
from src.core.gpu.gpu_selector import setup_gpu_selection

def show_gpu_status():
    """显示GPU状态和选择器 / Display GPU status and selector"""
    st.subheader("🖥️ GPU 状态 / GPU Status")
    high_memory_usage = display_gpu_usage()
    
    st.subheader("⚙️ GPU 配置 / GPU Configuration")
    gpu_count, selected_gpus = setup_gpu_selection()
    
    if selected_gpus:
        st.success(f"可用GPU数量 / Available GPUs: {gpu_count}")
        st.info(f"已选择的GPU / Selected GPUs: {selected_gpus}")
        
    return high_memory_usage, gpu_count, selected_gpus
