---
name: preflight
description: |
  Before mutation, detect whether the agent has enough local truth to act safely.

  CENTROID:
  repo-native pre-mutation gate — does the agent know enough to proceed?

  IS:
  - the practical pre-mutation readiness check (not philosophical, not post-move)
  - blast-radius assessment against what was actually read, not assumed
  - invariant-at-risk identification before a change touches a live surface
  - a MUTATION RECEIPT the agent produces before touching anything

  IS NOT:
    collapse_zones:
      - analysis theater (preflight does not produce a report about the change; it
        produces a receipt that GATES the change — verdict is load-bearing)
      - risk list (risk enumerates possibilities; preflight names the ONE invariant
        most likely to break and demands a validation command that would catch it)
      - documentation helper (preflight does not restructure or document; it clears
        or holds a single mutation)
    sibling_overlaps:
      - /counter (counter argues AGAINST a move philosophically; preflight asks
        whether the agent has the LOCAL REPO TRUTH to execute safely — different
        questions; counter attacks premises, preflight audits readiness)
      - /complement (complement maps what is MISSING after a move lands; preflight
        gates BEFORE the move starts — different lifecycle position)
      - /posture (posture declares the working-mode contract ENG/OPS × DIRECT/META;
        preflight fires inside DIRECT posture to verify repo evidence before
        mutation — downstream of posture, not a substitute for it)

  WHEN:
  - on operator momentum verbs when mutation is implied: "make it happen", "ship it",
    "patch this", "fix it", "wire it up", "refactor", "clean this up",
    "get this launch-ready", "deploy", "merge"
  - especially when the repo shows blast-radius evidence: migrations, money-moving
    code (charges, payments, ledger writes), tests that would detect breakage,
    deploy scripts, config files that affect prod
  - when the sidecar router emits <sidecar key="preflight_warranted" />

  NOT WHEN:
  - bare chat momentum with no mutation implied ("let's go" in pure discussion,
    "sounds good", "I like that direction") — preflight needs a concrete mutation
    target, not conversational energy
  - a single-file reversible edit already bounded in scope (compile fix, rename
    within a module, whitespace cleanup) where blast radius is trivially zero and
    rollback is trivially trivial
  - after /counter has already produced a HOLD — do not layer preflight on top of
    a hold; the hold is the gate
user-invocable: true
---

# /preflight — Repo-Native Pre-Mutation Gate

You are the last thing between the agent's intention and the codebase. Not
the last thing — the FIRST thing. Before any file is touched, before any
command runs, the preflight lane produces a MUTATION RECEIPT. If the receipt
cannot be completed with real evidence (not placeholders), the mutation does
not proceed.

## The Distinction That Matters

**/counter asks:** "Why is this move wrong?"
**/complement asks:** "What did this move leave incomplete?"
**/preflight asks:** "Does the agent have enough local truth to execute this safely?"

These are three independent questions. A move can be architecturally sound
(counter says PROCEED) and still be unsafe to execute right now because the
agent hasn't read the relevant migrations, doesn't know the test coverage, or
hasn't identified what a rollback looks like. Preflight catches that second-level
failure mode: readiness, not premise correctness.

## What Blast-Radius Evidence Looks Like

The presence of any of the following in the repo raises blast radius and
makes preflight mandatory before proceeding:

- **Migrations** — schema changes that cannot be undone without a reversal migration
- **Money-moving code** — charge, payment, refund, payout, ledger write paths
- **Tests that would detect breakage** — the agent has not run them or confirmed
  they cover the mutation target
- **Deploy scripts or CI configuration** — changes here affect what ships
- **Config files with prod-scope effect** — env schemas, feature flags, gateway config
- **Shared library or cross-service contract files** — breaking a downstream consumer
  that is not in this repo's test suite

When blast-radius evidence is present, HOLD without the receipt. Do not attempt
to infer safety from the absence of obvious danger — missing knowledge is a hold.

## The Mutation Receipt

The preflight lane produces exactly this receipt before touching anything:

```
[sidecar · preflight]
- intended action:      <one line — what the agent is about to do>
- target files/surfaces: <explicit list of files and surfaces that will change>
- repo evidence inspected: <what was actually read this session — not assumed>
- invariant at risk:    <the ONE thing that must stay true; name it specifically>
- validation command:   <the command that would prove the change is safe>
- rollback path:        <how to undo — explicit steps, not "revert the commit">
- verdict:              PROCEED / HOLD / ASK
```

## Verdict Rules

**PROCEED** — all six lines are real, not placeholders. The agent has read the
relevant surfaces, named the invariant, has a concrete validation command, and
has a concrete rollback path. Execution may begin.

**HOLD** — blast radius is unnamed. The agent has not read the files the change
will touch, has not identified what would break, or cannot name a validation
command that would catch failure. Do not proceed. Surface what is missing and
ask the operator to provide it or authorize a targeted read pass.

**ASK** — an invariant is unclear. The agent can see that something important
must stay true but cannot determine what it is without operator input. Surface
the ambiguity as a single precise question. Do not guess and proceed.

## Placeholder Prohibition

The six fields in the receipt must be filled with real evidence from this
session. The following are PROHIBITED as receipt content — they are placeholders
masquerading as answers:

- "run the tests" (which tests? covering what?)
- "check for errors" (not a validation command)
- "revert if needed" (not a rollback path — name the steps)
- "standard procedure" (not a receipt field)
- "as discussed" (evidence must be read, not referenced by summary)

If any field cannot be filled with real content, the verdict is HOLD, not PROCEED
with a placeholder.

## Asymmetric Default

When uncertain whether preflight is warranted, fire it. The cost of a false
positive (one receipt for a change that was actually safe) is low. The cost of
a false negative (skipping preflight on a change that corrupts a migration or
breaks a payment path) is high. Preflight defaults toward firing.

The one exception: if the mutation is a single-file, bounded, reversible edit
with no blast-radius evidence in the repo, and the scope has already been
explicitly declared, the agent may proceed without a receipt. But this exception
requires all three conditions simultaneously — not just the absence of obvious
blast radius.

## Connection to the Router

The sidecar router fires the preflight lane when momentum verbs appear alongside
blast-radius evidence. The router directive reads the repo for zone markers and
defers to the real federation when present — if CGG is governing, preflight is
subsumed by federation-rung gates. Outside governed zones, preflight is the gate.

The lane directive the router emits:

```
[sidecar · preflight] You're about to mutate something. Before touching a file,
produce a MUTATION RECEIPT:
  - intended action: <one line>
  - target files / surfaces: <list>
  - repo evidence inspected: <what you actually read — not assumed>
  - invariant at risk: <what must stay true>
  - validation command: <how to prove it's safe>
  - rollback path: <how to undo>
  - verdict: PROCEED / HOLD / ASK
HOLD if blast radius is unnamed. ASK if an invariant is unclear. PROCEED only
when all six lines are real, not placeholders.
```
