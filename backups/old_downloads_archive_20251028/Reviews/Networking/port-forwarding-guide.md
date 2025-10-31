# Detailed Port Forwarding Configuration for Secure Remote Access

This guide will walk you through the exact steps to configure port forwarding on your network devices for secure remote access to your Ethereum server.

## AT&T Gateway (BGW320-505) Configuration

### Setting Up IP Passthrough Mode

1. **Access the Gateway's Admin Panel**:
   - Connect to your AT&T Gateway via wired connection
   - Open a browser and go to http://192.168.1.254
   - Login with your administrator credentials

2. **Configure IP Passthrough**:
   - Navigate to: Settings → LAN → IP Passthrough
   - Set Allocation Mode to "Passthrough"
   - Passthrough Type: "DHCPS-fixed"
   - In the "Passthrough Fixed MAC Address" field, enter your Orbi router's MAC address
   - Save changes
   - Reboot the gateway when prompted

3. **Verify Firewall Settings**:
   - Go to: Firewall → Packet Filter
   - Make sure no filtering is active that would block VPN traffic
   - Specifically, verify UDP 1194 (OpenVPN) or UDP 51820 (WireGuard) is allowed if using these protocols

### Alternative: Port Forwarding on AT&T Gateway
If IP Passthrough is not an option, set up these port forwards:

1. Navigate to: Firewall → NAT/Gaming
2. Add a port forwarding rule:
   - Select your VPN server device
   - Protocol: TCP/UDP (as needed for your VPN)
   - Public port(s): VPN port (e.g., 1194, 51820)
   - Private port(s): Same as public
   - Save changes

## NETGEAR Orbi Router (RBR40) Configuration

### Setting Up VPN Server 

1. **Access the Orbi Admin Panel**:
   - Connect to your Orbi network
   - Open a browser and go to http://orbilogin.com
   - Login with admin credentials

