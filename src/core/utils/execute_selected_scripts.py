import os
import subprocess
import sys
import streamlit as st
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

def execute_script(script_path: str, working_directory: str, output_directory: str) -> tuple:
    """
    执行单个脚本
    Execute a single script
    
    Args:
        script_path (str): 脚本路径
        working_directory (str): 工作目录
        output_directory (str): 输出目录
        
    Returns:
        tuple: (script_name, success, message)
    """
    script_name = os.path.basename(script_path)
    try:
        # 使用Python解释器执行脚本
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_directory
        )
        
        # 获取输出
        stdout, stderr = process.communicate()
        
        # 写入日志
        log_file = os.path.join(output_directory, f"{os.path.splitext(script_name)[0]}.log")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Standard Output:\n{stdout}\n\nErrors:\n{stderr}")
        
        success = process.returncode == 0
        message = stderr if not success else "执行成功 / Execution successful"
        
        return script_name, success, message
    except Exception as e:
        return script_name, False, str(e)

def execute_selected_scripts(working_directory: str, script_files: list, output_directory: str) -> None:
    """
    并行执行选定的Python脚本
    Execute selected Python scripts in parallel
    
    Args:
        working_directory (str): 工作目录路径
        script_files (list): 要执行的脚本文件列表
        output_directory (str): 输出目录路径
    """
    try:
        # 确保目录存在
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # 创建进度条
        progress_text = "执行脚本中... / Executing scripts..."
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 准备脚本路径列表
        script_paths = [os.path.join(working_directory, script) for script in script_files]
        total_scripts = len(script_paths)
        completed_scripts = 0
        
        # 使用线程池并行执行脚本
        with ThreadPoolExecutor() as executor:
            # 提交所有任务
            future_to_script = {
                executor.submit(
                    execute_script, 
                    script_path, 
                    working_directory, 
                    output_directory
                ): script_path 
                for script_path in script_paths
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_script):
                script_name, success, message = future.result()
                completed_scripts += 1
                
                # 更新进度
                progress = completed_scripts / total_scripts
                progress_bar.progress(progress)
                status_text.text(f"{progress_text} ({completed_scripts}/{total_scripts})")
                
                # 显示执行结果
                if success:
                    st.success(f"✅ {script_name}: {message}")
                else:
                    st.error(f"❌ {script_name}: {message}")
        
        # 完成后清理进度显示
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"所有脚本执行完成 / All scripts completed ({completed_scripts}/{total_scripts})")
        
    except Exception as e:
        st.error(f"执行脚本时出错 / Error executing scripts: {str(e)}")

def fetch_last_lines_of_logs(directory: str, num_lines: int = 10) -> dict:
    """
    获取日志文件的最后几行
    Get the last few lines of log files
    
    Args:
        directory (str): 日志文件所在目录
        num_lines (int): 要获取的行数
        
    Returns:
        dict: 包含日志文件名和内容的字典
    """
    log_contents = {}
    try:
        for file in os.listdir(directory):
            if file.endswith('.log'):
                file_path = os.path.join(directory, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # 读取所有行并保留最后num_lines行
                        lines = f.readlines()
                        last_lines = lines[-num_lines:] if len(lines) > num_lines else lines
                        log_contents[file] = ''.join(last_lines)
                except Exception as e:
                    log_contents[file] = f"Error reading log file: {str(e)}"
    except Exception as e:
        st.error(f"读取日志文件时出错 / Error reading log files: {str(e)}")
    
    return log_contents 
