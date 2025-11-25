#!/usr/bin/env python3
"""
Smart Renamer for Intelligent File Processor
Generates intelligent, searchable filenames based on content
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class SmartRenamer:
    """Generates smart filenames based on content and classification"""

    def __init__(self, logger: logging.Logger):
        """
        Initialize smart renamer

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def generate_name(self, original_path: str, analysis: Dict, classification: Dict) -> str:
        """
        Generate smart filename

        Args:
            original_path: Original file path
            analysis: Content analysis result
            classification: Classification result (category, confidence, metadata)

        Returns:
            New filename (without path)
        """
        path = Path(original_path)
        extension = path.suffix
        category = classification.get('category', 'unknown')
        subcategory = classification.get('subcategory')

        # Get date prefix
        date_str = self._extract_date(analysis)

        # Get descriptive name based on category
        desc = self._generate_description(path.stem, analysis, category, subcategory)

        # Clean and format
        desc = self._clean_name(desc)

        # Build final name: YYYY-MM-DD_description.ext
        new_name = f"{date_str}_{desc}{extension}"

        # Truncate if too long (max 200 chars)
        if len(new_name) > 200:
            # Keep extension and date, truncate description
            max_desc_len = 200 - len(date_str) - len(extension) - 2  # 2 for underscores
            desc = desc[:max_desc_len]
            new_name = f"{date_str}_{desc}{extension}"

        return new_name

    def _extract_date(self, analysis: Dict) -> str:
        """
        Extract or generate date for filename

        Args:
            analysis: Content analysis result

        Returns:
            Date string in YYYY-MM-DD format
        """
        # Try to find date in content
        text = analysis.get('text_content', '')

        # Look for common date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    # Try to parse the date
                    # This is simplified - production would handle all formats
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # YYYY-MM-DD format
                            year, month, day = groups
                            date = datetime(int(year), int(month), int(day))
                            return date.strftime('%Y-%m-%d')
                except (ValueError, IndexError):
                    pass

        # Fall back to file modification date
        file_date = analysis.get('modified', datetime.now())
        return file_date.strftime('%Y-%m-%d')

    def _generate_description(self, original_stem: str, analysis: Dict,
                             category: str, subcategory: Optional[str]) -> str:
        """
        Generate descriptive part of filename

        Args:
            original_stem: Original filename without extension
            analysis: Content analysis
            category: Main category
            subcategory: Subcategory if available

        Returns:
            Descriptive string
        """
        text = analysis.get('text_content', '').lower()
        metadata = analysis.get('metadata', {})

        desc_parts = []

        # Extract vendor/company name for receipts/invoices
        if subcategory in ['receipts', 'invoices']:
            vendor = self._extract_vendor(text)
            if vendor:
                desc_parts.append(vendor)
            desc_parts.append(subcategory[:-1])  # 'receipt' not 'receipts'

            # Try to extract amount
            amount = self._extract_amount(text)
            if amount:
                desc_parts.append(amount)

        # Medical documents
        elif subcategory == 'medical':
            provider = self._extract_provider(text)
            if provider:
                desc_parts.append(provider)

            doc_type = self._extract_medical_type(text)
            if doc_type:
                desc_parts.append(doc_type)

        # Contracts
        elif subcategory in ['contracts', 'legal']:
            party = self._extract_party_name(text)
            if party:
                desc_parts.append(party)
            desc_parts.append('contract' if 'contract' in text else 'legal_document')

        # Policy documents
        elif subcategory == 'policies' and category == 'campaign':
            policy_topic = self._extract_policy_topic(text)
            if policy_topic:
                desc_parts.append('policy')
                desc_parts.append(policy_topic)

        # Use metadata title if available
        if not desc_parts and metadata.get('title'):
            title = metadata['title'][:50]  # Limit length
            desc_parts.append(title)

        # Fall back to cleaned original name
        if not desc_parts:
            desc_parts.append(original_stem)

        return '_'.join(desc_parts)

    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor/company name from text"""
        # Common vendors (simplified - production would have larger list)
        vendors = [
            'amazon', 'walmart', 'target', 'costco', 'kroger',
            'att', 'verizon', 'tmobile', 'spectrum',
            'duke energy', 'lge', 'louisville gas',
            'ups', 'fedex', 'usps'
        ]

        for vendor in vendors:
            if vendor in text:
                return vendor.replace(' ', '_')

        return None

    def _extract_amount(self, text: str) -> Optional[str]:
        """Extract dollar amount from text"""
        # Look for $XX.XX pattern
        pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
        matches = re.findall(pattern, text)

        if matches:
            # Take the last/largest amount (often the total)
            amounts = [float(m.replace(',', '')) for m in matches]
            amount = max(amounts)
            return f"{amount:.2f}".replace('.', '_')

        return None

    def _extract_provider(self, text: str) -> Optional[str]:
        """Extract medical provider name"""
        providers = [
            'baptist health', 'norton healthcare', 'norton',
            'ky one', 'university of louisville',
            'anthem', 'humana', 'aetna', 'cigna'
        ]

        for provider in providers:
            if provider in text:
                return provider.replace(' ', '_')

        return None

    def _extract_medical_type(self, text: str) -> Optional[str]:
        """Extract type of medical document"""
        types = {
            'lab_results': ['lab results', 'laboratory', 'test results'],
            'prescription': ['prescription', 'medication', 'rx'],
            'visit_summary': ['visit summary', 'office visit', 'consultation'],
            'insurance_claim': ['insurance claim', 'eob', 'explanation of benefits'],
            'bill': ['patient bill', 'statement', 'amount due']
        }

        for doc_type, keywords in types.items():
            if any(kw in text for kw in keywords):
                return doc_type

        return None

    def _extract_party_name(self, text: str) -> Optional[str]:
        """Extract party name from contract"""
        # Look for "between X and Y" or "with X"
        patterns = [
            r'between\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+and',
            r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1)
                return name.replace(' ', '_').lower()

        return None

    def _extract_policy_topic(self, text: str) -> Optional[str]:
        """Extract policy topic for campaign documents"""
        topics = {
            'public_safety': ['public safety', 'police', 'fire', 'emergency'],
            'education': ['education', 'school', 'teacher', 'student'],
            'budget': ['budget', 'fiscal', 'spending', 'revenue'],
            'infrastructure': ['infrastructure', 'roads', 'transit', 'transportation'],
            'wellness': ['wellness', 'health', 'mental health', 'community center'],
            'housing': ['housing', 'affordable housing', 'homeless'],
        }

        for topic, keywords in topics.items():
            if any(kw in text for kw in keywords):
                return topic

        return None

    def _clean_name(self, name: str) -> str:
        """
        Clean filename - lowercase, underscores, no special chars

        Args:
            name: Filename to clean

        Returns:
            Cleaned filename
        """
        # Convert to lowercase
        name = name.lower()

        # Replace spaces with underscores
        name = name.replace(' ', '_')

        # Remove special characters (keep alphanumeric, underscores, hyphens, dots)
        name = re.sub(r'[^a-z0-9_\-.]', '', name)

        # Replace multiple underscores with single
        name = re.sub(r'_+', '_', name)

        # Strip leading/trailing underscores
        name = name.strip('_')

        return name


if __name__ == "__main__":
    # Test smart renamer
    import sys
    from content_analyzer import ContentAnalyzer
    from intelligent_classifier import IntelligentClassifier

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    if len(sys.argv) > 1:
        test_file = sys.argv[1]

        # Analyze and classify
        analyzer = ContentAnalyzer(logger)
        analysis = analyzer.analyze(test_file)

        classifier = IntelligentClassifier(logger)
        category, confidence, class_meta = classifier.classify(analysis)
        subcategory = classifier.suggest_subcategory(category, analysis, class_meta)

        classification = {
            'category': category,
            'confidence': confidence,
            'subcategory': subcategory,
            'metadata': class_meta
        }

        # Generate smart name
        renamer = SmartRenamer(logger)
        new_name = renamer.generate_name(test_file, analysis, classification)

        print(f"\n=== Smart Rename ===")
        print(f"Original: {Path(test_file).name}")
        print(f"New name: {new_name}")
        print(f"Category: {category} > {subcategory}")
        print(f"Confidence: {confidence}%")

    else:
        print("Usage: python smart_renamer.py <file_path>")
