#!/usr/bin/env python3
"""
Simple Document Scan Organizer
Works with your Brother MFC-7860DW scanner
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

class SimpleScanOrganizer:
    def __init__(self):
        self.scan_base = Path.home() / "Scans"
        self.setup_folders()
    
    def setup_folders(self):
        """Create organized folder structure"""
        folders = {
            "Personal": ["Medical", "Financial", "Insurance", "Legal", "Taxes", 
                        "Receipts", "Warranties", "Education", "Travel", "Other"],
            "Business": ["Contracts", "Invoices", "Receipts", "Financial", "Legal",
                        "Correspondence", "Reports", "Taxes", "Insurance", "Other"],
            "Incoming": []
        }
        
        for category, subfolders in folders.items():
            category_path = self.scan_base / category
            category_path.mkdir(parents=True, exist_ok=True)
            
            for subfolder in subfolders:
                (category_path / subfolder).mkdir(exist_ok=True)
    
    def scan_document(self, filename=None):
        """Launch Simple Scan to scan a new document"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_{timestamp}"
        
        print(f"📄 Launching Simple Scan...")
        print(f"   Your Brother MFC-7860DW should be available")
        print(f"   Save location: {self.scan_base}/Incoming/")
        
        # Launch Simple Scan
        try:
            subprocess.run(['simple-scan'], check=False)
        except Exception as e:
            print(f"❌ Error launching Simple Scan: {e}")
    
    def organize_file(self, file_path, category, subcategory, custom_name=None):
        """Move file to organized location"""
        source = Path(file_path)
        if not source.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        # Create destination
        dest_dir = self.scan_base / category / subcategory
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if custom_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_name = f"{custom_name}_{timestamp}{source.suffix}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_name = f"{source.stem}_{timestamp}{source.suffix}"
        
        dest_file = dest_dir / dest_name
        
        # Ensure unique filename
        counter = 1
        while dest_file.exists():
            stem = dest_name.rsplit('.', 1)[0] if '.' in dest_name else dest_name
            ext = '.' + dest_name.rsplit('.', 1)[1] if '.' in dest_name else ''
            dest_file = dest_dir / f"{stem}_{counter}{ext}"
            counter += 1
        
        try:
            shutil.move(str(source), str(dest_file))
            print(f"✅ Moved: {source.name} → {category}/{subcategory}/{dest_file.name}")
            return True
        except Exception as e:
            print(f"❌ Error moving file: {e}")
            return False
    
    def list_incoming(self):
        """List files in the incoming folder"""
        incoming_dir = self.scan_base / "Incoming"
        if not incoming_dir.exists():
            print("📁 No incoming folder found")
            return []
        
        files = []
        for file_path in incoming_dir.iterdir():
            if file_path.is_file():
                files.append(file_path)
        
        return files
    
    def show_structure(self):
        """Show the folder structure"""
        print(f"\n📁 SCAN ORGANIZATION STRUCTURE")
        print(f"   Base: {self.scan_base}")
        
        for item in self.scan_base.iterdir():
            if item.is_dir():
                print(f"   📂 {item.name}/")
                for subitem in item.iterdir():
                    if subitem.is_dir():
                        file_count = len([f for f in subitem.iterdir() if f.is_file()])
                        print(f"      📁 {subitem.name}/ ({file_count} files)")
    
    def quick_organize_menu(self):
        """Interactive menu for organizing documents"""
        incoming_files = self.list_incoming()
        
        if not incoming_files:
            print("\n📥 No files in incoming folder")
            return
        
        print(f"\n📥 INCOMING FILES ({len(incoming_files)}):")
        for i, file_path in enumerate(incoming_files, 1):
            file_size = file_path.stat().st_size if file_path.exists() else 0
            size_mb = file_size / 1024 / 1024
            print(f"   {i}. {file_path.name} ({size_mb:.1f} MB)")
        
        # Simple organization
        print(f"\n🎯 ORGANIZE FILES:")
        print(f"   Categories: Personal, Business")
        print(f"   Common Subcategories:")
        print(f"     Personal: Medical, Financial, Legal, Receipts, Other")
        print(f"     Business: Contracts, Invoices, Financial, Legal, Other")
        
        for file_path in incoming_files:
            print(f"\n📄 File: {file_path.name}")
            category = input("   Category (Personal/Business): ").strip().title()
            
            if category not in ['Personal', 'Business']:
                print("   ❌ Invalid category, skipping...")
                continue
            
            subcategory = input("   Subcategory: ").strip().title()
            custom_name = input("   Custom name (optional): ").strip()
            
            if self.organize_file(file_path, category, subcategory, custom_name):
                print("   ✅ Organized successfully!")

def main():
    organizer = SimpleScanOrganizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "scan":
            organizer.scan_document()
        elif command == "organize":
            organizer.quick_organize_menu()
        elif command == "list":
            files = organizer.list_incoming()
            if files:
                print(f"📥 Incoming files: {len(files)}")
                for f in files:
                    print(f"   • {f.name}")
            else:
                print("📥 No incoming files")
        elif command == "structure":
            organizer.show_structure()
        else:
            print("❌ Unknown command")
    else:
        # Interactive mode
        print("🎯 SIMPLE SCAN ORGANIZER")
        print("=" * 40)
        print("Your Brother MFC-7860DW is ready!")
        print(f"Scan folder: {organizer.scan_base}")
        print()
        print("Commands:")
        print("  python3 simple_scan_organizer.py scan      - Launch scanner")
        print("  python3 simple_scan_organizer.py organize  - Organize files")
        print("  python3 simple_scan_organizer.py list      - List incoming files")
        print("  python3 simple_scan_organizer.py structure - Show folder structure")
        print()
        
        # Show current structure
        organizer.show_structure()
        
        # Check for incoming files
        incoming = organizer.list_incoming()
        if incoming:
            print(f"\n📥 You have {len(incoming)} files waiting to be organized!")
            organize_now = input("Organize them now? (y/n): ").lower().strip()
            if organize_now == 'y':
                organizer.quick_organize_menu()

if __name__ == "__main__":
    main()