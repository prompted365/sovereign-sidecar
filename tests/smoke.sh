#!/usr/bin/env bash
# Sovereign Sidecar — router smoke test.
#
# Verifies hooks/sidecar-router.py against specs/chamber.yaml.example:
#   - the six governance arrows fire on matching intent
#   - the posture toggle is detected
#   - no-match prompts stay silent
#   - bad stdin is fail-soft (no output, exit 0)
#
# Zero-cost: pure pattern-match, no LLM calls. Exit 0 = all pass, 1 = a failure.
#
#   bash tests/smoke.sh
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTER="$HERE/hooks/sidecar-router.py"
CHAMBER="$HERE/specs/chamber.yaml.example"

# Firing tests run from a NON-zone dir. The outpost boundary makes the sidecar
# defer (stay silent) inside any CGG/Ubiquity zone, and $HERE is under
# canonical's .ticzone — so firing must be exercised from clean ground.
NONZONE="$(mktemp -d)"
trap 'rmdir "$NONZONE" 2>/dev/null' EXIT

pass=0
fail=0

run() { ( cd "$NONZONE" && printf '%s' "$1" | SIDECAR_CHAMBER="$CHAMBER" python3 "$ROUTER" ); }

# check NAME PROMPT EXPECT   (EXPECT empty => expect no output)
check() {
  local name="$1" prompt="$2" expect="${3:-}"
  local out
  out="$(run "$prompt")"
  if [ -z "$expect" ]; then
    if [ -z "$out" ]; then
      echo "  ok   $name (silent)"; pass=$((pass + 1))
    else
      echo "  FAIL $name — expected silence, got: $out"; fail=$((fail + 1))
    fi
  else
    if printf '%s' "$out" | grep -q "$expect"; then
      echo "  ok   $name"; pass=$((pass + 1))
    else
      echo "  FAIL $name — expected '$expect', got: $out"; fail=$((fail + 1))
    fi
  fi
}

echo "Sovereign Sidecar — router smoke test"
echo "router:  $ROUTER"
echo "chamber: $CHAMBER"
echo ""

# Each governance arrow must now SPEAK its lane protocol (readable directive),
# not emit a bare KV tag. Assert the distinctive lane phrase is injected.
check "complement"     '{"prompt":"ok this is done and shipped — what did we miss?"}' 'COMPLEMENT lane'
check "counter"        '{"prompt":"should we lock in this schema change?"}'           'COUNTER lane'
check "ingest"         '{"prompt":"look at this https://example.com API docs"}'       'INGEST lane'
check "citation-intel" '{"prompt":"lets publish this and make it public"}'            'CITATION-INTEL'
check "tom"            '{"prompt":"compress this for the board"}'                     'TOM lane'
check "delegate"            '{"prompt":"break this down into subagents and orchestrate the swarm"}' 'swarm/tranche spec'
check "delegate-stress"     '{"prompt":"break this down into subagents and orchestrate the swarm"}' 'Decomposition Stress Test'
check "delegate-per-agent"  '{"prompt":"break this down into subagents and orchestrate the swarm"}' 'DISCRETE per-agent blocks'
check "delegate-verify"     '{"prompt":"break this down into subagents and orchestrate the swarm"}' 'necessary, NOT sufficient'
check "posture-toggle" '{"prompt":"[Posture → OPS/DIRECT] go"}'                       'Posture shift to OPS/DIRECT'
check "no-match"       '{"prompt":"what time is it"}'                                 ''
check "fail-soft"      'not json at all'                                             ''

# tic 308 — preflight lane fires on operator MOMENTUM (the pre-mutation moment).
check "preflight-momentum"  '{"prompt":"make it happen"}'                            'PREFLIGHT lane'
check "preflight-shipit"    '{"prompt":"ship it"}'                                   'PREFLIGHT lane'
# tic 308 — runtime RECEIPT names the matched trigger (the "why it fired", brief #2).
check "receipt-matched"     '{"prompt":"make it happen"}'                            '> chamber_bias'
# tic 308 — over-fire fixes (NEGATIVE tests): ordinary engineering language must NOT fire.
check "no-overfire-counter"  '{"prompt":"should we rename this variable"}'           ''
check "no-overfire-delegate" '{"prompt":"break this function down into smaller helpers"}' ''
# tic 308 — repo-state hooks (advisory). PreToolUse on a risky command fires; safe is silent.
check "pretool-risky"  '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git push origin main"}}' 'preflight_pre_mutation'
check "pretool-safe"   '{"hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{"file_path":"README.md"}}'           ''
check "subagentstop-verify" '{"hook_event_name":"SubagentStop"}'                     'delegate_verify_dont_trust_done'

# Outpost boundary: inside a governed zone ($HERE is under canonical's .ticzone)
# the sidecar defers and stays silent — unless SIDECAR_IGNORE_ZONE forces it.
ZP='{"prompt":"this is done and shipped, what did we miss?"}'
zone_out="$( cd "$HERE" && printf '%s' "$ZP" | SIDECAR_CHAMBER="$CHAMBER" python3 "$ROUTER" )"
if [ -z "$zone_out" ]; then
  echo "  ok   zone-suppression (silent inside governed zone)"; pass=$((pass + 1))
else
  echo "  FAIL zone-suppression — expected silence in zone, got: $zone_out"; fail=$((fail + 1))
fi
ovr_out="$( cd "$HERE" && printf '%s' "$ZP" | SIDECAR_IGNORE_ZONE=1 SIDECAR_CHAMBER="$CHAMBER" python3 "$ROUTER" )"
if printf '%s' "$ovr_out" | grep -q 'complement_due'; then
  echo "  ok   zone-override (SIDECAR_IGNORE_ZONE forces fire in zone)"; pass=$((pass + 1))
