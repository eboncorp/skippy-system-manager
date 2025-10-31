#!/bin/bash
# Comprehensive Ethereum Node Setup Script for Ubuntu with improved error checking and logging
set -euo pipefail

# Set variables
TARGET_DISK="/dev/nvme0n1"
MOUNT_POINT="/mnt/ethereum_node"
HOSTNAME="ebon-eth"
USERNAME="dave"
SSH_PORT=2222
EMAIL="eboncorp@gmail.com"
DOMAIN="eboneth.ddns.net"
LOG_FILE="/tmp/ethereum_node_setup.log"
CHROOT_LOG_FILE="/tmp/chroot_script.log"
ETHEREUM_NETWORK="mainnet"
GETH_DATA_DIR="/var/lib/goethereum"
BACKUP_DIR="/var/backups/ethereum"
NOIP_USERNAME="eboncorp"
NOIP_PASSWORD="REDACTED_SERVER_PASSWORD"  # Replace this with your actual No-IP password

# Function to log messages
log_message() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

# Function to check command success
check_command() {
    if [ $? -ne 0 ]; then
        log_message "Error: $1"
        exit 1
    fi
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    local line_number=${1:-"unknown"}
    log_message "Error occurred at line $line_number. Exit code: $exit_code"
    log_message "Cleaning up..."
    umount -R "$MOUNT_POINT" || true
    exit $exit_code
}

# Trap to catch and log errors
trap 'handle_error $LINENO' ERR
# Progress indicator functions
show_progress() {
    echo -n "$1... "
}

finish_progress() {
    echo "Done"
}

# Trap to catch and log errors
trap 'handle_error $LINENO' ERR

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
   log_message "This script must be run as root" 
   exit 1
fi

# Check for required commands
for cmd in parted mkfs.ext4 mkfs.fat debootstrap blkid; do
    if ! command -v $cmd &> /dev/null; then
        log_message "Error: $cmd is required but not installed. Aborting."
        exit 1
    fi
done

# Check internet connectivity
if ! ping -c 1 google.com &> /dev/null; then
    log_message "No internet connectivity. Please check your connection and try again."
    exit 1
fi

# Check for sufficient disk space
log_message "Checking disk space..."
TOTAL_SPACE=$(lsblk -bdno SIZE "${TARGET_DISK}" | numfmt --to=iec --format="%.0f")
TOTAL_SPACE_GB=$(echo "${TOTAL_SPACE}" | sed 's/G//')

log_message "Debug: Detected total space: ${TOTAL_SPACE} (${TOTAL_SPACE_GB}GB) on ${TARGET_DISK}"

if [ "${TOTAL_SPACE_GB}" -lt 100 ]; then
    log_message "Error: Insufficient disk space. At least 100GB is required, and 500GB or more is recommended."
    exit 1
elif [ "${TOTAL_SPACE_GB}" -lt 500 ]; then
    log_message "Warning: Less than 500GB of total disk space. This may impact performance or future upgrades."
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_message "Operation cancelled by user due to insufficient disk space"
        exit 1
    fi
else
    log_message "Sufficient disk space available: ${TOTAL_SPACE}"
fi

# Confirmation prompt
echo "This script will partition and format ${TARGET_DISK}."
echo "All data on ${TARGET_DISK} will be lost."
read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_message "Operation cancelled by user"
    exit 1
fi

# Main script starts here
log_message "Starting Ethereum node setup script"

# Update and install necessary packages
show_progress "Updating and installing necessary packages"
apt update && apt install -y debootstrap
finish_progress

# Unmount any existing partitions on the target disk
log_message "Unmounting any existing partitions on $TARGET_DISK..."
for mount in $(mount | grep "$TARGET_DISK" | awk '{ print $3 }' | sort -r); do
    log_message "Attempting to unmount $mount"
    if umount -l "$mount"; then
        log_message "Successfully unmounted $mount"
    else
        log_message "Failed to unmount $mount, but continuing..."
    fi
done

# Double check if any partitions are still mounted
if mount | grep "$TARGET_DISK" > /dev/null; then
    log_message "Warning: Some partitions on $TARGET_DISK are still mounted. Proceeding anyway..."
else
    log_message "All partitions on $TARGET_DISK have been unmounted"
fi

