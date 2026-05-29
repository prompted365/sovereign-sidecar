# Sidecar Proof Pack — Panel 1: Delegation

> **Sidecar catches what your agent skips while it is already in motion.**
>
> Same prompt. Same model. Same isolation. The only variable is whether the
> Sovereign Sidecar hook was active. Watch what the agent was about to ship.

---

## The setup

One goal, run through `claude -p` twice under **identical conditions**:

- **Goal:** *"Get `paymentsvc` to launch-readiness. It moves real money (charges, refunds, payouts, ledger). Delegate it to a swarm of subagents that audit the dimensions that matter, then orchestrate a go/no-go. Spec the delegation — don't execute it."*
- **Model:** `claude-sonnet-4-6` · spec-only · MCP off
- **Isolation:** clean `CLAUDE_CONFIG_DIR` — the control inherits **no** skills, agents, or settings. (One honest caveat below.)
- **Only difference:** the `delegate` arrow fires (with-sidecar) or it doesn't (without).

The agent is asked to produce a swarm/tranche spec. A blind judge (also `sonnet`, told nothing about which arm it's grading) scores each spec on four axes, and a deterministic regex audits ten structural slots.

---

## Before / after at a glance

Replicated across three independent runs (R1 + R2 ×2):

| | **without Sidecar** | **with Sidecar** |
|---|---|---|
| Total (judge, /12) | 8–10 | **11–12** |
| **Premise stress-test** (judge, /3) | **1** | **3** |
| Structural slots (regex, /10) | 5–6 | 8–10 |
| Decomposition Stress Test section | ❌ absent | ✅ present |

The headline isn't the total. It's the **premise stress-test axis: 1 → 3, in every single run.** That's the move a senior reviewer makes and a confident agent skips — *attacking its own plan before acting on it.*

---

## The artifact delta — what the agent was about to skip

Both specs are competent. Both name the right audit dimensions. The control even has a confident **"Deliberately Out of Scope"** section.

But the blind judge caught the difference:

> **Without Sidecar (premise stress = 1):**
> *"The 'Deliberately Out of Scope' table presents confident exclusions with justifications, but that is not a stress-test of the decomposition — it is a boundary declaration. The spec never names what the chosen slice gets structurally wrong. No seam analysis: A2 (financial correctness) and A4 (data integrity) both touch ledger invariants … neither owns the middleware/queue hand-off between them. No structural failure modes of the cut are identified; the decomposition is presented as a single confident pass."*

The control declared what it *wouldn't* do. It never asked what its own plan *gets wrong*. That's the blind spot that ships.

> **With Sidecar (premise stress = 3):**
> *"The Decomposition Stress Test names four genuine structural failure modes — not boundary hygiene or out-of-scope honesty, but actual exploit paths that exist because of the chosen slice."*

Those four, lifted verbatim from the with-sidecar spec — each one a way a payment service silently double-charges or loses money while **every individual auditor reports clean:**

1. **A2 + A4 atomic-handoff gap** — charge math is correct, ledger schema is sound, but the write between them isn't atomic. Processor charges the user, DB write fails, money is lost. Lives in neither agent's brief.
2. **A5 + A3 concurrent-replay race** — a valid idempotency key racing across a velocity-window reset double-charges. Neither an idempotency failure nor a velocity failure alone — only in conjunction.
3. **A7 + A2 + A3 retry-storm** — processor timeout where the charge went through but the response dropped triggers a retry; whether it double-charges depends on idempotency-key TTL vs retry window, which no agent is told to cross-check.
4. **A8 + A10 alert-runbook staleness** — an alert fires pointing at a runbook that references a deprecated endpoint. Alerts exist, runbooks exist, incident response is broken.

The judge — blind — independently flagged the *same* A2/A4 ledger seam and A3 middleware handoff as **missing from the control**. The sidecar arm named them before dispatch. That convergence is the proof: this isn't the regex being satisfied by a heading; it's the artifact carrying a real governance move it wouldn't have otherwise.

---

## ROI Receipt

```
## Sidecar Receipt — paymentsvc delegation

Boundary detected:   DELEGATE (fan a real-money audit out to subagents)
Missing move inserted: COUNTER + COMPLEMENT (stress the decomposition)

What changed in the artifact:
  + Added a Decomposition Stress Test section
  + Named 4 cross-agent exploit seams (double-charge / money-loss paths)
  + Each seam assigned to a synthesis-stage probe (A11)
  premise stress-test:  1  ->  3   (blind judge)
  structural coverage:  6  -> 8-10 / 10

Verdict:  the swarm plan is now safe to dispatch
Saved:    a bad swarm handoff that would have audited a payment
          service while leaving four double-charge seams uncovered
```

The user never had to know what "governance" means. They asked to delegate. The agent came back having proven it checked the thing it was most likely to skip.

---

## Methodology — and what this does NOT yet show

Honesty is the product. The same surface-discipline the sidecar enforces applies to its own proof:

- **n = 3 total** (R1 `deleg-20260529T102156`; R2 `162502` + `162509`). The **with-sidecar** arm is the stable signal: premise_stress = 3 and total 11–12/12 every run. The fresh **control** sits at 8/12 (R1's 10/12 was the high outlier).
- **The turn-count confound is unresolved, not beaten.** With-sidecar sometimes runs more turns. Slots-per-turn favored the sidecar in one R2 run and the control in the other. What's robust is the *judge axis* and *raw* slot coverage — not the turn-normalized version. We do not claim the sidecar wins "for free."
- **`paymentsvc` is a goal string, not a real repo.** The agent reasoned about a described service, not files/tests/migrations on disk. The strongest demo — the sidecar refusing to touch money-moving code like ordinary app code during an actual refactor — is **not yet measured.** It's the next panel, not this one.
- **One isolation leak:** a global `~/.claude/CLAUDE.md` posture banner bleeds into the "isolated" config (memory file isn't gated by `CLAUDE_CONFIG_DIR`). It's symmetric across both arms, so the delta holds — but it's why "ship posture+mode IN the package" is on the backlog ([issue #1](https://github.com/prompted365/sovereign-sidecar/issues/1)).

The directive that produces the Decomposition Stress Test was validated against this exact eval before shipping ([`e77e254`](https://github.com/prompted365/sovereign-sidecar/commit/e77e254)): the patch had to move the *blind judge's* axis, not just the regex slot, or it would have been reverted as gaming. It moved both.

---

*Panel 1 of the Sidecar Proof Pack. Panels 2–5 (refactor blast-radius, release preflight, context hydration) flex against a repo with mass and are forthcoming.*
