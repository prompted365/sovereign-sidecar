# Metapairs Specification

A metapair is the sidecar's pairing primitive — a declared bond between an existing skill (or orchestrator) and a sidecar arrow that carries an inferred invariant about HOW that skill is used in the operator's environment. The metapair is the surface where existing tooling earns a governance shim without surrendering its own behavior.

```
existing_skill_stack + sidecar = posture-aware, mode-governed execution
```

The sidecar does NOT replace the skill stack it pairs with. The skill stack keeps doing what it does. The metapair adds a posture-aware, disposition-biased arrow that fires alongside the skill at the moments where the skill's default behavior is known to drift.

## What a Metapair Is

A metapair is a `(skill_or_orchestrator, sidecar_arrow)` tuple carrying:

- **A target** — the skill or orchestrator the pair is bonded to (path, slash-name, or harness identifier)
- **A paired arrow** — which sidecar arrow shadows the target
- **An inferred invariant** — what the operator has observed about HOW the target tends to behave (over-commits in DIRECT, under-explores in META, etc.)
- **A fire trigger** — the condition under which the metapair activates the paired arrow
- **An evidence count and confidence** — the substrate that makes the invariant load-bearing rather than speculative

Metapairs are declarations. They are not learning loops. The router consults them; it does not author them.

## Schema

```yaml
# Metapair v0.1 — paired-arrow declaration
schema_version: "0.1"

metapair:
  id: "code_review_overcommits_in_ops_direct"

  target_skill: "/code-review"          # path, slash-name, or identifier
  target_orchestrator: "claude-code"    # claude-code | cursor | grok | generic
  paired_arrow: "counter"               # ingest | tom | complement | counter | citation-intel | posture

  inferred_invariant: |
    /code-review in OPS/DIRECT posture lands recommendations as commits faster
    than the operator can sanity-check; counter-arrow shadow forces an
    adversarial pass before the commit lands.

  evidence_count: 3                     # observed occurrences (n=K)
  confidence: 0.75                      # 0.0-1.0; rises with evidence_count

  fire_trigger:
    posture_match: "OPS/DIRECT"         # optional; null = any posture
    target_invocation: true             # fires when the target skill is invoked
    additional_signals: []              # optional extra keyword/regex hooks

  composes_with: []                     # other metapair ids this composes with
  suppresses: []                        # metapair ids this overrides
```

Multiple metapairs may share a target. A target with several paired arrows fires the highest-confidence pair whose `fire_trigger` matches, unless explicit `composes_with` declares otherwise.

## Examples

### Example 1 — /code-review in OPS/DIRECT over-commits

```yaml
metapair:
  id: "code_review_overcommits_in_ops_direct"
  target_skill: "/code-review"
  target_orchestrator: "claude-code"
  paired_arrow: "counter"
  inferred_invariant: |
    /code-review in OPS/DIRECT lands recommendations as commits faster than
    they can be sanity-checked. Counter-arrow shadow forces an adversarial
    pass before the commit lands.
  evidence_count: 3
  confidence: 0.75
  fire_trigger:
    posture_match: "OPS/DIRECT"
    target_invocation: true
```

### Example 2 — 3+ tool calls without pause raises counter_warranted

```yaml
metapair:
  id: "unpaused_tool_chain_raises_counter"
  target_orchestrator: "claude-code"
  target_skill: null                    # orchestrator-level pair, not skill-bound
  paired_arrow: "counter"
  inferred_invariant: |
    When the orchestrator chains 3+ tool calls without a pause for operator
    inspection, irreversible-decision risk rises. Counter-arrow shadow
    surfaces "what's the strongest case against the current trajectory"
    before the chain extends further.
  evidence_count: 4
  confidence: 0.80
  fire_trigger:
    posture_match: null                 # any posture
    target_invocation: false
    additional_signals:
      - "tool_call_count >= 3 without operator turn"
```

### Example 3 — /init in ENG/META under-explores existing structure

```yaml
metapair:
  id: "init_under_explores_in_eng_meta"
  target_skill: "/init"
  target_orchestrator: "claude-code"
  paired_arrow: "ingest"
  inferred_invariant: |
    /init in ENG/META tends to scaffold against assumed structure rather than
    observed structure. Ingest-arrow shadow forces metabolization of the
    actual repository shape before the scaffold lands.
  evidence_count: 2
  confidence: 0.60
  fire_trigger:
    posture_match: "ENG/META"
    target_invocation: true
```

