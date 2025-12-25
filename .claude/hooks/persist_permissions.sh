#!/bin/bash
# persist_permissions.sh - Persist dialog-granted permissions to settings.json
# Hook: PostToolUse
# Version: 1.4.0
#
# Captures EVERY successful tool use and adds permission pattern to settings.json
# if not already present. This ensures dialog-granted permissions persist.
#
# Features:
# - Captures Bash commands, MCP tools, file operations
# - Extracts redirect paths from Bash commands (>, >>, <)
# - Extracts file paths from tee, cat >, dd, cp, mv, etc.
# - Handles variable assignments and leading operators

set -euo pipefail

INPUT=$(cat)

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
TOOL_INPUT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('tool_input',{})))" 2>/dev/null || echo "{}")

# Skip if no tool name
[ -z "$TOOL_NAME" ] && exit 0

# Skip core conversation tools (never require dialog approval)
CORE_TOOLS="Task|TodoWrite|AskUserQuestion|EnterPlanMode|ExitPlanMode"
if echo "$TOOL_NAME" | grep -qE "^($CORE_TOOLS)$"; then
    exit 0
fi

SETTINGS_FILE="$HOME/.claude/settings.json"
PERSIST_LOG="$HOME/.claude/logs/persisted_permissions.log"
mkdir -p "$(dirname "$PERSIST_LOG")"

# Array to hold multiple permissions
PERMISSIONS=()

case "$TOOL_NAME" in
    Bash)
        # Extract full command
        CMD=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('command',''))" 2>/dev/null || echo "")
        if [ -n "$CMD" ]; then
            # Use Python to extract command and redirect paths
            readarray -t PERMISSIONS < <(echo "$CMD" | python3 -c "
import sys, re
from pathlib import Path

cmd = sys.stdin.read().strip()
permissions = set()  # Use set to avoid duplicates

def add_path_permission(path, prefix='Bash(>'):
    '''Add a path-based permission'''
    path = path.strip('\"\\'')
    if path.startswith('/'):
        parent = str(Path(path).parent)
        if parent and parent != '.' and parent != '/':
            permissions.add(f'{prefix} {parent}/**)')

# Extract output redirect paths (>, >>, 2>, 2>>)
for match in re.finditer(r'[12]?>>?\s*([^\s;&|]+)', cmd):
    add_path_permission(match.group(1), 'Bash(>')

# Extract input redirect paths (<, <<)
for match in re.finditer(r'<<?(?!<)\s*([^\s;&|]+)', cmd):
    path = match.group(1)
    if not path.startswith('EOF') and not path.startswith('END'):  # Skip heredocs
        add_path_permission(path, 'Bash(<')

# Extract tee output paths: | tee /path or | tee -a /path
for match in re.finditer(r'\|\s*tee\s+(?:-[a-z]+\s+)*([^\s;&|]+)', cmd):
    add_path_permission(match.group(1), 'Bash(>')

# Extract dd output: dd of=/path
for match in re.finditer(r'\bdd\b[^|;]*\bof=([^\s;&|]+)', cmd):
    add_path_permission(match.group(1), 'Bash(>')

# Extract cp/mv/rsync destination (last argument with absolute path)
for tool in ['cp', 'mv', 'rsync', 'scp']:
    pattern = rf'\b{tool}\b\s+(?:[^\s]+\s+)*(/[^\s;&|]+)'
    for match in re.finditer(pattern, cmd):
        add_path_permission(match.group(1), 'Bash(>')

# Extract command prefix
# Skip leading redirects and operators
clean_cmd = re.sub(r'^[<>|&;]+\s*\S*\s*', '', cmd)
clean_cmd = re.sub(r'^[<>|&;]+\s*', '', clean_cmd)
# Skip variable assignments
while re.match(r'^\w+=[^\s]*\s+', clean_cmd):
    clean_cmd = re.sub(r'^\w+=[^\s]*\s+', '', clean_cmd)
# Get first word
if clean_cmd.split():
    word = clean_cmd.split()[0]
    word = re.sub(r'[^a-zA-Z0-9_/./-]', '', word)
    if word:
        permissions.add(f'Bash({word}:*)')

for p in sorted(permissions):
    print(p)
" 2>/dev/null)
        fi
        ;;
    mcp__*)
        # MCP tools - allow the full tool
        PERMISSIONS+=("$TOOL_NAME")
        ;;
    WebFetch)
        # WebFetch with domain pattern
        URL=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url',''))" 2>/dev/null || echo "")
        if [ -n "$URL" ]; then
            DOMAIN=$(echo "$URL" | python3 -c "from urllib.parse import urlparse; import sys; print(urlparse(sys.stdin.read().strip()).netloc)" 2>/dev/null || echo "")
            [ -n "$DOMAIN" ] && PERMISSIONS+=("WebFetch(domain:$DOMAIN)")
        fi
        ;;
    WebSearch)
        # WebSearch is generally safe - allow all
        PERMISSIONS+=("WebSearch")
        ;;
    Read|Glob|Grep|Write|Edit)
        # File operation tools with path arguments
        PATH_ARG=$(echo "$TOOL_INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
p = d.get('path') or d.get('file_path') or d.get('pattern') or ''
print(p)
" 2>/dev/null || echo "")
        if [ -n "$PATH_ARG" ]; then
            # Generalize to parent directory pattern
            if [[ "$PATH_ARG" == *"*"* ]]; then
                # Already a glob pattern - extract base directory
                DIR=$(echo "$PATH_ARG" | sed 's/\*.*//;s|/$||')
                [ -n "$DIR" ] && PERMISSIONS+=("$TOOL_NAME($DIR/**)")
            else
                DIR=$(dirname "$PATH_ARG")
                PERMISSIONS+=("$TOOL_NAME($DIR/**)")
            fi
        fi
        ;;
    *)
        # Other tools with path arguments
        PATH_ARG=$(echo "$TOOL_INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
p = d.get('path') or d.get('file_path') or d.get('directory') or ''
print(p)
" 2>/dev/null || echo "")
        if [ -n "$PATH_ARG" ]; then
            DIR=$(dirname "$PATH_ARG")
            PERMISSIONS+=("$TOOL_NAME($DIR/**)")
        fi
        ;;
esac

# Skip if no permissions generated
[ ${#PERMISSIONS[@]} -eq 0 ] && exit 0

# Add each permission to settings.json
for PERMISSION in "${PERMISSIONS[@]}"; do
    # Skip empty permissions
    [ -z "$PERMISSION" ] && continue

    # Check if already in settings
    if grep -qF "\"$PERMISSION\"" "$SETTINGS_FILE" 2>/dev/null; then
        continue
    fi

    # Add to settings.json
    python3 <<PYEOF
import json
from datetime import datetime

settings_file = "$SETTINGS_FILE"
permission = "$PERMISSION"
log_file = "$PERSIST_LOG"

try:
    with open(settings_file) as f:
        settings = json.load(f)

    # Ensure structure exists
    if "permissions" not in settings:
        settings["permissions"] = {}
    if "allow" not in settings["permissions"]:
        settings["permissions"]["allow"] = []

    # Check not already present
    if permission not in settings["permissions"]["allow"]:
        settings["permissions"]["allow"].append(permission)

        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        # Log the addition
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] Added: {permission}\n")

except Exception as e:
    # Silent fail - don't break tool execution
    pass
PYEOF
done

exit 0
