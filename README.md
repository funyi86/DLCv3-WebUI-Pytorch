# DLC-WebUI

基于 DeepLabCut 的小鼠行为分析 Streamlit 界面 / Streamlit interface for DeepLabCut-based mouse behavior analysis

## ⚠️ 科学注意事项 / Scientific Notes (Read First)
- 当前部分行为判定依赖固定像素阈值与几何假设，必须结合实验装置标定（像素↔厘米、ROI、fps）与人工标注验证后再用于结论。
- 三箱实验目前用“爪-尾距离 < 40px”做检测，与常见三箱社交/室内占据指标不一致，结果仅供参考。
- CPP 使用固定中线 375px 且仅统计 15–35 帧停留，可能在分辨率变化时反转分区并截断真实停留时长。
- 理毛/抓挠基于像素距离与短时段筛选，未做体长归一化或节律性判据，可能误判或漏判。
- 游泳以躯干弯曲角阈值与 15–35 帧时长定义“游泳”，不等同于强迫游泳的常规运动/静止指标。
- 双鼠社交固定 100px/45° 阈值且图表默认 30fps，跨相机设置需重新校准。
- 抓取行为依赖固定 ROI 与 x 方向位移/速度，强依赖装置几何与拍摄角度。

## 建议参数起点 / Suggested Parameters (Starting Points)
以下为初次标定与回归测试的起始范围，建议先完成像素↔厘米标定，再以厘米或体长（BL）作为单位，并用人工标注数据校准。
- 通用：关键点置信度阈值 0.90–0.95；缺失插值间隙 ≤0.3–0.5s；平滑窗口 5–10 帧。
- 三箱 / Three-Chamber：按装置边界定义左/中/右 ROI；刺激区半径 2–3cm（或 0.5–1.0 BL）；最小停留 1s；统计进入次数与停留时长。
- CPP：根据标定中线划分 drug/saline；可排除中线带宽 1 BL；使用全程有效帧统计；偏好指数 (Tdrug-Tsaline)/(Tdrug+Tsaline)。
- 理毛 / Grooming：爪-口距离 <0.3–0.5 BL 且体躯移动 <0.5 BL/s；最小片段 0.5–1s；间隔合并 ≤0.2–0.3s。
- 抓挠 / Scratch：爪部速度 >1–2 BL/s 且位移幅度 0.1–0.3 BL/帧；事件持续 ≥0.3s；频率参考 5–15 Hz（需以标注校准）。
- 游泳 / Forced Swim：以质心速度判定不动；不动阈值 <0.1–0.2 BL/s 且持续 ≥1–2s；平滑窗口 0.3–0.5s。
- 双鼠社交 / Two-Social：鼻-鼻或鼻-体距离 <2–4cm（或 0.5–1.0 BL）；朝向阈值 45–60°；最小片段 1–2s；间隔合并 ≤0.5s。
- 抓取 / Catch：ROI 均以标定坐标定义；最小持续 0.1–0.3s；最小事件间隔 0.5–1.0s；轨迹距离与速度使用 2D 路径长度（cm/s）。

## 实验清单 / Experiment Checklist
- 标定：记录像素↔厘米比例、fps、相机角度；按装置尺寸标定 ROI（含刺激区/中线/禁入带）。
- 关键点质量：人工抽检并统计帧内关键点置信度分布；推荐中位数 ≥0.9，低置信度帧占比 ≤10%。
- 行为定义：明确行为起止判据（距离/速度/朝向/停留时长），并统一单位（cm 或 BL）。
- 参数校准：用标注子集做阈值扫描（距离、速度、最小时长、合并间隔），选取能最大化一致性的组合。
- 结果报告：固定输出单位、阈值、ROI 与视频条件；保留标注集与参数版本号。

## 回归测试清单 / Regression Test Checklist
以下为建议的初始验收目标（可根据实验与装置调整）。
- 通用一致性：在固定标注集上，事件级 F1 ≥0.75，持续时间中位误差 ≤0.3s。
- 三箱 / Three-Chamber：各区域停留时长与标注一致性 R ≥0.85；进入次数偏差 ≤10%。
- CPP：偏好指数误差 ≤0.1；drug/saline 停留时长偏差 ≤10%。
- 理毛 / Grooming：事件级 F1 ≥0.8；片段持续时间误差 ≤0.5s。
- 抓挠 / Scratch：事件频率偏差 ≤15%；每分钟计数相关性 R ≥0.8。
- 游泳 / Forced Swim：不动时间总量偏差 ≤10%；分钟级相关性 R ≥0.8。
- 双鼠社交 / Two-Social：interaction/proximity 时长偏差 ≤10%；事件级 F1 ≥0.75。
- 抓取 / Catch：事件级 F1 ≥0.75；轨迹长度误差 ≤10%；峰值高度误差 ≤0.3cm。

