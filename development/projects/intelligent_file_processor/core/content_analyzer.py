#!/usr/bin/env python3
"""
Content Analyzer for Intelligent File Processor
Extracts text and metadata from various file types
"""

import logging
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
import PyPDF2
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime


class ContentAnalyzer:
    """Analyzes file content and extracts metadata"""

    def __init__(self, logger: logging.Logger, ocr_engine=None):
        """
        Initialize content analyzer

        Args:
            logger: Logger instance
            ocr_engine: Optional OCR engine instance
        """
        self.logger = logger
        self.ocr_engine = ocr_engine

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze file and extract content/metadata

        Args:
            file_path: Path to file

        Returns:
            Dictionary with analysis results
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get basic file info
        result = {
            'path': str(path),
            'name': path.name,
            'extension': path.suffix.lower(),
            'size': path.stat().st_size,
            'mime_type': self._get_mime_type(path),
            'created': datetime.fromtimestamp(path.stat().st_ctime),
            'modified': datetime.fromtimestamp(path.stat().st_mtime),
            'text_content': '',
            'metadata': {},
            'keywords': []
        }

        # Extract content based on file type
        try:
            if result['mime_type'] and result['mime_type'].startswith('application/pdf'):
                self._analyze_pdf(path, result)
            elif result['mime_type'] and result['mime_type'].startswith('image/'):
                self._analyze_image(path, result)
            elif result['mime_type'] and result['mime_type'].startswith('text/'):
                self._analyze_text(path, result)

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            result['error'] = str(e)

        # Apply OCR if available and useful
        if self.ocr_engine and self.ocr_engine.is_available():
            result = self.ocr_engine.enhance_analysis(file_path, result)

        return result

    def _get_mime_type(self, path: Path) -> Optional[str]:
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type

    def _analyze_pdf(self, path: Path, result: Dict):
        """
        Extract text and metadata from PDF

        Args:
            path: Path to PDF file
            result: Result dictionary to update
        """
        try:
            with open(path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                # Extract metadata
                if pdf_reader.metadata:
                    result['metadata'] = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'keywords': pdf_reader.metadata.get('/Keywords', '')
                    }

                # Extract text from first 5 pages (for performance)
                text_parts = []
                max_pages = min(5, len(pdf_reader.pages))

                for i in range(max_pages):
                    try:
                        page = pdf_reader.pages[i]
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    except Exception as e:
                        self.logger.warning(f"Could not extract text from page {i}: {e}")

                result['text_content'] = '\n'.join(text_parts)
                result['page_count'] = len(pdf_reader.pages)

        except Exception as e:
            self.logger.error(f"Error analyzing PDF {path}: {e}")
            result['error'] = str(e)

    def _analyze_image(self, path: Path, result: Dict):
        """
        Extract EXIF metadata from image

        Args:
            path: Path to image file
            result: Result dictionary to update
        """
        try:
            with Image.open(path) as img:
                result['metadata']['dimensions'] = img.size
                result['metadata']['format'] = img.format
                result['metadata']['mode'] = img.mode

                # Extract EXIF data
                exif_data = img._getexif()
                if exif_data:
                    exif = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif[tag] = value

                    result['metadata']['exif'] = exif

                    # Extract common useful fields
                    if 'DateTime' in exif:
                        result['metadata']['photo_date'] = exif['DateTime']
                    if 'Make' in exif:
                        result['metadata']['camera_make'] = exif['Make']
                    if 'Model' in exif:
                        result['metadata']['camera_model'] = exif['Model']

        except Exception as e:
            self.logger.error(f"Error analyzing image {path}: {e}")
            result['error'] = str(e)

    def _analyze_text(self, path: Path, result: Dict):
        """
        Read text file content

        Args:
            path: Path to text file
            result: Result dictionary to update
        """
        try:
            # Try to detect encoding
            with open(path, 'rb') as f:
                raw_data = f.read()

            # Try UTF-8 first
            try:
                text_content = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                # Fall back to latin-1
                text_content = raw_data.decode('latin-1', errors='ignore')

            # Limit to first 10KB for performance
            if len(text_content) > 10000:
                text_content = text_content[:10000] + "\n... (truncated)"

            result['text_content'] = text_content

        except Exception as e:
            self.logger.error(f"Error analyzing text file {path}: {e}")
            result['error'] = str(e)

    def extract_keywords(self, analysis: Dict) -> list:
        """
        Extract important keywords from analysis

        Args:
            analysis: Analysis result dictionary

        Returns:
            List of keywords
        """
        keywords = []
        text_content = analysis.get('text_content', '').lower()

        # Common document type keywords
        type_keywords = {
            'invoice': ['invoice', 'bill', 'payment due', 'amount due'],
            'receipt': ['receipt', 'purchased', 'total paid', 'transaction'],
            'contract': ['contract', 'agreement', 'terms and conditions'],
            'policy': ['policy', 'coverage', 'terms', 'conditions'],
            'medical': ['patient', 'doctor', 'medical', 'health', 'diagnosis'],
            'financial': ['balance', 'statement', 'account', 'transaction'],
            'legal': ['hereby', 'whereas', 'party', 'agreement']
        }

        for doc_type, keywords_list in type_keywords.items():
            if any(kw in text_content for kw in keywords_list):
                keywords.append(doc_type)

        # Check metadata
        metadata = analysis.get('metadata', {})
        if 'title' in metadata and metadata['title']:
            keywords.append('has_title')
        if 'author' in metadata and metadata['author']:
            keywords.append('has_author')

        return keywords


if __name__ == "__main__":
    # Test content analyzer
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    analyzer = ContentAnalyzer(logger)

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"\nAnalyzing: {test_file}\n")

        result = analyzer.analyze(test_file)

        print("Results:")
        print(f"  Name: {result['name']}")
        print(f"  Type: {result['mime_type']}")
        print(f"  Size: {result['size']} bytes")
        print(f"  Extension: {result['extension']}")

        if result.get('metadata'):
            print(f"\n  Metadata:")
            for key, value in result['metadata'].items():
                if key != 'exif':  # Skip detailed EXIF for brevity
                    print(f"    {key}: {value}")

        if result.get('text_content'):
            preview = result['text_content'][:200]
            print(f"\n  Text Preview: {preview}...")

        keywords = analyzer.extract_keywords(result)
        if keywords:
            print(f"\n  Keywords: {', '.join(keywords)}")

    else:
        print("Usage: python content_analyzer.py <file_path>")
