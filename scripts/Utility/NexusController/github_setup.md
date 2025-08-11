# GitHub Integration Setup for NexusController

## Step 1: Create Personal Access Token

1. Go to GitHub.com and sign in to your **eboncorp** account
2. Navigate to: Settings → Developer settings → Personal access tokens → Tokens (classic)
3. Click "Generate new token" → "Generate new token (classic)"
4. Give it a name: "NexusController-Management"
5. Select these scopes:
   - **repo** (full control of repositories)
   - **admin:repo_hook** (repository hooks)
   - **user** (read user profile)
   - **admin:public_key** (SSH keys)

## Step 2: Save Token Securely

After generating the token, save it to the secure config file:

```bash
# Create secure token file
echo "your_github_token_here" | tee ~/.nexus/github_token
chmod 600 ~/.nexus/github_token
```

## Step 3: Test GitHub Connection

The NexusController will automatically:
- Sync your existing repositories: 
  - chainlink-node-setup
  - ethereum-node-manager.sh
  - ethereum-node-setup
  - full_eth_node_setup
- Upload SSH keys for seamless access
- Create backup repository for configurations

## Your GitHub Configuration
- Username: eboncorp
- Repository Management: ALL repositories (not just blockchain)
- SSH Key Upload: Disabled (can enable later)
- Config Backup: Disabled (can enable later)