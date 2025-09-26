import streamlit as st
import os
from src.core.utils.file_utils import (
    list_directories,
    upload_files,
    select_video_files
)

def setup_working_directory(root_directory: str):
    """设置工作目录并处理文件上传
    Setup working directory and handle file uploads
    
    Args:
        root_directory (str): 根目录路径
        
    Returns:
        tuple: (folder_path, selected_files)
    """
    try:
        # 确保根目录存在
        if not os.path.exists(root_directory):
            os.makedirs(root_directory)
            st.info(f"已创建根目录 / Created root directory: {root_directory}")
        
        # 初始化session state
        if 'show_folder_input' not in st.session_state:
            st.session_state.show_folder_input = False
        if 'folder_created' not in st.session_state:
            st.session_state.folder_created = False
        if 'current_folder' not in st.session_state:
            st.session_state.current_folder = None
        
        # 新建文件夹功能
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("📁 新建文件夹 / New Folder", use_container_width=True):
                st.session_state.show_folder_input = True
                st.session_state.folder_created = False
        
        if st.session_state.show_folder_input:
            folder_name = st.text_input("输入文件夹名称 / Enter folder name")
            col3, col4 = st.columns([1, 1])
            with col3:
                if st.button("✅ 确认 / Confirm", use_container_width=True) and folder_name:
                    new_folder_path = os.path.join(root_directory, folder_name)
                    try:
                        if not os.path.exists(new_folder_path):
                            os.makedirs(new_folder_path)
                            st.success(f"创建文件夹成功 / Created folder: {folder_name}")
                            st.session_state.folder_created = True
                            st.session_state.current_folder = folder_name
                            st.rerun()
                        else:
                            st.info(f"文件夹已存在 / Folder already exists: {folder_name}")
                    except Exception as e:
                        st.error(f"创建文件夹失败 / Failed to create folder: {str(e)}")
            with col4:
                if st.button("❌ 取消 / Cancel", use_container_width=True):
                    st.session_state.show_folder_input = False
                    st.rerun()
        
        # 获取目录列表
        directories = list_directories(root_directory)
        
        if not directories:
            st.warning("⚠️ 未找到工作目录，请先创建新文件夹 / No directories found, please create a new folder first")
            return None, None
        
        # 选择工作目录
        selected_directory = st.selectbox(
            "📂 选择工作目录 / Choose a directory",
            directories,
            index=directories.index(st.session_state.current_folder) if st.session_state.current_folder in directories else 0,
            help="选择要处理的文件所在的目录 / Select the directory containing the files to process"
        )
        
        if selected_directory:
            folder_path = os.path.join(root_directory, selected_directory)
            st.session_state.current_folder = selected_directory
            
            # 文件上传区域
            with st.container():
                st.subheader("📤 文件上传 / File Upload")
                upload_files(folder_path)
                selected_files = select_video_files(folder_path)
                
                if selected_files:
                    st.markdown("### 📋 已选择的视频文件 / Selected video files")
                    for file in selected_files:
                        st.markdown(f"- {os.path.basename(file)}")
                    return folder_path, selected_files
                else:
                    st.info("📭 未选择视频文件 / No video files selected")
                    return folder_path, None
        
        return None, None
        
    except Exception as e:
        st.error(f"列出目录失败 / Failed to list directories: {str(e)}")
        return None, None 