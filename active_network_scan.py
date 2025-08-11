#!/usr/bin/env python3
"""
Active Network Scanner
Discovers all devices on the local network
"""

import subprocess
import socket
import threading
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_network_info():
    """Get network configuration"""
    try:
        # Get default gateway and interface
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'default' in line:
                parts = line.split()
                gateway = parts[2]
                interface = parts[4] if len(parts) > 4 else 'unknown'
                
                # Get our IP on that interface
                result2 = subprocess.run(['ip', '-4', 'addr', 'show', interface], 
                                       capture_output=True, text=True)
                for line2 in result2.stdout.split('\n'):
                    if 'inet' in line2 and 'brd' in line2:
                        our_ip = line2.split()[1].split('/')[0]
                        subnet = '.'.join(our_ip.split('.')[:-1])
                        return our_ip, gateway, subnet, interface
    except:
        pass
    return None, None, None, None

def ping_host(ip):
    """Ping a single host"""
    try:
        # Use system ping command
        result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_hostname(ip):
    """Try to get hostname for IP"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ""

def get_mac_address(ip):
    """Get MAC address from ARP table"""
    try:
        result = subprocess.run(['ip', 'neigh', 'show', ip], 
                              capture_output=True, text=True)
        if result.stdout:
            parts = result.stdout.split()
            if len(parts) > 4 and parts[3] == 'lladdr':
                return parts[4]
    except:
        pass
    return ""

def identify_device(mac, hostname, ip):
    """Try to identify device type"""
    mac_prefix = mac[:8].upper() if mac else ""
    
    # Common MAC prefixes
    vendors = {
        "BC:A5:11": "Gigaset/Router",
        "00:50:56": "VMware",
        "00:0C:29": "VMware",
        "08:00:27": "VirtualBox",
        "52:54:00": "QEMU/KVM",
        "2C:CC:44": "Sony",
        "00:80:92": "Silex Technology",
        "10:E7:C6": "Apple",
        "B8:27:EB": "Raspberry Pi",
        "DC:A6:32": "Raspberry Pi",
        "E4:5F:01": "Raspberry Pi",
    }
    
    vendor = vendors.get(mac_prefix, "Unknown")
    
    # Check for common services
    services = []
    for port in [22, 80, 443, 445, 3389, 8080]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        if sock.connect_ex((ip, port)) == 0:
            service_names = {
                22: "SSH", 80: "HTTP", 443: "HTTPS", 
                445: "SMB", 3389: "RDP", 8080: "HTTP-Alt"
            }
            services.append(service_names.get(port, str(port)))
        sock.close()
    
    return vendor, services

def scan_network():
    """Main network scanning function"""
    print("🔍 Active Network Scanner")
    print("=" * 50)
    
    our_ip, gateway, subnet, interface = get_network_info()
    
    if not subnet:
        print("❌ Could not determine network configuration")
        return
    
    print(f"📍 Your IP: {our_ip}")
    print(f"🌐 Gateway: {gateway}")
    print(f"🔌 Interface: {interface}")
    print(f"🏠 Subnet: {subnet}.0/24")
    print("=" * 50)
    
    print("\n🔄 Scanning network... (this may take a minute)")
    
    # First, do a quick ping sweep
    active_hosts = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        # Submit all ping tasks
        future_to_ip = {
            executor.submit(ping_host, f"{subnet}.{i}"): f"{subnet}.{i}" 
            for i in range(1, 255)
        }
        
        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_ip), 1):
            ip = future_to_ip[future]
            sys.stdout.write(f"\r  Progress: {i}/254 hosts checked")
            sys.stdout.flush()
            
            if future.result():
                active_hosts.append(ip)
    
    print(f"\r  ✅ Found {len(active_hosts)} active hosts        ")
    print("\n🔍 Gathering device information...")
    
    # Gather detailed info for active hosts
    devices = []
    
    for ip in sorted(active_hosts, key=lambda x: int(x.split('.')[-1])):
        mac = get_mac_address(ip)
        hostname = get_hostname(ip)
        vendor, services = identify_device(mac, hostname, ip)
        
        devices.append({
            'ip': ip,
            'mac': mac or 'Unknown',
            'hostname': hostname or '',
            'vendor': vendor,
            'services': services
        })
    
    # Display results
    print("\n📊 Network Devices:")
    print("-" * 80)
    print(f"{'IP Address':<15} {'MAC Address':<18} {'Hostname':<20} {'Type/Services'}")
    print("-" * 80)
    
    for device in devices:
        services_str = ', '.join(device['services']) if device['services'] else ''
        type_info = f"{device['vendor']}"
        if services_str:
            type_info += f" [{services_str}]"
        
        # Highlight special devices
        if device['ip'] == our_ip:
            print(f"🖥️  {device['ip']:<15} {device['mac']:<18} {device['hostname']:<20} This device")
        elif device['ip'] == gateway:
            print(f"🌐 {device['ip']:<15} {device['mac']:<18} {device['hostname']:<20} Gateway/Router")
        else:
            print(f"   {device['ip']:<15} {device['mac']:<18} {device['hostname']:<20} {type_info}")
    
    print("-" * 80)
    print(f"\n📈 Summary: {len(devices)} devices found on network")
    
    # Show port summary
    all_services = {}
    for device in devices:
        for service in device['services']:
            all_services[service] = all_services.get(service, 0) + 1
    
    if all_services:
        print("\n🔌 Services found:")
        for service, count in sorted(all_services.items()):
            print(f"   • {service}: {count} device(s)")

if __name__ == "__main__":
    try:
        scan_network()
    except KeyboardInterrupt:
        print("\n\n❌ Scan cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")