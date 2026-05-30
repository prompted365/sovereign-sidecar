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
# Mute contract — two-source, OR-merged at read time
# ----------------------------------------------------------------------
#
# A mechanic (arrow-key or hook-event) is muted if it appears in EITHER
#   (a) env var SIDECAR_MUTE="comma,separated,keys" (case-insensitive, trimmed), OR
#   (b) the chamber's top-level `muted:` list.
# The two sources are UNIONed. Keys are arrow-keys (ingest, complement, counter, tom,
# citation_intel, delegate, preflight) AND/OR hook-event-names (PreToolUse, PostToolUse,
# SubagentStop, UserPromptSubmit). Hyphen/underscore aliasing is normalized. Special token
# "all" mutes everything; "all-repo-hooks" expands to the three repo-state hook events.
# Fail-soft: any exception → empty set → nothing muted → the arrow/hook fires (the product
# never silently breaks because of a malformed mute spec). A muted mechanic emits no stdout,
# so no fire-receipt line is appended — which is exactly how an ablation is ground-truthed.

_ALL_KEYS = {
    "ingest", "complement", "counter", "tom", "citation_intel", "delegate", "preflight",
    "pretooluse", "posttooluse", "subagentstop", "userpromptsubmit",
}
_REPO_HOOK_KEYS = {"pretooluse", "posttooluse", "subagentstop"}


def _muted_set(chamber):
    """Return the set of normalized muted keys from env + chamber. Fail-soft → empty set."""
    try:
        s = set()
        env = os.environ.get("SIDECAR_MUTE", "")
        for t in env.split(","):
            t = t.strip().lower().replace("-", "_")
            if t:
                s.add(t)
        if chamber:
            for t in (chamber.get("muted") or []):
                s.add(str(t).strip().lower().replace("-", "_"))
        if "all" in s:
            s |= set(_ALL_KEYS)
        if "all_repo_hooks" in s:
            s |= set(_REPO_HOOK_KEYS)
        return s
    except Exception:
        return set()


def _is_muted(key, muted):
    """True if `key` (normalized) is in the muted set. Fail-soft → not muted."""
    try:
        return key.strip().lower().replace("-", "_") in muted
    except Exception:
        return False


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
    """General indentation-based YAML-subset parser (PyYAML fallback).

    Handles the full v0.2 chamber shape WITHOUT a PyYAML dependency: nested
    mappings (posture/mode/stakes/repo_shape/arrows/disposition), block scalars
    (`key: |`), block + inline lists (`- item` / `[a, b]`), and typed scalars
    (int/float/bool/null/quoted-string). The earlier flat parser only reached
    `arrows.<k>.disposition_bias` + top-level scalars and would silently drop the
    v0.2 nesting — which would make the router blind to derived bias, live_context,
    mode, and layers_present whenever PyYAML was absent. Fail-soft: any error → None.
    """
    try:
        with open(path) as f:
            raw_lines = f.readlines()
    except Exception:
        return None
    # Pre-tokenize: keep non-blank, non-comment lines as (indent, text).
    toks = []
    for raw in raw_lines:
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        toks.append((indent, line.strip(), line))
    try:
        value, _ = _parse_block(toks, 0, 0)
        return value if isinstance(value, dict) else {"_root": value}
    except Exception:
        return None


def _scalarize(s):
    """Parse a YAML scalar token into a Python value."""
    s = s.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if (s[0] == s[-1]) and s[0] in ("'", '"') and len(s) >= 2:
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_scalarize(t) for t in inner.split(",")]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _parse_block(toks, i, indent):
    """Parse the mapping/list block at >= `indent`, starting at token i.

    Returns (value, next_index). Block scalars and nested structures are handled
    recursively by indentation.
    """
    # Detect list vs mapping by the first token at this indent.
    if i >= len(toks):
        return None, i
    first_indent, first_text, _ = toks[i]
    if first_text.startswith("- "):
        return _parse_list(toks, i, indent)
    if first_text == "-":
        return _parse_list(toks, i, indent)

    result = {}
    while i < len(toks):
        cur_indent, text, _ = toks[i]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            # Shouldn't happen at a mapping root; skip defensively.
            i += 1
            continue
        if text.startswith("- ") or text == "-":
            break
        key, _, val = text.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "|" or val == "|-" or val == ">" or val == ">-":
            # Block scalar — collect deeper-indented lines literally.
            block_lines = []
            j = i + 1
            block_indent = None
            while j < len(toks):
                ji, _, jraw = toks[j]
                if ji <= indent:
                    break
                if block_indent is None:
                    block_indent = len(jraw) - len(jraw.lstrip(" "))
                block_lines.append(jraw[block_indent:] if len(jraw) >= block_indent else jraw.strip())
                j += 1
            result[key] = "\n".join(block_lines)
            i = j
        elif val == "":
            # Nested block (mapping or list) — or empty value. NOTE: PyYAML dumps a
            # block sequence at the SAME indent as its parent key (`signals:` then
            # `- item` both at indent 2), so a list child is NOT necessarily deeper.
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            if nxt is not None and (nxt[1].startswith("- ") or nxt[1] == "-") and nxt[0] >= indent:
                child, ni = _parse_list(toks, i + 1, nxt[0])
                result[key] = child
                i = ni
            elif nxt is not None and nxt[0] > indent:
                child, ni = _parse_block(toks, i + 1, nxt[0])
                result[key] = child
                i = ni
            else:
                result[key] = None
                i += 1
        else:
            result[key] = _scalarize(val)
            i += 1
    return result, i


