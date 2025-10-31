#!/usr/bin/env python3
"""
Document Scanning Organizer
A tool to help organize scanned documents into personal and business categories
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess

class ScanOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Document Scan Organizer")
        self.root.geometry("800x600")
        
        # Base scan directory
        self.scan_base = Path.home() / "Scans"
        self.setup_folders()
        
        self.create_widgets()
        
    def setup_folders(self):
        """Create the folder structure if it doesn't exist"""
        folders = {
            "Personal": [
                "Medical", "Financial", "Insurance", "Legal", "Taxes", 
                "Receipts", "Warranties", "Education", "Travel", "Other"
            ],
            "Business": [
                "Contracts", "Invoices", "Receipts", "Financial", "Legal",
                "Correspondence", "Reports", "Taxes", "Insurance", "Other"
            ],
            "Incoming": []  # Temporary folder for new scans
        }
        
        for category, subfolders in folders.items():
            category_path = self.scan_base / category
            category_path.mkdir(parents=True, exist_ok=True)
            
            for subfolder in subfolders:
                (category_path / subfolder).mkdir(exist_ok=True)
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Document Scan Organizer", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Select Files", padding="10")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.selected_files_var = tk.StringVar()
        ttk.Button(file_frame, text="Browse for Files", 
                  command=self.browse_files).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(file_frame, text="Scan New Document", 
                  command=self.scan_new).grid(row=0, column=1)
        
        # Selected files display
        self.files_listbox = tk.Listbox(file_frame, height=6)
        self.files_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), 
                               pady=(10, 0))
        
        # Category selection frame
        category_frame = ttk.LabelFrame(main_frame, text="Organize Documents", padding="10")
        category_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Category selection
        ttk.Label(category_frame, text="Category:").grid(row=0, column=0, sticky=tk.W)
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var,
                                     values=["Personal", "Business"])
        category_combo.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        category_combo.bind('<<ComboboxSelected>>', self.update_subcategories)
        
        # Subcategory selection
        ttk.Label(category_frame, text="Subcategory:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.subcategory_var = tk.StringVar()
        self.subcategory_combo = ttk.Combobox(category_frame, textvariable=self.subcategory_var)
        self.subcategory_combo.grid(row=1, column=1, padx=(10, 0), sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Custom name
        ttk.Label(category_frame, text="Custom Name (optional):").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.custom_name_var = tk.StringVar()
        ttk.Entry(category_frame, textvariable=self.custom_name_var).grid(row=2, column=1, padx=(10, 0), 
                                                                         sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Organize button
        ttk.Button(category_frame, text="Organize Selected Files", 
                  command=self.organize_files).grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding="10")
        actions_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(actions_frame, text="Open Scans Folder", 
                  command=self.open_scans_folder).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(actions_frame, text="Process Incoming Folder", 
                  command=self.process_incoming).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(actions_frame, text="Create New Subfolder", 
                  command=self.create_subfolder).grid(row=0, column=2)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set(f"Ready. Scan folder: {self.scan_base}")
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        
        # Configure column weights
        main_frame.columnconfigure(1, weight=1)
        file_frame.columnconfigure(1, weight=1)
        category_frame.columnconfigure(1, weight=1)
        
    def browse_files(self):
        """Browse for files to organize"""
        files = filedialog.askopenfilenames(
            title="Select scanned documents",
            filetypes=[("PDF files", "*.pdf"), ("Image files", "*.png *.jpg *.jpeg *.tiff"), 
                      ("All files", "*.*")]
        )
        
        self.files_listbox.delete(0, tk.END)
        for file in files:
            self.files_listbox.insert(tk.END, file)
            
        self.status_var.set(f"Selected {len(files)} files")
    
    def scan_new(self):
        """Launch Simple Scan to scan a new document"""
        try:
            subprocess.Popen(['simple-scan'])
            self.status_var.set("Launched Simple Scan")
        except Exception as e:
            messagebox.showerror("Error", f"Could not launch Simple Scan: {str(e)}")
    
    def update_subcategories(self, event=None):
        """Update subcategories based on selected category"""
        category = self.category_var.get()
        
        subcategories = {
            "Personal": ["Medical", "Financial", "Insurance", "Legal", "Taxes", 
                        "Receipts", "Warranties", "Education", "Travel", "Other"],
            "Business": ["Contracts", "Invoices", "Receipts", "Financial", "Legal",
                        "Correspondence", "Reports", "Taxes", "Insurance", "Other"]
        }
        
        if category in subcategories:
            self.subcategory_combo['values'] = subcategories[category]
            self.subcategory_var.set("")
    
    def organize_files(self):
        """Organize selected files into the chosen category/subcategory"""
        files = [self.files_listbox.get(i) for i in range(self.files_listbox.size())]
        
        if not files:
            messagebox.showwarning("Warning", "No files selected")
            return
            
        category = self.category_var.get()
        subcategory = self.subcategory_var.get()
        
        if not category or not subcategory:
            messagebox.showwarning("Warning", "Please select both category and subcategory")
            return
        
        destination_folder = self.scan_base / category / subcategory
        destination_folder.mkdir(parents=True, exist_ok=True)
        
        organized_count = 0
        
        for file_path in files:
            try:
                file_obj = Path(file_path)
                if file_obj.exists():
                    # Generate new filename with timestamp if custom name provided
                    if self.custom_name_var.get().strip():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_name = f"{self.custom_name_var.get().strip()}_{timestamp}{file_obj.suffix}"
                    else:
                        # Use original name with timestamp if file exists
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_name = f"{file_obj.stem}_{timestamp}{file_obj.suffix}"
                    
                    destination = destination_folder / new_name
                    
                    # Ensure unique filename
                    counter = 1
                    while destination.exists():
                        base_name = destination.stem.rsplit('_', 1)[0] if '_' in destination.stem else destination.stem
                        destination = destination_folder / f"{base_name}_{timestamp}_{counter}{file_obj.suffix}"
                        counter += 1
                    
                    shutil.move(str(file_obj), str(destination))
                    organized_count += 1
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move {file_path}: {str(e)}")
        
        self.files_listbox.delete(0, tk.END)
        self.custom_name_var.set("")
        self.status_var.set(f"Organized {organized_count} files into {category}/{subcategory}")
        
        if organized_count > 0:
            messagebox.showinfo("Success", f"Successfully organized {organized_count} files!")
    
    def open_scans_folder(self):
        """Open the scans folder in file manager"""
        try:
            subprocess.Popen(['nautilus', str(self.scan_base)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
    
    def process_incoming(self):
        """Process files in the incoming folder"""
        incoming_folder = self.scan_base / "Incoming"
        if not incoming_folder.exists():
            incoming_folder.mkdir()
            
        files = list(incoming_folder.glob("*"))
        pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
        image_files = [f for f in files if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']]
        
        if not files:
            messagebox.showinfo("Info", "No files found in Incoming folder")
            return
        
        self.files_listbox.delete(0, tk.END)
        for file in files:
            if file.is_file():
                self.files_listbox.insert(tk.END, str(file))
                
        self.status_var.set(f"Found {len(files)} files in Incoming folder")
    
    def create_subfolder(self):
        """Create a new subfolder in selected category"""
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("Warning", "Please select a category first")
            return
            
        subfolder_name = tk.simpledialog.askstring("New Subfolder", 
                                                  f"Enter name for new subfolder in {category}:")
        if subfolder_name:
            new_folder = self.scan_base / category / subfolder_name
            try:
                new_folder.mkdir(exist_ok=True)
                self.update_subcategories()  # Refresh subcategory list
                messagebox.showinfo("Success", f"Created folder: {new_folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not create folder: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScanOrganizer(root)
    root.mainloop()