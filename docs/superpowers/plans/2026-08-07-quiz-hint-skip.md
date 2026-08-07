# 测试界面新增"提示"与"跳过"功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在拼写测试界面新增"跳过"（标记为已掌握）与"提示"（三种方案助答）两个辅助按钮，并在设置页提供提示方案配置。

**Architecture:** 不改 `quiz_logic.apply_result` 状态机签名。`skip` 在 `ui_quiz._save` 层走独立 mastered 直写分支；提示答对时在 `submit` 层把 result 改写为 `"blur"` 交给现有 `apply_result`。新增纯函数 `quiz_logic.reveal_mask(word, percent)` 供提示文本生成并可无 GUI 单测。配置经 `config.json` 新增 `hint_mode`/`hint_percent` 两键，由 `ui_settings` 读写、`ui_quiz` 读取。

**Tech Stack:** Python 3.12、Tkinter（ttk）、SQLite、pytest。

## Global Constraints

- 工作目录：`D:\GitHub项目\单词测试软件`
- Python >= 3.12，UI 文案全部用简体中文
- 代码不写注释（除非用户要求）
- 测试从仓库根目录运行 `pytest tests/ -v`（无 pytest.ini/pxproject.toml/conftest.py）
- `tests/test_quiz_ui.py` 需真实 GUI 环境（创建 `tk.Tk()`），无头会话会失败；其余逻辑测试可无 GUI
- 状态档位：`new` / `poor` / `blur` / `good` / `mastered`，复习间隔 1/3/7/30 天
- 配置默认值：`hint_mode="reveal"`、`hint_percent=30`
- 提示方案枚举：`reveal`（揭示前 N% 字母）/ `full`（显示完整拼写）/ `count`（显示字母个数）
- 揭示取整：`n = ceil(len*percent/100)`，向上取整，最短至少揭示 1 字母

---

### Task 1: `quiz_logic.reveal_mask` 纯函数 + 无 GUI 单测

**Files:**
- Modify: `quiz_logic.py`（顶部加 `import math`，末尾加 `reveal_mask`）
- Create: `tests/test_quiz_reveal.py`

**Interfaces:**
- Produces: `quiz_logic.reveal_mask(word: str, percent: int) -> str`
  - `word` 为英文单词，`percent` 为 0-100 整数
  - 返回 `word[:n] + "_" * (len(word)-n)`，其中 `n = max(0, min(len(word), ceil(len(word)*percent/100)))`（等价于 percent 钳制到 [0,100] 后向上取整）
  - 边界：`len(word)==0` → 返回空串

- [ ] **Step 1: 写失败的测试**

`tests/test_quiz_reveal.py`：
```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quiz_logic import reveal_mask

def test_reveal_30_percent_rounds_up():
    assert reveal_mask("apple", 30) == "ap___"

def test_reveal_50_percent():
    assert reveal_mask("book", 50) == "bo__"

def test_reveal_100_percent():
    assert reveal_mask("apple", 100) == "apple"

def test_reveal_0_percent():
    assert reveal_mask("apple", 0) == "_____"

def test_reveal_empty_word():
    assert reveal_mask("", 30) == ""

def test_reveal_percent_clamped():
    assert reveal_mask("apple", 200) == "apple"
    assert reveal_mask("apple", -10) == "_____"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_quiz_reveal.py -v`
Expected: FAIL with `ImportError: cannot import name 'reveal_mask'`

- [ ] **Step 3: 实现 `reveal_mask`**

在 `quiz_logic.py` 顶部加 `import math`，文件末尾追加：
```python
def reveal_mask(word, percent):
    p = max(0, min(100, percent))
    n = math.ceil(len(word) * p / 100)
    return word[:n] + "_" * (len(word) - n)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_quiz_reveal.py -v`
Expected: PASS（6 passed）

- [ ] **Step 5: 提交**

```bash
git add quiz_logic.py tests/test_quiz_reveal.py
git commit -m "feat: 新增提示揭示纯函数 reveal_mask"
```

---

### Task 2: 配置新增 `hint_mode` / `hint_percent`（config.json + main.py 默认值）

