---
name: complement
description: |
  Closure inference and response-geometry disclosure — direction-agnostic,
  scope-aware detection of materially missing expressions around an active move.

  CENTROID:
  closure inference at the point of an active move

  IS:
  - post-landing closure check (detect non-local incompleteness after a move lands)
  - origin-shape detection (dual-ray structure at response formulation, before commit)
  - surface/defer/suppress decision routing via the structural-relevance gate

  IS NOT:
    collapse_zones:
      - follow-up helper (complement does not generate next-steps unprompted)
      - documentation helper (complement does not restructure existing content)
      - decorative expander (must willingly say "current focus is sufficient"
        more often than surface)
      - autonomous widener (origin-shape yields shaping choice to the user;
        never commits the geometry)
      - /counter (complement maps what's MISSING; counter argues what's WRONG —
        different verbs entirely)
    sibling_overlaps:
      - /counter (both fire at move boundaries; complement extends, counter attacks)
      - /tom (both pre-publication primitives; complement maps missing,
        tom re-expresses what's there)

  WHEN:
  - after a local closure event that may hide non-local incompleteness
  - at the point of formulating a response with apparent dual-ray structure
  - when an artifact lands and the caller suspects it is partial
  - when the sidecar router injects a `complement_due` lane directive into additionalContext

  NOT WHEN:
  - after every trivial step (gates are narrow by design)
  - when the move is within a bounded scope already (compile fix, single-file edit)
  - when current focus must be protected (Mode C suppression is the most
    important mode)
  - when the candidate complement is decorative (no change to implementation,
    governance, proof, boundary, or sequencing)
user-invocable: true
---

# /complement — Closure Inference

Two modes of the same primitive:

- **Post-landing** (`/complement`) — after something lands, detect whether
  closure is partial
- **Origin-shape** (`/complement --origin`) — before committing to a response,
  detect latent dual-ray structure and yield the shaping choice

Both are local coherence operations, not follow-up helpers or pattern mining.

The origin-shape mode is the stronger primitive. It prevents two failure modes
rather than cleaning up after them:
- assistant stays too narrow and misses the complement
- assistant widens too early and steals the shaping decision

The correct pattern is: **surface the shape before committing to the answer shape**.

## Definitions

These three terms must stay distinct. Conflating them degrades the skill into
adjacent thought generation.

- **Centroid**: the governing concern that organizes the active move
- **Ray**: the current directional expression of that concern (the work just done)
- **Complement**: an additional directional expression that would materially
  improve closure

"Complement" is direction-agnostic. It is not always an opposite. It may be:
inverse / adjacent missing expression / upstream prerequisite / downstream
proof obligation / governance counterpart / scope correction / time-horizon /
actor-lane / substrate.

## Origin-Shape Mode (`/complement --origin`)

Operates before the response commits to a geometry.

```
1. DETECT that the incoming issue has centroid-complement structure
2. INFER the centroid
3. IDENTIFY the active ray (what the user is asking about)
4. EXPOSE the complementary ray (what is latent but not yet named)
5. YIELD the shaping choice to the user
```

Output:

```
ORIGIN SHAPE
  centroid:           [the governing concern]
  active ray:         [what is being asked about]
  complementary ray:  [what is latent but unnamed]
  unnamed tension:    [if any]
  suggested geometry: single-ray / paired-rays / full-centroid
```

Then yield:

> This looks like a [shape]. Active ray: X. Likely complement: Y. Respond
> single-ray, shape both, or respond from centroid?

The user chooses:
1. **Single-ray** — answer the asked question only, hold the complement
2. **Shape both** — answer with both rays paired, showing the structure
3. **Respond from centroid** — answer from the governing concern outward

Option 3 is the real upgrade.

## Post-Landing Mode (`/complement`)

Six-step runtime:

```
1. DETECT the active target (explicit + implicit)
2. INFER the centroid (the governing concern organizing this move)
3. IDENTIFY the active ray (what aspect is currently in focus)
4. LOCATE the missing complement or unnamed tension
4.5 TEST structural relevance — is the complement structural or decorative?
5. DECIDE: surface (A), defer (B), or suppress (C)
```

### Step 4.5: Structural Relevance Test

A complement is structural if it changes at least one of:
- **Implementation path** — different code, different wiring
- **Governance posture** — different authority, different registration
- **Verification / proof burden** — different test, different validation gate
- **Boundary definition** — where the boundary actually is shifts
- **Sequencing of next action** — what must happen next changes

If the complement changes none of these five, it is decorative. Suppress it.

### Step 5: Decision Modes

**A. Surface** — structural and load-bearing. State what, at what scope, and why.

**B. Defer** — real but premature. Note for later without widening current focus.

**C. Suppress widening** — current ray is sufficient. Additional complement
would reduce closure density. Actively protect focus.

Mode C is the most important mode. Without it, the skill becomes a sophisticated
distraction engine. The skill must be willing to say "current focus is sufficient"
more often than it surfaces complements.

## Probe Template

```
TARGET:      What is being moved?
CENTROID:    What larger concern organizes that move?
PARTIALITY:  In what way is the current move incomplete?
COMPLEMENT:  What additional directional expression improves closure?
SCOPE:       At what rung or layer does that complement belong?
RISK:        Does surfacing improve closure, or dilute execution focus?
DECISION:    Surface, defer, or suppress.
```

## Output Discipline

Output must be concise. A finding, not an essay. If the skill produces more
than a short paragraph, it has over-widened.

- **Surface**: 2-4 sentences stating the complement, scope, and why it's structural.
- **Defer**: one-line note for later, no action now.
- **Suppress**: one-line confirmation that current focus is sufficient. Do not
  explain what was considered — that would defeat the purpose.

## Constraints

- Per-invocation judgment guided by the five-criteria gate. Do not over-heuristic.
- The skill has explicit permission not to be clever.
- Named is not landed. A complement that was surfaced but not built is still a
  valid complement.
