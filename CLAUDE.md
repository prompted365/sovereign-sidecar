# Sovereign Sidecar — Domain CLAUDE.md

> Before performing any action, read the [federation CLAUDE.md](../../CLAUDE.md) and the [estate CLAUDE.md](../CLAUDE.md) to understand governance hierarchy. This is a **domain rung** under the developer estate (`canonical_developer/`). Authority flows downward only: federation → estate → this domain.

## Domain Identity

Sovereign Sidecar is the portable, persistence-free packaging of Breyden-originated posture/mode lane discipline for non-Ubiquity environments. It is an expression-activated meta lane that equips existing agent stacks with a governance shim before mutation.

**Load-bearing line:** Sovereign Sidecar is not a new orchestration product. It ships the Ubiquity-shaped interface before the buyer fully onboards into the Ubiquity substrate.

## Source Lineage

The following primitives are Breyden-originated originals:

- `/ingest` — metabolize external context without cargo-culting
- `/tom` — theory of mind, centroid-preserving re-expression
- `/complement` — topological closure inference (what did the move expose?)
- `/counter` — adversarial falsification (what's the strongest case against?)
- Posture/mode-equipped runtime inference
- Expression-activated meta lane skeleton
- Reusable skeleton deployment across Ubiquity and non-Ubiquity environments

External repos and public agent tooling are market validation, not source lineage.

## Architecture

```
USER MESSAGE
  │
  ├─→ UserPromptSubmit hook (parallel, non-blocking)
  │     └─→ Router (hooks/sidecar-router.py — the hook IS the router)
  │           ├─ Reads CHAMBER (pointers + disposition + dynamic posture)
  │           ├─ Intent assessment → quiver arrow selection
  │           └─ Quick-fire: <sidecar key="K" target="T" /> tags
  │                → downstream hook catches regex
  │                → pulls context from chamber pointer
  │                → fires the arrow
  │
  └─→ Primary work (unimpeded, parallel)
```

### Outpost Boundary

The router defers to the real federation when present: on every prompt it walks `cwd` up for a zone marker (`.ticzone`, `.federation-root`, `.estate-root`, `.domain-root`, `.site-root`) and stays silent if one is found. This makes **global (user-scope) registration safe** — the sidecar fires in non-Ubiquity environments and falls silent wherever CGG already governs. The same zone primitive scopes a resident outpost (e.g. `homeskillet-gk`) to a domain boundary rather than bleeding across rungs. Spec: `specs/router.md` → Outpost Boundary. Override: `SIDECAR_IGNORE_ZONE=1`.

### Chamber

The chamber is NOT a context dump. It is a pointer surface with disposition:

```yaml
chamber:
  arrows:
    complement:
      pointer: "path/to/complement/SKILL.md"
      tom_briefing: "topological closure — fire when move lands and PR < diff"
      disposition_bias: 0.7  # current session has been heavy implementation
    counter:
      pointer: "path/to/counter/SKILL.md"
      tom_briefing: "adversarial falsification — fire before architecture commits"
      disposition_bias: 0.4
    ingest:
      pointer: "path/to/ingest/SKILL.md"
      tom_briefing: "metabolize — fire when external context enters"
      disposition_bias: 0.2  # context is stable this session
    tom:
      pointer: "path/to/tom/SKILL.md"
      tom_briefing: "centroid-preserving re-expression — fire before publication"
      disposition_bias: 0.3
  posture: "ENG/DIRECT"
  disposition: "implementation-heavy; bias complement+counter; suppress ingest"
  refreshed_at: "session_start"  # or last posture shift
  filled_by: "/tactical-hydration → /consolidate → /tom per arrow"
```

Each arrow gets a /tom-compressed one-liner about what it means RIGHT NOW. The router reads ~200 tokens to know everything. Actual skill content lives at the pointer — pulled only when an arrow fires.

### Quick-Fire Signal Tags

```html
<sidecar key="complement_due" target="pr-description" confidence="0.8" />
<sidecar key="counter_warranted" target="architecture_decision" confidence="0.7" />
<sidecar key="ingest_needed" target="external_api_docs" confidence="0.9" />
```

Hook regex catches `<sidecar ... />`, extracts KV pairs, routes to the named arrow. No API. No persistence. Just text patterns hooks can parse.

### Quiver (Six Governance Arrows + Two Support Arrows)

| Arrow | Stance | Fires | Returns | Council Resonance |
|---|---|---|---|---|
| `/ingest` | metabolize | before context enters | shaped context | #9 #20 #40 |
| `/tom` | centroid-preserving | before expression | re-expressed content | #14 #18 #22 |
| `/complement` | cooperative-topological | after move lands | exposed surfaces | #3 #6 |
| `/counter` | adversarial-falsifying | before move commits | attack arguments | #1 #12 #23 |
| `/citation-intel` | readiness-check | before publication | readiness report | — |
| `/posture` | contract-declaration | on `[Posture →]` toggle | posture contract | — |
| `/tactical-hydration` | discovery | at chamber fill | pointer basket | — |
| `/consolidate` | packaging | at chamber fill | indexed dump | — |

`/tactical-hydration` and `/consolidate` are not user-facing arrows. They fill the chamber. The user interacts with the six governance arrows; the support arrows are infrastructure. Router firing note: `/citation-intel` is intent-matched like the other four; `/posture` is detected as an explicit `[Posture →]` / `POSTURE:` toggle, not yet inferred from a "mutation under META" condition (chamber declares the bias; router implements toggle-detection only).

### Metapairs

The sidecar pairs with existing skill libraries and their orchestrators. It does NOT replace them — it adds the governance shim:

```
existing_skill_stack + sidecar = posture-aware, mode-governed execution
```

The metapair holds inferred invariants about HOW skills are used:
- "When `/code-review` runs in OPS/DIRECT posture, it over-commits; in ENG/META, it under-explores"
- "When the user chains 3+ tool calls without pausing, counter_warranted confidence rises"

No persistence needed for session-scoped behavioral shaping. Persistence is the Ubiquity upgrade lane.

## Upgrade Lane (Sidecar → Ubiquity)

| Sidecar (stateless) | Ubiquity (persistent) | Tinkerer discovers they want... |
|---|---|---|
| Chamber (session-scoped) | Tic-gated conformations | "Why did I lose my posture history?" |
| Disposition (session-scoped) | Harmony manifold | "Why doesn't my quiver remember what worked?" |
| Quick-fire signals (ephemeral) | Signal manifold + warrants | "Why can't I track recurring conditions?" |
| No review pipeline | /review + CogPR queue | "Why can't I promote lessons to doctrine?" |

Each persistence ask maps to exactly one Ubiquity primitive. The sidecar IS the onramp.

## What Belongs Here vs Elsewhere

| Concern | Location |
|---|---|
| Router hook (UserPromptSubmit) | `hooks/sidecar-router.py` |
| Hook registration template | `hooks/settings.json.template` |
| Router spec | `specs/router.md` |
| Chamber schema + fill protocol | `specs/chamber.md` |
| Chamber example | `specs/chamber.yaml.example` |
| Arrow skills (/ingest, /counter, /citation-intel) | `skills/ingest/`, `skills/counter/`, `skills/citation-intel/` |
| Dehydrated /complement | `skills/complement/` |
| Dehydrated /tom | `skills/tom/` |
| Posture/mode shim | `skills/posture/` |
| Support skills (/tactical-hydration, /consolidate) | `skills/tactical-hydration/`, `skills/consolidate/` |
| Quick-fire signal emission | folded into `hooks/sidecar-router.py` (emits `<sidecar/>` tags in `additionalContext`) |
| Metapair registry | `specs/metapairs.md` |
| Council resonance mapping | `references/council-resonance.md` |

## Workspace Default Posture

- **ENG/META** until specs are authored
- **ENG/DIRECT** for skill implementation

## Sibling Position

- **`../context-grapple-gun/`** — CGG is the governance lifecycle for Claude Code. Sidecar is the portable governance shim for ANY agent stack. CGG is the engine; sidecar is the interface layer.
- **`../estate-seed/`** — EstateSeed creates governed estates under federation. Sidecar creates governed sessions without federation. Different rung, different lifecycle.
- **`../sovereign-starter/`** — Sovereign-starter ignites new federations. Sidecar equips existing environments. Different scope entirely.

## Market Position

Carries dual presentation:

- **Sidecar** — the technical lane. A governance shim attached to an existing skill stack. Names the structural relationship (sidecar to a primary vehicle).
- **Hangar for harnesses** — the market-facing lane. Where tinkerers store and maintain their agent rigs. Names the surface the user encounters first.

Same primitive, two registers. The technical lane is what it IS; the market-facing lane is how it PRESENTS. Both are load-bearing — collapsing to one register loses the audience that the other catches.

The hobbyist harness for harnesses. The thing someone installs on Saturday afternoon because they're curious about posture-aware agent work, and by Tuesday they're wondering why their work stack doesn't have it.

Not enterprise SaaS. Not B2B governance infrastructure. The consumer-level lane that catches people on their off time while they tinker with what their employer won't let them use at work.

The deeper primitive is not orchestration. It is expression-governance.