else
  echo "  FAIL zone-override — expected fire with override, got: $ovr_out"; fail=$((fail + 1))
fi

# ----------------------------------------------------------------------
# Chamber-v2 degradation ladder (specs/chamber-v2.md §2): the sidecar must be
# fail-soft across L1+L2 → L1-only → no-chamber, never WORSE than v1 when inputs
# are missing. All run from the NONZONE dir (zone-deferral off), zero model calls.
# ----------------------------------------------------------------------
echo ""
echo "chamber-v2 degradation ladder:"

# (a) L1+L2 — the v0.2 worked example carries a backdrop + per-arrow live_context.
#     Firing a lane must surface the constitutional backdrop and the live-context line.
# NOTE: the router emits JSON, so the '·' separator is escaped as · — grep for the
# ASCII phrase, not the literal middle-dot, or the match silently never fires.
L1L2_OUT="$(run '{"prompt":"lets ship it — make it happen"}')"
if printf '%s' "$L1L2_OUT" | grep -q 'Constitutional state for this session'; then
  echo "  ok   l1l2-backdrop (v0.2 chamber surfaces constitutional backdrop)"; pass=$((pass + 1))
else
  echo "  FAIL l1l2-backdrop — expected backdrop preamble, got: $L1L2_OUT"; fail=$((fail + 1))
fi
if printf '%s' "$L1L2_OUT" | grep -q 'Live context'; then
  echo "  ok   l1l2-live-context (per-arrow live_context woven into directive)"; pass=$((pass + 1))
else
  echo "  FAIL l1l2-live-context — expected 'Live context', got: $L1L2_OUT"; fail=$((fail + 1))
fi

# (b) L1-only — generate an L1-only chamber from a temp money-path repo (no enrich,
#     no model call). Mode must be UNRESOLVED and the router must STILL fire (shallower,
#     not blind) and flag the unresolved mode so it gates conservatively.
L1DIR="$(mktemp -d)"
mkdir -p "$L1DIR/src"
printf 'export async function processCharge(){ await db.charges.insert({}); }\n' > "$L1DIR/src/charge.ts"
printf 'export async function processRefund(){ await db.refunds.insert({}); }\n' > "$L1DIR/src/refund.ts"
L1CH="$L1DIR/chamber.yaml"
python3 "$HERE/hooks/chamber_fill.py" --root "$L1DIR" --out "$L1CH" --no-enrich \
  --now 2026-01-01T00:00:00Z >/dev/null 2>&1
L1_OUT="$( cd "$NONZONE" && printf '%s' '{"prompt":"make it happen"}' | SIDECAR_CHAMBER="$L1CH" python3 "$ROUTER" )"
if printf '%s' "$L1_OUT" | grep -q 'PREFLIGHT lane'; then
  echo "  ok   l1only-fires (L1-only chamber still fires the preflight lane)"; pass=$((pass + 1))
else
  echo "  FAIL l1only-fires — expected PREFLIGHT lane, got: $L1_OUT"; fail=$((fail + 1))
fi
if printf '%s' "$L1_OUT" | grep -q 'UNRESOLVED'; then
  echo "  ok   l1only-unresolved (mode flagged UNRESOLVED → gate conservatively)"; pass=$((pass + 1))
else
  echo "  FAIL l1only-unresolved — expected UNRESOLVED note, got: $L1_OUT"; fail=$((fail + 1))
fi
if printf '%s' "$L1CH" | grep -q "chamber.yaml" && grep -q "layers_present" "$L1CH"; then
  echo "  ok   l1only-written (chamber_fill produced an L1 chamber)"; pass=$((pass + 1))
else
  echo "  FAIL l1only-written — chamber_fill did not produce a chamber"; fail=$((fail + 1))
fi
rm -rf "$L1DIR"

# (c) no-chamber — degradation rung 3: NO chamber discoverable anywhere. We must
#     defeat the default-discovery fallback (~/.sidecar, ~/.claude/sidecar, ./.sidecar),
#     so we run with an EMPTY $HOME and from the NONZONE dir (no ./.sidecar) and leave
#     SIDECAR_CHAMBER unset. find_chamber_path() then returns None → chamber None → no
#     arrows fire → silent. Never crashes, never worse than v1.
EMPTYHOME="$(mktemp -d)"
NC_OUT="$( cd "$NONZONE" && printf '%s' '{"prompt":"make it happen"}' | env -u SIDECAR_CHAMBER HOME="$EMPTYHOME" python3 "$ROUTER" )"
if [ -z "$NC_OUT" ]; then
  echo "  ok   no-chamber-silent (no chamber discoverable → fail-soft silence)"; pass=$((pass + 1))
else
  echo "  FAIL no-chamber-silent — expected silence, got: $NC_OUT"; fail=$((fail + 1))
fi
rmdir "$EMPTYHOME" 2>/dev/null
# no-chamber posture toggle must STILL work (toggle detection is chamber-independent).
NC_POS="$( cd "$NONZONE" && printf '%s' '{"prompt":"[Posture → OPS/META] audit"}' | SIDECAR_CHAMBER="/nonexistent/chamber.yaml" python3 "$ROUTER" )"
if printf '%s' "$NC_POS" | grep -q 'Posture shift to OPS/META'; then
  echo "  ok   no-chamber-posture (toggle detection survives missing chamber)"; pass=$((pass + 1))
else
  echo "  FAIL no-chamber-posture — expected posture directive, got: $NC_POS"; fail=$((fail + 1))
fi

echo ""
echo "PASS=$pass FAIL=$fail"
[ "$fail" -eq 0 ] || exit 1
