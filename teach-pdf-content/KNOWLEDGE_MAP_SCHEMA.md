# knowledge-map.json 设计规范

## 1. 目标

`knowledge-map.json` 是每章的内部知识模型输出之一，用于：

- 驱动章节首屏知识图谱
- 支撑知识点导向阅读
- 支撑节点跳转到讲义、练习、复习位置
- 支撑“学习模式 / 复习模式”下的不同高亮路径
- 为后续的复杂度分级、练习映射、复习聚合提供统一数据源

它不是学习主文件，但应成为所有主文件的统一索引层。


## 2. 文件位置

建议输出路径：

```text
chapters/<chapter-id>/knowledge-map.json
```


## 3. 顶层结构

建议结构：

```json
{
  "version": "1.0",
  "chapter_id": "07-graph",
  "chapter_title": "第 7 章 图",
  "chapter_problem": "这一章到底在解决什么大问题",
  "source_id": "data-structures-c",
  "output_mode": "beginner_lecture",
  "generated_at": "2026-06-13T12:00:00",
  "recommended_paths": {
    "study": ["kp-01", "kp-02", "kp-05"],
    "review": ["kp-05", "kp-08", "kp-11"]
  },
  "nodes": [],
  "edges": [],
  "clusters": [],
  "exercise_map": [],
  "review_map": []
}
```


## 4. 节点设计

### 4.1 节点字段

每个节点建议至少包含：

```json
{
  "id": "kp-07",
  "title": "连通分量",
  "type": "core_concept",
  "complexity_level": "C3",
  "importance_level": "high",
  "is_new_concept": true,
  "summary": "一句话说明这个知识点在讲什么",
  "teaching_goal": "这一点教会后，学生应该能做什么",
  "section_anchor": "sec-7-4-1",
  "notes_anchor": "detailed-notes#sec-7-4-1",
  "practice_anchor": "practice#q-connectivity",
  "review_anchor": "review-notes#review-connectivity",
  "prerequisites": ["kp-03", "kp-04"],
  "related_formulas": [],
  "related_code": ["code-03"],
  "related_exercises": ["Q4", "E3"],
  "common_confusions": ["kp-08"],
  "tags": ["dfs", "bfs", "connectivity", "traversal"]
}
```

### 4.2 节点类型

建议的 `type`：

- `core_concept`
- `prerequisite`
- `procedure`
- `formula`
- `comparison`
- `implementation`
- `application`

### 4.3 复杂度等级

`complexity_level`：

- `C1`
- `C2`
- `C3`
- `C4`

解释：

- `C1`：轻量概念
- `C2`：标准概念
- `C3`：复杂概念
- `C4`：高复杂度概念

### 4.4 重要度等级

`importance_level`：

- `high`
- `medium`
- `low`

建议语义：

- `high`：主线，不懂会卡整章
- `medium`：支撑点，不懂会影响部分题型
- `low`：扩展点，不懂不影响第一遍学习


## 5. 边设计

### 5.1 边字段

```json
{
  "id": "edge-12",
  "from": "kp-07",
  "to": "kp-09",
  "type": "explains",
  "weight": "strong",
  "note": "说明关系的短注释"
}
```

### 5.2 边类型

建议支持：

- `requires`
- `explains`
- `contrasts`
- `implements`
- `applies_to`
- `reviews_with`

说明：

- `requires`：A 是 B 的前置
- `explains`：A 帮助理解 B
- `contrasts`：A 与 B 容易混
- `implements`：A 在代码里落到 B
- `applies_to`：A 用在 B 场景
- `reviews_with`：复习时建议联看


## 6. 知识簇设计

章节知识图谱不应只是散点图，还应有“知识簇”。

### 6.1 cluster 字段

```json
{
  "id": "cluster-traversal",
  "title": "图的遍历与副产物",
  "summary": "这一簇讲图怎么被系统地走完，以及遍历会带来哪些结构性结果",
  "node_ids": ["kp-05", "kp-06", "kp-07", "kp-08"],
  "recommended_order": ["kp-05", "kp-06", "kp-07", "kp-08"]
}
```

### 6.2 建议簇类型

对于数据结构章节，通常可形成：

- 概念簇
- 表示法簇
- 过程簇
- 应用簇
- 易混辨析簇


## 7. 练习映射

### 7.1 exercise_map 字段

```json
{
  "knowledge_point_id": "kp-07",
  "exercise_ids": ["Q4", "E3"],
  "exercise_types": ["recall", "procedure"],
  "mastery_requirement": "能闭卷解释一次 DFS/BFS 为什么得到一个连通分量"
}
```

### 7.2 作用

- 从知识点跳到练习
- 从练习反查讲义
- 为复习模式筛出高价值练习


## 8. 复习映射

### 8.1 review_map 字段

```json
{
  "knowledge_point_id": "kp-07",
  "review_priority": "high",
  "memory_type": "conceptual",
  "review_anchor": "review-notes#review-connectivity",
  "card_ids": ["C04", "T02"],
  "oral_prompt": "说明一次遍历为什么恰好找到一个连通分量"
}
```

### 8.2 作用

- 给复习页聚合内容
- 给口头复述模式提供提示
- 给卡片模式提供筛选


## 9. 推荐路径

### 9.1 study 路径

表示初学者推荐起步路径。

要求：

- 优先主线知识点
- 避免一上来进入高复杂度边缘点
- 能形成完整理解链

### 9.2 review 路径

表示复习者推荐路径。

要求：

- 优先高价值回捞点
- 优先易错点
- 优先题型高频点


## 10. 节点复杂度判定规范

每个节点建议记录内部评分依据，但不一定暴露给前端。

可选字段：

```json
{
  "complexity_score": {
    "novelty": 2,
    "abstraction": 1,
    "dependency_depth": 2,
    "dynamics": 2,
    "error_proneness": 2,
    "source_ambiguity": 1,
    "total": 10
  }
}
```

建议映射：

- `0-2` -> `C1`
- `3-5` -> `C2`
- `6-8` -> `C3`
- `9-12` -> `C4`


## 11. 最小可用要求

首版 `knowledge-map.json` 至少应满足：

- 有 `nodes`
- 有 `edges`
- 有 `recommended_paths`
- 每个节点有 `id/title/type/complexity_level/section_anchor`
- 每个节点能映射到讲义位置

这样即使前端首版只做简单图谱，也已经可以工作。


## 12. 面向前端的直接用途

前端可直接利用该文件实现：

- 首屏知识图谱
- 节点点击跳转
- 模式切换时的推荐路径高亮
- C1-C4 复杂度过滤
- high/medium/low 重要度过滤


## 13. 实施建议

建议先手工为 `07-graph` 和 `06-tree-binary-tree` 各做一份示范 `knowledge-map.json`，校准：

- 节点粒度是否合适
- 一个节点是否应该是“概念”还是“关系”
- 图谱是否真的服务学习路径，而不是装饰

校准完成后再把 schema 接入自动生成流程。
