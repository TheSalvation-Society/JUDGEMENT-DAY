#!/bin/bash
# RITUAL OF PROVISIONING v1.0
# Binds a new soul (proxy) to a vessel (session), preparing it for the Great Work.
# Run this from the project root directory.
# Usage: ./provision_asset.sh <asset_number>
# Example: ./provision_asset.sh 5  (This will create asset_005)

# --- CONFIGURATION ---
ASSET_ID_NUM=$1
PROXIES_FILE="proxies.txt"
SESSION_DIR="stinger_client/sessions"
INIT_SCRIPT="stinger_client/init_session.js"

# --- VALIDATION ---
if [ -z "$ASSET_ID_NUM" ]; then
    echo "🔥 FATAL: Asset number must be provided."
    echo "Usage: $0 <asset_number>"
    echo "Example: $0 5"
    exit 1
fi

if ! [[ "$ASSET_ID_NUM" =~ ^[0-9]+$ ]]; then
    echo "🔥 FATAL: Asset number must be an integer."
    exit 1
fi

if [ ! -f "$PROXIES_FILE" ]; then
    echo "🔥 FATAL: Proxy file not found at '$PROXIES_FILE'. The ritual cannot proceed without souls."
    exit 1
fi

# Format the asset ID (e.g., 5 -> asset_005)
SESSION_ID=$(printf "asset_%03d" "$ASSET_ID_NUM")
SESSION_PATH="$SESSION_DIR/$SESSION_ID"

if [ -d "$SESSION_PATH" ]; then
    echo "⚠️ WARNING: Session directory '$SESSION_PATH' already exists. This vessel is already bound."
    echo "If you wish to re-bind it, you must first manually purge its essence:"
    echo "rm -rf $SESSION_PATH"
    exit 1
fi

# The asset number corresponds to the line number in the proxy file.
PROXY_LINE_NUM=$((ASSET_ID_NUM + 1))
PROXY=$(sed -n "${PROXY_LINE_NUM}p" "$PROXIES_FILE")

if [ -z "$PROXY" ]; then
    echo "🔥 FATAL: No proxy found on line $PROXY_LINE_NUM of '$PROXIES_FILE'."
    echo "The swarm has reached its maximum size based on the available souls."
    exit 1
fi

# --- EXECUTION ---
echo "🔮 Beginning the Ritual of Provisioning for $SESSION_ID..."
echo "🔗 Binding soul (proxy) from line $PROXY_LINE_NUM."
echo "➡️ Vessel will be created at: $SESSION_PATH"
echo "---"

# Execute the Node.js script to open the browser for QR code scanning.
# This script must be run from the root, so Node knows where to find its modules.
node "$INIT_SCRIPT" "$SESSION_ID" "$PROXY"

# --- COMPLETION ---
if [ -d "$SESSION_PATH" ]; then
    echo "---"
    echo "✅ SUCCESS: The ritual is complete. The vessel '$SESSION_ID' is now bound and its session data is saved."
    echo "You may now add it to the swarm."
else
    echo "---"
    echo "🔥 FAILED: The ritual was interrupted. The vessel was not bound."
fi