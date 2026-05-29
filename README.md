# Sovereign Sidecar

### A hangar for your harnesses — posture-aware governance for any agent stack.

You already have a stack: skills, hooks, an orchestrator, your own way of working an
agent. The **Sovereign Sidecar** is the shim that rides alongside it — reading what
you're *about* to do and quietly equipping it with posture-aware, mode-governed
judgment. No new orchestrator. No rebuild. No persistence to manage. It bolts onto
the vehicle you already drive.

> **Two names, one primitive.** In the technical lane this is the **sidecar** — a
> governance shim attached to a primary skill stack. In the lane where you actually
> meet it, it's a **hangar for harnesses**: the place tinkerers store, tune, and
> maintain their agent rigs. Same thing, two registers — the technical name says what
> it *is*, the market name says how you *encounter* it.

---

## What it does

On every prompt, a single fail-soft `UserPromptSubmit` hook reads a lightweight
**chamber** (~200 tokens of pointers + disposition), pattern-matches your message
against a **quiver** of governance arrows, and — only when warranted — emits a quiet
signal tag your stack can act on. Zero LLM cost. Zero blocking. Pure text patterns.

```
USER MESSAGE
  ├─→ sidecar router (UserPromptSubmit hook, parallel, non-blocking)
  │     ├─ reads CHAMBER (pointers + disposition + current posture)
  │     ├─ intent match → arrow selection
  │     └─ quick-fire: <sidecar key="K" target="T" confidence="C" /> tags
  └─→ your primary work (unimpeded, in parallel)
```

### The quiver

| Arrow | Fires | Gives you |
|---|---|---|
| `/ingest` | before external context enters | metabolized context (no cargo-culting) |
| `/tom` | before you publish/express | centroid-preserving re-expression |
| `/complement` | after a move lands | the surfaces the move just exposed |
| `/counter` | before a decision commits | the strongest case against it |
| `/citation-intel` | before publication | extractability / readiness report |
| `/posture` | on a `[Posture → …]` toggle | an explicit working-mode contract |

(`/tactical-hydration` and `/consolidate` are support arrows — they fill the chamber;
you interact with the six above.)

---

## Quick start

1. **Drop the chamber** — copy `specs/chamber.yaml.example` to `~/.sidecar/chamber.yaml`
   (or `~/.claude/sidecar/chamber.yaml`) and tune each arrow's `disposition_bias` to taste.
2. **Register the hook** — copy the `UserPromptSubmit` block from
   `hooks/settings.json.template` into your `~/.claude/settings.json`, pointing at
   `hooks/sidecar-router.py`.
3. **Verify** — `bash tests/smoke.sh` (zero-cost, no model calls). You should see `PASS=10 FAIL=0`.

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
