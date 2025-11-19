#!/usr/bin/env python3
"""
OCR Engine for Intelligent File Processor
Extracts text from images and scanned PDFs using Tesseract
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import tempfile
from PIL import Image


class OCREngine:
    """Performs OCR on images and scanned PDFs"""

    def __init__(self, logger: logging.Logger, max_file_size_mb: int = 50):
        """
        Initialize OCR engine

        Args:
            logger: Logger instance
            max_file_size_mb: Maximum file size to OCR (in MB)
        """
        self.logger = logger
        self.max_file_size_mb = max_file_size_mb
        self.tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is installed"""
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.logger.debug("Tesseract OCR is available")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        self.logger.warning("Tesseract OCR not available - OCR will be skipped")
        return False

    def is_available(self) -> bool:
        """Check if OCR is available"""
        return self.tesseract_available

    def _auto_rotate_image(self, image: Image.Image) -> Image.Image:
        """
        Auto-rotate image to correct orientation using OSD (Orientation and Script Detection)

        Args:
            image: PIL Image object

        Returns:
            Rotated image
        """
        try:
            import pytesseract
            # Get orientation info
            osd = pytesseract.image_to_osd(image)
            rotation = int([line for line in osd.split('\n') if 'Rotate:' in line][0].split(':')[1].strip())

            if rotation != 0:
                self.logger.debug(f"Auto-rotating image by {rotation} degrees")
                return image.rotate(rotation, expand=True)
        except Exception as e:
            self.logger.debug(f"Could not auto-rotate: {e}")

        return image

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from image file with auto-rotation

        Args:
            image_path: Path to image file

        Returns:
            Extracted text or None if failed
        """
        if not self.tesseract_available:
            return None

        path = Path(image_path)

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            self.logger.warning(f"Image too large for OCR ({file_size_mb:.1f}MB > {self.max_file_size_mb}MB)")
            return None

        try:
            # Use pytesseract if available, otherwise call tesseract directly
            try:
                import pytesseract
                img = Image.open(path)
                # Try auto-rotation first
                img = self._auto_rotate_image(img)
                text = pytesseract.image_to_string(img)
                return text.strip()
            except ImportError:
                # Fall back to calling tesseract command directly with auto-rotation
                result = subprocess.run(
                    ['tesseract', str(path), 'stdout', '--psm', '1'],  # PSM 1 enables OSD
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    self.logger.error(f"Tesseract error: {result.stderr}")
                    return None

        except Exception as e:
            self.logger.error(f"OCR error for {image_path}: {e}")
            return None

    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 10) -> Optional[str]:
        """
        Extract text from scanned PDF using OCR

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to OCR (for performance)

        Returns:
            Extracted text or None if failed
        """
        if not self.tesseract_available:
            return None

        path = Path(pdf_path)

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            self.logger.warning(f"PDF too large for OCR ({file_size_mb:.1f}MB > {self.max_file_size_mb}MB)")
            return None

        try:
            # Try using pdf2image if available
            try:
                from pdf2image import convert_from_path
                import pytesseract

                # Convert PDF to images
                self.logger.debug(f"Converting PDF to images for OCR (max {max_pages} pages)...")
                images = convert_from_path(str(path), first_page=1, last_page=max_pages)

                # OCR each page with auto-rotation
                text_parts = []
                for i, image in enumerate(images):
                    self.logger.debug(f"  OCR page {i+1}/{len(images)}...")
                    # Auto-rotate before OCR
                    rotated_image = self._auto_rotate_image(image)
                    text = pytesseract.image_to_string(rotated_image)
                    if text.strip():
                        text_parts.append(text)

                return '\n\n'.join(text_parts)

            except ImportError:
                self.logger.warning("pdf2image not available - PDF OCR requires: pip install pdf2image")
                return None

        except Exception as e:
            self.logger.error(f"PDF OCR error for {pdf_path}: {e}")
            return None

    def enhance_analysis(self, file_path: str, current_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance existing analysis with OCR results

        Args:
            file_path: Path to file
            current_analysis: Existing analysis dict

        Returns:
            Enhanced analysis dict
        """
        if not self.tesseract_available:
            current_analysis['ocr_available'] = False
            return current_analysis

        mime_type = current_analysis.get('mime_type', '')
        extension = current_analysis.get('extension', '').lower()

        ocr_text = None

        # Try OCR for images
        if mime_type and mime_type.startswith('image/'):
            self.logger.info("Running OCR on image...")
            ocr_text = self.extract_text_from_image(file_path)

        # Try OCR for PDFs if no text was extracted
        elif extension == '.pdf' and not current_analysis.get('text_content'):
            self.logger.info("PDF has no text - trying OCR...")
            ocr_text = self.extract_text_from_pdf(file_path)

        if ocr_text:
            # Append OCR text to existing content
            existing_text = current_analysis.get('text_content', '')
            current_analysis['text_content'] = f"{existing_text}\n\n[OCR Text]\n{ocr_text}"
            current_analysis['ocr_performed'] = True
            current_analysis['ocr_char_count'] = len(ocr_text)
            self.logger.info(f"OCR extracted {len(ocr_text)} characters")
        else:
            current_analysis['ocr_performed'] = False

        return current_analysis


# Standalone installation check
def check_dependencies():
    """Check if OCR dependencies are installed"""
    print("Checking OCR dependencies...\n")

    # Check Tesseract
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract: {version}")
        else:
            print("❌ Tesseract: Error running")
    except FileNotFoundError:
        print("❌ Tesseract: Not installed")
        print("   Install: sudo apt install tesseract-ocr tesseract-ocr-eng")

    # Check pytesseract
    try:
        import pytesseract
        print("✅ pytesseract: Installed")
    except ImportError:
        print("⚠️  pytesseract: Not installed (optional)")
        print("   Install: pip install pytesseract")

    # Check pdf2image
    try:
        import pdf2image
        print("✅ pdf2image: Installed")
    except ImportError:
        print("⚠️  pdf2image: Not installed (optional - needed for PDF OCR)")
        print("   Install: pip install pdf2image")
        print("   Also requires: sudo apt install poppler-utils")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check_dependencies()
    else:
        # Test OCR
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )
        logger = logging.getLogger(__name__)

        ocr = OCREngine(logger)

        if ocr.is_available():
            print("✅ OCR is available and ready")
            if len(sys.argv) > 1:
                test_file = sys.argv[1]
                print(f"\nTesting OCR on: {test_file}\n")

                if test_file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.bmp')):
                    text = ocr.extract_text_from_image(test_file)
                elif test_file.lower().endswith('.pdf'):
                    text = ocr.extract_text_from_pdf(test_file)
                else:
                    print("Unsupported file type")
                    sys.exit(1)

                if text:
                    print("Extracted text:")
                    print("-" * 60)
                    print(text[:500])  # First 500 chars
                    if len(text) > 500:
                        print(f"\n... ({len(text)} total characters)")
                else:
                    print("No text extracted")
            else:
                print("\nUsage:")
                print("  python ocr_engine.py <image_or_pdf_file>")
                print("  python ocr_engine.py --check  # Check dependencies")
        else:
            print("❌ OCR not available")
            print("\nRun with --check to see what's missing:")
            print("  python ocr_engine.py --check")
