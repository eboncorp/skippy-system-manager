# Custom Agents

**Last Updated:** 2026-01-17

---

## Overview

Custom agents extend Claude Code with specialized personas and capabilities. Agents are defined with YAML frontmatter specifying name, description, tools, and color.

---

## Available Agents

| Agent | Purpose | Tools |
|-------|---------|-------|
| `code-reviewer` | Expert code review | Task, Bash, Glob, Grep, Read, Edit, Write |

---

## Agent: code-reviewer

**Description:** Expert code review focusing on best practices, code quality, and maintainability.

**When to Use:**
- After implementing a new feature
- Before committing changes
- When refactoring existing code
- For feedback on architectural decisions
- After writing complex algorithms or API endpoints

**Capabilities:**
- Correctness verification
- Readability assessment
- Performance analysis
- Security review
- Maintainability evaluation
- Standards compliance

---

## Creating New Agents

To add a custom agent, create a markdown file with YAML frontmatter:

```yaml
---
name: agent-name
description: When to use this agent (clear trigger conditions)
tools: Task, Bash, Glob, Grep, Read, Edit, Write
color: blue
---

Agent persona and instructions here...
```

**Frontmatter Fields:**
- `name`: Lowercase, hyphens (max 64 chars)
- `description`: Clear auto-invoke triggers (max 1024 chars)
- `tools`: Comma-separated list of allowed tools
- `color`: Display color (red, blue, green, etc.)

---

## Notes

- Agents inherit session permissions
- Custom agents are project-scoped
- Claude Code built-in agents (Explore, Plan, etc.) are always available
