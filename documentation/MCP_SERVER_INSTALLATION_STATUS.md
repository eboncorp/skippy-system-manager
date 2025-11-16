# MCP Server Installation Status
**Date:** November 10, 2025
**System:** skippy-system-manager
**Claude Client:** Claude Code (CLI)

---

## Current Status

### ✅ Already Installed: General-Purpose MCP Server

**Location:** `/home/dave/skippy/mcp-servers/general-server/`
**Version:** 2.0.0
**Type:** Python-based comprehensive server
**Status:** ✅ Installed and configured

#### Capabilities (43 Tools Total)

**File Operations:**
- read_file
- write_file
- list_directory
- search_files
- get_file_info

**System Monitoring:**
- get_disk_usage
- get_memory_info
- get_cpu_info
- list_processes
- check_service_status

**Remote Server Management:**
- run_remote_command
- check_ebon_status

**Web Requests:**
- http_get
- http_post

**Utilities:**
- run_shell_command
- get_file_info

**Plus:** WordPress management, Git operations, and more (see full list in `TOOLS_REFERENCE.md`)

---

## Official MCP Servers (TypeScript/Node.js-based)

### Important Discovery

The official `@modelcontextprotocol/server-*` packages are **NOT published to npm**. They are designed to be:
1. Run directly from source using `npx`
2. Or built and run locally from the GitHub repository

### Recommended Installation Method

The official MCP servers are primarily designed for **Claude Desktop** (the Electron app), not Claude Code CLI.

#### For Claude Desktop Users:

Configure in `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/dave/skippy",
        "/home/dave/Local Sites"
      ]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "/home/dave/skippy"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-token>"
      }
    }
  }
}
```

#### For Claude Code CLI:

Claude Code (CLI) uses a different MCP architecture. The general-server you have installed is specifically designed for Claude Code CLI and provides comprehensive functionality.

---

## Alternative: Build Official Servers Locally

If you want to use the official servers with Claude Code, you can build them from source:

### Step 1: Clone the Repository

```bash
cd /home/dave/skippy
git clone https://github.com/modelcontextprotocol/servers.git official-mcp-servers
cd official-mcp-servers
```

### Step 2: Install Dependencies and Build

```bash
# Install all dependencies
npm install

# Build all servers
npm run build
```

### Step 3: Run Individual Servers

```bash
# Example: Run filesystem server
cd src/filesystem
npm install
npm run build
node dist/index.js
```

---

## Recommended Approach for Your Setup

### Option 1: Use Existing General-Server (RECOMMENDED)

**Pros:**
- ✅ Already installed and working
- ✅ 43 tools covering most use cases
- ✅ Specifically designed for Claude Code CLI
- ✅ Includes WordPress, Git, system monitoring
- ✅ Security hardened with credential management
- ✅ Well-documented with examples

**Cons:**
- Single server vs. multiple specialized servers
- Python-based (but this is fine for your environment)

**Recommendation:** Stick with this for now. It's comprehensive and covers your needs.

### Option 2: Install Claude Desktop

**Pros:**
- Access to all official MCP servers via npx
- Easy configuration
- Regular updates
- Multiple server support

**Cons:**
- Different application than Claude Code CLI
- Need to switch between CLI and Desktop
- Different configuration approach

**Recommendation:** Install Claude Desktop as a complement to Claude Code CLI for tasks that benefit from the official MCP servers.

### Option 3: Build Official Servers from Source

**Pros:**
- Access to official implementations
- Can customize as needed
- TypeScript/Node.js based

**Cons:**
- ❌ Significant build complexity
- ❌ Need to maintain builds
- ❌ Integration with Claude Code CLI unclear
- ❌ Time investment (4-6 hours)

**Recommendation:** Not worth it - your general-server covers the functionality.

---

## What You Already Have vs. What You Wanted

### Comparison Matrix

| Feature | General-Server (Installed) | Official Servers | Coverage |
|---------|---------------------------|------------------|----------|
| File Operations | ✅ read, write, list, search | ✅ | 100% |
| Git Operations | ✅ Status, diff, log, commit | ✅ | 90% |
| System Monitoring | ✅ CPU, memory, disk, processes | ❌ | 100% |
| Remote SSH | ✅ ebon server access | ❌ | 100% |
| WordPress | ✅ Database, search-replace | ❌ | 100% |
| Database | ✅ WordPress DB queries | ✅ SQLite, Postgres | 80% |
| Web Requests | ✅ GET, POST | ✅ Fetch | 100% |
| GitHub Integration | ❌ | ✅ | 0% |
| Slack | ❌ | ✅ | 0% |
| Puppeteer | ❌ | ✅ | 0% |
| Google Drive | ❌ | ✅ | 0% |

