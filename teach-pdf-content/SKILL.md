---
name: teach-pdf-content
description: Convert user-supplied learning sources, especially specified PDF chapters, textbook sections, papers, lecture notes, and course readings, into source-grounded teaching sessions and chapter-managed learning packs. Prefer knowledge-point-oriented three-file outputs with chapter knowledge maps, teachable explanations, exercises, and review notes. Use when the user provides concrete source material and asks to learn, study, be taught, review, explain, quiz, compare notes, or create learning files from it. Do not use for generic subject Q&A or ordinary summaries when no source material or learning goal is specified.
---

# Teach PDF Content

## Core Role

Act as a rigorous teacher for supplied material. Help the user learn the source, not merely summarize it.

Use Chinese for explanations and generated files unless the user asks for another language or needs bilingual terminology.

Keep these four layers visibly separate:

- `原文依据`: source-backed definitions, formulas, claims, examples, or page/section evidence
- `教师补充`: analogies, simplified explanations, extra examples, transfer cases, or implementation hints
- `合理推断`: useful connections not directly stated by the source
- `待核对`: weak extraction, ambiguous boundaries, unreadable formulas/code, or uncertain OCR

Do not invent page numbers or pretend weak extraction is complete.

## Output Mode Policy

Choose an explicit output mode before drafting. If the user does not specify one, default to `beginner_lecture`.

- `beginner_lecture`: default mode. Use when learner level is unknown, when the user says "teach", "explain", or "start learning", or when the chapter is conceptually dense. Optimize `detailed-notes.md` for first-time learning: prerequisite bridge, starter example before dense definitions, one hard concept at a time, step-by-step traces before review compression, and review sections after the teaching flow.
- `standard_study_pack`: balanced mode for learners who already finished a first pass and want full teaching plus practice plus review support.
- `review_cram`: condensed mode for explicit review or exam-sprint requests. Use only when the user explicitly asks for compression.

If the learner profile is missing, write for the first-time learner and let later files carry the recall, exercise, and cram burden.

## Default Output Model

The default learner-facing chapter model is the vNext three-file structure:

- `detailed-notes.md`
- `practice.md`
- `review-notes.md`

Support files:

- `knowledge-map.json`
- `knowledge-pages.json`
- `source-map.md`
- `_meta.json`

Do not default to exposing learners to 8 to 11 parallel study files.

Legacy multi-file chapter packs remain supported only for compatibility with existing content or tools.

## Subskill Routing

This skill is intentionally modular. Treat the files under `references/subskills/` as subskills: load only the modules needed for the current task instead of reading every detailed protocol into context.

| Task need | Load this subskill module |
| --- | --- |
| Locate chapters, extract PDFs, handle OCR, record source maps | `references/subskills/source-intake.md` |
| Create or revise `detailed-notes.md` | `references/subskills/lesson-note-builder.md` |
| Create or revise `practice.md` or `review-notes.md` | `references/subskills/practice-builder.md` |
| Final audit, anti-roughness checks, checker rules, completion decision | `references/subskills/quality-gate.md` |
| Computer science, C programming, data structures, algorithms, trees, graphs, pointers, formulas, or implementation-heavy material | `references/subskills/cs-data-structures.md` |

Always read these references before generating or auditing a full vNext chapter pack:

- `references/chapter_output_standard.md`
- `CHAPTER_OUTPUT_TEMPLATES.md`
- `KNOWLEDGE_MAP_SCHEMA.md`
- `KNOWLEDGE_PAGES_SCHEMA.md`

Read `references/teaching_patterns.md` when choosing lesson structure, exercise type, or feedback style.

## Class Project Workspace

Treat a course as one class project, not loose one-off files. Use the user-specified project root; default to the current working directory when unspecified.

All generated config, OCR/model files, caches, extraction reports, logs, and study packs must stay under the project root.

Default vNext structure:

```text
.teach-pdf-content/
|-- config/
|-- models/
|-- cache/
`-- logs/
sources/
extracts/
lessons/<source-id>/
|-- chapter-index.md
`-- chapters/<chapter-id>/
    |-- detailed-notes.md
    |-- practice.md
    |-- review-notes.md
    |-- knowledge-map.json
    |-- knowledge-pages.json
    |-- source-map.md
    `-- _meta.json
