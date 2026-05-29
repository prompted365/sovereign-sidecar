#!/usr/bin/env python3
"""
Sovereign Sidecar Router (UserPromptSubmit hook)

Reads the chamber (~/.sidecar/chamber.yaml or $SIDECAR_CHAMBER), pattern-matches
the user message against arrow fire conditions, and — when confidence exceeds the
disposition_bias threshold — injects a READABLE LANE DIRECTIVE that makes the model
run that governance lane inline and return a small, envelope-shaped result.

Why a directive, not a tag: an earlier version emitted a machine KV tag
(<sidecar key="counter_warranted" .../>) and relied on a "downstream hook" to fire
the arrow. That consumer was never universal, and the bare tag is not actionable by
the model — model-visible context must be human-readable text intended for the LLM,
not an inter-extension dict. Injecting the lane protocol directly makes the model
the consumer: no second hook required, and the arrow's actual reasoning lands in the
thread instead of a tag nobody reads.

Discipline:
- Speaks to the model: additionalContext carries a readable directive (the compressed
  lane protocol), with a short human-readable provenance footnote (arrow + confidence).
- Zero LLM cost in the hook: pure pattern matching selects which lane to invite; the
  lane itself runs in the model's normal turn (cost only when warranted).
- Fail-soft: any exception is caught and an empty hook output is emitted so the user
  prompt is never blocked.

Hook contract (Claude Code):
- Receives prompt JSON on stdin: {"prompt": "<user message>", ...}
- Emits hookSpecificOutput.additionalContext containing signal tags
- Sets reloadSkills + sessionTitle for ambient chamber-aware identity
- Never blocks UserPromptSubmit on error

Exit codes:
- 0 always (fail-soft)
"""

import json
import os
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Chamber loading
# ----------------------------------------------------------------------

CHAMBER_ENV = "SIDECAR_CHAMBER"
DEFAULT_CHAMBER_PATHS = [
    "~/.sidecar/chamber.yaml",
    "~/.claude/sidecar/chamber.yaml",
    ".sidecar/chamber.yaml",
]

# Outpost boundary. The sidecar is the governance shim for NON-Ubiquity
# environments. When the real federation is present (a .ticzone or rung-root
# marker up the cwd tree), the sidecar defers and stays silent — it has
# arrived at the thing it was an onramp toward. This is the "outpost": a
# domain-level hook that stops at the zone root. The same primitive scopes a
# resident outpost (e.g. homeskillet-gk) to a domain boundary.
# Override with SIDECAR_IGNORE_ZONE=1 (testing / debug / forced fire).
ZONE_MARKERS = (".ticzone", ".federation-root", ".estate-root", ".domain-root", ".site-root")
ZONE_IGNORE_ENV = "SIDECAR_IGNORE_ZONE"


def find_chamber_path():
    """Locate the chamber file. Returns Path or None."""
    env_path = os.environ.get(CHAMBER_ENV)
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_file():
            return p
    for candidate in DEFAULT_CHAMBER_PATHS:
        p = Path(candidate).expanduser()
        if p.is_file():
            return p
    return None


def load_chamber(path):
    """Load chamber YAML. Returns dict or None on failure.

    Uses PyYAML if available; otherwise falls back to a minimal subset parser
    sufficient for chamber's flat key:value + nested arrows structure. The
    fallback is intentionally permissive — chamber authoring is the user's
    discipline, not the router's enforcement layer.
    """
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
    except ImportError:
        return _minimal_yaml_parse(path)
    except Exception:
        return None


def _minimal_yaml_parse(path):
    """Minimal YAML subset parser for chamber files."""
    try:
        with open(path) as f:
            lines = f.readlines()
    except Exception:
        return None

    result = {"arrows": {}, "support": {}}
    current_section = None
    current_arrow = None
    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if indent == 0 and ":" in line:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key in ("arrows", "support"):
                current_section = key
                current_arrow = None
            elif current_section is None:
                result[key] = val if val else None
        elif indent == 2 and stripped.endswith(":") and current_section in ("arrows", "support"):
            current_arrow = stripped[:-1]
            result[current_section][current_arrow] = {}
        elif indent >= 4 and ":" in line and current_arrow:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            try:
                val_parsed = float(val) if "." in val else int(val)
            except ValueError:
                val_parsed = val
            result[current_section][current_arrow][key] = val_parsed
    return result


# ----------------------------------------------------------------------
# Intent assessment
# ----------------------------------------------------------------------

