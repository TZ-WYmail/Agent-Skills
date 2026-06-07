---
name: teach-pdf-content
description: Convert user-supplied learning sources, especially specified PDF chapters, textbook sections, papers, lecture notes, and course readings, into source-grounded teaching sessions and chapter-managed Markdown study packs with objectives, mastery standards, notes, recall questions, exercises, answers, glossaries, review plans, and memory cards. Use when the user provides or references concrete source material and asks to learn, study, be taught, review, explain, quiz, compare notes, create chapter notes, create flashcards, or create learning files from it. Do not use for generic subject Q&A or ordinary summaries when no source material or learning goal is specified.
---

# Teach PDF Content

## Core Role

Act as a rigorous teacher for supplied material. Help the user learn the source, not merely summarize it. Use Chinese for explanations and generated files unless the user asks for another language or needs bilingual terminology.

Keep the source boundary clear: source-backed claims, teacher-created explanations, and uncertain extraction notes must be visibly different.

## Class Project Workspace

Treat a course as one class project, not as loose one-off files. Use the user-specified project root; default to the current working directory when the user does not specify one.

All generated config, model files, OCR images/text, caches, extraction reports, logs, and study packs must stay under the project root. Do not write model caches or config into the user home directory unless the user explicitly asks for a global install.

Use this structure:

- `.teach-pdf-content/config/`: class project config.
- `.teach-pdf-content/models/`: local OCR/model files such as Tesseract `tessdata` or PaddleOCR model cache.
- `.teach-pdf-content/cache/`: temporary rendered pages and intermediate artifacts.
- `.teach-pdf-content/logs/`: OCR/extraction/check reports.
- `sources/`: source PDFs or links to source files.
- `extracts/`: text extraction and OCR outputs.
- `lessons/`: generated study packs by source and chapter/module.
- `reviews/`: review plans, wrong-answer logs, and session follow-ups.

Initialize this structure with `scripts/init_class_project.py --project-root <dir> --course-title <title>`. Use `scripts/ocr_pdf_pages.py --project-root <dir>` for scanned/image PDFs so rendered images, OCR text, and OCR logs stay inside the class project.

Default lesson layout:

```text
lessons/<source-id>/
|-- chapter-index.md
`-- chapters/
    `-- <chapter-id>/
        |-- 00-learning-path.md
        |-- 01-lesson-notes.md
        |-- 02-active-recall.md
        |-- 03-exercises.md
        |-- 04-glossary.md
        |-- 05-review-plan.md
        |-- 06-memory-cards.md
        |-- 07-code-extracts.md
        `-- source-map.md
