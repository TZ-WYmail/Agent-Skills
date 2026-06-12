# Source Intake Subskill

Use this module when locating source ranges, extracting PDFs, handling OCR, or creating `source-map.md`.

## Scope

1. Identify source file, requested chapter/section/page range, output mode, language, learner profile, and project root.
2. Decide whether the request is one coherent chapter/module or a long multi-chapter job.
3. Ask one concise clarifying question only when chapter boundaries or source identity cannot be inferred safely.

## Chapter Management

- For a long source, create or update `lessons/<source-id>/chapter-index.md` before generating full packs.
- Generate one chapter or module pack at a time.
- Keep each pack source-bounded. Do not leak later chapters into earlier notes unless the user asks for cumulative review.
- Preserve existing user notes, answers, checkmarks, and review status when updating an existing pack.
- Prefer the vNext chapter structure and `scripts/new_lesson_pack_vnext.py` unless legacy compatibility is explicitly required.

## PDF Extraction

- Prefer `scripts/extract_pdf_text.py <pdf> --pages <range> --chapter-title <title> --out <md> --json-out <json>`.
- Use `--locate-chapter <title>` only for candidate evidence, not final proof.
- Inspect outline, table of contents, headings, and nearby text before trusting inferred boundaries.
- Distinguish physical PDF pages, printed book pages, and source sections.
- Rate chapter-location confidence:
  - High: outline/TOC and extracted heading agree.
  - Medium: TOC or heading evidence is partial but page boundaries are plausible.
  - Low: weak text matches, missing headings, scans, or ambiguous TOC.

## OCR And Weak Extraction

- If sampled pages extract no usable text, treat the PDF as scanned or image-only.
- Do not generate a full source-grounded pack from blank or low-quality extraction.
- For scanned pages, dense formulas, tables, figures, or code, mark unreliable content as `待核对`.
- Keep OCR rendered pages, text, logs, and model files under the class project root.

## Source Map Requirements

`source-map.md` must record:

- source file and requested range
- extraction tool and command or method
- physical PDF page range and printed page range if visible
- chapter-boundary evidence and confidence
- key claim evidence
- formula, table, figure, and code limitations
- OCR or manual inspection notes
- unreliable content and manual checks

## vNext Intake Rule

For vNext packs, source intake should prepare for:

- knowledge-point extraction
- concept complexity grading
- `knowledge-map.json` generation

That means intake should preserve enough boundary and evidence information for downstream mapping, not only enough to quote source pages.

## Completion Rule

Do not proceed to full teaching artifacts until source range and extraction quality are good enough to support source-grounded claims.
