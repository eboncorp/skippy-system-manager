---
name: ebon-status
description: Quick health check of ebon remote server
---

# Ebon Server Status

Check health and status of ebon remote server using MCP tools.

**Usage:** `/ebon-status`

## Instructions for Claude

1. Use MCP `check_ebon_status` tool for quick health check
2. Report uptime, load average, disk usage, memory
3. Check if key services are running (WordPress, nginx, MySQL)
4. Flag any issues or warnings

## Common Checks

Use these MCP tools for detailed diagnostics:
- `check_ebon_status` - Quick overall health
- `run_remote_command` - Run specific commands on ebon
- `get_disk_usage` - Check disk space (if running locally)

## Example Commands

**Via this slash command:**
- `/ebon-status` - Get full health report

**Via natural language:**
- "Check if WordPress is running on ebon"
- "Get ebon server uptime"
- "Check disk space on ebon"
- "Run 'systemctl status nginx' on ebon"

## Notes

- Uses SSH authentication (credentials in MCP server config)
- All commands run as configured ebon user
- Timeout: 30 seconds per command
