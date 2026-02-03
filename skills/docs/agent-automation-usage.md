# Agent 自动化用法（Cursor 可用手册）

供在 Cursor 内查阅的「Agent 自动化用法」参考手册，每条用法均给出在 Cursor 中的具体操作方式。若你之后能提供公众号原文或摘要，可在文末增补「与原文对应」小节。

---

## 1. 总览与前提

**目标读者与场景**：在 Cursor 里用 Agent 做自动化编码、排查、重构、理解代码库、TDD、Git/PR、长时间迭代直到达标等。本文档把通用「Agent 自动化」思路映射到 Cursor 的 Plan、Rules、Skills、对话与工具使用上。

**参考来源**：

- [使用 Agent 编码的最佳实践](https://cursor.com/cn/blog/agent-best-practices)（Cursor 官方）
- [Agent 概览](https://docs.cursor.com/zh/agent/overview)（Cursor 文档）

---

## 2. Agent 自动化核心三件套（对应 Cursor）

| 通用概念 | 在 Cursor 中的体现 |
|---------|-------------------|
| **Instructions** | 系统提示 + `.cursor/rules/` 下的规则、Plan 模式下的实现计划 |
| **Tools** | 代码库搜索（grep / 语义搜索）、文件编辑、终端执行、Apply、Review、MCP 等 |
| **User messages** | 输入框中的提示词、`@` 引用（文件/文件夹/Past Chats/Branch 等） |

**简要对照**：

- 想「指导 Agent 行为」→ 写 Rules、用 Plan 模式出计划、在提示里写清成功标准。
- 想「让 Agent 动手」→ 依赖其工具：搜索、编辑、运行命令、Apply 改动；需要时用 MCP 扩展能力。
- 想「带上下文」→ 用自然语描述需求，或 `@` 具体文件/目录/历史对话/分支。

---

## 3. 从规划开始（Plan 模式）

- **操作**：在 Agent 输入框按 `Shift+Tab` 进入 Plan 模式。
- **Agent 会做的事**：分析代码库、提出澄清问题、生成含文件路径与代码引用的实现计划、**等待你确认后再执行**。
- **Cursor 可用动作**：
  - 用「Save to workspace」把计划存到 `.cursor/plans/`，便于团队协作与断点续做。
  - 若结果不符合预期：回滚改动 →  refined 计划（把需求写更具体）→ 再跑一次，通常比在对话里反复修更干净。

不必每个任务都做详细计划；简单修改或已很熟的任务，可直接交给 Agent。

---

## 4. 上下文管理

- **让 Agent 自行拉取上下文**：不必在提示里手动 @ 每个文件。用自然语描述即可，例如「身份验证流程」「`CustomerOnboardingFlow` 的边界情况」，Agent 会用 grep 与语义搜索找相关文件。
- **何时手动引用**：若你已知确切文件或目录，在提示中 `@filename` 或 `@folder` 即可；无关文件过多会干扰重点。
- **`@Past Chats`**：新对话需要沿用旧结论时，用 `@Past Chats` 引用历史对话，由 Agent 按需读取，避免整段复制。
- **`@Branch`**：让 Agent 理解当前分支改动，例如：「Review the changes on this branch」「What am I working on?」。

---

## 5. 对话节奏：新对话 vs 继续当前对话

- **建议新开对话**：切换任务或功能、Agent 反复犯同类错误、已完成一个逻辑完整的工作单元。
- **建议继续当前对话**：同一功能迭代、需要前文上下文、正在调试它刚构建的内容。

过长对话会积累噪音，多轮总结后 Agent 易分心或切到无关任务。若感觉效果变差，可新开对话，并用 `@Past Chats` 带入必要结论。

---

## 6. 扩展 Agent：Rules 与 Skills（Cursor 可用配置）

### Rules（静态、每次生效）

- **位置**：`.cursor/rules/`，以 Markdown 文件存在。
- **建议写**：常用命令、代码风格/模式、指向规范示例的**引用**（写路径，不贴整份代码）；从简单起步，只在 Agent 反复犯同类错误时再加规则。
- **建议不写**：整份风格指南（交给 linter）、所有可能命令（Agent 已懂常见工具）、极少出现的边缘指令。

提示：规则可提交到 Git，团队共享；看到 Agent 犯错时可更新对应规则。

### Skills（动态、按需调用）

- **形式**：`SKILL.md` + 脚本/工作流；可包含 custom commands、hooks、领域知识。与「始终加载」的 Rules 不同，Skills 在 Agent 认为相关时动态加载。
- **与本仓库对齐**：本仓下即为 Skills 的实现方式，Agent 在匹配到描述时会加载对应 Skill。例如：
  - [douban-nowplaying-highrated/SKILL.md](../douban-nowplaying-highrated/SKILL.md)：豆瓣在映高分电影列表
  - [video-download/SKILL.md](../video-download/SKILL.md)：按链接下载视频
  - [ebook-converter/SKILL.md](../ebook-converter/SKILL.md)：电子书格式转换
  - [github-to-skill/SKILL.md](../github-to-skill/SKILL.md)：从 GitHub 仓库生成 Skill

---

## 7. 常见工作流（在 Cursor 中的具体做法）

### TDD

1. 明确说明在做 TDD，让 Agent 按预期输入/输出写测试，且不要写实现。
2. 让 Agent 运行测试，确认测试**失败**；此阶段不写实现。
3. 你满意测试后提交测试。
4. 让 Agent 写能通过测试的代码，并要求不修改测试；持续迭代直到所有测试通过。
5. 满意后提交实现。

可验证的「测试通过」是很好的迭代目标，Agent 表现更稳定。

### 理解代码库

像问队友一样用自然语提问，例如：

- 「这个项目里的日志是如何运作的？」
- 「我该如何添加一个新的 API endpoint？」
- 「`CustomerOnboardingFlow` 处理了哪些边界情况？」
- 「为什么我们在第 1738 行调用的是 `setUser()` 而不是 `createUser()`？」

Agent 会用 grep 与语义搜索在代码库中找答案，适合快速熟悉新项目。

### Git / PR

把多步流程固化成命令，放在 `.cursor/commands/`，在提示里用 `/` 触发。例如：

- **`/pr`**：为当前更改创建 Pull Request（看 diff → 写提交信息 → 提交并推送 → `gh pr create`，返回 PR URL）。
- **`/fix-issue [number]`**：用 `gh issue view` 取 issue、找相关代码、修复并开 PR。
- **`/review`**：跑 linter、查常见问题并给出需关注点摘要。
- **`/update-deps`**：检查过期依赖并逐个更新，每次更新后跑测试。

命令适合每天多次执行的固定工作流；可提交到 Git 供团队使用。

### 长时间运行直到达标

用 Skills + `.cursor/hooks.json` 的 **stop hook**，在满足条件时结束循环。简要步骤：

1. 在 `.cursor/hooks.json` 里配置 `stop` 钩子，指向你的脚本（例如 `.cursor/hooks/grind.ts`）。
2. Hook 从 stdin 读入上下文（如 `status`、`loop_count`），若未达标则输出 `followup_message` 让 Agent 继续，否则输出空结束。
3. 达标条件可写成「所有测试通过」或「`.cursor/scratchpad.md` 中出现 DONE」等可程序判断的形式。

适用于：一直修到测试全过、反复改 UI 直到和设计稿一致、任何「目标明确且可验证」的循环任务。

### 并行 Agent

- 在 Agent 下拉菜单中选择 **worktree** 或 **多模型**；Cursor 会为并行 Agent 自动建 Git worktree，各 Agent 文件与改动彼此隔离。
- 同一提示可同时在多个模型上跑，完成后并排比较，Cursor 会给出它认为更优的方案。
- 适用：棘手问题、比较不同模型写法、发现某模型遗漏的边界情况。大量并行时可开通知/声音，便于在完成时立刻查看。

### 云端 Agent

- **入口**：[cursor.com/agents](https://cursor.com/agents)、编辑器内或手机端。
- **流程**：描述任务与上下文 → Agent 克隆仓库并建分支 → 在远程沙箱中自主工作 → 完成后开 PR 并通知（Slack/邮件/Web）→ 你审查并合并。
- 适合：顺手发现的 bug 修复、小重构、补测试、更新文档等「容易进待办」的任务；可在本地 Agent 与云端 Agent 间按任务切换。Slack 中可通过 @Cursor 触发。

### Debug Mode

对「能复现但难定位原因」的 bug（竞争条件、时序、性能、回归），用 Agent 下拉中的 **Debug Mode**：

1. Agent 生成多条可能出错的假设。
2. 用日志等对你的代码做埋点。
3. 你在收集运行时数据的同时复现 bug。
4. Agent 根据实际行为定位根因。
5. 基于证据做有针对性的修复。

在 Cursor 中：Agent 下拉菜单 → 选择 Debug Mode，并尽量在提示里写清复现步骤与环境。

---

## 8. 代码审查与可验证目标

- **审查**：
  - Agent 完成后用 **Review → Find Issues** 做专项审查。
  - 对本地改动：在 Source Control 里对主分支跑 Agent Review。
  - 推送后可用 **Bugbot** 对 Pull Request 做自动化审查。
- **可验证目标**：类型、linter、测试都能让 Agent 判断「改对了没有」。在提示里尽量写出可验证的成功标准（例如「所有 `npm run typecheck` 与 `npm run test` 通过」），Agent 表现会更稳定。

---

## 9. 实用注意与清单

- **提示越具体，成功率越高**。对比：「add tests for auth.ts」 vs 「用 `__tests__/` 中的模式为 auth.ts 的 logout 边界写测试，避免 mocks」。
- **从少规则、少命令开始**，只在反复出错或形成固定工作流时再增加；在真正理解自己的模式之前不要过度优化。
- **把 Agent 当有能力的协作者**：要计划、要解释、对不认可的方案要追问；按任务类型选用并行/云端/Debug 等能力。
- **认真 review**：AI 生成的代码可能「看起来对」但有细微错误；Agent 跑得越快，你的 review 越重要。

### 在 Cursor 中落实 Agent 自动化的简短检查清单

- [ ] 复杂任务先用 **Plan 模式**（`Shift+Tab`）出计划，再执行。
- [ ] **Rules / 命令**从简起步，按实际反复出现的问题再补充。
- [ ] 善用 **@**（文件/文件夹/Past Chats/Branch）和 **Review**，减少噪音、提高可验证性。
- [ ] 为复杂任务选对模式：TDD、长时间循环、并行、云端、Debug 等。
- [ ] 在提示里写清**可验证的成功标准**（测试、类型、linter）。
- [ ] 效果下降时考虑**新开对话**，用 `@Past Chats` 带入必要上下文。

---

## 附录：可粘贴进 `.cursor/rules/` 的 Agent 用法速查

若希望 Agent 在每次对话中都能看到一段「用法速查」，可把下面内容保存到 `.cursor/rules/` 下的某条规则中（例如 `agent-usage.mdc` 或写在现有规则文件末尾）：

```markdown
# Agent 用法速查

- 复杂任务先用 Plan 模式（Shift+Tab）：先计划、确认再执行；计划可 Save to workspace 到 .cursor/plans/。
- 上下文：不知道具体文件时用自然语描述，交给 Agent 搜索；已知文件则 @ 引用。沿用旧结论用 @Past Chats，看当前分支用 @Branch。
- 新对话 vs 继续：换任务、重复犯错、完成一个单元→新对话；同功能迭代、要前文、正在调试→继续。效果变差可新对话 + @Past Chats。
- Rules 写命令/风格/示例路径，不贴整份代码；从简起步，反复错再加。Skills 按需加载，封装领域知识或工作流。
- 提示要具体、带可验证目标（测试/类型/linter）。Agent 完成后用 Review→Find Issues 或 Source Control 的 Agent Review；推送后用 Bugbot 审 PR。
- 棘手 bug 用 Debug Mode；可并行多模型或派到云端 Agent（cursor.com/agents）。把 Agent 当协作者：要计划、要解释、敢质疑。
```

---

*若你提供公众号 [原文](https://mp.weixin.qq.com/s/PvXywnkXDabmxl2YYLmvvQ) 的摘要或提纲，可在本文中增补「与原文对应」或「延伸阅读」小节。*
