# 电子书转带高亮 Markdown (ebook-to-highlight)

将 PDF/图片/MOBI/EPUB 转为 Markdown，并自动完成重点标注。一次完成「转换 + 高亮」两步。

## 执行流程

按顺序执行以下步骤。

### 1. 确认输入文件

- 用户已在提示中提供文件路径，或通过 `@文件` 引用
- 若未指定，向用户询问待转换的 `input_path`（支持 pdf/png/jpeg/mobi/epub）
- 确认文件存在

### 2. 执行 ebook_to_md 转换

使用 `ebook_to_md` Skill 进行转换：

- 调用方式：执行 `skills/ebook_to_md` 的转换逻辑（Python `run()` 或对应命令行）
- 参数：`input_path`、`output_path`（可设为与输入同目录、同主名的 .md）、`output_format="md"`
- **`ocr_backend`**：**必须使用 `baidu`**（中文识别效果更好）；仅当用户明确要求或百度 API 不可用时才用 `local`
- 转换成功后得到 .md 文件路径

若转换失败（返回 "错误: ..."），将错误信息告知用户并终止。

### 3. 执行 md_highlight 标注

对步骤 2 输出的 .md 文件，按 `md_highlight` Skill 的规则进行高亮：

- 读取 `skills/md_highlight/SKILL.md` 的完整规则（颜色-内容映射、约束、标记格式）
- 对 .md 内容添加 `<span style="background-color:颜色; padding:2px 4px; border-radius:3px;">重点内容</span>` 标记
- **大文件（>500 行）**：按标题或空行分段，每块约 200～400 行，逐块标注后写回对应位置
- 标注完成后覆盖原 .md 文件

### 4. 反馈用户

- 告知完成路径
- 可提供 brief 预览或前几段标注效果

---

## 总结

**流程**：ebook_to_md 转换 → md_highlight 标注 → 覆盖/保存 .md → 反馈用户。

**用法示例**：`/ebook-to-highlight @report.pdf` 或 `/ebook-to-highlight` 后按提示输入文件路径。
