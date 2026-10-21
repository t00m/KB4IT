---
DocType: Reference
Feature: Writing
HelpId: gallery
Keyword: mermaid, diagram, flowchart, sequence, formula, math, katex, latex, tex, equation, matrix
Level: basic
Order: 235
Related: howto-write-documents.md, reference-document-format.md
Section: Reference
Summary: Examples of diagrams and formulas, each with the Markdown you write and the result readers see.
---

# Diagram and formula gallery

Each example shows the Markdown you write, then the result as readers see it. Copy the source into a document and change it. The rules are in [Document format](reference-document-format.md#formulas); how to start is in [Write a document](howto-write-documents.md#diagrams).

Diagrams are drawn by [Mermaid](https://mermaid.js.org/) and formulas by [KaTeX](https://katex.org/), in the browser. Both ship with KB4IT, so the pages work offline and when opened from disk.

## Flowchart {#flowchart}

````markdown
```mermaid
flowchart LR
    A[Markdown files] --> B(kb4it build)
    B --> C{Changed?}
    C -- yes --> D[Compile the page]
    C -- no --> E[Reuse the cached page]
    D --> F[Website]
    E --> F
```
````

```mermaid
flowchart LR
    A[Markdown files] --> B(kb4it build)
    B --> C{Changed?}
    C -- yes --> D[Compile the page]
    C -- no --> E[Reuse the cached page]
    D --> F[Website]
    E --> F
```

## Sequence diagram {#sequence}

````markdown
```mermaid
sequenceDiagram
    participant You
    participant Serve as kb4it serve
    participant Browser
    You->>Serve: Save a document
    Serve->>Serve: Rebuild the changed pages
    Serve-->>Browser: Reload
    Browser->>Serve: Ask for the page
    Serve-->>Browser: New page
```
````

```mermaid
sequenceDiagram
    participant You
    participant Serve as kb4it serve
    participant Browser
    You->>Serve: Save a document
    Serve->>Serve: Rebuild the changed pages
    Serve-->>Browser: Reload
    Browser->>Serve: Ask for the page
    Serve-->>Browser: New page
```

## State diagram {#state}

````markdown
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review
    Review --> Draft: changes asked
    Review --> Published
    Published --> [*]
```
````

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review
    Review --> Draft: changes asked
    Review --> Published
    Published --> [*]
```

## Pie chart {#pie}

````markdown
```mermaid
pie title Documents by category
    "Procedure" : 42
    "Incident" : 17
    "Note" : 29
```
````

```mermaid
pie title Documents by category
    "Procedure" : 42
    "Incident" : 17
    "Note" : 29
```

## Inline formula {#inline}

````markdown
A circle of radius $r$ has the area $A = \pi r^2$, and $e^{i\pi} + 1 = 0$.
````

A circle of radius $r$ has the area $A = \pi r^2$, and $e^{i\pi} + 1 = 0$.

## Display formula {#display}

````markdown
$$
\int_0^1 x^2\,dx = \frac{1}{3}
$$
````

$$
\int_0^1 x^2\,dx = \frac{1}{3}
$$

## Sums and limits {#sums}

````markdown
$$
\sum_{k=1}^{n} k = \frac{n(n+1)}{2} \qquad \lim_{x \to 0} \frac{\sin x}{x} = 1
$$
````

$$
\sum_{k=1}^{n} k = \frac{n(n+1)}{2} \qquad \lim_{x \to 0} \frac{\sin x}{x} = 1
$$

## Matrix {#matrix}

````markdown
$$
A = \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}, \quad \det A = -2
$$
````

$$
A = \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}, \quad \det A = -2
$$

## Aligned equations {#aligned}

````markdown
$$
\begin{aligned}
(a + b)^2 &= a^2 + 2ab + b^2 \\
(a - b)^2 &= a^2 - 2ab + b^2
\end{aligned}
$$
````

$$
\begin{aligned}
(a + b)^2 &= a^2 + 2ab + b^2 \\
(a - b)^2 &= a^2 - 2ab + b^2
\end{aligned}
$$

## Cases {#cases}

````markdown
$$
|x| = \begin{cases} x & \text{if } x \ge 0 \\ -x & \text{if } x < 0 \end{cases}
$$
````

$$
|x| = \begin{cases} x & \text{if } x \ge 0 \\ -x & \text{if } x < 0 \end{cases}
$$

## Formula in a list {#list}

````markdown
- Disk use, in per cent: $\frac{used}{size} \times 100$
- Free space: $size - used$
````

- Disk use, in per cent: $\frac{used}{size} \times 100$
- Free space: $size - used$

## A dollar sign as text {#dollar}

````markdown
The licence costs \$5 per seat, or `$5` in code.
````

The licence costs \$5 per seat, or `$5` in code.
