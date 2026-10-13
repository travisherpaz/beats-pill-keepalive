#!/bin/bash
# Beats Pill keepalive installer: clones the repo, generates the LaunchAgent plist, and starts it.
set -euo pipefail

REPO_URL="https://github.com/travisherpaz/beats-pill-keepalive.git"
INSTALL_DIR="$HOME/.local/share/beats-pill-keepalive"
LABEL="com.local.beatskeepalive"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

[ "$(uname)" = "Darwin" ] || { echo "macOS only." >&2; exit 1; }
command -v git >/dev/null || { echo "git not found. Run: xcode-select --install" >&2; exit 1; }
/usr/bin/python3 --version >/dev/null 2>&1 || { echo "python3 not found. Run: xcode-select --install" >&2; exit 1; }

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only
else
    echo "Cloning into $INSTALL_DIR"
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Application Support/BeatsKeepAlive"
sed -e "s|REPLACE_WITH_ABSOLUTE_PATH_TO|$INSTALL_DIR|g" \
    -e "s|REPLACE_WITH_HOME|$HOME|g" \
    "$INSTALL_DIR/com.local.beatskeepalive.plist.template" > "$PLIST"
plutil -lint "$PLIST" >/dev/null

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl enable "$DOMAIN/$LABEL"

echo "Installed and running. Set your Beats Pill as the output device in System Settings > Sound."
echo "Log: $HOME/Library/Application Support/BeatsKeepAlive/keepalive.log"
