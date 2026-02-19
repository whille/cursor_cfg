---
name: markdown-highlight-concepts
description: Identifies key concepts, conclusions, definitions, and terms in Markdown text and highlights them with colors by type. Use when user wants to highlight important content in markdown files or distinguish different types of key phrases with multi-color markup.
---

# Markdown 重点标注

在给定 Markdown 文本中识别核心结论、关键数据、术语定义、重要提示、操作步骤等，按类型用不同颜色**背景高亮**。**修改后覆盖原文件**。

## 任务
你是专业的文档高亮助手，对输入的Markdown文本，按内容类型自动添加**不同背景色**的重点标记，严格遵守以下规则：

## 颜色-内容映射（必须严格执行）
- 浅黄(#fff3cd)：核心结论、主旨句、最终观点
- 浅绿(#d4edda)：关键数据、数字、百分比、时间节点
- 浅蓝(#d1ecf1)：定义、术语、概念、专有名词
- 浅橙(#fff2e6)：重要提示、注意、必须、警告、限定条件
- 浅紫(#e6e6fa)：步骤、流程、操作指令

## 标记格式（唯一允许格式）
<span style="background-color:颜色; padding:2px 4px; border-radius:3px;">重点内容</span>

## 约束
1. 单段重点占比≤30%，不整段高亮
2. 完整保留原文MD结构（标题、列表、代码、链接等）
3. 仅添加标记，不修改、不增删原文
4. 同类型内容必须用同一种颜色
5. 禁止使用==、**、*等原生MD标记

## 工作流程

1. 读取用户指定的 Markdown 文件
2. 按类型在合适位置添加 `<span style="background-color:...; padding:2px 4px; border-radius:3px;">` 标记
3. 将结果写回**同一文件**，覆盖原内容

## 示例

**输入：**
```markdown
徒长苗产生的原因主要是由于阳光不足、夜间温度过高以及氮肥和水分过多造成的。
```

**输出（写入原文件）：**
```markdown
<span style="background-color:#d1ecf1; padding:2px 4px; border-radius:3px;">徒长苗</span>产生的原因主要是由于<span style="background-color:#fff2e6; padding:2px 4px; border-radius:3px;">阳光不足</span>、<span style="background-color:#fff2e6; padding:2px 4px; border-radius:3px;">夜间温度过高</span>以及<span style="background-color:#fff2e6; padding:2px 4px; border-radius:3px;">氮肥和水分过多</span>造成的。
```
（术语定义=浅蓝，重要提示=浅橙）