def _parse_list(toks, i, indent):
    """Parse a `- item` list block. Returns (list, next_index)."""
    items = []
    while i < len(toks):
        cur_indent, text, raw = toks[i]
        if cur_indent < indent or not (text.startswith("- ") or text == "-"):
            break
        item_text = text[2:].strip() if text.startswith("- ") else ""
        if item_text == "":
            # Nested block under the dash.
            if i + 1 < len(toks) and toks[i + 1][0] > indent:
                child, ni = _parse_block(toks, i + 1, toks[i + 1][0])
                items.append(child)
                i = ni
            else:
                items.append(None)
                i += 1
        elif ":" in item_text and not (item_text[0] in ("'", '"')):
            # Inline mapping start inside a list item — treat the dash line as the
            # first key of a mapping that may continue on deeper-indented lines.
            synth = [(indent + 2, item_text, " " * (indent + 2) + item_text)]
            j = i + 1
            while j < len(toks) and toks[j][0] > indent:
                synth.append(toks[j])
                j += 1
            child, _ = _parse_block(synth, 0, indent + 2)
            items.append(child)
            i = j
        else:
            items.append(_scalarize(item_text))
            i += 1
    return items, i


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
        r"\b(each|every|per)[- ]agent\b",
        r"\b(split|divide|hand) (this |the goal |it )?(off |out )?(to|across|among) (\d+ |multiple |several )?(agents?|workers?)\b",
        r"\bdispatch (to |the )?(agents?|swarm|subagents?)\b",
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
        r"\b(patch|fix|wire up|implement|build|run|clean up|update|change|modify|edit|migrate|drop|delete|rewrite) (this|it|the \w+)\b",
        r"\brefactor\b",
        r"\bget (this|it|the repo) (ready|launch[- ]?ready|production[- ]?ready)\b",
        r"\b(deploy|merge|push) (this|it|the \w+|to)\b",
        r"\brun (the )?(migration|deploy|release|build)\b",
        r"\b(insert|update|write) (into |to )?(the )?\w*(ledger|charge|refund|payment|payout|balance|transaction)s?\b",
        r"\b(add|wire) (a |another )?(insert|update|write|call site)\b",
    ], 0.80),
]

# Posture toggle pattern (special — refreshes chamber disposition, not an arrow)
POSTURE_TOGGLE_PATTERN = re.compile(
    r"\[Posture\s*[→>=]\s*([A-Z]+)/([A-Z]+)\]|POSTURE:\s*([A-Z]+)/([A-Z]+)",
    re.IGNORECASE,
)


def _chamber_mode(chamber):
    """Return (mode_value, mode_source). v0.2 carries a mode dict; v0.1 only a
    posture string, from which mode is at best HINTED (never resolved)."""
    m = chamber.get("mode") if isinstance(chamber, dict) else None
    if isinstance(m, dict):
        return m.get("value"), m.get("source", "unresolved")
    p = chamber.get("posture") if isinstance(chamber, dict) else None
    if isinstance(p, dict):
        pv = p.get("value")
        if isinstance(pv, str) and "/" in pv:
            return pv.split("/", 1)[1].strip().upper(), "hinted"
    if isinstance(p, str) and "/" in p:
        return p.split("/", 1)[1].strip().upper(), "hinted"
    return None, "unresolved"


def _chamber_stakes(chamber):
    s = chamber.get("stakes") if isinstance(chamber, dict) else None
    if isinstance(s, dict):
        return s.get("level")
    return None


