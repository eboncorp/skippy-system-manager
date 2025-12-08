#!/usr/bin/env python3
"""
orbi_manager_v1.0.0.py - Orbi Network Management Tool

Manage Netgear Orbi RBR40 router via SOAP API.

Usage:
    python3 orbi_manager.py status      # Full status report
    python3 orbi_manager.py devices     # List connected devices
    python3 orbi_manager.py speedtest   # Run speed test
    python3 orbi_manager.py satellites  # Check satellite status
    python3 orbi_manager.py reboot      # Reboot router (use with caution)

Dependencies:
    pip install pynetgear

Created: 2025-12-02
"""

import sys
import os

# Add venv to path if exists
VENV_PATH = "/tmp/netgear_env/lib/python3.12/site-packages"
if os.path.exists(VENV_PATH):
    sys.path.insert(0, VENV_PATH)

from pynetgear import Netgear
import time

# Configuration - update if credentials change
ORBI_HOST = "10.0.0.1"
ORBI_USER = "admin"
ORBI_PASS = os.environ.get("ORBI_PASSWORD", "")  # Set via environment for security
ORBI_PORT = 80
ORBI_SSL = False


def get_netgear():
    """Get authenticated Netgear connection."""
    if not ORBI_PASS:
        print("Error: Set ORBI_PASSWORD environment variable")
        sys.exit(1)

    netgear = Netgear(
        host=ORBI_HOST,
        user=ORBI_USER,
        password=ORBI_PASS,
        port=ORBI_PORT,
        ssl=ORBI_SSL
    )

    if not netgear.login():
        print("Error: Failed to login to Orbi")
        sys.exit(1)

    return netgear


def cmd_status():
    """Show full router status."""
    netgear = get_netgear()

    print("=" * 50)
    print("ORBI STATUS REPORT")
    print("=" * 50)

    # Router Info
    info = netgear.get_info()
    print(f"\nRouter: {info.get('ModelName', 'Unknown')}")
    print(f"Firmware: {info.get('Firmwareversion', 'Unknown')}")

    # System Info
    sysinfo = netgear.get_system_info()
    if sysinfo:
        print(f"CPU: {sysinfo.get('NewCPUUtilization', '?')}%")
        print(f"Memory: {sysinfo.get('NewMemoryUtilization', '?')}%")

    # WAN Info
    wan = netgear.get_wan_ip_con_info()
    if wan:
        print(f"\nWAN IP: {wan.get('NewExternalIPAddress', '?')}")
        print(f"DNS: {wan.get('NewDNSServers', '?')}")

    # Devices
    devices = netgear.get_attached_devices()
    print(f"\nConnected Devices: {len(devices) if devices else 0}")

    # Satellites
    satellites = netgear.get_satellites()
    if satellites:
        print(f"Satellites: {len(satellites)}")
        for sat in satellites:
            print(f"  - {sat.get('DeviceName', 'Unknown')} ({sat.get('IP', '?')})")


def cmd_devices():
    """List connected devices."""
    netgear = get_netgear()

    print(f"{'Device':<30} {'IP':<15} {'Type':<10}")
    print("-" * 55)

    devices = netgear.get_attached_devices()
    if devices:
        for d in devices:
            print(f"{d.name:<30} {d.ip:<15} {d.type:<10}")
    else:
        print("No devices found")


def cmd_speedtest():
    """Run speed test."""
    netgear = get_netgear()

    print("Starting speed test (15 seconds)...")
    netgear.set_speed_test_start()
    time.sleep(15)

    result = netgear.get_new_speed_test_result()
    if not result:
        result = netgear.get_speed_test_result()

    if result:
        print(f"\nResults:")
        print(f"  Download: {result.get('NewOOKLADownlinkBandwidth', '?')} Mbps")
        print(f"  Upload: {result.get('NewOOKLAUplinkBandwidth', '?')} Mbps")
        print(f"  Ping: {result.get('AveragePing', '?')} ms")
    else:
        print("Speed test failed")


def cmd_satellites():
    """Show satellite status."""
    netgear = get_netgear()

    satellites = netgear.get_satellites()
    if satellites:
        for sat in satellites:
            print(f"\n{sat.get('DeviceName', 'Unknown Satellite')}")
            print(f"  Model: {sat.get('ModelName', '?')}")
            print(f"  IP: {sat.get('IP', '?')}")
            print(f"  Firmware: {sat.get('FWVersion', '?')}")
            print(f"  Backhaul: {sat.get('BHConnType', '?')}")
    else:
        print("No satellites found")


def cmd_reboot():
    """Reboot the router."""
    confirm = input("Are you sure you want to reboot? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled")
        return

    netgear = get_netgear()
    print("Rebooting router...")
    netgear.reboot()
    print("Reboot initiated. Wait 2-3 minutes for router to come back online.")


def main():
    if len(sys.argv) < 2:
        print("Usage: orbi_manager.py <command>")
        print("Commands: status, devices, speedtest, satellites, reboot")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    commands = {
        'status': cmd_status,
        'devices': cmd_devices,
        'speedtest': cmd_speedtest,
        'satellites': cmd_satellites,
        'reboot': cmd_reboot,
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: status, devices, speedtest, satellites, reboot")
        sys.exit(1)


if __name__ == "__main__":
    main()
