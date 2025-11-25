#!/usr/bin/env python3
"""
Process Existing Files - Trigger processing of files already in watched folders
"""

import sys
import time
import shutil
from pathlib import Path

# Add core directory to path
sys.path.insert(0, str(Path(__file__).parent / 'core'))

from config_loader import ConfigLoader
from content_analyzer import ContentAnalyzer
from intelligent_classifier import IntelligentClassifier
from smart_renamer import SmartRenamer
from file_organizer import FileOrganizer
import logging

# Optional Phase 2 imports
try:
    from ocr_engine import OCREngine
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from database import Database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

try:
    from ai_classifier import AIClassifier
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


def process_existing_files():
    """Process all existing files in watched folders"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    print("=" * 70)
    print(" Processing Existing Files")
    print("=" * 70)

    # Load config
    config = ConfigLoader()

    # Initialize components
    ocr_engine = None
    database = None
    ai_classifier = None

    if OCR_AVAILABLE:
        max_ocr_size = config.get('performance.max_ocr_size_mb', 50)
        ocr_engine = OCREngine(logger, max_file_size_mb=max_ocr_size)

    if DB_AVAILABLE:
        db_path = config.get('logging.database', '/home/dave/skippy/logs/file_processor.db')
        database = Database(db_path, logger)

    if AI_AVAILABLE and config.is_ai_enabled():
        ai_classifier = AIClassifier(logger, enabled=True)

    analyzer = ContentAnalyzer(logger, ocr_engine=ocr_engine)
    classifier = IntelligentClassifier(logger, min_confidence=config.get_min_confidence())
    renamer = SmartRenamer(logger)
    organizer = FileOrganizer(config, logger)

    # Get watch folders
    watch_folders = config.get_watch_folders()

    # Scan for files
    files_to_process = []
    ignore_patterns = config.get_ignore_patterns()

    for folder_config in watch_folders:
        folder_path = Path(folder_config['path'])
        if not folder_path.exists():
            continue

        print(f"\nScanning: {folder_path}")

        # Get all files (not directories, not hidden, not in ignore patterns)
        for item in folder_path.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                # Skip if matches ignore pattern
                skip = False
                for pattern in ignore_patterns:
                    if pattern in str(item):
                        skip = True
                        break

                if not skip:
                    files_to_process.append(item)

    if not files_to_process:
        print("\nNo files found to process.")
        return

    print(f"\nFound {len(files_to_process)} files to process")
    print("\nProcessing files...\n")

    processed = 0
    failed = 0

    for file_path in files_to_process:
        try:
            print(f"[{processed + failed + 1}/{len(files_to_process)}] {file_path.name}")

            # Analyze
            analysis = analyzer.analyze(str(file_path))

            # Classify
            category, confidence, class_meta = classifier.classify(analysis)

            # Try AI if available
            if ai_classifier and ai_classifier.is_available():
                ai_category, ai_confidence, ai_meta = ai_classifier.classify(
                    analysis,
                    rule_based_result=(category, confidence, class_meta)
                )
                if ai_category and ai_confidence and ai_confidence > confidence:
                    category = ai_category
                    confidence = ai_confidence
                    class_meta = ai_meta

            subcategory = classifier.suggest_subcategory(category, analysis, class_meta)

            print(f"  → {category}/{subcategory or 'none'} ({confidence}%)")

            # Check quarantine
            if classifier.should_quarantine(confidence):
                print(f"  ⚠️  Low confidence - quarantining")
                organizer.quarantine(str(file_path), reason=f"Low confidence ({confidence}%)")
                if database:
                    database.log_quarantine(
                        str(file_path),
                        f"Low confidence ({confidence}%)",
                        {'category': category, 'subcategory': subcategory, 'confidence': confidence}
                    )
                continue

            # Generate name
            classification = {
                'category': category,
                'confidence': confidence,
                'subcategory': subcategory,
                'metadata': class_meta
            }
            new_filename = renamer.generate_name(str(file_path), analysis, classification)

            # Organize
            result = organizer.organize(str(file_path), category, subcategory, new_filename)

            if result['success']:
                print(f"  ✅ → {result['destination']}")
                processed += 1

                # Log to database
                if database:
                    database.log_processed_file(
                        str(file_path),
                        result,
                        analysis,
                        {
                            'category': category,
                            'subcategory': subcategory,
                            'confidence': confidence,
                            'method': class_meta.get('method'),
                            'patterns': class_meta.get('patterns', [])
                        }
                    )
            else:
                print(f"  ❌ Error: {result.get('error')}")
                failed += 1

                if database:
                    database.log_error(str(file_path), result.get('error', 'Unknown error'))

        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1
            if database:
                database.log_error(str(file_path), str(e))

    print("\n" + "=" * 70)
    print(f" Complete: {processed} processed, {failed} failed")
    print("=" * 70)


if __name__ == '__main__':
    process_existing_files()
