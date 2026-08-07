# AGENTS.md

## 项目概述

基于本地词库的桌面单词拼写测试与复习软件。Tkinter + SQLite，Python 3.12+。UI 文案全部使用简体中文。

## 常用命令

- 运行：`python main.py`（需 Python 3.12+，先 `pip install -r requirements.txt`）
- 测试：`pytest tests/ -v`
  - 无 `pytest.ini`/`pyproject.toml`/`conftest.py`；每个测试文件顶部通过 `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` 手动加根目录到路径，因此必须从仓库根目录运行 pytest。
- 打包：PyInstaller `--onefile`，**不含内置词库**（`雅思词汇9400词EXCEL词-乱序版.xls` 不在仓库，`ensure_builtin` 检测到缺失即跳过）。`.spec`、`build/`、`dist/` 均被 gitignore，产出 exe 名为 `单词拼写测试.exe`（当前版本 v1.0.1，打包覆盖 `dist/` 旧 exe）。

## GitHub 发布注意

- **release 附件文件名不支持中文**：上传中文名的 exe 会被 GitHub 回退为 `default.exe`。release 附件统一用 ASCII 名 `word-quiz-app.exe`（与 v1.0.0 一致）；本地 `dist/` 内 exe 仍叫 `单词拼写测试.exe`。
- **release body 必须用 UTF-8 发送**：PowerShell `Invoke-RestMethod` 提交 JSON 时须 `[System.Text.Encoding]::UTF8.GetBytes($json)`，否则中文被存成 `?` 乱码（v1.0.0 曾踩坑，v1.0.1 已用正确编码）。
- **创建 release/上传附件无 MCP 工具、无 `gh` CLI**：用 `git credential fill`（GCM 存有 GitHub 凭据）取 token，再调 GitHub REST API（`POST /releases` 创建、`POST {upload_url}?name=` 上传、`PATCH /releases/assets/{id}` 改名）。
- tag ≠ release：推 tag 不会出现在 Releases 页，需单独创建 release。

## 架构

分层清晰，核心逻辑与 UI 分离：

- `database.py` — 全部 SQLite 访问（词库/词/进度/设置），表：books, words, word_state, daily_log, settings
- `importer.py` — Excel/CSV 解析与导入（pandas），从释义正则提取词性
- `quiz_logic.py` — 纯函数：`judge`（判定 correct/blur/wrong）、`apply_result`（状态迁移）、`build_queue`（出题队列）、`next_review_date`。这部分可单元测试，改动时优先改这里
- `ui_main.py` / `ui_quiz.py` / `ui_import.py` / `ui_settings.py` / `ui_theme.py` — 仅做展示与交互，不写业务逻辑
- `ui_wrongwords.py` — 错题整理弹窗；`pdf_export.py` — 不熟练词导出 PDF（PyMuPDF）
- `main.py` — 入口；用 `resource_path()` 兼容 PyInstaller 的 `sys.frozen`/`_MEIPASS` 场景

## 关键约定

- **代码不写注释**（除非用户明确要求）。
- 数据文件 `vocab.db` 与 `config.json` 生成在根目录，均被 gitignore；测试用临时/独立 db，勿用真实 `vocab.db`。
- 内置词库 `雅思词汇9400词EXCEL词-乱序版.xls` 为 3 列（序号/单词/中文释义），导入时 `word_col=1, meaning_col=2`。
- 词库状态档位：`new` / `poor` / `blur` / `good` / `mastered`，复习间隔 1/3/7/30 天（见 `quiz_logic.py` 的 `REVIEW_INTERVALS`）。
- 判定规则受 `config.json` 中 `ignore_case`、`ignore_punct`、`daily_new_words` 控制。
- 提示/跳过功能（`ui_quiz.py`）：`skip` 直接把词置为 `mastered`（next_review_date=今天+30，不计入 correct/blur/wrong 统计，走 `_save` 的独立分支）；`reveal_hint` 按 `config` 的 `hint_mode`（reveal/full/count）与 `hint_percent` 生成提示。用提示后：答对→`blur`、答错→`poor`，且该词不能再跳过（`skip` 对 `hint_used` 中的词直接 return，跳过按钮变灰）。`quiz_logic.reveal_mask(word, percent)` 为纯函数，可无 GUI 单测。
- 全局字号用 `ui_theme.FONT_SCALE = 1.3` 控制（`font(N)` 返回 `round(N*1.3)`）。窗口尺寸自适应：主/测试界面 `maximize()`，弹窗用 `ui_theme.fit_and_center(win,w,h)`（内部纯函数 `clamp_geometry(w,h,sw,sh,margin)` 按屏幕钳制居中，`tests/test_clamp_geometry.py` 覆盖 1080p/2K/2.5K、16:9/16:10）。
- 设置界面输入控件用紧凑 ttk 样式 `S.TEntry`/`S.TCombobox`（padding=2）+ `font(12)`，数字框约为原来 1/4、其余约 1/2；`main.py` 默认 `daily_new_words=200`。
- 提示方案在设置页下拉显示中文（`ui_settings.HINT_MODE_LABELS`），存储值 `hint_mode` 仍为 reveal/full/count（`HINT_MODE_LABELS_REV` 逆映射写回）。
- 快捷键：`config` 的 `key_skip`/`key_hint`（Tk event 序列，默认 `<Control-d>`/`<Control-space>`），设置页按键捕获输入框配置，`ui_quiz` 绑定到输入框 `self.entry`。`ui_settings.build_event_sequence(state, keysym)` 为纯函数（无修饰键返回 `""`），`_capture_key` 过滤纯修饰键 keysym 防止无效序列。
- 错题整理与导出 PDF（`ui_main.py` 的"整理错题"按钮 → `ui_wrongwords.py` 弹窗 → `pdf_export.py`）：不熟练词定义 = `word_state.status IN ('poor','blur')`，由 `database.list_unmastered_words(conn, book_id)` 查询（按 priority 降序）。`pdf_export.export_unmastered_pdf(book_name, words, out_path)` 用 PyMuPDF（`fitz`）生成卡片式 PDF，中文用黑体 `C:\Windows\Fonts\simhei.ttf`（`CN_FONT="simhei.ttf"`，路径由 `_font_path` 拼 `WINDIR`）。导出 PDF 依赖 `fitz`（已装，requirements 已加 `PyMuPDF`）。

## 测试注意

- `tests/test_quiz_ui.py` 会创建真实 `tk.Tk()` 窗口并通过 monkeypatch 屏蔽 messagebox。它**需要可用 GUI/显示环境**，在无头会话（CI/SSH）中会失败；其余数据库/逻辑测试可无 GUI 运行。
- 修改 `quiz_logic.py` 或 `database.py` 后务必跑 `pytest tests/ -v` 验证。

## 设计文档

`docs/superpowers/` 下有原始 spec 与 implement plan（`plans/2026-08-07-word-quiz.md`），记录了各模块接口签名，改动前可参考。