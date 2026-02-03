# Python 开发提交流程 (pydev)

按顺序执行以下步骤，完成代码检查、格式化与提交。

## 1. Ruff 检查与格式化

在项目根目录执行：

```bash
ruff check .
ruff format .
```

若有错误，先根据 ruff 的提示修复，再继续下一步。

## 2. 代码审查

- 快速过一遍本次修改的文件与逻辑
- 确认无明显 bug、逻辑错误、遗漏的边界情况
- 若有问题，指出并修复，然后从第 1 步重新执行

## 3. 提交与推送

**仅当第 1、2 步均通过时** 执行：

1. **生成提交信息**：根据 `git diff --staged` 和 `git status` 的变更，用约定式提交格式写一条简洁的 commit message（如 `feat: ...` / `fix: ...` / `refactor: ...`）。
2. **暂存并提交**：
   ```bash
   git add -A
   git commit -m "<你生成的 commit message>"
   ```
3. **推送**：
   ```bash
   git push
   ```

## 4. 若存在未修复的问题

若在第 1 或 2 步发现需要修复的问题且暂不提交：

- 明确列出：哪些文件/哪类问题需要处理
- 提示用户：修复完成后再重新运行本命令完成提交流程

---

**总结**：先 `ruff check` + `ruff format`，再人工审查，无问题则生成 commit message、提交并 push；有问题则列出待修复项并提示用户。
