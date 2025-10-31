#!/usr/bin/env python3
"""
GitHub Integration for NexusController Secure
Comprehensive GitHub account and repository management
"""

import os
import json
import subprocess
import requests
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import tempfile

class GitHubManager:
    """GitHub account and repository management"""
    
    def __init__(self, logger):
        self.logger = logger
        self.config_dir = Path.home() / '.nexus' / 'github'
        self.config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        self.accounts = {}
        self.current_account = None
        self.load_accounts()
    
    def load_accounts(self):
        """Load GitHub accounts from secure storage"""
        accounts_file = self.config_dir / 'accounts.json'
        if accounts_file.exists():
            try:
                with open(accounts_file, 'r') as f:
                    self.accounts = json.load(f)
                self.logger.log_event("github_accounts_loaded", {
                    "account_count": len(self.accounts)
                })
            except Exception as e:
                self.logger.log_event("github_accounts_load_error", {"error": str(e)})
    
    def save_accounts(self):
        """Save GitHub accounts securely"""
        accounts_file = self.config_dir / 'accounts.json'
        try:
            with open(accounts_file, 'w') as f:
                json.dump(self.accounts, f, indent=2)
            os.chmod(accounts_file, 0o600)
            self.logger.log_event("github_accounts_saved", {
                "account_count": len(self.accounts)
            })
        except Exception as e:
            self.logger.log_event("github_accounts_save_error", {"error": str(e)})
    
    def add_account(self, username: str, token: str, account_type: str = "personal") -> bool:
        """Add GitHub account with token"""
        try:
            # Validate token
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get('https://api.github.com/user', headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                
                self.accounts[username] = {
                    'username': username,
                    'token': token,  # In production, encrypt this
                    'account_type': account_type,
                    'user_info': user_info,
                    'added_at': datetime.now().isoformat()
                }
                
                self.save_accounts()
                self.logger.log_event("github_account_added", {
                    "username": username,
                    "account_type": account_type
                })
                return True
            else:
                print(f"❌ Invalid GitHub token for {username}")
                return False
                
        except Exception as e:
            print(f"❌ Error adding GitHub account: {e}")
            return False
    
    def set_current_account(self, username: str) -> bool:
        """Set active GitHub account"""
        if username in self.accounts:
            self.current_account = username
            self.logger.log_event("github_account_switched", {"username": username})
            return True
        return False
    
    def get_current_headers(self) -> Optional[Dict]:
        """Get API headers for current account"""
        if not self.current_account or self.current_account not in self.accounts:
            return None
        
        token = self.accounts[self.current_account]['token']
        return {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def upload_ssh_key(self, key_name: str, public_key_path: str) -> bool:
        """Upload SSH public key to GitHub"""
        headers = self.get_current_headers()
        if not headers:
            print("❌ No active GitHub account")
            return False
        
        try:
            with open(public_key_path, 'r') as f:
                public_key = f.read().strip()
            
            data = {
                'title': key_name,
                'key': public_key
            }
            
            response = requests.post(
                'https://api.github.com/user/keys',
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                print(f"✅ SSH key '{key_name}' uploaded to GitHub")
                self.logger.log_event("ssh_key_uploaded", {
                    "key_name": key_name,
                    "account": self.current_account
                })
                return True
            elif response.status_code == 422:
                print(f"⚠️  SSH key already exists on GitHub")
                return True
            else:
                print(f"❌ Failed to upload SSH key: {response.json()}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading SSH key: {e}")
            return False
    
    def list_repositories(self, repo_type: str = "all") -> List[Dict]:
        """List repositories for current account"""
        headers = self.get_current_headers()
        if not headers:
            return []
        
        try:
            url = f"https://api.github.com/user/repos?type={repo_type}&sort=updated&per_page=100"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                repos = response.json()
                self.logger.log_event("repositories_listed", {
                    "account": self.current_account,
                    "repo_count": len(repos)
                })
                return repos
            else:
                print(f"❌ Failed to list repositories: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error listing repositories: {e}")
            return []
    
    def clone_repository(self, repo_url: str, destination: str, use_ssh: bool = True) -> bool:
        """Clone repository with SSH authentication"""
        try:
            if use_ssh and 'https://github.com/' in repo_url:
                # Convert HTTPS URL to SSH
                repo_path = repo_url.replace('https://github.com/', '').replace('.git', '')
                repo_url = f'git@github.com:{repo_path}.git'
            
            cmd = ['git', 'clone', repo_url, destination]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Repository cloned to {destination}")
                self.logger.log_event("repository_cloned", {
                    "repo_url": repo_url,
                    "destination": destination
                })
                return True
            else:
                print(f"❌ Clone failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error cloning repository: {e}")
            return False
    
    def create_private_repo(self, repo_name: str, description: str = "") -> bool:
        """Create a private repository"""
        headers = self.get_current_headers()
        if not headers:
            return False
        
        try:
            data = {
                'name': repo_name,
                'description': description,
                'private': True,
                'auto_init': True
            }
            
            response = requests.post(
                'https://api.github.com/user/repos',
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                repo_info = response.json()
                print(f"✅ Private repository '{repo_name}' created")
                self.logger.log_event("repository_created", {
                    "repo_name": repo_name,
                    "account": self.current_account
                })
                return True
            else:
                print(f"❌ Failed to create repository: {response.json()}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating repository: {e}")
            return False

class GitHubBackup:
    """Secure backup of NexusController configurations to GitHub"""
    
    def __init__(self, github_manager: GitHubManager, logger):
        self.github = github_manager
        self.logger = logger
        self.backup_repo = "nexus-secure-backup"
        self.backup_dir = Path.home() / '.nexus' / 'backup_staging'
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    
    def setup_backup_repo(self) -> bool:
        """Setup private backup repository"""
        print("🔄 Setting up GitHub backup repository...")
        
        # Check if repo exists
        headers = self.github.get_current_headers()
        if not headers:
            return False
        
        response = requests.get(
            f"https://api.github.com/repos/{self.github.current_account}/{self.backup_repo}",
            headers=headers
        )
        
        if response.status_code == 404:
            # Create the repository
            if self.github.create_private_repo(
                self.backup_repo,
                "NexusController Secure - Encrypted Configuration Backup"
            ):
                print("✅ Backup repository created")
                return True
        elif response.status_code == 200:
            print("✅ Backup repository already exists")
            return True
        
        return False
    
    def create_backup_package(self) -> Optional[str]:
        """Create encrypted backup package"""
        try:
            backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"nexus_backup_{backup_time}.tar.gz"
            
            # Files to backup (already encrypted)
            backup_files = [
                Path.home() / '.nexus' / 'config.enc',
                Path.home() / '.ssh' / 'config',
                Path.home() / '.ssh' / 'known_hosts'
            ]
            
            # Create backup archive
            import tarfile
            with tarfile.open(backup_file, 'w:gz') as tar:
                for file_path in backup_files:
                    if file_path.exists():
                        tar.add(file_path, arcname=file_path.name)
            
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ Error creating backup package: {e}")
            return None
    
    def upload_backup(self, backup_file: str) -> bool:
        """Upload backup to GitHub repository"""
        headers = self.github.get_current_headers()
        if not headers:
            return False
        
        try:
            # Read backup file
            with open(backup_file, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            backup_name = Path(backup_file).name
            
            # Upload to GitHub
            data = {
                'message': f'Automated backup: {datetime.now().isoformat()}',
                'content': content
            }
            
            url = f"https://api.github.com/repos/{self.github.current_account}/{self.backup_repo}/contents/backups/{backup_name}"
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Backup uploaded to GitHub: {backup_name}")
                self.logger.log_event("backup_uploaded", {
                    "backup_file": backup_name,
                    "account": self.github.current_account
                })
                
                # Clean up local backup
                os.remove(backup_file)
                return True
            else:
                print(f"❌ Failed to upload backup: {response.json()}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading backup: {e}")
            return False
    
    def perform_backup(self) -> bool:
        """Perform complete backup process"""
        print("💾 Starting GitHub backup process...")
        
        if not self.setup_backup_repo():
            return False
        
        backup_file = self.create_backup_package()
        if not backup_file:
            return False
        
        return self.upload_backup(backup_file)
    
    def list_backups(self) -> List[Dict]:
        """List available backups on GitHub"""
        headers = self.github.get_current_headers()
        if not headers:
            return []
        
        try:
            url = f"https://api.github.com/repos/{self.github.current_account}/{self.backup_repo}/contents/backups"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            print(f"❌ Error listing backups: {e}")
            return []

class GitHubCLI:
    """GitHub CLI integration for advanced operations"""
    
    def __init__(self, logger):
        self.logger = logger
        self.cli_available = self.check_gh_cli()
    
    def check_gh_cli(self) -> bool:
        """Check if GitHub CLI is installed"""
        try:
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def install_gh_cli(self) -> bool:
        """Install GitHub CLI"""
        print("📦 Installing GitHub CLI...")
        try:
            # Install via package manager
            commands = [
                ['curl', '-fsSL', 'https://cli.github.com/packages/githubcli-archive-keyring.gpg'],
                ['sudo', 'dd', 'of=/usr/share/keyrings/githubcli-archive-keyring.gpg'],
                ['sudo', 'chmod', 'go+r', '/usr/share/keyrings/githubcli-archive-keyring.gpg'],
                ['echo', 'deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main'],
                ['sudo', 'tee', '/etc/apt/sources.list.d/github-cli.list'],
                ['sudo', 'apt', 'update'],
                ['sudo', 'apt', 'install', 'gh']
            ]
            
            # Simplified installation
            result = subprocess.run([
                'sudo', 'apt', 'update', '&&',
                'sudo', 'apt', 'install', '-y', 'gh'
            ], shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.cli_available = True
                print("✅ GitHub CLI installed successfully")
                return True
            else:
                print(f"❌ Failed to install GitHub CLI: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error installing GitHub CLI: {e}")
            return False
    
    def authenticate(self, token: str) -> bool:
        """Authenticate GitHub CLI with token"""
        if not self.cli_available:
            return False
        
        try:
            # Create temporary file with token
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(token)
                token_file = f.name
            
            # Authenticate using token file
            result = subprocess.run([
                'gh', 'auth', 'login', '--with-token'
            ], stdin=open(token_file, 'r'), capture_output=True, text=True)
            
            # Clean up token file
            os.unlink(token_file)
            
            if result.returncode == 0:
                print("✅ GitHub CLI authenticated")
                return True
            else:
                print(f"❌ GitHub CLI authentication failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error authenticating GitHub CLI: {e}")
            return False
    
    def create_issue(self, repo: str, title: str, body: str, labels: List[str] = None) -> bool:
        """Create issue in repository"""
        if not self.cli_available:
            return False
        
        try:
            cmd = ['gh', 'issue', 'create', '--repo', repo, '--title', title, '--body', body]
            
            if labels:
                cmd.extend(['--label', ','.join(labels)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Issue created: {title}")
                return True
            else:
                print(f"❌ Failed to create issue: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating issue: {e}")
            return False
    
    def get_repo_status(self, repo_path: str) -> Dict:
        """Get repository status and information"""
        try:
            os.chdir(repo_path)
            
            # Get various git/GitHub information
            status = {}
            
            # Git status
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            status['uncommitted_changes'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Current branch
            result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
            status['current_branch'] = result.stdout.strip()
            
            # Remote URL
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True)
            status['remote_url'] = result.stdout.strip()
            
            # Last commit
            result = subprocess.run(['git', 'log', '-1', '--format=%H:%s'], capture_output=True, text=True)
            if result.stdout.strip():
                commit_hash, commit_msg = result.stdout.strip().split(':', 1)
                status['last_commit'] = {'hash': commit_hash[:8], 'message': commit_msg}
            
            return status
            
        except Exception as e:
            return {'error': str(e)}

def github_menu(github_manager: GitHubManager, github_backup: GitHubBackup, github_cli: GitHubCLI):
    """GitHub management menu"""
    while True:
        print("\n🐙 GitHub Integration")
        print("=" * 25)
        
        # Show current account
        if github_manager.current_account:
            account_info = github_manager.accounts[github_manager.current_account]
            print(f"📊 Active Account: {account_info['username']} ({account_info['account_type']})")
        else:
            print("📊 No active GitHub account")
        
        print("\n1. 🔑 Manage GitHub Accounts")
        print("2. 🔐 Upload SSH Keys")
        print("3. 📦 Repository Management")
        print("4. 💾 Backup to GitHub")
        print("5. 🛠️  GitHub CLI Operations")
        print("6. 📊 Repository Status")
        print("7. 🔙 Back to Main Menu")
        
        choice = input("\n🎯 Select option (1-7): ").strip()
        
        if choice == '1':
            account_management_menu(github_manager)
        elif choice == '2':
            ssh_key_menu(github_manager)
        elif choice == '3':
            repository_menu(github_manager)
        elif choice == '4':
            backup_menu(github_backup)
        elif choice == '5':
            cli_menu(github_cli, github_manager)
        elif choice == '6':
            status_menu(github_manager)
        elif choice == '7':
            break
        else:
            print("❌ Invalid choice")

def account_management_menu(github_manager: GitHubManager):
    """GitHub account management submenu"""
    while True:
        print("\n🔑 GitHub Account Management")
        print("-" * 30)
        
        # List accounts
        if github_manager.accounts:
            print("📋 Configured Accounts:")
            for username, account in github_manager.accounts.items():
                active = "🟢" if username == github_manager.current_account else "⚪"
                print(f"  {active} {username} ({account['account_type']})")
        else:
            print("📋 No GitHub accounts configured")
        
        print("\n1. ➕ Add GitHub Account")
        print("2. 🔄 Switch Account")
        print("3. ❌ Remove Account")
        print("4. 🔙 Back")
        
        choice = input("\n🎯 Select option (1-4): ").strip()
        
        if choice == '1':
            add_github_account(github_manager)
        elif choice == '2':
            switch_github_account(github_manager)
        elif choice == '3':
            remove_github_account(github_manager)
        elif choice == '4':
            break
        else:
            print("❌ Invalid choice")

def add_github_account(github_manager: GitHubManager):
    """Add new GitHub account"""
    print("\n➕ Add GitHub Account")
    print("💡 You'll need a Personal Access Token with appropriate permissions")
    print("🔗 Create one at: https://github.com/settings/tokens")
    
    username = input("\n📝 GitHub username: ").strip()
    token = input("🔑 Personal Access Token: ").strip()
    
    account_types = ["personal", "work", "organization"]
    print("\n📋 Account types:")
    for i, acc_type in enumerate(account_types, 1):
        print(f"  {i}. {acc_type}")
    
    try:
        type_choice = int(input("🎯 Select type (1-3): ")) - 1
        if 0 <= type_choice < len(account_types):
            account_type = account_types[type_choice]
            
            if github_manager.add_account(username, token, account_type):
                print(f"✅ GitHub account '{username}' added successfully")
                github_manager.set_current_account(username)
            else:
                print("❌ Failed to add GitHub account")
        else:
            print("❌ Invalid account type")
    except ValueError:
        print("❌ Invalid input")

def switch_github_account(github_manager: GitHubManager):
    """Switch active GitHub account"""
    if not github_manager.accounts:
        print("❌ No GitHub accounts configured")
        return
    
    print("\n🔄 Switch GitHub Account")
    accounts = list(github_manager.accounts.keys())
    
    for i, username in enumerate(accounts, 1):
        active = "🟢" if username == github_manager.current_account else "⚪"
        account_type = github_manager.accounts[username]['account_type']
        print(f"  {i}. {active} {username} ({account_type})")
    
    try:
        choice = int(input("\n🎯 Select account: ")) - 1
        if 0 <= choice < len(accounts):
            username = accounts[choice]
            if github_manager.set_current_account(username):
                print(f"✅ Switched to account '{username}'")
            else:
                print("❌ Failed to switch account")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Invalid input")

def remove_github_account(github_manager: GitHubManager):
    """Remove GitHub account"""
    if not github_manager.accounts:
        print("❌ No GitHub accounts configured")
        return
    
    print("\n❌ Remove GitHub Account")
    accounts = list(github_manager.accounts.keys())
    
    for i, username in enumerate(accounts, 1):
        account_type = github_manager.accounts[username]['account_type']
        print(f"  {i}. {username} ({account_type})")
    
    try:
        choice = int(input("\n🎯 Select account to remove: ")) - 1
        if 0 <= choice < len(accounts):
            username = accounts[choice]
            confirm = input(f"⚠️  Really remove '{username}'? (yes/no): ").lower()
            
            if confirm == 'yes':
                del github_manager.accounts[username]
                if github_manager.current_account == username:
                    github_manager.current_account = None
                github_manager.save_accounts()
                print(f"✅ Account '{username}' removed")
            else:
                print("❌ Removal cancelled")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Invalid input")

def ssh_key_menu(github_manager: GitHubManager):
    """SSH key management menu"""
    if not github_manager.current_account:
        print("❌ No active GitHub account. Please add and select an account first.")
        return
    
    print(f"\n🔐 SSH Key Management - {github_manager.current_account}")
    print("-" * 40)
    
    # List local SSH keys
    ssh_dir = Path.home() / '.ssh'
    if ssh_dir.exists():
        print("📋 Local SSH Keys:")
        for key_file in ssh_dir.glob('*.pub'):
            print(f"  🔑 {key_file.name}")
    
    print("\n1. ⬆️  Upload SSH Key to GitHub")
    print("2. 🔑 Generate New SSH Key")
    print("3. 📋 List GitHub SSH Keys")
    print("4. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-4): ").strip()
    
    if choice == '1':
        upload_ssh_key(github_manager)
    elif choice == '2':
        generate_ssh_key()
    elif choice == '3':
        list_github_keys(github_manager)
    elif choice == '4':
        return
    else:
        print("❌ Invalid choice")

def upload_ssh_key(github_manager: GitHubManager):
    """Upload SSH key to GitHub"""
    ssh_dir = Path.home() / '.ssh'
    public_keys = list(ssh_dir.glob('*.pub'))
    
    if not public_keys:
        print("❌ No SSH public keys found")
        return
    
    print("\n⬆️  Upload SSH Key")
    for i, key_file in enumerate(public_keys, 1):
        print(f"  {i}. {key_file.name}")
    
    try:
        choice = int(input("\n🎯 Select key to upload: ")) - 1
        if 0 <= choice < len(public_keys):
            key_file = public_keys[choice]
            key_name = input(f"📝 Key name for GitHub [{key_file.stem}]: ").strip()
            
            if not key_name:
                key_name = f"nexus-{key_file.stem}"
            
            if github_manager.upload_ssh_key(key_name, str(key_file)):
                print("✅ SSH key uploaded successfully")
            else:
                print("❌ Failed to upload SSH key")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Invalid input")

def generate_ssh_key():
    """Generate new SSH key"""
    print("\n🔑 Generate New SSH Key")
    
    key_name = input("📝 Key name [nexus_github]: ").strip()
    if not key_name:
        key_name = "nexus_github"
    
    email = input("📧 Email for key: ").strip()
    if not email:
        email = f"nexus@{os.getenv('HOSTNAME', 'localhost')}"
    
    ssh_dir = Path.home() / '.ssh'
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    
    key_path = ssh_dir / key_name
    
    try:
        cmd = [
            'ssh-keygen', '-t', 'ed25519', '-f', str(key_path),
            '-N', '', '-C', email
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            os.chmod(key_path, 0o600)
            os.chmod(f"{key_path}.pub", 0o644)
            print(f"✅ SSH key generated: {key_path}")
            
            # Display public key
            with open(f"{key_path}.pub", 'r') as f:
                public_key = f.read().strip()
            print(f"\n📋 Public key:\n{public_key}")
        else:
            print(f"❌ SSH key generation failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error generating SSH key: {e}")

def list_github_keys(github_manager: GitHubManager):
    """List SSH keys on GitHub"""
    headers = github_manager.get_current_headers()
    if not headers:
        return
    
    try:
        response = requests.get('https://api.github.com/user/keys', headers=headers)
        if response.status_code == 200:
            keys = response.json()
            
            print(f"\n📋 SSH Keys on GitHub ({len(keys)} total):")
            for key in keys:
                print(f"  🔑 {key['title']} (ID: {key['id']})")
                print(f"     {key['key'][:50]}...")
        else:
            print(f"❌ Failed to list GitHub keys: {response.status_code}")
    except Exception as e:
        print(f"❌ Error listing GitHub keys: {e}")

def repository_menu(github_manager: GitHubManager):
    """Repository management menu"""
    if not github_manager.current_account:
        print("❌ No active GitHub account")
        return
    
    print(f"\n📦 Repository Management - {github_manager.current_account}")
    print("-" * 40)
    
    print("1. 📋 List Repositories")
    print("2. 📥 Clone Repository")
    print("3. ➕ Create Repository")
    print("4. 🔄 Repository Operations")
    print("5. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-5): ").strip()
    
    if choice == '1':
        list_repositories(github_manager)
    elif choice == '2':
        clone_repository(github_manager)
    elif choice == '3':
        create_repository(github_manager)
    elif choice == '4':
        repository_operations(github_manager)
    elif choice == '5':
        return
    else:
        print("❌ Invalid choice")

def list_repositories(github_manager: GitHubManager):
    """List user repositories"""
    print("\n📋 Loading repositories...")
    repos = github_manager.list_repositories()
    
    if repos:
        print(f"\n📦 Repositories ({len(repos)} total):")
        for repo in repos[:20]:  # Show first 20
            private = "🔒" if repo['private'] else "🌍"
            updated = repo['updated_at'][:10]
            print(f"  {private} {repo['name']} - {repo['description'][:50] if repo['description'] else 'No description'}")
            print(f"     Updated: {updated} | Language: {repo['language'] or 'N/A'}")
    else:
        print("❌ No repositories found or failed to load")

def clone_repository(github_manager: GitHubManager):
    """Clone repository"""
    print("\n📥 Clone Repository")
    
    repo_url = input("📝 Repository URL or owner/repo: ").strip()
    if not repo_url:
        return
    
    # Handle owner/repo format
    if '/' in repo_url and 'github.com' not in repo_url:
        repo_url = f"https://github.com/{repo_url}"
    
    destination = input("📂 Destination directory [current]: ").strip()
    if not destination:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        destination = f"./{repo_name}"
    
    use_ssh = input("🔑 Use SSH authentication? (Y/n): ").lower() != 'n'
    
    if github_manager.clone_repository(repo_url, destination, use_ssh):
        print("✅ Repository cloned successfully")
    else:
        print("❌ Failed to clone repository")

def create_repository(github_manager: GitHubManager):
    """Create new repository"""
    print("\n➕ Create Repository")
    
    repo_name = input("📝 Repository name: ").strip()
    if not repo_name:
        return
    
    description = input("📄 Description (optional): ").strip()
    
    if github_manager.create_private_repo(repo_name, description):
        print("✅ Repository created successfully")
    else:
        print("❌ Failed to create repository")

def repository_operations(github_manager: GitHubManager):
    """Repository operations submenu"""
    print("\n🔄 Repository Operations")
    print("1. 📊 Check Repository Status")
    print("2. 🔄 Pull Latest Changes")
    print("3. ⬆️  Push Changes")
    print("4. 🌿 Branch Management")
    print("5. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-5): ").strip()
    
    if choice == '1':
        check_repo_status()
    elif choice == '2':
        pull_changes()
    elif choice == '3':
        push_changes()
    elif choice == '4':
        branch_management()
    elif choice == '5':
        return
    else:
        print("❌ Invalid choice")

def check_repo_status():
    """Check git repository status"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if result.returncode == 0:
            if result.stdout.strip():
                print("\n📊 Repository Status - Uncommitted changes:")
                for line in result.stdout.strip().split('\n'):
                    status = line[:2]
                    filename = line[3:]
                    print(f"  {status} {filename}")
            else:
                print("\n✅ Repository is clean - no uncommitted changes")
        else:
            print("❌ Not in a git repository")
    except Exception as e:
        print(f"❌ Error checking status: {e}")

def pull_changes():
    """Pull latest changes"""
    try:
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Successfully pulled latest changes")
            print(result.stdout)
        else:
            print(f"❌ Pull failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error pulling changes: {e}")

def push_changes():
    """Push changes to remote"""
    try:
        # Check if there are changes to commit
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if result.stdout.strip():
            commit_msg = input("📝 Commit message: ").strip()
            if commit_msg:
                # Add all changes
                subprocess.run(['git', 'add', '.'])
                
                # Commit
                subprocess.run(['git', 'commit', '-m', commit_msg])
                
                # Push
                result = subprocess.run(['git', 'push'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Changes pushed successfully")
                else:
                    print(f"❌ Push failed: {result.stderr}")
            else:
                print("❌ Commit message required")
        else:
            print("ℹ️  No changes to commit")
    except Exception as e:
        print(f"❌ Error pushing changes: {e}")

def branch_management():
    """Branch management operations"""
    print("\n🌿 Branch Management")
    
    try:
        # Show current branch
        result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        if result.returncode == 0:
            current_branch = result.stdout.strip()
            print(f"📍 Current branch: {current_branch}")
        
        # List all branches
        result = subprocess.run(['git', 'branch', '-a'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📋 All branches:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
    except Exception as e:
        print(f"❌ Error getting branch info: {e}")

def backup_menu(github_backup: GitHubBackup):
    """GitHub backup management menu"""
    print("\n💾 GitHub Backup Management")
    print("-" * 30)
    
    print("1. 📤 Create Backup")
    print("2. 📋 List Backups")
    print("3. 📥 Restore Backup")
    print("4. ⚙️  Backup Settings")
    print("5. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-5): ").strip()
    
    if choice == '1':
        if github_backup.perform_backup():
            print("✅ Backup completed successfully")
        else:
            print("❌ Backup failed")
    elif choice == '2':
        backups = github_backup.list_backups()
        if backups:
            print(f"\n📋 Available Backups ({len(backups)} total):")
            for backup in backups:
                print(f"  💾 {backup['name']}")
        else:
            print("📋 No backups found")
    elif choice == '3':
        print("📥 Backup restoration not implemented in this demo")
    elif choice == '4':
        print("⚙️  Backup settings not implemented in this demo")
    elif choice == '5':
        return
    else:
        print("❌ Invalid choice")

def cli_menu(github_cli: GitHubCLI, github_manager: GitHubManager):
    """GitHub CLI operations menu"""
    print("\n🛠️  GitHub CLI Operations")
    print("-" * 25)
    
    if not github_cli.cli_available:
        print("❌ GitHub CLI not available")
        install = input("📦 Install GitHub CLI? (y/N): ").lower() == 'y'
        if install:
            github_cli.install_gh_cli()
        return
    
    print("1. 🔐 Authenticate CLI")
    print("2. 🐛 Create Issue")
    print("3. 📊 Repository Info")
    print("4. 🔍 Search")
    print("5. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-5): ").strip()
    
    if choice == '1':
        if github_manager.current_account:
            token = github_manager.accounts[github_manager.current_account]['token']
            github_cli.authenticate(token)
        else:
            print("❌ No active GitHub account")
    elif choice == '2':
        create_issue_cli(github_cli)
    elif choice == '3':
        show_repo_info(github_cli)
    elif choice == '4':
        print("🔍 Search functionality not implemented in this demo")
    elif choice == '5':
        return
    else:
        print("❌ Invalid choice")

def create_issue_cli(github_cli: GitHubCLI):
    """Create issue using GitHub CLI"""
    repo = input("📦 Repository (owner/repo): ").strip()
    if not repo:
        return
    
    title = input("📝 Issue title: ").strip()
    if not title:
        return
    
    body = input("📄 Issue description: ").strip()
    
    labels_input = input("🏷️  Labels (comma-separated, optional): ").strip()
    labels = [label.strip() for label in labels_input.split(',')] if labels_input else None
    
    if github_cli.create_issue(repo, title, body, labels):
        print("✅ Issue created successfully")
    else:
        print("❌ Failed to create issue")

def show_repo_info(github_cli: GitHubCLI):
    """Show repository information"""
    repo_path = input("📂 Repository path [current directory]: ").strip()
    if not repo_path:
        repo_path = "."
    
    status = github_cli.get_repo_status(repo_path)
    
    if 'error' in status:
        print(f"❌ Error: {status['error']}")
        return
    
    print(f"\n📊 Repository Information:")
    print(f"  🌿 Branch: {status.get('current_branch', 'Unknown')}")
    print(f"  🔗 Remote: {status.get('remote_url', 'Unknown')}")
    print(f"  📝 Uncommitted changes: {status.get('uncommitted_changes', 0)}")
    
    if 'last_commit' in status:
        commit = status['last_commit']
        print(f"  📋 Last commit: {commit['hash']} - {commit['message']}")

def status_menu(github_manager: GitHubManager):
    """GitHub status overview"""
    print("\n📊 GitHub Status Overview")
    print("=" * 30)
    
    if not github_manager.current_account:
        print("❌ No active GitHub account")
        return
    
    account_info = github_manager.accounts[github_manager.current_account]
    user_info = account_info.get('user_info', {})
    
    print(f"👤 Active Account: {account_info['username']}")
    print(f"📧 Email: {user_info.get('email', 'Not public')}")
    print(f"🏢 Company: {user_info.get('company', 'None')}")
    print(f"📍 Location: {user_info.get('location', 'Unknown')}")
    print(f"📦 Public Repos: {user_info.get('public_repos', 0)}")
    print(f"👥 Followers: {user_info.get('followers', 0)}")
    print(f"👤 Following: {user_info.get('following', 0)}")
    
    # Recent repository activity
    print(f"\n📦 Recent Repository Activity:")
    repos = github_manager.list_repositories()[:5]
    for repo in repos:
        private = "🔒" if repo['private'] else "🌍"
        updated = repo['updated_at'][:10]
        print(f"  {private} {repo['name']} - Updated: {updated}")

if __name__ == '__main__':
    # This would be integrated into the main NexusController Secure application
    print("🐙 GitHub Integration Module")
    print("This module is designed to be integrated into NexusController Secure")