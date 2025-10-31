#!/usr/bin/env python3
"""
Advanced Duplicate File Finder and Organizer
Finds and organizes duplicate files, with special handling for eth node scripts
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import re

class DuplicateFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate File Cleaner & Organizer")
        self.root.geometry("1000x700")
        
        # Data structures
        self.duplicates = defaultdict(list)
        self.eth_scripts = []
        self.scan_results = {}
        
        # Backup directory
        self.backup_dir = Path.home() / "CleanupBackups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Duplicate Scanner
        scan_frame = ttk.Frame(notebook)
        notebook.add(scan_frame, text="Duplicate Scanner")
        
        # Scan controls
        controls_frame = ttk.LabelFrame(scan_frame, text="Scan Options", padding="10")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Directory selection
        ttk.Label(controls_frame, text="Scan Directory:").grid(row=0, column=0, sticky=tk.W)
        self.scan_dir_var = tk.StringVar(value=str(Path.home()))
        ttk.Entry(controls_frame, textvariable=self.scan_dir_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(controls_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=5)
        
        # File type filters
        ttk.Label(controls_frame, text="Include Extensions:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.extensions_var = tk.StringVar(value=".sh,.py,.txt,.md,.svg,.png,.jpg,.jpeg,.pdf")
        ttk.Entry(controls_frame, textvariable=self.extensions_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        
        # Size filter
        ttk.Label(controls_frame, text="Min Size (KB):").grid(row=2, column=0, sticky=tk.W)
        self.min_size_var = tk.StringVar(value="1")
        ttk.Entry(controls_frame, textvariable=self.min_size_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Exclude directories
        self.exclude_cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="Exclude cache/temp directories", 
                       variable=self.exclude_cache_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Scan button
        ttk.Button(controls_frame, text="Start Scan", command=self.start_scan, 
                  style="Accent.TButton").grid(row=4, column=0, pady=10)
        
        # Results area
        results_frame = ttk.LabelFrame(scan_frame, text="Scan Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results tree
        columns = ('Hash', 'Size', 'Count', 'First File')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.results_tree.heading('#0', text='File Group')
        self.results_tree.heading('Hash', text='Hash')
        self.results_tree.heading('Size', text='Size')
        self.results_tree.heading('Count', text='Count')
        self.results_tree.heading('First File', text='First File')
        
        self.results_tree.column('#0', width=200)
        self.results_tree.column('Hash', width=100)
        self.results_tree.column('Size', width=80)
        self.results_tree.column('Count', width=60)
        self.results_tree.column('First File', width=300)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Tab 2: ETH Scripts Organizer
        eth_frame = ttk.Frame(notebook)
        notebook.add(eth_frame, text="ETH Scripts")
        
        # ETH script controls
        eth_controls_frame = ttk.LabelFrame(eth_frame, text="ETH Script Organization", padding="10")
        eth_controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(eth_controls_frame, text="Find All ETH Scripts", 
                  command=self.find_eth_scripts).grid(row=0, column=0, padx=5)
        ttk.Button(eth_controls_frame, text="Organize ETH Scripts", 
                  command=self.organize_eth_scripts).grid(row=0, column=1, padx=5)
        ttk.Button(eth_controls_frame, text="Create Master ETH Script", 
                  command=self.create_master_eth_script).grid(row=0, column=2, padx=5)
        
        # ETH results
        eth_results_frame = ttk.LabelFrame(eth_frame, text="ETH Scripts Found", padding="10")
        eth_results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ETH scripts listbox
        self.eth_listbox = tk.Listbox(eth_results_frame, selectmode=tk.MULTIPLE)
        eth_scrollbar = ttk.Scrollbar(eth_results_frame, orient=tk.VERTICAL, command=self.eth_listbox.yview)
        self.eth_listbox.configure(yscrollcommand=eth_scrollbar.set)
        
        self.eth_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        eth_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 3: Actions
        actions_frame = ttk.Frame(notebook)
        notebook.add(actions_frame, text="Cleanup Actions")
        
        # Action buttons
        action_buttons_frame = ttk.LabelFrame(actions_frame, text="Cleanup Actions", padding="10")
        action_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(action_buttons_frame, text="Preview Duplicates", 
                  command=self.preview_duplicates).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(action_buttons_frame, text="Remove Duplicates (Keep Newest)", 
                  command=lambda: self.remove_duplicates('newest')).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(action_buttons_frame, text="Remove Duplicates (Keep in Primary Location)", 
                  command=lambda: self.remove_duplicates('primary')).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(action_buttons_frame, text="Create Backup Before Cleanup", 
                  command=self.create_backup).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(action_buttons_frame, text="Restore from Backup", 
                  command=self.restore_backup).grid(row=1, column=1, padx=5, pady=5)
        
        # Summary area
        summary_frame = ttk.LabelFrame(actions_frame, text="Summary", padding="10")
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.summary_text = tk.Text(summary_frame, height=15, wrap=tk.WORD)
        summary_scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set)
        
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to scan for duplicates")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def browse_directory(self):
        """Browse for directory to scan"""
        directory = filedialog.askdirectory(initialdir=self.scan_dir_var.get())
        if directory:
            self.scan_dir_var.set(directory)
    
    def get_file_hash(self, file_path, block_size=65536):
        """Calculate SHA256 hash of file"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    hasher.update(data)
            return hasher.hexdigest()
        except (IOError, OSError):
            return None
    
    def should_exclude_path(self, path):
        """Check if path should be excluded from scan"""
        if not self.exclude_cache_var.get():
            return False
            
        exclude_patterns = [
            '/.cache/', '/.local/share/Trash/', '/.git/', '/.vscode/', 
            '/node_modules/', '/__pycache__/', '/.steam/', '/snap/',
            '/.config/google-chrome/', '/.config/BraveSoftware/',
            '/vfs/', '/vfsMeta/'
        ]
        
        str_path = str(path)
        return any(pattern in str_path for pattern in exclude_patterns)
    
    def start_scan(self):
        """Start scanning for duplicates"""
        self.status_var.set("Scanning for duplicates...")
        self.root.update()
        
        scan_dir = Path(self.scan_dir_var.get())
        if not scan_dir.exists():
            messagebox.showerror("Error", "Scan directory does not exist!")
            return
        
        # Parse extensions
        extensions = [ext.strip() for ext in self.extensions_var.get().split(',')]
        min_size = int(self.min_size_var.get()) * 1024  # Convert KB to bytes
        
        # Clear previous results
        self.duplicates.clear()
        self.results_tree.delete(*self.results_tree.get_children())
        
        file_hashes = {}
        processed_files = 0
        
        # Scan files
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file():
                # Check if should exclude
                if self.should_exclude_path(file_path):
                    continue
                    
                # Check extension
                if extensions and file_path.suffix not in extensions:
                    continue
                
                # Check size
                try:
                    if file_path.stat().st_size < min_size:
                        continue
                except OSError:
                    continue
                
                # Calculate hash
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        file_hashes[file_hash].append(file_path)
                    else:
                        file_hashes[file_hash] = [file_path]
                
                processed_files += 1
                if processed_files % 100 == 0:
                    self.status_var.set(f"Processed {processed_files} files...")
                    self.root.update()
        
        # Find duplicates (groups with more than one file)
        duplicate_count = 0
        total_duplicate_size = 0
        
        for file_hash, files in file_hashes.items():
            if len(files) > 1:
                self.duplicates[file_hash] = files
                duplicate_count += len(files) - 1  # Don't count the original
                
                # Add to tree
                first_file = files[0]
                try:
                    file_size = first_file.stat().st_size
                    size_str = self.format_file_size(file_size)
                    total_duplicate_size += file_size * (len(files) - 1)
                except OSError:
                    size_str = "Unknown"
                
                item = self.results_tree.insert('', 'end', 
                    text=f"Group {len(self.duplicates)}", 
                    values=(file_hash[:8] + "...", size_str, len(files), str(first_file)))
                
                # Add individual files as children
                for i, file_path in enumerate(files):
                    self.results_tree.insert(item, 'end', 
                        text=f"Copy {i+1}", 
                        values=("", "", "", str(file_path)))
        
        # Update summary
        self.summary_text.delete('1.0', tk.END)
        summary = f"""Duplicate Scan Results:
        
Total Files Processed: {processed_files:,}
Duplicate Groups Found: {len(self.duplicates):,}
Duplicate Files: {duplicate_count:,}
Total Wasted Space: {self.format_file_size(total_duplicate_size)}

Top Duplicate Categories:
{self.analyze_duplicate_categories()}
        """
        self.summary_text.insert('1.0', summary)
        
        self.status_var.set(f"Scan complete! Found {len(self.duplicates)} duplicate groups")
        
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def analyze_duplicate_categories(self):
        """Analyze what types of files are duplicated most"""
        categories = defaultdict(int)
        
        for files in self.duplicates.values():
            for file_path in files:
                if 'eth' in str(file_path).lower():
                    categories['ETH Scripts'] += 1
                elif file_path.suffix == '.py':
                    categories['Python Files'] += 1
                elif file_path.suffix == '.sh':
                    categories['Shell Scripts'] += 1
                elif file_path.suffix in ['.jpg', '.png', '.svg']:
                    categories['Images'] += 1
                elif file_path.suffix in ['.txt', '.md']:
                    categories['Documents'] += 1
                else:
                    categories['Other'] += 1
        
        result = ""
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            result += f"- {category}: {count:,} files\n"
        
        return result
    
    def find_eth_scripts(self):
        """Find all ETH-related scripts"""
        self.status_var.set("Finding ETH scripts...")
        self.eth_listbox.delete(0, tk.END)
        self.eth_scripts.clear()
        
        # Search patterns for ETH scripts
        patterns = ['*eth*', '*ethereum*', '*geth*', '*node*setup*', '*blockchain*']
        
        for pattern in patterns:
            for file_path in Path.home().rglob(pattern):
                if file_path.is_file() and file_path.suffix in ['.sh', '.py', '.txt']:
                    if not self.should_exclude_path(file_path):
                        self.eth_scripts.append(file_path)
        
        # Remove duplicates and sort
        self.eth_scripts = sorted(list(set(self.eth_scripts)))
        
        # Add to listbox
        for script in self.eth_scripts:
            self.eth_listbox.insert(tk.END, str(script))
        
        self.status_var.set(f"Found {len(self.eth_scripts)} ETH-related scripts")
    
    def organize_eth_scripts(self):
        """Organize ETH scripts into a clean structure"""
        if not self.eth_scripts:
            messagebox.showwarning("Warning", "No ETH scripts found. Run 'Find All ETH Scripts' first.")
            return
        
        # Create organized structure
        eth_org_dir = Path.home() / "EthereumScripts"
        eth_org_dir.mkdir(exist_ok=True)
        
        # Categories
        categories = {
            'Setup': eth_org_dir / 'Setup',
            'Configuration': eth_org_dir / 'Configuration', 
            'Monitoring': eth_org_dir / 'Monitoring',
            'Backup': eth_org_dir / 'Backup',
            'Archive': eth_org_dir / 'Archive'
        }
        
        for cat_dir in categories.values():
            cat_dir.mkdir(exist_ok=True)
        
        moved_count = 0
        
        for script in self.eth_scripts:
            try:
                # Determine category based on filename/content
                script_name = script.name.lower()
                
                if 'setup' in script_name or 'install' in script_name:
                    dest_dir = categories['Setup']
                elif 'config' in script_name or 'conf' in script_name:
                    dest_dir = categories['Configuration']
                elif 'monitor' in script_name or 'watch' in script_name:
                    dest_dir = categories['Monitoring']
                elif 'backup' in script_name or 'restore' in script_name:
                    dest_dir = categories['Backup']
                else:
                    dest_dir = categories['Archive']
                
                # Create unique filename
                dest_file = dest_dir / script.name
                counter = 1
                while dest_file.exists():
                    stem = script.stem
                    suffix = script.suffix
                    dest_file = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Move file
                shutil.move(str(script), str(dest_file))
                moved_count += 1
                
            except Exception as e:
                print(f"Error moving {script}: {e}")
        
        messagebox.showinfo("Success", f"Organized {moved_count} ETH scripts into {eth_org_dir}")
        self.status_var.set(f"Organized {moved_count} ETH scripts")
    
    def create_master_eth_script(self):
        """Create a master ETH script by combining the best parts"""
        if not self.eth_scripts:
            messagebox.showwarning("Warning", "No ETH scripts found. Run 'Find All ETH Scripts' first.")
            return
        
        master_script_path = Path.home() / "EthereumScripts" / "master_ethereum_setup.sh"
        master_script_path.parent.mkdir(exist_ok=True)
        
        with open(master_script_path, 'w') as master_file:
            master_file.write(f"""#!/bin/bash
# Master Ethereum Node Setup Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Compiled from {len(self.eth_scripts)} source scripts

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/ethereum_setup.log"

# Logging function
log() {{
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}}

log "Starting Master Ethereum Node Setup"

# TODO: Add consolidated setup logic here
# This master script combines functionality from:
""")
            
            # List source scripts
            for script in self.eth_scripts[:10]:  # Limit to first 10
                master_file.write(f"# - {script}\n")
            
            master_file.write(f"""
# Add your consolidated Ethereum setup logic here

log "Master Ethereum Node Setup Complete"
""")
        
        os.chmod(master_script_path, 0o755)
        messagebox.showinfo("Success", f"Created master script: {master_script_path}")
    
    def preview_duplicates(self):
        """Preview what will be deleted"""
        if not self.duplicates:
            messagebox.showwarning("Warning", "No duplicates found. Run scan first.")
            return
        
        preview = "Files that would be removed (keeping newest/primary):\n\n"
        
        for file_hash, files in list(self.duplicates.items())[:20]:  # Show first 20 groups
            files_sorted = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
            preview += f"Group: {files[0].name}\n"
            for i, file_path in enumerate(files_sorted):
                if i == 0:
                    preview += f"  KEEP: {file_path}\n"
                else:
                    preview += f"  DELETE: {file_path}\n"
            preview += "\n"
        
        if len(self.duplicates) > 20:
            preview += f"... and {len(self.duplicates) - 20} more groups\n"
        
        # Show in new window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Duplicate Removal Preview")
        preview_window.geometry("800x600")
        
        text_widget = tk.Text(preview_window, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(preview_window, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert('1.0', preview)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def remove_duplicates(self, strategy):
        """Remove duplicates using specified strategy"""
        if not self.duplicates:
            messagebox.showwarning("Warning", "No duplicates found. Run scan first.")
            return
        
        if not messagebox.askyesno("Confirm", f"Remove {sum(len(files)-1 for files in self.duplicates.values())} duplicate files?"):
            return
        
        self.create_backup()
        
        removed_count = 0
        freed_space = 0
        
        for file_hash, files in self.duplicates.items():
            try:
                if strategy == 'newest':
                    # Keep the newest file
                    files_sorted = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
                    files_to_remove = files_sorted[1:]
                else:  # strategy == 'primary'
                    # Keep the one in the primary location (e.g., not in cache, backup, or temp)
                    primary_files = [f for f in files if not self.should_exclude_path(f)]
                    if primary_files:
                        files_to_remove = [f for f in files if f != primary_files[0]]
                    else:
                        # If no primary location found, keep newest
                        files_sorted = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
                        files_to_remove = files_sorted[1:]
                
                # Remove duplicate files
                for file_path in files_to_remove:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        removed_count += 1
                        freed_space += file_size
                    except OSError as e:
                        print(f"Error removing {file_path}: {e}")
                        
            except Exception as e:
                print(f"Error processing duplicate group: {e}")
        
        messagebox.showinfo("Cleanup Complete", 
            f"Removed {removed_count} duplicate files\n"
            f"Freed {self.format_file_size(freed_space)} of disk space")
        
        self.status_var.set(f"Cleanup complete! Removed {removed_count} files")
        
        # Refresh scan
        self.start_scan()
    
    def create_backup(self):
        """Create backup of duplicate files before removal"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'total_groups': len(self.duplicates),
            'files': {}
        }
        
        for file_hash, files in self.duplicates.items():
            backup_info['files'][file_hash] = [str(f) for f in files]
        
        # Save backup info
        with open(self.backup_dir / 'backup_info.json', 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        self.status_var.set(f"Backup created at {self.backup_dir}")
    
    def restore_backup(self):
        """Restore from backup"""
        backup_dir = filedialog.askdirectory(
            title="Select backup directory",
            initialdir=Path.home() / "CleanupBackups"
        )
        
        if backup_dir:
            messagebox.showinfo("Restore", "Backup restore functionality would be implemented here")

def main():
    root = tk.Tk()
    app = DuplicateFinder(root)
    root.mainloop()

if __name__ == "__main__":
    main()