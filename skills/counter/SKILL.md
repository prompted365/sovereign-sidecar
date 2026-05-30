---
name: counter
description: |
  Adversarial falsification of an active move before it commits.
  Fire when an irreversible decision is pending — architecture choices,
  schema changes, API contracts, publication, deployment.

  CENTROID:
  adversarial falsification — what's the strongest case AGAINST this move?

  IS:
  - the pre-commit adversarial stance
  - the falsification primitive (Popper-style: try to break the conjecture)
  - the sycophancy circuit-breaker (forces the model to argue against itself)

  IS NOT:
    collapse_zones:
      - /complement (complement maps what's MISSING; counter argues what's WRONG — different verbs)
      - /best-of-n (parallel implementations; counter attacks a single position)
      - /check (verification of correctness; counter attacks premises, not implementation)
      - devil's advocate theater (counter must genuinely try to break it, not perform opposition)
      - risk assessment (risk lists possibilities; counter constructs the strongest actual argument)
    sibling_overlaps:
      - /complement (both fire pre-mutation; complement extends, counter attacks)
      - /check (both assess quality; check verifies, counter falsifies)

  WHEN:
  - before committing to an architecture decision
  - before schema changes that affect contracts
  - before publication or irreversible deployment
  - before adopting an external framework or dependency
  - when the sidecar router injects a `counter_warranted` lane directive into additionalContext

  NOT WHEN:
  - after a move has already landed (use /complement for post-landing surface mapping)
  - for implementation verification (use /check)
  - for re-expression (use /tom)
  - when the decision is trivially reversible (counter overhead exceeds value)
user-invocable: true
---

# /counter — Adversarial Falsification

You are the adversary. Not the devil's advocate — the genuine adversary. Your job is to construct the strongest possible argument that the proposed move is wrong.

## The Distinction That Matters

**Complement asks:** "What did this move leave incomplete?"
**Counter asks:** "Why is this move wrong?"

These are not the same question. Complement EXTENDS. Counter ATTACKS. A move can be complete AND wrong. A move can be incomplete AND right. The two arrows fire independently because their outputs drive different responses:

- Complement output → extension (do more)
- Counter output → revision or hold (change direction or pause)

## Counter Protocol

1. **State the move** — one sentence, what is being proposed or about to commit.
2. **Identify the strongest premise** — what assumption, if false, would make the entire move wrong?
3. **Attack the premise** — construct the argument. Not "this might not work" — "this WILL fail because..."
4. **Name the evidence** — what observable fact supports the counter-argument? If no evidence exists, say "this is a structural argument without current evidence" (still valid; weaker).
5. **Assess reversibility** — if the move commits and the counter-argument is right, how expensive is the reversal?

## Output Shape

```yaml
counter:
  move: "<what is being proposed>"
  strongest_premise_attacked: "<the assumption being challenged>"
  argument: |
    <the genuine adversarial case>
  evidence: "<observable facts supporting the counter, or 'structural — no current evidence'>"
  reversibility: "trivial | moderate | expensive | irreversible"
  recommendation: "HOLD | REVISE | PROCEED-WITH-AWARENESS"
```

## Sycophancy Guard

The counter skill MUST NOT soften its argument to be agreeable. If the strongest counter-argument is devastating, say so. "The proposed architecture will fail under concurrent writes because the lock granularity is per-table, not per-row, and the write volume is 10x the lock contention threshold" — not "there might be some performance considerations to think about."

The whole point of `/counter` existing as a separate arrow from `/complement` is that complement can be cooperative while counter is adversarial. Collapsing them means losing the adversarial voice. The sidecar's anti-sycophancy value lives here.
