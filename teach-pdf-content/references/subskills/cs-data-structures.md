# CS And Data Structures Subskill

Use this module for computer science, C programming, data structures, algorithms, trees, graphs, pointers, storage layouts, formulas, or implementation-heavy chapters.

## Mandatory Teaching Dimensions

For each data structure, cover:

- logical structure
- storage representation
- C struct or array layout when relevant
- core operations
- invariants
- edge cases
- complexity when the source covers it
- common implementation mistakes

For each algorithm, cover:

- input and output
- preconditions
- core idea
- ordered steps
- trace table on a tiny example
- correctness intuition or invariant
- complexity when the source covers it
- implementation pitfalls

For each formula or property, cover:

- exact statement
- symbol meanings
- conditions
- proof intuition
- minimal calculation
- common misuse

## Mandatory Mini-Patterns For Common Topics

When the chapter contains the following topics, include the matching mini-pattern instead of relying on generic prose:

| Topic signal | Required note content |
| --- | --- |
| tree / binary tree / 二叉树 | empty tree or null case; five basic binary-tree forms if introduced; shape diagram; 1-based and 0-based index table when arrays appear |
| traversal / 遍历 | visit-order template; one 6-8 node trace; level-order note if traversal categories are discussed; recursive base case |
| non-recursive traversal / 非递归 | stack-state trace table; state what the stack stores, such as node pointers |
| threaded tree / 线索二叉树 | `LTag/RTag` meaning table; one pointer/tag rewrite example; warning that threaded pointers are not child pointers |
| tree/forest conversion / 树和森林转换 | before/after diagram; state that the correspondence depends on the left-child/right-sibling rule |
| union-find / MFSet / 并查集 | parent array trace; merge only after `Find`; index convention; amortized-efficiency note when optimization is discussed |
| Huffman / 哈夫曼 | merge table; WPL calculation; path length counted by edges; equal weights may produce non-unique trees/codes; prefix condition |
| backtracking / 回溯 | state-tree sketch; minimal pseudocode with choose/recurse/undo; explain shared-state undo vs copied state |
| Catalan / tree counting / 计数 | recurrence hand calculation for small n; clarify `b_n` vs `C_n`; clarify ordered-tree `n` to binary-tree `n-1` offset |

## Visual Requirements

- trees and graphs need ASCII diagrams or a clear textual diagram
- pointer structures need node-field sketches or tables
- array-based structures need index convention tables
- conversions need before/after diagrams
- recursive processes need call/return or state-tree sketches

## Beginner-First Delivery

When output mode is `beginner_lecture` or the learner level is unknown:

- start each hard topic with a tiny structure, tiny input, or 5-8 node example before general rules
- keep one representation visible while explaining the operation or traversal
- prefer a trace table plus a short explanation over a dense summary table
- delay complexity and memorization-only compression until after the learner can trace the mechanism
- for new concepts with complexity `C3` or `C4`, add an explicit `为什么成立` section

## vNext Note Mapping

In the vNext chapter model:

- conceptual teaching belongs in `detailed-notes.md`
- exercises and traces for self-check belong in `practice.md`
- oral retell and trap compression belong in `review-notes.md`

Do not scatter learner-facing concepts into many parallel files.

## C Implementation Bridge

When teaching C data structures, connect concepts to:

- `typedef struct` layout
- pointer meaning
- null or empty case
- array index convention
- allocation or ownership assumptions when the source covers them
- one minimal operation or traversal snippet
- one common off-by-one or null-pointer bug

If the pack uses separate code excerpts elsewhere, link from `detailed-notes.md` into those code locations. If code is embedded directly in `detailed-notes.md`, keep it short and conceptual.

## Common Data-Structure Traps

- confusing logical structure with storage representation
- using 1-based formulas in 0-based arrays
- forgetting null or empty cases in recursion
- treating threaded pointers as child pointers
- merging union-find nodes without finding roots first
- accepting a Huffman code without checking prefix property or WPL
- memorizing traversal names without tracing visit order

## Required Practice

For a normal data-structure chapter, include at least:

- one diagram-labeling or structure-identification task
- one trace task
- one formula or property calculation
- one implementation or pseudocode task
- one error-diagnosis task
- one transfer task with a new structure or input
