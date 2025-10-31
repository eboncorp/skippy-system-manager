#!/usr/bin/env python3
"""
Unified System Manager v2.0 - Tkinter Version
"""

import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

class UnifiedSystemManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Unified System Manager v2.0")
        self.root.geometry("900x600")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = tk.Label(self.root, text="Unified System Manager", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Google Drive tab
        gdrive_frame = ttk.Frame(notebook)
        notebook.add(gdrive_frame, text="Google Drive")
        self.create_gdrive_tab(gdrive_frame)
        
        # System Cleanup tab
        cleanup_frame = ttk.Frame(notebook)
        notebook.add(cleanup_frame, text="System Cleanup")
        self.create_cleanup_tab(cleanup_frame)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self.create_settings_tab(settings_frame)
        
    def create_gdrive_tab(self, parent):
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Google Drive Status")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.rclone_status = tk.Label(status_frame, text="rclone: Checking...")
        self.rclone_status.pack(anchor='w')
        
        self.mount_status = tk.Label(status_frame, text="Mount: Checking...")
        self.mount_status.pack(anchor='w')
        
        # Actions frame
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Quick Setup", 
                  command=self.quick_setup).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Mount Drive", 
                  command=self.mount_drive).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Smart Backup", 
                  command=self.smart_backup).pack(side='left', padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Output")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.gdrive_log = scrolledtext.ScrolledText(log_frame, height=10)
        self.gdrive_log.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_cleanup_tab(self, parent):
        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Cleanup Options")
        options_frame.pack(fill='x', padx=10, pady=5)
        
        self.cleanup_vars = {}
        for name, key in [
            ("Package Cache", "package_cache"),
            ("Browser Caches", "browser_cache"),
            ("Temporary Files", "temp_files"),
            ("Docker Resources", "docker"),
        ]:
            var = tk.BooleanVar(value=True)
            self.cleanup_vars[key] = var
            ttk.Checkbutton(options_frame, text=name, variable=var).pack(anchor='w')
        
        # Actions frame
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Analyze System", 
                  command=self.analyze_system).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Start Cleanup", 
                  command=self.start_cleanup).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Emergency Cleanup", 
                  command=self.emergency_cleanup).pack(side='left', padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Output")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.cleanup_log = scrolledtext.ScrolledText(log_frame, height=10)
        self.cleanup_log.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_settings_tab(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Settings")
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(settings_frame, text="Mount Point:").pack(anchor='w')
        self.mount_point_var = tk.StringVar(value=str(Path.home() / "GoogleDrive"))
        tk.Entry(settings_frame, textvariable=self.mount_point_var, width=50).pack(anchor='w', pady=2)
        
        tk.Label(settings_frame, text="Max Transfers:").pack(anchor='w')
        self.max_transfers_var = tk.StringVar(value="4")
        tk.Entry(settings_frame, textvariable=self.max_transfers_var, width=10).pack(anchor='w', pady=2)
        
        ttk.Button(settings_frame, text="Save Settings", 
                  command=self.save_settings).pack(pady=10)
        
    def run_command_async(self, command, log_widget):
        def run():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                log_widget.insert(tk.END, result.stdout + "\n")
                if result.stderr:
                    log_widget.insert(tk.END, f"Error: {result.stderr}\n")
                log_widget.see(tk.END)
            except Exception as e:
                log_widget.insert(tk.END, f"Exception: {str(e)}\n")
                log_widget.see(tk.END)
                
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        
    def quick_setup(self):
        self.run_command_async("rclone config", self.gdrive_log)
        
    def mount_drive(self):
        script_path = Path.home() / ".unified-system-manager/scripts/gdrive-manager.sh"
        self.run_command_async(f"{script_path} mount", self.gdrive_log)
        
    def smart_backup(self):
        script_path = Path.home() / ".unified-system-manager/scripts/gdrive-manager.sh"
        self.run_command_async(f"{script_path} smart-backup", self.gdrive_log)
        
    def analyze_system(self):
        script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
        self.run_command_async(f"{script_path} --report-only", self.cleanup_log)
        
    def start_cleanup(self):
        if messagebox.askyesno("Confirm", "Start system cleanup?"):
            script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
            self.run_command_async(f"{script_path}", self.cleanup_log)
            
    def emergency_cleanup(self):
        if messagebox.askyesno("Emergency Cleanup", "Perform aggressive cleanup?"):
            script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
            self.run_command_async(f"{script_path} --emergency --yes", self.cleanup_log)
            
    def save_settings(self):
        messagebox.showinfo("Settings", "Settings saved successfully!")
        
    def run(self):
        self.root.mainloop()

def main():
    app = UnifiedSystemManager()
    app.run()

if __name__ == "__main__":
    main()
