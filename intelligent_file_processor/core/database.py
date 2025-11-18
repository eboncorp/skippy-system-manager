#!/usr/bin/env python3
"""
Database System for Intelligent File Processor
Logs all file processing actions and enables learning
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json


class Database:
    """Database for logging file processing and learning"""

    def __init__(self, db_path: str, logger: logging.Logger):
        """
        Initialize database

        Args:
            db_path: Path to SQLite database file
            logger: Logger instance
        """
        self.db_path = Path(db_path)
        self.logger = logger

        # Create parent directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows
        self.logger.debug(f"Connected to database: {self.db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Files processed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT NOT NULL,
                original_name TEXT NOT NULL,
                final_path TEXT,
                final_name TEXT,
                file_hash TEXT,
                file_size INTEGER,
                mime_type TEXT,
                classification TEXT,
                subcategory TEXT,
                confidence REAL,
                method TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_folder TEXT,
                destination_folder TEXT,
                success BOOLEAN,
                error_message TEXT,
                metadata TEXT
            )
        """)

        # User corrections (for learning)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER REFERENCES processed_files(id),
                old_classification TEXT,
                new_classification TEXT,
                old_path TEXT,
                new_path TEXT,
                corrected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)

        # Classification rules (learned patterns)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                classification TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                source TEXT,
                times_applied INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
        """)

        # Processing errors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                error_message TEXT,
                error_type TEXT,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE
            )
        """)

        # Quarantine queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quarantine (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                reason TEXT,
                suggested_classification TEXT,
                confidence REAL,
                quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed BOOLEAN DEFAULT FALSE,
                final_classification TEXT,
                reviewed_at TIMESTAMP
            )
        """)

        # Statistics (daily aggregates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                date DATE PRIMARY KEY,
                files_processed INTEGER DEFAULT 0,
                files_quarantined INTEGER DEFAULT 0,
                files_errored INTEGER DEFAULT 0,
                avg_confidence REAL,
                processing_time_avg REAL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_files_date ON processed_files(processed_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_files_classification ON processed_files(classification)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quarantine_reviewed ON quarantine(reviewed)")

        self.conn.commit()
        self.logger.debug("Database tables initialized")

    def log_processed_file(self, original_path: str, result: Dict[str, Any],
                          analysis: Dict[str, Any], classification: Dict[str, Any]) -> int:
        """
        Log a processed file

        Args:
            original_path: Original file path
            result: Organization result dict
            analysis: Content analysis dict
            classification: Classification result dict

        Returns:
            Row ID of inserted record
        """
        cursor = self.conn.cursor()

        # Calculate file hash
        file_hash = self._calculate_hash(original_path) if Path(original_path).exists() else None

        # Serialize metadata
        metadata = {
            'analysis': {
                'ocr_performed': analysis.get('ocr_performed', False),
                'page_count': analysis.get('page_count'),
                'metadata': analysis.get('metadata', {})
            },
            'classification': {
                'patterns': classification.get('patterns', []),
                'all_scores': classification.get('all_scores', {})
            }
        }

        cursor.execute("""
            INSERT INTO processed_files (
                original_path, original_name, final_path, final_name,
                file_hash, file_size, mime_type,
                classification, subcategory, confidence, method,
                source_folder, destination_folder,
                success, error_message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            original_path,
            Path(original_path).name,
            result.get('destination'),
            Path(result.get('destination', '')).name if result.get('destination') else None,
            file_hash,
            analysis.get('size'),
            analysis.get('mime_type'),
            classification.get('category'),
            classification.get('subcategory'),
            classification.get('confidence'),
            classification.get('method'),
            str(Path(original_path).parent),
            result.get('destination_folder'),
            result.get('success', False),
            result.get('error'),
            json.dumps(metadata)
        ))

        self.conn.commit()
        return cursor.lastrowid

    def log_quarantine(self, file_path: str, reason: str, classification: Dict[str, Any]):
        """Log a quarantined file"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO quarantine (
                file_path, reason, suggested_classification, confidence
            ) VALUES (?, ?, ?, ?)
        """, (
            file_path,
            reason,
            classification.get('category'),
            classification.get('confidence')
        ))

        self.conn.commit()

    def log_error(self, file_path: str, error_message: str, error_type: str = 'processing'):
        """Log a processing error"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO errors (file_path, error_message, error_type)
            VALUES (?, ?, ?)
        """, (file_path, error_message, error_type))

        self.conn.commit()

    def log_correction(self, file_id: int, old_classification: str, new_classification: str,
                      old_path: str, new_path: str, notes: str = None):
        """Log a user correction for learning"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO corrections (
                file_id, old_classification, new_classification,
                old_path, new_path, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (file_id, old_classification, new_classification, old_path, new_path, notes))

        self.conn.commit()

    def get_recent_files(self, limit: int = 20) -> List[Dict]:
        """Get recently processed files"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM processed_files
            ORDER BY processed_at DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_quarantine_queue(self, reviewed: bool = False) -> List[Dict]:
        """Get quarantined files"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM quarantine
            WHERE reviewed = ?
            ORDER BY quarantined_at DESC
        """, (reviewed,))

        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get processing statistics"""
        cursor = self.conn.cursor()

        # Total files processed
        cursor.execute("""
            SELECT COUNT(*) as total,
                   AVG(confidence) as avg_confidence,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM processed_files
            WHERE processed_at >= datetime('now', '-' || ? || ' days')
        """, (days,))

        totals = dict(cursor.fetchone())

        # By classification
        cursor.execute("""
            SELECT classification, COUNT(*) as count
            FROM processed_files
            WHERE processed_at >= datetime('now', '-' || ? || ' days')
            GROUP BY classification
            ORDER BY count DESC
        """, (days,))

        by_category = {row['classification']: row['count'] for row in cursor.fetchall()}

        # Errors
        cursor.execute("""
            SELECT COUNT(*) as error_count
            FROM errors
            WHERE occurred_at >= datetime('now', '-' || ? || ' days')
        """, (days,))

        errors = cursor.fetchone()['error_count']

        return {
            'period_days': days,
            'total_processed': totals['total'],
            'successful': totals['successful'],
            'failed': totals['total'] - totals['successful'],
            'avg_confidence': totals['avg_confidence'],
            'errors': errors,
            'by_category': by_category
        }

    def search_files(self, query: str, limit: int = 50) -> List[Dict]:
        """Search processed files"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM processed_files
            WHERE original_name LIKE ? OR final_name LIKE ?
            ORDER BY processed_at DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', limit))

        return [dict(row) for row in cursor.fetchall()]

    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.debug("Database connection closed")

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


