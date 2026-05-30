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

echo ""
echo "PASS=$pass FAIL=$fail"
[ "$fail" -eq 0 ] || exit 1
