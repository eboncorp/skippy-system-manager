# Complete Home Cloud Setup Guide - Part 4

## Part 6: Remote Access Setup

### 6.1 WireGuard VPN Configuration

#### Base WireGuard Setup
```ini
# /etc/wireguard/wg0.conf (Server Configuration)
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = <server_private_key>
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Client 1
[Peer]
PublicKey = <client1_public_key>
AllowedIPs = 10.8.0.2/32

# Client 2
[Peer]
PublicKey = <client2_public_key>
AllowedIPs = 10.8.0.3/32
```

#### WireGuard Management Script
```python
#!/usr/bin/env python3
import os
import subprocess
import qrcode
import base64
from datetime import datetime

class WireGuardManager:
    def __init__(self):
        self.config_dir = '/etc/wireguard'
        self.client_dir = '/etc/wireguard/clients'
        self.server_config = '/etc/wireguard/wg0.conf'
        
        # Ensure directories exist
        os.makedirs(self.client_dir, exist_ok=True)
    
    def generate_keypair(self):
        """Generate WireGuard keypair"""
        private_key = subprocess.check_output(['wg', 'genkey']).decode('utf-8').strip()
        public_key = subprocess.check_output(['echo', private_key, '|', 'wg', 'pubkey'],
                                          shell=True).decode('utf-8').strip()
        return private_key, public_key
    
    def create_client(self, client_name):
        """Create a new client configuration"""
        # Generate keys
        private_key, public_key = self.generate_keypair()
        
        # Get next available IP
        next_ip = self._get_next_ip()
        
        # Create client config
        client_config = f"""[Interface]
PrivateKey = {private_key}
Address = {next_ip}/32
DNS = 10.8.0.1

[Peer]
PublicKey = {self._get_server_pubkey()}
Endpoint = {self._get_server_endpoint()}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
        
        # Save client config
        client_file = os.path.join(self.client_dir, f"{client_name}.conf")
        with open(client_file, 'w') as f:
            f.write(client_config)
        
        # Add peer to server config
        self._add_peer_to_server(public_key, next_ip)
        
        # Generate QR code
        self._generate_qr_code(client_config, client_name)
        
        return {
            'config_file': client_file,
            'qr_code': f"{client_name}_qr.png",
            'public_key': public_key,
            'ip_address': next_ip
        }
    
    def _get_next_ip(self):
        """Get next available IP in the subnet"""
        used_ips = []
        with open(self.server_config, 'r') as f:
            for line in f:
                if 'AllowedIPs' in line:
                    ip = line.split('=')[1].strip().split('/')[0]
                    used_ips.append(ip)
        
        for i in range(2, 255):
            candidate = f"10.8.0.{i}"
            if candidate not in used_ips:
                return candidate
        
        raise Exception("No available IPs in subnet")
    
    def _get_server_pubkey(self):
        """Get server's public key"""
        with open(self.server_config, 'r') as f:
            for line in f:
                if 'PrivateKey' in line:
                    private_key = line.split('=')[1].strip()
                    return subprocess.check_output(
                        ['echo', private_key, '|', 'wg', 'pubkey'],
                        shell=True).decode('utf-8').strip()
        return None
    
    def _get_server_endpoint(self):
        """Get server's public endpoint"""
        return "your-domain.duckdns.org:51820"
    
    def _add_peer_to_server(self, public_key, ip):
        """Add peer to server configuration"""
        peer_config = f"""
[Peer]
PublicKey = {public_key}
AllowedIPs = {ip}/32
"""
        with open(self.server_config, 'a') as f:
            f.write(peer_config)
        
        # Reload WireGuard
        subprocess.run(['systemctl', 'reload', 'wg-quick@wg0'])
    
    def _generate_qr_code(self, config, client_name):
        """Generate QR code for mobile clients"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(config)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(os.path.join(self.client_dir, f"{client_name}_qr.png"))
    
    def list_clients(self):
        """List all configured clients"""
        clients = []
        for file in os.listdir(self.client_dir):
            if file.endswith('.conf'):
                client_name = file[:-5]
                with open(os.path.join(self.client_dir, file), 'r') as f:
                    config = f.read()
                    ip = config.split('Address = ')[1].split('/')[0]
                    clients.append({
                        'name': client_name,
                        'ip': ip,
                        'created': datetime.fromtimestamp(
                            os.path.getctime(os.path.join(self.client_dir, file))
                        )
                    })
        return clients
    
    def remove_client(self, client_name):
        """Remove a client configuration"""
        client_file = os.path.join(self.client_dir, f"{client_name}.conf")
        qr_file = os.path.join(self.client_dir, f"{client_name}_qr.png")
        
        # Get client's public key
        with open(client_file, 'r') as f:
            config = f.read()
            public_key = config.split('PublicKey = ')[1].split('\n')[0]
        
        # Remove client files
        os.remove(client_file)
        if os.path.exists(qr_file):
            os.remove(qr_file)
        
        # Remove peer from server config
        with open(self.server_config, 'r') as f:
            lines = f.readlines()
        
        with open(self.server_config, 'w') as f:
            skip = False
            for line in lines:
                if f'PublicKey = {public_key}' in line:
                    skip = True
                    continue
                if skip and line.startswith('[Peer]'):
                    skip = False
                if not skip:
                    f.write(line)
        
        # Reload WireGuard
        subprocess.run(['systemctl', 'reload', 'wg-quick@wg0'])

# Usage example
if __name__ == "__main__":
    wg = WireGuardManager()
    
    # Create new client
    client = wg.create_client("mobile_device")
    print(f"Created client: {client}")
    
    # List all clients
    clients = wg.list_clients()
    print("\nConfigured clients:")
    for client in clients:
        print(f"- {client['name']}: {client['ip']} (created: {client['created']})")
    
    # Remove client
    #wg.remove_client("mobile_device")
```

