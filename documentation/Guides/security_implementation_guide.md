# Security Implementation Guide

## 🎯 Overview
Complete security hardening setup for remote access to your HP Z4 G4 home server "ebon" and preparation for crypto node operations.

## 📋 Implementation Order

### Phase 1: Laptop Security Hardening (Run First)
```bash
# 1. Run laptop security setup (requires sudo)
sudo bash /home/dave/Skippy/laptop_security_setup.sh
```

**This script will:**
- Configure UFW firewall with restrictive rules
- Install and configure fail2ban
- Harden SSH configuration
- Install WireGuard VPN client
- Generate WireGuard keys
- Configure automatic security updates
- Set up system auditing

### Phase 2: Server VPN Setup (Run on HP Z4 G4)
```bash
# 2. Copy and run on your server "ebon"
scp /home/dave/Skippy/server_wireguard_setup.sh ebon@10.0.0.29:~/
ssh ebon@10.0.0.29
sudo bash server_wireguard_setup.sh
```

**This will:**
- Install WireGuard server
- Generate server keys
- Configure firewall rules
- Create client management tools

### Phase 3: YubiKey Preparation (Optional - run when ready)
```bash
# 3. Prepare for YubiKey 5 (when it arrives)
sudo bash /home/dave/Skippy/yubikey_preparation.sh
```

### Phase 4: Backup Strategy Setup
```bash
# 4. Set up secure backup system
bash /home/dave/Skippy/secure_backup_strategy.sh
```

## 🔧 Manual Configuration Steps

### After Phase 1 (Laptop Setup):
1. **Reboot your laptop** to apply all security settings
2. **Copy your laptop's WireGuard public key:**
   ```bash
   sudo cat /etc/wireguard/laptop_public.key
   ```

### After Phase 2 (Server Setup):
1. **Copy server's public key** from server output
2. **Add laptop as VPN client on server:**
   ```bash
   # Run on server
   sudo /usr/local/bin/add-vpn-client.sh laptop LAPTOP_PUBLIC_KEY 10.9.0.2
   ```
3. **Update laptop VPN config** with server's public key:
   ```bash
   # Edit on laptop
   sudo nano /etc/wireguard/home-server.conf
   # Replace SERVER_PUBLIC_KEY_HERE with actual key
   # Replace YOUR_HOME_IP with your public IP
   ```

### VPN Connection Test:
```bash
# On laptop - test VPN connection
sudo wg-quick up home-server

# Verify connection
wg show
ping 10.9.0.1

# Test SSH through VPN
ssh ebon@10.9.0.1

# Disconnect when done testing
sudo wg-quick down home-server
```

## 🔑 YubiKey Integration (When Hardware Arrives)

### Setup Steps:
1. **Test YubiKey detection:**
   ```bash
   sudo /usr/local/bin/test-yubikey.sh
   ```

2. **Generate SSH key on YubiKey:**
   ```bash
   ssh-keygen -t ecdsa-sk -f ~/.ssh/yubikey_ecdsa
   ```

3. **Add to server:**
   ```bash
   ssh-copy-id -i ~/.ssh/yubikey_ecdsa.pub ebon@10.9.0.1
   ```

4. **Follow checklist:**
   ```bash
   cat ~/yubikey_security_checklist.md
   ```

## 🛡️ Security Features Implemented

### Network Security:
- **UFW Firewall:** Restrictive rules, VPN-only access
- **WireGuard VPN:** Modern encryption (ChaCha20Poly1305, Curve25519)
- **Fail2ban:** Automated intrusion prevention
- **Network isolation:** VPN tunnel for all server access

### Authentication:
- **SSH key-only authentication** (passwords disabled)
- **YubiKey FIDO2/WebAuthn support** (when hardware arrives)
- **Multi-factor authentication** ready
- **Certificate-based VPN authentication**

### System Hardening:
- **Automatic security updates**
- **System auditing** enabled
- **AppArmor** mandatory access control
- **Kernel security parameters** optimized

### Backup & Recovery:
- **Encrypted backup system** (AES-256 + GPG)
- **Automated weekly backups**
- **Emergency recovery procedures**
- **Multiple backup locations support**

## 📊 Monitoring & Maintenance

### Daily Monitoring:
```bash
# Check security status
sudo /usr/local/bin/security-check.sh

# Check VPN status (on server)
sudo /usr/local/bin/vpn-status.sh
```

### Weekly Tasks:
```bash
# Create secure backup
~/.secure-backups/create_secure_backup.sh

# Verify backup integrity
~/.secure-backups/verify_backup.sh <backup_file>
```

## 🚨 Emergency Procedures

### If Laptop is Compromised:
1. **Immediately change all passwords**
2. **Revoke SSH keys on server:**
   ```bash
   # On server
   sudo nano ~/.ssh/authorized_keys
   # Remove compromised keys
   ```
3. **Block VPN access:**
   ```bash
   # On server
   sudo /usr/local/bin/remove-vpn-client.sh LAPTOP_PUBLIC_KEY
   ```
4. **Restore from backup on new device**

### If YubiKey is Lost:
1. **Disable 2FA on all accounts**
2. **Use backup YubiKey**
3. **Generate new SSH keys**
4. **Follow emergency checklist in ~/yubikey_security_checklist.md**

## 🔐 Security Best Practices

### Access Patterns:
- **Always use VPN** for server access
- **Never disable firewall** on laptop
- **Use YubiKey** for all authentication when available
- **Monitor logs** regularly for suspicious activity

### Key Management:
- **Rotate SSH keys** every 6 months
- **Keep backups current** (automated weekly)
- **Store backups securely** in multiple locations
- **Test recovery procedures** monthly

### Network Security:
- **Use WireGuard exclusively** for remote access
- **Monitor VPN connections** for anomalies
- **Update server regularly** via SSH through VPN
- **Never expose services directly** to internet

## 📈 Future Enhancements

When setting up crypto nodes:
- **Dedicated VLAN 50** (192.168.50.0/24) for Ethereum
- **Hardware security keys** for all crypto operations
- **Encrypted storage** for blockchain data
- **Monitoring dashboard** with Prometheus/Grafana

## 🎯 Success Criteria

✅ **Complete Setup Achieved When:**
- Laptop connects securely via VPN only
- SSH access works through VPN tunnel  
- YubiKey authenticates all operations
- Backups run automatically weekly
- All services monitored and logged
- Emergency procedures tested and documented

---

## 📞 Support

If you encounter issues:
1. Check logs: `/var/log/auth.log`, `/var/log/ufw.log`
2. Verify services: `systemctl status ufw fail2ban wg-quick@home-server`
3. Test connectivity: `ping`, `ssh -v`, `wg show`
4. Review this guide and security checklists

**Your infrastructure is now secured with enterprise-grade protection! 🛡️**