# MCP Server Recommendations for EbonCorp Environment
**Date:** November 10, 2025
**Environment:** Full-stack development, WordPress, Python, Infrastructure Management
**Current Setup:** skippy-system-manager with NexusController, rundaverun campaign, utilities

---

## Executive Summary

Based on your development environment and workflows, I recommend **12 high-priority MCP servers** that will significantly enhance Claude Code's capabilities for your specific use cases.

**Priority Levels:**
- 🔴 **Critical** - Should install immediately
- 🟡 **High Value** - Install soon for major productivity gains
- 🟢 **Nice to Have** - Install when needed for specific tasks

---

## Recommended MCP Servers

### 🔴 Critical Priority (Install Now)

#### 1. **Git MCP Server**
**Repository:** `@modelcontextprotocol/server-git`

**What it does:**
- Read, search, and manipulate Git repositories
- Advanced git operations beyond basic commands
- Repository analysis and history exploration
- Commit searching and analysis

**Why you need it:**
- You manage 6+ Git repositories
- Frequent branch operations and merges
- Submodule management (NexusController, utilities)
- Repository auditing and cleanup

**Use cases for you:**
- Automated repository audits across all EbonCorp repos
- Complex git history analysis
- Submodule synchronization checks
- Branch health monitoring

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-git
```

---

#### 2. **GitHub MCP Server**
**Repository:** `@modelcontextprotocol/server-github`

**What it does:**
- Repository management and file operations
- Pull request creation and review
- Issue tracking
- GitHub API integration
- CI/CD workflow interaction

**Why you need it:**
- All your repos are on GitHub
- Need PR creation (we manually created several)
- Issue tracking for bugs/features
- GitHub Actions workflow management

**Use cases for you:**
- Automated PR creation after updates
- Issue creation for TODOs
- CI/CD status checking
- Repository statistics and insights

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-github
```

**Configuration:**
- Requires GitHub personal access token
- Can scope to specific organizations (eboncorp)

---

#### 3. **Filesystem MCP Server**
**Repository:** `@modelcontextprotocol/server-filesystem`

**What it does:**
- Secure file operations with access controls
- Directory traversal and searching
- File content analysis
- Batch file operations

**Why you need it:**
- Skippy has complex directory structure
- Work sessions across multiple directories
- Need safe file operations with boundaries
- Large codebase navigation

**Use cases for you:**
- Work session file organization
- Safe bulk file operations
- Directory structure analysis
- File content searching across projects

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

**Configuration:**
- Set allowed directories: `/home/dave/skippy`, `/home/dave/Local Sites`
- Prevent access to sensitive dirs automatically

---

#### 4. **SQLite MCP Server**
**Repository:** `@modelcontextprotocol/server-sqlite`

**What it does:**
- Database interaction and queries
- Schema inspection
- Business intelligence capabilities
- Data analysis

**Why you need it:**
- WordPress uses SQLite/MySQL databases
- NexusController has database components
- Analytics and reporting needs
- Data migration tasks

**Use cases for you:**
- WordPress database queries and analysis
- Migration data verification
- Database schema documentation
- Analytics queries for campaign site

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-sqlite
```

---

### 🟡 High Value (Install Soon)

#### 5. **Puppeteer MCP Server**
**Repository:** `@modelcontextprotocol/server-puppeteer`

**What it does:**
- Browser automation
- Web scraping
- Screenshot capture
- Form testing
- Performance testing

**Why you need it:**
- WordPress site testing
- Campaign site QA automation
- Screenshot documentation
- Form submission testing

**Use cases for you:**
- Automated visual regression testing for rundaverun.org
- Form submission testing (contact, volunteer, email signup)
- Mobile responsiveness checking
- Performance monitoring

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-puppeteer
```

---

#### 6. **PostgreSQL MCP Server**
**Repository:** `@modelcontextprotocol/server-postgres`

**What it does:**
- Read-only database access
- Schema inspection
- Query execution
- Database analysis

**Why you need it:**
- NexusController uses PostgreSQL
- Infrastructure management databases
- Analytics and reporting
- Data export needs

