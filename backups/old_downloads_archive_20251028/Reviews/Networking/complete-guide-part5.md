# Complete Home Cloud Setup Guide - Part 5

## Part 7: SSL Certificate Management

### 7.1 Let's Encrypt Automation

#### Certificate Manager Script
```python
#!/usr/bin/env python3
import os
import subprocess
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import yaml

class CertificateManager:
    def __init__(self):
        self.config_file = '/opt/ssl/config.yml'
        self.cert_dir = '/etc/letsencrypt/live'
        self.email = 'admin@yourdomain.com'
        self.load_config()
        
    def load_config(self):
        """Load domain configuration"""
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def check_certificates(self):
        """Check certificate status for all domains"""
        results = []
        for domain in self.config['domains']:
            cert_path = os.path.join(self.cert_dir, domain['name'], 'cert.pem')
            if os.path.exists(cert_path):
                expiry = self.get_expiry_date(cert_path)
                days_left = (expiry - datetime.now()).days
                
                results.append({
                    'domain': domain['name'],
                    'expiry': expiry,
                    'days_left': days_left,
                    'needs_renewal': days_left < 30
                })
        
        return results
    
    def get_expiry_date(self, cert_path):
        """Get certificate expiry date"""
        cmd = f"openssl x509 -enddate -noout -in {cert_path}"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        date_str = result.split('=')[1].strip()
        return datetime.strptime(date_str, '%b %d %H:%M:%S %Y %Z')
    
    def renew_certificates(self):
        """Attempt to renew all certificates"""
        results = []
        for domain in self.config['domains']:
            try:
                # Prepare domain validation
                self.prepare_validation(domain)
                
                # Run certbot
                cmd = [
                    'certbot', 'certonly',
                    '--webroot',
                    '-w', domain['webroot'],
                    '-d', domain['name'],
                    '--email', self.email,
                    '--agree-tos',
                    '--non-interactive',
                    '--expand'
                ]
                
                if 'wildcard' in domain and domain['wildcard']:
                    cmd.extend(['-d', f"*.{domain['name']}"])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    results.append({
                        'domain': domain['name'],
                        'status': 'success',
                        'message': 'Certificate renewed successfully'
                    })
                    
                    # Reload services
                    self.reload_services()
                else:
                    results.append({
                        'domain': domain['name'],
                        'status': 'error',
                        'message': result.stderr
                    })
            
            except Exception as e:
                results.append({
                    'domain': domain['name'],
                    'status': 'error',
                    'message': str(e)
                })
        
        return results
    
    def prepare_validation(self, domain):
        """Prepare domain for validation"""
        if domain.get('validation_method') == 'dns':
            self.prepare_dns_validation(domain)
        else:
            self.prepare_http_validation(domain)
    
    def prepare_dns_validation(self, domain):
        """Prepare DNS validation"""
        # Implementation depends on DNS provider
        if domain.get('dns_provider') == 'cloudflare':
            self.update_cloudflare_dns(domain)
        # Add more providers as needed
    
    def prepare_http_validation(self, domain):
        """Prepare HTTP validation"""
        webroot = domain['webroot']
        os.makedirs(os.path.join(webroot, '.well-known/acme-challenge'),
                   exist_ok=True)
    
    def update_cloudflare_dns(self, domain):
        """Update Cloudflare DNS records"""
        # Implementation for Cloudflare DNS API
        pass
    
    def reload_services(self):
        """Reload services after certificate renewal"""
        services = self.config.get('services_to_reload', [])
        for service in services:
            subprocess.run(['systemctl', 'reload', service])
    
    def send_notification(self, message):
        """Send email notification"""
        msg = MIMEText(message)
        msg['Subject'] = 'SSL Certificate Update'
        msg['From'] = self.email
        msg['To'] = self.email
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(self.email, self.config['smtp_password'])
            server.send_message(msg)

# Example configuration (config.yml)
"""
domains:
  - name: yourdomain.com
    webroot: /var/www/html
    wildcard: true
    validation_method: http
  
  - name: cloud.yourdomain.com
    webroot: /var/www/nextcloud
    validation_method: http

  - name: plex.yourdomain.com
    webroot: /var/www/plex
    validation_method: dns
    dns_provider: cloudflare
    cloudflare_token: your_token

services_to_reload:
  - nginx
  - apache2
  - traefik

smtp_password: your_app_password
"""

# Usage example
if __name__ == "__main__":
    manager = CertificateManager()
    
    # Check certificates
    status = manager.check_certificates()
    
    # Renew if needed
    needs_renewal = any(cert['needs_renewal'] for cert in status)
    if needs_renewal:
        results = manager.renew_certificates()
        
        # Send notification
        message = "Certificate Renewal Results:\n\n"
        for result in results:
            message += f"{result['domain']}: {result['status']}\n"
            if result['status'] == 'error':
                message += f"Error: {result['message']}\n"
        
        manager.send_notification(message)
```

