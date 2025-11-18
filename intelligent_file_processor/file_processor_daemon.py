#!/usr/bin/env python3
"""
Intelligent File Processor Daemon
Main entry point - watches folders and processes files automatically
"""

import sys
import time
import logging
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


class FileProcessorDaemon:
    """Main daemon that coordinates all components"""

    def __init__(self, config_path: str = None):
        """
        Initialize daemon

        Args:
            config_path: Path to configuration file
        """
        # Setup logging
        self.setup_logging()

        # Load configuration
        self.config = ConfigLoader(config_path)
        self.logger.info("Configuration loaded successfully")

        # Initialize components
        self.analyzer = ContentAnalyzer(self.logger)
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
        """Setup logging configuration"""
        # For now, log to console
        # TODO: Add file logging based on config
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

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
            subcategory = self.classifier.suggest_subcategory(category, analysis, class_meta)

            self.logger.info(f"  Category: {category}")
            if subcategory:
                self.logger.info(f"  Subcategory: {subcategory}")
            self.logger.info(f"  Confidence: {confidence}%")

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

                self._notify(
                    f"✅ Organized: {Path(file_path).name}",
                    f"→ {new_filename}\n{category}/{subcategory}\n{confidence}% confidence"
                )
            else:
                self.logger.error(f"❌ Failed to organize: {result.get('error')}")
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

        self.logger.info(f"AI Classification: {'Enabled' if self.config.is_ai_enabled() else 'Disabled'}")
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
