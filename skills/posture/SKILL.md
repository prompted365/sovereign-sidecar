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

## Session-Start Posture Lifecycle (router contract)

This section specifies the contract the `hooks/sidecar-router.py` router **must**
satisfy. The router lane owns the implementation; this skill owns the spec.

### 1. Banner emission

The router must emit the POSTURE banner at session start and on every
`[Posture → X/Y]` toggle detected in a submitted prompt. The banner format is
exactly:

```
POSTURE: <ENG|OPS>/<DIRECT|META> (reason: <explicit|workspace default|verb inference>)
```

- **Session start** — router reads `chamber.posture` field; if absent or empty,
  applies determination-priority (see §2) and writes the resolved value back into
  the chamber before injecting the banner directive.
- **Toggle detected** — router parses the new posture, writes it to
  `chamber.posture`, updates `chamber.refreshed_at`, and injects the banner
  directive as inline context before the primary work proceeds.
- The banner is injected as human-readable model context (not a machine KV tag)
  so the model can act on the declared constraint immediately.

### 2. Posture persistence (chamber is the source of truth)

The chamber's `posture:` field is the single source of truth for active posture
within a session:

- On session start: initialize from explicit declaration → verb inference →
  workspace default (in that priority order).
- On `[Posture → X/Y]` toggle: overwrite `chamber.posture` immediately; do not
  carry the prior value forward.
- Between prompts: carry forward unchanged — the router must NOT re-derive posture
  on every prompt; it reads `chamber.posture` and applies it.
- The router must NOT re-emit the full banner on every prompt — only at session
  start and on toggle events. Repeated banner injection introduces noise without
  adding contract clarity.

### 3. Posture-derived trigger weighting

Active posture shifts the router's confidence thresholds for mutation-implying
arrows (`/counter`, `/complement`):

- **Under META**: when a prompt implies mutation (detected by mutation-keyword
  presence — write/edit/delete/commit/create/modify/rename/deploy/push/patch or
  API verbs POST/PUT/PATCH/DELETE), **raise** counter/preflight firing confidence
  above the arrow's `disposition_bias` baseline. A mutation under META is a
  contract violation worth surfacing before it executes.
- **Under DIRECT**: **lower** mutation-trigger confidence toward the arrow's
  baseline. Mutation is expected; the router's job is scope-checking, not
  general mutation friction.
- The weighting is a multiplier on `disposition_bias`, not a replacement. The
  chamber's per-arrow bias remains the calibration anchor; posture shifts the
  effective threshold.

### 4. Pre-mutation enforcement under META

When `chamber.posture` is META (either `ENG/META` or `OPS/META`) and the router
detects a mutation-implying prompt, the posture lane fires a HOLD-and-ask
directive before the primary work executes:

```
[sidecar · posture] Active posture is META (read-only contract).
This prompt implies a mutation: <one-sentence description of the detected action>.
META constraint: no file edits/writes, no git commits, no destructive commands,
no API writes (POST/PUT/PATCH/DELETE).

Switch to DIRECT or keep read-only?
  → "switch" or "POSTURE: <domain>/DIRECT" to proceed with mutation
  → "keep" or no response to proceed read-only (mutation will be blocked)
```

The directive is injected as model context so the model surfaces the hold to the
user and waits for resolution. The router does not block the tool call at the
physics layer (that is the harness gate's job if installed); the posture lane
raises the hold through the perception layer (model-visible directive).

### 5. Carry-forward discipline

- Posture carries forward within the session unless a toggle is explicitly detected.
- A workspace switch (cwd moves into a different workspace) triggers a
  re-evaluation: the router re-derives posture from the new workspace's default
  (if available) and re-emits the banner with `reason: workspace default`.
- Explicit `POSTURE: X/Y` declaration in a prompt always wins over carry-forward,
  regardless of what the chamber currently holds.

---

## Sidecar Integration Note

The chamber's `posture:` field couples this skill to the router at runtime.
Posture-aware arrow firing is the load-bearing benefit: the same user message
means different things in ENG/DIRECT vs OPS/META. The router weights
`disposition_bias` against the active posture (§3 above) rather than treating
all prompts identically.

The posture lane does not own the chamber schema — that lives in
`specs/chamber.md`. This skill owns the behavioral contract that the chamber
enables.
