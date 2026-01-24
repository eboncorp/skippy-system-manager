---
name: brain
description: Skippy Brain - Unified log aggregation, pattern detection, and auto-prevention
allowed-tools: ["Bash"]
---

# Skippy Brain

Unified intelligence system that:
- Aggregates logs from system, applications, and Claude
- Detects patterns in errors and warnings
- Generates auto-prevention rules
- Provides actionable insights

## Quick Status

```bash
/home/dave/skippy/bin/skippy-brain status
```

## Run Full Cycle

```bash
/home/dave/skippy/bin/skippy-brain cycle
```

## Other Commands

| Command | Description |
|---------|-------------|
| `skippy-brain ingest` | Collect logs from all sources |
| `skippy-brain analyze` | Detect patterns in collected logs |
| `skippy-brain report` | Show comprehensive report |
| `skippy-brain insights` | Show actionable insights |
| `skippy-brain errors` | Show recent errors |
| `skippy-brain search QUERY` | Search events by keyword |
| `skippy-brain rules` | Show prevention rules |
| `skippy-brain install` | Install rules as hooks |

## Integration Points

**Collects from:**
- System: journald, auth.log, fail2ban
- Apps: Skippy logs, MCP, WordPress, maintenance
- Claude: tool usage, blocked commands, sessions, email audit, skippy-learn

**Outputs to:**
- `/home/dave/skippy/.claude/learning/aggregated_events.jsonl`
- `/home/dave/skippy/.claude/learning/detected_patterns.json`
- `/home/dave/skippy/.claude/learning/prevention_rules.json`
- `~/.claude/hooks/auto_generated_rules.sh`
