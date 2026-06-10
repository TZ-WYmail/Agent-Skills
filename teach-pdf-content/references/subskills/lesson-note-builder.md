# Lesson Note Builder Subskill

Use this module before drafting or revising `01-lesson-notes.md`.

## Purpose

The chapter note must be source-bounded, novice-readable, recall-friendly, and exercise-ready. It should teach the chapter, not merely compress the source.

## Output Mode Default

Choose an output mode before drafting. If the user does not specify a mode, use `beginner_lecture`.

- `beginner_lecture`: default. Teach the chapter in first-pass order and delay review compression until after the main explanation.
- `standard_study_pack`: balanced teaching plus review support.
- `review_cram`: condensed review-only mode for explicit cram requests.

## Required Opening

Every full `01-lesson-notes.md` should start with:

1. title and source range
2. source-map link, extraction-quality note, and UTF-8 note when files are created on Windows
3. output mode and why it was chosen when not obvious
4. how to use this note
5. prerequisite reminder
6. starter example or toy case for the first pass
7. chapter map or knowledge tree
8. first-pass / second-pass / extension route
9. chapter problem and conceptual spine
10. links to relevant pack files such as `02-active-recall.md`, `03-exercises.md`, `07-code-extracts.md`, and `source-map.md`

## Key Concept Contract

For each key concept include:

- minimal definition
- intuition
- positive example
- non-example or boundary
- common confusion
- required mastery level
- closed-book criterion
- source reference

Split wide concept tables when they become hard to read. Prefer two small tables over one seven-column table.

## Closed-Loop Subsections

Each core subsection should answer:

- What question does this subsection answer?
- What is the short conclusion?
- What is the source evidence?
- What is the intuition?
- What is the smallest useful example?
- What is the mechanism, lifecycle, proof idea, or procedure?
- Why does this design or idea exist?
- What boundary or common confusion prevents misuse?
- What self-check tests the idea?
- Where is the answer key?

Do not put complete self-check answers immediately after the question. Use a final answer area or a collapsible answer block.

## Example Type Rules

Choose the example format by material type:

- Definition: positive example + non-example.
- Structure: ASCII diagram + labeled parts.
- Formula: symbol meanings + minimal calculation + misuse.
- Algorithm/process: ordered steps + trace table.
- Code concept: minimal snippet + one implementation pitfall.
- Conversion rule: before/after diagram.
- Abstract theory: toy case before general statement.

For `beginner_lecture`, place the first worked example before large summary tables whenever possible.

## Beginner Readability Rules

- Introduce prerequisites before using dependent terms.
- In `beginner_lecture`, do not open with a review checklist, a large concept table, or mastery standards before the learner sees the first concrete example.
- Mark what must be memorized, what must be understood, and what must be practiced.
- Add difficulty labels when a chapter mixes basic and advanced content.
- Do not let a large table replace explanation.
- Use short paragraphs and local examples before broad summaries.
- Include a "10-minute review route" for dense chapters.
- Add an objective/practice mapping so learners can prove each completion standard.
- Keep source-evidence labels consistent; do not mix unlabeled source facts and teacher supplements.
- If a page range is broad, identify the exact page or subsection for core definitions when possible.

## Required Closing Sections

For full notes, close with:

- `必须闭卷记住` / `Must Memorize`: exact definitions, formulas, ordered steps, and canonical contrasts.
- `理解即可`: ideas that should be explainable but not memorized word-for-word.
- `练习映射`: minimum completion standards mapped to recall/exercise IDs.
- `考前 10 分钟速读`: a short route through the most important definitions, diagrams, formulas, and traps.
- separated self-check and closed-book answer areas.

## Output Check

Before considering the note complete, verify that a learner can:

1. explain the chapter problem,
2. draw or trace the core structures/processes,
3. do one worked example per hard concept, with the first hard concept introduced through an example instead of a table dump,
4. distinguish the main confusions,
5. find the matching recall/exercise/code file.
