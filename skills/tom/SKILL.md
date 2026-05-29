---
name: tom
description: |
  Theory of Mind (centroid-preserving) re-expression engine. Trigger on /tom,
  "run tom", "tom this for X", "rewrite for X", "compress for X", "reframe as X",
  "translate the centroid", or any request to re-express context-window content
  for a different audience, style, scope, density, or purpose while preserving
  core meaning. Also triggers on meta and meta-meta ops: running /tom on a /tom
  artifact, theory-of-minding a TOM prompt.

  CENTROID:
  re-express content from one expression into another while preserving its
  centroid (invariant meaning), source-of-truth boundaries, and audience-critical
  distinctions

  IS:
  - centroid extractor (what does the source actually MEAN at its core?)
  - posture-shaped re-expression across nine axes (audience / style / scope /
    density / structure / fidelity / purpose / format / diagrams)
  - source-of-truth boundary preserver (warnings and unresolved risks are NOT
    softened to fit a friendlier register)
  - one-turn config primitive (propose-with-alternatives, then `go` is enough)

  IS NOT:
    collapse_zones:
      - summarizer (summaries lose structure; tom preserves structure while
        changing frame)
      - generic paraphrase (tom is centroid-locked, not synonym-swapped)
      - invented-capability author (anything claimed in output that wasn't in
        source is a failure, not a stylistic choice)
      - softened-warning author (risks reduced in force is failure, not posture)
      - audience-leakage author (internal-only details in external output is
        failure, not flexibility)
    sibling_overlaps:
      - /ingest (both transform; ingest transforms frame, tom transforms
        expression)
      - /complement (both pre-publication primitives; complement maps what's
        missing, tom re-expresses what's there)

  WHEN:
  - before publication or audience shift (board update, exec brief, doc handoff)
  - when source-content meaning must survive into a new audience or purpose
  - when sidecar router emits <sidecar key="tom_due" target="audience_shift" />
  - on explicit invocation

  NOT WHEN:
  - to summarize for the same audience (no re-expression target)
  - to invent capabilities not in source (centroid is invariant)
  - when current expression is already centroid-aligned to target audience
user-invocable: true
---

# /tom — Centroid-Preserving Re-Expression

You re-express content from one form to another while preserving its centroid
(invariant meaning). This is not summarization. It is not generic paraphrase.

## Core Promise

- **The centroid survives.** What the source means does not change.
- **The expression conforms.** Audience, style, scope, density, structure,
  fidelity, purpose, format match the configured posture.
- **Audience boundaries hold.** Warnings and unresolved risks are not softened
  to fit a friendlier register.
- **Invented capabilities are forbidden.** Adjacent work is not promoted into
  launch-scope work.

If the configured posture would normally force a centroid violation (e.g.,
`density: minimal` would normally drop a critical warning), keep the centroid
intact and trim elsewhere. The posture serves the centroid, not the other way
around.

## First-Response Protocol

The first response after `/tom` triggers is **not** an interrogation. It is a
**proposal with alternatives**, designed so the common case is one word back: `go`.

1. **Read the context window.** Identify the most likely object (what the user
   wants transformed). Look for the most recent substantial content block,
   document, prior exchange, named artifact, or referenced file.
2. **Detect meta-level.** Is the object itself a transformation prompt or skill?
   If yes, the operation is **meta** (transforming a transformation) or
   **meta-meta** (transforming /tom itself).
3. **Infer a posture.** Based on context cues — who's likely reading, what
   action follows, what audience signals exist — pick the posture that's most
   likely what the user wants.
4. **Pick 2 alternatives that span meaningful difference.** Avoid offering
   near-duplicates. Good axes: audience shift (internal ↔ external), purpose
   shift (decide ↔ learn ↔ execute), density shift (compact ↔ high).
5. **Produce the proposal.** Use this exact format:

```
**Object:** [one-line description of what's being transformed]
**Meta-level:** [base | meta | meta-meta]   ← only show if non-base
**Proposed posture:** [Posture Name]
*[2-line rationale citing the context cues that led here]*

​```yaml
audience: [value]
style: [value]
scope: [value]
density: [value]
structure: [value]
fidelity: [value]
purpose: [value]
format: [value]
diagrams: [value]
​```

**Alternatives if a different angle fits better:**
- **[Alt Posture 1]** — *when you'd want it*
- **[Alt Posture 2]** — *when you'd want it*

Say `go` to run, name an alternative, or override any axis.
```

6. **Stop.** Do not run the transformation yet. Wait for one-turn config response.

## After User Confirms

1. **Parse the source** into sections, clauses, and emphasis points.
2. **Extract the centroid.** For each major section: what is its invariant meaning?
3. **Re-express in the configured posture.** Audience / style / scope / density /
   structure / fidelity / purpose / format / diagrams.
4. **Hold the boundaries.** Source-of-truth, scope distinctions, warnings,
   concrete file paths preserved unless style explicitly authorizes summary.
5. **Render in configured format.** Markdown, HTML, JSON outline, slide outline.
6. **Append two short closing sections:**
   - `What this means in practice` — tailored to audience, 3–6 lines.
   - `Assumptions and preserved boundaries` — interpretation choices and what
     was held invariant.

## Meta-Level Handling

- **Base** — object is content. Centroid = what the content means.
- **Meta** — object is a prompt / framework / skill. Centroid = what the prompt
  DOES and HOW. Describe the mechanism in target audience's language; do NOT
  run the prompt.
- **Meta-meta** — object is /tom itself. Centroid = the theory-of-mind
  capability. Describe the SPACE of transformations, the INVARIANTS preserved,
  the FAILURE MODES guarded against. Stay one level above any concrete example.

## Failure Modes (these signal broken, not imperfect)

- **Invented capabilities** — anything claimed not in source.
- **Softened warnings** — risks reduced in force.
- **Promoted scope** — adjacent work described as launch-critical.
- **Audience leakage** — internal-only details in external output.
- **Centroid drift** — output reads well but no longer means what source meant.
- **Hallucinated specificity** — invented file paths / routes / function names.
- **Lost implications** — faithful recap of WHAT was said that loses WHAT TO DO NEXT.

If a configured axis would force one of these, **keep the centroid intact and
shorten elsewhere**.

---

Centroid preservation. Posture-shaped expression. The user is one word away
from the result.
