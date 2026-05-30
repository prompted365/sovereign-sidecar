---
name: ingest
description: |
  Metabolize external context into the working frame without cargo-culting.
  Fire when external content enters the session — URLs, pasted docs, API
  references, competitor analysis, framework docs, tutorial code.

  CENTROID:
  metabolize external context — consume primitives, retain sovereignty

  IS:
  - the gate between external knowledge and internal working frame
  - the anti-cargo-cult primitive (absorb patterns, reject wholesale adoption)
  - the sovereignty boundary (what enters must be shaped, not copied)

  IS NOT:
    collapse_zones:
      - /consolidate (consolidate packages known surfaces; ingest metabolizes unknown ones)
      - /tactical-hydration (RTCH discovers internal surfaces; ingest metabolizes external ones)
      - copy-paste with commentary (ingest transforms, not annotates)
      - summarizer (summaries lose structure; ingest preserves structure while changing frame)
    sibling_overlaps:
      - /tom (both transform; ingest transforms frame, tom transforms expression)
      - /tactical-hydration (both discover; RTCH discovers internal, ingest metabolizes external)

  WHEN:
  - when external docs, APIs, frameworks, or competitor patterns enter the session
  - when the user pastes code from an external source
  - when a URL is shared for context
  - when the sidecar router injects an `ingest_needed` lane directive into additionalContext

  NOT WHEN:
  - for internal project context (use /tactical-hydration)
  - for re-expressing existing content (use /tom)
  - for packaging known files (use /consolidate)
user-invocable: true
---

# /ingest — Metabolize External Context

You are the sovereignty boundary. External context enters through you or it enters raw.

## What Metabolize Means

Metabolize is not summarize. Metabolize is not copy. Metabolize is:

1. **Identify the pattern** — what structural primitive does this external content carry?
2. **Name it in our vocabulary** — does this pattern already have a name in our frame? If yes, map it. If no, name it.
3. **Assess adoption stance** — ADOPT (clean win, sovereignty intact), WRAP (useful but we own the surrounding semantics), WATCH (no pressure yet), NO-OP (already covered or hostile).
4. **Emit the shaped context** — the metabolized output carries the external pattern in our frame, with adoption stance declared.

## Output Shape

```yaml
ingested:
  source: "<url or description>"
  pattern_identified: "<what structural primitive this carries>"
  our_vocabulary_mapping: "<existing term or new term>"
  adoption_stance: "ADOPT | WRAP | WATCH | NO-OP"
  shaped_context: |
    <the external content re-expressed in our frame>
  sovereignty_note: |
    <what we keep, what we strip, why>
```

## Anti-Cargo-Cult Discipline

The test: can you explain the metabolized pattern WITHOUT using the external source's vocabulary? If you must use their terms to explain what you absorbed, you cargo-culted. If you can explain it in federation vocabulary (or cleanly named new terms), you metabolized.
