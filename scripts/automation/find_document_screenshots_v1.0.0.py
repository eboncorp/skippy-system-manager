#!/usr/bin/env python3
"""
Document Screenshot Detection Script
Scans Google Photos for images that appear to be screenshots of documents
"""

import os
import sys
import json
import subprocess
from PIL import Image, ImageStat
from PIL.ExifTags import TAGS
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentScreenshotDetector:
    def __init__(self, output_dir="/home/dave/DocumentScreenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        self.detected_dir = self.output_dir / "detected"
        self.text_heavy_dir = self.output_dir / "text_heavy"
        self.report_dir = self.output_dir / "reports"

        for d in [self.detected_dir, self.text_heavy_dir, self.report_dir]:
            d.mkdir(exist_ok=True)

    def analyze_image_metadata(self, image_path):
        """Extract metadata from image"""
        try:
            with Image.open(image_path) as img:
                # Basic image info
                info = {
                    'filename': os.path.basename(image_path),
                    'size': img.size,
                    'format': img.format,
                    'mode': img.mode,
                    'aspect_ratio': img.size[0] / img.size[1] if img.size[1] > 0 else 0
                }

                # Extract EXIF data
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = str(value)

                info['exif'] = exif_data
                return info
        except Exception as e:
            logger.error(f"Error analyzing {image_path}: {e}")
            return None

    def detect_screenshot_characteristics(self, image_path):
        """Detect if image has screenshot characteristics"""
        try:
            with Image.open(image_path) as img:
                info = self.analyze_image_metadata(image_path)
                if not info:
                    return False, "Could not analyze image"

                reasons = []
                score = 0

                # Check aspect ratio (many screenshots are 16:9, 4:3, or phone ratios)
                aspect_ratio = info['aspect_ratio']
                if 1.7 <= aspect_ratio <= 1.8:  # ~16:9
                    score += 2
                    reasons.append("16:9 aspect ratio (common for screen captures)")
                elif 1.3 <= aspect_ratio <= 1.4:  # ~4:3
                    score += 1
                    reasons.append("4:3 aspect ratio")
                elif 0.5 <= aspect_ratio <= 0.6:  # Phone screenshot
                    score += 2
                    reasons.append("Phone screenshot aspect ratio")

                # Check for common screenshot sizes
                width, height = info['size']
                common_screenshot_widths = [1920, 1366, 1440, 1280, 1080, 390, 428, 375]
                if width in common_screenshot_widths or height in common_screenshot_widths:
                    score += 1
                    reasons.append("Common screenshot dimensions")

                # Check if image is PNG (common for screenshots)
                if info['format'] == 'PNG':
                    score += 1
                    reasons.append("PNG format (common for screenshots)")

                # Check EXIF data for screenshot indicators
                exif = info.get('exif', {})
                if 'Software' in exif:
                    software = exif['Software'].lower()
                    screenshot_keywords = ['screenshot', 'snipping', 'grab', 'capture', 'screen']
                    if any(keyword in software for keyword in screenshot_keywords):
                        score += 3
                        reasons.append(f"Screenshot software detected: {exif['Software']}")

                # Check for lack of camera EXIF data (screenshots usually don't have camera info)
                camera_tags = ['Make', 'Model', 'Flash', 'FocalLength', 'ISOSpeedRatings']
                has_camera_data = any(tag in exif for tag in camera_tags)
                if not has_camera_data and len(exif) > 0:
                    score += 1
                    reasons.append("No camera metadata (typical of screenshots)")

                return score >= 3, reasons

        except Exception as e:
            logger.error(f"Error detecting screenshot characteristics in {image_path}: {e}")
            return False, [f"Error: {e}"]

    def detect_text_heavy_image(self, image_path):
        """Detect if image contains a lot of text (document-like)"""
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale for analysis
                gray = img.convert('L')

                # Calculate image statistics
                stat = ImageStat.Stat(gray)

                reasons = []
                score = 0

                # Check for high contrast (text typically has high contrast)
                std_dev = stat.stddev[0]
                if std_dev > 50:  # High contrast
                    score += 2
                    reasons.append(f"High contrast detected (std dev: {std_dev:.1f})")

                # Check for predominantly white/light background
                mean_brightness = stat.mean[0]
                if mean_brightness > 200:  # Very bright/white background
                    score += 1
                    reasons.append(f"Light/white background (brightness: {mean_brightness:.1f})")

                # Simple edge detection using histogram analysis
                # Text images typically have many sharp transitions
                hist = gray.histogram()

                # Look for bimodal distribution (text vs background)
                dark_pixels = sum(hist[:100])  # Dark pixels (0-99)
                light_pixels = sum(hist[156:])  # Light pixels (156-255)
                total_pixels = img.size[0] * img.size[1]

                dark_ratio = dark_pixels / total_pixels
                light_ratio = light_pixels / total_pixels

                if dark_ratio > 0.1 and light_ratio > 0.6:  # Some dark text on light background
                    score += 2
                    reasons.append(f"Text-like distribution: {dark_ratio:.2f} dark, {light_ratio:.2f} light")

                return score >= 3, reasons

        except Exception as e:
            logger.error(f"Error detecting text characteristics in {image_path}: {e}")
            return False, [f"Error: {e}"]

    def scan_photos_directory(self, photos_dir):
        """Scan a directory of photos for document screenshots"""
        photos_path = Path(photos_dir)
        if not photos_path.exists():
            logger.error(f"Photos directory does not exist: {photos_dir}")
            return

        results = {
            'scan_date': datetime.now().isoformat(),
            'directory': str(photos_dir),
            'total_images': 0,
            'detected_screenshots': [],
            'text_heavy_images': [],
            'potential_documents': []
        }

        # Supported image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}

        # Scan all images in directory
        for image_path in photos_path.rglob('*'):
            if image_path.suffix.lower() in image_extensions:
                results['total_images'] += 1
                logger.info(f"Analyzing: {image_path.name}")

                # Check for screenshot characteristics
                is_screenshot, screenshot_reasons = self.detect_screenshot_characteristics(str(image_path))

                # Check for text-heavy characteristics
                is_text_heavy, text_reasons = self.detect_text_heavy_image(str(image_path))

                image_result = {
                    'filename': image_path.name,
                    'path': str(image_path),
                    'is_screenshot': is_screenshot,
                    'screenshot_reasons': screenshot_reasons,
                    'is_text_heavy': is_text_heavy,
                    'text_reasons': text_reasons,
                    'is_potential_document': is_screenshot and is_text_heavy
                }

                if is_screenshot:
                    results['detected_screenshots'].append(image_result)
                    logger.info(f"  📱 Screenshot detected: {', '.join(screenshot_reasons)}")

                if is_text_heavy:
                    results['text_heavy_images'].append(image_result)
                    logger.info(f"  📄 Text-heavy image: {', '.join(text_reasons)}")

                if is_screenshot and is_text_heavy:
                    results['potential_documents'].append(image_result)
                    logger.info(f"  📋 POTENTIAL DOCUMENT: {image_path.name}")

                    # Copy potential document to output directory
                    output_path = self.detected_dir / image_path.name
                    try:
                        import shutil
                        shutil.copy2(str(image_path), str(output_path))
                        logger.info(f"  ✓ Copied to: {output_path}")
                    except Exception as e:
                        logger.error(f"  ✗ Failed to copy: {e}")

        # Save results
        report_file = self.report_dir / f"document_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\n📊 SCAN RESULTS:")
        logger.info(f"  Total images analyzed: {results['total_images']}")
        logger.info(f"  Screenshots detected: {len(results['detected_screenshots'])}")
        logger.info(f"  Text-heavy images: {len(results['text_heavy_images'])}")
        logger.info(f"  Potential documents: {len(results['potential_documents'])}")
        logger.info(f"  Report saved to: {report_file}")

        return results

    def scan_google_photos_remote(self, year=None, max_files=100):
        """Download and scan Google Photos for document screenshots"""
        logger.info("Starting Google Photos scan for document screenshots...")

        # Create temporary download directory
        temp_dir = self.output_dir / "temp_download"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Determine source path
            if year:
                source_path = f"googlephotos:media/by-year/{year}"
            else:
                source_path = "googlephotos:media/by-month"

            # Download recent photos for analysis
            logger.info(f"Downloading photos from {source_path}...")
            cmd = [
                'rclone', 'copy', source_path, str(temp_dir),
                '--include', '*.{jpg,jpeg,png,webp}',
                '--max-size', '10M',
                '--transfers', '3',
                '--max-duration', '2m'
            ]

            if max_files:
                cmd.extend(['--max-transfer', str(max_files)])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"rclone failed: {result.stderr}")
                return None

            # Scan the downloaded photos
            results = self.scan_photos_directory(str(temp_dir))

            return results

        except Exception as e:
            logger.error(f"Error scanning Google Photos: {e}")
            return None
        finally:
            # Clean up temporary files
            try:
                import shutil
                shutil.rmtree(str(temp_dir))
                logger.info("Cleaned up temporary files")
            except Exception as e:
                logger.warning(f"Failed to clean up temp files: {e}")

def main():
    parser = argparse.ArgumentParser(description='Find document screenshots in Google Photos')
    parser.add_argument('--local-dir', help='Scan local directory instead of Google Photos')
    parser.add_argument('--year', type=int, help='Scan specific year from Google Photos')
    parser.add_argument('--max-files', type=int, default=100, help='Maximum files to download and analyze')
    parser.add_argument('--output', default='/home/dave/DocumentScreenshots', help='Output directory')

    args = parser.parse_args()

    detector = DocumentScreenshotDetector(args.output)

    if args.local_dir:
        results = detector.scan_photos_directory(args.local_dir)
    else:
        results = detector.scan_google_photos_remote(args.year, args.max_files)

    if results:
        print(f"\n🎯 Found {len(results['potential_documents'])} potential document screenshots!")
        if results['potential_documents']:
            print("\nPotential documents:")
            for doc in results['potential_documents']:
                print(f"  • {doc['filename']}")
                print(f"    Screenshot reasons: {', '.join(doc['screenshot_reasons'])}")
                print(f"    Text reasons: {', '.join(doc['text_reasons'])}")
                print()

if __name__ == "__main__":
    main()