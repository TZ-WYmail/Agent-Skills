# Quality Gate Subskill

Use this module before finalizing a study pack, when auditing an existing note, or when the user complains that generated notes are rough.

## Completion Standard

A chapter pack is not complete merely because files exist.

A vNext pack must be:

- source-grounded
- novice-readable
- teaching-first by default unless the user explicitly asked for compressed review mode
- knowledge-point-organized
- practice-connected
- reviewable without opening the source every minute
- checked by `scripts/check_lesson_pack_vnext.py`

Legacy packs may still be checked by `scripts/check_lesson_pack.py`.

## P0 Roughness Failures

Revise before final if any P0 failure appears:

- no source range or source-map evidence
- no chapter problem or conceptual spine
- no chapter knowledge map or recommended route for a dense chapter
- default-mode note has no prerequisite reminder or starter example
- in default mode, review or checklist content arrives before the first real example
- structural topics lack diagram or ASCII sketch
- processes, algorithms, or formulas lack a worked example or trace
- a subsection gives a conclusion but does not explain why it holds
- a graph/tree/recursion/algorithm subsection lacks a minimum example, a trace, or a confusion boundary
- key concepts lack examples, non-examples, or boundaries
- practice prompts leak full answers
- review notes are just compressed prose instead of recall-oriented structure
- wide tables replace explanation
- the learner cannot tell what to memorize, understand, or practice
- the learner still has to return to the source for the actual mechanism

## P1 Improvement Warnings

Fix when time allows:

- missing 10-minute review route
- no knowledge-point-to-question mapping
- source page ranges are too broad for key definitions
- teacher supplements are not labeled consistently
- no wrong-answer recovery path
- no oral retell templates for dense conceptual clusters

## Audit Procedure

1. Read `detailed-notes.md` from the top as a first-time learner.
2. Mark missing prerequisite bridges, starter examples, diagrams, worked examples, why-it-holds explanations, traces, boundaries, and retell templates.
3. Check `practice.md` keeps prompts answer-free and includes a final answer section.
4. Check `review-notes.md` includes a 3-minute route, a 10-minute route, and wrong-answer recovery guidance.
5. Check `knowledge-map.json` exists and its node IDs map back into the learner-facing files.
6. Run `scripts/check_lesson_pack_vnext.py <study-pack-dir>`.
7. Fix P0 issues before telling the user the pack is complete.

## Reporting

When closing the task, report:

- files created or changed
- whether the pack is vNext or legacy
- checker result
- warnings intentionally left, if any
- file the learner should open first
