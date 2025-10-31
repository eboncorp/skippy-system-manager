#!/usr/bin/env python3
"""
Simple NexusController - Absolutely minimal working version
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import webbrowser

def connect_ebon():
    """Connect to Ebon server"""
    try:
        subprocess.Popen(['gnome-terminal', '--', 'ssh', 'ebon@10.0.0.29'])
    except:
        print("ssh ebon@10.0.0.29")

def open_web():
    """Open web interface"""
    try:
        webbrowser.open("http://10.0.0.29")
    except:
        print("http://10.0.0.29")

def main():
    root = tk.Tk()
    root.title("NexusController - Simple")
    root.geometry("800x600")
    
    # Header
    header = tk.Label(root, text="🌐 NexusController", 
                     font=("Arial", 18), bg='lightblue')
    header.pack(fill='x', pady=10)
    
    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    
    tk.Button(button_frame, text="SSH to Ebon", 
             command=connect_ebon, font=("Arial", 12),
             padx=20, pady=10).pack(side='left', padx=10)
             
    tk.Button(button_frame, text="Web Interface", 
             command=open_web, font=("Arial", 12),
             padx=20, pady=10).pack(side='left', padx=10)
    
    # Info
    info = tk.Label(root, text="Simple server access for Ebon (10.0.0.29)", 
                   font=("Arial", 10))
    info.pack(pady=20)
    
    root.mainloop()

if __name__ == '__main__':
    main()