# Pattern table. Each entry: (arrow_name, trigger_verb, patterns, base_confidence)
# Patterns are case-insensitive regex strings.
PATTERN_TABLE = [
    # /ingest — external context entering
    ("ingest", "needed", [
        r"https?://",                      # URL paste
        r"\bpasted\b",                     # explicit paste mention
        r"\bfrom (their|the) docs\b",      # external docs reference
        r"\blook at (this|these)\b",       # paste/handoff
        r"\bAPI docs\b",
        r"\bchangelog\b",
        r"\b(competitor|external) (analysis|pattern)\b",
    ], 0.75),

    # /complement — move landed
    ("complement", "due", [
        r"\b(done|shipped|merged|landed)\b",
        r"\bcommit(ted)?\b",
        r"\bPR (description|summary)\b",
        r"\b(this|that) (looks|seems) (done|complete)\b",
        r"\bwhat (did|are) (we|i) miss(ing)?\b",
        r"\banything else\b",
    ], 0.80),

    # /counter — irreversible decision pending
    ("counter", "warranted", [
        r"\bshould we\b",
        r"\b(architecture|schema|API) (decision|change|contract)\b",
        r"\b(commit to|lock in|finalize)\b",
        r"\bbefore we (deploy|publish|push to prod)\b",
        r"\bany reason not to\b",
        r"\bis this the right (approach|architecture|design)\b",
    ], 0.75),

    # /tom — audience shift / publication
    ("tom", "due", [
        r"\bfor the (board|exec|leadership|team)\b",
        r"\bexplain (this )?to\b",
        r"\b(compress|rewrite|reframe) (this |it )?for\b",
        r"\b(tom this|run tom)\b",
        r"\b(audience|register) shift\b",
    ], 0.85),

    # /citation-intel — publication readiness
    ("citation_intel", "due", [
        r"\b(publish|deploy|push to prod)\b",
        r"\bmake (this )?public\b",
        r"\bis (this|it) citation[- ]ready\b",
        r"\b(citation|SEO|AI search) (check|optimize|audit)\b",
        r"\b(robots\.txt|llms\.txt)\b",
        r"\bAI access stack\b",
    ], 0.80),

    # /delegate — orchestrator about to fan a goal out to subagents (the meta lane).
    # This is the orchestrator-as-delegator trigger: govern the swarm/tranche spec
    # (brief coherence, fan-out completeness, slicing stress-test, posture) BEFORE dispatch.
    ("delegate", "warranted", [
        r"\bdelegat",
        r"\bsub-?agents?\b",
        r"\bfan(?:ning)?[ -]out\b",
        r"\bspawn\b",
        r"\bbreak (this|it|the \w+) (down |up )?into\b",
        r"\borchestrat",
        r"\bparalleli[sz]e\b",
        r"\btranche",
        r"\bswarm\b",
        r"\baudit .* across\b",
        r"\b(decompos|divid)\w* (this|the|it|into)\b",
    ], 0.80),
]

# Posture toggle pattern (special — refreshes chamber disposition, not an arrow)
POSTURE_TOGGLE_PATTERN = re.compile(
    r"\[Posture\s*[→>=]\s*([A-Z]+)/([A-Z]+)\]|POSTURE:\s*([A-Z]+)/([A-Z]+)",
    re.IGNORECASE,
)


def assess_intent(prompt, chamber):
    """Return list of (arrow_key, trigger_verb, target, confidence, chamber_bias)
    tuples for arrows whose pattern-match confidence exceeds their chamber
    disposition_bias.

    confidence is base_confidence × match_density (capped at 1.0).
    target is derived from the strongest matching pattern's named group or
    the matched substring; falls back to "active_move" if undeterminable.
    """
    if not chamber:
        return []

    arrows = chamber.get("arrows", {}) or {}
    fires = []

    for arrow_key, trigger_verb, patterns, base_confidence in PATTERN_TABLE:
        # Map snake_case arrow_key to chamber key (citation_intel → citation_intel)
        chamber_arrow = arrows.get(arrow_key, {})
        bias_raw = chamber_arrow.get("disposition_bias", 0.5)
        try:
            bias = float(bias_raw)
        except (TypeError, ValueError):
            bias = 0.5

        match_count = 0
        first_match_target = None
        for pat in patterns:
            try:
                m = re.search(pat, prompt, re.IGNORECASE)
            except re.error:
                continue
            if m:
                match_count += 1
                if first_match_target is None:
                    first_match_target = m.group(0)[:40]

        if match_count == 0:
            continue

        # Confidence: base × density factor (1.0 for 1 match, 1.15 for 2, 1.3 for 3+)
        density_factor = {0: 0.0, 1: 1.0, 2: 1.15}.get(match_count, 1.3)
        confidence = min(1.0, base_confidence * density_factor)

        if confidence > bias:
            target = _derive_target(arrow_key, first_match_target or "active_move")
            fires.append((arrow_key, trigger_verb, target, confidence, bias))

    return fires


