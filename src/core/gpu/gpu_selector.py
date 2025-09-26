import streamlit as st
import GPUtil

def setup_gpu_selection():
    """
    设置GPU选择界面，返回GPU数量和选择的GPU列表
    Set up GPU selection interface, return GPU count and selected GPU list
    """
    gpus = GPUtil.getGPUs()
    gpu_count = len(gpus)
    
    if gpu_count == 0:
        st.warning("⚠️ 未检测到GPU / No GPU detected")
        return 0, []
        
    # 创建GPU选择选项
    gpu_options = [f"GPU {i}" for i in range(gpu_count)]
    selected_gpus = st.multiselect(
        "选择要使用的GPU / Select GPUs to use",
        range(gpu_count),
        default=list(range(gpu_count)),
        format_func=lambda x: f"GPU {x}"
    )
    
    if not selected_gpus:
        st.warning("⚠️ 请至少选择一个GPU / Please select at least one GPU")
        return gpu_count, []
        
    return gpu_count, selected_gpus 