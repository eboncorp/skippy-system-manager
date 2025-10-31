#!/usr/bin/env python3
"""
Business Document Auto-Organizer
Reads and categorizes business documents based on content analysis
"""

import os
import sys
import shutil
import re
from datetime import datetime
from pathlib import Path

class BusinessDocumentOrganizer:
    def __init__(self):
        self.scan_base = Path.home() / "Scans" / "Business"
        self.incoming_dir = Path.home() / "Scans" / "Incoming"
        self.setup_business_folders()
        
        # Document type patterns
        self.document_patterns = {
            "Tax_Documents/IRS_Forms": [
                r"Form\s+\d+", r"SS-\d+", r"CP\s*\d+", r"Internal Revenue Service", 
                r"IRS", r"1099", r"W-2", r"1040", r"8869", r"941", r"940"
            ],
            "Tax_Documents/State_Forms": [
                r"State.*Tax", r"Kentucky.*Revenue", r"State.*Income"
            ],
            "Tax_Documents/Local_Tax": [
                r"Louisville.*Metro.*Revenue", r"Occupational.*Tax", r"Local.*Tax"
            ],
            "Business_Registration/Federal": [
                r"FEIN", r"EIN", r"Federal.*Tax.*ID", r"Business.*Registration",
                r"Corporation.*Election", r"S.*Corporation", r"LLC.*Formation"
            ],
            "Business_Registration/State": [
                r"Articles.*Incorporation", r"State.*Registration", r"Secretary.*State"
            ],
            "Business_Registration/Local": [
                r"Business.*License", r"Local.*Registration", r"City.*Permit"
            ],
            "Banking_Financial/EFTPS": [
                r"EFTPS", r"Electronic.*Federal.*Tax.*Payment", r"PIN.*\d{4}"
            ],
            "Banking_Financial/Bank_Setup": [
                r"Bank.*Account", r"Routing.*Number", r"Account.*Opening"
            ],
            "Legal/Contracts": [
                r"Contract", r"Agreement", r"Terms.*Conditions"
            ],
            "Correspondence": [
                r"Dear.*", r"Letter", r"Notice.*Date", r"Re:"
            ]
        }
    
    def setup_business_folders(self):
        """Create comprehensive business folder structure"""
        folders = {
            "Tax_Documents": ["IRS_Forms", "State_Forms", "Local_Tax", "Quarterly_Reports"],
            "Business_Registration": ["Federal", "State", "Local", "Licenses"],
            "Banking_Financial": ["EFTPS", "Bank_Setup", "Account_Statements", "Payment_Systems"],
            "Legal": ["Contracts", "Articles", "Bylaws", "Compliance"],
            "Insurance": ["Business_Liability", "Workers_Comp", "Property"],
            "Financial": ["Accounting", "Bookkeeping", "Audits", "Financial_Statements"],
            "Invoices": ["Outgoing", "Incoming", "Payment_Records"],
            "Receipts": ["Business_Expenses", "Office_Supplies", "Equipment", "Travel"],
            "Reports": ["Monthly", "Quarterly", "Annual", "Compliance"],
            "Correspondence": ["Government", "Vendors", "Clients", "Legal"]
        }
        
        for category, subfolders in folders.items():
            category_path = self.scan_base / category
            category_path.mkdir(parents=True, exist_ok=True)
            
            for subfolder in subfolders:
                (category_path / subfolder).mkdir(exist_ok=True)
    
    def analyze_document_content(self, file_path):
        """Analyze document content to determine category"""
        try:
            # This would normally use OCR or PDF text extraction
            # For now, we'll check filename and simulate content analysis
            filename = file_path.name.lower()
            
            # Check each category pattern
            for category, patterns in self.document_patterns.items():
                for pattern in patterns:
                    if re.search(pattern.lower(), filename):
                        return category
            
            # Default categorization based on common business document types
            if any(word in filename for word in ["tax", "irs", "form"]):
                return "Tax_Documents/IRS_Forms"
            elif any(word in filename for word in ["contract", "agreement"]):
                return "Legal/Contracts"
            elif any(word in filename for word in ["invoice", "bill"]):
                return "Invoices/Incoming"
            elif any(word in filename for word in ["receipt", "expense"]):
                return "Receipts/Business_Expenses"
            elif any(word in filename for word in ["bank", "account"]):
                return "Banking_Financial/Bank_Setup"
            
            return "Other"  # Fallback
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return "Other"
    
    def organize_document(self, file_path, custom_name=None):
        """Organize a single document"""
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return False
        
        # Analyze content to determine category
        suggested_category = self.analyze_document_content(file_path)
        
        # Generate destination path
        if suggested_category == "Other":
            dest_dir = self.scan_base / "Other"
        else:
            dest_dir = self.scan_base / suggested_category
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_name:
            dest_filename = f"{custom_name}_{timestamp}{file_path.suffix}"
        else:
            dest_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        dest_path = dest_dir / dest_filename
        
        # Ensure unique filename
        counter = 1
        while dest_path.exists():
            stem = dest_filename.rsplit('.', 1)[0] if '.' in dest_filename else dest_filename
            ext = '.' + dest_filename.rsplit('.', 1)[1] if '.' in dest_filename else ''
            dest_path = dest_dir / f"{stem}_{counter}{ext}"
            counter += 1
        
        try:
            shutil.move(str(file_path), str(dest_path))
            print(f"✅ Organized: {file_path.name}")
            print(f"   → {suggested_category}/{dest_path.name}")
            return True, suggested_category
        except Exception as e:
            print(f"❌ Error moving {file_path.name}: {e}")
            return False, None
    
    def process_incoming_documents(self):
        """Process all documents in incoming folder"""
        if not self.incoming_dir.exists():
            print("No incoming folder found")
            return
        
        files = [f for f in self.incoming_dir.iterdir() if f.is_file()]
        if not files:
            print("No files in incoming folder")
            return
        
        print(f"\n📄 Found {len(files)} documents to organize:")
        organized_count = 0
        
        for file_path in files:
            print(f"\n📄 Processing: {file_path.name}")
            success, category = self.organize_document(file_path)
            if success:
                organized_count += 1
        
        print(f"\n✅ Organized {organized_count}/{len(files)} documents")
    
    def show_structure(self):
        """Show current business folder structure with file counts"""
        print("\n📁 BUSINESS DOCUMENT STRUCTURE:")
        for item in sorted(self.scan_base.iterdir()):
            if item.is_dir():
                total_files = sum(1 for f in item.rglob('*') if f.is_file())
                print(f"   📂 {item.name}/ ({total_files} files)")
                
                for subitem in sorted(item.iterdir()):
                    if subitem.is_dir():
                        file_count = len([f for f in subitem.iterdir() if f.is_file()])
                        print(f"      📁 {subitem.name}/ ({file_count} files)")

def main():
    organizer = BusinessDocumentOrganizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "process":
            organizer.process_incoming_documents()
        elif command == "structure":
            organizer.show_structure()
        elif command == "setup":
            organizer.setup_business_folders()
            print("✅ Business folder structure created")
        else:
            print("❌ Unknown command. Use: process, structure, or setup")
    else:
        print("🏢 BUSINESS DOCUMENT ORGANIZER")
        print("=" * 40)
        print("Commands:")
        print("  python3 business_document_organizer.py process   - Process incoming documents")
        print("  python3 business_document_organizer.py structure - Show folder structure")
        print("  python3 business_document_organizer.py setup     - Setup folder structure")
        print()
        organizer.show_structure()

if __name__ == "__main__":
    main()