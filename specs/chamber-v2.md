# Chamber v2 — The Constitutional Organ (Dynamic, Layered)

> **Status:** Spec authored tic 309/310 under Architect redirect. Supersedes the v0.1 design in `chamber.md`
> (which is retained as the historical baseline). Build is the next phase (spec-first, then kickoff).
>
> **Authority:** Architect redirect — "saving tokens on chamber craft is folly when it's our leverage, since
> persistence isn't holding the constitutional weight and backdrop that harmony disposition triggers, and posture
> and mode is runtime-primary auto-selected. Returning a chamber based solely on [a tag] with static text is a
> wasted opportunity." Chamber-fill mechanism: **layered (structured base + LLM enrich)**. Build after `/cadence`.

---

## 1. Why v0.1 is wrong (the diagnosis)

The v0.1 chamber optimizes the **wrong variable** and was **never fully implemented**:

- **Static, hand-authored.** No fill script exists. `refreshed_at: null`. The seven `disposition_bias` values are
  hand-tuned magic floats. The `disposition` is a one-line authored string. The "fill protocol"
  (`/tactical-hydration → /consolidate → /tom-per-arrow`) is described in `chamber.md` but **was never built**.
- **Token-thrift as a virtue.** v0.1 brags "reads ~200 tokens to know everything." But the measured reality
  (tic-309 freight-train eval) is that the **lane the chamber triggers costs ~2× the turn** — the hook's
  zero-LLM-cost is rounding error. Saving tokens on the *hook* while starving the *chamber* optimizes the one
  variable that doesn't matter.

| arm (freight train) | cost | turns | coverage |
|---|---|---|---|
| control (no sidecar) | $0.26 | 11 | 1/4 |
| full surface | $0.50 | 22 | 3/4 |
| mute-preflight | $0.63 | 34 | 3/4 |
| spec-only (with vs without) | $0.52 vs $0.56 | — | 5/6 vs 5/6 (zero lift) |

- **The constitutional backdrop has nowhere to live.** In **Ubiquity**, the constitutional weight is carried at
  runtime by **harmony disposition** (auto-selected by *conformation proximity* — matching current system shape to
  shape-at-time-of-prior-state), **posture**, and **mode** — all runtime-primary and auto-selected. The **sidecar
  has no persistence**, so that weight has *nowhere to live except the chamber*. A static-text chamber **drops the
  entire constitutional backdrop on the floor** and fakes it with seven floats.

**v2 thesis:** the chamber is not a cheap pointer index to skim — it is the **sidecar's only organ for holding
constitutional state**. It is the *stateless analog of harmony disposition*. Crafting it well is the highest-leverage
spend in the system. Spend tokens *here*.

---

## 2. Architecture — two layers

```
SESSION  ─┬─→  [L1] STRUCTURED BASE  (cheap, always-on, no LLM)
          │       cwd / repo-shape / git-state / file-types / recent-prompt verbs
          │       → posture HINTS + a coarse disposition + a structured stakes signal
          │       (always present; the floor the sidecar never goes blind below)
          │
          └─→  [L2] LLM ENRICH        (triggered, deep — NOT per-prompt)
                  fill pass: tactical-hydration → consolidate → tom-per-arrow
                  → resolves MODE, writes a rich disposition (the constitutional backdrop),
                    per-arrow "what this lane means RIGHT NOW", and DERIVED biases
                  trigger: session-start ∪ posture-shift ∪ stakes-signal-crossed
```

**Honesty about the split (Architect sharpening):** L1 *hints* posture cheaply but **cannot reliably resolve mode**
(ENG/OPS × DIRECT/META). cwd/git/verbs give a posture lean; resolving the working *mode* needs L2. The spec must not
pretend the cheap layer nails mode — L1 hints, L2 resolves. If L2 hasn't run, the chamber carries the L1 hint
explicitly marked as **unresolved** so the router gates conservatively rather than acting on a guess.

### Degradation ladder (fail-soft)
1. **L1 + L2 fresh** → full constitutional backdrop; biases derived; mode resolved.
2. **L1 only (L2 stale/failed/not-yet-run)** → coarse backdrop; mode marked `unresolved`; biases fall back to
   conservative structured defaults. Sidecar is *shallower, not blind*.
