# 全局字号放大、提示方案中文化与快捷键功能 Design

> 日期：2026-08-07
> 状态：已确认

## 目标

1. 全局字号放大至 1.3 倍（窗口尺寸不变，控件/文字放大）。
2. 设置页"提示方案"下拉显示中文标签，存储值不变。
3. 新增"跳过/提示"快捷键，默认可改，设置页按键捕获配置。

## 现状

- `ui_theme.py` 的 `font(N)` 为全局字号函数，被 `ui_quiz.py`/`ui_settings.py`/`ui_main.py`/`ui_import.py` 全部调用。
- 设置页提示方案下拉（`ui_settings.py:35-36`）`values=["reveal","full","count"]` 显示英文；`hint_mode` 存储值即这些英文键，`ui_quiz.py` 依赖。
- 测试界面目前仅回车 `submit`，无快捷键绑定。
- 设置页为固定窗口 `geometry("560x420")`、`resizable(False,False)`。

## 需求澄清结论

- 字号：全局 1.3 倍，窗口尺寸不变。
- 提示方案：下拉显示中文，存储 `hint_mode` 值不变（reveal/full/count）。
- 快捷键：存 `config.json`，默认可改；设置页按键捕获输入框配置；绑定输入框聚焦时生效；保存时冲突检测。
- 设置页固定窗口 + 1.3 倍字号 + 新增 2 行快捷键：采用"高度微调 + 压缩间距"避免控件被裁切。

## 改动文件

### 1. `ui_theme.py` — 全局字号 1.3 倍

`font()` 引入全局缩放系数：

```python
FONT_SCALE = 1.3

def font(size, bold=False):
    size = int(round(size * FONT_SCALE))
    name = (FONT_FAMILY, size)
    if bold:
        name = (FONT_FAMILY, size, "bold")
    return name
```

- 所有 `font(N)` 调用点自动放大（含 `apply_theme` 内 `fb = font(14)`，即 ttk 按钮/输入框/下拉/Spinbox 基础字号一并放大）。
- `CheckBox` 已按 DPI 自适应，无需改。
- 窗口尺寸不变（`ui_settings.py` 560x420、`ui_quiz.py` 900x680、`ui_main.py` 1100x760、`ui_import.py` 900x660 均保持）。

### 2. `ui_settings.py` — 提示方案中文 + 快捷键设置 + 布局

**a) 提示方案中文显示**（存储值不变）：

```python
HINT_MODE_LABELS = {
    "reveal": "揭示前N%字母",
    "full": "显示完整拼写照抄",
    "count": "显示字母个数",
}
```

- 下拉 `values` 用中文标签列表。
- `__init__`：`self.hint_mode_var` 初始化为 `HINT_MODE_LABELS[config["hint_mode"]]`（映射存储值→中文）。
- `save()`：`self.config["hint_mode"]` 写回 `HINT_MODE_LABELS` 的逆映射（中文→存储值）。

```python
HINT_MODE_LABELS_REV = {v: k for k, v in HINT_MODE_LABELS.items()}
```

**b) 快捷键设置**（新增 2 行，列于揭示比例之后）：

- `key_skip` 捕获输入框 + 标签"跳过快捷键"
- `key_hint` 捕获输入框 + 标签"提示快捷键"
- 捕获逻辑：`entry.bind("<KeyPress>", ...)`，从 `event.state & 0xf` 判断修饰键（Command/Shift/Lock/Control/Alt），组装 Tk event 序列（如 `<Control-d>`、`<Control-space>`、`<Control-Shift-s>`）；`Escape` 取消捕获、按钮"清除"回默认。
- 保存时校验：`key_skip == key_hint` 时 `messagebox.showwarning` 拒绝；空值回退默认。

**c) 布局**：窗口高度 `560x420` → `560x560`（微调高容纳新增行），适当压缩 `pady`（如 10→6）避免裁切。

### 3. `main.py` — config 默认值补充

`load_config()` 默认值新增：

```python
defaults = {"daily_new_words": 50, "ignore_case": True, "ignore_punct": False,
            "hint_mode": "reveal", "hint_percent": 30,
            "key_skip": "<Control-d>", "key_hint": "<Control-space>"}
```

### 4. `ui_quiz.py` — 快捷键绑定

`__init__` 中读取 `config["key_skip"]`/`config["key_hint"]`，绑定到输入框 `self.entry`：

```python
ks = self.config.get("key_skip", "<Control-d>")
kh = self.config.get("key_hint", "<Control-space>")
self.entry.bind(ks, lambda e: self.skip())
self.entry.bind(kh, lambda e: self.reveal_hint())
```

- 绑定在 `self.entry` 上，输入框聚焦时生效，组合键不干扰普通打字。
- `skip()`/`reveal_hint()` 已内置 `entry.instate(["disabled"])` 防误触，无需额外处理。
- 现有 `<Return>` 绑定 `submit` 保持不变。

## 状态与逻辑影响

- `hint_mode` 存储值不变，`ui_quiz.reveal_hint()` 零改动。
- 快捷键仅新增绑定，不改判定/状态/统计逻辑。
- 字号仅视觉放大，不改任何业务逻辑。

## 测试

- 快捷键绑定与捕获逻辑可抽成纯函数便于无 GUI 单测（如 `build_event_sequence(state, keysym) -> str`，放 `ui_settings` 或 `quiz_logic`）。
- `tests/test_quiz_ui.py`（需 GUI）：验证 `qa.entry` 上跳过快键绑定存在、触发 `skip()` 后状态为 mastered。
- 字号/中文显示为纯 UI，无自动化测试，手动冒烟验证。
- 改动后跑 `pytest tests/ -v` 确认无回归。

## 明确不做（YAGNI）

- 不改窗口尺寸（用户明确窗口不变）。
- 不改 `hint_mode` 存储值。
- 不做快捷键的全局/主界面绑定（仅测试界面输入框）。
- 不改 `CheckBox` 尺寸（已 DPI 自适应）。