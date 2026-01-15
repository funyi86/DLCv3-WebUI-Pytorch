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

def get_config_path() -> Optional[str]:
    """Resolve the authentication config path from env or defaults."""
    env_path = os.environ.get("DLC_WEBUI_CONFIG") or os.environ.get("DLC_WEBUI_CONFIG_PATH")
    if env_path:
        return env_path

    root_dir = get_root_path()
    candidates = [
        os.path.join(root_dir, 'src', 'core', 'config', 'config.local.yaml'),
        os.path.join(root_dir, 'src', 'core', 'config', 'config.yaml'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def render_config_setup_prompt(reason: str) -> None:
    """Show a first-time setup prompt for configuration."""
    st.error(reason)
    st.markdown("### 首次配置 / First-time setup")
    st.markdown("1. 生成本地配置 / Generate local config")
    st.code("python scripts/init_config.py")
    st.markdown("2. 或设置环境变量 / Or set env var")
    st.code('export DLC_WEBUI_CONFIG="/path/to/config.local.yaml"')
    st.code('setx DLC_WEBUI_CONFIG "C:\\path\\to\\config.local.yaml"')
    st.markdown("3. 重新启动应用 / Restart the app")
    st.info("`config.yaml` 为模板；真实配置应放在 `config.local.yaml`")

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
        render_config_setup_prompt('认证配置缺失 / Auth config missing')
        return None
        
    try:
        if 'credentials' not in config or 'cookie' not in config:
            render_config_setup_prompt('配置缺少 credentials 或 cookie / Missing credentials or cookie')
            return None
        usernames = config['credentials'].get('usernames')
        if not usernames:
            render_config_setup_prompt('认证配置缺少用户 / No users configured for authentication')
            return None
        for username, user_info in usernames.items():
            password = str(user_info.get('password', '')).strip()
            if not password or password.upper() == "CHANGE_ME":
                render_config_setup_prompt(f'用户密码未配置 / Password not set for user: {username}')
                return None
        cookie_key = config['cookie'].get('key')
        if not cookie_key or str(cookie_key).strip().upper() == "CHANGE_ME":
            render_config_setup_prompt('Cookie key 未配置 / Cookie key is not configured')
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

def load_app_config() -> Optional[Dict[str, Any]]:
    """Load the app config from env or default paths."""
    config_path = get_config_path()
    if not config_path:
        render_config_setup_prompt('未找到配置文件 / Config file not found.')
        return None
    config = load_config(config_path)
    if not config:
        render_config_setup_prompt(f'配置文件无效 / Invalid config file: {config_path}')
        return None
    return config

def require_authentication(config_path: Optional[str] = None) -> Optional[stauth.Authenticate]:
    """Require user authentication before rendering the rest of the page."""
    config = load_config(config_path) if config_path else load_app_config()
    authenticator = initialize_authenticator(config)
    if not authenticator:
        st.stop()

    authenticator.login(location="sidebar", fields={"Form name": "登录系统 / Login System"})
    auth_status = st.session_state.get("authentication_status")
    if auth_status is False:
        st.error('用户名或密码错误 / Username/password is incorrect')
        st.stop()
    if auth_status is None:
        st.warning('请输入用户名和密码 / Please enter your username and password')
        st.stop()

    return authenticator

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
