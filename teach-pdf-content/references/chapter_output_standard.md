# Chapter Output Standard

Use this reference when generating, auditing, or revising a chapter pack for `teach-pdf-content`.

The default standard is the vNext learner-facing three-file model:

- `detailed-notes.md`
- `practice.md`
- `review-notes.md`

Support files:

- `knowledge-map.json`
- `source-map.md`
- `_meta.json`

Legacy multi-file packs remain compatible, but they are no longer the preferred learner-facing format.

## Chapter Management

Never turn a course, half-book, or long PDF range into one huge Markdown file. Treat the course as a project and each chapter or coherent module as its own study pack.

Default layout:

```text
lessons/<source-id>/
|-- chapter-index.md
`-- chapters/
    `-- <chapter-id>/
        |-- detailed-notes.md
        |-- practice.md
        |-- review-notes.md
        |-- knowledge-map.json
        |-- source-map.md
        `-- _meta.json
```

If the requested range contains more than one chapter or would create a very large note, first create or update `chapter-index.md` with chapter boundaries, source ranges, status, and recommended generation order. Then generate one chapter pack at a time.

## Output Mode Selection

Choose one of these modes before drafting:

- `beginner_lecture`: default mode. Use when learner level is unknown or when the user asks to be taught. Prioritize first-pass comprehension over compression.
- `standard_study_pack`: balanced mode for learners who already had first exposure and want a full pack with teaching plus recall plus review support.
- `review_cram`: condensed mode for explicit review or exam-sprint requests. Use only when the user asks for compression.

If the user does not specify a mode, default to `beginner_lecture`.

## Knowledge-Point-First Rule

Before drafting prose, build the chapter knowledge model.

For each chapter:

1. identify core concepts
2. identify prerequisites
3. identify procedures, algorithms, formulas, and implementation anchors
4. mark which concepts are newly introduced in each subsection
5. assign complexity levels `C1-C4` to new concepts
6. decide teaching depth from complexity rather than from textbook heading size
7. create `knowledge-map.json` before finalizing learner-facing files

Do not simply mirror textbook headings if doing so hurts learning clarity.

## `detailed-notes.md` Contract

`detailed-notes.md` is the main teaching artifact.

It must read like a chapter handout that can teach the learner directly, not like a compressed review sheet or a definition dump.

Every full `detailed-notes.md` must contain:

1. chapter title and source range
2. source-map link, extraction-quality note, and encoding note when relevant
3. chapter problem: what this chapter solves and why it matters
4. prerequisite signal before dependent terms appear
5. chapter knowledge map near the top
6. suggested learning path for first pass and review pass
7. starter example or toy case before the first hard subsection
8. conceptual spine in 3-5 lines
9. core subsection notes with teaching closed loops
10. important distinctions and boundary cases
11. implementation or code bridge when relevant
12. closed-book output templates
13. 10-minute review route

Each core subsection should normally include:

- `本节主问题` / subsection question
- `本节知识点` / subsection knowledge-point table
- `先看一个最小例子`
- `正式结论 / 定义`
- `为什么成立`
- `过程追踪 / Trace`
- `边界、反例与易错点`
- `和相邻概念的区别`
- `代码 / 实现 / 题型连接`
- `本节闭卷输出模板`

If the subsection belongs to trees, graphs, traversal, recursion, state transitions, formulas, or implementation-heavy content, it is incomplete without:

- one minimum example
- one why-it-holds explanation
- one trace or ordered development
- one confusion boundary

## `practice.md` Contract

`practice.md` converts understanding into output ability.

It should contain:

1. how to use this practice file
2. knowledge-point-to-question mapping
3. closed-book explanation questions
4. discrimination questions
5. process-trace questions
6. basic exercises
7. core exercises
8. transfer exercises
9. common-error diagnosis
10. complete answers and scoring

Every question should state:

- question ID
- knowledge-point ID(s)
- type
- difficulty
- target mastery
- prompt
- hint

Prompt sections must stay answer-free except for hints. Complete answers belong in the final answer section.

## `review-notes.md` Contract

`review-notes.md` is not a shorter copy of `detailed-notes.md`.

It should reorganize the chapter for high-density recall and quick reactivation.

It should contain:

1. 3-minute recall route
2. 10-minute review route
3. must-memorize definitions, rules, and contrasts
4. high-value traps
5. concept comparison quick reference
6. oral retell templates
7. memory-card section
8. wrong-answer recovery rules
9. spaced review plan

## `knowledge-map.json` Contract

`knowledge-map.json` is the chapter's internal knowledge model and frontend navigation source.

Minimum requirements:

- top-level metadata
- `nodes`
- `edges`
- `recommended_paths`
- node IDs that map back to:
  - `detailed-notes.md`
  - `practice.md`
  - `review-notes.md`

The knowledge map is not decorative. It should support:

- chapter first-screen knowledge graph
- node-based reading navigation
- node-to-practice mapping
- node-to-review mapping
- study-mode and review-mode highlighting

## Novice Learnability Contract

A structurally complete note can still fail beginners.

Before finalizing a chapter pack:

- prerequisites must appear before dependent terms are used casually
- the first worked example should appear before dense definition tables
- dense or branching chapters need a chapter map near the top
- structural topics need a diagram, ASCII sketch, or labeled table
- procedures, algorithms, conversions, and formulas need a worked step-by-step example
- programming-heavy chapters need a code bridge
- key concepts need a non-example or boundary when confusion is likely
- the learner must be able to tell what to memorize, what to understand, and what to practice

## Answer-Key Placement

For `practice.md`, keep prompt sections answer-free except for short hints.

Put complete answers at the end in:

- `## 完整答案与评分点`
- or `## Complete Answers and Scoring`

Each answer should include:

- complete expected answer
- scoring or self-check points
- common wrong answer or trap
- source basis or teacher-designed note

Do not write `see source` as the answer.

## Concrete Example Rule

Every key knowledge point in `detailed-notes.md` needs a simple concrete example.

Prefer examples that are small enough to understand in one pass:

- definitions: positive example plus non-example when useful
- processes: tiny ordered scenario
- formulas: minimal calculation with symbols explained
- structures: labeled diagram or ASCII sketch
- algorithms: trace table on a tiny input

## Quality Checklist

Rewrite or continue the pack if any failure sign appears:

- the output is mostly a definition dump
- the chapter problem is missing
- the knowledge-point structure is invisible
- the note follows textbook headings mechanically without exposing the chapter's conceptual spine
- a subsection states a result but never explains why it holds
- a graph/tree/algorithm subsection has no trace
- key concepts have definitions but no simple concrete examples
- answers are source citations only and do not include real explanations
- review notes are just compressed prose instead of recall-oriented structure
- the learner cannot tell what must be memorized versus what only needs understanding

## Rough Note Anti-Patterns

These patterns often produce notes that look complete but do not actually teach:

- a big table replaces explanation
- definitions appear before the learner knows why they matter
- review content appears before the first real example in default mode
- examples are too small to train the target skill
- the note gives a conclusion, intuition, and citation, but the learner still has to return to the source for the mechanism
- a formula is stated but never used
- an algorithm is described but never traced
- a structure is described without a diagram
- common mistakes are listed without correction actions

## Legacy Compatibility

Legacy chapter packs remain supported for existing content, migration comparison, or explicit user requests.

When working in legacy mode:

- treat it as compatibility mode
- make clear that it is not the preferred learner-facing output
- prefer migration toward the vNext three-file model whenever possible
