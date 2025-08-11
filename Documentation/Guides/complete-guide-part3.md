# Complete Home Cloud Setup Guide - Part 3

## Part 5: Security Configuration and Hardening

### 5.1 Network Security

#### Firewall Configuration
```bash
#!/bin/bash
# Base firewall setup script

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (restrict to your IP range if possible)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow Plex
iptables -A INPUT -p tcp --dport 32400 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow WireGuard VPN
iptables -A INPUT -p udp --dport 51820 -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "IPTables-Dropped: "

# Save rules
iptables-save > /etc/iptables/rules.v4
```

#### VLAN Security Rules
```plaintext
Inter-VLAN Access Control List:

# Management VLAN (10)
allow from VLAN10 to all
deny to VLAN10 from all except VLAN30

# Media VLAN (20)
allow from VLAN20 to VLAN10 port 32400 # Plex
allow from VLAN20 to WAN HTTP/HTTPS
deny to VLAN20 from all except VLAN10,30

# Personal VLAN (30)
allow from VLAN30 to all
deny to VLAN30 from VLAN40

# IoT VLAN (40)
allow from VLAN40 to WAN HTTP/HTTPS
deny from VLAN40 to all local networks
```

### 5.2 Service Hardening

#### Docker Security Configuration
```yaml
# docker-compose-secure.yml
version: '3.8'

services:
  plex:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
      - SYS_NICE
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - plex_config:/config
      - media:/media:ro

  sonarr:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - sonarr_config:/config
      - media:/media
      - downloads:/downloads

volumes:
  plex_config:
    driver: local
    driver_opts:
      type: none
      device: /opt/docker/data/plex
      o: bind
  media:
    driver: local
    driver_opts:
      type: none
      device: /tank/media
      o: bind
```

#### SSL Configuration
```nginx
# /etc/nginx/conf.d/ssl.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 1.0.0.1 valid=300s;
resolver_timeout 5s;
add_header Strict-Transport-Security "max-age=63072000" always;
```

### 5.3 Access Control

#### User Management Script
```python
#!/usr/bin/env python3
import os
import sys
import pwd
import grp
import crypt
from datetime import datetime

class UserManager:
    def __init__(self):
        self.user_group = "media"
        self.base_dir = "/tank/media"
        
    def create_user(self, username, password):
        try:
            # Create group if it doesn't exist
            try:
                grp.getgrnam(self.user_group)
            except KeyError:
                os.system(f"groupadd {self.user_group}")
            
            # Create user
            encrypted_pass = crypt.crypt(password)
            os.system(f"useradd -m -g {self.user_group} -p {encrypted_pass} {username}")
            
            # Create user directories
            user_dir = os.path.join(self.base_dir, username)
            os.makedirs(user_dir, exist_ok=True)
            os.chown(user_dir, pwd.getpwnam(username).pw_uid, 
                    grp.getgrnam(self.user_group).gr_gid)
            os.chmod(user_dir, 0o750)
            
            print(f"Created user: {username}")
            return True
            
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return False
    
    def delete_user(self, username):
        try:
            # Archive user data
            user_dir = os.path.join(self.base_dir, username)
            if os.path.exists(user_dir):
                archive_name = f"{username}_backup_{datetime.now():%Y%m%d}"
                os.system(f"tar czf /backup/users/{archive_name}.tar.gz {user_dir}")
            
            # Delete user
            os.system(f"userdel -r {username}")
            print(f"Deleted user: {username}")
            return True
            
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            return False
    
    def modify_permissions(self, username, permission_level):
        try:
            user_dir = os.path.join(self.base_dir, username)
            if permission_level == "read":
                os.chmod(user_dir, 0o750)
            elif permission_level == "write":
                os.chmod(user_dir, 0o770)
            elif permission_level == "admin":
                os.chmod(user_dir, 0o775)
            return True
            
        except Exception as e:
            print(f"Error modifying permissions: {str(e)}")
            return False

# Usage example
if __name__ == "__main__":
    manager = UserManager()
    
    # Create new user
    manager.create_user("newuser", "SecurePass123!")
    
    # Modify permissions
    manager.modify_permissions("newuser", "read")
    
    # Delete user
    #manager.delete_user("newuser")
```

