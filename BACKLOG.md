# Sovereign Sidecar — Backlog

## Ship the posture + mode contract IN the package (not in global CLAUDE.md)

**Status:** noted (tic 306 / 2026-05-29)

**What:** The posture + mode (working-mode) lanes must be shipped as part of the
sidecar package itself. Today the package ships only the *mechanism*:
- `chamber.yaml` → `posture` arrow (fires `before_mutation_under_meta`)
- `skills/posture/SKILL.md` → the contract *centroid*, but not the full contract body
- `hooks/sidecar-router.py` → `detect_posture_toggle` + `posture_shift` tag emission

The actual **contract body** — session-start `POSTURE:` banner convention, the
ENG/OPS × DIRECT/META axis table, hard constraints by posture (META = read-only,
DIRECT = scoped mutation), posture determination priority, live-vs-local data rule,
mid-session toggles, scope-safety — currently lives in **global `~/.claude/CLAUDE.md`**.

**Why it matters (evidence):** In the delegation control experiment (runset
`deleg-20260529T102156`), the *supposedly isolated* arm (`CLAUDE_CONFIG_DIR` repointed
at a clean `.iso-home/.claude`) still emitted a `POSTURE: ENG/META` banner on a 1-turn
"reply READY" preflight call. `CLAUDE_CONFIG_DIR` strips skills/agents/hooks/settings
but does NOT gate the user memory file, which loads from literal `$HOME/.claude/CLAUDE.md`.
So while the posture contract lives in global memory it:
- leaks into every "isolated" run (can't be cleanly toggled per-arm),
- is symmetric-by-luck across arms rather than symmetric-by-construction,
- is not hook-gated like every other governance lane.

(The leak tripped in the trivial preflight but did NOT hold in the real measured
goal runs of R1 — POSTURE was emitted 13× in the with-sidecar arm and 0× in the
without arm, driven by the hook, not by ambient memory. The architectural lesson
stands either way: the contract should be hook-gated, isolable, and shipped with
the package.)

**Fix:** Relocate the full posture/mode contract body out of `~/.claude/CLAUDE.md`
and into the sidecar package (expand `skills/posture/SKILL.md` to carry the contract
body; ship a session-start posture lane so the banner + determination priority fire
through the router). Then global CLAUDE.md only points at the sidecar, and the lane
is isolable + hook-gated like ingest/tom/complement/counter/citation-intel.

**Net:** posture+mode become part of "the package we ship there" — toggleable,
isolable, and symmetric-by-construction.
