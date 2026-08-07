# 单词拼写测试与复习软件 — 设计文档

日期：2026-08-07

## 1. 目标

基于现有雅思词汇 Excel 词库，构建一个桌面拼写测试与复习软件。软件给出中文释义和词性，用户拼写英文；拼写正确则提示并换下一词（随机顺序），拼写错误则显示正确拼写并记录到错题集合，次日或下次打开优先复习错题。支持后续自行导入新词库。

## 2. 技术栈

- Python 3.12 + Tkinter（内置 GUI，零额外 GUI 依赖）
- SQLite（内置，存储数据）
- pandas + xlrd + openpyxl（首次导入 .xls 词库）
- pytest（单元测试）
- 后续可用 PyInstaller 打包为 exe（当前阶段先跑脚本）

## 3. 整体架构

```
单词测试软件/
├── 雅思词汇9400词EXCEL词-乱序版.xls   ← 原始词库（首次导入用，只读）
├── main.py                            ← 程序入口，启动主界面
├── database.py                        ← 数据层：词库管理、导入、状态存取(SQLite)
├── quiz_logic.py                      ← 核心逻辑：出题队列、判定、优先级、状态迁移
├── ui_main.py                         ← 主界面：词库选择、统计面板、开始按钮
├── ui_quiz.py                         ← 拼写测试界面
├── ui_import.py                       ← 词库导入向导（Excel/CSV）
├── vocab.db                           ← SQLite 数据文件（首次运行自动生成）
├── requirements.txt                   ← 依赖清单
└── config.json                        ← 全局设置
```

**数据流**：首次运行自动把内置 xls 导入为词库 → 用户可后续导入更多词库 → 主界面选择词库 → quiz_logic 基于当前词库生成当日队列 → 拼写 → 判定 → 更新状态。

## 4. 数据模型（SQLite，多词库独立）

### books 表
- `id` INTEGER PRIMARY KEY
- `name` TEXT 唯一（词库名称，如"雅思词汇9400"）
- `source` TEXT（builtin / imported）
- `created_at` TEXT
- `word_count` INTEGER

### words 表（每词库独立）
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `book_id` INTEGER 外键
- `word` TEXT 英文单词
- `meaning` TEXT 中文释义（含词性，原文清洗后保留）
- `pos` TEXT 提取的词性（如 n/v/a，从释义中 `v.` 等标注提取）
- UNIQUE(book_id, word) 导入时按单词去重

### word_state 表（每词一个状态行）
- `book_id` INTEGER
- `word_id` INTEGER
- `status` TEXT：new / poor / blur / good / mastered
- `wrong_count` INTEGER 累计错题次数
- `review_count` INTEGER 复习次数
- `last_result_date` TEXT 上次作答日期
- `next_review_date` TEXT 下次复习日期
- `priority` INTEGER 优先级分数（越高越先出）
- PRIMARY KEY(book_id, word_id)

### daily_log 表
- `id` INTEGER PRIMARY KEY
- `book_id` INTEGER
- `date` TEXT
- `new_done` INTEGER 新词完成数
- `correct` INTEGER
- `wrong` INTEGER
- `completed` INTEGER (0/1)

### settings 表
- `key` TEXT PRIMARY KEY
- `value` TEXT

### config.json
- `daily_new_words`：每日新词数 N（默认 50）
- `ignore_case`：是否忽略大小写（默认 true）
- `ignore_punct`：是否忽略标点（默认 false，即标点严格匹配）

## 5. 核心机制

### 5.1 出题队列构造（进入某词库学习时）

1. **待复习词** = `next_review_date <= 今天` 且状态为 poor/blur/good 的词，按 priority 降序排最前。
2. **新词** = 今日未学满 N 个的 new 状态词，乱序排在复习词之后。
3. 复习词与新词交替混合出题，避免连续轰炸同一类型。

### 5.2 判定逻辑（用户回车提交）

- 忽略大小写比较（配置控制）。
- 标点严格匹配（配置控制，默认不忽略），如 `A.M.` 与 `AM` 视为不一致；仅当用户在设置中开启"忽略标点"时才归一化。
- 归一化后比较：
  - 完全一致 → 正确
  - 编辑距离 == 1（漏/多/错一个字母）→ 模糊："很接近！正确拼写：xxx"
  - 否则 → 不会：红字显示正确拼写，状态置 poor，加入当轮重练（隔几题后重出一次）
- 答对：绿色"正确"，自动下一题。

### 5.3 状态迁移

- 答对：`poor→blur`、`blur→good`、`good`+间隔复习答对→`mastered`
- 答错：任何状态强制降为 `poor`
- 复习间隔：`poor` 次日 / `blur` 3 天后 / `good` 7 天后 / `mastered` 30 天后
- 每次作答立即写库，关闭窗口即保存。

### 5.4 词库导入

- 支持 `.xls / .xlsx / .csv`
- 自动识别表头，预览前 10 行
- 用户为"英文单词"和"中文释义"各选一列（下拉框，自动猜测常见表头如 word/单词/english/释义/中文）
- 输入词库名称
- 导入时清洗 + 按单词去重 + 自动提取词性 + 校验空行
- 导入后的词全部为 new 状态，学习进度完全独立

### 5.5 词库清洗规则

- 去除释义首尾空格、句号
- 处理异常标注（如 `n[化].` 提取词性时兼容）
- 多词短语、连字符词、大写词（Christmas）、带点缩写（A.M.）均保留原样，判定时按配置归一化

## 6. 界面设计

### 6.1 主界面（ui_main.py）

- 左侧词库列表：切换当前词库，显示各词库词数/掌握数
- 中间统计面板：今日新词 x/50、待复习数、错题总数、连续天数、掌握词数
- "开始学习"大按钮
- 底部"导入词库"和"设置"按钮

### 6.2 拼写界面（ui_quiz.py）

- 顶部：进度条 + "第 x/y 题" + 当前词状态标签
- 中部：大字显示中文释义（含词性），如 `v. 分，划分，分开；分配；(by)除`
- 输入框，回车提交
- 反馈区：绿/红显示判定结果
- 右下角：本轮剩余题数、"退出并保存"按钮
- 会话结束：显示本次小结（对/错/模糊统计），返回主界面

### 6.3 设置窗口

- 每日新词量
- 判定严格度（是否忽略大小写/标点）

### 6.4 导入向导（ui_import.py）

- 选文件 → 预览表头 → 选列 → 输入词库名 → 确认导入
- 失败/损坏文件：弹窗提示，不影响现有数据

## 7. 错误处理

- 词库文件缺失/损坏 → 弹窗提示；若已有 vocab.db 则正常继续
- 无待学词 → 提示"已完成，明天再来"
- 导入过程中任何异常 → 回滚本次导入，不影响现有数据

## 8. 测试

pytest 单元测试覆盖：
- 判定函数：大小写、标点严格匹配、编辑距离
- 状态迁移逻辑
- 出题队列构造（复习优先、新词数量、交替混合）
- 词库导入去重与清洗

## 9. 非目标

- 不含发音、例句、图片
- 不含账号同步/云备份
- 本阶段不打包 exe（后续确认满意后再打包）