def _runtime_modulation(arrow_key, chamber):
    """Runtime posture/mode/stakes bias delta — applied ONLY to v0.1 chambers whose
    `bias` was NOT derived at fill (v0.2 chambers already fold this in; re-applying
    would double-count). Mirrors chamber_fill.derive_biases so the two layers agree."""
    delta = 0.0
    mode, src = _chamber_mode(chamber)
    if src in ("resolved", "toggle") and mode:
        if mode == "META":
            if arrow_key == "preflight":
                delta += 0.25
            elif arrow_key in ("counter", "complement"):
                delta -= 0.10
        elif mode == "DIRECT":
            if arrow_key == "preflight":
                delta -= 0.10
    level = _chamber_stakes(chamber)
    if level == "high" and arrow_key in ("preflight", "counter"):
        delta -= 0.15
    elif level == "elevated" and arrow_key in ("preflight", "counter"):
        delta -= 0.07
    return delta


def _effective_bias(arrow_key, chamber_arrow, chamber):
    """Resolve the gate threshold for an arrow. Returns (bias, derived).

    v0.2: trust the chamber's derived `bias` (chamber_fill already folded
    posture/mode/stakes/repo_shape in per §4). v0.1: raw disposition_bias + a
    runtime modulation so a hand-authored legacy chamber still gets posture
    awareness. v0.1 chambers with neither field fall to the 0.5 neutral default,
    preserving exact pre-v2 behavior."""
    if isinstance(chamber_arrow, dict) and "bias" in chamber_arrow:
        try:
            return float(chamber_arrow["bias"]), True
        except (TypeError, ValueError):
            pass
    try:
        base = float((chamber_arrow or {}).get("disposition_bias", 0.5))
    except (TypeError, ValueError):
        base = 0.5
    base += _runtime_modulation(arrow_key, chamber)
    return max(0.0, min(1.0, base)), False


