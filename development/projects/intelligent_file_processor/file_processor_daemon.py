#!/usr/bin/env python3
"""
Intelligent File Processor Daemon
Main entry point - watches folders and processes files automatically
"""

import sys
import time
import logging
from logging.handlers import RotatingFileHandler
import argparse
from pathlib import Path
import subprocess

# Add core directory to path
sys.path.insert(0, str(Path(__file__).parent / 'core'))

from config_loader import ConfigLoader
from file_watcher import FileWatcher
from content_analyzer import ContentAnalyzer
from intelligent_classifier import IntelligentClassifier
from smart_renamer import SmartRenamer
from file_organizer import FileOrganizer

# Phase 2 imports (optional - graceful degradation)
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
    from core.ai_classifier import AIClassifier
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class FileProcessorDaemon:
    """Main daemon that coordinates all components"""

    def __init__(self, config_path: str = None):
        """
        Initialize daemon

        Args:
            config_path: Path to configuration file
        """
        # Setup basic logging (console only)
        self.setup_logging()

        # Load configuration
        self.config = ConfigLoader(config_path)
        self.logger.info("Configuration loaded successfully")

        # Configure file logging based on config
        self.configure_file_logging()

        # Initialize Phase 2 components (optional)
        self.ocr_engine = None
        self.database = None
        self.ai_classifier = None

        if OCR_AVAILABLE:
            max_ocr_size = self.config.get('performance.max_ocr_size_mb', 50)
            self.ocr_engine = OCREngine(self.logger, max_file_size_mb=max_ocr_size)
            if self.ocr_engine.is_available():
                self.logger.info("OCR engine initialized")

        if DB_AVAILABLE:
            db_path = self.config.get('logging.database', '/home/dave/skippy/logs/file_processor.db')
            self.database = Database(db_path, self.logger)
            self.logger.info(f"Database initialized: {db_path}")

        if AI_AVAILABLE and self.config.is_ai_enabled():
            self.ai_classifier = AIClassifier(self.logger, enabled=True)
            if self.ai_classifier.is_available():
                self.logger.info("AI classification enabled")

        # Initialize core components
        self.analyzer = ContentAnalyzer(self.logger, ocr_engine=self.ocr_engine)
        self.classifier = IntelligentClassifier(
            self.logger,
            min_confidence=self.config.get_min_confidence()
        )
        self.renamer = SmartRenamer(self.logger)
        self.organizer = FileOrganizer(self.config, self.logger)

        # Initialize file watcher
        self.watcher = FileWatcher(
            watch_folders=self.config.get_watch_folders(),
            callback=self.process_file,
            ignore_patterns=self.config.get_ignore_patterns(),
            logger=self.logger
        )

        self.logger.info("Intelligent File Processor initialized")

    def setup_logging(self):
        """Setup logging configuration (console only initially)"""
        # Create logger
        self.logger = logging.getLogger(__name__)

        # Prevent duplicate handlers if called multiple times
        if self.logger.handlers:
            return

        # Set log level to INFO initially (will be updated from config if available)
        log_level = logging.INFO

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Always add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Set initial log level
        self.logger.setLevel(log_level)

    def configure_file_logging(self):
        """Configure file logging based on config (called after config is loaded)"""
        # Get logging configuration
        log_file = self.config.get('logging.file')
        log_level_str = self.config.get('logging.level', 'INFO')
        max_size_mb = self.config.get('logging.max_size_mb', 50)
        backup_count = self.config.get('logging.backup_count', 5)

        # Update log level
        try:
            log_level = getattr(logging, log_level_str.upper())
            self.logger.setLevel(log_level)
        except (AttributeError, ValueError):
            self.logger.warning(f"Invalid log level '{log_level_str}', using INFO")
            self.logger.setLevel(logging.INFO)

        # Add file handler if log file is configured
        if log_file:
            try:
                # Create log directory if it doesn't exist
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                # Create rotating file handler
                max_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count
                )

                # Use same formatter as console
                formatter = logging.Formatter(
                    fmt='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(formatter)

                # Add file handler to logger
                self.logger.addHandler(file_handler)
                self.logger.info(f"File logging enabled: {log_file}")

            except Exception as e:
                self.logger.error(f"Failed to setup file logging: {e}")

    def process_file(self, file_path: str):
        """
        Process a new file

        Args:
            file_path: Path to file to process
        """
        self.logger.info(f"Processing: {file_path}")

        # Wait for stabilization (file fully written)
        stabilization_delay = self.config.get_stabilization_delay()
        self.logger.debug(f"Waiting {stabilization_delay}s for file stabilization...")
        time.sleep(stabilization_delay)

        try:
            # Step 1: Analyze content
            self.logger.info(f"[1/5] Analyzing content...")
            analysis = self.analyzer.analyze(file_path)

            # Step 2: Classify
            self.logger.info(f"[2/5] Classifying...")
            category, confidence, class_meta = self.classifier.classify(analysis)

            # Try AI classification if available and enabled
            if self.ai_classifier and self.ai_classifier.is_available():
                self.logger.info(f"  Rule-based: {category} ({confidence}%)")
                self.logger.info(f"  Trying AI classification...")

                ai_category, ai_confidence, ai_meta = self.ai_classifier.classify(
                    analysis,
                    rule_based_result=(category, confidence, class_meta)
                )

                # Use AI result if confidence is higher
                if ai_category and ai_confidence and ai_confidence > confidence:
                    self.logger.info(f"  Using AI result ({ai_confidence}% > {confidence}%)")
                    category = ai_category
                    confidence = ai_confidence
                    class_meta = ai_meta

            subcategory = self.classifier.suggest_subcategory(category, analysis, class_meta)

            self.logger.info(f"  Final: {category} ({confidence}%)")
            if subcategory:
                self.logger.info(f"  Subcategory: {subcategory}")

            # Step 3: Check if should quarantine
            if self.classifier.should_quarantine(confidence):
                self.logger.warning(f"  Low confidence - quarantining for review")
                result = self.organizer.quarantine(
                    file_path,
                    reason=f"Low confidence ({confidence}%)"
                )
                self._notify(f"Quarantined: {Path(file_path).name}",
                           f"Confidence only {confidence}% - review needed")
                return

            # Step 4: Generate smart name
            self.logger.info(f"[3/5] Generating smart filename...")
            classification = {
                'category': category,
                'confidence': confidence,
                'subcategory': subcategory,
                'metadata': class_meta
            }
            new_filename = self.renamer.generate_name(file_path, analysis, classification)
            self.logger.info(f"  New name: {new_filename}")

            # Step 5: Organize (move to destination)
            self.logger.info(f"[4/5] Organizing...")

            # Quarantine period (allow user to cancel)
            quarantine_period = self.config.get_quarantine_period()
            if quarantine_period > 0:
                self.logger.info(f"  Waiting {quarantine_period}s before final move...")
                self._notify(
                    f"Will organize: {Path(file_path).name}",
                    f"→ {new_filename}\n{category}/{subcategory}\n({quarantine_period}s to cancel)"
                )
                time.sleep(quarantine_period)

            result = self.organizer.organize(file_path, category, subcategory, new_filename)

            if result['success']:
                self.logger.info(f"[5/5] ✅ Success!")
                self.logger.info(f"  Destination: {result['destination']}")

                # Log to database if available
                if self.database:
                    try:
                        file_id = self.database.log_processed_file(
                            file_path,
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
                        self.logger.debug(f"  Logged to database (ID: {file_id})")
                    except Exception as e:
                        self.logger.error(f"Database logging error: {e}")

                self._notify(
                    f"✅ Organized: {Path(file_path).name}",
                    f"→ {new_filename}\n{category}/{subcategory}\n{confidence}% confidence"
                )
            else:
                self.logger.error(f"❌ Failed to organize: {result.get('error')}")

                # Log error to database
                if self.database:
                    try:
                        self.database.log_error(file_path, result.get('error', 'Unknown error'))
                    except Exception as e:
                        self.logger.error(f"Database error logging failed: {e}")

                self._notify(
                    f"❌ Error organizing: {Path(file_path).name}",
                    f"Error: {result.get('error')}"
                )

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
            self._notify(
                f"❌ Error processing: {Path(file_path).name}",
                f"Error: {str(e)}"
            )

    def _notify(self, title: str, message: str):
        """
        Send desktop notification

        Args:
            title: Notification title
            message: Notification message
        """
        if not self.config.get('notifications.enabled', True):
            return

        try:
            subprocess.run([
                'notify-send',
                '-u', 'normal',
                '-t', '5000',
                '-a', 'Intelligent File Processor',
                title,
                message
            ], check=False, capture_output=True)
        except Exception as e:
            self.logger.debug(f"Could not send notification: {e}")

    def run(self):
        """Run the daemon (blocking)"""
        self.logger.info("="*60)
        self.logger.info(" Intelligent File Processor Daemon Starting")
        self.logger.info("="*60)

        # Display configuration
        self.logger.info(f"Watching {len(self.config.get_watch_folders())} folders:")
        for folder in self.config.get_watch_folders():
            self.logger.info(f"  - {folder['path']}")

        # Phase 2 features status
        self.logger.info(f"OCR: {'Enabled' if self.ocr_engine and self.ocr_engine.is_available() else 'Disabled'}")
        self.logger.info(f"AI Classification: {'Enabled' if self.ai_classifier and self.ai_classifier.is_available() else 'Disabled'}")
        self.logger.info(f"Database Logging: {'Enabled' if self.database else 'Disabled'}")
        self.logger.info(f"Min Confidence: {self.config.get_min_confidence()}%")
        self.logger.info(f"Create Backups: {'Yes' if self.config.should_create_backup() else 'No'}")

        self.logger.info("="*60)
        self.logger.info(" Daemon started - Press Ctrl+C to stop")
        self.logger.info("="*60)

        # Start watching
        self.watcher.run()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Intelligent File Processor Daemon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default configuration
  ./file_processor_daemon.py

  # Start with custom config
  ./file_processor_daemon.py --config /path/to/config.yaml

  # Test mode (dry run)
  ./file_processor_daemon.py --test

For more information, see:
  /home/dave/skippy/documentation/intelligent_file_processor/
        """
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Path to configuration file'
    )

    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Test mode (dry run - no actual moves)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run daemon
    try:
        daemon = FileProcessorDaemon(config_path=args.config)
        daemon.run()
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
