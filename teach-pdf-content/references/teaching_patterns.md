# Teaching Patterns

Use this reference when choosing lesson structure, exercise type, or feedback style for supplied reading material.

## Pattern Selection Matrix

| Material type | Use this structure | Exercise emphasis |
| --- | --- | --- |
| Conceptual textbook chapter | Problem -> core idea -> mechanism -> boundary -> transfer | explanation, discrimination, transfer |
| Mathematical or formal material | definition -> assumptions -> theorem/rule -> proof intuition -> worked example -> counterexample | derivation, procedure, error correction |
| Research paper | question -> claim -> method -> evidence -> limitation -> replication/application | claim-evidence mapping, critique, transfer |
| Programming/API documentation | input -> steps -> output -> failure modes -> diagnostics -> practice task | procedure, debugging, scenario practice |
| Computer science / data structures | problem -> logical structure -> storage representation -> operations -> trace -> implementation pitfall | diagram labeling, procedure trace, code reading, error correction |
| Statistics/ML material | data/problem setup -> model/estimator -> assumptions -> objective -> evaluation -> failure cases | formula interpretation, boundary cases, experiment critique |
| Humanities text | central question -> argument structure -> key concepts -> position comparison -> interpretive tension | close reading, comparison, argument reconstruction |
| Case study | facts -> decision point -> constraints -> alternatives -> tradeoffs -> outcome | diagnosis, decision justification, transfer case |
| Law/medicine/economics textbook | rule/mechanism -> conditions -> exceptions -> applied case -> risk of misuse | classification, exception handling, applied reasoning |
| Figure/table-heavy report | visual elements -> comparison dimensions -> trend/relationship -> supported conclusion -> limits | graph reading, misread prevention, evidence checks |

## Complex Material Rules

For math:

- Extract definitions, assumptions, conclusion, proof idea, example, and counterexample.
- Explain every symbol before using the formula.
- Include at least one minimal calculation and one common misuse.

For papers:

- Separate author claim, method, evidence, and your critique.
- Mark empirical results with source pages or sections.
- Ask transfer questions that change dataset, population, assumption, or evaluation criterion.

For tools and APIs:

- Teach inputs, outputs, defaults, failure modes, and diagnostics.
- Include one "wrong usage" exercise and one realistic task.
- Prefer runnable examples when the workspace supports them.

For computer science and data structures:

- Separate logical structure from storage representation.
- Include a diagram or ASCII sketch for trees, graphs, linked structures, and state spaces.
- Include one trace table for algorithms, conversions, recursion, or formulas.
- Connect concepts to C structs, array indices, pointers, null/empty cases, and implementation pitfalls when relevant.
- Use at least one error-diagnosis exercise for common bugs such as off-by-one, missing base case, or confusing pointer meaning.

For humanities:

- Reconstruct the author's argument before evaluating it.
- Track key terms, contrasts, and implied assumptions.
- Use comparison prompts rather than only recall prompts.

For formulas, tables, and figures:

- Formula: original form, symbol meanings, conditions, intuition, minimal calculation, common misuse.
- Table: comparison objects, dimensions, major differences, reading conclusion, possible misread.
- Figure: elements, relationships, supported conclusion, what it does not prove.

## Lesson Quality Checks

A strong lesson should answer:

- What should the learner be able to do after the chapter?
- What prerequisite idea would make the chapter easier?
- Which distinction is easiest to confuse?
- What is the minimal example and the non-example?
- Which question proves transfer rather than copying?
- Which claims are source-backed, teacher supplements, or reasonable inferences?

## Exercise Design

Use a mix of:

- Recall: define, list, identify, restate without notes.
- Discrimination: compare similar concepts or decide which case applies.
- Procedure: calculate, derive, annotate, implement, or run a workflow.
- Error correction: diagnose a flawed explanation or solution.
- Transfer: apply the idea to a new context not directly in the source.

Difficulty labels:

- Basic: vocabulary and direct comprehension.
- Core: main mechanism, argument, or procedure.
- Transfer: new scenario, boundary condition, or critique.

Every exercise should include objective ID, type, difficulty, expected answer, scoring points, common wrong answer, and source basis or teacher-designed note.

## Feedback Style

When responding to a learner's answer:

1. State what is correct.
2. Name the missing or mistaken part.
3. Give the shortest corrected explanation that fixes the gap.
4. Ask one follow-up that tests the repaired idea.

Avoid vague praise. Use feedback tied to the concept and objective.

## Mini Conversion Example

Source idea: a model can perform well on training data but fail on new data because it learned noise rather than the underlying pattern.

Concept explanation:

- 原文依据：The source claim is about the gap between training performance and generalization. Cite the page or section.
- 教师补充：Think of the model as memorizing the practice set instead of learning the rule.

Active recall:

- Q: Explain overfitting without using the word "memorize"; include one symptom and one prevention strategy.
- Self-check: mentions training/new-data gap, learned noise, and a mitigation such as validation or regularization.

Transfer:

- Q: A classifier scores 99% on old examples and 62% on next month's data. Give two plausible causes and one diagnostic check.
- Note: Teacher-designed transfer task, not a source example.

Error feedback:

- If the learner says "the model is too simple", repair the distinction between overfitting and underfitting, then ask for one sign of each.

## Markdown Style

For generated study files:

- Put the main takeaway near the top.
- Use headings that match the learning path when the source hierarchy is hard to learn from.
- Keep paragraphs short and scannable.
- Use tables only when comparison or mapping is the point.
- Include source page or section references for definitions, claims, formulas, examples, and empirical results.
- Mark teacher-added analogies or extensions with `教师补充`.
