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

check "complement"     '{"prompt":"ok this is done and shipped — what did we miss?"}' 'complement_due'
check "counter"        '{"prompt":"should we lock in this schema change?"}'           'counter_warranted'
check "ingest"         '{"prompt":"look at this https://example.com API docs"}'       'ingest_needed'
check "citation-intel" '{"prompt":"lets publish this and make it public"}'            'citation_intel_due'
check "tom"            '{"prompt":"compress this for the board"}'                     'tom_due'
check "posture-toggle" '{"prompt":"[Posture → OPS/DIRECT] go"}'                       'posture_shift'
check "no-match"       '{"prompt":"what time is it"}'                                 ''
check "fail-soft"      'not json at all'                                             ''

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
