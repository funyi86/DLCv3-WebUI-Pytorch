# DLC-WebUI

基于 DeepLabCut 的动物行为分析 Web 界面 / DeepLabCut-based animal behavior analysis Web UI

## 快速开始 / Quickstart
- 创建环境 / Create env
  - Linux/macOS: `python -m venv .venv && source .venv/bin/activate`
  - Windows (PowerShell): `.venv\Scripts\Activate`
- 安装依赖 / Install runtime: `pip install -r requirements.txt`
- 运行应用 / Run app: `streamlit run Home.py`
- 首次使用 / First run: 浏览器访问 http://localhost:8501

## 开发命令 / Dev Commands
- 安装开发依赖 / Dev install: `pip install -e .[dev]`
- 运行测试 / Tests: `pytest`（已启用覆盖率 / coverage enabled）
- 代码格式 / Lint+Format: `black . && isort . && flake8`
- 类型检查 / Type check: `mypy src`

## 功能概览 / Features
- 视频预处理与裁剪 / Video preprocessing & cropping（GPU 可选 / GPU optional）
- 行为分析模块 / Behavior analysis: 抓挠、理毛、游泳、三箱、两鼠社交、CPP、抓取
- GPU 状态展示与选择 / GPU status & selector
- 用户认证与日志记录 / Auth + logging

## 目录结构 / Project Structure
```
Home.py                 # Streamlit 入口 / entrypoint
pages/                  # 多页面入口 / multipage routes
src/
  core/
    processing/ helpers/ utils/ gpu/ config/ logging/
  ui/
    components/         # 复用 UI 组件 / reusable UI
    pages/              # （可能废弃）旧版页面 / legacy pages
tests/                  # Pytest
docs/                   # 安装与快速开始 / docs
requirements.txt, pyproject.toml
logs/                   # 运行日志（可忽略于 PR）
```

## 配置与数据 / Config & Data
- 配置文件 / Config: `src/core/config/config.yaml`（可能包含认证信息；请勿提交到远端仓库）
- 数据与模型 / Data & Models: 放置于 `data/` 与 `models/`（不纳入 Git）
- GPU 可选 / GPU optional: 无 GPU 也可运行非 GPU 流程

## 贡献 / Contributing
- 开发规范与流程请见 `AGENTS.md`（Repository Guidelines）
- PR 需通过：`pytest`、`black/isort/flake8`、`mypy`，并附变更说明与必要截图

## 许可证 / License
MIT（见 `LICENSE`）