# Ensure the mount point is clear
if [ -d "$MOUNT_POINT" ]; then
    log_message "Removing existing mount point directory..."
    rm -rf "$MOUNT_POINT"
fi
mkdir -p "$MOUNT_POINT"

# Partition and format the disk
show_progress "Partitioning and formatting $TARGET_DISK"
parted -s "$TARGET_DISK" mklabel gpt
parted -s "$TARGET_DISK" mkpart primary fat32 1MiB 512MiB
parted -s "$TARGET_DISK" set 1 esp on
parted -s "$TARGET_DISK" mkpart primary ext4 512MiB 100%
finish_progress

# Update the kernel's partition table
log_message "Updating partition table..."
partprobe "$TARGET_DISK"

# Wait for a moment to ensure the new partitions are recognized
sleep 5

# Format partitions
show_progress "Formatting partitions"
mkfs.fat -F32 "${TARGET_DISK}p1"
mkfs.ext4 "${TARGET_DISK}p2"
finish_progress

# Mount the target system
show_progress "Mounting partitions"
mount "${TARGET_DISK}p2" "$MOUNT_POINT"
mkdir -p "$MOUNT_POINT/boot/efi"
mount "${TARGET_DISK}p1" "$MOUNT_POINT/boot/efi"
finish_progress

# Install the base system
show_progress "Installing base system"
debootstrap --arch amd64 focal "$MOUNT_POINT" http://archive.ubuntu.com/ubuntu
finish_progress

# Generate fstab
log_message "Generating fstab..."
mkdir -p "$MOUNT_POINT/etc"
{
    echo "# /etc/fstab: static file system information."
    echo "# Use 'blkid' to print the universally unique identifier for a device."
    echo "#"
    echo "# <file system>             <mount point>   <type>  <options>       <dump>  <pass>"
    echo "UUID=$(blkid -s UUID -o value ${TARGET_DISK}p2) /               ext4    errors=remount-ro 0       1"
    echo "UUID=$(blkid -s UUID -o value ${TARGET_DISK}p1) /boot/efi       vfat    umask=0077      0       1"
    echo "/swapfile                   none            swap    sw              0       0"
} > "$MOUNT_POINT/etc/fstab"

# Create a swapfile
show_progress "Creating swapfile"
dd if=/dev/zero of="$MOUNT_POINT/swapfile" bs=1M count=4096
chmod 600 "$MOUNT_POINT/swapfile"
mkswap "$MOUNT_POINT/swapfile"
finish_progress

# Prepare chroot environment
show_progress "Preparing chroot environment"
mount -t proc /proc "$MOUNT_POINT/proc"
mount --rbind /sys "$MOUNT_POINT/sys"
mount --make-rslave "$MOUNT_POINT/sys"
mount --rbind /dev "$MOUNT_POINT/dev"
mount --make-rslave "$MOUNT_POINT/dev"
cp /etc/resolv.conf "$MOUNT_POINT/etc/resolv.conf"
finish_progress

# Create the post-installation script
# Function to handle errors
handle_error() {
    local exit_code=$?
    local line_number=${1:-"unknown"}
    log_message "Error occurred at line $line_number. Exit code: $exit_code"
    log_message "Cleaning up..."
    umount -R "$MOUNT_POINT" || true
    exit $exit_code
}

# Trap to catch and log errors
trap 'handle_error $LINENO' ERR
log_message "Creating post-installation script..."
cat > "$MOUNT_POINT/root/post_install.sh" << EOL
#!/bin/bash
set -euo pipefail

# Redirect output to log file
exec > >(tee -a "$CHROOT_LOG_FILE") 2>&1

# Set variables
HOSTNAME="${HOSTNAME}"
USERNAME="${USERNAME}"
SSH_PORT=${SSH_PORT}
EMAIL="${EMAIL}"
DOMAIN="${DOMAIN}"
GETH_DATA_DIR="${GETH_DATA_DIR}"
BACKUP_DIR="${BACKUP_DIR}"
NOIP_USERNAME="${NOIP_USERNAME}"
NOIP_PASSWORD="${NOIP_PASSWORD}"

echo "Starting post-installation script..."

