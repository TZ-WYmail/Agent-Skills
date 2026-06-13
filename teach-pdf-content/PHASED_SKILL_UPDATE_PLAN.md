# teach-pdf-content 分阶段 Skill 升级计划

## 1. 文档目的

本文件用于管理 `teach-pdf-content` 的分阶段升级，不再停留在“讨论方向”，而是把后续改造拆成可执行阶段、明确影响文件、给出验收标准，并为每轮复测提供稳定入口。

本计划有两个对象：

1. 工程副本：`E:\Project\Agent Skill\teach-pdf-content`
2. 实际生效的 installed skill：`C:\Users\19767\.codex\skills\teach-pdf-content`

后续复测以 installed skill 为准。


## 2. 升级总目标

把 skill 从“生成多个 Markdown 功能文件的章节学习包”，升级为“知识点导向、三主文件输出、可被 HTML 教学层消费”的教学技能。

最终目标：

- 默认输出不再碎成 8 到 11 个学习入口文件。
- 每章以 3 个主文件组织：
  - `detailed-notes.md`
  - `practice.md`
  - `review-notes.md`
- 每章额外生成：
  - `knowledge-map.json`
  - `source-map.md`
  - `_meta.json`
- 内容生成逻辑从“目录导向”改为“知识点导向”。
- 新概念按复杂度 `C1-C4` 决定讲解深度。
- 前端首屏可展示章节知识图谱。


## 3. 阶段拆分总览

| 阶段 | 目标 | 状态 |
| --- | --- | --- |
| Phase 0 | 统一方案、补文档、确认真实生效 skill 路径 | 已完成 |
| Phase 1 | 更新 skill 规范与参考标准，默认指向 vNext 三主文件模型 | 本轮完成 |
| Phase 2 | 为 vNext 增加 scaffold / checker 脚本入口 | 本轮完成 |
| Phase 3 | 调整 subskills，让生成逻辑围绕知识点、复杂度、教学闭环组织 | 本轮完成 |
| Phase 4 | 选样章做迁移示范，验证新模板可用 | 待做 |
| Phase 5 | 引入知识点微讲页模型，生成页级教学数据，并把主流程切到 page-first | 本轮完成 |
| Phase 6 | 改 renderer，对接 `knowledge-map.json`、页级教学数据与翻页式前端 | 待做 |
| Phase 7 | 用样章复测、校准质量门、再推广到全课程 | 待做 |


## 4. 各阶段详细说明

### Phase 0：方案定稿与路径确认

目标：

- 明确重构不是“单纯 Markdown 改 HTML”。
- 明确 skill 的真实生效位置。
- 明确输出结构、知识图谱、复杂度分级、教学闭环方向。

已产出：

- `REFACTOR_IMPROVEMENT_PLAN.md`
- `CHAPTER_OUTPUT_TEMPLATES.md`
- `KNOWLEDGE_MAP_SCHEMA.md`
- 本文件

验收标准：

- 三主文件结构明确
- `knowledge-map.json` schema 明确
- 改造顺序明确


### Phase 1：Skill 主规范升级

目标：

- 让 installed skill 默认面向 vNext 模型，而不是继续把旧 8 文件当成主路径。
- 让后续调用 skill 的模型在读规范时，优先生成三主文件。

改动文件：

- `SKILL.md`
- `references/chapter_output_standard.md`
- `CHAPTER_OUTPUT_TEMPLATES.md`
- `KNOWLEDGE_MAP_SCHEMA.md`

关键变更：

- 默认 learner-facing 结构改为三主文件
- 增加 `knowledge-map.json` 规范入口
- 明确 Markdown 是“语义化教学源文件”
- 明确 legacy 结构仅作为兼容模式保留

验收标准：

- `SKILL.md` 明确写出三主文件模型
- skill 规范中出现知识点导向、复杂度分级、知识图谱要求
- skill 规范中不再把 `01-lesson-notes.md` 视为唯一主产物


### Phase 2：vNext 脚手架与校验器

目标：

- 提供能直接生成 vNext 目录结构的脚手架
- 提供能检查 vNext 输出是否缺关键结构的校验器

新增脚本：

- `scripts/new_lesson_pack_vnext.py`
- `scripts/check_lesson_pack_vnext.py`

设计原则：

- 不强行破坏旧脚本兼容性
- 新脚本专门服务三主文件模型
- 旧脚本继续保留，供兼容旧章节时使用

验收标准：

- 能脚手架生成：
  - `detailed-notes.md`
  - `practice.md`
  - `review-notes.md`
  - `knowledge-map.json`
  - `source-map.md`
  - `_meta.json`
- 校验器能发现：
  - 缺知识图谱
  - 缺 `为什么成立`
  - 缺 trace
  - 缺答案区
  - 缺复习路线


### Phase 3：Subskills 升级

目标：

- 让子技能不再围绕旧文件名写规则，而是围绕三主文件和教学闭环写规则。

改动文件：

- `references/subskills/lesson-note-builder.md`
- `references/subskills/practice-builder.md`
- `references/subskills/quality-gate.md`
- 必要时补充 `cs-data-structures.md`

关键变更：