3. **No chamber at all** → router fail-soft to current behavior (fire on raw pattern match at a safe default bias).
   v2 must never be *worse* than v1 when its inputs are missing.

---

## 3. What the chamber carries (v2 schema)

```yaml
schema_version: "0.2"

# --- L1: structured base (always present) ---
posture:
  value: "ENG/DIRECT"          # inferred lean OR explicit toggle
  source: "toggle | inferred | default"
  confidence: 0.0..1.0
mode:
  value: "DIRECT"              # DIRECT | META
  source: "resolved | hinted | unresolved"   # L2 resolves; L1 only hints
stakes:
  level: "low | elevated | high"   # structured signal: touching money/migrations/secrets/prod, dirty tree, etc.
  signals: ["dirty:charge.ts", "risky_path:migrations/"]   # the cheap evidence
repo_shape:                     # L1 evidence (cheap, no LLM)
  root: "/path"
  languages: ["ts", "sql"]
  invariant_hotspots: ["ledger_entries", "charges", "refunds"]   # grep-derived co-write surfaces
  git_dirty: true

# --- L2: enriched constitutional backdrop (the stateless cousin of harmony disposition) ---
disposition:                    # NOT a one-liner — the shape of the work + what it's biased toward + WHY
  text: |
    Money-path refactor under crash-atomicity pressure; coupled writers span charge/refund/ledger.
    Bias preflight+complement HARD (blast-radius breadth is the live risk). Counter on irreversible
    schema/txn-boundary calls. Suppress ingest (context stable).
  meaning_state: "preserved | strained | dissonant"   # the sidecar's read of coherence pressure
  derived_at_tic_or_ts: "..."
arrows:
  preflight:
    pointer: "skills/preflight/SKILL.md"
    live_context: "every ledger_entries writer must be enumerated before any charge/refund mutation"
    bias: 0.78                  # DERIVED (see §4), not hand-set
    stance: "pre_mutation_receipt"
  # ... all arrows, each with a live_context written against THIS session's work ...

# --- provenance ---
refreshed_at: "ISO"
fill_source: "session_start | posture_shift | stakes_crossed | manual"
layers_present: ["L1", "L2"]    # so the router knows what it's standing on
muted: []                       # honored by the SIDECAR_MUTE contract (already shipped)
```

---

## 4. Biases are DERIVED, not hand-tuned

Replace the seven magic floats with a derivation from the backdrop:

```
bias(arrow) = f(disposition_lean[arrow], posture, mode, stakes, repo_shape)
```

- **disposition_lean** — L2 names which arrows the work is biased toward (e.g. "bias preflight+complement HARD").
- **posture/mode** — META suppresses mutation-class arrows' *firing* but *raises* counter/complement (analysis lanes);
  DIRECT raises preflight/PreToolUse.
- **stakes** — `high` stakes (money/migration/prod, dirty tree on a risky path) raises preflight + counter bias.
- **repo_shape** — invariant hotspots that the current work touches raise preflight's bias for those surfaces.

L1-only fallback uses conservative structured defaults (documented constants), never the old magic floats.

---

## 5. Trigger discipline (the cost guard — Architect sharpening)

L2 enrich is **not per-prompt**. It fires on:
- **session-start** (first prompt of a session / first hook fire with no fresh chamber),
- **posture-shift** (`[Posture → X/Y]` toggle, or L1 detecting a strong posture-lean change),
- **stakes-crossed** (L1 stakes level rises, e.g. work moves onto a money/migration surface).

Between triggers, the router reads the cached chamber (cheap). This keeps the *expensive* craft rare and the
*always-on* L1 floor cheap. A `refreshed_at` + TTL guards against staleness (per the federation Volatility Handling
Law — internal snapshots carry explicit timestamps/TTLs).

---

## 6. Ubiquity bridge

