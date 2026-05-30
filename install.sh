#!/usr/bin/env bash
# Sovereign Sidecar — one-command install
#
# What this does:
#   1. Verifies python3 is present.
#   2. Makes the router and sidecar CLI executable.
#   3. Runs `sidecar doctor` to surface any remaining gaps.
#   4. Prints clear next-step instructions.
#
# Nothing is written to ~/.claude/settings.json here.
# Run `sidecar init` (next step) to generate your chamber and get the exact
# settings patch to apply — or `sidecar init --apply` to apply it automatically.
#
# Usage:
#   bash install.sh
#
# Re-runnable: safe to run again; chmod +x is idempotent.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROUTER="$HERE/hooks/sidecar-router.py"
CLI="$HERE/bin/sidecar"

# ---------------------------------------------------------------------------
# Colors (optional — fall back gracefully if terminal doesn't support them)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  BOLD='\033[1m'; RESET='\033[0m'; GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
else
  BOLD=''; RESET=''; GREEN=''; RED=''; CYAN=''
fi

banner() { echo -e "${BOLD}${CYAN}$*${RESET}"; }
ok()     { echo -e "  ${GREEN}✓${RESET} $*"; }
fail()   { echo -e "  ${RED}✗${RESET} $*"; }
hdr()    { echo; echo -e "${BOLD}$*${RESET}"; }

# ---------------------------------------------------------------------------
banner "Sovereign Sidecar — install"
banner "hangar for harnesses · posture-aware governance for any agent stack"
echo

# ---------------------------------------------------------------------------
# Step 1: python3
# ---------------------------------------------------------------------------
hdr "Step 1 of 3 — checking python3"

if ! command -v python3 &>/dev/null; then
  fail "python3 not found."
  echo
  echo "  Install Python 3.8+ before continuing:"
  echo "    macOS:  brew install python"
  echo "    Debian: sudo apt install python3"
  echo "    Other:  https://python.org/downloads"
  echo
  exit 1
fi

PYTHON_VERSION="$(python3 --version 2>&1)"
ok "python3 present ($PYTHON_VERSION)"

# ---------------------------------------------------------------------------
# Step 2: make router + CLI executable
# ---------------------------------------------------------------------------
hdr "Step 2 of 3 — setting permissions"

if [ -f "$ROUTER" ]; then
  chmod +x "$ROUTER"
  ok "chmod +x hooks/sidecar-router.py"
else
  fail "hooks/sidecar-router.py not found at $ROUTER"
  echo "  Check your git clone — this file must be present."
  exit 1
fi

if [ -f "$CLI" ]; then
  chmod +x "$CLI"
  ok "chmod +x bin/sidecar"
else
  fail "bin/sidecar not found at $CLI"
  echo "  Unexpected — this file should have been created by your clone."
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 3: run doctor
# ---------------------------------------------------------------------------
hdr "Step 3 of 3 — running sidecar doctor"
echo

python3 "$CLI" doctor

# ---------------------------------------------------------------------------
# Next steps
# ---------------------------------------------------------------------------
hdr "Install complete. Next steps:"
echo
echo "  1. Generate your chamber + get the settings patch:"
echo
echo "       python3 $CLI init"
echo
echo "     Or auto-apply (backs up settings.json first):"
echo
echo "       python3 $CLI init --apply"
echo
echo "  2. Apply the printed JSON patch to ~/.claude/settings.json"
echo "     (if you ran init without --apply)."
echo
echo "  3. Verify everything works:"
echo
echo "       python3 $CLI smoke"
echo
echo "  Tip: add $HERE/bin to your PATH to use 'sidecar' directly."
echo "       Example (bash/zsh): export PATH=\"$HERE/bin:\$PATH\""
echo