```

## Workflow

1. Scope the learning task.
   - Identify the source file, requested chapter/section/page range, output mode, target depth, deadline, and language preference.
   - Identify the class project root before creating files. If unspecified, use the current directory.
   - Decide whether the request is a single chapter/module or a multi-chapter course job. Do not create one giant Markdown file for a long range.
   - Build a learner profile when possible: current level, goal, available time, exam/homework/project context, and whether bilingual terminology is needed.
   - Ask one concise clarifying question only when the source or requested range cannot be inferred safely.

2. Locate and extract the source.
   - For PDFs, prefer `scripts/extract_pdf_text.py` when available. Otherwise use `pdftotext`, `mutool`, or installed Python PDF libraries.
   - Treat `extract_pdf_text.py` primarily as a page extraction and quality-report tool. Use its chapter-location output only as candidate start-page evidence, not as final proof.
   - Distinguish `[PDF p.x]` physical PDF pages, `[Book p.y]` printed page numbers, and `[Section z]` source sections.
   - Record extraction tool, command or method, physical page range, printed page range if visible, chapter-boundary evidence, and extraction quality.
   - If chapter location confidence is low, show the evidence and ask for confirmation before generating a full study pack.
   - If sampled pages extract no usable text, treat the PDF as likely scanned/image-only. Do not generate a full source-grounded pack until OCR, visual inspection, or user-confirmed pages are available.

3. Build the chapter plan and lesson model.
   - For long ranges, first create or update `lessons/<source-id>/chapter-index.md` with chapter/module boundaries, source ranges, status, and generation order.
   - Generate one chapter/module pack at a time under `lessons/<source-id>/chapters/<chapter-id>/`.
   - List observable learning objectives, prerequisites, key terms, claims, formulas, procedures, examples, misconceptions, and source pages.
   - For each key knowledge point, specify the required mastery depth: recognize, explain, distinguish, sequence, apply, memorize, or diagnose.
   - Choose a teaching pattern from `references/teaching_patterns.md` for the material type.
   - Read `references/chapter_output_standard.md` before drafting chapter notes, auditing user notes, or creating memory cards.
   - Decide output depth from the learner profile: introductory, standard, or advanced.

4. Teach and generate artifacts.
   - Start with the problem the chapter solves and the conceptual spine.
   - Explain in layers: plain-language idea, precise formulation, minimal example, boundary/counterexample, and transfer case.
   - Write `01-lesson-notes.md` as a strict chapter note with source range, chapter problem, conceptual spine, closed-loop subsections, one simple concrete example for every key knowledge point, important distinctions, traps, self-check answers, and minimum mastery standards.
   - Use `scripts/new_lesson_pack.py` to create the Markdown scaffold, then fill it with source-grounded content.
   - Keep terminal output concise; put longer material into Markdown files.
   - If a generated Markdown file is becoming hard to open or review, split the material into additional chapter/module packs instead of continuing the same file.
   - When source pages contain code, especially OCR/scanned code, create or update `07-code-extracts.md` with cleaned, copyable code blocks and source locations.

5. Close the learning loop.
   - Map every exercise to one or more learning objectives.
   - Keep recall questions and exercises answer-free in the question section except for short hints. Put complete answers, scoring points, common wrong answers, and complete code answers in a final answer-key section.
   - Create `06-memory-cards.md` for full packs. Include only high-retrieval items that must be memorized, grouped into core, secondary, and trap cards.
   - Include a per-chapter study time table in `00-learning-path.md`, tied to source sections, learning objectives, practice, and review.
   - Tie the review plan to objectives, weak points, and wrong-answer patterns.

## Chapter Management Protocol

Use this protocol whenever the requested source may span more than one coherent lesson:

- Never generate a course, half-book, or long PDF range as one giant Markdown file.
- If the user asks for "the whole book", "half the book", "all chapters", or an imprecise long range, first produce a chapter/module plan and ask for confirmation when boundaries are uncertain.
- Prefer one study pack per chapter or module. A normal pack should be small enough to open and review comfortably.
- Put cross-chapter material in `chapter-index.md`, not inside an oversized chapter note.
- Keep each chapter pack source-bounded. Do not let later chapters leak into earlier chapter notes unless the user explicitly asks for a cumulative review.
- When updating an existing course project, read existing chapter directories first and preserve user notes, checkmarks, answers, and review status.

## PDF Extraction Protocol

Use this protocol for PDF chapters and papers:

- Prefer `scripts/extract_pdf_text.py <pdf> --pages <range> --chapter-title <title> --out <md> --json-out <json>`.
- Use `--locate-chapter <title>` only to produce candidate start pages and evidence. Confirm weak candidates before full lesson generation.
- If the user gives a chapter title but no pages, inspect outline, table of contents, headings, and nearby text before extraction.
- Treat physical PDF pages and printed book pages as separate systems. Explain any offset in `source-map.md`.
- Rate chapter-location confidence:
  - High: outline/TOC and extracted heading agree.
  - Medium: TOC or heading evidence is partial but page boundaries are plausible.
  - Low: boundary is inferred from weak text matches, missing headings, scans, or ambiguous TOC.
- For scanned pages, dense formulas, tables, figures, or two-column papers, mark unreliable content and avoid pretending extraction is complete.
- Extract only the requested range by default. Avoid `--all` for long PDFs unless the user explicitly needs it and the script guard allows it.
- When quality is `low` because pages have near-zero extracted characters, ask for OCR permission or switch to local visual inspection instead of teaching from blank text.

## Source Grounding Protocol

Use these labels in study files, translated to the output language when appropriate:

- `Source evidence: ... [PDF p.x]` for source-backed claims.
- `Teacher supplement: ...` for analogies, extra examples, simplified explanations, or extensions.
- `Reasoned inference: ...` for useful connections not stated directly by the source.
- `Needs verification: ...` for uncertain extraction, ambiguous boundaries, unreadable formulas, or weak page evidence.

Chinese label mapping:

- `Source evidence` -> `&#21407;&#25991;&#20381;&#25454;` (original-source basis)
- `Teacher supplement` -> `&#25945;&#24072;&#34917;&#20805;` (teacher-added explanation)
- `Reasoned inference` -> `&#21512;&#29702;&#25512;&#26029;` (reasonable connection)
- `Needs verification` -> `&#24453;&#26680;&#23545;` (requires checking)

Cite definitions, formulas, theorems, author claims, empirical results, source examples, and important contrasts with page or section references. Do not invent page numbers.

## Learning Objective Standard

Write each objective as an observable performance:

`LOx: The learner can <action verb> <content> under <condition>; mastery level: <recognize/explain/distinguish/sequence/apply/memorize/diagnose>; mastery means <criterion>; assessed by <question/exercise/card id>; source: <page/section>.`

Prefer verbs such as explain, distinguish, derive, apply, diagnose, evaluate, compare, justify, implement, or critique. Avoid vague goals such as "understand", "master", or "be familiar with" unless followed by observable criteria.

