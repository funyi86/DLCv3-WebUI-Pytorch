import os
from typing import List, Optional
import streamlit as st

def create_video_combination_script(folder_path: str, selected_files: List[str], output_directory: str, output_filename: str = "combined_video.mp4") -> Optional[str]:
    """
    创建视频合并脚本
    Create video combination script
    
    Args:
        folder_path (str): 视频文件所在目录
        selected_files (List[str]): 选定的视频文件列表（完整路径）
        output_directory (str): 输出目录
        output_filename (str, optional): 输出文件名，默认为"combined_video.mp4"
        
    Returns:
        Optional[str]: 脚本文件路径（失败时返回 None）
    """
    try:
        # 确保输出目录存在
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            
        # 创建脚本文件
        script_name = "combine_videos.py"
        script_path = os.path.join(folder_path, script_name)
        
        # 写入脚本内容
        with open(script_path, 'w', encoding='utf-8') as f:
            # 添加编码声明
            f.write('# -*- coding: utf-8 -*-\n')
            f.write('import os\n')
            f.write('import subprocess\n\n')
            
            f.write('def combine_videos(input_files, output_file):\n')
            f.write('    # 创建文件列表\n')
            f.write('    with open("file_list.txt", "w", encoding="utf-8") as f:\n')
            f.write('        for file in input_files:\n')
            f.write('            f.write(f"file \'{file}\'\\n")\n')
            f.write('    \n')
            f.write('    # 使用ffmpeg合并视频\n')
            f.write('    try:\n')
            f.write('        subprocess.run(\n')
            f.write('            ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c", "copy", output_file],\n')
            f.write('            check=True\n')
            f.write('        )\n')
            f.write('        print(f"Videos combined successfully: {output_file}")\n')
            f.write('    except subprocess.CalledProcessError as e:\n')
            f.write('        print(f"Error combining videos: {e}")\n')
            f.write('    finally:\n')
            f.write('        # 清理临时文件\n')
            f.write('        if os.path.exists("file_list.txt"):\n')
            f.write('            os.remove("file_list.txt")\n')
            
            # 添加执行代码
            f.write('\n# 执行合并\n')
            f.write('input_files = [\n')
            for file_path in selected_files:
                f.write(f'    r"{file_path}",\n')
            f.write(']\n\n')
            
            output_file = os.path.join(output_directory, output_filename)
            f.write(f'output_file = r"{output_file}"\n')
            f.write('combine_videos(input_files, output_file)\n')
            
        return script_path
        
    except Exception as e:
        st.error(f"创建合并脚本失败 / Failed to create combination script: {str(e)}")
        return None 
