# Security Monitoring Tools for Ethereum Server

This guide details the setup and confi
   ```

3. **Integrating with Alertmanager**:
   ```bash
   sudo nano /etc/alertmanager/alertmanager.yml
   ```
   
   Update the configuration to add webhooks:
   ```yaml
   receivers:
   - name: 'email-notifications'
     email_configs:
     - to: 'your-email@example.com'
       send_resolved: true
   
   - name: 'security-webhook'
     webhook_configs:
     - url: 'http://localhost:9888/alert'
       send_resolved: false
   
   route:
     group_by: ['alertname', 'job']
     group_wait: 30s
     group_interval: 5m
     repeat_interval: 4h
     receiver: 'email-notifications'
     routes:
     - match:
         severity: 'critical'
       receiver: 'security-webhook'
   ```

4. **Create a simple webhook receiver**:
   ```bash
   sudo nano /usr/local/bin/alert-webhook.py
   ```
   
   Add the following content:
   ```python
   #!/usr/bin/env python3
   
   from http.server import HTTPServer, BaseHTTPRequestHandler
   import json
   import subprocess
   import logging
   
   # Configure logging
   logging.basicConfig(filename='/var/log/alert-webhook.log', level=logging.INFO,
                      format='%(asctime)s - %(levelname)s - %(message)s')
   
   class AlertHandler(BaseHTTPRequestHandler):
       def do_POST(self):
           content_length = int(self.headers['Content-Length'])
           post_data = self.rfile.read(content_length)
           alert_data = json.loads(post_data.decode('utf-8'))
           
           logging.info(f"Received alert: {alert_data}")
           
           # Process alerts
           for alert in alert_data.get('alerts', []):
               labels = alert.get('labels', {})
               annotations = alert.get('annotations', {})
               
               alert_name = labels.get('alertname', 'Unknown')
               instance = labels.get('instance', 'Unknown')
               
               # Handle different types of alerts
               if alert_name == 'UnusualNetworkTraffic':
                   ip = instance.split(':')[0]
                   subprocess.call(['/usr/local/bin/block-ddos.sh', ip])
                   logging.info(f"Executed DDoS protection for {ip}")
               
               elif alert_name == 'EthereumNodeDown':
                   subprocess.call(['/usr/local/bin/recover-ethereum.sh'])
                   logging.info(f"Executed Ethereum recovery script")
           
           # Send response
           self.send_response(200)
           self.send_header('Content-type', 'text/plain')
           self.end_headers()
           self.wfile.write(b'Alert received and processed')
   
   # Start HTTP server
   if __name__ == '__main__':
       server = HTTPServer(('localhost', 9888), AlertHandler)
       logging.info('Starting webhook server on port 9888')
       server.serve_forever()
   ```

5. **Create systemd service for webhook**:
   ```bash
   sudo nano /etc/systemd/system/alert-webhook.service
   ```
   
   Add the following configuration:
   ```
   [Unit]
   Description=Prometheus Alertmanager Webhook Receiver
   After=network.target
   
   [Service]
   Type=simple
   User=root
   ExecStart=/usr/bin/python3 /usr/local/bin/alert-webhook.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **Start and enable webhook service**:
   ```bash
   sudo chmod +x /usr/local/bin/alert-webhook.py
   sudo systemctl daemon-reload
   sudo systemctl start alert-webhook
   sudo systemctl enable alert-webhook
   ```

## Implementing Network Traffic Analysis

Add network traffic analysis to detect potential intrusions.

### Installing and Configuring Zeek (formerly Bro)

1. **Install dependencies**:
   ```bash
   sudo apt-get install cmake make gcc g++ flex bison libpcap-dev libssl-dev python3-dev swig zlib1g-dev
   ```

2. **Install Zeek**:
   ```bash
   # Add Zeek repository
   echo 'deb http://download.opensuse.org/repositories/security:/zeek/xUbuntu_20.04/ /' | sudo tee /etc/apt/sources.list.d/security:zeek.list
   wget -nv https://download.opensuse.org/repositories/security:zeek/xUbuntu_20.04/Release.key -O Release.key
   sudo apt-key add - < Release.key
   
   # Install Zeek
   sudo apt-get update
   sudo apt-get install zeek
   ```

3. **Configure Zeek**:
   ```bash
   sudo nano /opt/zeek/etc/networks.cfg
   ```
   
   Add your local networks:
   ```
   # Example for a home network
   10.0.0.0/8          Private IP space
   172.16.0.0/12       Private IP space
   192.168.0.0/16      Private IP space
   ```

4. **Update Zeek configuration**:
   ```bash
   sudo nano /opt/zeek/etc/zeekctl.cfg
   ```
   
   Adjust settings as needed:
   ```
   LogRotationInterval = 3600
   LogExpireInterval = 30
   ```

5. **Configure logging**:
   ```bash
   sudo nano /opt/zeek/share/zeek/site/local.zeek
   ```
   
   Add these lines at the end of the file:
   ```
   # Load the detect-protocols scripts
   @load protocols/ssl/validate-certs
   @load protocols/ssh/detect-bruteforcing
   @load protocols/http/detect-sqli
   @load misc/detect-traceroute
   @load policy/frameworks/intel/seen
   ```

6. **Initialize and start Zeek**:
   ```bash
   sudo /opt/zeek/bin/zeekctl deploy
   ```

7. **Create integration with monitoring**:
   ```bash
   sudo nano /usr/local/bin/zeek-to-prometheus.sh
   ```
   
   Add the following script:
   ```bash
   #!/bin/bash
   
   METRICS_FILE="/var/lib/prometheus/node_exporter/zeek_metrics.prom"
   
   # Count SSH brute force attempts
   SSH_ATTEMPTS=$(grep "SSHBruteforcing::detected" /opt/zeek/logs/current/notice.log | wc -l)
   
   # Count SSL certificate issues
   SSL_ISSUES=$(grep "SSL::Invalid_Server_Cert" /opt/zeek/logs/current/notice.log | wc -l)
   
   # Count SQL injection attempts
   SQL_ATTEMPTS=$(grep "HTTP::SQL_Injection_Attacker" /opt/zeek/logs/current/notice.log | wc -l)
   
   # Write metrics in Prometheus format
   cat > ${METRICS_FILE}.$<<EOF
   # HELP zeek_ssh_brute_force_attempts Number of SSH brute force attempts
   # TYPE zeek_ssh_brute_force_attempts counter
   zeek_ssh_brute_force_attempts ${SSH_ATTEMPTS}
   
   # HELP zeek_ssl_cert_issues Number of SSL certificate issues
   # TYPE zeek_ssl_cert_issues counter
   zeek_ssl_cert_issues ${SSL_ISSUES}
   
   # HELP zeek_sql_injection_attempts Number of SQL injection attempts
   # TYPE zeek_sql_injection_attempts counter
   zeek_sql_injection_attempts ${SQL_ATTEMPTS}
   EOF
   
   # Atomically update the metrics file
   mv ${METRICS_FILE}.$ ${METRICS_FILE}
   ```