# ... (rest of the post-installation script)
EOL
# Set up system
echo "Setting up system..."
ln -sf /usr/share/zoneinfo/UTC /etc/localtime
dpkg-reconfigure -f noninteractive tzdata
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
echo \$HOSTNAME > /etc/hostname

# Function to check command success
check_command() {
    if [ $? -ne 0 ]; then
        echo "Error: $1"
        return 1
    fi
    return 0
}

# Debug information
echo "Debug: Current Ubuntu version:"
cat /etc/os-release

echo "Debug: Available package sources before modifications:"
cat /etc/apt/sources.list
ls -l /etc/apt/sources.list.d/
# Update sources.list to use online repositories
log_message "Updating sources.list..."
cat > "$MOUNT_POINT/etc/apt/sources.list" << EOL
deb http://archive.ubuntu.com/ubuntu jammy main restricted
deb http://archive.ubuntu.com/ubuntu jammy-updates main restricted
deb http://archive.ubuntu.com/ubuntu jammy universe
deb http://archive.ubuntu.com/ubuntu jammy-updates universe
deb http://archive.ubuntu.com/ubuntu jammy multiverse
deb http://archive.ubuntu.com/ubuntu jammy-updates multiverse
deb http://archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu jammy-security main restricted
deb http://security.ubuntu.com/ubuntu jammy-security universe
deb http://security.ubuntu.com/ubuntu jammy-security multiverse
EOL

# Update and install packages
echo "Updating and installing packages..."
chroot "$MOUNT_POINT" apt update
check_command "Initial apt update failed" || exit 1

# Install software-properties-common for add-apt-repository
chroot "$MOUNT_POINT" apt install -y software-properties-common
check_command "Failed to install software-properties-common" || exit 1

# Add Grafana repository manually
log_message "Adding Grafana repository..."
chroot "$MOUNT_POINT" /bin/bash -c 'echo "deb https://packages.grafana.com/oss/deb stable main" | tee /etc/apt/sources.list.d/grafana.list'
chroot "$MOUNT_POINT" wget -q -O - https://packages.grafana.com/gpg.key | chroot "$MOUNT_POINT" apt-key add -
check_command "Failed to add Grafana repository" || exit 1

# Update again after adding new repositories
chroot "$MOUNT_POINT" apt update
check_command "apt update after adding repositories failed" || exit 1

# Install packages
chroot "$MOUNT_POINT" apt install -y linux-image-generic grub-efi-amd64 ubuntu-standard \
    curl git ufw unattended-upgrades apt-listchanges
check_command "Failed to install core packages" || exit 1

# Install fail2ban
chroot "$MOUNT_POINT" apt install -y fail2ban || log_message "Warning: fail2ban installation failed, continuing..."

# Install Prometheus and related packages
chroot "$MOUNT_POINT" apt install -y prometheus prometheus-node-exporter || log_message "Warning: Prometheus installation failed, continuing..."

# Install Grafana
chroot "$MOUNT_POINT" apt install -y grafana || log_message "Warning: Grafana installation failed, continuing..."

# Install miniupnpc (libminiupnpc-dev as a replacement)
chroot "$MOUNT_POINT" apt install -y libminiupnpc-dev || log_message "Warning: libminiupnpc-dev installation failed, continuing..."

# Upgrade all packages
chroot "$MOUNT_POINT" apt upgrade -y
check_command "apt upgrade failed" || exit 1

echo "Package installation and upgrade completed successfully."

# Debug output
log_message "Debug: Content of /etc/apt/sources.list after modification:"
cat "$MOUNT_POINT/etc/apt/sources.list"

log_message "Debug: Content of /etc/apt/sources.list.d/ after adding Grafana repository:"
ls -l "$MOUNT_POINT/etc/apt/sources.list.d/"

log_message "Debug: APT update output:"
chroot "$MOUNT_POINT" apt update

log_message "Debug: Installed packages:"
chroot "$MOUNT_POINT" dpkg -l

# Configure automatic updates
echo "Configuring automatic updates..."
echo 'Unattended-Upgrade::Automatic-Reboot "true";' >> /etc/apt/apt.conf.d/50unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot-Time "02:00";' >> /etc/apt/apt.conf.d/50unattended-upgrades

# Install and configure GRUB
echo "Installing and configuring GRUB..."
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu
update-grub