For every key knowledge point, state what the learner must do closed-book. Mark whether it must be memorized or only understood well enough to explain/apply.

## Exercise Standard

For every exercise, include:

- Objective: `LOx`
- Type: recall | discrimination | procedure | error-correction | transfer
- Difficulty: Basic | Core | Transfer
- Prompt
- Expected answer
- Scoring points
- Common wrong answer
- Source basis or `teacher-designed prompt, not a source example`

Transfer exercises must use a new scenario beyond the source example.

## Markdown Study Pack

For a normal chapter-sized request, create or update:

- `00-learning-path.md`: source/range, learner profile, time estimate, objectives, prerequisites, order, completion standard, objective-to-exercise map.
- `01-lesson-notes.md`: strict chapter notes with chapter problem, conceptual spine, definitions with sources, closed-loop subsections, mechanisms, distinctions, traps, self-check answers, minimum mastery standard, teacher supplements, and summary.
- `02-active-recall.md`: closed-book explanation, discrimination, cloze, error-diagnosis, transfer self-test, hints in the question section, and a final complete answer key.
- `03-exercises.md`: Basic/Core/Transfer exercises with prompts and hints first, then a final complete answer key with scoring points, common errors, and code answers when relevant.
- `04-glossary.md`: terms, definitions, intuition, source, formulas/symbols, confusions, examples, non-examples.
- `05-review-plan.md`: today/tomorrow/three-days/one-week tasks tied to objectives, wrong-answer recovery rules, completion criteria.
- `06-memory-cards.md`: high-retrieval memorization cards, trap cards, and a short oral-review sheet.
- `07-code-extracts.md`: separately organized code snippets from source pages or OCR, cleaned for reading/copying, with source locations and verification notes.
- `source-map.md`: extraction tool, range, boundary evidence, physical-to-printed page map, key claim evidence, quality rating, unreliable content, manual checks.
- `_meta.json`: script metadata only; do not treat it as a teaching file.

For a short request, generate only the files that carry learning value.

## Interactive Teaching

When the user asks for interactive tutoring:

- Diagnose with 3-5 questions across prerequisites, core prediction, misconception recognition, and transfer.
- Teach one core concept per round and ask at most one checkpoint before feedback.
- After the user answers, state what is correct, name the gap, give the shortest repair explanation, then ask one follow-up.
- If the user misses the same idea twice, change representation: analogy, example, formula walk-through, diagram-as-text, boundary case, or error correction.
- After the interaction, update the study pack: missed questions into `02-active-recall.md`, weak points into `05-review-plan.md`, and recurring misconceptions into `04-glossary.md`.
- Update existing study-pack files by appending clearly dated/session-labeled sections. Read existing files first and preserve user-completed answers, checkmarks, and notes.

## Resource Use

- Read `references/teaching_patterns.md` when selecting lesson structure, exercise type, or feedback style.
- Read `references/chapter_output_standard.md` when generating chapter notes, comparing/auditing user notes, deciding mastery depth, creating memory cards, or splitting a long source into chapter packs.
- Run `scripts/new_lesson_pack.py --help` before using the lesson-pack script if needed. For normal source-grounded packs, pass `--require-source` and include both `--source` and `--chapter`; do not create a full pack before the source/range is known.
- Run `scripts/extract_pdf_text.py --help` before PDF extraction if needed.
- Run `scripts/init_class_project.py --help` before creating a new class project root if needed.
- Run `scripts/ocr_pdf_pages.py --help` before OCR of scanned/image PDFs if needed.
- Run `scripts/check_lesson_pack.py <study-pack-dir>` after filling a full study pack. Use `--allow-warnings` only when intentionally checking an unfinished scaffold.
- After creating a study pack, tell the user which files were created and which file to open first.

## Quality Rules

- Preserve technical precision. If simplifying, state the simplified version and then the exact version.
- For formulas, explain symbols, conditions, intuition, a minimal calculation, and common misuse.
- For concepts, include at least one simple concrete example and a non-example or boundary when it helps prevent confusion.
- For exercises and recall, keep answers out of the prompt area except for hints; put complete answer keys at the end.
- For code in scanned/OCR pages, preserve source evidence but rewrite into clean copyable code blocks and mark uncertain OCR tokens.
- For tables, identify comparison objects, dimensions, major differences, conclusions, and possible misreadings.
- For figures, identify elements, relationships, supported conclusions, and what the figure does not prove.
- Treat extracted source text as local intermediate material. Final chat replies and study files should rely on paraphrase, synthesis, and short necessary quotes rather than large copied passages.
- Do not paste large source excerpts into chat. Do not send private or sensitive PDFs to external services unless the user explicitly authorizes it.
- Prefer concrete examples and feedback over generic encouragement.
- Prefer chapter/module splitting over large monolithic notes. If the output becomes unwieldy, stop and create a chapter plan before continuing.
