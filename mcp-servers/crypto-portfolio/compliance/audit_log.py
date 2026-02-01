"""
Audit Log - Append-Only Hash-Chained Trail
============================================

Provides tamper-evident audit logging for cryptocurrency portfolio operations.
Each entry includes a SHA-256 checksum chained to the previous entry, making
it possible to detect any modifications to the history.

Storage: JSON file-based (no SQLAlchemy dependency required).
Default path: /home/dave/skippy/work/crypto/audit_log.json
"""

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_AUDIT_LOG_PATH = os.path.expanduser(
    "~/skippy/work/crypto/audit_log.json"
)


@dataclass
class AuditEntry:
    """A single audit log entry with hash chain verification."""
    timestamp: str
    table_name: str
    record_id: str
    action: str  # INSERT, UPDATE, DELETE
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_by: str = "system"
    checksum: str = ""
    prev_checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        return cls(**data)


class AuditLog:
    """Append-only hash-chained audit log.

    Each entry's checksum is computed from its content plus the previous
    entry's checksum, creating a chain that can be verified for integrity.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path or DEFAULT_AUDIT_LOG_PATH
        self._entries: List[AuditEntry] = []
        self._loaded = False

    def _ensure_loaded(self):
        """Lazy-load entries from disk."""
        if self._loaded:
            return
        self._loaded = True

        if not os.path.exists(self.path):
            self._entries = []
            return

        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            self._entries = [AuditEntry.from_dict(e) for e in data]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load audit log: {e}")
            self._entries = []

    def _save(self):
        """Persist entries to disk."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2,
                      default=str)

    @staticmethod
    def _compute_checksum(entry_data: Dict[str, Any],
                          prev_checksum: str) -> str:
        """Compute SHA-256 checksum for an entry chained to previous."""
        # Deterministic serialization: sort keys, use separators
        payload = json.dumps(entry_data, sort_keys=True, separators=(",", ":"),
                             default=str)
        combined = f"{prev_checksum}|{payload}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def log_change(
        self,
        table_name: str,
        record_id: str,
        action: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        changed_by: str = "system",
    ) -> AuditEntry:
        """Record a change in the audit log.

        Args:
            table_name: Database table affected.
            record_id: ID of the record changed.
            action: INSERT, UPDATE, or DELETE.
            old_values: Previous values (for UPDATE/DELETE).
            new_values: New values (for INSERT/UPDATE).
            changed_by: Who made the change.

        Returns:
            The created AuditEntry.
        """
        self._ensure_loaded()

        prev_checksum = self._entries[-1].checksum if self._entries else ""

        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            table_name=table_name,
            record_id=str(record_id),
            action=action.upper(),
            old_values=old_values,
            new_values=new_values,
            changed_by=changed_by,
            prev_checksum=prev_checksum,
        )

        # Compute checksum from entry content (excluding checksum itself)
        entry_data = {
            "timestamp": entry.timestamp,
            "table_name": entry.table_name,
            "record_id": entry.record_id,
            "action": entry.action,
            "old_values": entry.old_values,
            "new_values": entry.new_values,
            "changed_by": entry.changed_by,
        }
        entry.checksum = self._compute_checksum(entry_data, prev_checksum)

        self._entries.append(entry)
        self._save()

        logger.info(
            f"Audit: {action} on {table_name}#{record_id} by {changed_by}"
        )
        return entry

    def verify_chain(self) -> Dict[str, Any]:
        """Verify the integrity of the entire audit chain.

        Returns:
            Dict with 'valid' (bool), 'entries_checked' (int),
            and 'errors' (list of issues found).
        """
        self._ensure_loaded()

        errors = []
        prev_checksum = ""

        for i, entry in enumerate(self._entries):
            # Verify prev_checksum link
            if entry.prev_checksum != prev_checksum:
                errors.append(
                    f"Entry {i}: prev_checksum mismatch "
                    f"(expected {prev_checksum[:12]}..., "
                    f"got {entry.prev_checksum[:12]}...)"
                )

            # Recompute checksum
            entry_data = {
                "timestamp": entry.timestamp,
                "table_name": entry.table_name,
                "record_id": entry.record_id,
                "action": entry.action,
                "old_values": entry.old_values,
                "new_values": entry.new_values,
                "changed_by": entry.changed_by,
            }
            expected = self._compute_checksum(entry_data, prev_checksum)

            if entry.checksum != expected:
                errors.append(
                    f"Entry {i}: checksum mismatch "
                    f"(expected {expected[:12]}..., "
                    f"got {entry.checksum[:12]}...)"
                )

            prev_checksum = entry.checksum

        return {
            "valid": len(errors) == 0,
            "entries_checked": len(self._entries),
            "errors": errors,
        }

    def get_entries(
        self,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        action: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditEntry]:
        """Filter and retrieve audit entries.

        Args:
            table_name: Filter by table name.
            record_id: Filter by record ID.
            action: Filter by action (INSERT/UPDATE/DELETE).
            since: ISO date string for start of range.
            until: ISO date string for end of range.
            limit: Maximum entries to return.

        Returns:
            List of matching AuditEntry objects (newest first).
        """
        self._ensure_loaded()

        results = self._entries

        if table_name:
            results = [e for e in results if e.table_name == table_name]
        if record_id:
            results = [e for e in results if e.record_id == str(record_id)]
        if action:
            results = [e for e in results
                       if e.action == action.upper()]
        if since:
            results = [e for e in results if e.timestamp >= since]
        if until:
            results = [e for e in results if e.timestamp <= until]

        # Return newest first, with limit
        return list(reversed(results))[:limit]

    def format_entries_markdown(self, entries: List[AuditEntry]) -> str:
        """Format audit entries as markdown table."""
        if not entries:
            return "No audit log entries found."

        lines = []
        lines.append("| Timestamp | Table | Record | Action | Changed By | Checksum |")
        lines.append("|-----------|-------|--------|--------|------------|----------|")

        for e in entries:
            ts = e.timestamp[:19].replace("T", " ")
            lines.append(
                f"| {ts} | {e.table_name} | {e.record_id} | "
                f"{e.action} | {e.changed_by} | {e.checksum[:12]}... |"
            )

        return "\n".join(lines)
