# Lesson Note Builder Subskill

Use this module before drafting or revising `detailed-notes.md`.

## Purpose

`detailed-notes.md` is the chapter's main teaching file.

Its job is not to compress the source. Its job is to teach the chapter so the learner can understand the mechanism without constantly returning to the textbook.

## Output Mode Default

Choose an output mode before drafting. If the user does not specify one, use `beginner_lecture`.

- `beginner_lecture`: default. Teach the chapter in first-pass order and delay review compression until after the main explanation.
- `standard_study_pack`: balanced teaching plus practice plus review support.
- `review_cram`: condensed review-only mode for explicit cram requests.

## Drafting Rule

Do not draft prose directly from textbook headings.

Before writing:

1. extract subsection knowledge points
2. mark which concepts are new in this subsection
3. assign `C1-C4` complexity to new concepts
4. assign a teaching contract for each page:
   - `page_kind`
   - `teaching_profile`
   - `clarity_risk`
   - `must_answer`
   - `exit_outcomes`
   - `failure_signals`
5. decide teaching depth from the teaching contract, not from complexity alone
6. confirm how each subsection maps into `knowledge-map.json`
7. for high-importance `C3/C4` points, sketch what a `10-15 minute micro-lesson` on this point would look like

The note should follow the chapter's knowledge structure, not only the textbook's printing structure.

Default vNext authoring is page-first:

1. build `knowledge-map.json`
2. draft `knowledge-pages.json`
3. let each important page stand as an independent micro-lesson
4. compile `detailed-notes.md` from those pages

Do not treat `knowledge-pages.json` as page data extracted from a finished long note unless you are explicitly migrating old content.

## Required Opening

Every full `detailed-notes.md` should open with:

1. title and source range
2. source-map link and extraction-quality note
3. output mode and why it was chosen when not obvious
4. how to use this note
5. prerequisite reminder
6. chapter problem
7. chapter knowledge map summary
8. suggested first-pass / review-pass route
9. starter example or toy case
10. conceptual spine

## Knowledge-Point Table Rule

Each core subsection should include a small knowledge-point table or equivalent structured list that makes these fields visible:

- knowledge-point ID
- title
- is new concept or not
- complexity level `C1-C4`
- importance
- mastery target

This is required because the note is both:

- a human teaching document
- a semantic source for frontend rendering and node jumps

## Closed-Loop Subsections

Each core subsection should normally answer:

- What question does this subsection answer?
- What are the main knowledge points here?
- What is the smallest useful example?
- What is the formal conclusion or definition?
- Why does the conclusion hold?
- What is the mechanism, lifecycle, proof idea, or procedure?
- What boundary, counterexample, or common confusion prevents misuse?
- What similar concept must be distinguished?
- What implementation or problem-type anchor should the learner connect it to?
- What closed-book retell template should the learner be able to produce?

Do not put complete self-check answers immediately after the question. Use a final answer area or a collapsible answer block.

Keep the closed loop fixed, but do not force every knowledge point to use the exact same internal explanation order. Choose the order that best teaches the point:

- concept explanations may start from use case then definition
- structure explanations may start from storage goal then fields
- algorithm explanations may start from trace then invariant
- principle explanations may start from the learner's doubt then the argument

## Complexity-Driven Teaching Depth

Teach different concepts with different depth.

Important:

- complexity is not permission to under-explain
- `C1/C2` does not mean "just fill the minimum blocks"
- if a page has high confusion risk, heavy dependency load, or transfer burden, increase the teaching profile even when the complexity label is not high

### `C1`

Needs:

- one-sentence problem
- one-sentence conclusion
- one minimum example
- one boundary reminder

### `C2`

Needs:

- question
- conclusion
- minimum example
- why this definition exists
- easy confusion
- closed-book wording

If the learner could still reasonably ask "why is this designed this way?" or "how do I tell it apart from the nearby concept?", do not keep this page at a lazy minimum. Upgrade the page's teaching profile.

### `C3`

Needs:

- starter example
- observation
- formal result
- why it holds
- trace
- boundary or trap
- nearby-concept comparison
- implementation or question-type connection
- closed-book output template
- usually enough substance to stand as a page-sized micro-lesson

### `C4`

Needs:

- introduction problem
- minimum counterexample or starter example
- layered explanation
- full trace
- why it holds
- why simpler alternatives fail
- multiple nearby-concept comparisons
- code/formula/diagram bridge
- closed-book output template
- compressed review form
- should normally be treated as a standalone page-sized micro-lesson

## Example Type Rules

Choose the example format by material type:

- definition: positive example plus non-example
- structure: ASCII diagram plus labeled parts
- formula: symbol meanings plus minimal calculation plus misuse
- algorithm or process: ordered steps plus trace table
- code concept: minimal snippet plus one implementation pitfall
- conversion rule: before/after diagram
- abstract theory: toy case before general statement

For `beginner_lecture`, place the first worked example before large summary tables whenever possible.

## Mandatory Why/Trace Rule

If the subsection belongs to trees, graphs, traversal, recursion, state transitions, formulas, or implementation-heavy mechanisms, it must contain:

- one minimum example
- one why-it-holds explanation
- one trace or ordered development
- one confusion boundary

If one of these is missing, the subsection is unfinished.

## Micro-Lesson Rule

For high-importance `C3/C4` knowledge points, ask before drafting:

- if I had only 10 to 15 minutes to teach this one point, where would I start?
- what is the minimum example that makes the mechanism visible?
- what specific learner doubt must be resolved?
- what must the learner be able to say closed-book after this page?

Do not let such points collapse into one paragraph under a larger subsection if they deserve independent teaching weight.

## Anti-Laziness Rule

Do not treat the subsection template as the task.

The real task is:

1. answer the page's `must_answer` questions
2. produce the page's `exit_outcomes`
3. remove the listed `failure_signals`

If a page has the correct block names but still fails these three checks, the page is unfinished.

## Beginner Readability Rules

- Introduce prerequisites before using dependent terms.
- In `beginner_lecture`, do not open with a review checklist, a large concept table, or mastery standards before the learner sees the first concrete example.
- Mark what must be memorized, what must be understood, and what must be practiced.
- Do not let a large table replace explanation.
- Use short paragraphs and local examples before broad summaries.
- Include a `10-minute review route` for dense chapters.
- Add stable section names such as:
  - `本节主问题`
  - `本节知识点`
  - `先看一个最小例子`
  - `正式结论 / 定义`
  - `为什么成立`
  - `过程追踪 / Trace`
  - `边界、反例与易错点`
  - `和相邻概念的区别`
  - `代码 / 实现 / 题型连接`
  - `本节闭卷输出模板`

These stable names exist for both learners and frontend rendering.

## Required Closing Sections

For full notes, close with:

- `关键术语与公式速查`
- `实现与代码连接`
- `易混概念总对比`
- `闭卷输出模板`
- `10 分钟速读路线`

If the chapter is implementation-heavy, explicitly point to code locations or code IDs.

## Output Check

Before considering the note complete, verify that a learner can:

1. explain the chapter problem
2. trace the core structures or processes
3. explain why the hard conclusions hold
4. distinguish the main confusions
5. find the matching practice and review locations
6. retell the chapter's core points without immediately reopening the source
