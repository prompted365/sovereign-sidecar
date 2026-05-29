---
name: posture
description: |
  Working-mode declaration and runtime contract — declare ENG/OPS × DIRECT/META
  posture at session start; enforce read-only semantics for META; surface
  scope-overreach warnings for DIRECT.

  CENTROID:
  session-mode contract that shapes which actions are allowed before mutation

  IS:
  - one-line POSTURE banner at session start
  - read-only enforcement for META postures (no file writes, no commits, no API mutations)
  - scope-bounded mutation for DIRECT postures (only files explicitly required)
  - mid-session toggle surface ([Posture → X/Y])
  - workspace-default fallback when posture is undeclared

  IS NOT:
    collapse_zones:
      - permission system (posture is contract, not enforcement; harness gates
        enforce — this skill describes the contract)
      - approval queue (posture declares intent; approvals gate actions)
      - audit log (the banner is observable; audit lives elsewhere)
      - mode coercion (the user declares; the skill describes what each
        declaration means)
    sibling_overlaps:
      - /counter (both pre-commit primitives; counter falsifies, posture
        bounds scope)
      - /complement (both shape responses; complement detects geometry,
        posture declares contract)

  WHEN:
  - at session start (always)
  - on workspace switch (re-emit banner)
  - on explicit mode toggle ([Posture → X/Y])
  - when the next move could mutate state and the posture is META

  NOT WHEN:
  - mid-thought (posture is session-scoped, not per-message)
  - for permissions (posture describes; permissions enforce)
user-invocable: true
---

# /posture — Working Mode Contract

The two axes: **domain** (ENG / OPS) × **depth** (DIRECT / META).

| | DIRECT (execute) | META (analyze) |
|---|---|---|
| **ENG** | Implement, fix, ship code | Architect, plan, design |
| **OPS** | Run pipelines, hit APIs, generate artifacts | Audit outputs, review quality, refine playbooks |

## Session-Start Banner

At the start of any new session (or after workspace switch), output exactly:

```
POSTURE: <ENG|OPS>/<DIRECT|META> (reason: <explicit|workspace default|verb inference>)
```

Only ask a question if posture is ambiguous AND the next step has side effects.

## Hard Constraints by Posture

### META = read-only

- No file edits or writes
- No git commit / push
- No destructive commands
- No API writes (POST / PUT / PATCH / DELETE)
- If an action would mutate state, pause and ask: "Switch to DIRECT or keep read-only?"

### DIRECT = scoped mutation

- Only touch the files / modules explicitly required
- Run relevant validation (tests / lint / pipeline checks) before claiming done
- Repo-wide refactors, renames, or sweeping changes require pausing and asking
  even in DIRECT

## Posture Determination Priority

1. **Explicit declaration** (always wins) — e.g., `POSTURE: OPS/DIRECT`
2. **Verb inference**
   - DIRECT verbs: fix, implement, build, generate, run, patch, ship
   - META verbs: plan, design, analyze, audit, review, explore
   - Mixed verbs in one request: default to META and ask before mutating
3. **Workspace default** — declared in the workspace's CLAUDE.md
4. **Carry-forward** within the same session unless a toggle is declared

## Live vs Local Data Rule

When the task references an external system (API, CRM, third-party service):
- In **OPS/DIRECT**: default to live calls when the user asks for current state
- In **META**: allow read-only calls only
- If unclear whether to hit live APIs or analyze local exports, ask one line
  before proceeding

## Mid-Session Toggles

Output exactly one line, then immediately operate in the new posture:

```
[Posture → OPS/META]
```

For mixed-mode task lists, prefix each task:

```
[ENG/DIRECT] implement the parser
[ENG/META] design the next interface
[OPS/DIRECT] run the migration
[OPS/META] audit yesterday's pipeline output
```

## Scope Safety (Prevents Overreach)

Even in DIRECT mode, if the request implies repo-wide refactors, renames,
sweeping scrubs, or touching staged files not created in-session, pause and
ask before executing.

## Workspace Switching

If cwd moves into a different workspace, re-emit the POSTURE banner and re-evaluate
from the new workspace default unless explicitly pinned.

## Sidecar Integration

The sidecar chamber holds the current posture; the router hook detects
`[Posture → X/Y]` toggles and emits `<sidecar key="posture_shift" />` for
downstream consumers (chamber refresh, disposition update).

Posture-aware arrow firing is the load-bearing benefit: same user message means
different things in ENG/DIRECT vs OPS/META. The router weights confidence
against the chamber's disposition_bias for the active posture.