### 7.2 Certificate Monitoring

#### Certificate Monitor Service
```systemd
# /etc/systemd/system/cert-monitor.service
[Unit]
Description=SSL Certificate Monitor
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/ssl
ExecStart=/usr/local/bin/cert-monitor.py
Restart=always
RestartSec=3600

[Install]
WantedBy=multi-user.target
```

#### Monitoring Script
```python
#!/usr/bin/env python3
import os
import time
import logging
from datetime import datetime
import subprocess
import requests

class CertificateMonitor:
    def __init__(self):
        self.setup_logging()
        self.cert_dir = '/etc/letsencrypt/live'
        self.check_interval = 86400  # 24 hours
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename='/var/log/cert-monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def check_cert_status(self, domain):
        """Check certificate status for a domain"""
        cert_path = os.path.join(self.cert_dir, domain, 'cert.pem')
        
        try:
            # Check local certificate
            local_status = self.check_local_cert(cert_path)
            
            # Check remote certificate
            remote_status = self.check_remote_cert(domain)
            
            return {
                'domain': domain,
                'local_expiry': local_status['expiry'],
                'remote_expiry': remote_status['expiry'],
                'match': local_status['fingerprint'] == remote_status['fingerprint'],
                'valid': local_status['valid'] and remote_status['valid']
            }
            
        except Exception as e:
            logging.error(f"Error checking {domain}: {str(e)}")
            return None
    
    def check_local_cert(self, cert_path):
        """Check local certificate file"""
        cmd = f"openssl x509 -in {cert_path} -noout -fingerprint -dates"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        fingerprint = next(line for line in result.split('\n') 
                         if line.startswith('SHA1')).split('=')[1]
        
        end_date = next(line for line in result.split('\n') 
                       if line.startswith('notAfter')).split('=')[1]
        expiry = datetime.strptime(end_date, '%b %d %H:%M:%S %Y %Z')
        
        return {
            'fingerprint': fingerprint,
            'expiry': expiry,
            'valid': expiry > datetime.now()
        }
    
    def check_remote_cert(self, domain):
        """Check certificate on remote server"""
        cmd = f"echo | openssl s_client -servername {domain} " \
              f"-connect {domain}:443 2>/dev/null | " \
              f"openssl x509 -noout -fingerprint -dates"
        
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        fingerprint = next(line for line in result.split('\n') 
                         if line.startswith('SHA1')).split('=')[1]
        
        end_date = next(line for line in result.split('\n') 
                       if line.startswith('notAfter')).split('=')[1]
        expiry = datetime.strptime(end_date, '%b %d %H:%M:%S %Y %Z')
        
        return {
            'fingerprint': fingerprint,
            'expiry': expiry,
            'valid': expiry > datetime.now()
        }
    
    def send_alert(self, status):
        """Send alert for certificate issues"""
        if not status['valid'] or not status['match']:
            message = f"""
Certificate Alert for {status['domain']}:
Valid: {status['valid']}
Local/Remote Match: {status['match']}
Local Expiry: {status['local_expiry']}
Remote Expiry: {status['remote_expiry']}
            """
            
            # Send to multiple alert channels
            self.send_email_alert(message)
            self.send_slack_alert(message)
            self.log_alert(message)
    
    def send_email_alert(self, message):
        """Send email alert"""
        # Implementation similar to previous email sending code
        pass
    
    def send_slack_alert(self, message):
        """Send Slack alert"""
        webhook_url = "your_slack_webhook_url"
        payload = {
            "text": f"SSL Certificate Alert:\n```{message}```"
        }
        requests.post(webhook_url, json=payload)
    
    def log_alert(self, message):
        """Log alert to monitoring system"""
        logging.warning(message)
    
    def run(self):
        """Main monitoring loop"""
        while True:
            try:
                domains = os.listdir(self.cert_dir)
                for domain in domains:
                    if os.path.isdir(os.path.join(self.cert_dir, domain)):
                        status = self.check_cert_status(domain)
                        if status:
                            self.send_alert(status)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logging.error(f"Monitor error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes on error

# Run the monitor
if __name__ == "__main__":
    monitor = CertificateMonitor()
    monitor.run()
```

I'll continue with the Remote Access Security section, including advanced firewall configurations and intrusion detection. Would you like me to proceed?