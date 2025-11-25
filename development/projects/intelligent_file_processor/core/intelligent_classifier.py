#!/usr/bin/env python3
"""
Intelligent Classifier for Intelligent File Processor
Classifies files based on content analysis using rules and patterns
"""

import logging
import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta


class IntelligentClassifier:
    """Classifies files based on content and metadata"""

    def __init__(self, logger: logging.Logger, min_confidence: int = 75):
        """
        Initialize classifier

        Args:
            logger: Logger instance
            min_confidence: Minimum confidence threshold (0-100)
        """
        self.logger = logger
        self.min_confidence = min_confidence

        # Classification rules (pattern: category, confidence boost)
        self.rules = self._build_rules()

    def _build_rules(self) -> Dict[str, list]:
        """Build classification rules"""
        return {
            'campaign': [
                # RunDaveRun campaign materials
                (['dave biggers', 'rundaverun', 'louisville metro council',
                  'policy proposal', 'campaign'], 95),
                (['@rundaverun.org', 'campaign@'], 90),
                (['policy', 'platform', 'endorsement'], 70),
            ],
            'business': [
                # Business documents
                (['eboncorp', 'ebon corp', 'llc'], 90),
                (['invoice', 'bill', 'payment due'], 85),
                (['contract', 'agreement', 'terms and conditions'], 85),
                (['receipt', 'purchased', 'order confirmation'], 80),
                (['proposal', 'quote', 'estimate'], 75),
            ],
            'personal_medical': [
                # Medical documents
                (['patient', 'diagnosis', 'treatment', 'prescription'], 90),
                (['doctor', 'physician', 'clinic', 'hospital'], 85),
                (['lab results', 'test results', 'medical record'], 90),
                (['insurance claim', 'explanation of benefits', 'eob'], 85),
                (['baptist health', 'norton healthcare', 'anthem'], 80),
            ],
            'personal_financial': [
                # Financial documents
                (['bank statement', 'account balance', 'transaction history'], 90),
                (['credit card', 'visa', 'mastercard', 'discover'], 85),
                (['investment', '401k', 'retirement', 'portfolio'], 85),
                (['tax return', 'w-2', '1099', 'irs'], 90),
                (['chase', 'fifth third', 'wells fargo'], 75),
            ],
            'personal_legal': [
                # Legal documents
                (['deed', 'title', 'lease', 'rental agreement'], 90),
                (['will', 'testament', 'estate', 'power of attorney'], 95),
                (['hereby', 'whereas', 'witnesseth'], 85),
                (['notary', 'notarized', 'sworn'], 80),
            ],
            'technical': [
                # Technical/code files
                (['function', 'class', 'import', 'def ', 'const '], 90),
                (['#!/usr/bin', '#!/bin/', 'import sys'], 95),
                (['configuration', 'config', 'settings'], 75),
            ]
        }

    def classify(self, analysis: Dict[str, Any]) -> Tuple[str, int, Dict]:
        """
        Classify file based on content analysis

        Args:
            analysis: Content analysis result

        Returns:
            Tuple of (category, confidence, metadata)
        """
        # Extract useful data
        text = analysis.get('text_content', '').lower()
        filename = analysis.get('name', '').lower()
        extension = analysis.get('extension', '').lower()
        metadata = analysis.get('metadata', {})

        # Combined searchable text
        searchable = f"{text} {filename} {' '.join(str(v) for v in metadata.values())}"

        # Score each category
        scores = {}
        matched_patterns = {}

        for category, rules in self.rules.items():
            score = 0
            patterns = []

            for keywords, confidence_boost in rules:
                # Check if any keyword matches
                for keyword in keywords:
                    if keyword in searchable:
                        score += confidence_boost
                        patterns.append(keyword)
                        break  # Only count first match per rule

            scores[category] = score
            matched_patterns[category] = patterns

        # Find best match
        if not scores or max(scores.values()) == 0:
            # No matches - check file extension
            category, confidence = self._classify_by_extension(extension)
            return category, confidence, {'method': 'extension', 'patterns': []}

        best_category = max(scores, key=scores.get)
        raw_score = scores[best_category]

        # Normalize confidence to 0-100 scale
        # Max realistic score is ~300 (multiple high-confidence matches)
        confidence = min(100, int((raw_score / 300) * 100))

        # Boost confidence if filename also matches
        if any(pattern in filename for pattern in matched_patterns[best_category]):
            confidence = min(100, confidence + 10)

        # Boost if multiple different patterns matched
        if len(matched_patterns[best_category]) >= 3:
            confidence = min(100, confidence + 10)

        result_metadata = {
            'method': 'content_analysis',
            'patterns': matched_patterns[best_category],
            'all_scores': scores
        }

        # Split personal_* categories into main category and subcategory
        if '_' in best_category:
            main, sub = best_category.split('_', 1)
            result_metadata['subcategory'] = sub
            best_category = main

        return best_category, confidence, result_metadata

    def _classify_by_extension(self, extension: str) -> Tuple[str, int]:
        """
        Classify based on file extension

        Args:
            extension: File extension (with dot)

        Returns:
            Tuple of (category, confidence)
        """
        # Extension-based classification
        extension_map = {
            '.sh': ('technical', 70),
            '.py': ('technical', 70),
            '.js': ('technical', 70),
            '.json': ('technical', 60),
            '.yaml': ('technical', 60),
            '.yml': ('technical', 60),
            '.md': ('technical', 50),
            '.txt': ('personal', 30),
            '.jpg': ('media', 60),
            '.jpeg': ('media', 60),
            '.png': ('media', 60),
            '.gif': ('media', 60),
            '.mp4': ('media', 70),
            '.mp3': ('media', 70),
            '.pdf': ('personal', 40),  # Too generic
            '.docx': ('personal', 40),
            '.doc': ('personal', 40),
        }

        if extension in extension_map:
            return extension_map[extension]

        return 'unknown', 30

    def should_quarantine(self, confidence: int) -> bool:
        """
        Check if file should be quarantined based on confidence

        Args:
            confidence: Classification confidence (0-100)

        Returns:
            True if should quarantine
        """
        return confidence < self.min_confidence

    def suggest_subcategory(self, category: str, analysis: Dict, classification: Dict) -> Optional[str]:
        """
        Suggest subcategory within main category

        Args:
            category: Main category
            analysis: Content analysis
            classification: Classification result

        Returns:
            Suggested subcategory or None
        """
        # Check if already in metadata
        if 'subcategory' in classification:
            return classification['subcategory']

        text = analysis.get('text_content', '').lower()

        # Business subcategories
        if category == 'business':
            if any(kw in text for kw in ['invoice', 'bill']):
                return 'invoices'
            elif any(kw in text for kw in ['receipt', 'purchase']):
                return 'receipts'
            elif any(kw in text for kw in ['contract', 'agreement']):
                return 'contracts'
            elif any(kw in text for kw in ['financial', 'statement']):
                return 'financial'
            else:
                return 'correspondence'

        # Personal subcategories
        elif category == 'personal':
            # Already handled by personal_medical, personal_financial, personal_legal
            if any(kw in text for kw in ['medical', 'health', 'patient']):
                return 'medical'
            elif any(kw in text for kw in ['bank', 'account', 'financial']):
                return 'financial'
            elif any(kw in text for kw in ['legal', 'contract', 'deed']):
                return 'legal'
            elif any(kw in text for kw in ['tax', '1099', 'w-2']):
                return 'taxes'
            elif any(kw in text for kw in ['receipt', 'purchase']):
                return 'receipts'
            else:
                return 'misc'

        # Campaign subcategories
        elif category == 'campaign':
            if any(kw in text for kw in ['policy', 'proposal']):
                return 'policies'
            elif any(kw in text for kw in ['press', 'release', 'announcement']):
                return 'press_releases'
            elif any(kw in text for kw in ['media', 'photo', 'video']):
                return 'media_assets'
            elif any(kw in text for kw in ['financial', 'donation', 'contribution']):
                return 'financial_reports'
            else:
                return 'correspondence'

        # Technical subcategories
        elif category == 'technical':
            ext = analysis.get('extension', '').lower()
            if ext in ['.sh', '.py', '.js', '.rb']:
                return 'scripts'
            elif ext in ['.md', '.txt', '.pdf']:
                return 'documentation'
            elif ext in ['.json', '.yaml', '.yml', '.conf', '.cfg']:
                return 'configs'
            else:
                return 'misc'

        return None


if __name__ == "__main__":
    # Test classifier
    import sys
    from content_analyzer import ContentAnalyzer

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    if len(sys.argv) > 1:
        test_file = sys.argv[1]

        # Analyze file
        analyzer = ContentAnalyzer(logger)
        analysis = analyzer.analyze(test_file)

        # Classify
        classifier = IntelligentClassifier(logger, min_confidence=75)
        category, confidence, metadata = classifier.classify(analysis)

        print(f"\n=== Classification Results ===")
        print(f"File: {analysis['name']}")
        print(f"Category: {category}")
        print(f"Confidence: {confidence}%")
        print(f"Subcategory: {classifier.suggest_subcategory(category, analysis, metadata)}")
        print(f"Method: {metadata['method']}")

        if metadata.get('patterns'):
            print(f"Matched patterns: {', '.join(metadata['patterns'])}")

        if classifier.should_quarantine(confidence):
            print(f"\n⚠️  Low confidence - would quarantine for review")
        else:
            print(f"\n✅ Confident classification - would auto-organize")

    else:
        print("Usage: python intelligent_classifier.py <file_path>")
