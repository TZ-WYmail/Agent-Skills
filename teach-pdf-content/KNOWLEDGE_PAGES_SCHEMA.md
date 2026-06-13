# knowledge-pages.json 设计规范

## 1. 目标

`knowledge-pages.json` 是章节级页式教学数据源，用于支持：

- 一页一个知识点的翻页式前端阅读
- 从知识图谱节点直接进入对应知识点页
- 学习模式 / 复习模式下的不同块展示
- 从知识点页跳到练习与复习位置

它不是给学习者直接打开的主文件，而是：

- `detailed-notes.md` 的页级来源之一
- 前端知识点翻页器的直接输入


## 2. 文件位置

```text
chapters/<chapter-id>/knowledge-pages.json
```


## 3. 顶层结构

```json
{
  "version": "1.0",
  "chapter_id": "07-graph",
  "chapter_title": "第 7 章 图",
  "source_id": "data-structures-c",
  "output_mode": "beginner_lecture",
  "generated_at": "2026-06-13T20:00:00",
  "pages": []
}
```


## 4. page 结构

每个 `page` 对应一个知识点的独立教学页。

```json
{
  "page_id": "kp-07-08",
  "knowledge_point_id": "kp-07-08",
  "title": "连通分量、生成树与生成森林",
  "type": "principle_explanation",
  "complexity_level": "C3",
  "importance_level": "high",
  "estimated_teaching_minutes": 12,
  "prerequisites": ["kp-07-06", "kp-07-07"],
  "learning_goal": "读完后能解释一次无向图遍历为什么恰好得到一个连通分量，并说明树边为什么构成生成树或生成森林",
  "entry_question": "遍历一次图，除了访问所有点，还会顺手暴露哪些结构信息？",
  "page_summary": "无向图中，从一个未访问点出发的一次 DFS/BFS 恰好覆盖它所在的一个连通分量；首次发现新点留下的树边连接全部访问点且不成环，因此形成生成树或生成森林。",
  "notes_anchor": "detailed-notes#7-4-1-连通分量生成树与生成森林",
  "practice_refs": ["Q-03", "Q-08"],
  "review_refs": ["C04", "模板 1"],
  "source_refs": ["PDF p.182-p.184"],
  "blocks": []
}
```


## 5. page type 建议

建议支持以下页类型：

- `concept_explanation`
- `representation_explanation`
- `procedure_explanation`
- `comparison_explanation`
- `principle_explanation`
- `formula_explanation`
- `implementation_bridge`

说明：

- 类型用于指导前端和生成器，不要求学习者看到
- 类型决定 block 的推荐组合和展示顺序


## 6. block 结构

每个 page 的内容由若干 block 构成。

```json
{
  "type": "why_it_holds",
  "title": "为什么一次遍历恰好得到一个连通分量",
  "content": [
    "遍历只能沿已有边扩展，所以不会跳到别的连通块。",
    "同一连通块内的点对起点都存在路径，遍历会沿路径逐步访问它们。"
  ]
}
```

`content` 可以是：

- 段落数组
- 列表数组
- 代码片段字符串
- trace 行数组


## 7. block type 建议

建议支持：

- `hook`
- `intuition`
- `minimum_example`
- `formal_statement`
- `why_it_holds`
- `trace`
- `comparison`
- `confusion_fix`
- `boundary_case`
- `implementation_bridge`
- `closed_book_retell`
- `mini_check`
- `recap`

注意：

- 不是每个知识点都必须包含全部 block
- 但高重要度 `C3/C4` 点通常应包含：
  - `hook`
  - `minimum_example`
  - `why_it_holds`
  - `trace`
  - `confusion_fix`
  - `closed_book_retell`


## 8. 最小可用要求

第一版 `knowledge-pages.json` 至少要满足：

- 有 `pages`
- 每个 page 有：
  - `page_id`
  - `knowledge_point_id`
  - `title`
  - `complexity_level`
  - `importance_level`
  - `learning_goal`
  - `entry_question`
  - `page_summary`
  - `blocks`
- 每个重点 page 至少有 3 个以上 block


## 9. 与其他文件的映射关系

每个 page 应至少映射到：

- `knowledge-map.json` 中的一个 node
- `detailed-notes.md` 中的一个 anchor
- `practice.md` 中的相关题目
- `review-notes.md` 中的相关卡片或复述模板

这决定了前端是否能真正实现：

- 节点跳页
- 页到题
- 页到复习
- 复习回页


## 10. 生成建议

每个重点知识点在生成 page 前，先生成内部 teaching brief：

- 适合的讲解模式
- 最小例子
- 必讲 why
- 最常见误解
- 闭卷目标
- 预计讲解时长

然后再把 brief 展开成 block。
