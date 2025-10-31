#!/usr/bin/env python3
"""
System-wide Document Organizer
Scans all common document locations and organizes files based on content analysis
"""

import os
import shutil
from pathlib import Path
import PyPDF2
import re
from typing import List, Dict, Tuple

class SystemWideOrganizer:
    def __init__(self):
        self.home = Path.home()
        self.scan_base = self.home / "Scans"
        
        # Common document locations to scan
        self.scan_locations = [
            self.home / "Documents",
            self.home / "Downloads", 
            self.home / "Desktop",
            self.home / "Scans",
            self.home / "Pictures" / "Scanner",
        ]
        
        # Document categories and their patterns
        self.categories = {
            "Business": {
                "Run Dave Run LLC": ["run dave run", "rdr", "dave run"],
                "Pennybrooke": ["pennybrooke", "penny brooke"],
                "PaperWerk Services": ["paperwerk", "paper werk"],
                "General": ["llc", "business", "registration", "ein", "tax id"]
            },
            "Personal": {
                "Medical": ["medical", "health", "doctor", "svs vision", "eye care", "prescription"],
                "Legal": ["will", "testament", "legal", "attorney", "court"],
                "Property": ["mortgage", "deed", "property", "real estate", "title"],
                "Education": ["student", "loan", "university", "college", "degree"],
                "Tax": ["1099", "tax", "irs", "w-2", "w2", "income"]
            }
        }

    def extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.lower()
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return ""

    def categorize_document(self, file_path: Path) -> List[Tuple[str, str]]:
        """Categorize document based on content analysis"""
        categories = []
        
        # Get filename for initial hints
        filename = file_path.name.lower()
        
        # For PDFs, analyze content
        if file_path.suffix.lower() == '.pdf':
            content = self.extract_pdf_text(file_path)
        else:
            content = filename
        
        # Check business categories
        for business, keywords in self.categories["Business"].items():
            if any(keyword in content for keyword in keywords):
                categories.append(("Business", business))
        
        # Check personal categories  
        for category, keywords in self.categories["Personal"].items():
            if any(keyword in content for keyword in keywords):
                if category == "Medical":
                    categories.append(("Personal", "Medical/Bills"))
                else:
                    categories.append(("Personal", category))
        
        # Default fallback
        if not categories:
            categories.append(("Personal", "Other"))
            
        return categories

    def create_directory_structure(self, base_path: Path, category: str, subcategory: str):
        """Create directory structure if it doesn't exist"""
        target_dir = base_path / category / subcategory
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def find_all_documents(self) -> List[Path]:
        """Find all documents in scan locations"""
        all_files = []
        
        for location in self.scan_locations:
            if location.exists():
                print(f"Scanning {location}...")
                for file_path in location.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.jpg', '.png', '.tiff', '.doc', '.docx']:
                        all_files.append(file_path)
        
        return all_files

    def organize_file(self, file_path: Path) -> bool:
        """Organize a single file"""
        try:
            categories = self.categorize_document(file_path)
            
            for category, subcategory in categories:
                target_dir = self.create_directory_structure(self.scan_base, category, subcategory)
                
                # Create Unprocessed subfolder for business documents
                if category == "Business":
                    target_dir = target_dir / "Unprocessed"
                    target_dir.mkdir(exist_ok=True)
                
                target_path = target_dir / file_path.name
                
                # Avoid moving to same location
                if file_path.parent == target_dir:
                    continue
                    
                # Handle duplicates
                counter = 1
                original_target = target_path
                while target_path.exists():
                    stem = original_target.stem
                    suffix = original_target.suffix
                    target_path = target_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Copy for first category, move for subsequent ones
                if categories.index((category, subcategory)) == 0:
                    shutil.move(str(file_path), str(target_path))
                    print(f"Moved: {file_path} -> {target_path}")
                else:
                    shutil.copy2(str(file_path), str(target_path))
                    print(f"Copied: {file_path} -> {target_path}")
                    
            return True
            
        except Exception as e:
            print(f"Error organizing {file_path}: {e}")
            return False

    def run_organization(self):
        """Run the complete organization process"""
        print("Starting system-wide document organization...")
        
        # Find all documents
        all_files = self.find_all_documents()
        print(f"Found {len(all_files)} documents to process")
        
        # Process each file
        organized = 0
        for file_path in all_files:
            if self.organize_file(file_path):
                organized += 1
        
        print(f"\nOrganization complete! Processed {organized} out of {len(all_files)} files")

if __name__ == "__main__":
    organizer = SystemWideOrganizer()
    organizer.run_organization()