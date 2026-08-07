# AGENTS.md

## 项目概述

基于本地词库的桌面单词拼写测试与复习软件。Tkinter + SQLite，Python 3.12+。UI 文案全部使用简体中文。

## 常用命令

- 运行：`python main.py`（需 Python 3.12+，先 `pip install -r requirements.txt`）
- 测试：`pytest tests/ -v`
  - 无 `pytest.ini`/`pyproject.toml`/`conftest.py`；每个测试文件顶部通过 `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` 手动加根目录到路径，因此必须从仓库根目录运行 pytest。
- 打包：PyInstaller（`--onefile --add-data` 内置词库 `雅思词汇9400词EXCEL词-乱序版.xls`）。`.spec`、`build/`、`dist/` 均被 gitignore，产出 exe 名为 `单词拼写测试.exe`。

## 架构

分层清晰，核心逻辑与 UI 分离：

- `database.py` — 全部 SQLite 访问（词库/词/进度/设置），表：books, words, word_state, daily_log, settings
- `importer.py` — Excel/CSV 解析与导入（pandas），从释义正则提取词性
- `quiz_logic.py` — 纯函数：`judge`（判定 correct/blur/wrong）、`apply_result`（状态迁移）、`build_queue`（出题队列）、`next_review_date`。这部分可单元测试，改动时优先改这里
- `ui_main.py` / `ui_quiz.py` / `ui_import.py` / `ui_settings.py` / `ui_theme.py` — 仅做展示与交互，不写业务逻辑
- `main.py` — 入口；用 `resource_path()` 兼容 PyInstaller 的 `sys.frozen`/`_MEIPASS` 场景

## 关键约定

- **代码不写注释**（除非用户明确要求）。
- 数据文件 `vocab.db` 与 `config.json` 生成在根目录，均被 gitignore；测试用临时/独立 db，勿用真实 `vocab.db`。
- 内置词库 `雅思词汇9400词EXCEL词-乱序版.xls` 为 3 列（序号/单词/中文释义），导入时 `word_col=1, meaning_col=2`。
- 词库状态档位：`new` / `poor` / `blur` / `good` / `mastered`，复习间隔 1/3/7/30 天（见 `quiz_logic.py` 的 `REVIEW_INTERVALS`）。
- 判定规则受 `config.json` 中 `ignore_case`、`ignore_punct`、`daily_new_words` 控制。

## 测试注意

- `tests/test_quiz_ui.py` 会创建真实 `tk.Tk()` 窗口并通过 monkeypatch 屏蔽 messagebox。它**需要可用 GUI/显示环境**，在无头会话（CI/SSH）中会失败；其余数据库/逻辑测试可无 GUI 运行。
- 修改 `quiz_logic.py` 或 `database.py` 后务必跑 `pytest tests/ -v` 验证。

## 设计文档

`docs/superpowers/` 下有原始 spec 与 implement plan（`plans/2026-08-07-word-quiz.md`），记录了各模块接口签名，改动前可参考。