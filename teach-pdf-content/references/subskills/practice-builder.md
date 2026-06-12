# Practice Builder Subskill

Use this module when creating or updating `practice.md` and `review-notes.md`.

## Purpose

The vNext learning pack separates:

- `detailed-notes.md`: teach and explain
- `practice.md`: test and diagnose
- `review-notes.md`: compress and reactivate

This module governs the latter two files.

## Learning Objectives

Write each objective as observable performance:

`LOx: The learner can <action> <content> under <condition>; mastery level: <recognize/explain/distinguish/sequence/apply/memorize/diagnose>; mastery means <criterion>; assessed by <question/card id>; source: <page/section>.`

Avoid vague goals like `understand` unless followed by concrete criteria.

## `practice.md` Contract

`practice.md` should convert understanding into output ability.

It should normally contain:

1. usage instructions
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
- type: recall | discrimination | procedure | error-correction | transfer
- difficulty
- target mastery
- prompt
- hint

## `practice.md` Rules

- Keep question sections answer-free except for short hints.
- Put complete answers in final answer-key sections.
- Map every question to one or more knowledge-point IDs.
- Include source basis or mark `teacher-designed prompt, not a source example`.
- Include common wrong answers and scoring or self-check points.
- For graph, tree, traversal, recursion, and algorithm chapters, include process-trace questions. Do not skip them.

## Balanced Practice Set

For a normal chapter, include at least:

- closed-book explanation
- concept discrimination
- procedure or trace
- error diagnosis
- transfer to a new case
- code or implementation task when relevant

Transfer exercises must use a scenario beyond the source example.

## `review-notes.md` Contract

`review-notes.md` is not just a shorter `detailed-notes.md`.

It should reorganize the chapter around recall and fast reactivation.

It should normally contain:

1. 3-minute recall route
2. 10-minute review route
3. must-memorize definitions, rules, and canonical contrasts
4. high-value traps
5. concept comparison quick reference
6. oral retell templates
7. memory-card section
8. wrong-answer recovery rules
9. spaced review plan

## Oral Retell Rule

For each important knowledge cluster, include at least one oral retell template.

A retell template should tell the learner:

- what question to answer
- what skeleton to use
- what must be mentioned
- what is commonly omitted

This is especially important for chapters where the learner can appear to understand while still being unable to explain the mechanism.

## Memory-Card Rule

Do not card everything. Create cards only for high-retrieval items:

- exact definitions expected closed-book
- stable formulas or conditions
- process skeletons
- canonical contrasts
- repeated traps
- short stable `why this design exists` answers

Do not card long prose, broad motivation, or full examples.

## Wrong-Answer Recovery Rule

If a learner misses the same idea twice, change representation rather than only repeating the same wording.

Possible recovery modes:

- smaller example
- trace table
- comparison table
- boundary case
- formula walk-through
- error diagnosis
- oral retell

## Output Check

Before considering `practice.md` and `review-notes.md` complete, verify that:

1. prompt sections do not leak full answers
2. questions map back to knowledge points
3. review notes are recall-oriented rather than just compressed prose
4. hard mechanisms have trace-style practice
5. the learner can see what to review in 3 minutes and 10 minutes
