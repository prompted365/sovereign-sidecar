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
        # "should we" narrowed to CONSEQUENTIAL verbs (tic 308) — bare "should we rename this
        # var" no longer fires the full adversarial lane; the recalibrated gate also requires
        # corroboration for a single weak match.
        r"\bshould we (really |actually )?(commit|lock|finalize|merge|ship|deploy|adopt|migrate|standardi[sz]e|drop|delete|rewrite|switch to|go with)\b",
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
        r"\borchestrat",
        r"\bparalleli[sz]e\b",
        r"\btranche",
        r"\bswarm\b",
        # NOTE (tic 308): bare decomposition verbs ("break X into", "audit .* across",
        # "decompose this") were REMOVED — they over-fired the full swarm directive on
        # ordinary refactors ("break this function into smaller helpers"). delegate now
        # requires genuine fan-out / agent vocabulary; a real delegation prompt carries it
        # alongside any decomposition verb, so legit cases still fire (multi-match).
    ], 0.80),

    # /preflight — operator MOMENTUM implying imminent mutation (the repo-native pre-mutation
    # gate). This is the high-value moment the governance-literate arrows miss: the user says
    # "go / ship it / make it happen / patch this" with NO governance language. UserPromptSubmit
    # only sees the prompt (not tool/repo state), so this is the momentum heuristic; the PRECISE
    # gate lives in the PreToolUse handler (which sees the actual file/bash intent). The runtime
    # receipt makes any false-fire cheap to reject rather than silent noise.
    ("preflight", "warranted", [
        r"\bmake it happen\b",
        r"\blet'?s (go|do (this|it)|ship)\b",
        r"\bgo ahead\b",
        r"\bship it\b",
        r"\bsend it\b",
        r"\b(patch|fix|wire up|implement|build|run|clean up) (this|it|the \w+)\b",
        r"\brefactor\b",
        r"\bget (this|it|the repo) (ready|launch[- ]?ready|production[- ]?ready)\b",
        r"\b(deploy|merge|push) (this|it|the \w+|to)\b",
        r"\brun (the )?(migration|deploy|release|build)\b",
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

        # Confidence: base × density factor. Single-match sits MID-BAND (~0.5) so a chamber
        # disposition_bias in the 0.4–0.7 range ACTUALLY gates firing; additional matches climb
        # toward the base ceiling. Pre-tic-308 this was {1:1.0, 2:1.15, 3+:1.3}, which put
        # single-match confidence AT base (0.75–0.85) — above every sane bias — so the bias knob
        # gated nothing and every arrow fired on a single pattern match (verified inert tic 308).
        # Recalibrated per entourage brief: one weak signal is no longer enough; corroboration is.
        density_factor = {0: 0.0, 1: 0.65, 2: 0.85}.get(match_count, 1.0)
        confidence = min(1.0, base_confidence * density_factor)

        if confidence > bias:
            target = _derive_target(arrow_key, first_match_target or "active_move")
            # Carry the raw matched substring for the runtime receipt — it is the "why it
            # fired" the user sees, turning a false-fire from silent noise into a rejectable
            # signal (entourage brief #2).
            fires.append((arrow_key, trigger_verb, target, confidence, bias,
                          first_match_target or ""))

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
        "  - verify, don't trust 'done': bounded subagents return \"done\" for work that silently "
        "failed — their scoped context can't see the cross-cutting inconsistency a peer would catch. "
        "The synthesis contract must state how the parent INDEPENDENTLY verifies each subagent's "
        "result (against sibling output, source data, or a counter-check); a \"done\" report is "
        "necessary, NOT sufficient.\n"
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
    "preflight": (
        "Operator momentum detected — a mutation may be imminent. Run the PREFLIGHT lane "
        "BEFORE you touch the repo. Produce a mutation receipt:\n"
        "  - intended action (one line)\n"
        "  - target files / surfaces\n"
        "  - repo evidence actually inspected (read it — don't assume)\n"
        "  - invariant at risk (what must stay true through the change)\n"
        "  - validation command (how you'll prove the change is safe)\n"
        "  - rollback path (how to undo)\n"
        "  - verdict: PROCEED / HOLD / ASK\n"
        "  HOLD if blast radius is unnamed; ASK if an invariant is unclear; PROCEED only when "
        "all six lines are real, not placeholders. If nothing is actually about to mutate, say "
        "\"no mutation pending\" and stop — don't manufacture ceremony."
    ),
}


def build_lane_directive(arrow_key, trigger_verb, confidence, bias, matched=""):
    """Build a readable lane directive. Returns str, or None for unknown arrows.

    The trailing RECEIPT line stays human-readable but keeps the `<arrow>_<verb>`
    token so a downstream tool (or a smoke test) can still detect which lane fired
    without parsing a machine-only dict. It also names the matched trigger substring
    — the "why it fired" — so the user can reject a mis-fire at a glance instead of
    learning to skim past silent noise (entourage brief #2).
    """
    body = LANE_DIRECTIVES.get(arrow_key)
    if not body:
        return None
    label = arrow_key.replace("_", "-")
    why = f' · matched "{matched}"' if matched else ""
    return (
        f"[sidecar · {label}] {body}\n"
        f"  (arrow: {arrow_key}_{trigger_verb}{why} · confidence {confidence:.2f} "
        f"> chamber_bias {bias:.2f})"
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
# Repo-state hooks (PreToolUse / PostToolUse / SubagentStop) — conservative, advisory
# ----------------------------------------------------------------------
#
# The UserPromptSubmit lane reads only the prompt. The repo-native obstacle-avoidance the
# product promises lives HERE: catch dangerous tool intent BEFORE mutation, digest evidence
# AFTER, and verify done-claims at subagent stop. v1 is ADVISORY — it injects receipts into
# additionalContext; it does NOT hard-block. The {"decision":"block"} capability is confirmed
# available in Claude Code 2.1.157 and is reserved for a measured later gate (block-class
# behavior is its own /review decision). Fail-soft throughout: any error → no output, never
# blocks the tool call. These handlers are the runtime half of "rails on gates."

_RISKY_PATH_RE = re.compile(
    r"(migrations?/|/ledger|/charge|/refund|/payment|/webhook|"
    r"\.env\b|secrets?|credential|package\.json|package-lock|yarn\.lock|"
    r"Dockerfile|docker-compose|/deploy|/prod|\.github/workflows/)",
    re.IGNORECASE,
)
_RISKY_BASH_RE = re.compile(
    r"\b(git\s+(push|reset\s+--hard|clean\s+-[a-z]*f|rebase)|rm\s+-rf|"
    r"npm\s+publish|migrate|alembic|prisma\s+migrate|drop\s+table|truncate\b|"
    r"deploy|terraform\s+apply|kubectl\s+apply)\b",
    re.IGNORECASE,
)


def _risk_surface(tool_name, tool_input):
    """Return a short list of human-readable risk tags for a tool call, or [] if low-risk."""
    tags = []
    ti = tool_input if isinstance(tool_input, dict) else {}
    if tool_name in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        path = str(ti.get("file_path") or ti.get("notebook_path") or "")
        if _RISKY_PATH_RE.search(path):
            tags.append(f"writes {os.path.basename(path) or 'a sensitive surface'}")
    elif tool_name == "Bash":
        cmd = str(ti.get("command") or "")
        if _RISKY_BASH_RE.search(cmd):
            tags.append("a destructive / deploy / migration / push command")
    return tags


def _hook_context(event_name, text):
    return {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": text}}


def handle_pretooluse(payload):
    """Advisory pre-mutation receipt when a tool call touches a risky surface."""
    tool_name = payload.get("tool_name", "")
    surface = _risk_surface(tool_name, payload.get("tool_input", {}))
    if not surface:
        return None
    receipt = (
        f"[sidecar · preflight] About to {tool_name} — risk surface: {', '.join(surface)}.\n"
        "Before this mutation lands, name (one line each): the invariant at risk, the validation "
        "command that proves it's safe, and the rollback path. If the blast radius isn't named, "
        "HOLD and inspect the adjacent surfaces first — a peer file may share the invariant you're "
        "about to touch.\n"
        f"  (arrow: preflight_pre_mutation · tool {tool_name})"
    )
    return _hook_context("PreToolUse", receipt)


def handle_posttooluse(payload):
    """Advisory evidence-digestion nudge after a risky mutation succeeds."""
    tool_name = payload.get("tool_name", "")
    surface = _risk_surface(tool_name, payload.get("tool_input", {}))
    if not surface:
        return None
    nudge = (
        f"[sidecar · post-tool] {tool_name} touched {', '.join(surface)}. Before moving on: did "
        "you run the validation for it, and check whether an adjacent file imports the same "
        "invariant? Name the next required check, or state why none is needed.\n"
        f"  (arrow: preflight_post_tool · tool {tool_name})"
    )
    return _hook_context("PostToolUse", nudge)


def handle_stop(payload, event_name):
    """SubagentStop → verify-don't-trust-done advisory (a subagent just reported done). Plain
    Stop is a v1 no-op: a real done-claim verifier needs transcript inspection (owed as a
    follow-up gate); the block capability is confirmed available for that future surface."""
    if event_name != "SubagentStop":
        return None
    advisory = (
        "[sidecar · verify] A subagent reported done. Its scoped context cannot see the "
        "cross-cutting inconsistency a peer would catch — independently verify its result "
        "(against sibling output, source data, or a counter-check) before you trust it. A "
        "\"done\" report is necessary, NOT sufficient.\n"
        "  (arrow: delegate_verify_dont_trust_done · event SubagentStop)"
    )
    return _hook_context("SubagentStop", advisory)


# ----------------------------------------------------------------------
# UserPromptSubmit lane
# ----------------------------------------------------------------------

def handle_user_prompt(payload):
    """Build the UserPromptSubmit hook output (posture + arrow lane directives), or None."""
    prompt = payload.get("prompt", "") or payload.get("user_prompt", "")
    if not isinstance(prompt, str) or not prompt.strip():
        return None

    chamber_path = find_chamber_path()
    chamber = load_chamber(chamber_path) if chamber_path else None

    directives = []

    # Posture toggle takes precedence — re-declare the working-mode contract.
    posture = detect_posture_toggle(prompt)
    if posture:
        directives.append(build_posture_directive(*posture))

    # Arrow firing: each warranted arrow injects its lane protocol as a directive,
    # with a receipt naming the matched trigger (the "why it fired").
    if chamber:
        fires = assess_intent(prompt, chamber)
        for arrow_key, trigger_verb, target, confidence, bias, matched in fires:
            directives.append(
                build_lane_directive(arrow_key, trigger_verb, confidence, bias, matched)
            )

    directives = [d for d in directives if d]
    if not directives:
        return None

    plural = "lane" if len(directives) == 1 else "lanes"
    header = (
        f"[Sovereign Sidecar] Your message activated {len(directives)} governance "
        f"{plural}. Run each inline before your main response, then continue:"
    )
    additional_context = header + "\n\n" + "\n\n".join(directives)
    return _hook_context("UserPromptSubmit", additional_context)


# ----------------------------------------------------------------------
# Hook entry point — branches on the hook event
# ----------------------------------------------------------------------

def main():
    # Fail-soft: any failure emits empty hook output (never blocks prompt or tool).
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return  # no input, no output
        payload = json.loads(raw)

        # Outpost boundary: defer to the real federation when present (all events).
        if in_governed_zone():
            return

        event = payload.get("hook_event_name", "")
        if event == "PreToolUse":
            out = handle_pretooluse(payload)
        elif event == "PostToolUse":
            out = handle_posttooluse(payload)
        elif event in ("Stop", "SubagentStop"):
            out = handle_stop(payload, event)
        else:
            # UserPromptSubmit (or a legacy {"prompt": …} payload with no event name).
            out = handle_user_prompt(payload)

        if out:
            sys.stdout.write(json.dumps(out))
    except Exception:
        # Fail-soft. No output, no block.
        return


if __name__ == "__main__":
    main()
