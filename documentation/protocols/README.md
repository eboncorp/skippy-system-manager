# Skippy System Manager Protocols

This directory contains protocol documents that define systematic workflows and best practices for the Skippy System Manager and Claude Code usage.

## What are Protocols?

Protocols are standardized procedures that ensure consistency, quality, and reproducibility across all operations. Each protocol document describes:

- **Context**: When and why to use this protocol
- **Guidelines**: General principles to follow
- **Procedure**: Step-by-step instructions
- **Examples**: Real-world usage examples
- **Related Protocols**: Cross-references to related procedures

---

## Available Protocols

### Everyday Claude Code Use Protocols (Start Here!)

**New users should read these first:**

1. **[Session Start Protocol](session_start_protocol.md)** ⭐⭐⭐
   - How to start each Claude Code session effectively
   - Clear goal stating
   - Context provision

2. **[Tool Selection Protocol](tool_selection_protocol.md)** ⭐⭐⭐
   - When to use existing scripts vs write new code
   - Tool inventory (skippy, skippy-tools, utilities)
   - Decision tree for tool selection

3. **[Work Session Documentation Protocol](work_session_documentation_protocol.md)** ⭐⭐⭐
   - Automatic documentation during sessions
   - Where files are saved
   - How to find previous work

4. **[Safety and Backup Protocol](safety_backup_protocol.md)** ⭐⭐⭐
   - Automatic safety measures
   - Before/after file preservation
   - Recovery options

5. **[Verification Protocol](verification_protocol.md)** ⭐⭐
   - What gets verified automatically
   - When verification happens
   - Manual verification checklist

6. **[Error Recovery Protocol](error_recovery_protocol.md)** ⭐⭐
   - How errors are handled
   - Automatic retry logic
   - When to stop vs continue

7. **[Context Preservation Protocol](context_preservation_protocol.md)** ⭐⭐
   - Multi-session work continuity
   - How to continue previous work
   - Work file preservation

8. **[Question Asking Protocol](question_asking_protocol.md)** ⭐⭐
   - When Claude asks vs just does it
   - Autonomy settings
   - Question types

9. **[Script Usage vs Creation Protocol](script_usage_creation_protocol.md)** ⭐⭐
   - When to use existing scripts
   - When to write new code
   - Script creation standards

10. **[Update and Maintenance Protocol](update_maintenance_protocol.md)** ⭐
    - Regular maintenance schedules
    - Repository updates
    - Dependency management

### Development Protocols

11. **[Script Saving Protocol](script_saving_protocol.md)**
    - How to save, version, and organize scripts
    - Naming conventions and best practices

12. **[Git Workflow Protocol](git_workflow_protocol.md)**
    - Branching strategy
    - Commit message format
    - Code review process

### Operations Protocols

13. **[Conversation Cleanup Protocol](conversation_cleanup_protocol.md)**
    - Organizing 184+ conversation files
    - Retention policy
    - Archive structure

14. **[Deployment Success Verification Protocol](deployment_success_verification_protocol.md)**
    - Post-deployment success criteria
    - Automated verification
    - Sign-off checklist

15. **[Secret Rotation Protocol](secret_rotation_protocol.md)**
    - WordPress security key rotation
    - Database password rotation
    - API key management

16. **[Campaign Content Approval Protocol](campaign_content_approval_protocol.md)**
    - Content review workflow
    - Fact-checking requirements
    - Approval gates

17. **[Documentation Consolidation Protocol](documentation_consolidation_protocol.md)**
    - One source of truth principle
    - Merging duplicate docs
    - Master index creation

---

## Quick Start Guide

### For Daily Claude Code Use

**Read These First (5-10 minutes):**
1. [Session Start Protocol](session_start_protocol.md) - Start sessions correctly
2. [Tool Selection Protocol](tool_selection_protocol.md) - Know what tools exist
3. [Safety and Backup Protocol](safety_backup_protocol.md) - Understand automatic protections

**Then Reference As Needed:**
- [Work Session Documentation](work_session_documentation_protocol.md) - Where things are saved
- [Error Recovery](error_recovery_protocol.md) - When things go wrong
- [Context Preservation](context_preservation_protocol.md) - Continue multi-session work

### For New Team Members

1. Start with [Session Start Protocol](session_start_protocol.md)
2. Review [Tool Selection Protocol](tool_selection_protocol.md)
3. Understand [Git Workflow Protocol](git_workflow_protocol.md)
4. Learn [Script Saving Protocol](script_saving_protocol.md)

### For Operations

