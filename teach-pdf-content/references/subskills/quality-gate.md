# Quality Gate Subskill

Use this module before finalizing a study pack, when auditing an existing note, or when the user complains that generated notes are rough.

## Completion Standard

A full chapter pack is not complete merely because all files exist. It must be:

- source-grounded
- novice-readable
- practice-connected
- code-connected when relevant
- reviewable without opening the source every minute
- checked by `scripts/check_lesson_pack.py`

## P0 Roughness Failures

Revise before final if any P0 failure appears:

- no source range or source-map evidence
- no chapter problem or conceptual spine
- no chapter map or first-pass route for a dense chapter
- structural topics lack diagram/ASCII sketch
- processes, algorithms, or formulas lack a worked example or trace
- key concepts lack examples, non-examples, or boundaries
- programming/data-structure chapters lack code links or implementation notes
- self-check answers sit immediately after the questions
- wide tables replace explanation
- common mistakes lack correction actions
- the learner cannot tell what to memorize, understand, or practice

## P1 Improvement Warnings

Fix when time allows:

- missing 10-minute review route
- no objective-to-exercise mapping in the note
- source page ranges are too broad for key definitions
- teacher supplements are not labeled consistently
- no difficulty labels for mixed easy/hard material
- no wrong-answer recovery path

## Audit Procedure

1. Read `01-lesson-notes.md` from the top as a first-time learner.
2. Mark missing diagrams, worked examples, trace tables, non-examples, and code links.
3. Check `02-active-recall.md` and `03-exercises.md` have final answer keys.
4. Check `07-code-extracts.md` exists when source/code demands it.
5. Run `scripts/check_lesson_pack.py <study-pack-dir>`.
6. Fix P0 issues before telling the user the pack is complete.

## Reporting

When closing the task, report:

- files created or changed
- checker result
- warnings intentionally left, if any
- file the learner should open first
