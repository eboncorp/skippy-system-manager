#!/usr/bin/env python3
"""
Active Network Scanner v2.0
Enhanced with async operations, type hints, and better error handling
Discovers all devices on the local network with improved performance
"""

import asyncio
import subprocess
import socket
import sys
import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path
import ipaddress

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NetworkDevice:
    """Represents a discovered network device"""
    ip_address: str
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    services: List[str] = None
    response_time: Optional[float] = None
    last_seen: datetime = None
    device_type: Optional[str] = None

    def __post_init__(self):
        if self.services is None:
            self.services = []
        if self.last_seen is None:
            self.last_seen = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['last_seen'] = self.last_seen.isoformat()
        return data

class NetworkScanner:
    """Advanced network scanner with async operations"""

    # Common MAC vendor prefixes
    MAC_VENDORS = {
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
        "00:1B:21": "Intel",
        "00:21:6A": "Intel",
        "A4:C3:F0": "Intel",
        "00:15:5D": "Microsoft Hyper-V",
        "00:25:90": "Dell",
        "F4:39:09": "HP",
        "3C:52:82": "HP",
        "00:0C:6E": "ASUS",
        "00:1F:C6": "ASUS",
    }

    # Common service ports to scan
    COMMON_PORTS = {
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        8080: "HTTP-Alt",
        8096: "Jellyfin",
        9090: "Cockpit",
        10000: "Webmin"
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the network scanner

        Args:
            cache_dir: Directory to cache scan results
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "network_scanner"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "devices.json"
        self.devices: Dict[str, NetworkDevice] = {}
        self.load_cache()

    def load_cache(self) -> None:
        """Load cached device information"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    for ip, device_data in data.items():
                        device_data['last_seen'] = datetime.fromisoformat(device_data['last_seen'])
                        self.devices[ip] = NetworkDevice(**device_data)
                logger.info(f"Loaded {len(self.devices)} devices from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

    def save_cache(self) -> None:
        """Save device information to cache"""
        try:
            cache_data = {ip: device.to_dict() for ip, device in self.devices.items()}
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Saved {len(self.devices)} devices to cache")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    async def get_network_info(self) -> Optional[Tuple[str, str, str, str]]:
        """Get network configuration asynchronously

        Returns:
            Tuple of (our_ip, gateway, subnet, interface) or None
        """
        try:
            # Get default gateway and interface
            proc = await asyncio.create_subprocess_exec(
                'ip', 'route',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            for line in stdout.decode().split('\n'):
                if 'default' in line:
                    parts = line.split()
                    gateway = parts[2]
                    interface = parts[4] if len(parts) > 4 else 'unknown'

                    # Get our IP on that interface
                    proc2 = await asyncio.create_subprocess_exec(
                        'ip', '-4', 'addr', 'show', interface,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout2, _ = await proc2.communicate()

                    for line2 in stdout2.decode().split('\n'):
                        if 'inet' in line2 and 'brd' in line2:
                            our_ip = line2.split()[1].split('/')[0]
                            subnet_cidr = line2.split()[1]
                            network = ipaddress.ip_network(subnet_cidr, strict=False)
                            subnet = str(network.network_address)
                            return our_ip, gateway, subnet, interface
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
        return None

    async def ping_host(self, ip: str) -> Tuple[str, bool, Optional[float]]:
        """Ping a single host asynchronously

        Args:
            ip: IP address to ping

        Returns:
            Tuple of (ip, is_alive, response_time)
        """
        try:
            start_time = asyncio.get_event_loop().time()
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '1', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            response_time = asyncio.get_event_loop().time() - start_time

            is_alive = proc.returncode == 0
            return ip, is_alive, response_time if is_alive else None
        except Exception as e:
            logger.debug(f"Ping failed for {ip}: {e}")
            return ip, False, None

    async def get_hostname(self, ip: str) -> Optional[str]:
        """Get hostname for IP address asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, socket.gethostbyaddr, ip)
        except:
            return None

    async def get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address from ARP table"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'ip', 'neigh', 'show', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if stdout:
                parts = stdout.decode().split()
                if len(parts) > 4 and parts[3] == 'lladdr':
                    return parts[4].upper()
        except Exception as e:
            logger.debug(f"Failed to get MAC for {ip}: {e}")
        return None

    async def scan_port(self, ip: str, port: int, timeout: float = 0.5) -> bool:
        """Check if a port is open on the given IP

        Args:
            ip: IP address to scan
            port: Port number to check
            timeout: Connection timeout in seconds

        Returns:
            True if port is open, False otherwise
        """
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

    async def identify_device(self, device: NetworkDevice) -> None:
        """Identify device type and services

        Args:
            device: NetworkDevice to identify
        """
        # Identify vendor by MAC prefix
        if device.mac_address:
            mac_prefix = device.mac_address[:8]
            device.vendor = self.MAC_VENDORS.get(mac_prefix, "Unknown")

        # Scan for common services
        tasks = []
        for port, service_name in self.COMMON_PORTS.items():
            tasks.append(self.scan_port(device.ip_address, port))

        results = await asyncio.gather(*tasks)

        device.services = [
            service for port, service in self.COMMON_PORTS.items()
            if results[list(self.COMMON_PORTS.keys()).index(port)]
        ]

        # Determine device type based on services and hostname
        device.device_type = self._classify_device(device)

    def _classify_device(self, device: NetworkDevice) -> str:
        """Classify device based on available information

        Args:
            device: Device to classify

        Returns:
            Device type string
        """
        # Check for specific services
        if "Jellyfin" in device.services:
            return "Media Server"
        if "RDP" in device.services:
            return "Windows PC"
        if "SSH" in device.services and "HTTP" in device.services:
            return "Linux Server"
        if "SSH" in device.services:
            return "Linux/Unix Device"
        if device.vendor == "Raspberry Pi":
            return "Raspberry Pi"
        if "HTTP" in device.services or "HTTPS" in device.services:
            return "Web Device"
        if device.vendor and "Router" in device.vendor:
            return "Router/Gateway"

        return "Unknown Device"

    async def scan_network(self, subnet: str = None, max_workers: int = 50) -> List[NetworkDevice]:
        """Scan the network for active devices

        Args:
            subnet: Subnet to scan (e.g., "192.168.1.0/24")
            max_workers: Maximum concurrent ping operations

        Returns:
            List of discovered NetworkDevice objects
        """
        # Get network info if not provided
        if not subnet:
            network_info = await self.get_network_info()
            if not network_info:
                logger.error("Could not determine network configuration")
                return []

            our_ip, gateway, subnet_base, interface = network_info
            # Create /24 subnet from base
            subnet = f"{'.'.join(subnet_base.split('.')[:-1])}.0/24"

            logger.info(f"Scanning network: {subnet}")
            logger.info(f"Your IP: {our_ip}, Gateway: {gateway}, Interface: {interface}")

        # Parse subnet
        try:
            network = ipaddress.ip_network(subnet)
        except ValueError as e:
            logger.error(f"Invalid subnet: {e}")
            return []

        # Ping all hosts in subnet
        ping_tasks = [self.ping_host(str(ip)) for ip in network.hosts()]

        print(f"\n🔍 Scanning {len(ping_tasks)} IP addresses...")
        ping_results = await asyncio.gather(*ping_tasks)

        # Filter active hosts
        active_hosts = [
            (ip, response_time)
            for ip, is_alive, response_time in ping_results
            if is_alive
        ]

        print(f"✅ Found {len(active_hosts)} active hosts\n")

        # Gather detailed information for active hosts
        devices = []
        print("📊 Gathering device information...")

        for ip, response_time in active_hosts:
            # Check if we have cached info
            if ip in self.devices:
                device = self.devices[ip]
                device.last_seen = datetime.now()
                device.response_time = response_time
            else:
                device = NetworkDevice(
                    ip_address=ip,
                    response_time=response_time
                )

            # Get MAC address
            device.mac_address = await self.get_mac_address(ip)

            # Get hostname
            hostname_result = await self.get_hostname(ip)
            if hostname_result:
                device.hostname = hostname_result[0]

            # Identify device type and services
            await self.identify_device(device)

            devices.append(device)
            self.devices[ip] = device

            # Show progress
            print(f"  Scanned {ip}: {device.device_type}")

        # Save cache
        self.save_cache()

        return sorted(devices, key=lambda x: ipaddress.ip_address(x.ip_address))

    def print_results(self, devices: List[NetworkDevice], our_ip: str = None, gateway: str = None) -> None:
        """Print scan results in a formatted table

        Args:
            devices: List of discovered devices
            our_ip: Our IP address (for highlighting)
            gateway: Gateway IP address (for highlighting)
        """
        print("\n" + "="*100)
        print(f"{'IP Address':<15} {'MAC Address':<18} {'Hostname':<25} {'Type':<20} {'Services'}")
        print("="*100)

        for device in devices:
            services_str = ', '.join(device.services[:3])  # Show first 3 services
            if len(device.services) > 3:
                services_str += f" (+{len(device.services)-3})"

            # Determine icon and highlighting
            icon = "  "
            if device.ip_address == our_ip:
                icon = "🖥️"
                type_str = "This Device"
            elif device.ip_address == gateway:
                icon = "🌐"
                type_str = "Gateway/Router"
            else:
                type_str = device.device_type or device.vendor or "Unknown"
                if device.device_type == "Media Server":
                    icon = "🎬"
                elif device.device_type == "Raspberry Pi":
                    icon = "🥧"
                elif "Server" in device.device_type:
                    icon = "🖲️"
                elif "Windows" in device.device_type:
                    icon = "💻"

            hostname = (device.hostname or '')[:25]

            print(f"{icon} {device.ip_address:<15} {device.mac_address or 'Unknown':<18} "
                  f"{hostname:<25} {type_str:<20} {services_str}")

        print("="*100)
        print(f"\n📈 Summary: {len(devices)} devices found on network")

        # Service summary
        all_services = {}
        for device in devices:
            for service in device.services:
                all_services[service] = all_services.get(service, 0) + 1

        if all_services:
            print("\n🔌 Services discovered:")
            for service, count in sorted(all_services.items()):
                print(f"   • {service}: {count} device(s)")

async def main():
    """Main entry point"""
    try:
        scanner = NetworkScanner()

        # Get network info first
        network_info = await scanner.get_network_info()
        if not network_info:
            print("❌ Could not determine network configuration")
            return

        our_ip, gateway, subnet_base, interface = network_info

        print("🔍 Active Network Scanner v2.0")
        print("="*50)
        print(f"📍 Your IP: {our_ip}")
        print(f"🌐 Gateway: {gateway}")
        print(f"🔌 Interface: {interface}")
        print("="*50)

        # Scan network
        devices = await scanner.scan_network()

        # Print results
        scanner.print_results(devices, our_ip, gateway)

        # Export option
        print("\n💾 Scan results cached to ~/.cache/network_scanner/devices.json")

    except KeyboardInterrupt:
        print("\n\n❌ Scan cancelled by user")
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())