1. Follow [Update and Maintenance Protocol](update_maintenance_protocol.md)
2. Implement [Deployment Success Verification Protocol](deployment_success_verification_protocol.md)
3. Know [Secret Rotation Protocol](secret_rotation_protocol.md)

### For Campaign Work

1. Apply [Campaign Content Approval Protocol](campaign_content_approval_protocol.md)
2. Use [Deployment Success Verification Protocol](deployment_success_verification_protocol.md)
3. Follow [Documentation Consolidation Protocol](documentation_consolidation_protocol.md)

---

## Protocol Categories

### 🎯 Everyday Use (Critical)
These protocols are followed automatically by Claude Code in every session:
- Session Start
- Tool Selection
- Work Session Documentation
- Safety and Backup
- Verification
- Error Recovery

### 📚 Reference (As Needed)
These protocols provide guidance for specific situations:
- Context Preservation
- Question Asking
- Script Usage vs Creation
- Update and Maintenance

### 🔧 Operational (Periodic)
These protocols define regular maintenance and operations:
- Conversation Cleanup
- Secret Rotation
- Deployment Verification
- Documentation Consolidation

### 📋 Campaign-Specific
These protocols are specific to campaign website management:
- Campaign Content Approval
- Deployment Success Verification

---

## Using Protocols

### Protocols Claude Follows Automatically

Claude Code automatically follows these protocols without you needing to ask:
- ✅ Work Session Documentation - Saves to skippy/conversations automatically
- ✅ Safety and Backup - Creates before/after files automatically
- ✅ Verification - Verifies operations automatically
- ✅ Error Recovery - Handles errors with retry logic
- ✅ Tool Selection - Checks existing tools first

### Protocols You Should Know

You should be aware of these to work effectively with Claude:
- 📖 Session Start - How to start sessions effectively
- 📖 Context Preservation - How to continue previous work
- 📖 Question Asking - When Claude will ask vs proceed

### Protocols To Implement

These require your active participation:
- 🔧 Update and Maintenance - Run regular checks
- 🔧 Secret Rotation - Quarterly key rotation
- 🔧 Conversation Cleanup - Monthly organization

---

## Creating New Protocols

When creating a new protocol:

1. Use the template below
2. Follow the standard format
3. Save to this directory
4. Update this README
5. Follow git workflow protocol

## Protocol Template

```markdown
# Protocol Name

**Version**: 1.0.0
**Last Updated**: YYYY-MM-DD
**Owner**: Team/Person

---

## Context

When and why to use this protocol.

## Purpose

- Goal 1
- Goal 2
- Goal 3

---

## Guidelines

General principles to follow.

## Procedure

1. Step-by-step instructions
2. Clear and actionable
3. With examples

---

## Examples

Real-world usage examples.

## Related Protocols

- Link to related protocol 1
- Link to related protocol 2

---

## Best Practices

### DO:
✅ Thing to do

### DON'T:
❌ Thing to avoid

---

## Quick Reference

[Quick commands or cheat sheet]

---

**Generated**: YYYY-MM-DD
**Status**: Active
**Next Review**: YYYY-MM-DD
```

---

## Version Control

All protocols are version-controlled with the repository. Changes to protocols:

1. Follow git workflow protocol
2. Create feature branch for changes
3. Update version number and last updated date
4. Document changes in commit message
5. Merge to master

---

## Protocol Statistics

**Total Protocols:** 17
**Everyday Use:** 10
**Development:** 2
**Operations:** 5
**Status:** All active

**Created:** 2025-11-06
**Last Updated:** 2025-11-06

---

## Questions?

If a protocol is unclear or needs improvement, please:

1. Ask Claude to clarify
2. Request protocol update
3. Suggest improvements

---

## Quick Reference Card

### Starting a Session
```
"I need to [action] [target] for [project]"
Example: "I need to update the budget page for rundaverun"
```

### Finding Previous Work
```
ls ~/skippy/conversations/rundaverun_*
ls ~/skippy/conversations/*2025-11-06*
```

### Using Existing Tools
```
# WordPress deployment
bash skippy-scripts/wordpress/pre_deployment_validator_v1.0.0.sh

# Find duplicates
utilities find-duplicates ~/Downloads

# Security scan
bash ~/skippy-tools/utility/pre_commit_security_scan_v1.0.0.sh

# Health check
skippy health
```

### Continuing Previous Work
```
"Continue from yesterday's work on [topic]"
"Pick up where we left off on [project]"
```

---

**Note**: These protocols are living documents and should be updated as processes evolve.