def assess_intent(prompt, chamber):
    """Return list of (arrow_key, trigger_verb, target, confidence, chamber_bias,
    matched, live_context) tuples for arrows whose pattern-match confidence exceeds
    their EFFECTIVE bias (v0.2 derived bias, or v0.1 disposition_bias + modulation).

    confidence is base_confidence × match_density (capped at 1.0).
    target is derived from the strongest matching pattern's named group or
    the matched substring; falls back to "active_move" if undeterminable.
    """
    if not chamber:
        return []

    arrows = chamber.get("arrows", {}) or {}
    fires = []
    muted = _muted_set(chamber)

    for arrow_key, trigger_verb, patterns, base_confidence in PATTERN_TABLE:
        # Mute honor-site #1: drop a muted arrow before any pattern matching so no directive
        # is built (no stdout → no fire-receipt → ablation is ground-truthed by absence).
        if _is_muted(arrow_key, muted):
            continue
        # Map snake_case arrow_key to chamber key (citation_intel → citation_intel)
        chamber_arrow = arrows.get(arrow_key, {}) or {}
        bias, _derived = _effective_bias(arrow_key, chamber_arrow, chamber)
        live_context = chamber_arrow.get("live_context") if isinstance(chamber_arrow, dict) else None

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
            # signal (entourage brief #2). Also carry the per-arrow live_context (v0.2): the
            # L2-enriched "what this lane means RIGHT NOW for THIS work" line.
            fires.append((arrow_key, trigger_verb, target, confidence, bias,
                          first_match_target or "", live_context or ""))

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
        "  2. grep our codebase for the vocabulary this source uses (its key terms, type names, "
        "function names) — list every existing call site or doc that already names this pattern, so "
        "you map to what exists instead of duplicating it. If zero hits, name the pattern cleanly as net-new.\n"
        "  3. Declare an adoption stance: ADOPT / WRAP / WATCH / NO-OP — and for WRAP/ADOPT, name the "
        "exact file(s) the adopted pattern will touch.\n"
        "  4. Emit a two-column keep/strip list: every primitive you KEEP vs. every one you STRIP, "
        "with a one-clause why per row.\n"
        "  Anti-cargo-cult test: re-state the metabolized pattern using ONLY the vocabulary surfaced "
        "by your grep in step 2 (or your clean new names) — zero of the source's own terms. If you "
        "can't, you cargo-culted; re-metabolize before using it."
    ),
    "complement": (
        "A move just landed. Run the COMPLEMENT lane inline:\n"
        "  1. Name the centroid (governing concern) and the active ray (what you just did).\n"
        "  2. Breadth sweep — grep the repo for every OTHER surface that shares this move's "
        "invariant, not just its imports: peer files in the same directory, sibling call sites of "
        "the same function/table/endpoint, and semantically-coupled twins (e.g. if you touched "
        "charge.ts, search for refund.ts / void.ts; if you touched one writer of a constraint, find "
        "the other writers). List each hit you found and whether the same complement applies there.\n"
        "  3. Surface the single strongest MISSING complement — but only if it changes "
        "implementation, governance, proof burden, a boundary, or what must happen next. A sibling "
        "from step 2 that needs the same change IS that complement.\n"
        "  4. If the sweep is clean and nothing structural is missing, say \"current focus is "
        "sufficient — swept N peers/siblings, none coupled\" and stop. Do not invent decorative "
        "additions. Return a finding, not an essay."
    ),
    "counter": (
        "An irreversible / hard-to-reverse decision looks imminent. Run the COUNTER lane inline "
        "— you are the genuine adversary, not a devil's advocate:\n"
        "  1. State the move in one sentence.\n"
        "  2. Name the single premise that, if false, makes the whole move wrong.\n"
        "  3. Falsify it with evidence, don't assert it: go find the disconfirming fact. grep/read "
        "the actual code, data, or call sites the premise depends on (the table the lock granularity "
        "assumes, the call sites that share the contract you're changing, the config that sets the "
        "threshold) and quote what you found. Build the strongest case it WILL fail (not \"might\") "
        "from that quoted evidence; only if the search returns nothing may you mark \"structural — no "
        "current evidence,\" and say what you searched.\n"
        "  4. Enumerate the blast radius: list every other surface that depends on this premise being "
        "true (other call sites, sibling files, downstream consumers) so the cost of being wrong is "
        "named, not guessed.\n"
        "  5. Verdict: HOLD / REVISE / PROCEED-WITH-AWARENESS. Do not soften the argument to stay agreeable."
    ),
    "tom": (
        "An audience / expression shift is in play. Run the TOM lane:\n"
        "  1. Extract the centroid (invariant meaning) of the source in one sentence.\n"
        "  2. Before re-expressing, enumerate the source's load-bearing constraints — list EVERY "
        "warning, unresolved risk, scope boundary, and concrete identifier (file path, route, "
        "function, capability) the source actually states. This is your invariant set.\n"
        "  3. Re-express for the target audience.\n"
        "  4. Diff the re-expression against the step-2 list: confirm each enumerated item survives "
        "unsoftened, and confirm you introduced ZERO capability/path/route/name not present in step "
        "2. Emit the result as a SURVIVED / SOFTENED / DROPPED / INVENTED ledger — one row per item.\n"
        "  Any SOFTENED, DROPPED, or INVENTED row is a centroid violation: keep the centroid intact "
        "and trim register elsewhere, then re-diff."
    ),
    "citation_intel": (
        "Publication looks imminent. Run the CITATION-INTEL readiness check before you publish — "
        "produce findings from actual inspection, not assertions:\n"
        "  1. EXTRACT the single most extractable claim and token-estimate the draft (words ÷ 0.75). "
        "Confirm the claim sits in the first 500 tokens — quote the sentence and its position; if "
        "past 500, flag it.\n"
        "  2. SCAN entities: list every proper noun + concrete stat in the draft (need ≥3). If fewer, "
        "the piece is too abstract to be cited — flag it.\n"
        "  3. AUDIT the site AI-access stack by actually reading the files — do not assume:\n"
        "     - read robots.txt and list which AI crawlers are explicitly allowed vs missing (GPTBot, "
        "ClaudeBot, PerplexityBot, anthropic-ai, Google-Extended, OAI-SearchBot, Meta-ExternalAgent)\n"
        "     - check llms.txt exists, is current, and lists this article (grep the article slug in it)\n"
        "     - confirm llms.txt Content-Type is text/plain; charset=utf-8\n"
        "  4. GENERATE 2-3 FAQ questions answerable from the body (answers must carry the primary "
        "claim, no new claims), and assign schema by type (BIZ → BlogPosting+FAQ / INFRA → "
        "+speakable / CENTROID → Article+mentions+FAQ).\n"
        "  Return a per-check readiness report with status + one concrete action item per failure. "
        "Each line must reference what you actually read, not 'looks fine'."
    ),
    "delegate": (
        "You're about to fan this goal out to subagents — govern the dispatch as a coherent "
        "swarm/tranche spec, not an ad-hoc spray:\n"
        "  - map the seam surface FIRST (concrete): before writing briefs, grep the goal's shared "
        "invariants across the repo — run grep -rniE on the cross-cutting concepts (e.g. "
        "ledger|charge|refund|payment|auth|schema|migration) and LIST which files touch each. The "
        "seams live where two agents' scopes both land on the same listed file/invariant. You cannot "
        "stress-test a decomposition you have not enumerated.\n"
        "  - tom each brief: every subagent brief must preserve the goal's centroid — no drift, no "
        "softened constraint, no invented scope; state what each subagent must NOT do. Emit each "
        "brief as ITS OWN block under a named heading (SA-N / A-N / T-N / Agent-N) — DISCRETE "
        "per-agent blocks, NOT a single table row per agent.\n"
        "  - counter the slicing: emit a section titled literally **Decomposition Stress Test** "
        "naming 3+ structural failure modes of THIS cut, each anchored to a file/invariant from your "
        "seam grep (seam gaps between agents, blind spots a peer agent's scope would swallow, runtime "
        "leaks at composition). Out-of-scope honesty and boundary hygiene are NOT stress-testing — "
        "name what the chosen slice GETS WRONG.\n"
        "  - verify, don't trust 'done': the synthesis contract must name HOW the parent "
        "independently verifies each subagent's result — re-run against source / spot-check N rows vs "
        "source / cross-validate with a sibling / counter-check probe. 'Review for quality' is "
        "trusting the subagent's framing, not verification. A \"done\" report is necessary, NOT "
        "sufficient.\n"
        "  - complement the fan-out: is the set complete — any load-bearing lane/subagent MISSING? "
        "(and resist over-spawning decorative agents).\n"
        "  - point, don't inscribe: each brief POINTS its subagent at the right surfaces/sources to "
        "hydrate from (path + purpose line) — don't inline or dump content.\n"
        "  - sequence + parallelize: state the dependency graph explicitly; run independent briefs in "
        "PARALLEL, serialize only true dependencies and name the handoff.\n"
        "  - posture + ingest: give each subagent a DIRECT vs META scope so none overreach; /ingest "
        "shared context once at the parent and point subagents at the metabolized form.\n"
        "  Emit the dispatch as an explicit spec (Decomposition Stress Test FIRST, then briefs, "
        "dependency graph, synthesis contract) before spawning anything."
    ),
    "preflight": (
        "Operator momentum detected — a mutation may be imminent. Run the PREFLIGHT lane BEFORE you "
        "touch the repo. The receipt is necessary but NOT sufficient: a clean receipt that only "
        "inspected this file misses sibling writers of the same invariant. Produce a mutation receipt "
        "AND enumerate:\n"
        "  - intended action (one line)\n"
        "  - target files / surfaces\n"
        "  - invariant at risk + the concrete token it is keyed to (the table / contract / symbol the "
        "change writes)\n"
        "  - OTHER writers of that invariant across the WHOLE repo — run the search now, list "
        "path:line for each. Use grep -rn for the mutation pattern (INSERT/UPDATE/insert(/update( "
        "etc.) AND a separate semantic-sibling pass on the concept word (charge / refund / payout / "
        "ledger) to catch coupled files that share the invariant with NO import edge. A list of one "
        "means you under-searched.\n"
        "  - per-sibling reconciliation: for each writer found, does this change keep its copy of the "
        "invariant true, or must it change too?\n"
        "  - repo evidence actually inspected (read it — don't assume)\n"
        "  - validation command that catches breakage at ALL sites; rollback path (explicit steps)\n"
        "  - verdict: PROCEED / HOLD / ASK\n"
        "  HOLD if any sibling writer is unenumerated or unreconciled; ASK if the invariant token is "
        "unclear; PROCEED only when the writer list is complete and every line is real, not a "
        "placeholder. If nothing is actually about to mutate, say \"no mutation pending\" and stop — "
        "don't manufacture ceremony."
    ),
}


