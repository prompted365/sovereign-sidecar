# Chamber Specification

The chamber is the sidecar's working memory surface — a session-scoped pointer store that the router reads on every user message. It is filled once (at session start or posture shift) by /tactical-hydration → /consolidate → /tom-per-arrow, then read cheaply on every hook fire.

## Design Constraints

1. **Pointers over content.** The chamber holds paths and /tom-compressed briefings, not skill bodies or documentation. The router reads ~200 tokens per chamber consultation.
2. **Disposition over instruction.** The chamber tells the quiver what it's biased toward, not what to do. "Implementation-heavy session; bias complement+counter" — not "run complement on every PR."
3. **Dynamic posture.** The chamber's posture field updates on `[Posture →]` toggle detection. The router's intent assessment is posture-aware — same user message means different things in ENG/DIRECT vs OPS/META.
4. **No persistence.** The chamber dies with the session. Persistence is the Ubiquity upgrade lane — not a sidecar concern.

## Schema

```yaml
# Chamber v0.1 — session-scoped pointer surface
schema_version: "0.1"

posture: "ENG/DIRECT"           # current session posture
disposition: |                   # /tom-compressed session trajectory
  implementation-heavy; bias complement+counter;
  suppress ingest (context stable)

arrows:
  ingest:
    pointer: "skills/ingest/SKILL.md"
    tom_briefing: "metabolize — fire when external context enters the session"
    disposition_bias: 0.2        # 0.0 = suppress, 1.0 = always fire
    fires: "before_context_enters"
    stance: "metabolize"

  tom:
    pointer: "skills/tom/SKILL.md"
    tom_briefing: "centroid-preserving re-expression — fire before publication or audience shift"
    disposition_bias: 0.3
    fires: "before_expression"
    stance: "centroid_preserving"

  complement:
    pointer: "skills/complement/SKILL.md"
    tom_briefing: "topological closure — fire when a move lands and exposed surfaces aren't named"
    disposition_bias: 0.7
    fires: "after_move_lands"
    stance: "cooperative_topological"

  counter:
    pointer: "skills/counter/SKILL.md"
    tom_briefing: "adversarial falsification — fire before committing to an architecture or irreversible decision"
    disposition_bias: 0.4
    fires: "before_move_commits"
    stance: "adversarial_falsifying"

  citation_intel:
    pointer: "skills/citation-intel/SKILL.md"
    tom_briefing: "publication readiness — fire before publishing content to AI-searchable surfaces"
    disposition_bias: 0.1
    fires: "before_publication"
    stance: "readiness_check"

# Support arrows (not user-facing; fill the chamber)
support:
  tactical_hydration:
    pointer: "skills/tactical-hydration/SKILL.md"
    role: "discover pointer targets at session start"
  consolidate:
    pointer: "skills/consolidate/SKILL.md"
    role: "package discovered targets into chamber-consumable form"

refreshed_at: null               # ISO timestamp of last fill
fill_source: null                # "session_start" | "posture_shift" | "manual"
```

## Fill Protocol

1. `/tactical-hydration` runs against the current working directory with `target_profile: mixed`, `fanout_level: conservative`
2. Selected surfaces become chamber pointers
3. `/consolidate` packages the pointer targets (headings-only, not full content)
4. `/tom` compresses each arrow's briefing against the consolidated context: "given what this session is working on, when should this arrow fire?"
5. Router reads the chamber on every `UserPromptSubmit`

## Router Consultation Protocol

The router does NOT re-read skill files on every message. It reads the chamber (~200 tokens), pattern-matches the user message against arrow fire conditions, and emits a quick-fire signal only when confidence exceeds the disposition_bias threshold for that arrow.

```
confidence(complement) = 0.85
disposition_bias(complement) = 0.7
0.85 > 0.7 → FIRE

confidence(counter) = 0.3
disposition_bias(counter) = 0.4
0.3 < 0.4 → SUPPRESS
```

## Disposition Updates

Disposition refreshes on:
- Session start (full chamber fill)
- Posture toggle (`[Posture → X/Y]` detected by the router hook)
- Manual refresh (`/sidecar refresh` if skill is installed)

Disposition does NOT refresh on every message. That would be expensive and noisy.