def _derive_target(arrow_key, raw_target):
    """Project the matched substring into a stable target slug for the signal tag."""
    target_map = {
        "ingest": "external_context",
        "complement": "active_move",
        "counter": "pending_decision",
        "tom": "audience_shift",
        "citation_intel": "publication",
        "delegate": "delegation_plan",
    }
    return target_map.get(arrow_key, "active_move")


def detect_posture_toggle(prompt):
    """Return (domain, depth) tuple if a posture toggle is in the prompt, else None."""
    m = POSTURE_TOGGLE_PATTERN.search(prompt)
    if not m:
        return None
    domain = m.group(1) or m.group(3)
    depth = m.group(2) or m.group(4)
    if not (domain and depth):
        return None
    return (domain.upper(), depth.upper())


# ----------------------------------------------------------------------
# Lane directives — the router SPEAKS the lane protocol
# ----------------------------------------------------------------------
#
# Each directive is a compressed form of the arrow's SKILL.md protocol. The
# router injects the matching directive so the model runs that lane inline,
# instead of emitting a KV tag and hoping a (never-universal) downstream hook
# fires the arrow. The directive IS the consumer-activation surface.

LANE_DIRECTIVES = {
    "ingest": (
        "External context is entering. Run the INGEST lane before you absorb it:\n"
        "  1. Identify the structural pattern the source carries.\n"
        "  2. Map it to our existing vocabulary, or name it cleanly.\n"
        "  3. Declare an adoption stance: ADOPT / WRAP / WATCH / NO-OP.\n"
        "  4. Note what you keep vs. strip, and why.\n"
        "  Test: can you explain it WITHOUT the source's own words? If not, you cargo-culted "
        "— re-metabolize before using it."
    ),
    "complement": (
        "A move just landed. Run the COMPLEMENT lane inline:\n"
        "  - Name the centroid (governing concern) and the active ray (what you just did).\n"
        "  - Surface the single strongest MISSING complement — but only if it changes "
        "implementation, governance, proof burden, a boundary, or what must happen next.\n"
        "  - If nothing structural is missing, say \"current focus is sufficient\" and stop. "
        "Do not invent decorative additions. Return a finding, not an essay."
    ),
    "counter": (
        "An irreversible / hard-to-reverse decision looks imminent. Run the COUNTER lane inline "
        "— you are the genuine adversary, not a devil's advocate:\n"
        "  1. State the move in one sentence.\n"
        "  2. Name the single premise that, if false, makes the whole move wrong.\n"
        "  3. Build the strongest case it WILL fail (not \"might\") — cite evidence, or mark "
        "\"structural, no current evidence.\"\n"
        "  4. Verdict: HOLD / REVISE / PROCEED-WITH-AWARENESS. Do not soften the argument to stay agreeable."
    ),
    "tom": (
        "An audience / expression shift is in play. Run the TOM lane:\n"
        "  - Extract the centroid (invariant meaning) of the source.\n"
        "  - Re-express it for the target audience WITHOUT softening warnings, leaking "
        "internal-only detail, inventing capabilities, or promoting adjacent work to launch-scope.\n"
        "  - The posture serves the centroid, not the other way around."
    ),
    "citation_intel": (
        "Publication looks imminent. Run the CITATION-INTEL readiness check before you publish:\n"
        "  - Is the content extractable / citation-ready for AI-search surfaces? (clear claims, "
        "named sources, clean structure, llms.txt / robots posture)\n"
        "  - Return a short readiness report; flag anything to fix before going public."
    ),
    "delegate": (
        "You're about to fan this goal out to subagents — govern the dispatch as a coherent "
        "swarm/tranche spec, not an ad-hoc spray:\n"
        "  - tom each brief: every subagent brief must preserve the goal's centroid — no drift, "
        "no softened constraint, no invented scope; state what each subagent must NOT do. "
        "Emit each brief as ITS OWN block under a named heading (SA-N / A-N / T-N / Agent-N — "
        "your choice of label — but DISCRETE per-agent blocks, NOT a single table row per agent.)\n"
        "  - counter the slicing: attack your own decomposition — is this the right cut? what does "
        "this fan-out structurally get WRONG or leave uncovered? Emit a section titled literally "
        "**Decomposition Stress Test** that names 3+ structural failure modes of THIS slice "
        "(seam gaps between agents, blind spots a peer agent's scope would swallow, where the cut "
        "leaks at runtime). Out-of-scope honesty is NOT stress-testing. Boundary hygiene is NOT "
        "stress-testing. Name what the chosen slice GETS WRONG, not what it correctly excludes.\n"
        "  - complement the fan-out: is the set complete — any load-bearing lane/subagent MISSING? "
        "(and resist over-spawning decorative agents).\n"
        "  - point, don't inscribe: each brief POINTS its subagent at the right surfaces/sources to "
        "hydrate from — don't inline or dump content into the brief; keep briefs lean.\n"
        "  - sequence + parallelize: make dependencies explicit; run independent briefs in PARALLEL, "
        "serialize only true dependencies — state the dependency graph and where parallelism wins.\n"
        "  - posture + ingest: give each subagent a DIRECT vs META scope so none overreach, and "
        "metabolize shared context before handing it down (don't paste raw).\n"
        "  Emit the dispatch as an explicit spec before spawning anything."
    ),
}