#### Authentication Script
```python
#!/usr/bin/env python3
import jwt
import datetime
import hashlib
import sqlite3
from functools import wraps

class AuthManager:
    def __init__(self):
        self.secret_key = "your-secret-key"
        self.db_path = "/opt/auth/users.db"
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT, 
                      role TEXT, last_login DATETIME)''')
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_token(self, username, role):
        payload = {
            'username': username,
            'role': role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def login(self, username, password):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT password, role FROM users WHERE username = ?', 
                 (username,))
        user = c.fetchone()
        
        if user and user[0] == self.hash_password(password):
            c.execute('UPDATE users SET last_login = ? WHERE username = ?',
                     (datetime.datetime.utcnow(), username))
            conn.commit()
            token = self.generate_token(username, user[1])
            conn.close()
            return token
        
        conn.close()
        return None
    
    def require_auth(self, roles=[]):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                token = request.headers.get('Authorization')
                if not token:
                    return {'message': 'Missing token'}, 401
                
                payload = self.verify_token(token)
                if not payload:
                    return {'message': 'Invalid token'}, 401
                
                if roles and payload['role'] not in roles:
                    return {'message': 'Insufficient permissions'}, 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# Usage example
auth_manager = AuthManager()

@auth_manager.require_auth(roles=['admin'])
def admin_only():
    return {'message': 'Admin access granted'}

@auth_manager.require_auth(roles=['user', 'admin'])
def user_access():
    return {'message': 'User access granted'}
```

### 5.4 Security Monitoring

#### Intrusion Detection Script
```python
#!/usr/bin/env python3
import re
import time
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

class SecurityMonitor:
    def __init__(self):
        self.log_paths = {
            'ssh': '/var/log/auth.log',
            'nginx': '/var/log/nginx/access.log',
            'plex': '/var/log/plex/Plex Media Server.log'
        }
        self.db_path = '/opt/security/events.db'
        self.init_db()
        
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS security_events
                     (timestamp DATETIME, event_type TEXT, 
                      source_ip TEXT, description TEXT)''')
        conn.commit()
        conn.close()
    
    def parse_logs(self):
        patterns = {
            'ssh_fail': r'Failed password for .* from (.*) port',
            'nginx_404': r'(.*) - .* ".*" 404',
            'nginx_403': r'(.*) - .* ".*" 403',
            'plex_auth': r'Failed login attempt from (.*)'
        }
        
        events = []
        
        for service, log_path in self.log_paths.items():
            try:
                with open(log_path, 'r') as f:
                    for line in f:
                        for event_type, pattern in patterns.items():
                            match = re.search(pattern, line)
                            if match:
                                source_ip = match.group(1)
                                events.append({
                                    'timestamp': datetime.now(),
                                    'event_type': event_type,
                                    'source_ip': source_ip,
                                    'description': line.strip()
                                })
            except Exception as e:
                print(f"Error parsing {service} log: {str(e)}")
        
        return events
    
    def analyze_events(self, events):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        alerts = []
        
        for event in events:
            # Check for brute force attempts
            c.execute('''SELECT COUNT(*) FROM security_events
                        WHERE event_type LIKE ?
                        AND source_ip = ?
                        AND timestamp > datetime("now", "-1 hour")''',
                     (event['event_type'], event['source_ip']))
            
            count = c.fetchone()[0]
            
            if count > 10:
                alerts.append({
                    'level': 'HIGH',
                    'message': f'Possible brute force from {event["source_ip"]}',
                    'count': count
                })
            
            # Store event
            c.execute('''INSERT INTO security_events
                        VALUES (?, ?, ?, ?)''',
                     (event['timestamp'], event['event_type'],
                      event['source_ip'], event['description']))
        
        conn.commit()
        conn.close()
        return alerts
    
    def send_alert(self, alert):
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender = "your-email@gmail.com"
        password = "your-app-password"
        recipient = "admin@example.com"
        
        msg = MIMEText(f"""
        Security Alert: {alert['message']}
        Level: {alert['level']}
        Count: {alert['count']}
        Time: {datetime.now()}
        """)
        
        msg['Subject'] = f"Security Alert - {alert['level']}"
        msg['From'] = sender
        msg['To'] = recipient
        
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
        except Exception as e:
            print(f"Error sending alert: {str(e)}")
    
    def run(self):
        while True:
            events = self.parse_logs()
            alerts = self.analyze_events(events)
            
            for alert in alerts:
                self.send_alert(alert)
            
            time.sleep(300)  # Check every 5 minutes

# Usage
if __name__ == "__main__":
    monitor = SecurityMonitor()
    monitor.run()
```

I'll continue with the Remote Access Setup section. Would you like me to proceed?