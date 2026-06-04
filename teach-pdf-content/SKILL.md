---
name: teach-pdf-content
description: Convert user-supplied learning sources, especially specified PDF chapters, textbook sections, papers, lecture notes, and course readings, into source-grounded teaching sessions and Markdown study packs with objectives, explanations, recall questions, exercises, answers, glossaries, and review plans. Use when the user provides or references concrete source material and asks to learn, study, be taught, review, explain, quiz, or create learning files from it. Do not use for generic subject Q&A or ordinary summaries when no source material or learning goal is specified.
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
- `lessons/`: generated study packs by chapter/module.
- `reviews/`: review plans, wrong-answer logs, and session follow-ups.

Initialize this structure with `scripts/init_class_project.py --project-root <dir> --course-title <title>`. Use `scripts/ocr_pdf_pages.py --project-root <dir>` for scanned/image PDFs so rendered images, OCR text, and OCR logs stay inside the class project.

## Workflow

1. Scope the learning task.
   - Identify the source file, requested chapter/section/page range, output mode, target depth, deadline, and language preference.
   - Identify the class project root before creating files. If unspecified, use the current directory.
   - Build a learner profile when possible: current level, goal, available time, exam/homework/project context, and whether bilingual terminology is needed.
   - Ask one concise clarifying question only when the source or requested range cannot be inferred safely.

2. Locate and extract the source.
   - For PDFs, prefer `scripts/extract_pdf_text.py` when available. Otherwise use `pdftotext`, `mutool`, or installed Python PDF libraries.
   - Treat `extract_pdf_text.py` primarily as a page extraction and quality-report tool. Use its chapter-location output only as candidate start-page evidence, not as final proof.
   - Distinguish `[PDF p.x]` physical PDF pages, `[Book p.y]` printed page numbers, and `[Section z]` source sections.
   - Record extraction tool, command or method, physical page range, printed page range if visible, chapter-boundary evidence, and extraction quality.
   - If chapter location confidence is low, show the evidence and ask for confirmation before generating a full study pack.
   - If sampled pages extract no usable text, treat the PDF as likely scanned/image-only. Do not generate a full source-grounded pack until OCR, visual inspection, or user-confirmed pages are available.

3. Build the lesson model.
   - List observable learning objectives, prerequisites, key terms, claims, formulas, procedures, examples, misconceptions, and source pages.
   - Choose a teaching pattern from `references/teaching_patterns.md` for the material type.
   - Decide output depth from the learner profile: introductory, standard, or advanced.

4. Teach and generate artifacts.
   - Start with the problem the chapter solves and the conceptual spine.
   - Explain in layers: plain-language idea, precise formulation, minimal example, boundary/counterexample, and transfer case.
   - Use `scripts/new_lesson_pack.py` to create the Markdown scaffold, then fill it with source-grounded content.
   - Keep terminal output concise; put longer material into Markdown files.

5. Close the learning loop.
   - Map every exercise to one or more learning objectives.
   - Include answer keys, scoring points, and common wrong answers for self-study.
   - Tie the review plan to objectives, weak points, and wrong-answer patterns.

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

`LOx: The learner can <action verb> <content> under <condition>; mastery means <criterion>; assessed by <question/exercise id>; source: <page/section>.`

Prefer verbs such as explain, distinguish, derive, apply, diagnose, evaluate, compare, justify, implement, or critique. Avoid vague goals such as "understand", "master", or "be familiar with" unless followed by observable criteria.

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
- `01-lesson-notes.md`: chapter problem, conceptual spine, definitions with sources, layered explanation, minimal example, boundaries, formulas/tables/figures, checkpoints, teacher supplements, summary.
- `02-active-recall.md`: closed-book explanation, discrimination, cloze, error-diagnosis, transfer self-test, answer criteria.
- `03-exercises.md`: Basic/Core/Transfer exercises with objectives, answers, scoring points, common errors, and follow-ups.
- `04-glossary.md`: terms, definitions, intuition, source, formulas/symbols, confusions, examples, non-examples.
- `05-review-plan.md`: today/tomorrow/three-days/one-week tasks tied to objectives, wrong-answer recovery rules, completion criteria.
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
- Run `scripts/new_lesson_pack.py --help` before using the lesson-pack script if needed. For normal source-grounded packs, pass `--require-source` and include both `--source` and `--chapter`; do not create a full pack before the source/range is known.
- Run `scripts/extract_pdf_text.py --help` before PDF extraction if needed.
- Run `scripts/init_class_project.py --help` before creating a new class project root if needed.
- Run `scripts/ocr_pdf_pages.py --help` before OCR of scanned/image PDFs if needed.
- Run `scripts/check_lesson_pack.py <study-pack-dir>` after filling a full study pack. Use `--allow-warnings` only when intentionally checking an unfinished scaffold.
- After creating a study pack, tell the user which files were created and which file to open first.

## Quality Rules

- Preserve technical precision. If simplifying, state the simplified version and then the exact version.
- For formulas, explain symbols, conditions, intuition, a minimal calculation, and common misuse.
- For tables, identify comparison objects, dimensions, major differences, conclusions, and possible misreadings.
- For figures, identify elements, relationships, supported conclusions, and what the figure does not prove.
- Treat extracted source text as local intermediate material. Final chat replies and study files should rely on paraphrase, synthesis, and short necessary quotes rather than large copied passages.
- Do not paste large source excerpts into chat. Do not send private or sensitive PDFs to external services unless the user explicitly authorizes it.
- Prefer concrete examples and feedback over generic encouragement.
