import os
import zipfile
import streamlit as st
import base64
from typing import List, Optional


def filter_and_zip_files(folder_path: str, included_ext: Optional[List[str]] = None, excluded_ext: Optional[List[str]] = None) -> None:
    """
    将指定目录中的文件打包成zip文件并提供下载
    Zip files in the specified directory and provide download

    Args:
        folder_path (str): 目录路径
        included_ext (List[str], optional): 要包含的文件扩展名列表
        excluded_ext (List[str], optional): 要排除的文件扩展名列表
    """
    try:
        # 创建临时zip文件
        zip_path = os.path.join(folder_path, 'results.zip')

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()

                    # 检查文件是否应该被包含
                    should_include = True
                    if included_ext:
                        should_include = ext in included_ext
                    if excluded_ext and ext in excluded_ext:
                        should_include = False

                    if should_include and file != 'results.zip':
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)

        # 创建下载按钮
        with open(zip_path, 'rb') as f:
            bytes_data = f.read()
        b64 = base64.b64encode(bytes_data).decode()
        href = f'<a href="data:application/zip;base64,{b64}" download="results.zip">📥 下载ZIP文件 / Download ZIP</a>'
        st.markdown(href, unsafe_allow_html=True)

        # 删除临时zip文件
        os.remove(zip_path)

    except Exception as e:
        st.error(f"创建ZIP文件失败 / Failed to create ZIP file: {str(e)}")
