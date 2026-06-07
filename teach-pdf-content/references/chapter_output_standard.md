# Chapter Output Standard

Use this reference when generating chapter notes, auditing user notes, deciding mastery depth, or creating memory cards. It merges the former chapter-note and chapter-memory-card workflows into the main `teach-pdf-content` process.

## Chapter Management

Never turn a course, half-book, or long PDF range into one huge Markdown file. Treat the course as a project and each chapter or coherent module as its own study pack.

Default layout:

```text
lessons/<source-id>/
|-- chapter-index.md
`-- chapters/
    |-- 01-<chapter-slug>/
    |   |-- 00-learning-path.md
    |   |-- 01-lesson-notes.md
    |   |-- 02-active-recall.md
    |   |-- 03-exercises.md
    |   |-- 04-glossary.md
    |   |-- 05-review-plan.md
    |   |-- 06-memory-cards.md
    |   `-- source-map.md
    `-- 02-<chapter-slug>/
```

If the requested range contains more than one chapter or would create a very large note, first create or update `chapter-index.md` with chapter boundaries, source ranges, status, and the recommended generation order. Then generate one chapter pack at a time.

## Chapter Note Contract

A real chapter note must be source-bounded, novice-readable, recall-friendly, and strict enough for later closed-book review.

Before writing or rewriting notes:

1. Confirm the source range.
2. Read the user's existing note if provided.
3. Audit coverage, source traceability, conceptual structure, beginner readability, recall value, and error risk.
4. If a user note is empty or nearly empty, state that no content comparison is possible and switch to a gap comparison.

Every full chapter note must contain:

1. chapter title and source range
2. chapter problem: what problem this chapter solves and why it matters
3. conceptual spine in 3-5 lines
4. key concepts with definition, intuition, one simple concrete example, easy confusion, and source
5. core subsection notes with closed loops
6. mechanisms, lifecycle steps, or argument flow in order
7. important distinctions and boundary cases
8. common mistakes or traps
9. closed-book checks with answer keys
10. minimum mastery standard

## Subsection Closed Loop

For each core subsection, write a closed loop instead of a loose explanation:

```markdown
### x.x Subsection title

- Question this subsection answers:
- Short conclusion:
- Source evidence:
- Intuition:
- Simple concrete example:
- Mechanism / development:
- Why this design or idea exists:
- Boundary / common confusion:
- Minimum self-check:
- Self-check answer key:
```

A hard subsection is incomplete if it only has a definition, a flow without purpose, a conclusion without mechanism, or a mechanism without boundary. At least one of these must appear: why the mechanism exists, what problem it prevents, what similar concept it differs from, or what error a beginner is likely to make.

## Knowledge Mastery Contract

For each key knowledge point, specify the required mastery depth. Avoid vague labels such as "understand" unless the expected performance is observable.

Use these levels:

- `Recognize`: identify the concept, symbol, state, or claim when seen.
- `Explain`: explain the idea in plain language and precise terms.
- `Distinguish`: separate it from a similar concept, boundary case, or common trap.
- `Sequence`: retell ordered steps, lifecycle, proof outline, or argument flow.
- `Apply`: use the idea in a new exercise, scenario, calculation, diagnosis, or implementation.
- `Memorize`: reproduce exact names, conditions, short definitions, ordered states, or canonical contrasts.
- `Diagnose`: identify why a proposed answer, interpretation, or solution is wrong.

Every learning objective or key concept should state the mastery level, closed-book criterion, assessment item, and source reference.

## Answer-Key Placement

For recall questions and exercises, keep the prompt section answer-free. The prompt section may contain a short hint, source range, or relevant objective, but it must not include the complete answer.

Put complete answers at the end of the file in a dedicated answer-key section:

- For `02-active-recall.md`, use `## 答案区` or `## Answer Key`.
- For `03-exercises.md`, use `## 完整答案与评分标准` or `## Complete Answers and Scoring`.