2. **Install and Configure VPN Server**:
   - Navigate to: Advanced → VPN Service
   - Enable VPN service
   - Select OpenVPN as the protocol
   - Configure these settings:
     - Interface Type: TUN
     - VPN Network/Netmask: 10.8.0.0/24 (make sure this doesn't conflict with your local subnet)
     - Client Access: "Home Network only" for more security or "Home Network and Internet" for full access
     - Encryption: AES-256-CBC
     - Authentication: HMAC-SHA256
   - Create VPN Client Access:
     - Add a new user
     - Username: [secure username]
     - Password: [strong password]
   - Download the configuration files and certificates

3. **Enable Port Forwarding** (if Orbi is not in bridge mode):
   - Navigate to: Advanced → Port Forwarding/Port Triggering
   - Add a port forwarding rule:
     - Service Name: "VPN Server"
     - Protocol: TCP and UDP
     - External Starting/Ending Port: 1194 (for OpenVPN) or 51820 (for WireGuard)
     - Internal IP Address: The local IP of your Orbi router
     - Internal Starting/Ending Port: Same as external
   - Enable the rule and save changes

### Additional Security Settings for Orbi

1. **Implement Access Controls**:
   - Navigate to: Advanced → Security → Access Control
   - Enable Access Control
   - Set Access Rule to "Allow all new devices to connect"
   - Add your devices to the allowed devices list
   - Block all unlisted devices

2. **Enable Traffic Meter**:
   - Navigate to: Advanced → Advanced Setup → Traffic Meter
   - Enable Traffic Meter
   - Set monthly traffic limit
   - Enable email notifications for unusual activity

## NETGEAR ProSafe Plus Switch (JGS524PE) Configuration

### Basic Configuration Access

1. **Initial Setup**:
   - Connect to switch via ethernet
   - Install and open NETGEAR ProSafe Plus Configuration Utility
   - Discover the switch on your network
   - Login with default credentials (then change immediately)
   - Default IP is typically 192.168.0.239

### VLAN Configuration

1. **Create VLANs**:
   - Navigate to: VLAN → 802.1Q → Advanced → VLAN Configuration
   - Create three VLANs:
     - VLAN ID 10: Name "General" (for everyday devices)
     - VLAN ID 20: Name "IoT" (for smart home/less secure devices)
     - VLAN ID 30: Name "Ethereum" (isolated network for your server)

2. **Configure VLAN Port Settings**:
   - Navigate to: VLAN → 802.1Q → Advanced → VLAN Membership
   - For each port, set appropriate VLAN membership:
     - Port connected to Orbi: Tagged member of all VLANs (10, 20, 30)
     - Ports for general devices: Untagged members of VLAN 10
     - Ports for IoT devices: Untagged members of VLAN 20
     - Port for Ethereum server: Untagged member of VLAN 30 only
   - Set PVID settings accordingly (PVID = Port VLAN ID):
     - Port connected to Orbi: PVID 1 (Default VLAN)
     - General device ports: PVID 10
     - IoT device ports: PVID 20
     - Ethereum server port: PVID 30

3. **Configure Port Isolation for Ethereum Server**:
   - Navigate to: Security → Traffic Control → Port Isolation
   - Enable port isolation on the Ethereum server port
   - Make sure it can only communicate with the uplink port to the router

### QoS Configuration for Ethereum Traffic

1. **Set Up QoS**:
   - Navigate to: QoS → Advanced → 802.1p/DSCP
   - Create a high priority queue for Ethereum server port
   - Navigate to: QoS → Advanced → Port Priority
   - Set Ethereum server port to high priority

### Port Security for Ethereum Server

1. **Lock Down Ethereum Server Port**:
   - Navigate to: Security → Network Access → Port Authentication
   - Enable 802.1X port-based authentication for the Ethereum server port
   - Navigate to: Security → Traffic Control → Storm Control
   - Enable Broadcast, Multicast, and Unknown Unicast storm control on the Ethereum server port
   - Set appropriate rate limits (e.g., 20%)

## Ethereum Server Configuration

### Network Interface Setup

1. **Static IP Configuration**:
   - Assign static IP in the VLAN 30 subnet (e.g., 192.168.30.10)
   - Set subnet mask to 255.255.255.0
   - Set gateway to router's IP on VLAN 30 (e.g., 192.168.30.1)
   - Configure DNS servers (consider using secure DNS like 1.1.1.2 or 9.9.9.9)

2. **Host-based Firewall Rules**:
   - For Linux (using iptables):
     ```bash
     # Flush existing rules
     iptables -F
     
     # Default policies
     iptables -P INPUT DROP
     iptables -P FORWARD DROP
     iptables -P OUTPUT ACCEPT
     
     # Allow established connections
     iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
     
     # Allow loopback
     iptables -A INPUT -i lo -j ACCEPT
     
     # Allow SSH (change port if you've configured a non-standard port)
     iptables -A INPUT -p tcp --dport 22 -j ACCEPT
     
     # Allow Ethereum P2P traffic
     iptables -A INPUT -p tcp --dport 30303 -j ACCEPT
     iptables -A INPUT -p udp --dport 30303 -j ACCEPT
     
     # Optional: Allow specific RPC connections ONLY from specific IPs
     iptables -A INPUT -p tcp --dport 8545 -s YOUR_TRUSTED_IP -j ACCEPT
     
     # Save rules (persistent across reboots)
     apt-get install iptables-persistent
     netfilter-persistent save
     ```

   - For Windows:
     - Open Windows Defender Firewall with Advanced Security
     - Create inbound rules for TCP/UDP port 30303
     - Create specific inbound rules for RPC ports if needed
     - Block all other inbound connections

### SSH Configuration for Secure Remote Access

1. **SSH Key-based Authentication**:
   - Generate SSH key pair on your laptop:
     ```bash
     ssh-keygen -t ed25519 -f ~/.ssh/ethereum_server
     ```
   - Copy public key to server:
     ```bash
     ssh-copy-id -i ~/.ssh/ethereum_server.pub user@your-server-ip
     ```
   - Disable password authentication on server:
     - Edit `/etc/ssh/sshd_config`
     - Set `PasswordAuthentication no`
     - Set `PubkeyAuthentication yes`
     - Restart SSH service

2. **Change Default SSH Port**:
   - Edit `/etc/ssh/sshd_config`
   - Change `Port 22` to a non-standard port (e.g., Port 2222)
   - Update firewall rules accordingly
   - Restart SSH service

3. **Implement Fail2ban**:
   - Install fail2ban:
     ```bash
     apt-get install fail2ban
     ```
   - Configure SSH jail:
     - Create `/etc/fail2ban/jail.local`
     - Add configuration:
       ```
       [sshd]
       enabled = true
       port = 2222
       filter = sshd
       logpath = /var/log/auth.log
       maxretry = 3
       bantime = 3600
       ```
   - Restart fail2ban:
     ```bash
     systemctl restart fail2ban
     ```

## Remote Access Client Setup

### VPN Client Configuration

1. **Install OpenVPN Client**:
   - Windows: Download and install OpenVPN GUI
   - macOS: Download and install Tunnelblick
   - Linux: `apt-get install openvpn` or equivalent

2. **Import Configuration**:
   - Copy the configuration files generated by your Orbi router
   - Import them into your OpenVPN client
   - Test the connection

3. **Create Connection Script**:
   - Create a script that:
     1. Connects to VPN
     2. Establishes SSH connection to Ethereum server
     3. Sets up proper port forwarding if needed

### Multi-Factor Authentication Setup

1. **Set up Google Authenticator** (or similar TOTP app):
   - Install Google Authenticator on server:
     ```bash
     apt-get install libpam-google-authenticator
     ```
   - Run the initialization:
     ```bash
     google-authenticator
     ```
   - Configure PAM:
     - Edit `/etc/pam.d/sshd`
     - Add `auth required pam_google_authenticator.so`
   - Edit SSH config:
     - Set `ChallengeResponseAuthentication yes`
     - Set `AuthenticationMethods publickey,keyboard-interactive`
   - Restart SSH

2. **Test Complete Authentication Flow**:
   - Connect to VPN
   - Attempt SSH connection using key
   - Verify TOTP prompt appears
   - Enter TOTP code to complete login
