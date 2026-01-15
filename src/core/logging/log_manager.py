import os
import logging
import streamlit as st
from datetime import datetime
from typing import Optional

def setup_logging() -> None:
    """
    设置日志系统
    Setup logging system
    """
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                os.path.join('logs', 'app.log'),
                encoding='utf-8'
            )
        ]
    )

def load_last_usage_log(file_path: str) -> str:
    """
    加载最后的使用日志
    Load last usage log
    
    Args:
        file_path (str): 日志文件路径
        
    Returns:
        str: 最后一行日志或错误信息
    """
    try:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 如果文件不存在，创建它
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Log file created at {current_time}\n")
            return "新建日志文件 / New log file created"
            
        # 读取最后一行
        with open(file_path, 'r', encoding='utf-8') as usage_file:
            lines = usage_file.readlines()
            if lines:
                return lines[-1].strip()
            return "日志为空 / Log is empty"
            
    except Exception as e:
        logging.error(f"读取日志错误 / Error reading log: {str(e)}")
        return f"读取日志错误 / Error reading log: {str(e)}"

def update_session_last_usage(log_message: str) -> None:
    """
    更新会话中的最后使用记录
    Update last usage record in session
    
    Args:
        log_message (str): 日志消息
    """
    if 'last_log_line_usage' not in st.session_state or st.session_state['last_log_line_usage'] != log_message:
        st.session_state['last_log_line_usage'] = log_message

def log_user_action(user_name: str, action: str, file_path: Optional[str] = None) -> None:
    """
    记录用户操作
    Log user action
    
    Args:
        user_name (str): 用户名
        action (str): 操作描述
        file_path (str, optional): 日志文件路径
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{current_time} - {user_name} - {action}"
    
    if file_path:
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{log_message}\n")
        except Exception as e:
            logging.error(f"写入日志错误 / Error writing log: {str(e)}")
    
    logging.info(log_message) 
