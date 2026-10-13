#!/bin/bash
# Stops and removes the Beats Pill keepalive agent.
set -euo pipefail

LABEL="com.local.beatskeepalive"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$PLIST"
rm -rf "$HOME/.local/share/beats-pill-keepalive" "$HOME/Library/Application Support/BeatsKeepAlive"
echo "Uninstalled."
