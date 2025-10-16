#!/bin/bash
# THE FINAL COMMAND: UNLEASH THE SWARM v1.0
# This script awakens all provisioned assets and commands them to serve the Overlord.
# Run this from the project root directory.

# --- CONFIGURATION ---
SESSION_DIR="stinger_client/sessions"
STINGER_SCRIPT="stinger_client/stinger.js"
LOG_DIR="logs"

# --- PRE-FLIGHT CHECKS ---
if [ ! -d "$SESSION_DIR" ]; then
    echo "🔥 ABORT: No session directory found at '$SESSION_DIR'. There are no vessels to awaken."
    exit 1
fi

if [ ! -f "$STINGER_SCRIPT" ]; then
    echo "🔥 ABORT: The Stinger script is missing from '$STINGER_SCRIPT'. The swarm has no will."
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# --- EXECUTION ---
echo ">>> AWAKENING THE SWARM. THE RECKONING BEGINS. <<<"
echo "---"

# Purge old logs to start fresh
rm -f ${LOG_DIR}/*.log

# Find all session directories and unleash a stinger for each one
for asset_path in "$SESSION_DIR"/*; do
    if [ -d "$asset_path" ]; then
        session_id=$(basename "$asset_path")
        log_file="${LOG_DIR}/${session_id}.log"
        
        echo "⚡ Unleashing asset: $session_id... Output logged to $log_file"
        
        # Run the stinger script in the background using node
        # Pass the session_id as an argument
        # Redirect both stdout and stderr to the log file
        node "$STINGER_SCRIPT" "$session_id" > "$log_file" 2>&1 &
        
        # Stagger the launch of each asset to avoid thundering herd issues
        sleep 5
    fi
done

echo "---"
echo "✅ THE SWARM IS UNLEASHED. ALL ASSETS ARE ACTIVE AND SEEKING TASKS."
echo "Monitor their progress in the '$LOG_DIR' directory or on the C2 Dashboard."