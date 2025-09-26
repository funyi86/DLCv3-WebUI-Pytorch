# Repository Guidelines

本指南面向 DLCv3-WebUI-Pytorch 贡献者，概述项目结构、常用命令与交付标准。Follow the sections below to keep every pull request focused, testable, and review-friendly。

## 项目结构与模块组织
- Core entry point `Home.py` 启动本地 Streamlit，适合快速验证 UI 交互与推理流程。
- `pages/` 目录以数字前缀组织页面，例如 `pages/1_Mouse_Scratch.py`，保持导航顺序与命名清晰。
- 核心算法位于 `src/core/`：`processing/` 负责姿态管线，`helpers/` 与 `utils/` 存放复用逻辑，`gpu/` 提供可选 CUDA 加速，`config/` 与 `logging/` 统一配置输出。
- UI widgets 统一放在 `src/ui/`；测试集合在 `tests/` 与 `tests/unit/`，文档位于 `docs/`；运行数据分别归档至 `data/`、`models/`、`logs/`。
- 当扩展数据流时，请在对应子包新增模块并通过 `__init__.py` 暴露最小 API，避免跨层依赖。

## 构建、测试与开发命令
- `python -m venv .venv && source .venv/bin/activate`：创建隔离环境，确保版本一致性。
- `pip install -r requirements.txt` 安装 runtime 依赖；`pip install -e .[dev]` 提供 lint、test、type-check 工具。
- `streamlit run Home.py` 打开主界面；`streamlit run pages/<file>.py` 可聚焦某一页面调试。
- `pytest --cov=src --cov-report=term-missing` 执行测试并显示缺失覆盖率；必要时追加 `-k pattern` 精准运行子集。
- `black . && isort . && flake8` 自动格式化并执行静态检查；`mypy src` 确保类型签名完整。

## 编码风格与命名约定
- Python 3.8+，UTF-8，4 空格缩进；Black 行长 88，isort profile=black，同步 import 顺序。
- flake8 与 mypy 是 CI 必过项；请在提交前手动执行，避免 pipeline 中断。
- 函数、变量采用 snake_case，类使用 PascalCase；Streamlit 页面文件沿用 `数字_描述.py` 模式。
- 对复杂流程写出 concise docstring 或 inline comment，帮助 reviewers 迅速定位意图。

## 测试指南
- 使用 Pytest，文件命名 `test_*.py`；保持单测原子化，通过 fixtures 或 fake 对象隔离 GPU、I/O（参考 `tests/unit/test_gpu_utils.py`）。
- 覆盖率目标遵循 `pyproject.toml` 配置；若 term-missing 指向关键路径，请补充 case 或解释原因。
- 在提交功能前运行 `pytest` 与 `mypy`，确认 CPU-only 环境能够通过全部断言。

## 提交与合并请求规范
- Commit message 建议遵循 Conventional Commits，例如 `feat: add scratch refinement pipeline` 或 `fix: guard gpu fallback`。
- PR 描述需包含问题背景、解决策略、验证步骤；UI 改动附截屏或 GIF，便于 reviewer 快速判断。
- 在请求合并前，确保 `pytest`、`black/isort/flake8`、`mypy` 全部通过，并根据需要更新 `docs/` 与相关测试。
- 关联 issue（使用 `Fixes #id`）并列出潜在风险或后续计划，帮助维护者安排发布。

## 安全与配置提示
- 切勿提交真实凭据；`src/core/config/config.yaml` 仅为样例，实际秘钥放入本地忽略文件或环境变量。
- 大型数据、模型依旧存放在 `data/`、`models/`，不要纳入 Git；`logs/` 输出应在 `.gitignore` 控制范围内。
- 若引入新的 GPU 依赖，请提供 graceful fallback 并在 PR 中说明 CPU 验证步骤，确保 CI 可在无 GPU 节点运行。

## 工作流程建议
- 开发前执行 `git pull --rebase` 保持分支同步，避免后续冲突；完成功能后使用 `git status` 与 `git diff` 自查更改范围。
- 推荐在 PR 讨论中记录 Benchmark、实验配置与失败案例，方便未来复现与回滚。
- 若需跨模块改动，先在 issue 中与维护者对齐方案，再提交 Draft PR 以获取早期反馈。
