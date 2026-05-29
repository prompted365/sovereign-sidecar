---
name: consolidate
description: |
  Context consolidation — concatenate any file surface into a single
  LLM-consumable indexed markdown dump. Works with local dirs, glob patterns,
  git repos (ours or public), and conversational intent targets.

  CENTROID:
  file-surface to single-indexed-markdown-dump consolidation

  IS:
  - local directory / glob consolidation
  - git repo (ours or public) clone + consolidation
  - conversational intent resolution (grep / glob to files)
  - git diff range consolidation
  - harpoon target prep with anchor-assessment preamble

  IS NOT:
    collapse_zones:
      - file authoring (consolidate reads and concatenates; never writes to source)
      - doctrine judgment (consolidate packages for other agents; never judges
        content)
      - opinionated content filter (skip-binary and exclude-pattern are rules,
        not curation)
      - lossy compressor (truncation at limits is a transparency boundary, not
        a curation choice)
      - /tactical-hydration rewrite (RTCH selects; consolidate packages —
        distinct boundaries)
    sibling_overlaps:
      - /tactical-hydration (RTCH selects surfaces; consolidate packages them)
      - /ingest (both produce shaped artifacts; ingest metabolizes external,
        consolidate packages internal)

  WHEN:
  - when an agent needs a consolidated context surface for downstream work
  - when an arena spec needs a single dump of N files as anchor context
  - when a harpoon assessment needs an anchor-assessment preamble
  - on explicit invocation

  NOT WHEN:
  - when single-file read is enough (just read it)
  - when the consumer is a human (consolidate output is dense; humans want
    structure)
  - when source files are unbounded (set explicit limit or use /tactical-hydration
    first)
user-invocable: true
---

# /consolidate — File Surface to Indexed Dump

Concatenate file surfaces into a single indexed markdown dump that downstream
agents consume as anchor context.

## Input Patterns

- **Local directory**: `consolidate ./path/to/dir`
- **Glob**: `consolidate ./src/**/*.ts`
- **Git repo**: `consolidate https://github.com/org/repo`
- **Conversational intent**: `consolidate the recent commits about auth`
  (resolves to grep/glob plan first, then consolidate)
- **Git diff range**: `consolidate diff HEAD~5..HEAD`

## Output Structure

```markdown
# Consolidated: <source-description>

**Sources**: <N files>
**Total bytes**: <bytes>
**Generated**: <timestamp>

## Index

1. [path/to/file1.ts](#file-1-path-to-file1-ts) — <one-line summary>
2. [path/to/file2.md](#file-2-path-to-file2-md) — <one-line summary>
...

---

## File 1: path/to/file1.ts

```typescript
<full file content>
```

---

## File 2: path/to/file2.md

<full file content>

---

...
```

## Rules (Not Curation)

- **skip-binary**: binary files are excluded from the dump (PDFs, images, etc.).
  This is a rule, not a curation choice.
- **exclude-pattern**: `.git/`, `node_modules/`, `dist/`, `build/`, `.next/` are
  excluded by default. Override with `--include-pattern`.
- **truncation**: per-file at 500KB; total dump at 5MB. Truncation is
  transparent (the dump explicitly says "[FILE TRUNCATED AT 500KB]"), not silent.

## Conversational Intent Resolution

When invoked with intent rather than paths (e.g., `consolidate the auth code`),
the skill runs a probe plan first:

1. **Grep** for keyword across the working dir
2. **Glob** for likely file patterns
3. **Surface** the candidate paths to the user for confirmation
4. **Consolidate** the confirmed set

Intent-driven invocations never silently consolidate unconfirmed file sets.

## Sidecar Integration

When the sidecar router fills the chamber, `/consolidate` runs AFTER
`/tactical-hydration` selects surfaces:

```
/tactical-hydration --target mixed --fanout conservative
  → outputs: selected_surfaces[]
/consolidate <selected_surfaces[].path>
  → outputs: single indexed dump (headings only for chamber briefing)
/tom --centroid "what should this arrow fire on?" --object <dump>
  → outputs: tom_briefing per arrow
```

The three skills compose at chamber-fill time: hydrate selects, consolidate
packages, tom briefs.

## Constraints

- **Read-only.** Consolidate never writes to source files.
- **Provenance preserved.** Every consolidated file carries its path as a
  section header.
- **Truncation transparent.** Hidden truncation is failure; declared truncation
  is design.
- **No opinion on content.** Consolidate doesn't filter for quality or relevance;
  that's the consumer's job.
