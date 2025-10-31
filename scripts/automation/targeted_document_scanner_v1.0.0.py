#!/usr/bin/env python3
"""
Targeted Document Screenshot Scanner
More efficient scanning with specific search parameters and filters
"""

import os
import sys
import json
import subprocess
import argparse
import logging
from PIL import Image, ImageStat
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TargetedDocumentScanner:
    def __init__(self, output_dir="/home/dave/DocumentScreenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.detected_dir = self.output_dir / "detected"
        self.reports_dir = self.output_dir / "reports"

        for d in [self.detected_dir, self.reports_dir]:
            d.mkdir(exist_ok=True)

    def scan_google_photos_targeted(self,
                                  search_terms=None,
                                  file_types=None,
                                  date_range=None,
                                  size_range=None,
                                  max_files=50,
                                  source_path=None):
        """
        Targeted scan with specific filters
        """
        logger.info("Starting targeted Google Photos scan...")

        # Create temp directory
        temp_dir = self.output_dir / "temp_targeted"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Build rclone command with filters
            cmd = ['rclone', 'copy']

            # Determine source
            if source_path:
                source = f"googlephotos:{source_path}"
            elif date_range:
                if len(date_range) == 1:  # Single year
                    source = f"googlephotos:media/by-year/{date_range[0]}"
                elif len(date_range) == 2:  # Year and month
                    source = f"googlephotos:media/by-month/{date_range[0]}-{date_range[1]:02d}"
                else:
                    source = "googlephotos:media/all"
            else:
                source = "googlephotos:media/all"

            cmd.extend([source, str(temp_dir)])

            # Add file type filters
            if file_types:
                include_pattern = "*.{" + ",".join(file_types) + "}"
                cmd.extend(['--include', include_pattern])
            else:
                cmd.extend(['--include', '*.{jpg,jpeg,png,webp}'])

            # Add size filters
            if size_range:
                if size_range[0]:  # min size
                    cmd.extend(['--min-size', size_range[0]])
                if size_range[1]:  # max size
                    cmd.extend(['--max-size', size_range[1]])
            else:
                cmd.extend(['--max-size', '20M'])  # Default max size

            # Add transfer limits
            cmd.extend([
                '--transfers', '2',
                '--checkers', '4',
                '--max-duration', '3m'
            ])

            if max_files:
                cmd.extend(['--max-transfer', str(max_files)])

            # Add specific filters for likely screenshots
            if search_terms:
                for term in search_terms:
                    if term.lower() in ['screenshot', 'screen', 'capture']:
                        cmd.extend(['--include', f'*{term}*'])

            logger.info(f"Running: {' '.join(cmd)}")

            # Execute rclone
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.warning(f"rclone warning/error: {result.stderr}")

            # Check what was downloaded
            downloaded_files = list(temp_dir.glob('**/*'))
            image_files = [f for f in downloaded_files if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]

            logger.info(f"Downloaded {len(image_files)} images for analysis")

            if not image_files:
                logger.warning("No images downloaded. Try different parameters.")
                return None

            # Analyze downloaded images
            results = self.analyze_images_advanced(image_files, search_terms)

            return results

        except subprocess.TimeoutExpired:
            logger.error("Download timed out. Try smaller date range or fewer files.")
            return None
        except Exception as e:
            logger.error(f"Error in targeted scan: {e}")
            return None
        finally:
            # Cleanup
            try:
                import shutil
                shutil.rmtree(str(temp_dir))
                logger.info("Cleaned up temporary files")
            except Exception as e:
                logger.warning(f"Failed to clean up: {e}")

    def analyze_images_advanced(self, image_files, search_terms=None):
        """Advanced image analysis with scoring system"""
        results = {
            'scan_date': datetime.now().isoformat(),
            'total_images': len(image_files),
            'analysis_results': [],
            'high_confidence': [],
            'medium_confidence': [],
            'low_confidence': []
        }

        for image_path in image_files:
            logger.info(f"Analyzing: {image_path.name}")

            analysis = self.comprehensive_analysis(image_path, search_terms)
            results['analysis_results'].append(analysis)

            # Categorize by confidence score
            total_score = analysis['screenshot_score'] + analysis['document_score']

            if total_score >= 7:
                results['high_confidence'].append(analysis)
                self.copy_to_detected(image_path, "high_confidence")
                logger.info(f"  🎯 HIGH CONFIDENCE DOCUMENT: {image_path.name}")
            elif total_score >= 4:
                results['medium_confidence'].append(analysis)
                self.copy_to_detected(image_path, "medium_confidence")
                logger.info(f"  📄 Medium confidence: {image_path.name}")
            elif total_score >= 2:
                results['low_confidence'].append(analysis)
                logger.info(f"  📱 Low confidence: {image_path.name}")

        # Save detailed report
        report_file = self.reports_dir / f"targeted_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\n📊 TARGETED SCAN RESULTS:")
        logger.info(f"  Total analyzed: {results['total_images']}")
        logger.info(f"  High confidence: {len(results['high_confidence'])}")
        logger.info(f"  Medium confidence: {len(results['medium_confidence'])}")
        logger.info(f"  Low confidence: {len(results['low_confidence'])}")
        logger.info(f"  Report: {report_file}")

        return results

    def comprehensive_analysis(self, image_path, search_terms=None):
        """Comprehensive analysis with detailed scoring"""
        try:
            with Image.open(image_path) as img:
                analysis = {
                    'filename': image_path.name,
                    'path': str(image_path),
                    'size': img.size,
                    'format': img.format,
                    'screenshot_score': 0,
                    'document_score': 0,
                    'screenshot_reasons': [],
                    'document_reasons': [],
                    'metadata_analysis': {}
                }

                # Screenshot analysis
                analysis.update(self.analyze_screenshot_characteristics(img, image_path))

                # Document analysis
                analysis.update(self.analyze_document_characteristics(img))

                # Filename analysis
                if search_terms:
                    filename_score = self.analyze_filename(image_path.name, search_terms)
                    analysis['screenshot_score'] += filename_score['score']
                    analysis['screenshot_reasons'].extend(filename_score['reasons'])

                return analysis

        except Exception as e:
            logger.error(f"Error analyzing {image_path}: {e}")
            return {
                'filename': image_path.name,
                'error': str(e),
                'screenshot_score': 0,
                'document_score': 0
            }

    def analyze_screenshot_characteristics(self, img, image_path):
        """Detailed screenshot analysis"""
        score = 0
        reasons = []
        metadata = {}

        width, height = img.size
        aspect_ratio = width / height if height > 0 else 0

        # Aspect ratio analysis
        if 1.7 <= aspect_ratio <= 1.8:  # 16:9
            score += 3
            reasons.append("16:9 aspect ratio (common desktop)")
        elif 1.3 <= aspect_ratio <= 1.4:  # 4:3
            score += 2
            reasons.append("4:3 aspect ratio")
        elif 0.4 <= aspect_ratio <= 0.6:  # Phone portrait
            score += 3
            reasons.append("Mobile screenshot aspect ratio")
        elif 1.6 <= aspect_ratio <= 2.2:  # Phone landscape
            score += 2
            reasons.append("Mobile landscape ratio")

        # Common screenshot dimensions
        common_widths = [390, 414, 428, 375, 360, 1080, 1920, 1366, 1440, 1280]
        common_heights = [844, 896, 926, 667, 640, 1920, 1080, 768, 900, 720]

        if width in common_widths or height in common_heights:
            score += 2
            reasons.append(f"Common device dimensions ({width}x{height})")

        # Format analysis
        if img.format == 'PNG':
            score += 2
            reasons.append("PNG format (screenshot preferred)")
        elif img.format == 'WEBP':
            score += 1
            reasons.append("WebP format (modern screenshots)")

        # File size analysis (screenshots often have specific size patterns)
        file_size = image_path.stat().st_size if image_path.exists() else 0
        size_mb = file_size / (1024 * 1024)

        if 0.1 <= size_mb <= 5:  # Typical screenshot range
            score += 1
            reasons.append(f"Typical screenshot file size ({size_mb:.1f}MB)")

        # EXIF analysis
        try:
            exif_data = img._getexif() if hasattr(img, '_getexif') else None
            if exif_data:
                # Look for screenshot indicators
                software = exif_data.get(0x0131, '')  # Software tag
                if any(term in software.lower() for term in ['screenshot', 'snip', 'grab', 'capture']):
                    score += 4
                    reasons.append(f"Screenshot software: {software}")

                # Lack of camera data suggests screenshot
                camera_tags = [0x010F, 0x0110, 0x9003, 0x829A, 0x8827]  # Make, Model, DateTime, ExposureTime, ISO
                camera_data_count = sum(1 for tag in camera_tags if tag in exif_data)

                if camera_data_count == 0:
                    score += 1
                    reasons.append("No camera metadata")

                metadata['exif_tags'] = len(exif_data)
                metadata['has_camera_data'] = camera_data_count > 0
            else:
                score += 1
                reasons.append("No EXIF data (typical of screenshots)")
        except:
            pass

        return {
            'screenshot_score': score,
            'screenshot_reasons': reasons,
            'metadata_analysis': metadata
        }

    def analyze_document_characteristics(self, img):
        """Analyze if image contains document-like content"""
        score = 0
        reasons = []

        # Convert to grayscale for analysis
        gray = img.convert('L')

        # Statistical analysis
        stat = ImageStat.Stat(gray)
        mean_brightness = stat.mean[0]
        std_dev = stat.stddev[0]

        # High contrast (good for text)
        if std_dev > 60:
            score += 3
            reasons.append(f"High contrast ({std_dev:.1f})")
        elif std_dev > 40:
            score += 2
            reasons.append(f"Medium contrast ({std_dev:.1f})")

        # Bright background (typical of documents)
        if mean_brightness > 220:
            score += 2
            reasons.append(f"Very bright background ({mean_brightness:.1f})")
        elif mean_brightness > 180:
            score += 1
            reasons.append(f"Light background ({mean_brightness:.1f})")

        # Histogram analysis for text patterns
        hist = gray.histogram()
        total_pixels = img.size[0] * img.size[1]

        # Dark text pixels (0-80)
        dark_pixels = sum(hist[:81])
        dark_ratio = dark_pixels / total_pixels

        # Light background pixels (200-255)
        light_pixels = sum(hist[200:])
        light_ratio = light_pixels / total_pixels

        # Medium pixels (81-199)
        medium_pixels = sum(hist[81:200])
        medium_ratio = medium_pixels / total_pixels

        # Good text pattern: some dark, lots of light, minimal medium
        if dark_ratio > 0.05 and light_ratio > 0.6 and medium_ratio < 0.3:
            score += 3
            reasons.append(f"Text-like distribution: {dark_ratio:.2f} dark, {light_ratio:.2f} light")
        elif dark_ratio > 0.02 and light_ratio > 0.4:
            score += 1
            reasons.append(f"Possible text pattern: {dark_ratio:.2f} dark, {light_ratio:.2f} light")

        # Edge detection simulation (look for sharp transitions)
        # Count pixels with significant intensity changes
        edge_pixels = 0
        hist_diffs = [abs(hist[i+1] - hist[i]) for i in range(len(hist)-1)]
        sharp_transitions = sum(1 for diff in hist_diffs if diff > total_pixels * 0.001)

        if sharp_transitions > 50:
            score += 2
            reasons.append(f"Many sharp transitions ({sharp_transitions})")
        elif sharp_transitions > 20:
            score += 1
            reasons.append(f"Some sharp transitions ({sharp_transitions})")

        return {
            'document_score': score,
            'document_reasons': reasons
        }

    def analyze_filename(self, filename, search_terms):
        """Analyze filename for document/screenshot indicators"""
        score = 0
        reasons = []

        filename_lower = filename.lower()

        # Screenshot indicators in filename
        screenshot_terms = ['screenshot', 'screen', 'capture', 'snap', 'shot', 'grab']
        document_terms = ['doc', 'pdf', 'receipt', 'invoice', 'form', 'text', 'page']
        app_terms = ['whatsapp', 'telegram', 'signal', 'browser', 'chrome', 'safari', 'email']

        for term in screenshot_terms:
            if term in filename_lower:
                score += 2
                reasons.append(f"Screenshot term in filename: {term}")

        for term in document_terms:
            if term in filename_lower:
                score += 1
                reasons.append(f"Document term in filename: {term}")

        for term in app_terms:
            if term in filename_lower:
                score += 1
                reasons.append(f"App term in filename: {term}")

        # Date patterns (screenshots often have timestamps)
        import re
        if re.search(r'\d{4}[\-_]\d{2}[\-_]\d{2}', filename_lower):
            score += 1
            reasons.append("Date pattern in filename")

        return {'score': score, 'reasons': reasons}

    def copy_to_detected(self, image_path, confidence_level):
        """Copy detected image to organized folder"""
        try:
            confidence_dir = self.detected_dir / confidence_level
            confidence_dir.mkdir(exist_ok=True)

            import shutil
            output_path = confidence_dir / image_path.name
            shutil.copy2(str(image_path), str(output_path))

        except Exception as e:
            logger.warning(f"Failed to copy {image_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Targeted document screenshot scanner')

    # Search parameters
    parser.add_argument('--search-terms', nargs='+', help='Search terms in filenames')
    parser.add_argument('--file-types', nargs='+', default=['jpg', 'jpeg', 'png', 'webp'],
                       help='File types to include')
    parser.add_argument('--year', type=int, help='Specific year to scan')
    parser.add_argument('--month', type=int, help='Specific month (with year)')
    parser.add_argument('--min-size', help='Minimum file size (e.g., 100k)')
    parser.add_argument('--max-size', default='20M', help='Maximum file size')
    parser.add_argument('--max-files', type=int, default=50, help='Maximum files to analyze')
    parser.add_argument('--source-path', help='Custom Google Photos path')

    # Output
    parser.add_argument('--output', default='/home/dave/DocumentScreenshots', help='Output directory')

    args = parser.parse_args()

    scanner = TargetedDocumentScanner(args.output)

    # Build parameters
    date_range = None
    if args.year:
        date_range = [args.year]
        if args.month:
            date_range.append(args.month)

    size_range = [args.min_size, args.max_size]

    # Run targeted scan
    results = scanner.scan_google_photos_targeted(
        search_terms=args.search_terms,
        file_types=args.file_types,
        date_range=date_range,
        size_range=size_range,
        max_files=args.max_files,
        source_path=args.source_path
    )

    if results:
        print(f"\n🎯 TARGETED SCAN COMPLETE!")
        print(f"High confidence documents: {len(results['high_confidence'])}")
        print(f"Medium confidence: {len(results['medium_confidence'])}")
        print(f"Low confidence: {len(results['low_confidence'])}")

        if results['high_confidence']:
            print("\n🔥 High confidence documents found:")
            for doc in results['high_confidence']:
                print(f"  • {doc['filename']} (Score: {doc['screenshot_score'] + doc['document_score']})")

if __name__ == "__main__":
    main()