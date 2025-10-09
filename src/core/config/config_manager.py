import os
from typing import Optional, Dict, Any, cast
import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth

def get_root_path() -> str:
    """获取项目根目录路径"""
    current_file = os.path.abspath(__file__)
    core_config_dir = os.path.dirname(current_file)
    core_dir = os.path.dirname(core_config_dir)
    src_dir = os.path.dirname(core_dir)
    root_dir = os.path.dirname(src_dir)
    return root_dir

def get_data_path() -> str:
    """获取数据目录路径"""
    return os.path.join(get_root_path(), 'data')

def get_models_path() -> str:
    """获取模型目录路径"""
    return os.path.join(get_root_path(), 'models')

def load_config(file_path: str) -> Optional[Dict[str, Any]]:
    """加载配置文件
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        配置字典或None（如果加载失败）
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)

        if isinstance(config_data, dict):
            return cast(Dict[str, Any], config_data)
        return None
    except FileNotFoundError:
        return None
    except yaml.YAMLError as e:
        st.error(f'YAML文件解析错误：{e}')
        return None
    except Exception as e:
        st.error(f'加载配置文件时发生错误：{str(e)}')
        return None

def initialize_authenticator(config: Optional[Dict[str, Any]]) -> Optional[stauth.Authenticate]:
    """初始化认证器
    
    Args:
        config: 配置字典
        
    Returns:
        认证器实例或None（如果初始化失败）
    """
    if not config:
        return None
        
    try:
        if 'credentials' not in config or 'cookie' not in config:
            return None
            
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )
        return authenticator
    except Exception as e:
        st.error(f'认证初始化失败：{str(e)}')
        return None

def load_last_usage_log(file_path: str) -> str:
    """加载最后的使用日志
    
    Args:
        file_path: 日志文件路径
        
    Returns:
        最后一行日志或错误信息
    """
    try:
        if not os.path.exists(file_path):
            return "No usage log available."
            
        with open(file_path, 'r', encoding='utf-8') as usage_file:
            lines = usage_file.readlines()
            if lines:
                return lines[-1].strip()
            return "No usage log entries."
    except Exception as e:
        st.error(f'读取日志错误：{e}')
        return "Error accessing usage log."

def update_session_last_usage(log_message: str) -> None:
    """更新会话中的最后使用记录
    
    Args:
        log_message: 日志消息
    """
    if 'last_log_line_usage' not in st.session_state or st.session_state['last_log_line_usage'] != log_message:
        st.session_state['last_log_line_usage'] = log_message