| Sidecar v2 (stateless) | Ubiquity (persistent) | What the tinkerer discovers they want |
|---|---|---|
| L1 structured base (per-session) | conformation snapshots (tic-gated) | "why does my backdrop reset each session?" |
| L2 disposition (session-scoped, re-derived) | **harmony disposition** (conformation-proximity retrieved, multi-timescale) | "why doesn't my disposition remember what worked under this *shape* before?" |
| posture/mode (inferred per session) | posture/mode runtime-primary, persisted + auto-selected | "why do I re-declare posture every session?" |
| derived bias (from this session) | bias shaped by civilizational memory + decay | "why doesn't my quiver learn across sessions?" |

v2 makes the sidecar chamber the **honest stateless shadow** of harmony disposition — so the upgrade lane to Ubiquity
is "add persistence + conformation-proximity retrieval," not "rebuild the concept." (Ubiquity itself is moving *beyond*
this into deeper context-craft; v2 is the sidecar's reach toward that.)

---

## 7. Eval plan (measure value-per-token, not just lift)

Re-run the freight train (`run_fulldress.py`) against v2 vs the **static-chamber baseline already established**
(control 1/4 @ $0.26; full 3/4 @ $0.50). New arms / metrics:
- **v2-full vs v1-full** — does the richer chamber raise coverage, sharpen firing (fewer false-fires), and/or improve
  **coverage-per-dollar**?
- **L1-only vs L1+L2** — is the LLM enrich worth its cost, or does the structured floor carry most of it? (mirrors the
  mute-ablation finding that the cheap UPS directive already carried the breadth — v2 must beat that bar to justify L2).
- **Report value-per-token explicitly** — coverage / cost_usd per arm. The win condition is not "more lift at any cost";
  it is "more coherence per dollar than v1, *or* equal coherence with sharper/cheaper firing."

---

## 8. Copy rewrite (drop the wrong story)

`sovereign-sidecar` README/marketing currently leads with token-thrift ("zero-LLM-cost", "reads ~200 tokens to know
everything"). Rewrite to lead with the **two true differentiators**:
1. **The refuse-path** — the terminal of a lane isn't "proceed"; it's a coherence read ending in *act or refuse*.
   Tool-chains end at push/mutate; the sidecar ends at *whether the move coheres*. That is the structural difference.
2. **The constitutional backdrop** — the chamber is the stateless organ that holds *what this work is, what mode it's
   in, what's at stake* and shapes the quiver accordingly. The craft of that backdrop is the product, not its thrift.

Remove every claim that frames token-saving as the value.

---

## 9. Open questions / risks (for the build to resolve)

- **L1 mode inference fidelity.** How far can cheap signals push mode before L2 is needed? Build should measure the
  L1 mode-hint accuracy vs L2-resolved mode and tune the `unresolved` gate.
- **L2 fill cost.** What does one enrich pass actually cost, and does the per-session amortization hold? Instrument it.
- **Staleness vs cost.** TTL tuning for `refreshed_at` — too short re-bills L2, too long drifts. Start conservative.
- **Stakes signal precision.** The L1 stakes heuristic reuses the router's `_RISKY_PATH_RE`/`_RISKY_BASH_RE` surface;
  validate it doesn't over-escalate.
- **Backward compat.** v2 must degrade to v1-or-better when L1/L2 absent (§2 ladder). The existing `SIDECAR_MUTE`
  contract and fail-soft guarantee must survive untouched.

---

## 10. Build manifest (what the kickoff swarm produces)

1. `chamber_fill.py` (or hook-integrated) — L1 structured-base inference + L2 enrich fill pass, trigger-gated, writes
   the v0.2 chamber. Fail-soft to the degradation ladder.
2. Router changes — consume the v0.2 chamber: posture/mode/stakes-aware `assess_intent`, derived bias, per-arrow
   `live_context` woven into directives, `layers_present` gating. Preserve `SIDECAR_MUTE` + fail-soft.
3. `chamber.yaml.example` → v0.2; `chamber.md` cross-links here.
4. Freight-train eval extension (§7) — v2 arms + value-per-token reporting.
5. README/marketing copy rewrite (§8).
6. Smoke coverage for L1-only / L1+L2 / no-chamber degradation.