# Create user and configure SSH
echo "Creating user and configuring SSH..."
useradd -m -s /bin/bash \$USERNAME
echo "\$USERNAME:\$(openssl rand -base64 12)" | chpasswd
usermod -aG sudo \$USERNAME
sed -i "s/#Port 22/Port \$SSH_PORT/" /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Set up firewall
echo "Setting up firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow \$SSH_PORT/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 30303/tcp
ufw allow 30303/udp
ufw --force enable

# Configure fail2ban
echo "Configuring fail2ban..."
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sed -i 's/bantime  = 10m/bantime  = 1h/' /etc/fail2ban/jail.local
sed -i 's/findtime  = 10m/findtime  = 20m/' /etc/fail2ban/jail.local
sed -i 's/maxretry = 5/maxretry = 3/' /etc/fail2ban/jail.local

# Install Geth
echo "Installing Geth..."
add-apt-repository -y ppa:ethereum/ethereum
apt update
apt install -y ethereum

# Create Geth systemd service
echo "Creating Geth systemd service..."
cat > /etc/systemd/system/geth.service <<EOLS
[Unit]
Description=Ethereum Go Client
After=network.target

[Service]
User=\$USERNAME
ExecStart=/usr/bin/geth --datadir \$GETH_DATA_DIR --http --http.addr 0.0.0.0 --http.vhosts=* --http.api eth,net,web3 --ws --ws.addr 0.0.0.0 --ws.origins=* --cache 16384 --maxpeers 50
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOLS

# Set up Geth data directory and log rotation
echo "Setting up Geth data directory and log rotation..."
mkdir -p \$GETH_DATA_DIR
chown -R \$USERNAME:\$USERNAME \$GETH_DATA_DIR
cat > /etc/logrotate.d/geth <<EOLS
\$GETH_DATA_DIR/geth.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 \$USERNAME \$USERNAME
}
EOLS

# Set up backup script and cron job
echo "Setting up backup script and cron job..."
mkdir -p \$BACKUP_DIR
cat > /usr/local/bin/backup-ethereum.sh <<EOLS
#!/bin/bash
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\$BACKUP_DIR/ethereum_backup_\\\$TIMESTAMP.tar.gz"
systemctl stop geth
tar -czf \\\$BACKUP_FILE \$GETH_DATA_DIR
systemctl start geth
find \$BACKUP_DIR -type f -mtime +30 -delete
EOLS
chmod +x /usr/local/bin/backup-ethereum.sh
echo "0 3 * * * root /usr/local/bin/backup-ethereum.sh" >> /etc/crontab

# Enable and start services
echo "Enabling and starting services..."
systemctl enable geth prometheus prometheus-node-exporter grafana-server

# Install and configure Certbot
echo "Installing and configuring Certbot..."
snap install core
snap refresh core
snap install --classic certbot
ln -s /snap/bin/certbot /usr/bin/certbot
certbot certonly --standalone -d \$DOMAIN --non-interactive --agree-tos -m \$EMAIL

# Set up Nginx as reverse proxy
echo "Setting up Nginx as reverse proxy..."
apt install -y nginx
cat > /etc/nginx/sites-available/geth <<EOLS
server {
    listen 443 ssl;
    server_name \$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/\$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/\$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://localhost:8545;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\\$host;
        proxy_cache_bypass \\\$http_upgrade;
    }
}
EOLS
ln -s /etc/nginx/sites-available/geth /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Set up automatic SSL renewal
echo "Setting up automatic SSL renewal..."
echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | tee -a /etc/crontab > /dev/null

# Install and configure No-IP Dynamic Update Client (DUC)
echo "Installing No-IP Dynamic Update Client..."
cd /home/\$USERNAME
wget --content-disposition https://www.noip.com/download/linux/latest
tar xf noip-duc_*.tar.gz
cd noip-duc_*/binaries
apt install -y ./noip-duc_*_amd64.deb

# Configure No-IP DUC
echo "Configuring No-IP DUC..."
noip-duc -g all.ddnskey.com --username "\$NOIP_USERNAME" --password "\$NOIP_PASSWORD" --hostnames "\$DOMAIN" --daemon

