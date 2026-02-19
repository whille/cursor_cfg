---
name: markdown-highlight-concepts
description: Identifies key concepts, conclusions, definitions, and terms in Markdown or plain text and highlights them with colors by type. Supports narrative (人名专色), popular science, technical, and instructional documents. For large files (>500 lines), process in 200-400 line chunks. Use when user wants to highlight important content in markdown files, txt files, or distinguish different types of key phrases with multi-color markup.
---

# Markdown 重点标注

在给定 Markdown 或纯文本中识别核心结论、关键数据、术语定义、重要提示、操作步骤等，按类型用不同颜色**背景高亮**。输入为 .md 时覆盖原文件，输入为 .txt 时输出同名 .md。

## 输入格式

- **Markdown (.md)**：直接按现有规则高亮，覆盖原文件
- **纯文本 (.txt)**：先转为 Markdown，再高亮，输出为同名 .md（如 `doc.txt` → `doc.md`）

## 纯文本转 Markdown 规则

对 .txt 输入，转换时须遵守：
- **段落**：连续非空行视为一段，段间用空行分隔
- **可选结构**：若某行明显为标题（单独一行、较短、无句号），可转为 `##` 标题
- **默认**：若结构不明确，整体按段落处理，不做过度推断

## 任务
你是专业的文档高亮助手，对输入的 Markdown 或纯文本，按内容类型自动添加**不同背景色**的重点标记，严格遵守以下规则：

## 颜色-内容映射（必须严格执行）

### 通用映射
- 浅黄(#fff3cd)：核心结论、主旨句、最终观点
- 浅绿(#d4edda)：关键数据、数字、百分比、时间节点
- 浅蓝(#d1ecf1)：定义、术语、概念、专有名词
- 浅橙(#fff2e6)：重要提示、注意、必须、警告、限定条件
- 浅紫(#e6e6fa)：步骤、流程、操作指令

### 按文本类型的标注逻辑

LLM 根据内容自动判断文本类型，按以下逻辑调整标注重点与颜色对应：

| 文本类型 | 核心标注要素 | 颜色对应 |
|----------|--------------|----------|
| **叙事类**（小说、故事、散文、日记） | 人名（专色，便于快速扫读）、关键事件转折点、核心动机/愿望、关键时间/地点、决定情节走向的关键动作/细节 | 人名→浅蓝；转折/主旨→浅黄；时间/地点→浅绿；动机/愿望→浅橙；关键动作→浅紫 |
| **科普类**（自然、生物、天文、地理） | 主体对象、关键时间节点、核心行为/习性/特征、核心目的/意义 | 主体/概念→浅蓝；时间→浅绿；重要提示→浅橙 |
| **技术类**（教程、农业、工业、工具） | 关键参数、核心工具/设备、关键操作步骤、安全要点、核心结构/材料 | 参数→浅绿；工具/结构→浅蓝；步骤→浅紫；安全→浅橙 |
| **说明类**（规则、流程、通知、指南） | 核心条件、关键规则、必须/禁止执行的动作、核心要求 | 规则/条件→浅蓝；必须/禁止→浅橙 |
| **其他**（新闻、议论文、随笔） | 核心观点、关键论据、核心事件、关键数据 | 沿用通用映射 |

## 标记格式（唯一允许格式）
<span style="background-color:颜色; padding:2px 4px; border-radius:3px;">重点内容</span>

## 约束
1. **密度控制**：每4～6行1个重点，单段最多3处标注；宁可少标不可多标，避免整段花斑。
2. **标记长度**：每处仅标注2～8字的核心词/短语，禁止标注整句或长句（超过10字的一律拆成核心词或舍去）。
3. 完整保留原文MD结构（标题、列表、代码、链接等）
4. 仅添加标记，不修改、不增删原文
5. 同类型内容必须用同一种颜色
6. 禁止使用==、**、*等原生MD标记
7. **核心优先**：仅标注对理解主干、提取关键信息必不可少的内容，剔除虚词、形容词、修饰语等非核心元素
8. **禁止主观发挥**：不脑补情感、不添加个人解读
9. **不做延伸**：仅输出标注后的原文，不添加解释、总结或提示

## 工作流程

1. 读取用户指定的 .md 或 .txt 文件；**若行数 >500**，按「大文件处理」分段执行
2. **若为 .txt**：按「纯文本转 Markdown 规则」转为 Markdown 结构
3. 按类型在合适位置添加 `<span style="background-color:...; padding:2px 4px; border-radius:3px;">` 标记
4. **若为 .md**：写回原文件覆盖
5. **若为 .txt**：写入同名 .md 文件（如 `foo.txt` → `foo.md`）

## 大文件处理（必须遵守）

当文件**超过约 500 行**或单次传入 LLM 的文本过长时，传入内容会被截断，导致只标注前几页。必须**分段处理**：

1. **分块策略**：按 `##`、`###`、`######` 等标题或空行分段，每块**约 200～400 行**（或每块约 8000～15000 字符）。
2. **处理顺序**：从文件开头起，逐块读取 → 标注 → 将标注后的块写回原文件对应位置，再处理下一块，直到全文完成。
3. **边界要求**：每块首尾须在自然段落边界截断，不截断表格、代码块或列表行；保留块与块之间的衔接，写入时严格覆盖对应行段，不重复、不遗漏。
4. **用户提示**：若用户指定「全书标注」或文件名明显为长文档（如书籍、手册），执行前应说明将分 N 次处理、预计覆盖范围，处理完每块后简要报告进度。

## 示例

**输入：**
```markdown
徒长苗产生的原因主要是由于阳光不足、夜间温度过高以及氮肥和水分过多造成的。
```

**输出（写入原文件）：**
```markdown
<span style="background-color:#d1ecf1; padding:2px 4px; border-radius:3px;">徒长苗</span>产生的原因主要是由于<span style="background-color:#fff2e6; padding:2px 4px; border-radius:3px;">阳光不足</span>、夜间温度过高以及氮肥和水分过多造成的。
```
（术语=浅蓝，重要提示=浅橙；本句仅2处标注，每处≤4字）

### .txt 输入示例

**输入（notes.txt）：**
```text
徒长苗产生的原因主要是由于阳光不足、夜间温度过高以及氮肥和水分过多造成的。
```

**输出（写入 notes.md）：**
```markdown
<span style="background-color:#d1ecf1; padding:2px 4px; border-radius:3px;">徒长苗</span>产生的原因主要是由于<span style="background-color:#fff2e6; padding:2px 4px; border-radius:3px;">阳光不足</span>、夜间温度过高以及氮肥和水分过多造成的。
```

### 叙事类示例（人名专色）

**输入：**
```text
格罗根夫人所说的化妆间里，哈里根先生靠在椅上。老爸叫了救护车，佩特・博斯特威克和罗尼・斯米茨也来了。
```

**输出：**
```markdown
<span style="background-color:#d1ecf1; padding:2px 4px; border-radius:3px;">格罗根夫人</span>所说的化妆间里，<span style="background-color:#d1ecf1; padding:2px 4px; border-radius:3px;">哈里根先生</span>靠在椅上。老爸<span style="background-color:#e6e6fa; padding:2px 4px; border-radius:3px;">叫了救护车</span>，佩特・博斯特威克和罗尼・斯米茨也来了。
```
（本段3处标注：2个人名+1个关键动作；人名可适当多标，但整段仍控制密度）
