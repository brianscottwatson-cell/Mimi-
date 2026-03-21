#!/usr/bin/env bash
# openclaw-bootstrap.sh — Sets up OpenClaw agent skills for Claude Code
# Usage: bash openclaw-bootstrap.sh
set -euo pipefail

SKILL_ROOT="${HOME}/.claude/skills/openclaw-skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/agents/openclaw/claude-skills"

echo "=== OpenClaw Skills Bootstrap ==="
echo ""

# Create skill directories
echo "[1/3] Creating skill directories..."
mkdir -p "${SKILL_ROOT}"/{startup-gtm,demand-gen,customer-onboarding,vendor-onboarding}

# Copy skill files from repo if they exist, otherwise from ~/.claude
if [ -d "${SOURCE_DIR}" ]; then
  echo "[2/3] Installing skills from repo (${SOURCE_DIR})..."
  cp -r "${SOURCE_DIR}/"* "${SKILL_ROOT}/"
elif [ -d "${SKILL_ROOT}" ] && [ -f "${SKILL_ROOT}/startup-gtm/SKILL.md" ]; then
  echo "[2/3] Skills already installed at ${SKILL_ROOT}. Skipping copy."
else
  echo "[2/3] No source skill files found. Creating from embedded definitions..."
  echo "       Run this script from the Mimi- repo root, or ensure skills are already installed."
  exit 1
fi

# Verify installation
echo "[3/3] Verifying installation..."
SKILLS=("startup-gtm" "demand-gen" "customer-onboarding" "vendor-onboarding")
ALL_OK=true

for skill in "${SKILLS[@]}"; do
  if [ -f "${SKILL_ROOT}/${skill}/SKILL.md" ]; then
    echo "  OK  /${skill}"
  else
    echo "  MISSING  /${skill}/SKILL.md"
    ALL_OK=false
  fi
done

if [ -f "${SKILL_ROOT}/CLAUDE.md" ]; then
  echo "  OK  CLAUDE.md (shared config)"
else
  echo "  MISSING  CLAUDE.md"
  ALL_OK=false
fi

echo ""
if [ "${ALL_OK}" = true ]; then
  echo "All OpenClaw skills installed successfully."
  echo ""
  echo "Available skills:"
  echo "  /startup-gtm          — Go-to-market strategy for startups"
  echo "  /demand-gen           — Multi-channel demand generation"
  echo "  /customer-onboarding  — Post-sale activation and onboarding"
  echo "  /vendor-onboarding    — Partner/vendor intake and enablement"
  echo ""
  echo "Skills are located at: ${SKILL_ROOT}"
else
  echo "Some skills are missing. Check the output above."
  exit 1
fi
