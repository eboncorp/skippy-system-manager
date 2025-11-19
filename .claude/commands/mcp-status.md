---
name: mcp-status
description: Check MCP server status and available tools
---

# MCP Server Status

Check status of all MCP servers and list available tools.

## Instructions for Claude

1. Run `claude mcp list` via Bash tool to show server health
2. Summarize which servers are connected
3. List total tool count per server
4. Report any connection issues or failures

## MCP Servers Expected

**general-server** (52 tools):
- Google Drive management (13 tools)
- Pexels stock photos (4 tools)
- File operations
- System monitoring
- Remote server management (ebon)
- Web requests

## Troubleshooting

If servers show as disconnected:
1. Check virtual environment: `source /home/dave/skippy/development/mcp_servers/mcp-servers/general-server/.venv/bin/activate`
2. Test server manually: `python3 server.py`
3. Check logs: `~/.claude/logs/`
4. Restart Claude Code if needed

**Quick fix:** Restart Claude Code to reconnect MCP servers