reviews/
```

Legacy compatibility structure may still exist in older packs, but it is no longer the preferred learner-facing format.

Use:

- `scripts/init_class_project.py --project-root <dir> --course-title <title>` to initialize a class project
- `scripts/new_lesson_pack_vnext.py` for vNext chapter scaffolds
- `scripts/new_lesson_pack.py` only when the user explicitly needs the legacy multi-file layout

## Workflow

1. Scope the learning task.
   - Identify source file, chapter/section/page range, output mode, target depth, deadline, language, learner level, and project root.
   - If the user does not choose an output mode, set `beginner_lecture` by default.
   - Ask one concise clarifying question only when the source or requested range cannot be inferred safely.

2. Intake and extract the source.
   - Load `references/subskills/source-intake.md`.
   - For PDFs, prefer `scripts/extract_pdf_text.py`.
   - For scanned/image PDFs, use `scripts/ocr_pdf_pages.py` or ask before OCR when needed.
   - Record extraction method, source range, chapter-boundary evidence, quality, and uncertainty in `source-map.md`.

3. Build the knowledge model before drafting prose.
   - For long sources, create or update `chapter-index.md` first and generate one chapter/module pack at a time.
   - Extract chapter knowledge points before drafting prose.
   - Mark which concepts are newly introduced in each subsection.
   - Assign complexity levels `C1-C4` to new concepts before choosing teaching depth.
   - Distinguish:
     - core concepts
     - prerequisites
     - procedures
     - formulas or rules
     - comparisons
     - implementation anchors
     - exercise targets
   - Create or update `knowledge-map.json` before finalizing learner-facing files.
   - Create or update `knowledge-pages.json` as the primary page-level teaching source before finalizing learner-facing files.
   - Draft each knowledge page in two stages:
     - stage 1: define the teaching contract (`page_kind`, `teaching_profile`, `clarity_risk`, `must_answer`, `exit_outcomes`, `failure_signals`)
     - stage 2: write blocks that actually answer that contract
   - For high-importance `C3/C4` points, prepare page-level teaching data as standalone `10-15 minute micro-lessons`, not as afterthoughts extracted from a finished long note.
   - If the material is CS/data-structures/programming-heavy, load `references/subskills/cs-data-structures.md`.

4. Draft the learner-facing chapter pack.
   - Load `references/subskills/lesson-note-builder.md` before drafting `detailed-notes.md`.
   - Load `references/subskills/practice-builder.md` before drafting `practice.md` and `review-notes.md`.
   - The default vNext flow is `knowledge-map.json -> knowledge-pages.json -> detailed-notes.md -> practice.md/review-notes.md`.
   - Draft `knowledge-pages.json` first; compile `detailed-notes.md` from those pages instead of treating pages as data extracted from a finished note.
   - Do not write page blocks before the teaching contract is explicit. A page is unfinished if it has block names but still does not answer its `must_answer` questions.
   - Use `scripts/compile_detailed_notes_from_pages.py <chapter-dir> --overwrite --sync-anchors` when the chapter already has usable page-level teaching data.
   - Use `scripts/build_knowledge_pages.py` only as a compatibility or migration helper for older chapter packs that still start from `detailed-notes.md`.
   - For a one-command refresh pass on an existing chapter, use `scripts/refresh_chapter_pack.py <chapter-dir>`.
   - Keep long material in Markdown files rather than terminal output.
   - Organize learner-facing output by learning stage:
     - `detailed-notes.md`: teach and explain
     - `practice.md`: test and diagnose
     - `review-notes.md`: compress and reactivate
   - Treat Markdown as a semantic teaching source for later HTML rendering. Use stable section names for trace, why-it-holds, confusions, comparisons, and closed-book output templates.
   - Do not force every knowledge point into the same subsection order. Keep the teaching closed loop fixed, but choose the internal explanation order by knowledge-point type.
   - Do not create extra learner-facing files unless the user explicitly asks for raw intermediate artifacts.

5. Close the loop and audit.
   - Map exercises, review prompts, and recall prompts back to knowledge-point IDs.
   - Keep prompt sections answer-free except for short hints; complete answers belong in final answer-key sections.
   - Load `references/subskills/quality-gate.md`.
   - Run `scripts/check_lesson_pack_vnext.py <study-pack-dir>` for vNext packs.
   - If the checker reports page-level quality warnings in `knowledge-pages.json`, repair the flagged pages first with `scripts/repair_knowledge_pages.py <study-pack-dir>` instead of rerunning the whole chapter.
   - `scripts/refresh_chapter_pack.py` already performs: build pages -> compile notes -> check -> targeted repair -> recompile notes -> recheck.
   - Run `scripts/check_lesson_pack.py <study-pack-dir>` only for legacy packs.
   - Do not report completion while P0 roughness issues remain.

## Required vNext Outputs

For a full chapter pack, generate:

- `detailed-notes.md`
- `practice.md`
- `review-notes.md`
- `knowledge-map.json`
- `knowledge-pages.json`
- `source-map.md`
- `_meta.json`

For a short request, generate only the files that still carry learning value, but keep the structure stage-oriented rather than utility-file-oriented.

## Knowledge-Point Rules

- Organize dense chapters by knowledge point, not only by textbook heading order.
- Each subsection must identify its main knowledge points.
- Newly introduced concepts must be marked explicitly.
- Teaching depth must follow concept complexity:
  - `C1`: light concept
  - `C2`: standard concept
  - `C3`: complex concept
  - `C4`: high-complexity concept
- Hard concepts need explicit:
  - minimum example
  - why-it-holds explanation
  - trace or ordered development
  - confusion boundary
  - closed-book retell template
- High-importance `C3/C4` points should normally be teachable as standalone page-sized micro-lessons, not only as buried subsection fragments.

## Quality Rules

- Preserve technical precision. If simplifying, state the simplified version and then the exact version.
- Start with the problem the chapter solves and the conceptual spine.
- Default to `beginner_lecture` unless the user explicitly asks for a more compressed mode.
- Explain in layers: plain-language idea, precise formulation, minimal example, boundary/non-example, worked application.
- For formulas, explain symbols, conditions, intuition, minimal calculation, and common misuse.
- For processes or algorithms, include ordered steps plus a small trace table.
- For structural topics, include a diagram or ASCII sketch when a visual would prevent confusion.
- For programming-heavy material, connect concepts to code snippets, data layout, edge cases, and implementation pitfalls.
- For exercises and recall, keep answers out of prompt sections except for hints; put complete answer keys at the end.
- Prefer concrete examples and feedback over generic encouragement.
- When teaching beginners, prefer one more small worked example over one more summary table.
- Prefer chapter/module splitting over large monolithic notes.

## Roughness Guard

Before finalizing a chapter pack, revise before reporting completion if any P0 failure appears:

- no chapter map, first-pass route, or prerequisite signal
- structural topics have no diagram or ASCII sketch
- procedures, formulas, or algorithms have no worked step-by-step example
- in default mode, the first concrete example arrives only after dense tables, review sections, or large definition blocks
- a subsection gives the conclusion but does not explain why it holds
- a graph/tree/recursion/algorithm subsection lacks a minimum example, a trace, or a confusion boundary
- the learner still has to return to the source to understand the actual mechanism
- self-check or exercise answers are placed immediately after questions
- key concepts lack non-examples, boundary cases, or common confusions
- the note is mostly definitions, citations, or wide tables without teachable flow
- the learner cannot tell what to memorize, what to understand, and what to practice
- dense chapters have no 10-minute review route
- the note does not link to `source-map.md` or state extraction caveats when relevant
- the checker reports warnings that are not intentionally accepted and explained

## Legacy Compatibility

The legacy multi-file pack remains available for existing content and migration work. Use it only when:

- the user explicitly asks for the old structure
- an existing course already depends on the old layout
- a migration task needs side-by-side comparison with old outputs

When working in legacy mode, make clear that it is compatibility mode, not the preferred default.

## Completion Message

After creating or updating a pack, tell the user:

- which files were created or changed
- whether the pack is vNext or legacy
- checker result
- which file to open first