**Files:**
- Modify: `main.py:23`（`load_config()` 默认值字典）
- Modify: `config.json`（新增两键）

**Interfaces:**
- Consumes: 无
- Produces: `config.json` / `main.load_config()` 返回含 `hint_mode`（str）、`hint_percent`（int）的 dict

- [ ] **Step 1: 更新 `main.py` 默认值**

`main.py` 第 23 行改为：
```python
    defaults = {"daily_new_words": 50, "ignore_case": True, "ignore_punct": False,
                "hint_mode": "reveal", "hint_percent": 30}
```

- [ ] **Step 2: 更新 `config.json`**

改 `config.json`：
```json
{
  "daily_new_words": 30,
  "ignore_case": false,
  "ignore_punct": true,
  "hint_mode": "reveal",
  "hint_percent": 30
}
```

- [ ] **Step 3: 提交**

```bash
git add main.py config.json
git commit -m "feat: 配置新增提示方案与比例"
```

---

### Task 3: 设置页新增"提示设置"区块

**Files:**
- Modify: `ui_settings.py`（`__init__` 加控件，`save` 加字段）

**Interfaces:**
- Consumes: `config` dict（含 `hint_mode`、`hint_percent`）
- Produces: `config["hint_mode"]`、`config["hint_percent"]` 被更新并写回 config.json

**提示方案下拉选项值**：`reveal`（揭示前N%字母）、`full`（显示完整拼写照抄）、`count`（显示字母个数）
**揭示比例下拉选项值**：20、30、40、50（IntVar）

- [ ] **Step 1: 在 `__init__` 新增提示设置控件**

在 `ui_settings.py` 第 32 行（忽略标点 CheckBox 之后）新增：
```python
        tk.Label(rows, text="提示方案", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=4, column=0, sticky="w", pady=10)
        self.hint_mode_var = tk.StringVar(value=config.get("hint_mode", "reveal"))
        hint_mode_box = ttk.Combobox(rows, textvariable=self.hint_mode_var, state="readonly", width=14,
                                     values=["reveal", "full", "count"])
        hint_mode_box.grid(row=4, column=1, sticky="w")
        tk.Label(rows, text="揭示比例", font=font(14), bg=COLOR_BG, fg=COLOR_TEXT).grid(row=5, column=0, sticky="w", pady=10)
        self.hint_percent_var = tk.IntVar(value=int(config.get("hint_percent", 30)))
        percent_box = ttk.Combobox(rows, textvariable=self.hint_percent_var, state="readonly", width=14,
                                   values=[20, 30, 40, 50])
        percent_box.grid(row=5, column=1, sticky="w")
        ttk.Button(rows, text="保存", style="Primary.TButton", command=self.save).grid(row=6, column=0, columnspan=2, pady=(20, 0))
```

- [ ] **Step 2: 更新 `save()` 写回新字段**

将 `ui_settings.py` 第 33 行（原保存按钮）删除，保存按钮已移到 Step 1 的 row=6。更新 `save()`（第 36-42 行）为：
```python
    def save(self):
        self.config["daily_new_words"] = self.daily_var.get()
        self.config["ignore_case"] = self.case_var.get()
        self.config["ignore_punct"] = self.punct_var.get()
        self.config["hint_mode"] = self.hint_mode_var.get()
        self.config["hint_percent"] = self.hint_percent_var.get()
        config_path = os.path.join(os.path.dirname(self.db_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        self.destroy()
```

- [ ] **Step 3: 冒烟验证（手动）**

Run: `python main.py` → 点"设置"，确认出现"提示方案""揭示比例"，保存后 `config.json` 含新键且值正确。

- [ ] **Step 4: 提交**

```bash
git add ui_settings.py
git commit -m "feat: 设置页新增提示方案与比例"
```

---

### Task 4: 测试界面新增"提示"与"跳过"按钮及逻辑

**Files:**
- Modify: `ui_quiz.py`（`__init__` 加 `hint_used`、`_build_ui` 加按钮、加 `reveal_hint`/`skip` 方法、改 `submit`/`_save`/`finish`）
- Modify: `tests/test_quiz_ui.py`（加 `hint_mode`/`hint_percent` 到 fixture cfg，新增两个测试）

