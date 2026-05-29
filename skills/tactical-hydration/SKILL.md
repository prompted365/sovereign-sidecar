---
name: tactical-hydration
description: |
  Runtime tactical context hydration — staged discovery and bounded
  source-bearing hydration. Answers "how does the agent know where to look
  before it already knows where to look?" via filesystem shape, structural
  signals, and typed candidate baskets.

  CENTROID:
  intent → bounded, source-reenterable evidence packet via staged source-bearing
  discovery

  IS:
  - structured intake of agent intent (goal, seeds, profile, fanout, mutation risk)
  - zone orientation (cwd / repo root / obvious truth files)
  - low-cost shape scout (directory map, headings, durable handles, refs)
  - typed candidate basket with origin / use taxonomy
  - tactical probe plan (multiple bounded probes, not one giant regex)
  - bounded chunk hydration with line-range provenance and next-re-entry commands
  - agent-ready evidence packet (selected_surfaces, unresolved_questions, caution_map)

  IS NOT:
    collapse_zones:
      - vector database (no embedding-space retrieval)
      - semantic oracle (does not "understand" content; surfaces structural signals)
      - doctrine engine (produces evidence; downstream consumers judge truth)
      - "read everything" (bounded reads only; refuses unbounded scans)
      - /consolidate rewrite (RTCH selects; /consolidate packages)
    sibling_overlaps:
      - /consolidate (RTCH selects surfaces; /consolidate packages them —
        distinct boundaries)
      - /ingest (both discover; RTCH discovers internal, ingest metabolizes
        external)

  WHEN:
  - at sidecar chamber-fill (session start, posture shift)
  - when an agent needs to know what surfaces exist before reading them
  - when the next move requires source-bearing evidence under bounded read budget
  - on explicit invocation

  NOT WHEN:
  - when target surface is already known (just read it)
  - for external context (use /ingest)
  - when the answer needs zero filesystem reads (conversation-only is enough)
user-invocable: true
---

# /tactical-hydration — RTCH

Runtime tactical context hydration. The staged discovery primitive: from intent
to bounded source-bearing evidence packet, in stages, with provenance.

The acronym RTCH (runtime-tactical-context-hydration) is the working shorthand.

## What This Solves

Cold-start: an agent has intent but no map. Without RTCH, the agent either
reads everything (context overflow) or guesses which file matters (premature
scope commitment). RTCH stages the discovery so each read sharpens the next.

## Stage Pipeline

```
1. INTAKE      — structured intent (goal, seeds, profile, fanout, mutation risk)
2. ORIENT      — zone discovery (cwd, repo root, obvious truth files)
3. SCOUT       — low-cost shape (directory map, headings, durable handles)
4. CANDIDATE   — typed basket (origin / use taxonomy + pairing rules)
5. PROBE PLAN  — multiple bounded probes, not one giant regex
6. HYDRATE     — bounded chunk reads with line-range provenance
7. PACKET      — emit evidence packet (selected_surfaces, unresolved, cautions)
```

## Intake Schema

```yaml
intent:
  goal: "<one-line description of what the agent needs to do>"
  seeds: ["<file path>", "<keyword>", "<concept>"]
  profile: "narrow | mixed | broad"
  fanout: "conservative | moderate | aggressive"
  mutation_risk: "read_only | local_mutation | cross_repo_mutation"
```

- `profile` shapes what counts as a candidate (narrow = same file family;
  mixed = adjacent files; broad = cross-domain).
- `fanout` shapes how many candidates to surface (conservative = top 3;
  moderate = top 7; aggressive = top 15).
- `mutation_risk` shapes the caution map (read_only = empty cautions;
  cross_repo_mutation = explicit warnings).

## Probe Plan Discipline

Each probe is bounded:
- **Type**: grep / glob / rg-window / read-lines / json-key / yaml-key
- **Scope**: explicit paths or glob patterns
- **Read budget**: max lines or max files per probe
- **Termination**: probe ends when budget exhausted OR target found

Probes are NOT free-form. The plan declares each probe upfront so the agent
can audit the read budget before committing.

## Output Packet Shape

```yaml
selected_surfaces:
  - path: "<file path>"
    role: "<why this surface was selected>"
    line_range: "<L1-L2 or null for full-file>"
    re_entry_command: "<one-line command to re-read this surface>"

unresolved_questions:
  - "<question the agent could not answer from available surfaces>"

caution_map:
  - surface: "<path>"
    caution: "<mutation risk, schema instability, etc.>"

read_budget_consumed: <integer lines>
read_budget_remaining: <integer lines>
```

## Constraints

- **Bounded reads only.** No unbounded grep across entire trees.
- **Provenance required.** Every selected surface declares line range + re-entry command.
- **Profile shapes scope.** A narrow profile must not return broad-scope candidates.
- **Cautions are first-class.** Mutation risk warnings are emitted in the packet,
  not as a separate channel.

## Sidecar Integration

When the sidecar router fills the chamber, it invokes `/tactical-hydration` with
`target_profile: mixed`, `fanout_level: conservative` against the working dir.
The selected surfaces become chamber arrow pointers. /consolidate packages
their headings for the chamber's tom_briefing field.
