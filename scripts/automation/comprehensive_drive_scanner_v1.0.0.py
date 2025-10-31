#!/usr/bin/env python3
"""
Comprehensive Drive Scanner
Scans all local and cloud drives for documents and organizes them
"""

import os
import shutil
from pathlib import Path
import PyPDF2
import re
from typing import List, Dict, Tuple
from datetime import datetime

class ComprehensiveDriveScanner:
    def __init__(self):
        self.home = Path.home()
        self.scan_base = self.home / "Scans"
        
        # All locations to scan including cloud drives
        self.scan_locations = [
            # Local directories
            self.home / "Documents",
            self.home / "Downloads", 
            self.home / "Desktop",
            self.home / "Pictures",
            self.home / "Scans",
            # Cloud drives
            self.home / "OneDrive",
            self.home / "Dropbox",
            self.home / "GoogleDrive"
        ]
        
        # File types to scan
        self.file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                                '.jpg', '.jpeg', '.png', '.tiff', '.txt']
        
        # Document categories
        self.categories = {
            "Business": {
                "Run Dave Run LLC": ["run dave run", "rdr", "dave run", "rundaverun"],
                "Pennybrooke": ["pennybrooke", "penny brooke"],
                "PaperWerk Services": ["paperwerk", "paper werk"],
                "Decibel Customs": ["decibel", "customs", "audio"],
                "GTI": ["gti", "greater than i"],
                "Ebon Corp": ["ebon", "corp"],
                "General": ["llc", "business", "registration", "ein", "tax id", "budget", "invoice"]
            },
            "Personal": {
                "Medical": ["medical", "health", "doctor", "svs vision", "eye", "prescription", "hospital"],
                "Legal": ["will", "testament", "legal", "attorney", "court", "agreement", "contract"],
                "Property": ["mortgage", "deed", "property", "real estate", "title", "roofing"],
                "Education": ["student", "loan", "university", "college", "degree", "school"],
                "Tax": ["1099", "tax", "irs", "w-2", "w2", "income", "return", "form 1120"],
                "Financial": ["bank", "credit", "loan", "payment", "bill"],
                "Automotive": ["vehicle", "car", "auto", "registration", "insurance"],
                "Identification": ["driver", "license", "passport", "birth certificate", "ccdw"]
            }
        }
        
        self.scan_results = {
            "total_files": 0,
            "documents_found": 0,
            "by_location": {},
            "by_category": {},
            "duplicates": [],
            "large_files": []
        }

    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from various file types"""
        try:
            if file_path.suffix.lower() == '.pdf':
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages[:5]:  # Check first 5 pages
                        text += page.extract_text() + "\n"
                    return text.lower()
            elif file_path.suffix.lower() in ['.txt']:
                with open(file_path, 'r', errors='ignore') as file:
                    return file.read().lower()
            else:
                return file_path.name.lower()
        except Exception as e:
            return file_path.name.lower()

    def categorize_document(self, file_path: Path) -> List[Tuple[str, str]]:
        """Categorize document based on content and filename"""
        categories = []
        content = self.extract_text_from_file(file_path)
        
        # Check business categories
        for business, keywords in self.categories["Business"].items():
            if any(keyword in content for keyword in keywords):
                categories.append(("Business", business))
        
        # Check personal categories  
        for category, keywords in self.categories["Personal"].items():
            if any(keyword in content for keyword in keywords):
                categories.append(("Personal", category))
        
        # Default fallback
        if not categories:
            if "business" in content or "llc" in content or "corp" in content:
                categories.append(("Business", "General"))
            else:
                categories.append(("Personal", "Other"))
            
        return categories

    def scan_location(self, location: Path) -> Dict:
        """Scan a specific location for documents"""
        location_stats = {
            "total_files": 0,
            "documents": [],
            "categories": {}
        }
        
        if not location.exists():
            return location_stats
        
        print(f"\nScanning {location}...")
        
        try:
            for file_path in location.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.file_extensions:
                    location_stats["total_files"] += 1
                    self.scan_results["total_files"] += 1
                    
                    # Get file info
                    file_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                        "categories": self.categorize_document(file_path)
                    }
                    
                    # Track large files (>10MB)
                    if file_info["size"] > 10_000_000:
                        self.scan_results["large_files"].append(file_info)
                    
                    location_stats["documents"].append(file_info)
                    
                    # Count by category
                    for cat_type, cat_name in file_info["categories"]:
                        key = f"{cat_type}/{cat_name}"
                        if key not in location_stats["categories"]:
                            location_stats["categories"][key] = 0
                        location_stats["categories"][key] += 1
                        
                        if key not in self.scan_results["by_category"]:
                            self.scan_results["by_category"][key] = 0
                        self.scan_results["by_category"][key] += 1
        
        except PermissionError as e:
            print(f"  Permission denied: {location}")
        except Exception as e:
            print(f"  Error scanning {location}: {e}")
        
        return location_stats

    def find_duplicates(self, all_documents: List[Dict]) -> List[Tuple[str, str]]:
        """Find potential duplicate files based on name and size"""
        duplicates = []
        seen = {}
        
        for doc in all_documents:
            key = (doc["name"], doc["size"])
            if key in seen:
                duplicates.append((seen[key], doc["path"]))
            else:
                seen[key] = doc["path"]
        
        return duplicates

    def generate_report(self):
        """Generate comprehensive scan report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE DRIVE SCAN REPORT")
        report.append("=" * 80)
        report.append(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Overall statistics
        report.append("OVERALL STATISTICS:")
        report.append(f"  Total files scanned: {self.scan_results['total_files']}")
        report.append(f"  Total locations: {len(self.scan_locations)}")
        report.append("")
        
        # By location breakdown
        report.append("FILES BY LOCATION:")
        for location, stats in self.scan_results["by_location"].items():
            report.append(f"\n  {location}:")
            report.append(f"    Files found: {stats['total_files']}")
            if stats['categories']:
                report.append("    Categories:")
                for cat, count in sorted(stats['categories'].items()):
                    report.append(f"      {cat}: {count}")
        
        # Category summary
        report.append("\n" + "=" * 40)
        report.append("DOCUMENT CATEGORIES SUMMARY:")
        for category, count in sorted(self.scan_results["by_category"].items()):
            report.append(f"  {category}: {count} documents")
        
        # Large files
        if self.scan_results["large_files"]:
            report.append("\n" + "=" * 40)
            report.append("LARGE FILES (>10MB):")
            for file in sorted(self.scan_results["large_files"], key=lambda x: x["size"], reverse=True)[:10]:
                size_mb = file["size"] / 1_000_000
                report.append(f"  {file['name']}: {size_mb:.1f}MB")
                report.append(f"    Location: {Path(file['path']).parent}")
        
        # Duplicates
        if self.scan_results["duplicates"]:
            report.append("\n" + "=" * 40)
            report.append("POTENTIAL DUPLICATES:")
            for file1, file2 in self.scan_results["duplicates"][:20]:
                report.append(f"  {Path(file1).name}")
                report.append(f"    Location 1: {Path(file1).parent}")
                report.append(f"    Location 2: {Path(file2).parent}")
        
        # Recommendations
        report.append("\n" + "=" * 40)
        report.append("RECOMMENDATIONS:")
        
        if self.scan_results["duplicates"]:
            report.append(f"  • Found {len(self.scan_results['duplicates'])} potential duplicate files")
        
        unorganized = self.scan_results["by_category"].get("Personal/Other", 0)
        if unorganized > 10:
            report.append(f"  • {unorganized} documents need proper categorization")
        
        if self.scan_results["large_files"]:
            report.append(f"  • {len(self.scan_results['large_files'])} large files could be archived")
        
        return "\n".join(report)

    def run_comprehensive_scan(self):
        """Run the complete comprehensive scan"""
        print("Starting comprehensive drive scan...")
        print("This includes local storage and cloud drives (OneDrive, Dropbox, Google Drive)")
        
        all_documents = []
        
        # Scan each location
        for location in self.scan_locations:
            stats = self.scan_location(location)
            self.scan_results["by_location"][str(location)] = stats
            all_documents.extend(stats["documents"])
        
        # Find duplicates
        self.scan_results["duplicates"] = self.find_duplicates(all_documents)
        self.scan_results["documents_found"] = len(all_documents)
        
        # Generate and save report
        report = self.generate_report()
        
        # Save report to file
        report_path = self.home / "drive_scan_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print("\n" + report)
        print(f"\n\nReport saved to: {report_path}")
        
        return self.scan_results

if __name__ == "__main__":
    scanner = ComprehensiveDriveScanner()
    scanner.run_comprehensive_scan()