# Create a systemd service for No-IP DUC
echo "Creating systemd service for No-IP DUC..."
cat > /etc/systemd/system/noip-duc.service <<EOLS
[Unit]
Description=No-IP Dynamic Update Client
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/noip-duc -g all.ddnskey.com --username "\$NOIP_USERNAME" --password "\$NOIP_PASSWORD" --hostnames "\$DOMAIN" --daemon
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOLS

# Enable and start the No-IP DUC service
echo "Enabling and starting No-IP DUC service..."
systemctl enable noip-duc.service
systemctl start noip-duc.service

# Attempt automatic port forwarding with UPnP
echo "Attempting automatic port forwarding with UPnP..."
LOCAL_IP=\$(ip route get 1 | awk '{print \$7;exit}')
upnpc -a \$LOCAL_IP \$SSH_PORT \$SSH_PORT TCP
upnpc -a \$LOCAL_IP 80 80 TCP
upnpc -a \$LOCAL_IP 443 443 TCP
upnpc -a \$LOCAL_IP 30303 30303 TCP
upnpc -a \$LOCAL_IP 30303 30303 UDP

# Check if ports are accessible
echo "Checking if ports are accessible..."
check_port() {
    nc -z -w5 \$(curl -s https://api.ipify.org) \$1 >/dev/null 2>&1
    if [ \$? -eq 0 ]; then
        echo "Port \$1 is open"
    else
        echo "Port \$1 is not accessible. You may need to set up port forwarding manually."
    fi
}

check_port \$SSH_PORT
check_port 80
check_port 443
check_port 30303

echo "============================================================"
echo "IMPORTANT: Port Forwarding Instructions"
echo "============================================================"
echo "If any of the ports above are not accessible, you need to set up port forwarding on your Orbi RBR4 router:"
echo "1. Access your router's admin interface at http://orbilogin.com or http://192.168.1.1"
echo "2. Log in with your admin credentials"
echo "3. Go to Advanced > Advanced Setup > Port Forwarding / Port Triggering"
echo "4. Add port forwarding rules for the following ports:"
echo "   - SSH: \$SSH_PORT (TCP)"
echo "   - HTTP: 80 (TCP)"
echo "   - HTTPS: 443 (TCP)"
echo "   - Ethereum P2P: 30303 (TCP and UDP)"
echo "5. The internal IP address should be set to this machine's local IP address: \$LOCAL_IP"
echo "6. Save the settings and restart your router if required"
echo "============================================================"

echo "Post-installation script completed."
EOL

# Make the post-installation script executable
chmod +x "$MOUNT_POINT/root/post_install.sh"

# Chroot into the new system and run the post-installation script
show_progress "Chrooting into the new system and running post-installation script"
chroot "$MOUNT_POINT" /root/post_install.sh
finish_progress

# Backup important configuration files
log_message "Backing up important configuration files..."
mkdir -p "$MOUNT_POINT/root/config_backups"
cp "$MOUNT_POINT/etc/fstab" "$MOUNT_POINT/root/config_backups/"
cp "$MOUNT_POINT/etc/ssh/sshd_config" "$MOUNT_POINT/root/config_backups/"
cp "$MOUNT_POINT/etc/systemd/system/geth.service" "$MOUNT_POINT/root/config_backups/"

# Unmount all mounted partitions
show_progress "Unmounting partitions"
umount -R "$MOUNT_POINT"
finish_progress

# Preserve setup logs
log_message "Preserving setup logs..."
mkdir -p "$MOUNT_POINT/var/log/ethereum_setup"
cp "$LOG_FILE" "$MOUNT_POINT/var/log/ethereum_setup/main_setup.log"
cp "$MOUNT_POINT$CHROOT_LOG_FILE" "$MOUNT_POINT/var/log/ethereum_setup/chroot_setup.log"

log_message "Ethereum node setup completed successfully."
echo "============================================================"
echo "Ethereum Node Setup Complete"
echo "============================================================"
echo "Your Ethereum node has been set up successfully."
echo "Please reboot your system to start using your new Ethereum node."
echo "After rebooting, you can SSH into your node using:"
echo "ssh -p $SSH_PORT $USERNAME@$DOMAIN"
echo "Remember to update your SSH client configuration if needed."
echo "Setup logs have been preserved in /var/log/ethereum_setup/"
echo "Important configuration files have been backed up to /root/config_backups/"
echo "============================================================"
