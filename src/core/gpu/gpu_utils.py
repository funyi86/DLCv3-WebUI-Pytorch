import streamlit as st
import GPUtil
from typing import List, Dict


def get_gpu_utilization() -> List[Dict[str, float]]:
    """收集当前 GPU 利用率与显存占用信息"""
    gpus = GPUtil.getGPUs()
    usage = []
    for gpu in gpus:
        usage.append({
            'id': gpu.id,
            'memory_util': getattr(gpu, 'memoryUtil', 0.0),
            'gpu_util': getattr(gpu, 'load', 0.0),
            'total_memory': getattr(gpu, 'memoryTotal', 0.0),
            'used_memory': getattr(gpu, 'memoryUsed', 0.0)
        })
    return usage


def display_gpu_usage() -> bool:
    """
    显示GPU使用情况，并返回是否有高内存使用的标志
    Display GPU usage and return a flag indicating high memory usage
    """
    gpus = GPUtil.getGPUs()
    high_memory_usage = False

    if not gpus:
        st.warning("⚠️ 未检测到GPU / No GPU detected")
        return False

    for gpu in gpus:
        # 创建GPU使用信息的列
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**GPU {gpu.id}**: {gpu.name}")
            st.progress(gpu.load)
            st.text(f"GPU利用率 / GPU Utilization: {gpu.load*100:.1f}%")

        with col2:
            memory_util = gpu.memoryUtil
            st.markdown(f"**显存使用 / Memory Usage**: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")
            st.progress(memory_util)
            st.text(f"显存占用率 / Memory Utilization: {memory_util*100:.1f}%")

        # 检查是否有高内存使用
        if memory_util > 0.75:  # 75%作为高内存使用的阈值
            high_memory_usage = True

    return high_memory_usage
