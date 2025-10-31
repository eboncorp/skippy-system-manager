#!/usr/bin/env python3
"""
Smart Document Organizer
Automatically reads and categorizes both business and personal documents
"""

import os
import sys
import shutil
import re
from datetime import datetime
from pathlib import Path

class SmartDocumentOrganizer:
    def __init__(self):
        self.scan_base = Path.home() / "Scans"
        self.incoming_dir = self.scan_base / "Incoming"
        self.documents_dir = Path.home() / "Documents"
        self.setup_enhanced_folders()
        
        # Enhanced document classification patterns
        self.document_patterns = {
            # BUSINESS DOCUMENTS
            "Business/Tax_Documents/IRS_Forms": [
                r"Form\s+\d+", r"SS-\d+", r"CP\s*\d+", r"Internal Revenue Service", 
                r"IRS", r"1099", r"W-2", r"1040", r"8869", r"941", r"940", r"FEIN", r"EIN"
            ],
            "Business/Tax_Documents/State_Forms": [
                r"State.*Tax", r"Kentucky.*Revenue", r"State.*Income"
            ],
            "Business/Tax_Documents/Local_Tax": [
                r"Louisville.*Metro.*Revenue", r"Occupational.*Tax", r"Local.*Tax"
            ],
            "Business/Business_Registration/Federal": [
                r"Corporation.*Election", r"S.*Corporation", r"LLC.*Formation",
                r"Business.*Registration", r"Articles.*Incorporation"
            ],
            "Business/Banking_Financial/EFTPS": [
                r"EFTPS", r"Electronic.*Federal.*Tax.*Payment", r"PIN.*\d{4}"
            ],
            "Business/Legal/Contracts": [
                r"Contract", r"Agreement", r"Terms.*Conditions", r"Service.*Agreement"
            ],
            "Business/Insurance/Business_Liability": [
                r"Business.*Insurance", r"Liability.*Policy", r"Commercial.*Insurance"
            ],
            
            # PERSONAL DOCUMENTS
            "Personal/Medical/Records": [
                r"Medical.*Record", r"Patient", r"Doctor", r"Physician", r"Hospital",
                r"Lab.*Result", r"Blood.*Test", r"X-Ray", r"MRI", r"Prescription"
            ],
            "Personal/Medical/Insurance": [
                r"Health.*Insurance", r"Medical.*Insurance", r"Insurance.*Card",
                r"Coverage", r"Premium", r"Deductible", r"Co-pay"
            ],
            "Personal/Taxes/Federal": [
                r"1040", r"Tax.*Return", r"Refund", r"W-2", r"1099", r"Schedule"
            ],
            "Personal/Taxes/State": [
                r"State.*Tax.*Return", r"Kentucky.*Tax"
            ],
            "Personal/Financial/Banking": [
                r"Bank.*Statement", r"Account.*Statement", r"Checking", r"Savings",
                r"Credit.*Card", r"Loan", r"Mortgage"
            ],
            "Personal/Financial/Investment": [
                r"Investment", r"Stock", r"Bond", r"401k", r"IRA", r"Retirement",
                r"Portfolio", r"Dividend"
            ],
            "Personal/Insurance/Auto": [
                r"Auto.*Insurance", r"Car.*Insurance", r"Vehicle.*Insurance"
            ],
            "Personal/Insurance/Home": [
                r"Homeowner", r"Home.*Insurance", r"Property.*Insurance"
            ],
            "Personal/Insurance/Life": [
                r"Life.*Insurance", r"Term.*Life", r"Whole.*Life"
            ],
            "Personal/Legal/Estate": [
                r"Will", r"Testament", r"Estate", r"Trust", r"Power.*Attorney"
            ],
            "Personal/Legal/Property": [
                r"Deed", r"Title", r"Property.*Record", r"Real.*Estate"
            ],
            "Personal/Education/Transcripts": [
                r"Transcript", r"Diploma", r"Degree", r"Certificate", r"GPA"
            ],
            "Personal/Travel/Documents": [
                r"Passport", r"Visa", r"Travel.*Document", r"Boarding.*Pass", r"Itinerary"
            ]
        }
        
        # Business vs Personal keywords
        self.business_indicators = [
            "corporation", "llc", "business", "commercial", "company", "corp",
            "fein", "ein", "employer", "payroll", "revenue", "profit", "loss"
        ]
        
        self.personal_indicators = [
            "personal", "individual", "patient", "medical", "health", "family",
            "home", "residence", "ssn", "social security"
        ]
    
    def setup_enhanced_folders(self):
        """Create comprehensive folder structure for both business and personal"""
        folders = {
            # BUSINESS FOLDERS
            "Business": {
                "Tax_Documents": ["IRS_Forms", "State_Forms", "Local_Tax", "Quarterly_Reports"],
                "Business_Registration": ["Federal", "State", "Local", "Licenses"],
                "Banking_Financial": ["EFTPS", "Bank_Accounts", "Payment_Systems", "Statements"],
                "Legal": ["Contracts", "Articles", "Compliance", "Litigation"],
                "Insurance": ["Business_Liability", "Workers_Comp", "Property", "Professional"],
                "Financial": ["Accounting", "Bookkeeping", "Audits", "Statements"],
                "Invoices": ["Outgoing", "Incoming", "Payment_Records"],
                "Receipts": ["Business_Expenses", "Office_Supplies", "Equipment"],
                "Reports": ["Monthly", "Quarterly", "Annual", "Compliance"],
                "Correspondence": ["Government", "Vendors", "Clients", "Legal"]
            },
            
            # PERSONAL FOLDERS
            "Personal": {
                "Medical": ["Records", "Insurance", "Bills", "Prescriptions", "Test_Results"],
                "Taxes": ["Federal", "State", "Supporting_Documents", "Returns"],
                "Financial": ["Banking", "Investment", "Credit_Cards", "Loans", "Retirement"],
                "Insurance": ["Auto", "Home", "Life", "Health", "Disability"],
                "Legal": ["Estate", "Property", "Contracts", "Court_Documents"],
                "Education": ["Transcripts", "Certificates", "Continuing_Ed"],
                "Travel": ["Documents", "Reservations", "Receipts"],
                "Warranties": ["Electronics", "Appliances", "Vehicles"],
                "Receipts": ["Personal", "Household", "Medical", "Auto"],
                "Other": []
            }
        }
        
        for main_category, subcategories in folders.items():
            main_path = self.scan_base / main_category
            main_path.mkdir(parents=True, exist_ok=True)
            
            for category, subfolders in subcategories.items():
                category_path = main_path / category
                category_path.mkdir(exist_ok=True)
                
                for subfolder in subfolders:
                    (category_path / subfolder).mkdir(exist_ok=True)
    
    def determine_business_or_personal(self, content_text):
        """Determine if document is business or personal based on content"""
        content_lower = content_text.lower()
        
        business_score = sum(1 for keyword in self.business_indicators if keyword in content_lower)
        personal_score = sum(1 for keyword in self.personal_indicators if keyword in content_lower)
        
        if business_score > personal_score:
            return "Business"
        elif personal_score > business_score:
            return "Personal"
        else:
            return "Unknown"
    
    def analyze_document_content(self, file_path):
        """Analyze document to determine best category"""
        try:
            filename = file_path.name.lower()
            
            # First, try to match specific document patterns
            best_match = None
            highest_score = 0
            
            for category, patterns in self.document_patterns.items():
                score = 0
                for pattern in patterns:
                    if re.search(pattern.lower(), filename):
                        score += 1
                
                if score > highest_score:
                    highest_score = score
                    best_match = category
            
            if best_match:
                return best_match
            
            # Fallback: determine business vs personal first
            main_category = self.determine_business_or_personal(filename)
            
            if main_category == "Unknown":
                # Use heuristics based on common document types
                if any(word in filename for word in ["tax", "irs", "1099", "w2"]):
                    if any(word in filename for word in ["business", "corp", "llc"]):
                        return "Business/Tax_Documents/IRS_Forms"
                    else:
                        return "Personal/Taxes/Federal"
                elif any(word in filename for word in ["medical", "doctor", "hospital"]):
                    return "Personal/Medical/Records"
                elif any(word in filename for word in ["bank", "statement", "account"]):
                    if any(word in filename for word in ["business", "corp"]):
                        return "Business/Banking_Financial/Bank_Accounts"
                    else:
                        return "Personal/Financial/Banking"
                elif any(word in filename for word in ["insurance"]):
                    if any(word in filename for word in ["auto", "car", "vehicle"]):
                        return "Personal/Insurance/Auto"
                    elif any(word in filename for word in ["home", "house"]):
                        return "Personal/Insurance/Home"
                    elif any(word in filename for word in ["business"]):
                        return "Business/Insurance/Business_Liability"
                    else:
                        return "Personal/Insurance/Health"
                
                return "Personal/Other"  # Default fallback
            
            return f"{main_category}/Other"
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return "Personal/Other"
    
    def organize_document(self, file_path, interactive=False):
        """Organize a single document with optional interactive mode"""
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return False
        
        # Analyze content to determine category
        suggested_category = self.analyze_document_content(file_path)
        
        print(f"\n📄 File: {file_path.name}")
        print(f"   Suggested: {suggested_category}")
        
        final_category = suggested_category
        custom_name = None
        
        if interactive:
            # Ask user to confirm or modify
            confirm = input("   Accept suggestion? (y/n/modify): ").strip().lower()
            if confirm == 'n' or confirm == 'modify':
                print("   Available categories:")
                print("   Business: Tax_Documents, Business_Registration, Banking_Financial, Legal, etc.")
                print("   Personal: Medical, Taxes, Financial, Insurance, Legal, etc.")
                final_category = input("   Enter category path: ").strip()
            
            custom_name = input("   Custom name (optional): ").strip()
        
        # Generate destination path
        dest_dir = self.scan_base / final_category
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
            print(f"✅ Organized: {final_category}/{dest_path.name}")
            return True
        except Exception as e:
            print(f"❌ Error moving {file_path.name}: {e}")
            return False
    
    def process_incoming_documents(self, interactive=False):
        """Process documents from both incoming folder and Documents folder"""
        all_files = []
        
        # Check incoming folder
        if self.incoming_dir.exists():
            incoming_files = [f for f in self.incoming_dir.iterdir() if f.is_file()]
            all_files.extend(incoming_files)
        
        # Check Documents folder for recent PDFs (likely scans)
        if self.documents_dir.exists():
            recent_docs = [f for f in self.documents_dir.iterdir() 
                          if f.is_file() and f.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']]
            all_files.extend(recent_docs)
        
        # Check Personal/Other folder for documents that need reorganization
        personal_other = self.scan_base / "Personal" / "Other"
        if personal_other.exists():
            other_files = [f for f in personal_other.iterdir() if f.is_file()]
            all_files.extend(other_files)
        
        if not all_files:
            print("No files found in incoming folder or Documents folder")
            return
        
        print(f"\n📄 Found {len(all_files)} documents to organize")
        organized_count = 0
        
        for file_path in all_files:
            if self.organize_document(file_path, interactive):
                organized_count += 1
        
        print(f"\n✅ Organized {organized_count}/{len(all_files)} documents")
    
    def show_structure(self):
        """Show current folder structure with file counts"""
        print("\n📁 DOCUMENT ORGANIZATION STRUCTURE:")
        for main_category in ["Business", "Personal"]:
            main_path = self.scan_base / main_category
            if main_path.exists():
                total_files = sum(1 for f in main_path.rglob('*') if f.is_file())
                print(f"\n🏢 {main_category}/ ({total_files} total files)")
                
                for category in sorted(main_path.iterdir()):
                    if category.is_dir():
                        cat_files = sum(1 for f in category.rglob('*') if f.is_file())
                        print(f"   📂 {category.name}/ ({cat_files} files)")
                        
                        for subfolder in sorted(category.iterdir()):
                            if subfolder.is_dir():
                                sub_files = len([f for f in subfolder.iterdir() if f.is_file()])
                                if sub_files > 0:
                                    print(f"      📁 {subfolder.name}/ ({sub_files} files)")

def main():
    organizer = SmartDocumentOrganizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "auto":
            organizer.process_incoming_documents(interactive=False)
        elif command == "interactive":
            organizer.process_incoming_documents(interactive=True)
        elif command == "structure":
            organizer.show_structure()
        elif command == "setup":
            organizer.setup_enhanced_folders()
            print("✅ Enhanced folder structure created")
        else:
            print("❌ Unknown command. Use: auto, interactive, structure, or setup")
    else:
        print("🎯 SMART DOCUMENT ORGANIZER")
        print("=" * 50)
        print("Automatically organizes business and personal documents")
        print()
        print("Commands:")
        print("  python3 smart_document_organizer.py auto        - Auto-organize all documents")
        print("  python3 smart_document_organizer.py interactive - Interactive organization")
        print("  python3 smart_document_organizer.py structure   - Show folder structure")
        print("  python3 smart_document_organizer.py setup       - Setup folder structure")
        print()
        organizer.show_structure()

if __name__ == "__main__":
    main()