if __name__ == "__main__":
    # Test database
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Create test database
    db_path = "/tmp/test_file_processor.db"
    db = Database(db_path, logger)

    print(f"✅ Database created: {db_path}\n")

    # Test logging
    test_analysis = {
        'size': 1024,
        'mime_type': 'text/plain',
        'ocr_performed': False
    }

    test_classification = {
        'category': 'business',
        'subcategory': 'invoices',
        'confidence': 85,
        'method': 'content_analysis',
        'patterns': ['invoice', 'bill']
    }

    test_result = {
        'success': True,
        'destination': '/home/dave/skippy/documents/business/invoices/test.txt',
        'destination_folder': '/home/dave/skippy/documents/business/invoices'
    }

    file_id = db.log_processed_file(
        '/tmp/test.txt',
        test_result,
        test_analysis,
        test_classification
    )

    print(f"Logged file with ID: {file_id}")

    # Get statistics
    stats = db.get_statistics(days=7)
    print(f"\nStatistics:")
    print(f"  Total processed: {stats['total_processed']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Avg confidence: {stats['avg_confidence']:.1f}%")

    # Get recent files
    recent = db.get_recent_files(limit=5)
    print(f"\nRecent files: {len(recent)}")
    for file in recent:
        print(f"  - {file['original_name']} → {file['classification']}")

    db.close()
    print("\n✅ Database test complete")
