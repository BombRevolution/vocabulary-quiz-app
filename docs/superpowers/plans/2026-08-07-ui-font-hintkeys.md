# 全局字号放大、提示方案中文化与快捷键功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全局字号放大至 1.3 倍（窗口不变）、设置页提示方案下拉中文化（存储值不变）、新增跳过/提示快捷键（默认 Ctrl+D/Ctrl+空格，可配置）。

**Architecture:** `ui_theme.font()` 引入 `FONT_SCALE=1.3` 全局系数，所有 `font(N)` 调用自动放大。提示方案下拉显示中文标签、存储值 `hint_mode` 不变，`ui_quiz` 零改动。快捷键存 `config.json`（`key_skip`/`key_hint`，Tk event 格式），设置页按键捕获输入框配置，测试界面绑定到输入框 `self.entry`。

**Tech Stack:** Python 3.12、Tkinter（ttk）、pytest。

## Global Constraints

- 工作目录：`D:\GitHub项目\单词测试软件`
- Python >= 3.12，UI 文案全部用简体中文
- 代码不写注释（除非用户要求）
- 测试从仓库根目录运行 `pytest tests/ -v`
- `tests/test_quiz_ui.py` 需真实 GUI 环境，无头会话会失败；其余逻辑测试可无 GUI
- 全局字号系数 `FONT_SCALE = 1.3`（`round(N*1.3)`）
- 窗口尺寸**不变**（设置页 560x420、测试界面 900x680、主界面 1100x760、导入 900x660 均保持）
- 提示方案存储值：`reveal` / `full` / `count`（不变）
- 快捷键默认值：`key_skip="<Control-d>"`、`key_hint="<Control-space>"`（Tk event 序列格式）
- 设置页窗口高度微调 `560x420` → `560x560` 容纳新增行，压缩 `pady` 避免裁切

---

### Task 1: 全局字号 1.3 倍

**Files:**
- Modify: `ui_theme.py:21-25`（`font()` 函数）

**Interfaces:**
- Produces: `ui_theme.font(size: int, bold: bool = False) -> tuple`，返回 `(FONT_FAMILY, round(size*1.3), ["bold"])`；新增模块常量 `FONT_SCALE = 1.3`

- [ ] **Step 1: 修改 `font()` 引入全局系数**

在 `ui_theme.py` 顶部（`FONT_FAMILY` 定义后）加常量，并修改 `font()`：
```python
FONT_FAMILY = "Microsoft YaHei UI"
FONT_SCALE = 1.3
```
```python
def font(size, bold=False):
    size = int(round(size * FONT_SCALE))
    name = (FONT_FAMILY, size)
    if bold:
        name = (FONT_FAMILY, size, "bold")
    return name
```

- [ ] **Step 2: 验证**

Run: `python -c "from ui_theme import font; assert font(20)==('Microsoft YaHei UI',26); assert font(14)==('Microsoft YaHei UI',18); assert font(11,True)==('Microsoft YaHei UI',14,'bold'); print('OK')"`
Expected: `OK`（20*1.3=26、14*1.3=18.2→18、11*1.3=14.3→14）

- [ ] **Step 3: 提交**

```bash
git add ui_theme.py
git commit -m "feat: 全局字号放大至1.3倍"
```

---

### Task 2: config 新增快捷键默认值

**Files:**
- Modify: `main.py:23-24`（`load_config()` 默认值）
- Modify: `config.json`（新增两键）

**Interfaces:**
- Consumes: 无
- Produces: `load_config()` 返回 dict 新增 `key_skip`（str）、`key_hint`（str）；`config.json` 含两键

- [ ] **Step 1: 更新 `main.py` 默认值**

`main.py` 第 23-24 行改为：
```python
    defaults = {"daily_new_words": 50, "ignore_case": True, "ignore_punct": False,
                "hint_mode": "reveal", "hint_percent": 30,
                "key_skip": "<Control-d>", "key_hint": "<Control-space>"}
```

- [ ] **Step 2: 更新 `config.json`**

改 `config.json`：
```json
{
  "daily_new_words": 30,
  "ignore_case": false,
  "ignore_punct": true,
  "hint_mode": "reveal",
  "hint_percent": 30,
  "key_skip": "<Control-d>",
  "key_hint": "<Control-space>"
}
```

- [ ] **Step 3: 提交**

```bash
git add main.py config.json
git commit -m "feat: 配置新增跳过/提示快捷键默认值"
```

---

### Task 3: 设置页——提示方案中文 + 快捷键设置 + 布局调整

**Files:**
- Modify: `ui_settings.py`（`__init__`、`save()`、新增 `_capture/open` 辅助与 `build_event_sequence` 纯函数）

