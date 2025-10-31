# Manual Server Setup Instructions

## Your fresh Ubuntu Server is ready at: `ebon@10.0.0.29`

### Step 1: Connect via Terminal
Open a **new terminal window** (outside of Claude) and run:

```bash
ssh ebon@10.0.0.29
```
Enter the password you set during Ubuntu installation.

### Step 2: Copy SSH Key (from Skippy)
In another terminal on Skippy, run:
```bash
ssh-copy-id ebon@10.0.0.29
```
Enter the password when prompted.

### Step 3: Test SSH Key
```bash
ssh ebon@10.0.0.29 "echo 'SSH key working!'"
```
Should connect without password.

### Step 4: Initial Server Setup
SSH to the server and run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git htop vim ufw tree ncdu docker.io

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8080
sudo ufw allow 80
sudo ufw allow 443

# Add user to docker group
sudo usermod -aG docker $USER

# Check system status
hostnamectl
free -h
df -h
```

### Step 5: Copy Home Server Master Files
From Skippy terminal:
```bash
scp -r ~/Skippy/* ebon@10.0.0.29:/tmp/home-server/
```

### Step 6: Install Home Server Master
SSH to server:
```bash
ssh ebon@10.0.0.29
cd /tmp/home-server
chmod +x home_server_installer.sh
./home_server_installer.sh
```

### Step 7: Access Your Server
- **Web Interface**: http://10.0.0.29:8080
- **SSH**: ssh ebon@10.0.0.29
- **Local**: http://ebon-eth.local:8080

## Quick One-Liner Setup
Once SSH key is working, you can run this all at once:

```bash
ssh ebon@10.0.0.29 "
sudo apt update && sudo apt upgrade -y && \
sudo apt install -y curl wget git htop vim ufw tree ncdu docker.io && \
sudo ufw enable --force && \
sudo ufw allow ssh && sudo ufw allow 8080 && sudo ufw allow 80 && sudo ufw allow 443 && \
sudo usermod -aG docker \$USER && \
echo 'Server setup complete!'
"
```

## After Setup
Your HP Z4 G4 will be a powerful Ubuntu Server ready for:
- ✅ Home Server Master unified management
- ✅ Docker containers and services  
- ✅ Ethereum node hosting
- ✅ Cloud sync and backup
- ✅ Web services and monitoring

The clean Ubuntu Server installation on enterprise hardware will be perfect for all your home server needs!