def build_lane_directive(arrow_key, trigger_verb, confidence, bias):
    """Build a readable lane directive. Returns str, or None for unknown arrows.

    The trailing provenance line stays human-readable but keeps the
    `<arrow>_<verb>` token so a downstream tool (or a smoke test) can still
    detect which lane fired without parsing a machine-only dict.
    """
    body = LANE_DIRECTIVES.get(arrow_key)
    if not body:
        return None
    label = arrow_key.replace("_", "-")
    return (
        f"[sidecar · {label}] {body}\n"
        f"  (arrow: {arrow_key}_{trigger_verb} · confidence {confidence:.2f} "
        f"· chamber_bias {bias:.2f})"
    )


def build_posture_directive(domain, depth):
    return (
        f"[sidecar · posture] Posture shift to {domain}/{depth} detected — re-declare the "
        f"working-mode contract:\n"
        f"  - META = read-only: no file edits, no commits, no API writes. If a step would mutate "
        f"state, pause and ask.\n"
        f"  - DIRECT = mutate only the scoped surface, then run the relevant validation before "
        f"claiming done.\n"
        f"  (arrow: posture_shift · target {domain}/{depth})"
    )


# ----------------------------------------------------------------------
# Outpost boundary — defer to the real federation when present
# ----------------------------------------------------------------------

def in_governed_zone(start=None):
    """True if cwd (or `start`) sits within a CGG/Ubiquity-governed zone.

    Walks from cwd up to filesystem root looking for any ZONE_MARKERS. If the
    real federation is present, the sidecar stays silent and defers to it —
    the outpost that stops at the zone root. Honors SIDECAR_IGNORE_ZONE for
    testing. Fail-soft: any error returns False (sidecar fires rather than
    silently breaking).
    """
    if os.environ.get(ZONE_IGNORE_ENV):
        return False
    try:
        p = Path(start).expanduser().resolve() if start else Path.cwd()
    except Exception:
        return False
    for d in (p, *p.parents):
        for marker in ZONE_MARKERS:
            try:
                if (d / marker).exists():
                    return True
            except Exception:
                continue
    return False


# ----------------------------------------------------------------------
# Hook entry point
# ----------------------------------------------------------------------

def main():
    # Fail-soft: any failure emits empty hook output (does not block prompt).
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return  # no input, no output
        payload = json.loads(raw)
        prompt = payload.get("prompt", "") or payload.get("user_prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            return

        # Outpost boundary: defer to the real federation when present.
        if in_governed_zone():
            return

        chamber_path = find_chamber_path()
        chamber = load_chamber(chamber_path) if chamber_path else None

        directives = []

        # Posture toggle takes precedence — re-declare the working-mode contract.
        posture = detect_posture_toggle(prompt)
        if posture:
            directives.append(build_posture_directive(*posture))

        # Arrow firing: each warranted arrow injects its lane protocol as a directive.
        if chamber:
            fires = assess_intent(prompt, chamber)
            for arrow_key, trigger_verb, target, confidence, bias in fires:
                directives.append(build_lane_directive(arrow_key, trigger_verb, confidence, bias))

        directives = [d for d in directives if d]
        if not directives:
            return

        # Emit. The directives ride inside additionalContext as readable instructions
        # the model acts on directly — it runs each lane inline before its main reply.
        plural = "lane" if len(directives) == 1 else "lanes"
        header = (
            f"[Sovereign Sidecar] Your message activated {len(directives)} governance "
            f"{plural}. Run each inline before your main response, then continue:"
        )
        additional_context = header + "\n\n" + "\n\n".join(directives)
        hook_output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": additional_context,
            }
        }
        sys.stdout.write(json.dumps(hook_output))
    except Exception:
        # Fail-soft. No output, no block.
        return


if __name__ == "__main__":
    main()