def build_lane_directive(arrow_key, trigger_verb, confidence, bias, matched="", live_context=""):
    """Build a readable lane directive. Returns str, or None for unknown arrows.

    The trailing RECEIPT line stays human-readable but keeps the `<arrow>_<verb>`
    token so a downstream tool (or a smoke test) can still detect which lane fired
    without parsing a machine-only dict. It also names the matched trigger substring
    — the "why it fired" — so the user can reject a mis-fire at a glance instead of
    learning to skim past silent noise (entourage brief #2).

    v0.2: if the chamber carries a per-arrow `live_context` (the L2-enriched "what
    this lane means RIGHT NOW for THIS work"), it is woven in just before the protocol
    so the generic lane body is anchored to the session's actual surface.
    """
    body = LANE_DIRECTIVES.get(arrow_key)
    if not body:
        return None
    label = arrow_key.replace("_", "-")
    why = f' · matched "{matched}"' if matched else ""
    lc = ""
    if live_context:
        lc = f"Live context (this session): {str(live_context).strip()}\n"
    return (
        f"[sidecar · {label}] {lc}{body}\n"
        f"  (arrow: {arrow_key}_{trigger_verb}{why} · confidence {confidence:.2f} "
        f"> chamber_bias {bias:.2f})"
    )


def build_posture_directive(domain, depth):
    return (
        f"[sidecar · posture] Posture shift to {domain}/{depth} detected — re-declare the "
        f"working-mode contract and act on it now:\n"
        f"  - First, RE-EMIT the banner line exactly: POSTURE: {domain}/{depth} (reason: explicit "
        f"toggle).\n"
        f"  - META = read-only: no file edits/writes, no git commit/push, no destructive commands, "
        f"no API writes (POST/PUT/PATCH/DELETE). If your NEXT planned step would mutate state, do NOT "
        f"take it — name the step in one line and ask: \"Switch to DIRECT or keep read-only?\" before "
        f"any tool call.\n"
        f"  - DIRECT = mutate only the explicitly-scoped surface; before claiming done, run the "
        f"relevant validation (name the exact test/lint/build command and its result). Repo-wide "
        f"refactors/renames still require pausing to ask even in DIRECT.\n"
        f"  - Carry this posture forward for the rest of the session until the next explicit "
        f"[Posture → X/Y] toggle.\n"
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
    r"(migrations?/|\b(ledger|charge|refund|payment|payout|balance|transaction|webhook)\b|"
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


# PreToolUse advisory text — two registers, swappable by SIDECAR_PREFLIGHT_MODE.
#
# concrete (default, SHIPPED): a CONCRETE ACTION — "grep the repo for EVERY OTHER writer
#   of this invariant and LIST them" — which drives the model to actually run the search
#   that surfaces semantic siblings (e.g. refund.ts next to charge.ts) with no import edge.
# generic (ablation only): the weaker tic-309 register — "inspect the adjacent surfaces
#   first, a peer file may share the invariant" — exhortation without a concrete tool action.
#   Used by the generic-vs-concrete ablation (eval arm E1) to isolate whether the LIFT on
#   coupled-file coverage is owned by the CONCRETE-ACTION upgrade, not the rigor receipt alone.
#
# Default is "concrete" so unset env preserves the shipped product behavior exactly. Fail-soft:
# any unrecognized value falls back to concrete.

_PREFLIGHT_BODY_CONCRETE = (
    "This is a shared-invariant surface. Before the mutation lands, do the ENUMERATION first — "
    "do not start with the edit:\n"
    "  1. Identify the contract this write upholds (the table/ledger/endpoint/secret it touches, "
    "e.g. an INSERT into `ledger_entries`, a charge/refund handler, a migration on `payments`).\n"
    "  2. Run a concrete repo-wide search for EVERY OTHER WRITER of that same contract — not just "
    "files this one imports. Grep the repo for the literal table/collection name, the "
    "function/route name, and the invariant's keyword (e.g. `grep -rn \"ledger_entries\" .`, "
    "`grep -rni \"refund\\|charge\\|payment\" src/`). Co-violators are usually SEMANTIC SIBLINGS "
    "(refund.ts next to charge.ts), not import-graph neighbors.\n"
    "  3. LIST the call sites you found by path, one per line, and for each say: does it hold the "
    "same invariant (e.g. atomic transaction, idempotency key, auth check) that you are about to "
    "add/change here? If any sibling shares the invariant and does NOT yet hold it, name it as "
    "in-scope-or-deferred — do not silently fix only the file in front of you.\n"
    "  4. Then name (one line each): the invariant at risk, the validation command that proves it "
    "safe, and the rollback path.\n"
    "If you cannot list the other writers, you have not searched — search before you mutate."
)

_PREFLIGHT_BODY_GENERIC = (
    "This is a sensitive surface. Before the mutation lands, take a moment to think about coupling:\n"
    "  - Name the invariant this write upholds (atomicity, idempotency, auth, etc.).\n"
    "  - Inspect the adjacent surfaces first — a peer file may share the invariant you're about to "
    "touch, so don't fix only the file in front of you.\n"
    "  - Note the validation command and the rollback path.\n"
    "Keep the change tight and consistent with the surrounding code."
)


def _preflight_mode():
    """Read SIDECAR_PREFLIGHT_MODE env. Returns 'generic' or 'concrete' (default). Fail-soft."""
    try:
        v = (os.environ.get("SIDECAR_PREFLIGHT_MODE", "") or "").strip().lower()
        return "generic" if v == "generic" else "concrete"
    except Exception:
        return "concrete"


def handle_pretooluse(payload, chamber=None):
    """Advisory pre-mutation receipt when a tool call touches a risky surface."""
    # Mute honor-site #2: PreToolUse muted (honors both "pretooluse" and the
    # "preflight_pre_mutation" fire-site alias).
    muted = _muted_set(chamber)
    if _is_muted("PreToolUse", muted) or _is_muted("preflight_pre_mutation", muted):
        return None
    tool_name = payload.get("tool_name", "")
    surface = _risk_surface(tool_name, payload.get("tool_input", {}))
    if not surface:
        return None
    surface_tags = ", ".join(surface)
    mode = _preflight_mode()
    body = _PREFLIGHT_BODY_GENERIC if mode == "generic" else _PREFLIGHT_BODY_CONCRETE
    receipt = (
        f"[sidecar · preflight] About to {tool_name} — risk surface: {surface_tags}.\n"
        f"{body}\n"
        f"  (arrow: preflight_pre_mutation · tool {tool_name} · mode {mode})"
    )
    return _hook_context("PreToolUse", receipt)


def handle_posttooluse(payload, chamber=None):
    """Advisory evidence-digestion nudge after a risky mutation succeeds."""
    # Mute honor-site #3: PostToolUse muted.
    muted = _muted_set(chamber)
    if _is_muted("PostToolUse", muted) or _is_muted("preflight_post_tool", muted):
        return None
    tool_name = payload.get("tool_name", "")
    surface = _risk_surface(tool_name, payload.get("tool_input", {}))
    if not surface:
        return None
    surface_tags = ", ".join(surface)
    nudge = (
        f"[sidecar · post-tool] {tool_name} just wrote {surface_tags}. The mutation is on disk but "
        "UNVERIFIED. Before moving to the next step, do these concrete checks now:\n"
        "  1. Run the validation that proves this write upholds its invariant — the actual command "
        "(test, typecheck, lint, migration dry-run, or a targeted unit test). Paste the command and "
        "its result, do not assert 'looks correct'.\n"
        "  2. Re-run the co-writer search for the contract you just touched "
        "(`grep -rn \"<table-or-contract-name>\" .`) and confirm the enumerated siblings from "
        "preflight are now CONSISTENT with this change — if you added an atomic transaction / "
        "idempotency guard / auth check here, open each sibling writer and confirm it has the same "
        "guard, or explicitly record which sibling is still divergent and why that is acceptable.\n"
        "  3. State the next required check by name, or state — with the specific reason — why no "
        "further check is needed.\n"
        "A write with no run validation and no sibling cross-check is a candidate drift point, not a "
        "finished step.\n"
        f"  (arrow: preflight_post_tool · tool {tool_name})"
    )
    return _hook_context("PostToolUse", nudge)


def handle_stop(payload, event_name, chamber=None):
    """SubagentStop → verify-don't-trust-done advisory (a subagent just reported done). Plain
    Stop is a v1 no-op: a real done-claim verifier needs transcript inspection (owed as a
    follow-up gate); the block capability is confirmed available for that future surface."""
    if event_name != "SubagentStop":
        return None
    # Mute honor-site #4: SubagentStop muted (also accepts the arrow alias).
    muted = _muted_set(chamber)
    if _is_muted("SubagentStop", muted) or _is_muted("delegate_verify_dont_trust_done", muted):
        return None
    advisory = (
        "[sidecar · verify] A subagent reported done. Its scoped context could not see the "
        "cross-cutting inconsistency a peer would catch — a 'done' report is necessary, NOT "
        "sufficient. Run an INDEPENDENT re-check now, with concrete commands, before you trust it:\n"
        "  1. List what the subagent claims it changed (files/contracts). For each touched contract, "
        "run your own repo-wide search for OTHER writers of it "
        "(`grep -rn \"<table-or-contract-name>\" .`) — the subagent's bounded scope is exactly where "
        "it would have missed a semantic sibling.\n"
        "  2. Run the validation yourself — re-execute the test/typecheck/build that proves the "
        "claim, and read the actual output. Do not accept the subagent's summary of its own "
        "validation.\n"
        "  3. Diff or open the changed files and confirm the invariant the task required is actually "
        "present in the code (not just described in the report).\n"
        "  4. Verdict: VERIFIED (with the command output you ran) / DIVERGENT (name the gap) / "
        "UNVERIFIED (say what you could not check).\n"
        "If you have not run a command of your own, you have not verified — you have re-read a "
        "report.\n"
        "  (arrow: delegate_verify_dont_trust_done · event SubagentStop)"
    )
    return _hook_context("SubagentStop", advisory)


# ----------------------------------------------------------------------
# UserPromptSubmit lane
# ----------------------------------------------------------------------

def handle_user_prompt(payload, chamber=None):
    """Build the UserPromptSubmit hook output (posture + arrow lane directives), or None."""
    prompt = payload.get("prompt", "") or payload.get("user_prompt", "")
    if not isinstance(prompt, str) or not prompt.strip():
        return None

    # Mute honor-site #5: UserPromptSubmit muted WHOLESALE (mutes the whole prompt lane
    # including posture; per-arrow muting is handled inside assess_intent).
    if _is_muted("UserPromptSubmit", _muted_set(chamber)):
        return None

    directives = []

    # Posture toggle takes precedence — re-declare the working-mode contract.
    posture = detect_posture_toggle(prompt)
    if posture:
        directives.append(build_posture_directive(*posture))

    # Arrow firing: each warranted arrow injects its lane protocol as a directive,
    # with a receipt naming the matched trigger (the "why it fired") and any v0.2
    # per-arrow live_context.
    if chamber:
        fires = assess_intent(prompt, chamber)
        for arrow_key, trigger_verb, target, confidence, bias, matched, live_context in fires:
            directives.append(
                build_lane_directive(arrow_key, trigger_verb, confidence, bias, matched, live_context)
            )

    directives = [d for d in directives if d]
    if not directives:
        return None

    plural = "lane" if len(directives) == 1 else "lanes"
    header = (
        f"[Sovereign Sidecar] Your message activated {len(directives)} governance "
        f"{plural}. Run each inline before your main response, then continue:"
    )
    backdrop = build_constitutional_backdrop(chamber)
    parts = [header]
    if backdrop:
        parts.append(backdrop)
    parts.extend(directives)
    additional_context = "\n\n".join(parts)
    return _hook_context("UserPromptSubmit", additional_context)


def build_constitutional_backdrop(chamber):
    """Compose the v0.2 constitutional-backdrop preamble the lanes run against.

    This is the v2 point: the chamber is the sidecar's only organ for holding
    constitutional state (the stateless cousin of harmony disposition). When the
    chamber carries an L2 disposition / resolved mode / stakes, surface it so the
    firing lanes are anchored to WHAT THIS WORK IS, not just the matched pattern.
    Returns "" for a bare v0.1 chamber (no backdrop to show) — fail-soft."""
    if not isinstance(chamber, dict):
        return ""
    bits = []
    mode, mode_src = _chamber_mode(chamber)
    stakes = _chamber_stakes(chamber)
    layers = chamber.get("layers_present") or []
    posture = chamber.get("posture")
    posture_v = posture.get("value") if isinstance(posture, dict) else posture

    disp = chamber.get("disposition")
    disp_text = disp.get("text") if isinstance(disp, dict) else (disp if isinstance(disp, str) else None)

    # A v0.1 chamber has no mode dict, no stakes, no layers, and only a one-line
    # disposition string — nothing constitutional to surface beyond the lanes.
    if not (isinstance(chamber.get("mode"), dict) or stakes or layers):
        return ""

    line_bits = []
    if posture_v:
        line_bits.append(f"posture {posture_v}")
    if mode:
        suffix = "" if mode_src in ("resolved", "toggle") else f" ({mode_src} — UNRESOLVED, gate conservatively)"
        line_bits.append(f"mode {mode}{suffix}")
    if stakes:
        line_bits.append(f"stakes {stakes}")
    if layers:
        line_bits.append("layers " + "+".join(layers))
    if line_bits:
        bits.append("· ".join(line_bits))

    if disp_text and "L1-only" not in disp_text:
        bits.append(str(disp_text).strip())

    if not bits:
        return ""
    body = "\n".join(bits)
    return f"[sidecar · backdrop] Constitutional state for this session:\n{body}"


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

        # Load chamber once and thread it into each handler. The chamber carries both the
        # arrow disposition and the `muted:` list; loading it here (cheap, no LLM cost) lets
        # the repo-state handlers honor mute without each re-reading from disk.
        chamber_path = find_chamber_path()
        chamber = load_chamber(chamber_path) if chamber_path else None

        event = payload.get("hook_event_name", "")
        if event == "PreToolUse":
            out = handle_pretooluse(payload, chamber)
        elif event == "PostToolUse":
            out = handle_posttooluse(payload, chamber)
        elif event in ("Stop", "SubagentStop"):
            out = handle_stop(payload, event, chamber)
        else:
            # UserPromptSubmit (or a legacy {"prompt": …} payload with no event name).
            out = handle_user_prompt(payload, chamber)

        if out:
            sys.stdout.write(json.dumps(out))
    except Exception:
        # Fail-soft. No output, no block.
        return


if __name__ == "__main__":
    main()