Every answer key must include enough content for self-study:

- the complete expected answer, not only a source citation
- scoring or self-check points
- common wrong answer or trap
- complete code when the question asks for code
- source basis or teacher-designed note

Do not write "see source" as the answer. Source references support the answer; they do not replace it.

## Concrete Examples

Every key knowledge point in `01-lesson-notes.md` needs a simple concrete example. Prefer examples that are small enough to understand in one pass:

- For definitions: give one positive example and, when useful, one non-example.
- For processes: give a tiny ordered scenario.
- For formulas: give a minimal calculation with symbols explained.
- For code/API concepts: give a short runnable or copyable snippet when possible.
- For abstract theory: give a toy case before any complex case.

Mark examples as source-backed when they come from the source. Mark teacher-created examples as teacher supplements.

## Code Extraction

When the source contains code, especially scanned/OCR code, create `07-code-extracts.md` so the learner can read and copy code separately from prose notes.

For each snippet, include:

- source location: PDF page, book page, section, or figure/listing number
- language if known
- OCR reliability: high, medium, low, or needs manual verification
- cleaned copyable code block
- notes on uncertain tokens, missing indentation, wrapped lines, or source formatting
- short explanation of what the snippet demonstrates

Never silently "fix" uncertain scanned code. Use `待核对` / `Needs verification` for ambiguous identifiers, operators, punctuation, indentation, or line breaks.

## Study Time Table

Every chapter pack must include a per-chapter study time table in `00-learning-path.md`. The table should map study blocks to source sections, objectives, tasks, minutes, and completion checks.

Use realistic, bounded blocks:

- first pass reading
- core concept explanation
- closed-book recall
- exercises or code practice
- memory cards and review

If the learner gives a deadline or available time, fit the table to that constraint. If not, provide a standard plan plus a compressed plan.

## Memory Card Selection

Memory cards are part of the full study-pack workflow, not a separate skill. Create `06-memory-cards.md` only after the chapter note and learning objectives are clear.

Do not card everything. Make cards only for high retrieval value items:

- exact definitions the course expects the learner to reproduce
- state names and meanings
- lifecycle or process steps
- API/function roles only when they are core checkpoints
- direct contrasts a teacher could ask
- stable, short "why this design exists" answers
- canonical traps that repeatedly cause wrong answers

Skip items better learned by understanding than memorization:

- long prose explanations
- broad motivation text with no stable answer
- implementation trivia with no review value
- full examples that only illustrate the mood of a rule

## Card Rules

Every card must obey these rules:

1. One card tests one target fact, distinction, sequence, or trap.
2. The front side asks one thing only.
3. The back side fits in 1-4 bullets or one short paragraph.
4. If the card depends on contrast, the contrast appears in the prompt.
5. If the card tests sequence, the answer is ordered.
6. If the card needs "and also", split it.

Preferred card types:

- definition
- distinction
- sequence
- condition -> result
- misconception repair
- cloze, only for exact names, flags, or ordered terms

Group cards into `Core`, `Secondary`, and `Trap`. Add a 3-minute oral review at the end with 5-10 speakable bullets.

## Quality Checklist

Rewrite or continue the note if any failure sign appears:

- The output is mostly a definition dump.
- The chapter problem is missing.
- The conceptual spine is not visible early.
- Key concepts have definitions but no simple concrete examples.
- The reader cannot tell sequence, causality, or boundaries.
- Questions contain full answers inline instead of keeping answers in the final answer key.
- Answers are source citations only and do not include complete explanations or code.
- Scanned/OCR code is mixed into prose notes instead of being cleaned into `07-code-extracts.md`.
- The chapter has no study time table.
- Names of functions, states, variables, or theories appear without their role.
- A subsection explains "what" but never closes the loop on "why", "how", or "how to check".
- Review questions have no answer keys.
- The learner cannot tell what must be memorized versus what only needs understanding.
- The generated Markdown is so large that it is hard to open or review.