### 6.2 Reverse Proxy Configuration

#### Traefik Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  traefik:
    image: traefik:v2.9
    container_name: traefik
    command:
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "/etc/traefik/acme.json:/acme.json"
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.yourdomain.com`)"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik.service=api@internal"

  plex:
    image: plexinc/pms-docker
    container_name: plex
    restart: unless-stopped
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.plex.rule=Host(`plex.yourdomain.com`)"
      - "traefik.http.routers.plex.entrypoints=websecure"
      - "traefik.http.routers.plex.tls.certresolver=letsencrypt"
      - "traefik.http.services.plex.loadbalancer.server.port=32400"

  nextcloud:
    image: nextcloud
    container_name: nextcloud
    restart: unless-stopped
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nextcloud.rule=Host(`cloud.yourdomain.com`)"
      - "traefik.http.routers.nextcloud.entrypoints=websecure"
      - "traefik.http.routers.nextcloud.tls.certresolver=letsencrypt"
      - "traefik.http.services.nextcloud.loadbalancer.server.port=80"

networks:
  proxy:
    external: true
```

#### Dynamic Configuration Example
```yaml
# /etc/traefik/dynamic.yml
http:
  middlewares:
    secureHeaders:
      headers:
        sslRedirect: true
        forceSTSHeader: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 31536000
        customFrameOptionsValue: "SAMEORIGIN"
        contentTypeNosniff: true
        browserXssFilter: true
        referrerPolicy: "strict-origin-when-cross-origin"
        featurePolicy: "camera 'none'; microphone 'none'; geolocation 'none'"
        customResponseHeaders:
          X-Robots-Tag: "none,noarchive,nosnippet,notranslate,noimageindex"
          server: ""

    rateLimit:
      rateLimit:
        average: 100
        burst: 50

    ipWhitelist:
      ipWhitelist:
        sourceRange:
          - "10.0.0.0/8"
          - "192.168.0.0/16"
          - "172.16.0.0/12"

tls:
  options:
    default:
      minVersion: "VersionTLS12"
      cipherSuites:
        - "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"
        - "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
        - "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"
        - "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"
      curvePreferences:
        - "CurveP521"
        - "CurveP384"
```

I'll continue with SSL Certificate Management and Remote Access Security. Would you like me to proceed?