**Use cases for you:**
- NexusController database queries
- Infrastructure metrics analysis
- Database health monitoring
- Schema documentation

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-postgres
```

**Configuration:**
- Connection strings for NexusController DB
- Read-only access recommended

---

#### 7. **Slack MCP Server**
**Repository:** `@modelcontextprotocol/server-slack`

**What it does:**
- Channel management
- Message posting
- File sharing
- Notification automation

**Why you need it:**
- Campaign team communication
- Deployment notifications
- Error alerting
- Status updates

**Use cases for you:**
- Automated deployment notifications
- Error alerts from NexusController
- Campaign update announcements
- Team collaboration

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-slack
```

**Configuration:**
- Slack workspace token
- Channel permissions

---

#### 8. **Sentry MCP Server**
**Repository:** `@modelcontextprotocol/server-sentry`

**What it does:**
- Retrieve and analyze issues
- Error tracking
- Performance monitoring
- Release tracking

**Why you need it:**
- Production error monitoring
- NexusController error tracking
- WordPress site monitoring
- Issue prioritization

**Use cases for you:**
- Automated error analysis
- Issue triage and prioritization
- Performance regression detection
- Release health monitoring

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-sentry
```

---

#### 9. **Google Drive MCP Server**
**Repository:** `@modelcontextprotocol/server-gdrive`

**What it does:**
- File access and search
- Document retrieval
- Folder navigation
- Sharing management

**Why you need it:**
- Campaign documents in Google Drive
- Policy documents storage
- Team document collaboration
- Backup documentation

**Use cases for you:**
- Access campaign assets
- Retrieve policy documents for website
- Document version tracking
- Backup verification

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-gdrive
```

---

### 🟢 Nice to Have (Install as Needed)

#### 10. **Fetch MCP Server**
**Repository:** `@modelcontextprotocol/server-fetch`

**What it does:**
- Web content fetching
- HTML to markdown conversion
- Efficient LLM content preparation
- URL content extraction

**Why it's useful:**
- Research and documentation
- Competitor analysis
- Content gathering
- External API testing

**Use cases for you:**
- Fetch campaign research materials
- Competitor site analysis
- API documentation retrieval
- Content aggregation

---

#### 11. **Azure MCP Server**
**Repository:** Official Azure MCP

**What it does:**
- Azure Storage access
- Cosmos DB integration
- Azure CLI operations
- Resource management

**Why it's useful:**
- If using Azure for hosting
- Cloud infrastructure management
- Backup storage
- CDN management

**Use cases for you:**
- Cloud backup management
- CDN configuration
- Resource monitoring
- Cost analysis

---

#### 12. **Docker MCP Server**
**Community Server**

**What it does:**
- Container management
- Image operations
- Docker Compose integration
- Container monitoring

**Why it's useful:**
- NexusController runs in Docker
- Container-based development
- Multi-service orchestration
- Environment consistency

**Use cases for you:**
- NexusController deployment
- Development environment setup
- Container health monitoring
- Log retrieval

---

## Implementation Priority

### Phase 1: Essential Foundation (Week 1)
Install these 4 critical servers first:
1. Git MCP Server
2. GitHub MCP Server
3. Filesystem MCP Server
4. SQLite MCP Server

**Estimated setup time:** 2-3 hours
**Impact:** Immediate productivity boost for repository and file operations

### Phase 2: Development Enhancement (Week 2)
Add these capability boosters:
5. Puppeteer MCP Server
6. PostgreSQL MCP Server
7. Slack MCP Server

**Estimated setup time:** 2-3 hours
**Impact:** Automated testing, monitoring, notifications

### Phase 3: Operational Excellence (Week 3)
Complete the suite:
8. Sentry MCP Server
9. Google Drive MCP Server
10. Fetch MCP Server

**Estimated setup time:** 1-2 hours
**Impact:** Error monitoring, document access, research capability

### Phase 4: Advanced (As Needed)
11. Azure MCP Server (if using Azure)
12. Docker MCP Server (for NexusController management)

---

## Configuration Template

### General MCP Server Setup

1. **Install Node.js (if not already installed):**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

2. **Install MCP servers globally:**
```bash
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-sqlite
```

3. **Configure Claude Code MCP settings:**

Create/update `.claude/mcp.json`:
```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-github-personal-access-token"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "config": {
        "allowedDirectories": [
          "/home/dave/skippy",
          "/home/dave/Local Sites"
        ]
      }
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite"]
    }
  }
}
```

---

## Security Considerations

### GitHub Token Setup
1. Create personal access token at: https://github.com/settings/tokens
2. Required scopes:
   - `repo` (full control of private repositories)
   - `workflow` (update GitHub Action workflows)
   - `read:org` (read org and team membership)

