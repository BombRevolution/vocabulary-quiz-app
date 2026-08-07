# 错题整理与导出 PDF 功能 Design

> 日期：2026-08-07
> 状态：已确认

## 目标

把当前词库中"不熟练"的词整理出来，一方面在软件内部查看，另一方面导出为 PDF 方便打印（仿照用户提供的考研英语生词本 PDF 排版风格）。

## 需求澄清结论

- **不熟练词定义**：`word_state.status IN ('poor','blur')`（不会/模糊），已掌握（mastered）、已会（good）、未学（new）均排除。
- **功能形态**：主界面新增"整理错题"按钮 → 弹窗内查看不熟练词完整列表 + 底部"导出 PDF"按钮。
- **PDF 内容**：用词库现有数据（单词 + 词性 + 中文释义），仿生词本卡片式排版。词库无音标/英文释义/搭配字段，这些不显示。
- **PDF 生成**：用 PyMuPDF（`fitz`），已安装，中文用 `C:\Windows\Fonts\msyh.ttc`（微软雅黑），英文用内置字体。

## 现状

- `word_state` 表含 `status`、`wrong_count`、`priority`、`last_result_date` 等字段。
- `words` 表含 `word`、`meaning`（中文释义）、`pos`（词性）。
- 主界面 `ui_main.py` 左侧按钮列有"导入词库/重置进度/删除词库/设置"，右侧已有"近期错题"和"今日待复习"两个卡片（仅显示前 8 个）。
- PyMuPDF 已安装（`fitz`），`msyh.ttc` 中文渲染已验证正常。

## 改动文件

### 1. `database.py` — 新增查询函数

```python
def list_unmastered_words(conn, book_id):
    rows = conn.execute(
        "SELECT w.word, w.meaning, w.pos FROM words w "
        "JOIN word_state ws ON ws.word_id=w.id AND ws.book_id=w.book_id "
        "WHERE w.book_id=? AND ws.status IN ('poor','blur') "
        "ORDER BY ws.priority DESC, ws.last_result_date DESC",
        (book_id,)).fetchall()
    return [dict(r) for r in rows]
```

返回 list[dict]，每项含 `word`/`meaning`/`pos`。

### 2. `ui_main.py` — 新增"整理错题"按钮

在 `ui_main.py` 左侧按钮列"设置"按钮之前新增（`btn_col.pack` 上下文中）：
```python
ttk.Button(btn_col, text="整理错题", style="Secondary.TButton",
           command=self.open_wrongwords).pack(fill="x", pady=(0, 6))
```
新增方法：
```python
def open_wrongwords(self):
    book = self.current_book()
    if not book:
        messagebox.showinfo("提示", "请先选择词库")
        return
    from ui_wrongwords import WrongWordsDialog
    WrongWordsDialog(self.root, self.conn, book)
```

### 3. `ui_wrongwords.py` — 错题整理弹窗（新文件）

`WrongWordsDialog(tk.Toplevel)`，构造参数 `(root, conn, book)`：
- 标题"不熟练词整理 - {book['name']}"
- 顶部标签：共 N 个不熟练词
- 中部 `ttk.Treeview`：列 = 单词 / 词性 / 中文释义，可滚动，展示 `database.list_unmastered_words(conn, book["id"])` 全部结果
- 底部两个按钮：`[导出 PDF]`（调用 `pdf_export.export_unmastered_pdf`）、`[关闭]`
- 导出 PDF：`filedialog.asksaveasfilename`（filetypes 含 `*.pdf`）选路径 → 调用纯函数生成 → `messagebox.showinfo` 提示成功；异常时提示错误

### 4. `pdf_export.py` — PDF 生成纯函数（新文件）

```python
def export_unmastered_pdf(book_name, words, out_path):
    import fitz
    doc = fitz.open()
    # 参数 words: list[dict]，每项含 word/pos/meaning
    # 用 msyh.ttc 渲染中文，英文内置字体
    # 每词一个卡片块：单词(大号粗体) + 词性(斜体灰色) + 中文释义(正文)
    # 卡片间浅色分隔线，自动分页（每页约 8-10 词）
    # 每页顶部标题"不熟练词整理 - {book_name}" + 生成日期
    doc.save(out_path)
    doc.close()
```

- 中文字体：`C:\Windows\Fonts\msyh.ttc`（微软雅黑）
- 返回 None，成功写入 `out_path`。

### 5. `requirements.txt` — 追加依赖

追加一行 `PyMuPDF`。

## 测试

- `pdf_export.export_unmastered_pdf` 为纯函数，可写无 GUI 测试：构造几条 `{"word","pos","meaning"}` 数据，导出到临时路径，断言文件存在且非空（用 fitz 打开验证页数/内容）。
- `database.list_unmastered_words` 可无 GUI 测试：临时 db 插入词并设置 status，断言返回正确。
- `ui_wrongwords.py` 弹窗需 GUI，手动冒烟验证。
- 改动后跑 `pytest tests/ -v` 确认无回归。

## 明确不做（YAGNI）

- 不改 `word_state`/`words` 表结构（不扩展音标/英文释义/搭配字段）。
- 不做联网查词。
- 不改窗口尺寸。
- 不导出已掌握（mastered）词。