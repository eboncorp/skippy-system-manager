"""
Database storage for portfolio data.

Uses SQLite for local persistence of:
- Portfolio snapshots
- Staking rewards
- DCA executions
- Rebalancing history
- Price history
"""

import sqlite3
import json
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator

from config import settings


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def decimal_decoder(dct: dict) -> dict:
    """Decode strings back to Decimals where appropriate."""
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                # Try to parse as Decimal if it looks like a number
                if value.replace(".", "").replace("-", "").isdigit():
                    dct[key] = Decimal(value)
            except:
                pass
    return dct


class Database:
    """SQLite database for portfolio data."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.data.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Portfolio snapshots
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_usd_value TEXT NOT NULL,
                    total_staked_value TEXT NOT NULL,
                    positions_json TEXT NOT NULL,
                    allocation_json TEXT NOT NULL,
                    drift_json TEXT NOT NULL
                )
            """)
            
            # Staking rewards
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staking_rewards (
                    id TEXT PRIMARY KEY,
                    asset TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    usd_value TEXT NOT NULL,
                    price TEXT NOT NULL,
                    source TEXT NOT NULL,
                    tx_hash TEXT
                )
            """)
            
            # DCA executions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dca_executions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    usd_amount TEXT NOT NULL,
                    filled_amount TEXT,
                    filled_price TEXT,
                    exchange TEXT,
                    status TEXT NOT NULL,
                    order_id TEXT,
                    error TEXT
                )
            """)
            
            # Rebalancing sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rebalance_sessions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    trades_json TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL
                )
            """)
            
            # Price history (for tax calculations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset TEXT NOT NULL,
                    price TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    UNIQUE(asset, timestamp)
                )
            """)
            
            # Tax lots (for cost basis tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tax_lots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    cost_basis TEXT NOT NULL,
                    acquisition_date TEXT NOT NULL,
                    source TEXT NOT NULL,
                    remaining_amount TEXT NOT NULL,
                    closed_date TEXT,
                    proceeds TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON portfolio_snapshots(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rewards_timestamp ON staking_rewards(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rewards_asset ON staking_rewards(asset)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dca_timestamp ON dca_executions(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_asset_time ON price_history(asset, timestamp)")
    
    # Portfolio Snapshots
    
    def save_snapshot(self, snapshot: Any) -> int:
        """Save a portfolio snapshot."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Convert positions to JSON-serializable format
            positions_data = {}
            for asset, pos in snapshot.positions.items():
                positions_data[asset] = {
                    "asset": pos.asset,
                    "total_amount": str(pos.total_amount),
                    "available_amount": str(pos.available_amount),
                    "staked_amount": str(pos.staked_amount),
                    "usd_value": str(pos.usd_value),
                    "price": str(pos.price),
                }
            
            allocation_data = {k: str(v) for k, v in snapshot.actual_allocation.items()}
            drift_data = {k: str(v) for k, v in snapshot.drift.items()}
            
            cursor.execute("""
                INSERT INTO portfolio_snapshots 
                (timestamp, total_usd_value, total_staked_value, positions_json, allocation_json, drift_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp.isoformat(),
                str(snapshot.total_usd_value),
                str(snapshot.total_staked_value),
                json.dumps(positions_data),
                json.dumps(allocation_data),
                json.dumps(drift_data),
            ))
            
            return cursor.lastrowid
    
    def get_latest_snapshot(self) -> Optional[Dict]:
        """Get the most recent portfolio snapshot."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM portfolio_snapshots 
                ORDER BY timestamp DESC LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_snapshot(row)
    
    def get_snapshots(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get portfolio snapshots in a date range."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM portfolio_snapshots WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [self._row_to_snapshot(row) for row in cursor.fetchall()]
    
    def _row_to_snapshot(self, row: sqlite3.Row) -> Dict:
        """Convert a database row to snapshot dict."""
        return {
            "id": row["id"],
            "timestamp": datetime.fromisoformat(row["timestamp"]),
            "total_usd_value": Decimal(row["total_usd_value"]),
            "total_staked_value": Decimal(row["total_staked_value"]),
            "positions": json.loads(row["positions_json"], object_hook=decimal_decoder),
            "allocation": json.loads(row["allocation_json"], object_hook=decimal_decoder),
            "drift": json.loads(row["drift_json"], object_hook=decimal_decoder),
        }
    
    # Staking Rewards
    
    def save_staking_reward(self, reward: Any) -> None:
        """Save a staking reward."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO staking_rewards 
                (id, asset, amount, timestamp, usd_value, price, source, tx_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reward.id,
                reward.asset,
                str(reward.amount),
                reward.timestamp.isoformat(),
                str(reward.usd_value_at_receipt),
                str(reward.price_at_receipt),
                reward.source,
                reward.tx_hash,
            ))
    
    def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Dict]:
        """Get staking rewards with optional filters."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM staking_rewards WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            if asset:
                query += " AND asset = ?"
                params.append(asset)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            
            return [{
                "id": row["id"],
                "asset": row["asset"],
                "amount": Decimal(row["amount"]),
                "timestamp": datetime.fromisoformat(row["timestamp"]),
                "usd_value": Decimal(row["usd_value"]),
                "price": Decimal(row["price"]),
                "source": row["source"],
                "tx_hash": row["tx_hash"],
            } for row in cursor.fetchall()]
    
    # DCA Executions
    
    def save_dca_execution(self, execution: Any) -> None:
        """Save a DCA execution."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO dca_executions 
                (id, timestamp, asset, usd_amount, filled_amount, filled_price, exchange, status, order_id, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.id,
                execution.timestamp.isoformat(),
                execution.asset,
                str(execution.usd_amount),
                str(execution.filled_amount) if execution.filled_amount else None,
                str(execution.filled_price) if execution.filled_price else None,
                execution.exchange,
                execution.status,
                execution.order_id,
                execution.error,
            ))
    
    def get_dca_executions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get DCA executions with optional filters."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM dca_executions WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            
            return [{
                "id": row["id"],
                "timestamp": datetime.fromisoformat(row["timestamp"]),
                "asset": row["asset"],
                "usd_amount": Decimal(row["usd_amount"]),
                "filled_amount": Decimal(row["filled_amount"]) if row["filled_amount"] else None,
                "filled_price": Decimal(row["filled_price"]) if row["filled_price"] else None,
                "exchange": row["exchange"],
                "status": row["status"],
                "order_id": row["order_id"],
                "error": row["error"],
            } for row in cursor.fetchall()]
    
    # Price History
    
    def save_price(self, asset: str, price: Decimal, timestamp: datetime) -> None:
        """Save a price point."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO price_history (asset, price, timestamp)
                VALUES (?, ?, ?)
            """, (asset, str(price), timestamp.isoformat()))
    
    def get_price_at_time(
        self,
        asset: str,
        timestamp: datetime,
    ) -> Optional[Decimal]:
        """Get price closest to a given timestamp."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Get closest price before or at timestamp
            cursor.execute("""
                SELECT price FROM price_history 
                WHERE asset = ? AND timestamp <= ?
                ORDER BY timestamp DESC LIMIT 1
            """, (asset, timestamp.isoformat()))
            
            row = cursor.fetchone()
            if row:
                return Decimal(row["price"])
            
            return None
    
    # Tax Lots
    
    def add_tax_lot(
        self,
        asset: str,
        amount: Decimal,
        cost_basis: Decimal,
        acquisition_date: datetime,
        source: str,
    ) -> int:
        """Add a new tax lot."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tax_lots 
                (asset, amount, cost_basis, acquisition_date, source, remaining_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                asset,
                str(amount),
                str(cost_basis),
                acquisition_date.isoformat(),
                source,
                str(amount),
            ))
            
            return cursor.lastrowid
    
    def get_open_tax_lots(self, asset: str) -> List[Dict]:
        """Get open (non-zero remaining) tax lots for an asset."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM tax_lots 
                WHERE asset = ? AND CAST(remaining_amount AS REAL) > 0
                ORDER BY acquisition_date ASC
            """, (asset,))
            
            return [{
                "id": row["id"],
                "asset": row["asset"],
                "amount": Decimal(row["amount"]),
                "cost_basis": Decimal(row["cost_basis"]),
                "acquisition_date": datetime.fromisoformat(row["acquisition_date"]),
                "source": row["source"],
                "remaining_amount": Decimal(row["remaining_amount"]),
            } for row in cursor.fetchall()]
    
    def close_tax_lot(
        self,
        lot_id: int,
        amount_sold: Decimal,
        proceeds: Decimal,
        close_date: datetime,
    ) -> None:
        """Close (partially or fully) a tax lot."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Get current remaining amount
            cursor.execute("SELECT remaining_amount FROM tax_lots WHERE id = ?", (lot_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Tax lot {lot_id} not found")
            
            remaining = Decimal(row["remaining_amount"])
            new_remaining = remaining - amount_sold
            
            if new_remaining < 0:
                raise ValueError(f"Cannot sell more than remaining amount ({remaining})")
            
            cursor.execute("""
                UPDATE tax_lots 
                SET remaining_amount = ?, closed_date = ?, proceeds = ?
                WHERE id = ?
            """, (str(new_remaining), close_date.isoformat(), str(proceeds), lot_id))


# Global database instance
db = Database()