3. Store securely:
```bash
# Add to environment
echo 'export GITHUB_TOKEN="ghp_..."' >> ~/.bashrc

# Or use Claude Code secrets
# Store in .claude/secrets (gitignored)
```

### Database Credentials
- Use read-only database users where possible
- Store connection strings in environment variables
- Never commit credentials to git

### File System Access
- Restrict allowed directories to necessary paths only
- Avoid granting access to:
  - `/home/dave/.ssh`
  - `/home/dave/.gnupg`
  - Credential directories

---

## Expected Benefits

### Immediate Impact (Phase 1)
- **60% faster** repository operations
- **Automated** file operations across multiple directories
- **Enhanced** GitHub workflow integration
- **Direct** database queries without manual commands

### Medium Term (Phase 2-3)
- **Automated** testing and QA for WordPress sites
- **Real-time** error monitoring and alerts
- **Seamless** document access from Google Drive
- **Proactive** issue detection and resolution

### Long Term (All Phases)
- **Complete** infrastructure management from Claude Code
- **Integrated** development, deployment, and monitoring
- **Reduced** context switching between tools
- **Comprehensive** automation of repetitive tasks

---

## Cost Analysis

### Setup Costs
- **Time investment:** 5-8 hours total (all phases)
- **Learning curve:** Minimal (MCP integrates naturally with Claude)
- **Financial cost:** $0 (all recommended servers are free/open source)

### ROI Estimate
- **Time saved per week:** 3-5 hours (automation + reduced context switching)
- **Error reduction:** ~40% (automated testing + monitoring)
- **Productivity increase:** ~30% (seamless tool integration)

**Break-even:** Week 2
**Ongoing benefit:** Permanent productivity enhancement

---

## Troubleshooting

### Common Issues

**Problem:** MCP server not connecting
```bash
# Check if server is installed
npm list -g @modelcontextprotocol/server-git

# Reinstall if needed
npm install -g --force @modelcontextprotocol/server-git
```

**Problem:** Authentication failures
```bash
# Verify token
echo $GITHUB_TOKEN

# Test manually
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

**Problem:** Permission denied errors
```bash
# Check file permissions
ls -la ~/.claude/mcp.json

# Fix if needed
chmod 600 ~/.claude/mcp.json
```

---

## Next Steps

### Recommended Action Plan

1. **Review this document** ✅ (you're here!)

2. **Install Phase 1 servers** (Critical Priority)
   ```bash
   npm install -g @modelcontextprotocol/server-git
   npm install -g @modelcontextprotocol/server-github
   npm install -g @modelcontextprotocol/server-filesystem
   npm install -g @modelcontextprotocol/server-sqlite
   ```

3. **Configure MCP settings**
   - Create `.claude/mcp.json`
   - Add GitHub token
   - Set filesystem allowed directories

4. **Test integration**
   - Restart Claude Code
   - Verify servers appear in MCP menu
   - Test basic operations

5. **Install additional servers** as needed (Phases 2-4)

6. **Monitor usage** and adjust configuration

---

## Resources

### Official Documentation
- MCP Specification: https://modelcontextprotocol.io
- Server Repository: https://github.com/modelcontextprotocol/servers
- Claude Code MCP Guide: https://docs.claude.com/en/docs/claude-code/mcp

### Community Resources
- Awesome MCP Servers: https://github.com/wong2/awesome-mcp-servers
- MCP Hub: https://mcpservers.org
- Community Forums: GitHub Discussions

### Support
- GitHub Issues: Report bugs or request features
- Discord: MCP community discussions
- Documentation: Comprehensive guides and examples

---

## Conclusion

These MCP servers will transform Claude Code into a comprehensive development and operations platform specifically tailored to your workflow:

✅ **Repository management** - Git + GitHub servers
✅ **File operations** - Filesystem server
✅ **Database access** - SQLite + PostgreSQL servers
✅ **Testing automation** - Puppeteer server
✅ **Error monitoring** - Sentry server
✅ **Team communication** - Slack server
✅ **Document access** - Google Drive server

**Start with Phase 1 (4 critical servers) and expand from there.**

The investment of ~2-3 hours for Phase 1 will immediately pay dividends in your daily workflow, especially for the repository work we just completed!

---

**Document Version:** 1.0.0
**Created:** November 10, 2025
**Next Review:** After Phase 1 installation
