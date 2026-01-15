# 安装指南 / Installation Guide

## 系统要求 / System Requirements

### 硬件要求 / Hardware Requirements
- CPU: 4核或以上 / 4 cores or more
- 内存: 16GB或以上 / 16GB RAM or more
- GPU: NVIDIA GPU with 8GB或以上显存 / NVIDIA GPU with 8GB VRAM or more
- 硬盘空间: 50GB或以上 / 50GB disk space or more

### 软件要求 / Software Requirements
- 操作系统 / Operating System:
  - Windows 10/11
  - Ubuntu 20.04/22.04
  - macOS 12或以上 / macOS 12 or later
- Python 3.8或以上 / Python 3.8 or later
- CUDA 11.0或以上 / CUDA 11.0 or later
- cuDNN 8.0或以上 / cuDNN 8.0 or later

## 安装步骤 / Installation Steps

### 1. 安装Python环境 / Install Python Environment
```bash
# 使用conda创建环境 / Create environment with conda
conda create -n dlc-webui python=3.9
conda activate dlc-webui
```

### 2. 安装CUDA和cuDNN / Install CUDA and cuDNN
- 从NVIDIA官网下载并安装CUDA / Download and install CUDA from NVIDIA website
- 安装对应版本的cuDNN / Install corresponding cuDNN version

### 3. 克隆项目 / Clone Project
```bash
git clone https://github.com/yourusername/DLC-WebUI.git
cd DLC-WebUI
```

### 4. 安装依赖 / Install Dependencies
```bash
# 使用pip安装依赖 / Install dependencies with pip
pip install -r requirements.txt

# 或使用conda安装 / Or install with conda
conda env create -f environment.yml
```

### 5. 配置设置 / Configure Settings
1. 复制配置模板 / Copy configuration template
```bash
python scripts/init_config.py
```

2. 修改配置文件 / Modify configuration file
- 如需自定义用户名/邮箱，请重新运行脚本并传参 / Re-run the script with arguments to customize username/email
- 如需使用自定义路径，设置 `DLC_WEBUI_CONFIG` 指向你的配置文件 / Set DLC_WEBUI_CONFIG for a custom path

## 验证安装 / Verify Installation

### 1. 运行测试 / Run Tests
```bash
pytest tests/
```

### 2. 启动应用 / Start Application
```bash
python app.py
```

### 3. 访问Web界面 / Access Web Interface
- 打开浏览器访问 / Open browser and visit: http://localhost:8501

## 常见问题 / Common Issues

### 1. CUDA相关问题 / CUDA Related Issues
- 确保CUDA版本与PyTorch兼容 / Ensure CUDA version is compatible with PyTorch
- 检查环境变量设置 / Check environment variables

### 2. 依赖安装问题 / Dependency Installation Issues
- 使用清华镜像源加速下载 / Use Tsinghua mirror for faster download
- 检查Python版本兼容性 / Check Python version compatibility

### 3. 运行时错误 / Runtime Errors
- 检查GPU驱动版本 / Check GPU driver version
- 验证文件权限设置 / Verify file permissions

## 更新说明 / Update Notes

### 版本更新 / Version Updates
- 定期检查新版本 / Check for new versions regularly
- 按照更新日志进行升级 / Follow changelog for upgrades

### 数据备份 / Data Backup
- 更新前备份数据 / Backup data before updates
- 保存自定义配置 / Save custom configurations 
