# Sovereign Sidecar — Backlog

## Posture contract lifecycle (hook-gated, isolable)

**Status:** body shipped (tic 308 / 2026-05-29) — remaining work: lifecycle

**What shipped:** The posture + mode contract body now lives in the package
(`skills/posture/SKILL.md`). The session-start `POSTURE:` banner convention, the
ENG/OPS × DIRECT/META axis table, hard constraints by posture (META = read-only,
DIRECT = scoped mutation), posture determination priority, live-vs-local data rule,
mid-session toggles, and scope-safety are all in the package, not only in global
`~/.claude/CLAUDE.md`.

**Remaining work — hook-gated posture LIFECYCLE:**
- **Session-start emission** — router fires the posture banner automatically on
  session open (currently requires explicit `POSTURE:` declaration or inference)
- **Persistence-within-session** — posture state survives across turns without
  re-declaration (chamber holds it; router must read and carry it)
- **Posture-derived trigger weighting** — arrow `disposition_bias` adjusted by active
  posture (same message means different things in ENG/DIRECT vs OPS/META; weighting
  should follow posture, not be static)
- **Pre-mutation enforcement under META** — router detects mutation-class intent and
  surfaces the META = read-only constraint before the turn executes, not after
- **Chamber refresh on posture shift** — `[Posture → X/Y]` toggle triggers full
  disposition recalculation (currently detected but chamber refresh is manual)

**Why lifecycle matters:** body-in-package is necessary but not sufficient. The
architectural win — posture that is hook-gated, isolable, and symmetric-by-construction
across control arms — requires the lifecycle wiring above.