## Inference Protocol

Metapairs are minted through a four-stage lifecycle. The sidecar may suggest candidates from session reflection; the operator authorizes.

| Stage | Trigger | Action |
|---|---|---|
| **observe** | n=1 occurrence | operator (or sidecar suggestion) notes the pattern; no metapair yet |
| **hypothesize** | n=1 with operator intent to track | draft metapair authored with `confidence: 0.3-0.5`, marked unconfirmed |
| **confirm** | n=2 | metapair promoted to confirmed; `confidence: 0.5-0.7` |
| **inscribe** | n=3 | metapair becomes load-bearing in the registry; `confidence: 0.7+`; fires on every matching trigger |

The router does NOT auto-mint metapairs from session telemetry. Metapairs are operator-curated. The sidecar may emit a quick-fire signal of the form `<sidecar key="metapair_candidate" target="<observed_pattern>" />` when it detects a recurring shape, but inscription requires explicit operator action.

This boundary is deliberate. Auto-inference of behavioral rules collapses the metapair into a learning loop, which would require persistence, which is the Ubiquity upgrade lane.

## Registry

Metapairs live at `~/.sidecar/metapairs.yaml` — a single declaration file the operator curates. The registry is read by the router at chamber fill time and composed into the chamber's disposition layer:

```yaml
# ~/.sidecar/metapairs.yaml
schema_version: "0.1"

metapairs:
  - id: "code_review_overcommits_in_ops_direct"
    # ... (full metapair declaration)
  - id: "unpaused_tool_chain_raises_counter"
    # ... (full metapair declaration)
  - id: "init_under_explores_in_eng_meta"
    # ... (full metapair declaration)
```

### Composition with the Chamber

The chamber holds the *current session's* disposition. The registry holds the *operator's accumulated* invariants. At chamber fill time the router walks the registry and, for each metapair whose `fire_trigger.posture_match` matches the chamber's current posture, raises the paired arrow's `disposition_bias` by `confidence × 0.2` (capped at 1.0).

A confirmed metapair tilts the quiver. An inscribed metapair tilts it harder. An unconfirmed candidate does not tilt at all.

### Fire Sequence

1. User message arrives
2. Router reads chamber + walks registry
3. For each metapair with `target_invocation: true`, router watches for the target skill being invoked in the message or in pending tool calls
4. For each metapair with `additional_signals`, router runs the signal regex against the message
5. When a metapair's `fire_trigger` matches AND the paired arrow's adjusted `disposition_bias` exceeds threshold, router emits a quick-fire signal
6. The arrow fires alongside (not instead of) the target skill

The target skill continues to do what it does. The arrow shadows it.

## What Metapairs Are NOT

- **NOT auto-inferred behavioral rules.** The operator curates. The sidecar may suggest, but inscription is manual. Auto-inference is the Ubiquity upgrade lane.
- **NOT permission overrides.** Posture handles permissioning (META = read-only, DIRECT = scoped mutation). Metapairs do not loosen or tighten permissions; they fire arrows.
- **NOT skill replacements.** A metapair is additive. The target skill keeps doing its job. The arrow shadows alongside.
- **NOT persistent across sessions by default.** The registry file `~/.sidecar/metapairs.yaml` persists at the filesystem level, but the sidecar's internal model is session-scoped. The registry is a declaration the operator maintains; the sidecar does not write to it during a session.
- **NOT a learning loop.** The sidecar does not gradient-descend toward better metapairs. Each metapair is a discrete declaration with a discrete lifecycle.
- **NOT cross-operator.** A metapair encodes one operator's observations of one stack. It does not generalize. Generalization is the Ubiquity upgrade lane.

## Upgrade Lane to Ubiquity

When a metapair shows cross-session recurrence — the same pattern firing across multiple stacks, multiple operators, or multiple harnesses — it becomes a candidate for promotion to the Ubiquity federation's pattern manifold. At that point the metapair stops being a private declaration and becomes a doctrine candidate: the inferred invariant earns review against the federation's accreted patterns, and (if promoted) becomes a primitive available to every sidecar instance. The sidecar's registry stays local; the manifold absorbs only what crosses the recurrence threshold. The metapair is the seed; the manifold is the orchard.