**Interfaces:**
- Consumes: `config` dict（含 `hint_mode`、`hint_percent`、`key_skip`、`key_hint`）
- Produces: `ui_settings.HINT_MODE_LABELS`（dict）、`ui_settings.HINT_MODE_LABELS_REV`（dict）、`ui_settings.build_event_sequence(state: int, keysym: str) -> str`；`config["hint_mode"]`/`config["key_skip"]`/`config["key_hint"]` 被更新并写回 config.json

**`build_event_sequence` 纯函数**（修饰键位：Shift=1, Lock=2, Control=4, Mod1/Alt=8）：
```python
def build_event_sequence(state, keysym):
    mods = []
    if state & 0x4:
        mods.append("Control")
    if state & 0x1:
        mods.append("Shift")
    if state & 0x8:
        mods.append("Alt")
    if not mods:
        return ""
    return "<" + "-".join(mods + [keysym]) + ">"
```
- 无修饰键（`mods` 空）返回 `""`（拒绝纯字母/数字键，避免干扰打字）
- 例：state=5(Control+Shift)、keysym="s" → `<Control-Shift-s>`；state=0、keysym="a" → `""`

- [ ] **Step 1: 新增常量与纯函数**

在 `ui_settings.py` 顶部（`import` 之后）新增：
```python
HINT_MODE_LABELS = {
    "reveal": "揭示前N%字母",
    "full": "显示完整拼写照抄",
    "count": "显示字母个数",
}
HINT_MODE_LABELS_REV = {v: k for k, v in HINT_MODE_LABELS.items()}


def build_event_sequence(state, keysym):
    mods = []
    if state & 0x4:
        mods.append("Control")
    if state & 0x1:
        mods.append("Shift")
    if state & 0x8:
        mods.append("Alt")
    if not mods:
        return ""
    return "<" + "-".join(mods + [keysym]) + ">"
```

- [ ] **Step 2: `__init__` 提示方案改中文**

将 `ui_settings.py` 第 34-36 行改为（values 用中文标签，初始值映射）：
```python
        initial_mode = config.get("hint_mode", "reveal")
        self.hint_mode_var = tk.StringVar(value=HINT_MODE_LABELS[initial_mode])
        hint_mode_box = ttk.Combobox(rows, textvariable=self.hint_mode_var, state="readonly", width=18,
                                     values=list(HINT_MODE_LABELS.values()))
```

- [ ] **Step 3: `__init__` 新增快捷键两行**

将保存按钮行（第 43 行）上移，在其前插入快捷键两行（row=6、row=7，保存按钮移到 row=8），并新增捕获辅助方法。新增控件行：
```python
        tk.Label(rows, text="跳过快捷键", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=6, column=0, sticky="w", pady=6)
        self.skip_key_entry = ttk.Entry(rows, width=18)
        self.skip_key_entry.insert(0, config.get("key_skip", "<Control-d>"))
        self.skip_key_entry.grid(row=6, column=1, sticky="w")
        self.skip_key_entry.bind("<KeyPress>", lambda e: self._capture_key(e, self.skip_key_entry))
        tk.Label(rows, text="提示快捷键", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=7, column=0, sticky="w", pady=6)
        self.hint_key_entry = ttk.Entry(rows, width=18)
        self.hint_key_entry.insert(0, config.get("key_hint", "<Control-space>"))
        self.hint_key_entry.grid(row=7, column=1, sticky="w")
        self.hint_key_entry.bind("<KeyPress>", lambda e: self._capture_key(e, self.hint_key_entry))
        ttk.Button(rows, text="保存", style="Primary.TButton", command=self.save).grid(row=8, column=0, columnspan=2, pady=(20, 0))
```

- [ ] **Step 4: 新增 `_capture_key` 辅助方法**

在 `ui_settings.py` `save` 方法前新增：
```python
    def _capture_key(self, event, entry):
        if event.keysym == "Escape":
            return
        seq = build_event_sequence(event.state, event.keysym)
        if seq:
            entry.delete(0, "end")
            entry.insert(0, seq)
        return "break"
```

- [ ] **Step 5: 修改 `save()` 处理中文映射与快捷键校验**

将 `save()` 改为：
```python
    def save(self):
        self.config["daily_new_words"] = self.daily_var.get()
        self.config["ignore_case"] = self.case_var.get()
        self.config["ignore_punct"] = self.punct_var.get()
        self.config["hint_mode"] = HINT_MODE_LABELS_REV[self.hint_mode_var.get()]
        self.config["hint_percent"] = self.hint_percent_var.get()
        skip_key = self.skip_key_entry.get().strip() or "<Control-d>"
        hint_key = self.hint_key_entry.get().strip() or "<Control-space>"
        if skip_key == hint_key:
            messagebox.showwarning("快捷键冲突", "跳过与提示快捷键不能相同，请重新设置")
            return
        self.config["key_skip"] = skip_key
        self.config["key_hint"] = hint_key
        config_path = os.path.join(os.path.dirname(self.db_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        self.destroy()
```