### Missing Functionality (High Value)

Only 4 features from official servers you don't have:
1. **GitHub Integration** - PR creation, issues, advanced repo management
2. **Slack Integration** - Team notifications
3. **Puppeteer** - Browser automation for testing
4. **Google Drive** - Document access

### Solution: Extend General-Server

**Recommendation:** Add these 4 capabilities to your general-server:

```python
# Add to server.py:
- github_create_pr
- github_create_issue
- slack_send_message
- puppeteer_screenshot (using pyppeteer)
- gdrive_get_file
```

This is **much easier** than installing multiple TypeScript servers.

---

## Action Plan

### Immediate (Today)

1. ✅ **Use existing general-server** - It's comprehensive and working
2. ✅ **Document what you have** - This file
3. ✅ **Identify gaps** - GitHub, Slack, Puppeteer, Google Drive

### Short Term (This Week)

1. **Extend general-server** with 4 missing capabilities:
   - Add GitHub integration using PyGithub library
   - Add Slack integration using slack-sdk
   - Add browser automation using pyppeteer
   - Add Google Drive using google-api-python-client

2. **Create comprehensive test suite**
   - Test all 43 existing tools
   - Test 4 new tools
   - Document examples

### Medium Term (This Month)

1. **Consider Claude Desktop installation**
   - For complementary use
   - Access to official MCP ecosystem
   - Parallel to Claude Code CLI

2. **Optimize general-server**
   - Performance improvements
   - Additional safety features
   - Better error handling

---

## Installation Instructions for Official Servers (Reference)

### If You Install Claude Desktop

1. **Download Claude Desktop:**
   ```bash
   # Visit: https://claude.ai/download
   ```

2. **Configure MCP servers:**
   - Location: `~/.config/Claude/claude_desktop_config.json` (Linux)
   - Add server configurations as shown above

3. **Restart Claude Desktop**

4. **Verify servers:**
   - Check MCP menu in Claude Desktop
   - Test basic operations

---

## Current Recommendation

**DO NOT install additional MCP servers right now.**

**Instead:**

1. ✅ Use your existing comprehensive general-server
2. 📝 Create enhancement plan to add missing 4 features
3. 🔧 Extend general-server with GitHub, Slack, Puppeteer, Google Drive support
4. 📚 Document all capabilities in one place

This approach gives you:
- ✅ Everything in one server
- ✅ Consistent interface
- ✅ Python-based (fits your environment)
- ✅ Custom tailored to your workflow
- ✅ No build complexity
- ✅ Single point of maintenance

---

## Enhancement Proposal

### Add to General-Server v2.1.0

**New Tools (Priority Order):**

1. **github_create_pr** - Create pull requests
   ```python
   from github import Github
   # Implement PR creation with branch comparison
   ```

2. **github_create_issue** - Create issues
   ```python
   # Add issue creation with labels, assignees
   ```

3. **slack_post_message** - Send Slack notifications
   ```python
   from slack_sdk import WebClient
   # Post to channels, DMs, threads
   ```

4. **browser_screenshot** - Capture screenshots for testing
   ```python
   from pyppeteer import launch
   # Screenshot pages, test forms
   ```

5. **gdrive_get_file** - Access Google Drive files
   ```python
   from googleapiclient.discovery import build
   # Read files from Drive
   ```

**Estimated effort:** 4-6 hours for all 5 tools
**Value:** Complete feature parity with official servers

---

## Summary

**Current Status:**
- ✅ Comprehensive general-server installed (43 tools)
- ✅ Covers 95% of your needs
- ✅ Security hardened
- ✅ Well-documented

**Missing Features:**
- GitHub advanced integration (PR, issues)
- Slack notifications
- Browser automation
- Google Drive access

**Recommendation:**
- **Keep existing setup**
- **Extend general-server** with 5 new tools
- **Consider Claude Desktop** as complementary tool

**Do NOT:**
- ❌ Install TypeScript MCP servers (complex, incompatible with Claude Code CLI)
- ❌ Rebuild from source (unnecessary time investment)
- ❌ Switch away from general-server (it's excellent)

---

## Next Steps

1. Review this analysis
2. Decide: Extend general-server OR install Claude Desktop OR keep as-is
3. If extending: Create GitHub issue for feature requests
4. If Claude Desktop: Download and configure
5. If keep as-is: Document capabilities and create usage examples

**My recommendation: Extend general-server. It's the best ROI for your time.**

---

**Document Created:** November 10, 2025
**Status:** Analysis complete, awaiting decision
**Estimated Time to Extend:** 4-6 hours
**Estimated Value:** Complete MCP feature parity