**Interfaces:**
- Consumes: `quiz_logic.reveal_mask(word, percent)`（Task 1）、`config["hint_mode"]`/`config["hint_percent"]`（Task 2）
- Produces: `QuizApp` 新增方法 `reveal_hint()`、`skip()`；`_save(item, result)` 支持 `result in ("correct","blur","wrong","skip")`

- [ ] **Step 1: `__init__` 加 `hint_used` 集合**

在 `ui_quiz.py` 第 19 行（`self.retry_done = set()` 之后）新增：
```python
        self.hint_used = set()
```

- [ ] **Step 2: `_build_ui` 底部行加两个按钮**

将 `ui_quiz.py` 第 101-102 行（`ttk.Button(... 退出并保存 ...).grid(...)`）替换为：
```python
        ttk.Button(bottom, text="提示", style="Secondary.TButton",
                   command=self.reveal_hint).grid(row=0, column=1, sticky="e", padx=(0, 8))
        ttk.Button(bottom, text="跳过", style="Secondary.TButton",
                   command=self.skip).grid(row=0, column=2, sticky="e", padx=(0, 8))
        ttk.Button(bottom, text="退出并保存", style="Secondary.TButton",
                   command=self.finish).grid(row=0, column=3, sticky="e")
```

- [ ] **Step 3: 新增 `reveal_hint` 与 `skip` 方法**

在 `ui_quiz.py` `submit` 方法前新增：
```python
    def reveal_hint(self):
        if self.entry.instate(["disabled"]):
            return
        item = self.queue[self.idx]
        word = item["word"]
        mode = self.config.get("hint_mode", "reveal")
        if mode == "full":
            text = word
        elif mode == "count":
            text = " ".join(["_"] * len(word))
        else:
            pct = int(self.config.get("hint_percent", 30))
            text = quiz_logic.reveal_mask(word, pct)
        self.hint_text.config(text=f"提示：{text}")
        self.hint_used.add(item["id"])

    def skip(self):
        if self.entry.instate(["disabled"]):
            return
        item = self.queue[self.idx]
        self.stats["skipped"] = self.stats.get("skipped", 0) + 1
        self._save(item, "skip")
        self.feedback.config(text=f"已标记为学会：{item['word']}", fg=COLOR_CORRECT)
        self.entry.config(state="disabled")
        self.idx += 1
        self.win.after(600, self._advance)
```

- [ ] **Step 4: `_build_ui` 增加 `hint_text` 标签**

在 `ui_quiz.py` 第 93-94 行（`self.hint` 标签之后）新增：
```python
        self.hint_text = tk.Label(inner, text="", font=font(16, bold=True), bg=COLOR_CARD, fg=COLOR_PRIMARY)
        self.hint_text.pack(pady=(0, 8))
```

并在 `_show_next`（第 131 行 `self.hint.config(...)` 之后）清除提示：
```python
        self.hint_text.config(text="")
```

- [ ] **Step 5: 修改 `submit` 处理提示答对改写**

将 `ui_quiz.py` 第 145-156 行逻辑改为（在 `_save` 前判断提示）：
```python
        result = quiz_logic.judge(user, item["word"], self.config.get("ignore_case", True),
                                  self.config.get("ignore_punct", False))
        used_hint = item["id"] in self.hint_used
        save_result = result
        if used_hint and result == "correct":
            save_result = "blur"
        self.stats[save_result] += 1
        self._save(item, save_result)
        if result == "correct":
            label = "✓ 正确（借助提示）" if used_hint else f"✓ 正确：{item['word']}"
            self.feedback.config(text=label, fg=COLOR_CORRECT)
        elif result == "blur":
            self.feedback.config(text=f"很接近！正确拼写是 {item['word']}", fg=COLOR_BLUR)
        else:
            self.feedback.config(text=f"✗ 错误，正确拼写是 {item['word']}", fg=COLOR_WRONG)
```

- [ ] **Step 6: 修改 `_save` 支持 `skip`**