## 目录 / Table of Contents
- [科学注意事项 / Scientific Notes (Read First)](#科学注意事项--scientific-notes-read-first)
- [建议参数起点 / Suggested Parameters (Starting Points)](#建议参数起点--suggested-parameters-starting-points)
- [实验清单 / Experiment Checklist](#实验清单--experiment-checklist)
- [回归测试清单 / Regression Test Checklist](#回归测试清单--regression-test-checklist)
- [概览 / Overview](#概览--overview)
- [快速上手 / Quickstart](#快速上手--quickstart)
- [功能矩阵 / Feature Matrix](#功能矩阵--feature-matrix)
- [页面导航 / Page Navigation](#页面导航--page-navigation)
- [项目结构 / Project Structure](#项目结构--project-structure)
- [配置与数据 / Configuration & Data](#配置与数据--configuration--data)
- [开发流程 / Development Workflow](#开发流程--development-workflow)
- [测试与质量 / Testing & Quality](#测试与质量--testing--quality)
- [文档与脚本 / Docs & Scripts](#文档与脚本--docs--scripts)
- [贡献指南 / Contributing](#贡献指南--contributing)
- [许可证 / License](#许可证--license)

## 概览 / Overview
- 提供端到端小鼠行为分析：视频预处理、裁剪、DeepLabCut 动作推理与行为分类。
- 基于 Streamlit 构建，内置认证、GPU 选择和运行日志，方便实验室多用户协作。
- 支持 CPU-only 部署，GPU 加速为可选加速路径，默认在无 GPU 环境优雅降级。
- 目录与模块遵循 `src/core`, `src/ui`, `pages` 划分，便于扩展新行为或组件。

## 快速上手 / Quickstart
1. **克隆仓库 / Clone**
   ```bash
   git clone https://github.com/your-org/DLCv3-WebUI-Pytorch.git
   cd DLCv3-WebUI-Pytorch
   ```
2. **Ubuntu 自动化安装 / Ubuntu automated setup**
   ```bash
   bash install_dlc_env_ubuntu.sh DLCv3-WebUI
   conda activate DLCv3-WebUI
   ```
   脚本会创建 Conda + mamba 环境并安装运行所需依赖，如需开发工具可追加 `pip install -e .[dev]`。
3. **配置认证与路径 / Configure auth & paths**
   - 运行 `python scripts/init_config.py` 生成 `src/core/config/config.local.yaml`（含密码哈希与 cookie key）。
   - 或设置环境变量 `DLC_WEBUI_CONFIG` 指向你的配置文件路径。
   - 设置 `data/`、`models/`、`logs/` 至本地大容量磁盘，避免提交到 Git。
3. **macOS CPU-only 指南 / macOS CPU-only guide**
   - 见 `docs/guides/installation.md` 的 “macOS CPU-only Quick Start” 章节。
4. **运行应用 / Run the app**
   ```bash
   streamlit run Home.py
   ```
   浏览器访问 `http://localhost:8501`。若调试单一页面：`streamlit run pages/<page>.py`。

## 功能矩阵 / Feature Matrix
- **用户登录 / Authentication**：基于 `streamlit-authenticator`，集中配置于 `config.local.yaml` 或 `DLC_WEBUI_CONFIG`。
- **GPU 管理 / GPU manager**：调用 `GPUtil` 监控显卡状态，支持在界面中选择推理设备。
- **视频预处理 / Video preprocessing**：封装裁剪、拼接、帧抽取等操作，兼容多实验范式。
- **行为分析 / Behavioral analysis**：抓挠、理毛、游泳、三箱、双鼠社交、条件位置偏好（CPP）、抓取等流程。
- **日志追踪 / Logging**：`logs/usage.txt` 记录最近活动，首页可视化最新条目。
- **可扩展 UI 组件 / Reusable UI**：`src/ui/components` 存放常用控件与样式，保持页面一致性。

## 页面导航 / Page Navigation
- `Home.py`：登录入口、系统状态、最近活动摘要。
- `pages/1_Mouse_Scratch.py`：抓挠行为识别与可视化流程。
- `pages/2_Mouse_Grooming.py`：理毛行为分析，支持多视频批量处理。
- `pages/3_Mouse_Swimming.py`：游泳测试，包含姿态轨迹和事件统计。
- `pages/4_Three_Chamber.py`：三箱社交实验数据导入与指标对比。
- `pages/5_Two_Social.py`：双鼠社交交互分析，支持同步视频。
- `pages/6_Mouse_CPP.py`：条件位置偏好实验（CPP）结果汇总。
- `pages/7_Video_Preparation.py`：批量视频预处理、帧提取和格式转换。
- `pages/8_Video_Crop.py`：交互式视频裁剪与 ROI 设置。
- `pages/9_Mouse_Catch.py`：抓取实验流程与动作分类。

## 项目结构 / Project Structure
```
DLCv3-WebUI-Pytorch/
├── Home.py                # Streamlit 入口 / entry point
├── pages/                 # 主界面分页 / Streamlit pages
├── src/
│   ├── core/
│   │   ├── config/        # 配置加载 & Auth
│   │   ├── processing/    # 行为分析与视频处理流水线
│   │   ├── helpers/       # 下载、视频拼接等复用逻辑
│   │   ├── gpu/           # GPU 检测与选择工具
│   │   ├── logging/       # 使用日志记录与追踪
│   │   └── utils/         # 通用脚本执行与文件处理
│   ├── ui/                # UI 组件与样式
│   └── static/            # 静态资源（图片、CSS）
├── tests/                 # Pytest 集合（示例见 unit/test_gpu_utils.py）
├── docs/                  # 安装与快速开始文档
├── scripts/               # 安装、分析脚本与参考说明
├── install_dlc_env_ubuntu.sh
├── requirements.txt
├── pyproject.toml
└── logs/, data/, models/  # 运行输出（默认忽略于 Git）
```
扩展新模块时更新对应 `__init__.py` 并保持跨层依赖最小化。

## 配置与数据 / Configuration & Data
- `src/core/config/config.yaml` 为示例模板（含 `CHANGE_ME` 占位符）；请复制为 `src/core/config/config.local.yaml` 或通过 `DLC_WEBUI_CONFIG` 指定真实配置。
- 数据与模型分别放在 `data/`、`models/`，保持在 Git ignore 范围内。
- 日志输出位于 `logs/`，通过 `src/core/logging` 统一管理，可自定义保留策略。

## 开发流程 / Development Workflow
- 创建并激活虚拟环境，执行 `pip install -e .[dev]` 以安装测试、格式化与类型检查工具。
- 更新页面或算法时，优先复用 `src/ui/components` 与 `src/core/processing`，避免在 `pages/` 内编写大量业务逻辑。
- 新增数据流请在 `src/core/<module>/__init__.py` 暴露最小 API，保持模块边界清晰。
- 重要实验配置、Benchmark 与失败案例建议记录在 PR 讨论或 `docs/` 对应章节。

## 测试与质量 / Testing & Quality
- 单测使用 Pytest：`pytest --cov=src --cov-report=term-missing`
- 静态检查与格式化：`black . && isort . && flake8`
- 类型检查：`mypy src`
- CPU-only 环境需全部通过以上命令；若新增 GPU 功能，请为 CPU 场景提供 fallback 并补充说明。
- 参考 `tests/unit/test_gpu_utils.py` 了解如何使用 fixtures 隔离硬件依赖。

## 文档与脚本 / Docs & Scripts
- 入门文档与补充指南：`docs/README.md`、`docs/guides/installation.md`、`docs/guides/quickstart.md`
- 部署与环境脚本：`install_dlc_env_ubuntu.sh`、`scripts/deeplabcut v3 install *.txt`
- 分析辅助脚本：`scripts/analyze_references.py`、`archive/` 下存有历史实现，可用作参考但不建议直接复用。

## 贡献指南 / Contributing
- 请先阅读 `AGENTS.md` 与 `CONTRIBUTING.md`，了解提交规范、命名约定与代码风格。
- Commit 推荐使用 Conventional Commits，例如 `feat: add scratch refinement pipeline`。
- PR 需附带变更背景、解决策略与验证步骤；UI 改动请附截图或 GIF。
- 在合并前确保 `pytest`、`black`、`isort`、`flake8`、`mypy` 均通过，并同步更新相关文档与测试。

## 许可证 / License
本项目使用 MIT License，详情见 `LICENSE`。
