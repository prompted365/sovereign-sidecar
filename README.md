# Sovereign Sidecar

**Category: Runtime Preflight for AI Agents**

> **a repo-native preflight mentor that catches what your agent skips before it ships, delegates, publishes, or mutates**

In-flight obstacle avoidance for AI agents. You already have a stack: skills, hooks,
an orchestrator, your own way of working an agent. The **Sovereign Sidecar** bolts
onto the vehicle you already drive — reading what you're *about* to do and quietly
surfacing the move your agent was most likely to skip.

No new orchestrator. No rebuild. No persistence to manage.

> **Also known as:** the **hangar for harnesses** — the place tinkerers store, tune,
> and maintain their agent rigs. Same primitive, two registers: the technical name says
> what it *is*, the market name says how you *encounter* it. If you're here on a
> Saturday afternoon curious about posture-aware agent work, this is the door.

---

## What it does

On every prompt, a single fail-soft `UserPromptSubmit` hook reads a lightweight
**chamber** (~200 tokens of pointers + disposition), pattern-matches your message
against a **quiver** of governance arrows, and — only when warranted — injects the
matched lane's **protocol as a readable directive**, so your agent runs that lane
inline *before* it acts. The intent-match is zero-LLM-cost text patterns; the lane
itself runs in the turn you're already paying for, only when governance is warranted.

```
USER MESSAGE
  ├─→ sidecar router (UserPromptSubmit hook, parallel, non-blocking)
  │     ├─ reads CHAMBER (pointers + disposition + current posture)
  │     ├─ intent match → arrow selection
  │     └─ injects the lane directive — the model runs the lane inline:
  │          ingest / tom / complement / counter → coherence read → ACT or REFUSE
  └─→ your primary work (unimpeded, in parallel)
```

The model is the consumer: the directive carries the lane's actual protocol, so the
lane's reasoning lands in your thread — not a tag your stack has to wire up. The
terminal of a lane pass isn't "proceed"; it's a coherence read that ends in **act or
refuse**. That refuse-path is the structural difference from tool-chain orchestration:
recipes end at *push/mutate*; the sidecar ends at *whether the move coheres*.

### The quiver

| Arrow | Fires | Gives you |
|---|---|---|
| `/ingest` | before external context enters | metabolized context (no cargo-culting) |
| `/tom` | before you publish/express | re-expressed content — meaning preserved, audience conformed |
| `/complement` | after a move lands | the surfaces the move just exposed |
| `/counter` | before a decision commits | the strongest case against it |
| `/citation-intel` | before publication | extractability / readiness report |
| `/posture` | on a `[Posture → …]` toggle | an explicit working-mode contract |
| `/delegate` | before you fan out to subagents | a governed swarm spec — per-agent briefs, dependency graph, decomposition stress test |

(`/tactical-hydration` and `/consolidate` are support arrows — they fill the chamber;
you interact with the seven above.)

> `/delegate` is the arrow with measured proof: same prompt, same model, same isolation —
> with the arrow active the agent names the cross-agent failure seams it otherwise ships.
> See [`proof/delegation.md`](proof/delegation.md).

---

## Quick start

1. **Drop the chamber** — copy `specs/chamber.yaml.example` to `~/.sidecar/chamber.yaml`
   (or `~/.claude/sidecar/chamber.yaml`) and tune each arrow's `disposition_bias` to taste.
2. **Register the hook** — copy the `UserPromptSubmit` block from
   `hooks/settings.json.template` into your `~/.claude/settings.json`, pointing at
   `hooks/sidecar-router.py`.
3. **Verify** — `bash tests/smoke.sh` (zero-cost, no model calls). You should see `PASS=14 FAIL=0`.

The router is **fail-soft by design**: a missing chamber, bad stdin, or any exception
emits empty output. Your prompts are never blocked.

### Plays well where it lands

The router walks up from `cwd` for a zone marker (`.ticzone`, `.federation-root`, …)
and **stays silent inside an already-governed environment** — so global (user-scope)
registration is safe. It fires in your own environments and defers wherever a real
governance substrate already runs. (`SIDECAR_IGNORE_ZONE=1` overrides.)

---

## The upgrade lane

The sidecar is deliberately stateless. When you start wishing it remembered things,
each wish maps to exactly one piece of the full [Ubiquity](https://promptedllc.com)
substrate:

| You'll wish for… | …which is | in Ubiquity |
|---|---|---|
| posture history | tic-gated conformations | (persistent) |
| a quiver that remembers what worked | the harmony manifold | (persistent) |
| tracking recurring conditions | signal manifold + warrants | (persistent) |
| promoting a lesson to a rule | `/review` + the CogPR queue | (persistent) |

The sidecar is the on-ramp. You don't have to take it — but the door is there.

---

## Lineage / Depth

The arrows in the quiver are Breyden-originated governance primitives. For those
who want the spine underneath:

- **/tom** runs **centroid-preserving re-expression** — holds the source content's invariant meaning intact while conforming its expression to a different audience, density, or purpose. Not summarization. Not paraphrase. The centroid survives.
- **/complement** runs **topological closure inference** — after a move lands, it asks what the move just structurally exposed. Direction-agnostic: the complement may be inverse, adjacent, upstream prerequisite, downstream proof obligation, or scope correction.
- **Council resonance** maps each arrow to the [Ubiquity Council](references/council-resonance.md) postures that ground it — the deeper frame the sidecar is an outpost of.

These terms are not required to use the package. They are load-bearing for the upgrade lane: when you start wishing the sidecar remembered more, these are the concepts that scale into the full Ubiquity substrate.

---

## Part of the Ubiquity Ecosystem

Sovereign Sidecar is a **standalone outpost of [Ubiquity](https://promptedllc.com)** —
usable entirely on its own, but pointing home at the primary federation. It packages
Breyden-originated posture/mode-lane discipline (`/ingest`, `/tom`, `/complement`,
`/counter`, and the expression-activated meta lane) so it travels to environments the
full substrate doesn't govern yet. It is a sibling, in the same spirit as the
Context Grapple Gun and other Ubiquity outposts: standalone, clearly badged, pointing
home.

It is **not** enterprise SaaS and **not** B2B governance infrastructure. It's the
consumer-lane harness for harnesses — the thing you install on a Saturday afternoon
because you're curious about posture-aware agent work, and by Tuesday you wonder why
your day-job stack doesn't have it.

---

## License

Source-available under the [Fair Use License](LICENSE.md): free to tinker with, learn
from, run on your own rigs, fork, and contribute to. **Commercial use is welcome —
permitted by agreement** with Prompted LLC. Reach out at **breyden@prompted.community**;
the agreement exists to steward the project, not to gatekeep.

---

*Built by [Prompted LLC](https://promptedllc.com). Part of the Ubiquity ecosystem.*
