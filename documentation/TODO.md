# skippy-system-manager TODO

**Generated:** 2025-11-25
**Repository:** eboncorp/skippy-system-manager

## High Priority

### 🔴 Directory Cleanup
- [ ] Merge `development/scripts/` and `development/Scripts/` (case collision)
- [ ] Archive or delete `development/scripts_old/`
- [ ] Archive or delete `development/projects_old/`
- [ ] Review `app-to-deploy/` - contains NexusController (separate repo?)

### 🔴 Documentation
- [ ] Update README.md with current project structure
- [ ] Document MCP servers (general-server, wordpress-validator)
- [ ] Create CONTRIBUTING.md for development guidelines

## Medium Priority

### 🟡 Code Organization
- [ ] Consolidate duplicate utility directories:
  - `development/utilities/`
  - `development/skippy_tools/`
- [ ] Review `development/blockchain/` - still active?
- [ ] Clean up `development/examples/` - move to docs or archive

### 🟡 MCP Server Improvements
- [ ] Add tests for general-server (82 tools)
- [ ] Add tests for wordpress-validator
- [ ] Document tool usage in README files

### 🟡 Testing
- [ ] Set up pytest for Python components
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Increase test coverage for core modules

## Low Priority

### 🟢 Enhancements
- [ ] Create unified CLI entry point for skippy tools
- [ ] Add version tracking across all components
- [ ] Implement health check dashboard

### 🟢 Housekeeping
- [ ] Review and update .gitignore
- [ ] Add pre-commit hooks for all contributors
- [ ] Create release tagging strategy

## Completed
- [x] Add intelligent_file_processor project
- [x] Add /claude-health slash command
- [x] Expand tool permissions in settings.json
- [x] Add conversation transcripts
- [x] Add guides and protocols documentation
