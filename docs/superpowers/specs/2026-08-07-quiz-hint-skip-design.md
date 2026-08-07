# 测试界面新增"提示"与"跳过"功能 Design

> 日期：2026-08-07
> 状态：已确认

## 目标

在拼写测试界面（`ui_quiz.py`）新增两个辅助按钮，提升使用体验：

1. **跳过**：遇到简单词汇直接标记为"已掌握"并跳过，不参与拼写判定。
2. **提示**：遇到难词时，按用户设置的方案提供帮助（揭示前 N% 字母 / 显示完整拼写 / 显示字母个数）。

## 需求澄清结论

- 跳过：直接把词设为 `mastered`（复习间隔 30 天），不再频繁出现。
- 提示：设置页单独开一页，提供三种方案（reveal / full / count）供用户选择。
- 提示比例：reveal 方案的揭示比例可选（20/30/40/50%），默认 30%。
- 用提示后答对：状态降级为 `blur`（不轻易升级）。
- 揭示取整：向上取整，最短至少揭示 1 个字母。

## 改动文件

### 1. `config.json` 新增键

```json
"hint_mode": "reveal",   // reveal | full | count
"hint_percent": 30
```

`main.py` 的 `load_config()` 默认值需同步补充：
```python
defaults = {"daily_new_words": 50, "ignore_case": True, "ignore_punct": False,
            "hint_mode": "reveal", "hint_percent": 30}
```

### 2. `quiz_logic.py` 新增纯函数 `reveal_mask`

纯加法，不动现有函数：

```python
def reveal_mask(word, percent):
    n = math.ceil(len(word) * percent / 100)
    return word[:n] + "_" * (len(word) - n)
```

- 边界：`len(word)==0` → 返回空串；percent 用 `min/max` 钳制到 `[0,100]`。
- 示例：`reveal_mask("apple", 30) == "ap___"`（5*0.3=1.5，向上取整=2）。

### 3. `ui_settings.py` 新增"提示设置"区块

在现有 `SettingsDialog` 中每日新词/大小写/标点之后新增：

- **提示方案**（下拉/单选）：`reveal`（揭示前 N% 字母）/ `full`（显示完整拼写）/ `count`（显示字母个数）
- **揭示比例**（下拉）：20% / 30% / 40% / 50%，仅当方案为 `reveal` 时启用
- `save()` 写回 `hint_mode`、`hint_percent`（复用现有 config.json 写入逻辑）

### 4. `ui_quiz.py` 新增两按钮与逻辑

- 底部布局：`[剩余 X 题] ... [提示] [跳过] [退出并保存]`
- `self.hint_used = set()`：记录用过提示的词 id
- `reveal_hint()`：按 `hint_mode` 生成提示文本，显示在独立标签 `hint_text`，标记该词已用提示
- `skip(item)`：`_save` 时 result=`"skip"` 走 mastered 直写；反馈"已标记为学会"；延时进下一题
- `submit()`：若 `item["id"] in self.hint_used` 且 result==`"correct"`，改写为 `"blur"` 传给 `_save`，但反馈文案显示"✓ 正确（借助提示）"
- `_save()` 扩展：`skip` 走独立 UPDATE（status=mastered, next_review_date=今天+30），其余走 `apply_result`
- 防误触：`entry` 处于 `disabled`（延时阶段）时，跳过/提示按钮不响应

### 提示文本生成

- `reveal`：`reveal_mask(word, percent)` 的结果，如 `ap___`
- `full`：完整拼写 `apple`
- `count`：`_ _ _ _`（len 个下划线，空格分隔）

## 状态与统计

- 跳过：计入已掌握（mastered+1），不计入 正确/模糊/错误 三档
- 提示答对：计入模糊（blur+1）
- 小结 `finish()`：正确/模糊/错误 不变，可补充"借助提示 N 词"

## 测试

- `quiz_logic.reveal_mask` → 无 GUI 纯函数测试：`("apple",30)=="ap___"`、`("book",50)=="bo__"`、空串、percent 越界钳制
- `tests/test_quiz_ui.py`（需 GUI）：`test_skip_marks_mastered`、`test_hint_used_correct_counts_as_blur`
- 改动后跑 `pytest tests/ -v` 验证

## 明确不做（YAGNI）

- 不改 `apply_result` 状态机签名
- 不做多级提示（逐字母递增）
- 不做跳过/提示的撤销