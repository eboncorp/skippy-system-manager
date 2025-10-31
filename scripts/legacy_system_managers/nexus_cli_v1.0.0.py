#!/usr/bin/env python3
"""
NexusController CLI - Command Line Interface
Simple menu-driven access to Ebon server
"""

import sys
import subprocess
import webbrowser
import socket
import time

def check_ebon_status():
    """Check if Ebon server is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('10.0.0.29', 22))
        sock.close()
        return result == 0
    except:
        return False

def connect_ssh():
    """Connect to Ebon via SSH"""
    print("🔗 Connecting to Ebon server...")
    try:
        subprocess.run(['ssh', 'ebon@10.0.0.29'])
    except KeyboardInterrupt:
        print("\n📡 SSH session ended")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        print("💡 Try manually: ssh ebon@10.0.0.29")

def open_web():
    """Open Ebon web interface"""
    print("🌐 Opening web interface...")
    try:
        webbrowser.open("http://10.0.0.29")
        print("✅ Web browser launched")
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print("💡 Manual URL: http://10.0.0.29")

def show_status():
    """Show Ebon server status"""
    print("📊 Checking Ebon server status...")
    
    # SSH check
    print("  🔍 Testing SSH connection...")
    if check_ebon_status():
        print("  ✅ SSH: ONLINE")
    else:
        print("  ❌ SSH: OFFLINE")
    
    # HTTP check
    print("  🔍 Testing HTTP service...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('10.0.0.29', 80))
        sock.close()
        if result == 0:
            print("  ✅ HTTP: ONLINE")
        else:
            print("  ❌ HTTP: OFFLINE")
    except:
        print("  ❓ HTTP: UNKNOWN")

def show_banner():
    """Show application banner"""
    print("\n" + "="*60)
    print("🌐 NexusController CLI")
    print("Central Command Hub for Ebon Server Access")
    print("="*60)

def show_menu():
    """Show main menu"""
    print("\n📋 Available Commands:")
    print("  1. 🔗 SSH Connect to Ebon")
    print("  2. 🌐 Open Web Interface")
    print("  3. 📊 Check Server Status")
    print("  4. ❓ Show This Menu")
    print("  5. 🚪 Exit")
    print("-" * 40)

def main():
    """Main application loop"""
    show_banner()
    
    # Initial status check
    if check_ebon_status():
        print("🟢 Ebon server is ONLINE")
    else:
        print("🔴 Ebon server appears OFFLINE")
    
    show_menu()
    
    while True:
        try:
            choice = input("\n🎯 Enter command (1-5): ").strip()
            
            if choice == '1':
                connect_ssh()
            elif choice == '2':
                open_web()
            elif choice == '3':
                show_status()
            elif choice == '4':
                show_menu()
            elif choice == '5':
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Enter 1-5 or use command 4 for menu.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
        except EOFError:
            print("\n\n👋 Goodbye!")
            sys.exit(0)

if __name__ == '__main__':
    main()