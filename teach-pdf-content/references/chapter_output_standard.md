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
2. source-map link, source range, extraction-quality note, and encoding note when relevant
3. how to use this note and which companion files to open
4. chapter map or knowledge tree for dense chapters
5. first-pass, second-pass, and extension route when the chapter mixes difficulty levels
6. chapter problem: what problem this chapter solves and why it matters
7. conceptual spine in 3-5 lines
8. key concepts with definition, intuition, one simple concrete example, easy confusion, non-example or boundary, and source
9. core subsection notes with closed loops
10. mechanisms, lifecycle steps, or argument flow in order
11. important distinctions and boundary cases
12. common mistakes or traps with correction actions
13. closed-book checks with separated answer keys
14. minimum mastery standard
15. must-memorize vs understand-only split
16. practice mapping from mastery standards to recall/exercise IDs
17. 10-minute review route for dense chapters

## Novice Learnability Contract

A note that is structurally complete can still be too rough for a beginner. For full chapter notes, add the missing representation before finalizing:

- Dense or branching chapters need a chapter map near the top.
- Structural concepts need a diagram, ASCII sketch, or labeled table.
- Procedures, algorithms, conversions, and formulas need a worked step-by-step example.
- Programming-heavy chapters need a code bridge: data layout, snippet reference, empty/null case, and implementation pitfall.
- Key concepts need a non-example or boundary when confusion is likely.
- The reader must be able to tell what to memorize, what to understand, and what to practice.
- Self-check answers must not sit immediately after the question unless hidden in a collapsible answer block.

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
- Answer location:
```

A hard subsection is incomplete if it only has a definition, a flow without purpose, a conclusion without mechanism, or a mechanism without boundary. At least one of these must appear: why the mechanism exists, what problem it prevents, what similar concept it differs from, or what error a beginner is likely to make.

Put complete subsection self-check answers in a final `## 小节自测答案区` / `## Subsection Self-Check Answer Key` section, or hide them in `<details>` blocks. Do not train the learner to read the answer before attempting recall.

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
- For structures: give a labeled diagram or ASCII sketch.
- For conversions: give before/after representation and one trace step.
- For algorithms: give a trace table on a tiny input.

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

## Rough Note Anti-Patterns

These patterns are especially likely to produce notes that look complete but do not teach well:

- A big table replaces explanation.
- Definitions appear before the learner knows why they matter.
- Examples are too small to train the target skill.
- A formula is stated but never used.
- An algorithm is described but never traced.
- A structure is described without a diagram or representation.
- Code exists in `07-code-extracts.md` but `01-lesson-notes.md` never points to it.
- Common mistakes are listed without correction actions.
- Source citations are present but the learning path is unclear.
- The note gives the self-check answer before the learner has a chance to recall.