需在 `ui_settings.py` 顶部 `from tkinter import ttk` 行改为 `from tkinter import ttk, messagebox`。

- [ ] **Step 6: 布局调整——窗口高度与间距**

将 `ui_settings.py` 第 15 行 `self.geometry("560x420")` 改为 `self.geometry("560x560")`。将各行的 `pady=10` 压缩为 `pady=6`（第 23/27/30/33/38 行），标题 `pady=(0,20)` 可保留。

- [ ] **Step 7: 验证**

Run: `python -c "import ast; ast.parse(open('ui_settings.py',encoding='utf-8').read()); from ui_settings import build_event_sequence, HINT_MODE_LABELS, HINT_MODE_LABELS_REV; assert build_event_sequence(5,'s')=='<Control-Shift-s>'; assert build_event_sequence(0,'a')==''; assert HINT_MODE_LABELS_REV['揭示前N%字母']=='reveal'; print('OK')"`
Expected: `OK`

- [ ] **Step 8: 提交**

```bash
git add ui_settings.py
git commit -m "feat: 设置页提示方案中文、快捷键配置与布局调整"
```

---

### Task 4: 测试界面快捷键绑定

**Files:**
- Modify: `ui_quiz.py`（`__init__` 加绑定）
- Modify: `tests/test_quiz_ui.py`（fixture cfg 加 `key_skip`/`key_hint`，新增测试）

**Interfaces:**
- Consumes: `config["key_skip"]`、`config["key_hint"]`（Task 2）
- Produces: `QuizApp` 输入框 `self.entry` 绑定跳过快键（调用 `self.skip()`）与提示快键（调用 `self.reveal_hint()`）

- [ ] **Step 1: `__init__` 绑定快捷键**

在 `ui_quiz.py` `_build_ui` 之后、`_show_next` 之前（`__init__` 内约第 40 行）新增：
```python
        self.entry.bind(self.config.get("key_skip", "<Control-d>"), lambda e: self.skip())
        self.entry.bind(self.config.get("key_hint", "<Control-space>"), lambda e: self.reveal_hint())
```

- [ ] **Step 2: 更新 fixture cfg**

`tests/test_quiz_ui.py:26` cfg 改为：
```python
    cfg = {"daily_new_words": 50, "ignore_case": True, "ignore_punct": False,
           "hint_mode": "reveal", "hint_percent": 30,
           "key_skip": "<Control-d>", "key_hint": "<Control-space>"}
```

- [ ] **Step 3: 新增测试**

`tests/test_quiz_ui.py` 末尾新增：
```python
def test_skip_hotkey_bound(quiz_app):
    qa = quiz_app
    qa.win.update_idletasks()
    qa.entry.event_generate("<Control-d>")
    qa.win.update_idletasks()
    assert qa.stats.get("skipped", 0) == 1
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/test_quiz_ui.py -v`（需 GUI 环境）
Expected: 全部 PASS（含新测试）

- [ ] **Step 5: 提交**

```bash
git add ui_quiz.py tests/test_quiz_ui.py
git commit -m "feat: 测试界面绑定跳过/提示快捷键"
```

---

### Task 5: 全量回归验证

**Files:**
- 无新增/修改

- [ ] **Step 1: 运行全部测试**

Run: `pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 2: 手动冒烟（可选）**

Run: `python main.py` → 观察字号变大；设置页看提示方案中文下拉、快捷键捕获；测试界面按 Ctrl+D 跳过、Ctrl+空格提示。

- [ ] **Step 3: 提交收尾**

```bash
git add -A
git commit -m "chore: 字号/中文/快捷键功能全量验证通过"
```

---

## Self-Review 记录

- **Spec 覆盖**：字号（spec §1）→ Task 1；config 默认值（§3）→ Task 2；提示方案中文+快捷键+布局（§2）→ Task 3；快捷键绑定（§4）→ Task 4；测试（§测试）→ Task 3 纯函数验证 + Task 4 GUI 测试 + Task 5 回归。
- **占位符扫描**：所有代码块为完整实现，无 TBD/TODO。
- **类型一致性**：`build_event_sequence(state:int, keysym:str)->str` 在 Task 3 Step 1 定义、Step 4 使用；`HINT_MODE_LABELS(normal)↔HINT_MODE_LABELS_REV(inverse)` 在 Task 3 Step 1 定义、Step 2/5 使用；`key_skip`/`key_hint` 键名在 Task 2 定义、Task 3/4 读取一致。