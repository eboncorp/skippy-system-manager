# Claude Code Health Check

Perform comprehensive health check on Claude Code configuration and systems.

## Instructions for Claude

Run the following checks and report status:

### 1. MCP Server Status
```bash
claude mcp list
```
Expected: All servers connected

### 2. Skills Count
```bash
ls -1 ~/.claude/skills/ | wc -l
```
Expected: 87 skills

### 3. Skills Backup Status
```bash
ls -1 ~/.claude/skills_backup/ | wc -l
diff <(ls -1 ~/.claude/skills/) <(ls -1 ~/.claude/skills_backup/) | head -10
```
Expected: Same count, no differences

### 4. Hooks Status
```bash
ls -lh ~/.claude/hooks/
```
Expected: 4 hook scripts, all executable

### 5. Storage Usage
```bash
du -sh ~/.claude/
du -sh ~/.claude/projects/
du -sh ~/.claude/debug/
du -sh ~/.claude/file-history/
du -sh /home/dave/skippy/.claude/
```

### 6. Recent Compactions
```bash
ls -lt ~/.claude/compactions/ | head -5
```

### 7. Conversation History Size
```bash
wc -l ~/.claude/history.jsonl
```

### 8. Settings Validation
```bash
cat ~/.claude/settings.json | python3 -m json.tool > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"
```

### 9. CLAUDE.md Files
```bash
ls -lh ~/.claude/CLAUDE.md /home/dave/skippy/.claude/CLAUDE.md
wc -l ~/.claude/CLAUDE.md /home/dave/skippy/.claude/CLAUDE.md
```

### 10. Slash Commands Count
```bash
ls -1 /home/dave/skippy/.claude/commands/ | wc -l
```
Expected: 27 commands (26 + claude-health)

## Report Format

Present results in a clear summary table:

| Component | Status | Details |
|-----------|--------|---------|
| MCP Servers | ✅/❌ | Connected/Disconnected |
| Skills | ✅/❌ | 87/87, backup synced |
| Hooks | ✅/❌ | 4 scripts, executable |
| Storage | ✅/⚠️/❌ | Total size, growth rate |
| Compactions | ✅/❌ | Recent activity |
| History | ✅/❌ | Entry count |
| Settings | ✅/❌ | Valid JSON |
| CLAUDE.md | ✅/❌ | Present, line counts |
| Commands | ✅/❌ | Count |

## Issue Detection

Report any issues found:
- ❌ MCP servers disconnected
- ❌ Skills backup out of sync
- ❌ Hooks not executable
- ⚠️  Storage >500 MB (consider cleanup)
- ⚠️  No recent compactions (>7 days)
- ❌ Invalid settings.json
- ❌ Missing CLAUDE.md files

## Recommendations

Based on health check, suggest:
- Actions needed to fix issues
- Maintenance tasks due soon
- Optimization opportunities
