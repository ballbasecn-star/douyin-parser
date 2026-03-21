# 仓库协作说明

本仓库用于长期的 AI 协作式迭代。请把 `docs/` 目录视为项目的外置记忆；当行为、范围或约束发生变化时，需要同步更新文档。

## 阅读顺序

开始工作时，只读取当前任务真正需要的最小文档集合：

1. `docs/roadmap/current.md`
2. `docs/product/prd.md`
3. `docs/architecture/overview.md`
4. `docs/modules/` 中与当前任务相关的模块文档
5. 如果任务会改变既有长期决策，再读取 `docs/architecture/decisions/` 中相关 ADR

除非被阻塞，不要一次性加载整个 `docs/` 目录。

## 事实来源

- `README.md`：面对人的项目介绍和快速开始
- `docs/product/prd.md`：当前产品范围与非目标
- `docs/architecture/overview.md`：系统边界与核心数据流
- `docs/architecture/project-structure.md`：后端项目结构与分层规范
- `docs/architecture/data-storage.md`：数据库与持久化规范
- `docs/architecture/environment-strategy.md`：环境划分与配置隔离原则
- `docs/modules/*.md`：模块职责与行为
- `docs/roadmap/current.md`：当前阶段正在做什么
- `docs/operations/deployment.md`：开发与生产部署方式
- `docs/operations/development-workflow.md`：开发、验证与 Git 提交流程
- `docs/architecture/decisions/*.md`：关键技术与产品决策

如果代码与文档不一致，除非文档明确标记为未来规划，否则应在改代码时同步修正文档。

## 文档更新规则

当以下内容发生变化时，必须同步更新文档：

- 产品范围
- API 契约
- 数据模型
- 部署拓扑
- 默认服务商选择
- 安全假设
- 模块职责

当变化会影响长期方向或约束未来实现时，需要新增或更新 ADR。

## Git 提交规则

本仓库对 AI 的 Git 提交行为采用以下默认规则：

### 默认行为

- 当一次任务的代码或文档修改已经完成，并且已完成最小必要验证后，AI 应默认执行本地 `git commit`
- AI 可以自动执行 `git add` 和 `git commit`
- AI 默认不自动执行 `git push`，除非用户明确要求
- AI 不自动执行 `git commit --amend`

### 允许自动提交的前提

只有在以下条件同时满足时，AI 才应自动提交：

1. 当前任务的改动范围已经闭环
2. 已完成适用的最小验证
3. 工作区中没有会被误提交的无关改动

### 必须先暂停并询问用户的情况

如果出现以下任一情况，AI 不应自动提交，而应先说明情况：

- 工作区中出现来源不明或与当前任务无关的改动
- 当前任务只完成了一部分
- 本次修改影响面较大，但尚未做基本验证
- 当前变更实际上应拆成多个独立 commit

### 提交信息规范

优先使用简洁、明确的提交信息，推荐格式：

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`
- `chore: ...`

要求：

- 标题直接描述结果
- 不使用含糊描述，如“update”“修改一下”“final”
- 文档改动单独使用 `docs:`

### 提交范围规则

- 不提交与当前任务无关的文件
- 不把用户已有但未要求处理的改动一起提交
- 若工作区存在无关改动，优先只提交本次任务相关文件

### 提交后的说明

完成提交后，AI 应在回复中明确说明：

- commit 是否已完成
- commit message 是什么
- 是否做了验证
- 是否尚未 push

## 当前产品方向

当前产品有两层：

1. 已经存在的单视频解析、转录、分析工作流
2. 基于单视频内核向上扩展的创作者监控工作流

创作者监控工作流应先从以下能力开始：

- 博主管理
- 博主视频列表同步
- 手动选择视频进行转录和分析

除非路线图明确改变，否则不要直接跳到“全自动批量分析”。