- `lesson-note-builder` 改为面向 `detailed-notes.md`
- `practice-builder` 改为面向 `practice.md` 与 `review-notes.md`
- `quality-gate` 增加知识点映射、trace、闭卷输出、知识图谱等校验项

验收标准：

- 子技能文档明确引用三主文件
- 图 / 树 / 遍历 / 算法类内容被强制要求最小例子 + trace + why
- quality gate 能判定“只是摘要，不是教学稿”的失败情况


### Phase 4：样章迁移示范

目标：

- 用真实课程内容验证新技能不是纸面方案。

优先样章：

- `07-graph`
- `06-tree-binary-tree`

优先小节：

- `7.4.1 连通分量、生成树与生成森林`
- 树或遍历章节中的一个过程型难点

任务：

- 手工或半自动迁移为三主文件
- 为示范章写一份 `knowledge-map.json`
- 用新版 checker 跑验证

验收标准：

- 学习者只看新主文件就能学，不必频繁翻教材补“为什么成立”
- 小节中有最小例子、why、trace、边界、闭卷模板
- 前端能消费该章结构


### Phase 5：知识点微讲生成

目标：

- 把生成粒度从“小节讲义”进一步下沉为“知识点微讲页”
- 让模型按“10 到 15 分钟讲清一个知识点”的思路生成重点内容

改动对象：

- `SKILL.md`
- `references/subskills/lesson-note-builder.md`
- 未来新增的页级数据结构，例如 `knowledge-pages.json`

关键能力：

- 为每个知识点先生成 teaching brief
- 对重点知识点生成页级 block 数据
- 支持按知识点类型切换讲解模式，而不是强套统一模板
- 支持并行生成知识点页，再回收汇编为三主文件
- `detailed-notes.md` 由 `knowledge-pages.json` 汇编得到，而不是再从长讲义中反向抽页
- 保留 `build_knowledge_pages.py` 作为旧包迁移工具，而不是主流程

验收标准：

- 样章中的高重要度 `C3/C4` 知识点形成独立微讲页
- 知识点页不只是结论摘要，而是真正具备问题、例子、why、误区、闭卷输出
- `detailed-notes.md` 由页级知识点内容汇编得到，而不是反向拆长文


### Phase 6：Renderer 对接

目标：

- 让网页层真正基于三主文件、知识图谱和页级知识点数据展示
- 从“章节阅读页”升级成“知识点翻页教学器”

改动对象：

- `scripts/render_lesson_site.py`
- 未来新增的页级数据源，例如 `knowledge-pages.json`

关键能力：

- 首屏知识图谱
- 从图谱点击进入知识点页
- 一页一个知识点的翻页阅读
- 学习模式 / 复习模式切换
- `为什么成立` 卡片
- trace 展开
- 题目答案延迟显示
- 口头复述模式

验收标准：

- 章节首屏展示知识图谱
- 点击节点能跳到 `detailed-notes` / `practice` / `review-notes`
- 页面结构围绕三主文件展开，而不是围绕旧 8 文件标签展开
- 重点知识点可按翻页方式快速浏览，不必在长 Markdown 中滚动查找


### Phase 7：课程级复测与推广

目标：

- 用真实课程批量验证升级后 skill 的稳定性。

复测方式：

1. 用 installed skill 重新生成 1 个示范章
2. 检查输出结构是否为三主文件
3. 检查知识图谱是否生成
4. 检查关键过程型小节是否包含 why + trace + 边界
5. 再扩大到 2 到 3 章

验收标准：

- skill 稳定生成三主文件
- 质量门对粗糙输出能报错或报 warning
- 课程章节不再出现 11 个并列学习文件


## 5. 本轮改造范围

本轮优先完成：

1. Phase 1：更新真实生效 skill 的主规范
2. Phase 2：增加 vNext scaffold / checker
3. Phase 3：更新关键 subskills

本轮不做：

- 大规模章节内容迁移
- renderer 的完整 UI 重构
- 全课程批量重跑


## 6. 本轮完成后的复测建议

你重新测试时，建议重点看这 5 个点：

1. 新生成的章节是否默认产出三主文件，而不是 8 到 11 个学习主文件。
2. `detailed-notes.md` 是否出现知识点表、`为什么成立`、trace、闭卷输出模板。
3. `practice.md` 是否把题目区和答案区分离。
4. `review-notes.md` 是否有 3 分钟 / 10 分钟复习路线、口头复述模板、错题回炉规则。
5. 是否生成 `knowledge-map.json`。


## 7. 复测失败时的定位顺序

如果你复测后发现效果仍不对，按这个顺序定位：

1. 先看 installed skill 的 `SKILL.md` 是否已更新
2. 再看是否调用了 vNext scaffold
3. 再看 subskill 是否仍引用旧文件名
4. 再看生成结果是否落成三主文件结构
5. 最后看内容本身是否真正补了 why / trace / 边界


## 8. 后续执行建议

本轮 skill 更新完成后，下一步最值得做的是：

1. 用新版 skill 重跑 `07-graph` 的一个示范章
2. 如果结果基本对，再去改 renderer
3. 不建议现在就全量重跑整门课

原因：

- 先拿真实难章节校准，比先做大规模迁移更稳
- 如果生成逻辑还没校准，越早批量跑，返工越大