将 `ui_quiz.py` 第 114-121 行的 `_save` 改为：
```python
    def _save(self, item, result):
        if result == "skip":
            nrd = (date.today() + timedelta(days=quiz_logic.REVIEW_INTERVALS["mastered"])).isoformat()
            self.conn.execute(
                "UPDATE word_state SET status='mastered', next_review_date=?, last_result_date=? "
                "WHERE book_id=? AND word_id=?",
                (nrd, self.today, self.book["id"], item["id"]))
            self.conn.commit()
            return
        st = self._state(item)
        state = dict(st) if st else {"status": "new", "wrong_count": 0, "review_count": 0,
                                     "priority": 0, "first_quiz_date": None}
        new = quiz_logic.apply_result(state, result, self.today)
        self.conn.execute(
            "UPDATE word_state SET status=?, wrong_count=?, review_count=?, priority=?, "
            "first_quiz_date=?, last_result_date=?, next_review_date=? WHERE book_id=? AND word_id=?",
            (new["status"], new["wrong_count"], new["review_count"], new["priority"],
             new.get("first_quiz_date"), new.get("last_result_date"), new.get("next_review_date"),
             self.book["id"], item["id"]))
        self.conn.commit()
```

需在 `ui_quiz.py` 顶部 `from datetime import date` 改为 `from datetime import date, timedelta`。

- [ ] **Step 7: 更新 fixture cfg 并新增测试**

`tests/test_quiz_ui.py` 第 26 行 cfg 改为：
```python
    cfg = {"daily_new_words": 50, "ignore_case": True, "ignore_punct": False,
           "hint_mode": "reveal", "hint_percent": 30}
```

文件末尾新增：
```python
def test_skip_marks_mastered(quiz_app):
    qa = quiz_app
    item = qa.queue[qa.idx]
    qa._save(item, "skip")
    row = qa.conn.execute(
        "SELECT status FROM word_state WHERE book_id=? AND word_id=?",
        (qa.book["id"], item["id"])).fetchone()
    assert row[0] == "mastered"


def test_hint_used_correct_counts_as_blur(quiz_app):
    qa = quiz_app
    item = qa.queue[qa.idx]
    qa.hint_used.add(item["id"])
    qa.entry.insert(0, item["word"])
    qa.submit()
    assert qa.stats["blur"] == 1
    row = qa.conn.execute(
        "SELECT status FROM word_state WHERE book_id=? AND word_id=?",
        (qa.book["id"], item["id"])).fetchone()
    assert row[0] == "blur"
```

- [ ] **Step 8: 运行测试验证**

Run: `pytest tests/test_quiz_ui.py tests/test_quiz_reveal.py -v`（需 GUI 环境）
Expected: 全部 PASS

- [ ] **Step 9: 提交**

```bash
git add ui_quiz.py tests/test_quiz_ui.py
git commit -m "feat: 测试界面新增提示与跳过功能"
```

---

### Task 5: 全量回归验证

**Files:**
- 无新增/修改

- [ ] **Step 1: 运行全部测试**

Run: `pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 2: 手动冒烟（可选）**

Run: `python main.py` → 开始学习 → 点"提示"看三种方案效果、点"跳过"看状态变为已掌握、用提示后答对看状态为模糊。

- [ ] **Step 3: 提交收尾**

```bash
git add -A
git commit -m "chore: 提示与跳过功能全量验证通过"
```

---

## Self-Review 记录

- **Spec 覆盖**：config 键（spec §改动文件1）→ Task 2；reveal_mask（§2）→ Task 1；设置页（§3）→ Task 3；测试界面按钮与逻辑（§4）→ Task 4；状态与统计（§状态与统计）→ Task 4；测试（§测试）→ Task 1/4；YAGNI（§明确不做）→ 未实现撤销/多级提示/改 apply_result。
- **占位符扫描**：所有代码块为完整实现，无 TBD/TODO。
- **类型一致性**：`reveal_mask(word, percent) -> str` 在 Task 1 定义、Task 4 Step 3 使用；`_save(item, result)` 支持 `"skip"` 在 Task 4 Step 3 调用、Step 6 实现；`hint_mode`/`hint_percent` 键名在 Task 2 定义、Task 3/4 读取一致。`REVIEW_INTERVALS["mastered"]==30` 与 Spec 一致。