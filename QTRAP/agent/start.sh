#!/usr/bin/env bash
set -euo pipefail

# Entry point for the QTRAP agent. Runs Claude Code with CLAUDE.md as
# context and the tools in agent/tools/ as its only means of acting on
# the cluster.
#
# Inputs:
#   run_config.yaml, .env (in this directory)
#   --headless (optional, run non-interactively)
#
# Outputs:
#   an interactive or headless Claude Code session

if [ "$#" -gt 1 ]; then
    echo "Usage: $0 [--headless]"
    exit 1
fi

if [ "$#" -eq 1 ] && [ "$1" != "--headless" ]; then
    echo "Usage: $0 [--headless]"
    exit 1
fi

# Determine the agent directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Error: .env not found in $SCRIPT_DIR."
    echo "Copy .env.example to .env and update REMOTE_HOST and REMOTE_BASE_DIR."
    exit 1
fi

# run_config.yaml is checked by the agent itself.

set -a
source "$SCRIPT_DIR/.env"
set +a

if [ -z "${REMOTE_HOST:-}" ]; then
    echo "Error: REMOTE_HOST is not set in $SCRIPT_DIR/.env."
    exit 1
fi

if [ -z "${REMOTE_BASE_DIR:-}" ]; then
    echo "Error: REMOTE_BASE_DIR is not set in $SCRIPT_DIR/.env."
    exit 1
fi

if [ -z "${QRSH_FLAGS:-}" ]; then
    echo "Error: QRSH_FLAGS is not set in $SCRIPT_DIR/.env."
    exit 1
fi

PROMPT="Read $SCRIPT_DIR/CLAUDE.md, then run the QTRAP workflow using the settings in $SCRIPT_DIR/run_config.yaml."

if [ "$#" -eq 1 ]; then
    claude -p "$PROMPT" --output-format stream-json
else
    claude "$PROMPT"
fi