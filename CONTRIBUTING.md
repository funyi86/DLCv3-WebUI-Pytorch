# 贡献指南 / Contributing Guide

感谢你对 DLC-WebUI 的关注！本指南汇总了开发流程、代码规范与提交流程，帮助你快速完成高质量的贡献。

## 前置准备 / Before You Start
- 阅读 `AGENTS.md` 获取仓库整体约束与术语说明。
- 在个人分支上开发，保持 `main` 只接收已审查的变更。
- 更新分支前执行 `git pull --rebase`，减少后续冲突。

## 开发环境 / Development Environment
- 推荐使用仓库提供的自动化脚本：
  ```bash
  bash install_dlc_env_ubuntu.sh DLCv3-WebUI
  conda activate DLCv3-WebUI
  ```
- 安装开发工具链：
  ```bash
  pip install -e .[dev]
  ```
- 所有命令默认在 Python 3.8+ 环境执行，确保与 CI 一致。

## 项目结构 / Project Layout
```
DLCv3-WebUI-Pytorch/
├── Home.py                  # Streamlit 入口 / entry point
├── pages/                   # UI 页面（数字前缀保持导航顺序）
├── src/
│   ├── core/
│   │   ├── config/          # 配置加载、认证能力
│   │   ├── processing/      # 行为与视频处理流水线
│   │   ├── helpers/         # 下载、视频组合等复用逻辑
│   │   ├── gpu/             # GPU 检测与调度
│   │   ├── logging/         # 统一日志接口
│   │   └── utils/           # 通用脚本与文件工具
│   ├── ui/components/       # 可复用 UI 控件、样式
│   └── static/              # CSS、图片等静态资源
├── tests/                   # Pytest 集合（示例：unit/test_gpu_utils.py）
├── docs/                    # 文档与指南
├── scripts/                 # 安装或分析脚本
├── install_dlc_env_ubuntu.sh
├── requirements.txt
└── pyproject.toml
```
扩展新模块时请在对应 `__init__.py` 暴露最小 API，避免跨层依赖。

## 代码规范 / Coding Standards
- **格式 / Formatting**：执行 `black .`（行长 88）、`isort . --profile black`、`flake8`。
- **类型 / Typing**：使用显式类型注解；CI 要求 `mypy src` 无错误。
- **命名 / Naming**：模块与函数采用 `snake_case`，类使用 `PascalCase`，页面文件命名遵循 `数字_描述.py`。
- **注释 / Comments**：对复杂逻辑提供简洁中英文注释或 docstring，避免冗长说明。
- **异常 / Errors**：优先复用 `src/core` 中已有异常与日志工具，保持错误信息可追踪。

## 测试与验证 / Testing & Verification
在提交或创建 PR 前务必运行：
```bash
pytest --cov=src --cov-report=term-missing
black .
isort .
flake8
mypy src
```
- 针对 GPU 相关改动，确保 CPU-only 环境仍能正常执行（提供 fallback）。
- 新增功能需附带相应单测或说明缺失原因；可参考 `tests/unit/test_gpu_utils.py` 构建硬件隔离的测试。

## Git 工作流 / Git Workflow
- **分支命名 / Branch naming**：`feature/<short-description>`、`fix/<issue-id>` 等，保持可读。
- **提交信息 / Commit messages**：遵循 Conventional Commits，例如 `feat: add grooming smoothing filter`。
- **提交粒度 / Commit granularity**：保持逻辑完整、易于 review；避免将无关改动混入同一提交。

## Pull Request 要求 / Pull Request Checklist
- 说明问题背景、解决方案与测试情况；UI 变更附加截图或 GIF。
- 确认本地通过 `pytest`、`black`、`isort`、`flake8`、`mypy`。
- 更新相关文档（例如 README、docs/）与示例配置。
- 引用关联 issue：`Fixes #<id>` 或 `Refs #<id>`。
- 标注已知风险、后续计划或待办事项，帮助 reviewer 评估影响范围。

## 安全与配置 / Security & Configuration
- 不要提交真实凭据或敏感数据：`src/core/config/config.yaml` 仅作示例，真实配置请放在 `src/core/config/config.local.yaml` 或通过环境变量引用（可运行 `python scripts/init_config.py` 生成）。
- `data/`、`models/`、`logs/` 与 `config.local.yaml` 默认在 `.gitignore` 内，保持仓库清洁。
- 引入新依赖时提供 CPU 兼容路径，并在 PR 描述说明验证方式。

## 发布与变更日志 / Releases & Changelog
- 遵循语义化版本号（Major.Minor.Patch）。
- 当变更影响用户行为或接口时，更新 release note 或在 PR 中补充迁移说明。

如有疑问，欢迎在 issue 或 PR 讨论区沟通。感谢你的贡献！
