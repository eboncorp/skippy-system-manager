#!/usr/bin/env python3
"""
NexusController Test - Minimal version to identify issues
"""

import sys
import os

print("Testing imports...")

try:
    import tkinter as tk
    print("✓ tkinter imported successfully")
except Exception as e:
    print(f"✗ tkinter failed: {e}")
    sys.exit(1)

try:
    import psutil
    print("✓ psutil imported successfully")
except Exception as e:
    print(f"✗ psutil failed: {e}")

try:
    import paramiko
    print("✓ paramiko imported successfully")
except Exception as e:
    print(f"✗ paramiko failed: {e}")

print("\nTesting basic GUI...")

try:
    root = tk.Tk()
    root.title("NexusController Test")
    root.geometry("400x300")
    
    label = tk.Label(root, text="NexusController GUI Test", font=("Arial", 16))
    label.pack(pady=50)
    
    def test_function():
        print("Button clicked!")
        
    button = tk.Button(root, text="Test Button", command=test_function)
    button.pack(pady=20)
    
    # Don't start mainloop, just test creation
    root.update()
    print("✓ GUI creation successful")
    
    # Test basic system info
    try:
        import socket
        hostname = socket.gethostname()
        print(f"✓ Hostname: {hostname}")
    except Exception as e:
        print(f"✗ System info failed: {e}")
    
    root.destroy()
    print("✓ All tests passed!")
    
except Exception as e:
    print(f"✗ GUI test failed: {e}")
    import traceback
    traceback.print_exc()