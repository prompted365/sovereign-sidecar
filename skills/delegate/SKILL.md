---
name: delegate
description: |
  Govern the fan-out to subagents — ensure the dispatch is a coherent spec,
  not an ad-hoc spray, before anything is spawned.

  CENTROID:
  orchestrator-as-delegator gate — govern the swarm/tranche spec before dispatch.

  IS:
  - the orchestration checkpoint: brief quality, slice soundness, synthesis contract
  - the Decomposition Stress Test: naming what the chosen cut GETS WRONG,
    not just what it correctly excludes
  - the verify-don't-trust-done contract: the parent's independent verification
    protocol for each subagent's result
  - posture + ingest scoping for each subagent before any work begins

  IS NOT:
    collapse_zones:
      - swarm executor (delegate governs the spec; spawning is downstream)
      - brief author (delegate governs brief quality; content is the orchestrator's)
      - synthesis agent (delegate specifies how verification happens; it does not
        do the cross-agent verification — that is the parent's execution responsibility)
      - scope auditor (delegate does not audit individual subagent scopes for
        correctness; it audits whether the decomposition leaves structural seam gaps)
    sibling_overlaps:
      - /counter (counter attacks a single move's premises; delegate attacks the
        structural soundness of a FAN-OUT — seam gaps, blind spots, runtime leaks
        that exist because of how the slicing was done)
      - /complement (complement maps missing expressions after a move; delegate
        checks whether the fan-out set is complete BEFORE dispatch — different
        lifecycle position)
      - /preflight (preflight gates pre-mutation readiness from the repo-evidence
        angle; delegate gates pre-dispatch soundness from the decomposition-quality
        angle — both fire before action, different axes)

  WHEN:
  - when an orchestrator is about to fan a goal out to subagents (spawn, swarm,
    tranche, parallelize, delegate, decompose, break down into agents)
  - when a swarm or tranche spec is being authored and involves a goal with
    cross-cutting invariants (money-moving, schema-touching, multi-service)
  - when the sidecar router emits <sidecar key="delegate_warranted" />

  NOT WHEN:
  - for single-agent work (there is no fan-out to govern)
  - after the spec has already been dispatched (govern before; do not audit
    after the fact — that is /complement or /counter's territory)
  - when the "subagents" are purely decorative parallel reads with no synthesis
    contract and no cross-cutting invariants (overhead exceeds value)
user-invocable: true
---

# /delegate — Orchestrator-as-Delegator Gate

You are governing the spec before the swarm ships. Not the swarm — the spec.
The moment the orchestrator fans a goal out to subagents is the moment the
cross-cutting invariants become invisible to each individual agent. Every subagent
operates in a scoped context. Scoped contexts cannot see seams. Seams are where
money is lost, migrations break, and audit surfaces report clean while the system
is already wrong.

The delegate lane fires before dispatch. It produces a governed spec, not a
table row per agent and a prayer that coverage is complete.

## Why This Arrow Exists — The Proof

`proof/delegation.md` documents the controlled experiment (R1 + R2×2 + R3):

- **Goal:** fan a real-money service audit out to a subagent swarm
- **Only variable:** whether the delegate arrow fired
- **Result:**
  - premise stress-test (blind judge): **1 → 3** in every run
  - Decomposition Stress Test section: absent without sidecar, present with it
  - structural coverage (regex): 5–6/10 → 8–10/10

The headline is the judge axis, not the total. The blind judge independently
flagged the same A2/A4 ledger seam and A3 middleware handoff as missing from the
control arm. Both were named in the with-sidecar arm before dispatch. Convergence
across blind judgment and structured audit is the proof that this is a real
governance move, not a heading the regex is satisfied by.

For n: premise_stress delta with-sidecar=3 vs control=1 replicated n=4
(R1 + R2×2 + R3); the verify-don't-trust-done clause measured n=1 at R3
(verification_rigor judge axis 2 vs control 1). Methodology limitations are
documented in `proof/delegation.md` — the turn-count confound is unresolved,
the `paymentsvc` goal is a described service not a real repo, and one isolation
leak (global CLAUDE.md posture banner) was symmetric across both arms.

## The Six Governance Moves

When the delegate arrow fires, the orchestrator runs these six moves before
spawning anything.

### 1. TOM Each Brief

Every subagent brief must preserve the goal's centroid. Not a summary. Not a
scoped slice. The centroid — the invariant that organizes the whole goal — must
be present in every brief, so no subagent drifts off it in isolation.

**Format:** emit each brief as its own discrete block under a named heading.
One heading per subagent: `SA-1`, `A-1`, `T-1`, `Agent-1` — the label scheme
is the orchestrator's choice, but DISCRETE per-agent blocks are mandatory. A
single table row per agent is not a brief. It is a cell.

Each brief block must carry:
- **Scope** — what this agent is responsible for (bounded, not aspirational)
- **Sources** — pointers to where the agent should hydrate from (not content dumps)
- **Must-NOT** — an explicit line naming what this agent must not do, touch,
  assume, or cross-check with a sibling's domain

The Must-NOT line is not politeness. It is the seam declaration. If two agents
both own "data integrity," the seam between their definitions of that term is
where the system breaks.

### 2. Decomposition Stress Test

Attack your own decomposition. This section is mandatory and must be titled
literally **Decomposition Stress Test**.

The section names 3 or more structural failure modes of THIS cut — not what
the decomposition correctly excludes, not boundary hygiene, not "out of scope"
declarations. Those are correct and irrelevant. The stress test names what the
chosen slice GETS WRONG:

- **Seam gaps** — places where two agents' scopes touch and neither fully owns
  the invariant at the boundary
- **Blind spots** — an assumption that one agent makes which a peer's scoped
  context would swallow without surfacing as an error
- **Runtime leaks** — a failure mode that only appears when the agents' results
  are composed at synthesis, invisible to any individual agent running alone

A control example of what does NOT count as a stress-test item:
"This agent will not audit authentication." That is a scope boundary. It says
nothing about what the decomposition gets wrong.

A real stress-test item from `proof/delegation.md`:
"A2 + A4 atomic-handoff gap — charge math is correct, ledger schema is sound,
but the write between them isn't atomic. Processor charges the user, DB write
fails, money is lost. Lives in neither agent's brief."

The difference: the real item names a seam that exists BECAUSE of the chosen
cut, that both agents would miss, that produces a real failure mode.

### 3. Verify, Don't Trust "Done"

Bounded subagents return "done" for work that silently failed. Their scoped
context cannot see the cross-cutting inconsistency a peer would catch. A "done"
report is necessary — not sufficient.

The spec must include a synthesis contract: how the PARENT independently verifies
each subagent's result before accepting it. Acceptable verification forms:

- **Re-run against source** — parent re-executes a check against the same source
  data the subagent used, without accepting the subagent's interpretation
- **Spot-check vs source** — parent reads N rows from the source directly and
  compares to the subagent's output
- **Cross-validate with sibling** — parent presents each subagent's output to
  a peer subagent and asks whether it is consistent with the peer's findings
- **Counter-check** — parent runs a specific falsifying probe against the
  subagent's conclusion

"Review the subagent's output for quality" is not a verification contract. It
is trusting the subagent's own framing. Verification must be independent of
the subagent's narrative.

### 4. Complement the Fan-Out

Check whether the agent set is complete. Is there a load-bearing
lane missing — an audit dimension, a service boundary, a synthesis agent
that should exist but doesn't?

Apply the structural relevance gate from `/complement`:
- Does adding an agent change implementation, governance, proof burden, a
  boundary, or what must happen next?
- If not, the additional agent is decorative. Resist over-spawning.

### 5. Point, Don't Inscribe

Briefs POINT subagents at sources. They do not dump content into the brief.

A brief that includes 200 lines of schema definitions is not a brief — it is
a partial context dump that the subagent will treat as canonical and the
orchestrator will treat as delivered. The subagent then reads nothing else.
The schema changes. The brief is now wrong.

Each source reference in a brief should be:
- A file path with a purpose statement ("read `migrations/` to understand
  schema state — do not assume the schema matches the API contracts")
- A named query or command the subagent should run
- A pointer to the surface, not the surface itself

### 6. Sequence and Parallelize

Make dependencies explicit. State the dependency graph. Where independence
holds, run briefs in parallel. Where a true dependency exists (Agent B cannot
start until Agent A's result is available), serialize and name the handoff.

"Run all agents in parallel" is not a dependency graph. It may be correct, but
it must be stated as a deliberate decision, not a default.

**Posture scope:** give each subagent an explicit DIRECT/META scope so none
overreach. A subagent scoped META cannot mutate. A subagent scoped DIRECT must
also carry the invariant it is responsible for keeping true.

**Ingest shared context:** metabolize any shared context before handing it down.
Do not paste raw external material into multiple briefs. Run `/ingest` on it
once at the orchestrator level and point subagents at the metabolized form.

## Output Shape

The delegate lane produces an explicit spec before any subagent is spawned.
The spec is not prose. It is structured enough that a different orchestrator
reading it could execute the dispatch without asking questions:

```
## Dispatch Spec — <goal summary>

### Decomposition Stress Test
<3+ structural failure modes of this cut>

### Agent Briefs

#### A-1: <name>
- Scope: ...
- Sources: ...
- Must-NOT: ...
- Posture: DIRECT | META

#### A-2: <name>
...

### Dependency Graph
<which agents are independent / which must serialize and why>

### Synthesis Contract
<how the parent independently verifies each agent's result>
```

The Decomposition Stress Test section comes FIRST — before the briefs — because
the seam analysis should inform the final brief design, not be retrofitted after
briefs are written.