8. **Make script executable and add to cron**:
   ```bash
   sudo chmod +x /usr/local/bin/zeek-to-prometheus.sh
   sudo mkdir -p /var/lib/prometheus/node_exporter
   sudo chown prometheus:prometheus /var/lib/prometheus/node_exporter
   
   # Add to crontab
   echo "*/5 * * * * root /usr/local/bin/zeek-to-prometheus.sh" | sudo tee -a /etc/cron.d/zeek-metrics
   ```

9. **Update Node Exporter configuration**:
   ```bash
   sudo nano /etc/systemd/system/node_exporter.service
   ```
   
   Update ExecStart line to include:
   ```
   ExecStart=/usr/local/bin/node_exporter \
       --collector.filesystem \
       --collector.netdev \
       --collector.meminfo \
       --collector.cpu \
       --collector.diskstats \
       --collector.textfile.directory=/var/lib/prometheus/node_exporter \
       --web.listen-address=127.0.0.1:9100
   ```

10. **Restart Node Exporter**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl restart node_exporter
    ```

## Regular Security Auditing Procedures

Establish regular security auditing procedures to maintain your Ethereum server's security posture.

### Creating a Security Audit Checklist

1. **Weekly security tasks**:
   - Review system logs for unusual activity
   - Check for unusual network connections
   - Verify running processes
   - Review alert history
   - Check disk usage for unexpected changes
   - Verify Ethereum node synchronization
   - Review authentication logs

2. **Monthly security tasks**:
   - Update all system packages
   - Run full system scan with RKHunter
   - Run Lynis security audit
   - Test backup and recovery procedures
   - Review all firewall rules
   - Check for open ports with nmap
   - Verify system user accounts

3. **Quarterly security tasks**:
   - Rotate SSH keys
   - Regenerate VPN certificates
   - Test intrusion detection response
   - Review and update alerting rules
   - Test failover procedures
   - Conduct penetration testing
   - Review overall security architecture

### Implementing Security Audit Automation

1. **Create a master audit script**:
   ```bash
   sudo nano /usr/local/bin/security-audit.sh
   ```
   
   Add the following content:
   ```bash
   #!/bin/bash
   
   # Security Audit Script
   
   LOG_DIR="/var/log/security-audit"
   REPORT_FILE="${LOG_DIR}/audit-report-$(date +%Y-%m-%d).txt"
   
   # Create log directory if it doesn't exist
   mkdir -p ${LOG_DIR}
   
   # Start report
   echo "====================================" > ${REPORT_FILE}
   echo "Security Audit Report: $(date)" >> ${REPORT_FILE}
   echo "====================================" >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # Check for available updates
   echo "System Update Status:" >> ${REPORT_FILE}
   apt-get --just-print upgrade | grep "upgraded," >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # List open ports
   echo "Open Network Ports:" >> ${REPORT_FILE}
   netstat -tuln | grep LISTEN >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # Check for failed login attempts
   echo "Recent Failed Login Attempts:" >> ${REPORT_FILE}
   grep "Failed password" /var/log/auth.log | tail -n 20 >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # Check for unusual processes
   echo "Top CPU Consuming Processes:" >> ${REPORT_FILE}
   ps aux --sort=-%cpu | head -n 10 >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # Check disk usage
   echo "Disk Usage:" >> ${REPORT_FILE}
   df -h >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # Run quick malware scan
   echo "Malware Scan Results:" >> ${REPORT_FILE}
   freshclam -v >> ${REPORT_FILE} 2>&1
   clamscan --recursive=yes --infected /etc /home /var/www >> ${REPORT_FILE} 2>&1
   echo "" >> ${REPORT_FILE}
   
   # Check Ethereum node status
   echo "Ethereum Node Status:" >> ${REPORT_FILE}
   systemctl status geth | grep Active >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # List recently modified executables
   echo "Recently Modified Executables:" >> ${REPORT_FILE}
   find /usr/bin /usr/sbin /bin /sbin -type f -mtime -7 -ls >> ${REPORT_FILE}
   echo "" >> ${REPORT_FILE}
   
   # Run Lynis partial scan
   echo "Lynis Security Scan:" >> ${REPORT_FILE}
   lynis audit system --quiet --no-colors --report-file=${REPORT_FILE}.lynis
   cat ${REPORT_FILE}.lynis >> ${REPORT_FILE}
   rm ${REPORT_FILE}.lynis
   
   # Email the report
   cat ${REPORT_FILE} | mail -s "Security Audit Report - $(date +%Y-%m-%d)" your-email@example.com
   
   echo "Security audit completed. Report saved to ${REPORT_FILE}"
   ```

2. **Schedule regular audits**:
   ```bash
   sudo chmod +x /usr/local/bin/security-audit.sh
   
   # Weekly audit
   echo "0 1 * * 1 root /usr/local/bin/security-audit.sh" | sudo tee -a /etc/cron.d/security-audit
   ```

## Emergency Response Plan

Create a comprehensive emergency response plan to address security incidents.

### Documenting Incident Response Procedures

1. **Create incident response document**:
   ```bash
   sudo mkdir -p /etc/security/incident-response
   sudo nano /etc/security/incident-response/README.md
   ```
   
   Add the following content:
   ```markdown
   # Ethereum Server Security Incident Response Procedures
   
   ## Detection Phase
   
   1. **Confirm the incident**:
      - Review alert details
      - Verify through multiple sources
      - Document initial findings
   
   2. **Initial assessment**:
      - Determine incident severity
      - Identify affected systems
      - Estimate potential impact
   
   ## Containment Phase
   
   1. **For network attacks**:
      - Execute: `/usr/local/bin/block-ddos.sh [attacking_IP]`
      - Review firewall logs
      - Consider temporarily disconnecting from internet
   
   2. **For system compromise**:
      - Isolate affected systems
      - Disable compromised accounts
      - Preserve evidence for forensic analysis
   
   3. **For Ethereum node issues**:
      - Stop the node: `systemctl stop geth`
      - Backup blockchain data
      - Check for unauthorized transactions
   
   ## Eradication Phase
   
   1. **Remove malware/backdoors**:
      - Run full system scan: `rkhunter --check --skip-keypress`
      - Remove compromised files
      - Check for persistence mechanisms
   
   2. **Patch vulnerabilities**:
      - Update all packages: `apt update && apt upgrade -y`
      - Apply security patches
      - Fix misconfigurations
   
   ## Recovery Phase
   
   1. **Restore services**:
      - Restart critical services
      - Verify system integrity
      - Monitor for recurring issues
   
   2. **For Ethereum node**:
      - Verify blockchain integrity
      - Restart node: `systemctl start geth`
      - Monitor synchronization
   
   ## Post-Incident Activities
   
   1. **Documentation**:
      - Complete incident report
      - Document lessons learned
      - Update response procedures
   
   2. **System hardening**:
      - Implement additional security measures
      - Update monitoring rules
      - Conduct follow-up security audit
   
   ## Emergency Contacts
   
   - **System Administrator**: [Name, Phone, Email]
   - **Network Provider**: [Company, Support Number]
   - **Ethereum Specialist**: [Name, Phone, Email]
   - **Security Team**: [Name, Phone, Email]
   ```

2. **Create lockdown script**:
   ```bash
   sudo nano /usr/local/bin/emergency-lockdown.sh
   ```
   
   Add the following content:
   ```bash
   #!/bin/bash
   
   # Emergency Lockdown Script
   
   # Log the execution
   logger -t security "ALERT: Emergency lockdown procedure initiated"
   
   # Stop Ethereum node to prevent further transactions
   systemctl stop geth
   
   # Block all non-essential traffic
   iptables -F
   iptables -P INPUT DROP
   iptables -P FORWARD DROP
   iptables -P OUTPUT DROP
   
   # Allow only SSH from trusted IPs (adjust as needed)
   iptables -A INPUT -p tcp --dport 22 -s 192.168.40.0/24 -j ACCEPT
   iptables -A OUTPUT -p tcp --sport 22 -d 192.168.40.0/24 -j ACCEPT
   
   # Allow DNS for basic functionality
   iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
   iptables -A INPUT -p udp --sport 53 -j ACCEPT
   
   # Take forensic snapshot if LVM is used
   if lvs | grep -q "root"; then
     lvcreate -s -n root_snapshot -L 5G /dev/mapper/vg-root
     logger -t security "Created LVM snapshot for forensic analysis"
   fi
   
   # Collect critical logs
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   mkdir -p /root/security_incident_${TIMESTAMP}
   cp -r /var/log/* /root/security_incident_${TIMESTAMP}/
   journalctl -xe > /root/security_incident_${TIMESTAMP}/journalctl.log
   
   # Generate process list and network connections
   ps aux > /root/security_incident_${TIMESTAMP}/processes.log
   netstat -tulpn > /root/security_incident_${TIMESTAMP}/netstat.log
   lsof -i > /root/security_incident_${TIMESTAMP}/lsof.log
   
   # Send alert notification
   echo "CRITICAL SECURITY ALERT: Emergency lockdown has been activated on $(hostname) at $(date)" | mail -s "EMERGENCY: Security Lockdown Activated" your-email@example.com
   
   echo "Emergency lockdown completed. System is now in restricted state."
   echo "Contact security team before restoring normal operation."
   ```

3. **Make script executable**:
   ```bash
   sudo chmod +x /usr/local/bin/emergency-lockdown.sh
   ```

## Mobile Security Monitoring Dashboards

Create mobile-optimized dashboards for security monitoring on the go.

### Setting Up Mobile-Friendly Grafana Dashboards

1. **Create a mobile security dashboard**:
   - Login to Grafana
   - Click "+" → "Dashboard"
   - Add title "Mobile Security Dashboard"
   - Set refresh rate to 1m

2. **Add critical security panels**:
   - **System Load**:
     - Add panel → Graph
     - Metric: `node_load1{instance="localhost:9100"}`
     - Title: "System Load"
   
   - **Memory Usage**:
     - Add panel → Gauge
     - Metric: `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100`
     - Title: "Memory Usage %"
     - Thresholds: 75 (yellow), 90 (red)
   
   - **Disk Usage**:
     - Add panel → Gauge
     - Metric: `(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_free_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100`
     - Title: "Disk Usage %"
     - Thresholds: 75 (yellow), 90 (red)
   
   - **Ethereum Node Status**:
     - Add panel → Stat
     - Metric: `up{job="ethereum"}`
     - Title: "Ethereum Node"
     - Value mapping: 1=Online (green), 0=Offline (red)
   
   - **Failed SSH Attempts**:
     - Add panel → Graph
     - Metric: `rate(node_log_file_content_logins_failed[5m])`
     - Title: "Failed SSH Attempts"
   
   - **Zeek Security Events**:
     - Add panel → Graph
     - Metric: `zeek_ssh_brute_force_attempts + zeek_sql_injection_attempts`
     - Title: "Security Events"
   
   - **Active Alerts**:
     - Add panel → Table
     - Metric: `ALERTS{alertstate="firing"}`
     - Title: "Active Alerts"
     - Columns: alertname, severity, instance

3. **Optimize for mobile**:
   - Edit dashboard settings
   - Set "Time picker" to show last 6 hours by default
   - Arrange panels in a single column for easy scrolling
   - Use larger fonts and clear colors for visibility on small screens

4. **Save dashboard** and access from Grafana mobile app

## Periodic Security Report Generation

Set up automated security reports to monitor your Ethereum server's security status.

### Configuring Weekly Security Reports

1. **Create report generation script**:
   ```bash
   sudo nano /usr/local/bin/generate-security-report.sh
   ```
   
   Add the following content:
   ```bash
   #!/bin/bash
   
   # Weekly Security Report Generator
   
   REPORT_DIR="/var/reports/security"
   DATE=$(date +%Y-%m-%d)
   REPORT_FILE="${REPORT_DIR}/security-report-${DATE}.html"
   
   # Create report directory if it doesn't exist
   mkdir -p ${REPORT_DIR}
   
   # Start HTML report
   cat > ${REPORT_FILE} << EOF
   <!DOCTYPE html>
   <html>
   <head>
     <title>Security Report: ${DATE}</title>
     <style>
       body { font-family: Arial, sans-serif; margin: 40px; }
       h1 { color: #333366; }
       h2 { color: #333366; margin-top: 30px; }
       table { border-collapse: collapse; width: 100%; }
       th, td { text-align: left; padding: 8px; }
       tr:nth-child(even) { background-color: #f2f2f2; }
       th { background-color: #333366; color: white; }
       .critical { color: red; font-weight: bold; }
       .warning { color: orange; }
       .good { color: green; }
     </style>
   </head>
   <body>
     <h1>Ethereum Server Security Report</h1>
     <p>Generated on: $(date)</p>
     <p>Server: $(hostname)</p>
     
     <h2>System Status</h2>
     <table>
       <tr>
         <th>Metric</th>
         <th>Value</th>
         <th>Status</th>
       </tr>
       <tr>
         <td>Uptime</td>
         <td>$(uptime -p)</td>
         <td class="good">OK</td>
       </tr>
       <tr>
         <td>Load Average</td>
         <td>$(uptime | awk -F'load average:' '{print $2}')</td>
         <td class="$(awk 'BEGIN {if ($(cat /proc/loadavg | cut -d " " -f1) > 2) print "warning"; else print "good";}')">
           $(awk 'BEGIN {if ($(cat /proc/loadavg | cut -d " " -f1) > 2) print "HIGH"; else print "OK";}')
         </td>
       </tr>
       <tr>
         <td>Memory Usage</td>
         <td>$(free -h | grep Mem | awk '{print $3 " / " $2}')</td>
         <td class="$(free | grep Mem | awk '{if ($3/$2*100 > 80) print "warning"; else print "good";}')">
           $(free | grep Mem | awk '{if ($3/$2*100 > 80) print "HIGH"; else print "OK";}')
         </td>
       </tr>
       <tr>
         <td>Disk Usage</td>
         <td>$(df -h / | grep / | awk '{print $5 " (" $3 " / " $2 ")"}')</td>
         <td class="$(df -h / | grep / | awk '{gsub("%","",$5); if ($5 > 80) print "warning"; else print "good";}')">
           $(df -h / | grep / | awk '{gsub("%","",$5); if ($5 > 80) print "HIGH"; else print "OK";}')
         </td>
       </tr>
       <tr>
         <td>Failed Logins (7 days)</td>
         <td>$(grep "Failed password" /var/log/auth.log | wc -l)</td>
         <td class="$(grep "Failed password" /var/log/auth.log | wc -l | awk '{if ($1 > 50) print "warning"; else print "good";}')">
           $(grep "Failed password" /var/log/auth.log | wc -l | awk '{if ($1 > 50) print "HIGH"; else print "OK";}')
         </td>
       </tr>
     </table>
     
     <h2>Ethereum Node Status</h2>
     <table>
       <tr>
         <th>Metric</th>
         <th>Value</th>
         <th>Status</th>
       </tr>
       <tr>
         <td>Service Status</td>
         <td>$(systemctl is-active geth)</td>
         <td class="$(systemctl is-active geth | awk '{if ($1 == "active") print "good"; else print "critical";}')">
           $(systemctl is-active geth | awk '{if ($1 == "active") print "RUNNING"; else print "STOPPED";}')
         </td>
       </tr>
     </table>
     
     <h2>Security Scan Results</h2>
     <table>
       <tr>
         <th>Check</th>
         <th>Result</th>
         <th>Status</th>
       </tr>
       <tr>
         <td>RKHunter</td>
         <td>$(rkhunter --check --skip-keypress --rwo | grep -c "Warning" || echo "0") warnings</td>
         <td class="$(rkhunter --check --skip-keypress --rwo | grep -c "Warning" | awk '{if ($1 > 0) print "warning"; else print "good";}')">
           $(rkhunter --check --skip-keypress --rwo | grep -c "Warning" | awk '{if ($1 > 0) print "CHECK NEEDED"; else print "CLEAN";}')
         </td>
       </tr>
       <tr>
         <td>Updated Packages</td>
         <td>$(apt-get --just-print upgrade | grep -c "upgraded,")</td>
         <td class="$(apt-get --just-print upgrade | grep -c "upgraded," | awk '{if ($1 > 10) print "warning"; else print "good";}')">
           $(apt-get --just-print upgrade | grep -c "upgraded," | awk '{if ($1 > 10) print "UPDATES NEEDED"; else print "UPDATED";}')
         </td>
       </tr>
       <tr>
         <td>Open Ports</td>
         <td>$(netstat -tuln | grep LISTEN | wc -l)</td>
         <td class="$(netstat -tuln | grep LISTEN | wc -l | awk '{if ($1 > 10) print "warning"; else print "good";}')">
           $(netstat -tuln | grep LISTEN | wc -l | awk '{if ($1 > 10) print "REVIEW NEEDED"; else print "OK";}')
         </td>
       </tr>
     </table>
     
     <h2>Recent Security Events</h2>
     <table>
       <tr>
         <th>Event Type</th>
         <th>Count</th>
         <th>Status</th>
       </tr>
       <tr>
         <td>SSH Brute Force Attempts</td>
         <td>$(grep "Failed password" /var/log/auth.log | wc -l)</td>
         <td class="$(grep "Failed password" /var/log/auth.log | wc -l | awk '{if ($1 > 20) print "warning"; else print "good";}')">
           $(grep "Failed password" /var/log/auth.log | wc -l | awk '{if ($1 > 20) print "INVESTIGATE"; else print "NORMAL";}')
         </td>
       </tr>
       <tr>
         <td>Firewall Blocks</td>
         <td>$(grep "UFW BLOCK" /var/log/syslog | wc -l)</td>
         <td class="$(grep "UFW BLOCK" /var/log/syslog | wc -l | awk '{if ($1 > 1000) print "warning"; else print "good";}')">
           $(grep "UFW BLOCK" /var/log/syslog | wc -l | awk '{if ($1 > 1000) print "INVESTIGATE"; else print "NORMAL";}')
         </td>
       </tr>
     </table>
     
     <h2>Recommendations</h2>
     <ul>
       $(apt-get --just-print upgrade | grep -q "upgraded," && echo "<li class='warning'>System updates are available. Consider updating soon.</li>" || echo "<li class='good'>System is up to date.</li>")
       $(df -h / | grep / | awk '{gsub("%","",$5); if ($5 > 80) print "<li class=\"warning\">Disk space is running low. Consider cleanup.</li>";}')
       $(systemctl is-active geth | grep -q "inactive" && echo "<li class='critical'>Ethereum node is not running. Immediate attention required.</li>")
     </ul>
     
     <p><small>This report is generated automatically. Please contact your system administrator for any questions.</small></p>
   </body>
   </html>
   EOF
   
   # Email the report
   echo "Weekly security report is ready. Please see the attached HTML file." | mail -s "Security Report ${DATE}" -a ${REPORT_FILE} your-email@example.com
   
   echo "Security report generated: ${REPORT_FILE}"
   ```

2. **Make script executable and schedule it**:
   ```bash
   sudo chmod +x /usr/local/bin/generate-security-report.sh
   
   # Add to weekly cron
   echo "0 7 * * 0 root /usr/local/bin/generate-security-report.sh" | sudo tee -a /etc/cron.d/security-report
   ```

## Integration with External Security Services

Integrate with external security services for additional protection and monitoring.

### Setting Up Crowdsec for Community-Based Threat Intelligence

1. **Install Crowdsec**:
   ```bash
   curl -s https://packagecloud.io/install/repositories/crowdsec/crowdsec/script.deb.sh | sudo bash
   sudo apt-get install crowdsec
   ```

2. **Install bouncer**:
   ```bash
   sudo apt-get install crowdsec-firewall-bouncer-iptables
   ```

3. **Configure Crowdsec**:
   ```bash
   sudo cscli collections install crowdsecurity/linux
   sudo cscli collections install crowdsecurity/sshd
   sudo systemctl restart crowdsec
   ```

4. **Check Crowdsec status**:
   ```bash
   sudo cscli metrics
   sudo cscli alerts list
   ```

5. **Integrate with Prometheus**:
   ```bash
   # Install metrics exporter
   sudo apt-get install crowdsec-prometheus-exporter
   
   # Add to Prometheus configuration
   sudo nano /etc/prometheus/prometheus.yml
   ```
   
   Add to scrape_configs:
   ```yaml
   - job_name: 'crowdsec'
     static_configs:
       - targets: ['localhost:6060']
   ```

6. **Restart Prometheus**:
   ```bash
   sudo systemctl restart prometheus
   ```

### Setting Up OSSEC for Host-Based Intrusion Detection

1. **Install OSSEC**:
   ```bash
   sudo apt-get install build-essential
   wget https://github.com/ossec/ossec-hids/archive/3.6.0.tar.gz
   tar -xzf 3.6.0.tar.gz
   cd ossec-hids-3.6.0
   ```

2. **Configure and install**:
   ```bash
   sudo ./install.sh
   ```
   
   Follow the interactive prompts:
   - Choose "local" installation
   - Provide your email for alerts
   - Configure the integrity check daemon
   - Enable rootkit detection

3. **Start OSSEC**:
   ```bash
   sudo /var/ossec/bin/ossec-control start
   ```

4. **Create custom rules for Ethereum**:
   ```bash
   sudo nano /var/ossec/rules/local_rules.xml
   ```
   
   Add custom rules:
   ```xml
   <group name="ethereum,">
     <rule id="100100" level="10">
       <match>Failed to start Geth</match>
       <description>Ethereum node failed to start</description>
       <group>service_availability,</group>
     </rule>
   
     <rule id="100101" level="12">
       <match>unauthorized access attempt</match>
       <regex>rpc</regex>
       <description>Unauthorized RPC access attempt</description>
       <group>attack,</group>
     </rule>
   </group>
   ```

5. **Restart OSSEC to apply rules**:
   ```bash
   sudo /var/ossec/bin/ossec-control restart
   ```

## Creating a Security Monitoring Dashboard in Grafana

Create a comprehensive security monitoring dashboard in Grafana.

### Setting Up a Complete Security Dashboard

1. **Log into Grafana** and create a new dashboard.

2. **Add system health panels**:
   - System load average (graph)
   - Memory usage (gauge)
   - Disk usage (gauge)
   - Network traffic (graph)

3. **Add security-specific panels**:
   - Failed login attempts (counter/graph)
   - Failed SSH authentication (counter/graph)
   - Firewall blocked connections (counter/graph)
   - Zeek security events (graph)
   - OSSEC alerts (graph)
   - CrowdSec detections (counter)

4. **Add Ethereum-specific panels**:
   - Node status (stat panel)
   - Sync status (gauge)
   - Peer count (gauge)
   - Transaction pool size (graph)
   - RPC requests (graph)

5. **Add alert overview panels**:
   - Active alerts table
   - Alert history graph
   - Alert count by severity

6. **Create dashboard rows by category**:
   - System Status
   - Network Security
   - Host Security
   - Ethereum Node
   - Alerts Overview

7. **Configure dashboard settings**:
   - Auto-refresh: 1m
   - Time range controls
   - Dashboard variables for filtering
   - Templating for reusability

8. **Save the dashboard** and set permissions.

## Regular Security Review

Schedule and conduct regular security reviews to maintain your Ethereum server's security posture.

### Security Review Process

1. **Weekly review tasks**:
   - Review monitoring dashboards for anomalies
   - Check alert history for patterns
   - Verify backups are working properly
   - Inspect logs for unusual activities
   - Check system updates and apply if needed

2. **Monthly review tasks**:
   - Review firewall rules and network segmentation
   - Audit user accounts and access privileges
   - Verify VPN configuration and access logs
   - Run security scanning tools (Lynis, rkhunter)
   - Check for updates to Ethereum node software

3. **Quarterly review tasks**:
   - Conduct thorough security audit
   - Perform penetration testing
   - Review security architecture
   - Update security policies and procedures
   - Test disaster recovery plans

4. **Document review findings**:
   - Maintain a security log book
   - Track vulnerabilities and mitigations
   - Update security procedures as needed
   - Document lessons learned

5. **Create a review checklist**:
   ```bash
   sudo nano /etc/security/review-checklist.md
   ```
   
   Add detailed checklist items for each review period.
         guration of comprehensive security monitoring for your Ethereum server, enabling you to detect and respond to potential security threats.

## Monitoring Strategy Overview

A robust security monitoring strategy encompasses several layers:

1. **System-level monitoring**: CPU, memory, disk, and network usage
2. **Service-level monitoring**: Ethereum node status and performance
3. **Security-specific monitoring**: Intrusion detection, log analysis, and anomaly detection
4. **Alerting and response**: Notification and automated response to security events

## Prometheus and Grafana Setup

Prometheus and Grafana form the backbone of your monitoring infrastructure.

### Installing Prometheus

1. **Create a system user for Prometheus**:
   ```bash
   sudo useradd -rs /bin/false prometheus
   ```

2. **Download and install Prometheus**:
   ```bash
   # Download the latest version
   wget https://github.com/prometheus/prometheus/releases/download/v2.43.0/prometheus-2.43.0.linux-amd64.tar.gz
   
   # Extract the archive
   tar xvfz prometheus-2.43.0.linux-amd64.tar.gz
   
   # Create directories
   sudo mkdir -p /etc/prometheus /var/lib/prometheus
   
   # Copy binaries
   sudo cp prometheus-2.43.0.linux-amd64/prometheus /usr/local/bin/
   sudo cp prometheus-2.43.0.linux-amd64/promtool /usr/local/bin/
   
   # Copy configuration files
   sudo cp -r prometheus-2.43.0.linux-amd64/consoles /etc/prometheus
   sudo cp -r prometheus-2.43.0.linux-amd64/console_libraries /etc/prometheus
   
   # Set ownership
   sudo chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus
   ```

3. **Configure Prometheus**:
   ```bash
   sudo nano /etc/prometheus/prometheus.yml
   ```
   
   Add the following configuration:
   ```yaml
   global:
     scrape_interval: 15s
     evaluation_interval: 15s
   
   alerting:
     alertmanagers:
       - static_configs:
           - targets: ['localhost:9093']
   
   rule_files:
     - "/etc/prometheus/rules/*.yml"
   
   scrape_configs:
     - job_name: 'prometheus'
       static_configs:
         - targets: ['localhost:9090']
     
     - job_name: 'node_exporter'
       static_configs:
         - targets: ['localhost:9100']
     
     - job_name: 'ethereum'
       metrics_path: /metrics
       static_configs:
         - targets: ['localhost:6060']
     
     - job_name: 'blackbox'
       metrics_path: /probe
       params:
         module: [http_2xx]
       static_configs:
         - targets:
           - http://localhost:8545  # Ethereum JSON-RPC
       relabel_configs:
         - source_labels: [__address__]
           target_label: __param_target
         - source_labels: [__param_target]
           target_label: instance
         - target_label: __address__
           replacement: localhost:9115  # Blackbox exporter address
   ```

4. **Create a systemd service for Prometheus**:
   ```bash
   sudo nano /etc/systemd/system/prometheus.service
   ```
   
   Add the following configuration:
   ```
   [Unit]
   Description=Prometheus Time Series Collection and Processing Server
   Wants=network-online.target
   After=network-online.target
   
   [Service]
   User=prometheus
   Group=prometheus
   Type=simple
   ExecStart=/usr/local/bin/prometheus \
       --config.file /etc/prometheus/prometheus.yml \
       --storage.tsdb.path /var/lib/prometheus/ \
       --web.console.templates=/etc/prometheus/consoles \
       --web.console.libraries=/etc/prometheus/console_libraries \
       --web.listen-address=127.0.0.1:9090
   
   [Install]
   WantedBy=multi-user.target
   ```

5. **Start and enable Prometheus**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start prometheus
   sudo systemctl enable prometheus
   ```

### Installing Grafana

1. **Add Grafana repository**:
   ```bash
   sudo apt-get install -y apt-transport-https software-properties-common
   wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
   echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
   ```

2. **Install Grafana**:
   ```bash
   sudo apt-get update
   sudo apt-get install grafana
   ```

3. **Configure Grafana for secure access**:
   ```bash
   sudo nano /etc/grafana/grafana.ini
   ```
   
   Update these settings:
   ```ini
   [server]
   protocol = https
   http_addr = 127.0.0.1
   cert_file = /etc/grafana/certificates/cert.pem
   cert_key = /etc/grafana/certificates/key.pem
   
   [security]
   admin_user = admin
   admin_password = your-strong-password
   disable_gravatar = true
   cookie_secure = true
   
   [users]
   allow_sign_up = false
   auto_assign_org = true
   auto_assign_org_role = Viewer
   ```

4. **Generate self-signed certificates** (for development, use proper certs in production):
   ```bash
   sudo mkdir -p /etc/grafana/certificates
   sudo openssl req -x509 -newkey rsa:4096 -keyout /etc/grafana/certificates/key.pem -out /etc/grafana/certificates/cert.pem -days 365 -nodes
   sudo chown -R grafana:grafana /etc/grafana/certificates
   ```

5. **Start and enable Grafana**:
   ```bash
   sudo systemctl start grafana-server
   sudo systemctl enable grafana-server
   ```

## Installing Monitoring Exporters

These exporters collect metrics from your system and Ethereum node.

### Node Exporter for System Metrics

1. **Create a system user**:
   ```bash
   sudo useradd -rs /bin/false node_exporter
   ```

2. **Download and install Node Exporter**:
   ```bash
   # Download the latest version
   wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
   
   # Extract
   tar xvfz node_exporter-1.5.0.linux-amd64.tar.gz
   
   # Copy binary
   sudo cp node_exporter-1.5.0.linux-amd64/node_exporter /usr/local/bin/
   sudo chown node_exporter:node_exporter /usr/local/bin/node_exporter
   ```

3. **Create systemd service**:
   ```bash
   sudo nano /etc/systemd/system/node_exporter.service
   ```
   
   Add the following configuration:
   ```
   [Unit]
   Description=Node Exporter
   Wants=network-online.target
   After=network-online.target
   
   [Service]
   User=node_exporter
   Group=node_exporter
   Type=simple
   ExecStart=/usr/local/bin/node_exporter \
       --collector.filesystem \
       --collector.netdev \
       --collector.meminfo \
       --collector.cpu \
       --collector.diskstats \
       --web.listen-address=127.0.0.1:9100
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Start and enable Node Exporter**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start node_exporter
   sudo systemctl enable node_exporter
   ```

### Blackbox Exporter for Endpoint Monitoring

1. **Create a system user**:
   ```bash
   sudo useradd -rs /bin/false blackbox_exporter
   ```

2. **Download and install Blackbox Exporter**:
   ```bash
   # Download
   wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.23.0/blackbox_exporter-0.23.0.linux-amd64.tar.gz
   
   # Extract
   tar xvfz blackbox_exporter-0.23.0.linux-amd64.tar.gz
   
   # Create config directory
   sudo mkdir -p /etc/blackbox_exporter
   
   # Copy binary and config
   sudo cp blackbox_exporter-0.23.0.linux-amd64/blackbox_exporter /usr/local/bin/
   sudo cp blackbox_exporter-0.23.0.linux-amd64/blackbox.yml /etc/blackbox_exporter/
   sudo chown blackbox_exporter:blackbox_exporter /usr/local/bin/blackbox_exporter
   sudo chown -R blackbox_exporter:blackbox_exporter /etc/blackbox_exporter
   ```

3. **Configure Blackbox Exporter**:
   ```bash
   sudo nano /etc/blackbox_exporter/blackbox.yml
   ```
   
   Add the following configuration:
   ```yaml
   modules:
     http_2xx:
       prober: http
       http:
         preferred_ip_protocol: ip4
         fail_if_ssl: false
         fail_if_not_ssl: false
         tls_config:
           insecure_skip_verify: true
   
     tcp_connect:
       prober: tcp
       tcp:
         preferred_ip_protocol: ip4
   
     icmp:
       prober: icmp
       icmp:
         preferred_ip_protocol: ip4
   ```

4. **Create systemd service**:
   ```bash
   sudo nano /etc/systemd/system/blackbox_exporter.service
   ```
   
   Add the following configuration:
   ```
   [Unit]
   Description=Blackbox Exporter
   Wants=network-online.target
   After=network-online.target
   
   [Service]
   User=blackbox_exporter
   Group=blackbox_exporter
   Type=simple
   ExecStart=/usr/local/bin/blackbox_exporter \
       --config.file=/etc/blackbox_exporter/blackbox.yml \
       --web.listen-address=127.0.0.1:9115
   
   [Install]
   WantedBy=multi-user.target
   ```

5. **Start and enable Blackbox Exporter**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start blackbox_exporter
   sudo systemctl enable blackbox_exporter
   ```

### Geth Exporter for Ethereum Metrics

The Geth client already provides metrics on port 6060 when started with the `--metrics` flag.

1. **Update your Geth service** to include metrics:
   ```bash
   sudo nano /etc/systemd/system/geth.service
   ```
   
   Ensure the ExecStart line includes:
   ```
   ExecStart=/usr/bin/geth ... --metrics --metrics.addr 127.0.0.1 --metrics.port 6060
   ```

2. **Restart Geth**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart geth
   ```

## Setting Up Alertmanager

Alertmanager handles alerts from Prometheus and routes them to receivers like email or messaging services.

1. **Download and install Alertmanager**:
   ```bash
   # Download
   wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz
   
   # Extract
   tar xvfz alertmanager-0.25.0.linux-amd64.tar.gz
   
   # Create directories
   sudo mkdir -p /etc/alertmanager /var/lib/alertmanager
   
   # Copy binary and configuration
   sudo cp alertmanager-0.25.0.linux-amd64/alertmanager /usr/local/bin/
   sudo cp alertmanager-0.25.0.linux-amd64/amtool /usr/local/bin/
   sudo cp alertmanager-0.25.0.linux-amd64/alertmanager.yml /etc/alertmanager/
   sudo chown -R prometheus:prometheus /etc/alertmanager /var/lib/alertmanager
   ```

2. **Configure Alertmanager**:
   ```bash
   sudo nano /etc/alertmanager/alertmanager.yml
   ```
   
   Add the following configuration (replace with your details):
   ```yaml
   global:
     smtp_smarthost: 'smtp.gmail.com:587'
     smtp_from: 'alertmanager@example.com'
     smtp_auth_username: 'your-email@gmail.com'
     smtp_auth_password: 'your-app-password'
     smtp_require_tls: true
   
   route:
     group_by: ['alertname', 'job']
     group_wait: 30s
     group_interval: 5m
     repeat_interval: 4h
     receiver: 'email-notifications'
   
   receivers:
   - name: 'email-notifications'
     email_configs:
     - to: 'your-email@example.com'
       send_resolved: true
   ```

3. **Create systemd service**:
   ```bash
   sudo nano /etc/systemd/system/alertmanager.service
   ```
   
   Add the following configuration:
   ```
   [Unit]
   Description=Alertmanager for Prometheus
   Wants=network-online.target
   After=network-online.target
   
   [Service]
   User=prometheus
   Group=prometheus
   Type=simple
   ExecStart=/usr/local/bin/alertmanager \
     --config.file=/etc/alertmanager/alertmanager.yml \
     --storage.path=/var/lib/alertmanager \
     --web.listen-address=127.0.0.1:9093
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Start and enable Alertmanager**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start alertmanager
   sudo systemctl enable alertmanager
   ```

## Creating Alert Rules

Configure Prometheus alert rules to trigger notifications for security and performance issues.

1. **Create rules directory**:
   ```bash
   sudo mkdir -p /etc/prometheus/rules
   ```

2. **Create system alert rules**:
   ```bash
   sudo nano /etc/prometheus/rules/system_alerts.yml
   ```
   
   Add the following rules:
   ```yaml
   groups:
   - name: system_alerts
     rules:
     - alert: HighCPULoad
       expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "High CPU load (instance {{ $labels.instance }})"
         description: "CPU load is > 80%\n  VALUE = {{ $value }}\n  LABELS = {{ $labels }}"
     
     - alert: HighMemoryUsage
       expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "High memory usage (instance {{ $labels.instance }})"
         description: "Memory usage is > 90%\n  VALUE = {{ $value }}\n  LABELS = {{ $labels }}"
     
     - alert: HighDiskUsage
       expr: (node_filesystem_size_bytes{fstype!="tmpfs"} - node_filesystem_free_bytes{fstype!="tmpfs"}) / node_filesystem_size_bytes{fstype!="tmpfs"} * 100 > 85
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "High disk usage (instance {{ $labels.instance }})"
         description: "Disk usage is > 85%\n  VALUE = {{ $value }}\n  LABELS = {{ $labels }}"
   ```

3. **Create Ethereum alert rules**:
   ```bash
   sudo nano /etc/prometheus/rules/ethereum_alerts.yml
   ```
   
   Add the following rules:
   ```yaml
   groups:
   - name: ethereum_alerts
     rules:
     - alert: EthereumNodeDown
       expr: up{job="ethereum"} == 0
       for: 2m
       labels:
         severity: critical
       annotations:
         summary: "Ethereum node is down (instance {{ $labels.instance }})"
         description: "Ethereum node has been down for more than 2 minutes."
     
     - alert: LowPeerCount
       expr: ethereum_p2p_peers < 5
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "Low peer count (instance {{ $labels.instance }})"
         description: "Ethereum node has less than 5 peers\n  VALUE = {{ $value }}\n  LABELS = {{ $labels }}"
     
     - alert: ChainSyncIssue
       expr: time() - ethereum_blockchain_head_timestamp > 600
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "Blockchain sync issue (instance {{ $labels.instance }})"
         description: "Ethereum blockchain is more than 10 minutes behind\n  VALUE = {{ $value }}\n  LABELS = {{ $labels }}"
   ```

4. **Create security alert rules**:
   ```bash
   sudo nano /etc/prometheus/rules/security_alerts.yml
   ```
   
   Add the following rules:
   ```yaml
   groups:
   - name: security_alerts
     rules:
     - alert: UnusualNetworkTraffic
       expr: rate(node_network_receive_bytes_total[5m]) > 10 * 1024 * 1024
       for: 10m
       labels:
         severity: warning
       annotations:
         summary: "Unusual network traffic (instance {{ $labels.instance }})"
         description: "Network receive traffic is higher than normal\n  VALUE = {{ $value }} bytes/s\n  LABELS = {{ $labels }}"
     
     - alert: UnusualDiskActivity
       expr: rate(node_disk_io_time_seconds_total[5m]) > 0.5
       for: 10m
       labels:
         severity: warning
       annotations:
         summary: "Unusual disk activity (instance {{ $labels.instance }})"
         description: "Disk I/O is higher than normal\n  VALUE = {{ $value }}\n  LABELS = {{ $labels }}"
     
     - alert: EndpointDown
       expr: probe_success{job="blackbox"} == 0
       for: 2m
       labels:
         severity: critical
       annotations:
         summary: "Endpoint down (instance {{ $labels.instance }})"
         description: "Endpoint {{ $labels.instance }} is down"
   ```

5. **Set ownership and restart Prometheus**:
   ```bash
   sudo chown -R prometheus:prometheus /etc/prometheus/rules
   sudo systemctl restart prometheus
   ```

## Setting Up Grafana Dashboards

Configure Grafana dashboards to visualize system, Ethereum, and security metrics.

1. **Access Grafana** via https://your-server-ip:3000 (or via SSH tunnel for security)

2. **Add Prometheus data source**:
   - Click "Configuration" (gear icon) → "Data Sources"
   - Click "Add data source"
   - Select "Prometheus"
   - Set URL to "http://localhost:9090"
   - Click "Save & Test"

3. **Import system monitoring dashboard**:
   - Click "+" → "Import"
   - Enter dashboard ID "1860" (Node Exporter Full)
   - Select your Prometheus data source
   - Click "Import"

4. **Import Ethereum monitoring dashboard**:
   - Click "+" → "Import"
   - Enter dashboard ID "13877" (Ethereum Metrics)
   - Select your Prometheus data source
   - Click "Import"

5. **Create a security monitoring dashboard**:
   - Click "+" → "Dashboard"
   - Add panels for:
     - Network traffic anomalies
     - Disk activity
     - Failed SSH login attempts
     - Firewall rejected packets
     - Endpoint availability

## Intrusion Detection System (IDS) Setup

Add an intrusion detection system to monitor for potential security threats.

### Installing and Configuring Wazuh

Wazuh is a powerful open-source security monitoring solution.

1. **Add Wazuh repository**:
   ```bash
   curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo apt-key add -
   echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee -a /etc/apt/sources.list.d/wazuh.list
   ```

2. **Install Wazuh agent**:
   ```bash
   sudo apt-get update
   sudo apt-get install wazuh-agent
   ```

3. **Configure Wazuh agent**:
   ```bash
   sudo nano /var/ossec/etc/ossec.conf
   ```
   
   Update manager settings:
   ```xml
   <ossec_config>
     <client>
       <server>
         <address>your-wazuh-server-ip</address>
         <port>1514</port>
         <protocol>tcp</protocol>
       </server>
       <config-profile>ubuntu, ubuntu20, ubuntu20.04</config-profile>
     </client>
   </ossec_config>
   ```

4. **Enable and start Wazuh agent**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable wazuh-agent
   sudo systemctl start wazuh-agent
   ```

### Setting Up Fail2ban

Fail2ban protects against brute force attacks by blocking suspicious IP addresses.

1. **Install Fail2ban**:
   ```bash
   sudo apt-get install fail2ban
   ```

2. **Create local configuration**:
   ```bash
   sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
   sudo nano /etc/fail2ban/jail.local
   ```
   
   Update these settings:
   ```ini
   [DEFAULT]
   # Ban IP addresses for one hour
   bantime = 3600
   
   # Increase find time to catch slow brute force attempts
   findtime = 3600
   
   # Ban after 5 failures
   maxretry = 5
   
   # Email to notify
   destemail = your-email@example.com
   sender = fail2ban@ethereum-server
   
   [sshd]
   enabled = true
   
   [ethereum-rpc]
   enabled = true
   port = 8545
   filter = ethereum-rpc
   logpath = /var/log/ethereum/rpc.log
   maxretry = 3
   bantime = 86400  # 24 hours
   ```

3. **Create custom filter for Ethereum RPC**:
   ```bash
   sudo nano /etc/fail2ban/filter.d/ethereum-rpc.conf
   ```
   
   Add the following content:
   ```ini
   [Definition]
   failregex = ^.*authentication failure from <HOST>.*$
               ^.*invalid JWT from <HOST>.*$
               ^.*unauthorized access attempt from <HOST>.*$
   ignoreregex =
   ```

4. **Start and enable Fail2ban**:
   ```bash
   sudo systemctl start fail2ban
   sudo systemctl enable fail2ban
   ```

## Centralized Logging with ELK Stack

Set up centralized logging for better security monitoring and analysis.

### Installing and Configuring Filebeat

1. **Add Elastic repository**:
   ```bash
   wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
   echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
   ```

2. **Install Filebeat**:
   ```bash
   sudo apt-get update
   sudo apt-get install filebeat
   ```

3. **Configure Filebeat**:
   ```bash
   sudo nano /etc/filebeat/filebeat.yml
   ```
   
   Update the configuration:
   ```yaml
   filebeat.inputs:
   - type: log
     enabled: true
     paths:
       - /var/log/auth.log
       - /var/log/syslog
       - /var/log/ethereum/*.log
   
   filebeat.modules:
     - module: system
       syslog:
         enabled: true
       auth:
         enabled: true
   
   output.elasticsearch:
     hosts: ["your-elasticsearch-server:9200"]
     username: "elastic"
     password: "your-password"
   
   setup.kibana:
     host: "your-kibana-server:5601"
   ```

4. **Enable and start Filebeat**:
   ```bash
   sudo systemctl enable filebeat
   sudo systemctl start filebeat
   ```

## Security Auditing Tools

Install and configure tools for regular security auditing.

### Setting Up Lynis

Lynis is an open-source security auditing tool for Unix/Linux systems.

1. **Install Lynis**:
   ```bash
   sudo apt-get install lynis
   ```

2. **Create weekly audit script**:
   ```bash
   sudo nano /usr/local/bin/weekly-audit.sh
   ```
   
   Add the following content:
   ```bash
   #!/bin/bash
   
   # Run Lynis audit and save report
   DATE=$(date +%Y-%m-%d)
   /usr/bin/lynis audit system --cronjob > /var/log/lynis-audit-$DATE.log
   
   # Send email with report
   cat /var/log/lynis-audit-$DATE.log | mail -s "Weekly Security Audit Report - $DATE" your-email@example.com
   
   # Keep only last 8 reports
   find /var/log/ -name "lynis-audit-*.log" -type f -mtime +56 -delete
   ```

3. **Make script executable**:
   ```bash
   sudo chmod +x /usr/local/bin/weekly-audit.sh
   ```

4. **Add to crontab**:
   ```bash
   echo "0 2 * * 0 root /usr/local/bin/weekly-audit.sh" | sudo tee -a /etc/cron.d/security-audit
   ```

### Installing RKHunter (Rootkit Hunter)

RKHunter scans for rootkits, backdoors, and local exploits.

1. **Install RKHunter**:
   ```bash
   sudo apt-get install rkhunter
   ```

2. **Update RKHunter database**:
   ```bash
   sudo rkhunter --update
   sudo rkhunter --propupd
   ```

3. **Create daily scan script**:
   ```bash
   sudo nano /etc/cron.daily/rkhunter-scan
   ```
   
   Add the following content:
   ```bash
   #!/bin/bash
   
   /usr/bin/rkhunter --check --skip-keypress --report-warnings-only
   ```

4. **Make script executable**:
   ```bash
   sudo chmod +x /etc/cron.daily/rkhunter-scan
   ```

## Mobile Monitoring Setup

Set up mobile notifications for critical security alerts.

### Configuring Grafana Mobile App

1. **Install Grafana mobile app** on your smartphone (available for iOS and Android)

2. **Enable Grafana alerting**:
   - In Grafana web interface, go to "Alerting" → "Notification channels"
   - Click "Add channel"
   - Name: "Mobile App"
   - Type: "Grafana mobile app"
   - Default: Yes
   - Click "Save"

3. **Link your mobile device**:
   - Open Grafana mobile app
   - Add your Grafana server (you'll need to configure secure external access)
   - Sign in with your Grafana credentials
   - Enable notifications when prompted

### Setting Up Telegram Bot for Alerts

As an alternative, you can use Telegram for mobile alerts.

1. **Create a Telegram bot**:
   - Message @BotFather on Telegram
   - Use the /newbot command
   - Follow instructions to create a bot
   - Save the API token

2. **Create a Telegram channel or group**:
   - Create a new channel or group for alerts
   - Add your bot as an administrator

3. **Install Alertmanager Telegram plugin**:
   ```bash
   wget https://github.com/metalmatze/alertmanager-bot/releases/download/0.4.3/alertmanager-bot-0.4.3-linux-amd64
   sudo mv alertmanager-bot-0.4.3-linux-amd64 /usr/local/bin/alertmanager-bot
   sudo chmod +x /usr/local/bin/alertmanager-bot
   ```

4. **Create systemd service**:
   ```bash
   sudo nano /etc/systemd/system/alertmanager-bot.service
   ```
   
   Add the following configuration:
   ```
   [Unit]
   Description=AlertManager Bot for Telegram
   After=network.target
   
   [Service]
   User=prometheus
   ExecStart=/usr/local/bin/alertmanager-bot \
     --telegram.token=YOUR_BOT_TOKEN \
     --telegram.chat=YOUR_CHAT_ID \
     --alertmanager.url=http://localhost:9093
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

5. **Update Alertmanager configuration**:
   ```bash
   sudo nano /etc/alertmanager/alertmanager.yml
   ```
   
   Add Webhook receiver:
   ```yaml
   receivers:
   - name: 'telegram-notifications'
     webhook_configs:
     - url: 'http://localhost:8080'
   ```

6. **Start and enable the bot**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable alertmanager-bot
   sudo systemctl start alertmanager-bot
   ```

## Setting Up Automated Responses

Configure automated responses to security incidents to enable immediate action when security events are detected.

### Creating Response Scripts

1. **DDoS Protection Script**:
   ```bash
   sudo nano /usr/local/bin/block-ddos.sh
   ```
   
   Add the following content:
   ```bash
   #!/bin/bash
   
   # Get the attacking IP from the alert
   ATTACKER_IP=$1
   
   # Add to blacklist
   sudo iptables -A INPUT -s $ATTACKER_IP -j DROP
   
   # Log the action
   logger -t security "Blocked potential DDoS from $ATTACKER_IP"
   
   # Send notification
   echo "Blocked potential DDoS attack from $ATTACKER_IP" | mail -s "Security Alert: DDoS Blocked" your-email@example.com
   ```

2. **Service Recovery Script**:
   ```bash
   sudo nano /usr/local/bin/recover-ethereum.sh
   ```
   
   Add the following content:
   ```bash
   #!/bin/bash
   
   # Check if Ethereum node is running
   if ! systemctl is-active --quiet geth; then
     # Attempt to restart
     systemctl restart geth
     
     # Log the restart attempt
     logger -t ethereum "Attempting to restart Geth service"
     
     # Wait for startup
     sleep 30
     
     # Check if successfully restarted
     if systemctl is-active --quiet geth; then
       logger -t ethereum "Geth service successfully restarted"
       echo "Ethereum node recovered successfully" | mail -s "Recovery: Ethereum Node" your-email@example.com
     else
       logger -t ethereum "CRITICAL: Failed to restart Geth service"
       echo "CRITICAL: Failed to restart Ethereum node" | mail -s "URGENT: Ethereum Node Recovery Failed" your-email@example.com
     fi
   fi