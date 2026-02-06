"""
Cost Basis & Tax Tracking Module
Tracks purchase prices, calculates gains/losses, and generates tax reports.

Supports:
- FIFO, LIFO, HIFO, and Specific ID accounting methods
- Short-term vs long-term capital gains
- Transaction import from all supported exchanges
- Tax report generation (Form 8949 format)
"""

import logging
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class AccountingMethod(Enum):
    FIFO = "fifo"      # First In, First Out
    LIFO = "lifo"      # Last In, First Out  
    HIFO = "hifo"      # Highest In, First Out (tax efficient)
    SPECIFIC = "specific"  # Specific identification


@dataclass
class CostBasisLot:
    """Represents a single purchase lot."""
    lot_id: str
    asset: str
    quantity: float
    cost_per_unit: float
    total_cost: float
    purchase_date: datetime
    exchange: str
    transaction_id: Optional[str] = None
    remaining_quantity: float = None
    
    def __post_init__(self):
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity


@dataclass
class SaleRecord:
    """Represents a sale and its tax implications."""
    sale_id: str
    asset: str
    quantity: float
    sale_price_per_unit: float
    total_proceeds: float
    sale_date: datetime
    exchange: str
    lots_used: List[Dict]  # List of {lot_id, quantity, cost_basis}
    total_cost_basis: float
    gain_loss: float
    is_long_term: bool
    transaction_id: Optional[str] = None


class CostBasisTracker:
    """Tracks cost basis across all exchanges."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__), 
                "data", 
                "cost_basis.db"
            )
        
        # Ensure directory exists
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_database()
        self.accounting_method = AccountingMethod.FIFO
    
    def _init_database(self):
        """Initialize database tables."""
        cursor = self.conn.cursor()
        
        # Cost basis lots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lots (
                lot_id TEXT PRIMARY KEY,
                asset TEXT NOT NULL,
                quantity REAL NOT NULL,
                remaining_quantity REAL NOT NULL,
                cost_per_unit REAL NOT NULL,
                total_cost REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                exchange TEXT NOT NULL,
                transaction_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sales records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id TEXT PRIMARY KEY,
                asset TEXT NOT NULL,
                quantity REAL NOT NULL,
                sale_price_per_unit REAL NOT NULL,
                total_proceeds REAL NOT NULL,
                sale_date TEXT NOT NULL,
                exchange TEXT NOT NULL,
                lots_used TEXT NOT NULL,
                total_cost_basis REAL NOT NULL,
                gain_loss REAL NOT NULL,
                is_long_term INTEGER NOT NULL,
                transaction_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Manual adjustments table (for transfers, gifts, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adjustments (
                adjustment_id TEXT PRIMARY KEY,
                asset TEXT NOT NULL,
                adjustment_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                cost_basis REAL,
                date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lots_asset ON lots(asset)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lots_date ON lots(purchase_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_asset ON sales(asset)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)")
        
        self.conn.commit()
    
    def set_accounting_method(self, method: AccountingMethod):
        """Set the accounting method for cost basis calculation."""
        self.accounting_method = method
    
    def add_purchase(
        self,
        asset: str,
        quantity: float,
        cost_per_unit: float,
        purchase_date: datetime,
        exchange: str,
        transaction_id: str = None
    ) -> CostBasisLot:
        """Record a purchase (creates a new lot)."""
        import uuid
        
        lot_id = str(uuid.uuid4())[:8]
        total_cost = quantity * cost_per_unit
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO lots 
            (lot_id, asset, quantity, remaining_quantity, cost_per_unit, 
             total_cost, purchase_date, exchange, transaction_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lot_id, asset.upper(), quantity, quantity, cost_per_unit,
            total_cost, purchase_date.isoformat(), exchange, transaction_id
        ))
        self.conn.commit()
        
        return CostBasisLot(
            lot_id=lot_id,
            asset=asset.upper(),
            quantity=quantity,
            cost_per_unit=cost_per_unit,
            total_cost=total_cost,
            purchase_date=purchase_date,
            exchange=exchange,
            transaction_id=transaction_id,
            remaining_quantity=quantity
        )
    
    def record_sale(
        self,
        asset: str,
        quantity: float,
        sale_price_per_unit: float,
        sale_date: datetime,
        exchange: str,
        transaction_id: str = None,
        specific_lots: List[str] = None
    ) -> SaleRecord:
        """
        Record a sale and calculate gain/loss.
        
        Args:
            asset: Asset being sold
            quantity: Amount being sold
            sale_price_per_unit: Price per unit at sale
            sale_date: Date of sale
            exchange: Exchange where sale occurred
            transaction_id: Optional transaction ID
            specific_lots: For SPECIFIC method, list of lot_ids to use
        
        Returns:
            SaleRecord with gain/loss calculation
        """
        import uuid
        
        # Get available lots
        lots = self._get_available_lots(asset)
        
        if not lots:
            raise ValueError(f"No cost basis lots found for {asset}")
        
        # Select lots based on accounting method
        selected_lots = self._select_lots(
            lots, quantity, sale_date, specific_lots
        )
        
        # Calculate totals
        total_proceeds = quantity * sale_price_per_unit
        total_cost_basis = sum(lot["cost_basis"] for lot in selected_lots)
        gain_loss = total_proceeds - total_cost_basis
        
        # Determine if long-term (held > 1 year)
        # Use the earliest lot's date for this determination
        earliest_purchase = min(lot["purchase_date"] for lot in selected_lots)
        is_long_term = (sale_date - earliest_purchase).days > 365
        
        # Update lot quantities
        self._deplete_lots(selected_lots)
        
        # Record the sale
        sale_id = str(uuid.uuid4())[:8]
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sales
            (sale_id, asset, quantity, sale_price_per_unit, total_proceeds,
             sale_date, exchange, lots_used, total_cost_basis, gain_loss,
             is_long_term, transaction_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sale_id, asset.upper(), quantity, sale_price_per_unit, total_proceeds,
            sale_date.isoformat(), exchange, json.dumps(selected_lots, default=str),
            total_cost_basis, gain_loss, 1 if is_long_term else 0, transaction_id
        ))
        self.conn.commit()
        
        return SaleRecord(
            sale_id=sale_id,
            asset=asset.upper(),
            quantity=quantity,
            sale_price_per_unit=sale_price_per_unit,
            total_proceeds=total_proceeds,
            sale_date=sale_date,
            exchange=exchange,
            lots_used=selected_lots,
            total_cost_basis=total_cost_basis,
            gain_loss=gain_loss,
            is_long_term=is_long_term,
            transaction_id=transaction_id
        )
    
    def _get_available_lots(self, asset: str) -> List[Dict]:
        """Get all lots with remaining quantity for an asset."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT lot_id, asset, remaining_quantity, cost_per_unit, 
                   purchase_date, exchange
            FROM lots
            WHERE asset = ? AND remaining_quantity > 0
            ORDER BY purchase_date
        """, (asset.upper(),))
        
        lots = []
        for row in cursor.fetchall():
            lots.append({
                "lot_id": row[0],
                "asset": row[1],
                "remaining_quantity": row[2],
                "cost_per_unit": row[3],
                "purchase_date": datetime.fromisoformat(row[4]),
                "exchange": row[5]
            })
        
        return lots
    
    def _select_lots(
        self,
        lots: List[Dict],
        quantity_needed: float,
        sale_date: datetime,
        specific_lots: List[str] = None
    ) -> List[Dict]:
        """Select lots based on accounting method."""
        
        if self.accounting_method == AccountingMethod.FIFO:
            # Already sorted by date ascending
            sorted_lots = lots
        elif self.accounting_method == AccountingMethod.LIFO:
            sorted_lots = sorted(lots, key=lambda x: x["purchase_date"], reverse=True)
        elif self.accounting_method == AccountingMethod.HIFO:
            sorted_lots = sorted(lots, key=lambda x: x["cost_per_unit"], reverse=True)
        elif self.accounting_method == AccountingMethod.SPECIFIC:
            if not specific_lots:
                raise ValueError("Specific lots required for SPECIFIC accounting method")
            sorted_lots = [l for l in lots if l["lot_id"] in specific_lots]
        else:
            sorted_lots = lots
        
        selected = []
        remaining_needed = quantity_needed
        
        for lot in sorted_lots:
            if remaining_needed <= 0:
                break
            
            quantity_from_lot = min(lot["remaining_quantity"], remaining_needed)
            cost_basis = quantity_from_lot * lot["cost_per_unit"]
            
            selected.append({
                "lot_id": lot["lot_id"],
                "quantity": quantity_from_lot,
                "cost_per_unit": lot["cost_per_unit"],
                "cost_basis": cost_basis,
                "purchase_date": lot["purchase_date"]
            })
            
            remaining_needed -= quantity_from_lot
        
        if remaining_needed > 0.00000001:  # Small tolerance for float precision
            raise ValueError(
                f"Insufficient cost basis lots. Need {quantity_needed}, "
                f"have {quantity_needed - remaining_needed}"
            )
        
        return selected
    
    def _deplete_lots(self, selected_lots: List[Dict]):
        """Update remaining quantities in lots."""
        cursor = self.conn.cursor()
        
        for lot in selected_lots:
            cursor.execute("""
                UPDATE lots
                SET remaining_quantity = remaining_quantity - ?
                WHERE lot_id = ?
            """, (lot["quantity"], lot["lot_id"]))
        
        self.conn.commit()
    
    def get_current_holdings(self) -> Dict[str, Dict]:
        """Get current holdings with cost basis."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT asset, 
                   SUM(remaining_quantity) as total_quantity,
                   SUM(remaining_quantity * cost_per_unit) as total_cost
            FROM lots
            WHERE remaining_quantity > 0
            GROUP BY asset
        """)
        
        holdings = {}
        for row in cursor.fetchall():
            asset, quantity, total_cost = row
            if quantity > 0:
                holdings[asset] = {
                    "quantity": quantity,
                    "total_cost_basis": total_cost,
                    "average_cost": total_cost / quantity
                }
        
        return holdings
    
    def get_unrealized_gains(self, current_prices: Dict[str, float]) -> Dict[str, Dict]:
        """Calculate unrealized gains/losses based on current prices."""
        holdings = self.get_current_holdings()
        
        results = {}
        total_cost = 0
        total_value = 0
        total_unrealized = 0
        
        for asset, data in holdings.items():
            current_price = current_prices.get(asset, 0)
            current_value = data["quantity"] * current_price
            unrealized = current_value - data["total_cost_basis"]
            
            results[asset] = {
                "quantity": data["quantity"],
                "cost_basis": data["total_cost_basis"],
                "average_cost": data["average_cost"],
                "current_price": current_price,
                "current_value": current_value,
                "unrealized_gain": unrealized,
                "unrealized_percent": (unrealized / data["total_cost_basis"] * 100) 
                                      if data["total_cost_basis"] > 0 else 0
            }
            
            total_cost += data["total_cost_basis"]
            total_value += current_value
            total_unrealized += unrealized
        
        results["_total"] = {
            "total_cost_basis": total_cost,
            "total_current_value": total_value,
            "total_unrealized_gain": total_unrealized,
            "total_unrealized_percent": (total_unrealized / total_cost * 100) 
                                        if total_cost > 0 else 0
        }
        
        return results
    
    def get_realized_gains(
        self,
        year: int = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """Get realized gains/losses for a period."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM sales WHERE 1=1"
        params = []
        
        if year:
            query += " AND strftime('%Y', sale_date) = ?"
            params.append(str(year))
        if start_date:
            query += " AND sale_date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND sale_date <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY sale_date"
        cursor.execute(query, params)
        
        sales = []
        short_term_gain = 0
        long_term_gain = 0
        total_proceeds = 0
        total_cost = 0
        
        for row in cursor.fetchall():
            sale = {
                "sale_id": row[0],
                "asset": row[1],
                "quantity": row[2],
                "sale_price": row[3],
                "proceeds": row[4],
                "sale_date": row[5],
                "exchange": row[6],
                "cost_basis": row[8],
                "gain_loss": row[9],
                "is_long_term": bool(row[10])
            }
            sales.append(sale)
            
            if sale["is_long_term"]:
                long_term_gain += sale["gain_loss"]
            else:
                short_term_gain += sale["gain_loss"]
            
            total_proceeds += sale["proceeds"]
            total_cost += sale["cost_basis"]
        
        return {
            "sales": sales,
            "short_term_gain": short_term_gain,
            "long_term_gain": long_term_gain,
            "total_gain": short_term_gain + long_term_gain,
            "total_proceeds": total_proceeds,
            "total_cost_basis": total_cost,
            "num_transactions": len(sales)
        }
    
    def generate_tax_report(self, year: int) -> Dict:
        """Generate tax report data for Form 8949."""
        gains = self.get_realized_gains(year=year)
        
        # Separate short-term and long-term
        short_term = [s for s in gains["sales"] if not s["is_long_term"]]
        long_term = [s for s in gains["sales"] if s["is_long_term"]]
        
        return {
            "tax_year": year,
            "form_8949_part_i": {  # Short-term
                "description": "Short-term transactions (held 1 year or less)",
                "transactions": short_term,
                "total_proceeds": sum(s["proceeds"] for s in short_term),
                "total_cost_basis": sum(s["cost_basis"] for s in short_term),
                "total_gain_loss": sum(s["gain_loss"] for s in short_term)
            },
            "form_8949_part_ii": {  # Long-term
                "description": "Long-term transactions (held more than 1 year)",
                "transactions": long_term,
                "total_proceeds": sum(s["proceeds"] for s in long_term),
                "total_cost_basis": sum(s["cost_basis"] for s in long_term),
                "total_gain_loss": sum(s["gain_loss"] for s in long_term)
            },
            "schedule_d_summary": {
                "short_term_gain_loss": gains["short_term_gain"],
                "long_term_gain_loss": gains["long_term_gain"],
                "net_gain_loss": gains["total_gain"]
            }
        }
    
    def import_from_exchange(
        self,
        exchange_name: str,
        transactions: List[Dict]
    ) -> Tuple[int, int]:
        """
        Import transactions from an exchange.
        
        Args:
            exchange_name: Name of the exchange
            transactions: List of transaction dicts with keys:
                - type: "buy" or "sell"
                - asset: Asset symbol
                - quantity: Amount
                - price: Price per unit
                - date: Transaction date (datetime or ISO string)
                - transaction_id: Optional ID
        
        Returns:
            Tuple of (purchases_imported, sales_imported)
        """
        purchases = 0
        sales = 0
        
        for tx in transactions:
            tx_date = tx["date"]
            if isinstance(tx_date, str):
                tx_date = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))
            
            if tx["type"].lower() == "buy":
                self.add_purchase(
                    asset=tx["asset"],
                    quantity=tx["quantity"],
                    cost_per_unit=tx["price"],
                    purchase_date=tx_date,
                    exchange=exchange_name,
                    transaction_id=tx.get("transaction_id")
                )
                purchases += 1
            
            elif tx["type"].lower() == "sell":
                try:
                    self.record_sale(
                        asset=tx["asset"],
                        quantity=tx["quantity"],
                        sale_price_per_unit=tx["price"],
                        sale_date=tx_date,
                        exchange=exchange_name,
                        transaction_id=tx.get("transaction_id")
                    )
                    sales += 1
                except ValueError as e:
                    logger.warning("Could not record sale: %s", e)
        
        return purchases, sales
    
    def export_to_csv(self, filepath: str, year: int = None):
        """Export tax data to CSV for tax software import."""
        import csv
        
        gains = self.get_realized_gains(year=year)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header matching common tax software formats
            writer.writerow([
                "Description", "Date Acquired", "Date Sold",
                "Proceeds", "Cost Basis", "Gain/Loss", "Term"
            ])
            
            for sale in gains["sales"]:
                # Get acquisition date from lots_used (stored in DB)
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT lots_used FROM sales WHERE sale_id = ?",
                    (sale["sale_id"],)
                )
                lots_data = json.loads(cursor.fetchone()[0])
                acq_date = lots_data[0]["purchase_date"] if lots_data else "Various"
                
                writer.writerow([
                    f"{sale['quantity']} {sale['asset']}",
                    acq_date[:10] if isinstance(acq_date, str) else acq_date,
                    sale["sale_date"][:10],
                    f"{sale['proceeds']:.2f}",
                    f"{sale['cost_basis']:.2f}",
                    f"{sale['gain_loss']:.2f}",
                    "Long-term" if sale["is_long_term"] else "Short-term"
                ])
        
        print(f"Exported {len(gains['sales'])} transactions to {filepath}")
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Cost Basis & Tax Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Holdings command
    holdings_parser = subparsers.add_parser("holdings", help="View current holdings with cost basis")
    
    # Gains command
    gains_parser = subparsers.add_parser("gains", help="View realized gains/losses")
    gains_parser.add_argument("--year", type=int, help="Tax year")
    
    # Tax report command
    tax_parser = subparsers.add_parser("tax", help="Generate tax report")
    tax_parser.add_argument("year", type=int, help="Tax year")
    tax_parser.add_argument("--export", help="Export to CSV file")
    
    # Add purchase command
    buy_parser = subparsers.add_parser("buy", help="Record a purchase")
    buy_parser.add_argument("asset", help="Asset symbol (e.g., BTC)")
    buy_parser.add_argument("quantity", type=float, help="Amount purchased")
    buy_parser.add_argument("price", type=float, help="Price per unit")
    buy_parser.add_argument("--exchange", default="manual", help="Exchange name")
    buy_parser.add_argument("--date", help="Purchase date (YYYY-MM-DD)")
    
    # Add sale command
    sell_parser = subparsers.add_parser("sell", help="Record a sale")
    sell_parser.add_argument("asset", help="Asset symbol")
    sell_parser.add_argument("quantity", type=float, help="Amount sold")
    sell_parser.add_argument("price", type=float, help="Sale price per unit")
    sell_parser.add_argument("--exchange", default="manual", help="Exchange name")
    sell_parser.add_argument("--date", help="Sale date (YYYY-MM-DD)")
    
    # Method command
    method_parser = subparsers.add_parser("method", help="Set accounting method")
    method_parser.add_argument(
        "method",
        choices=["fifo", "lifo", "hifo"],
        help="Accounting method"
    )
    
    args = parser.parse_args()
    
    tracker = CostBasisTracker()
    
    try:
        if args.command == "holdings":
            holdings = tracker.get_current_holdings()
            print("\n📊 Current Holdings with Cost Basis")
            print("=" * 60)
            
            for asset, data in sorted(holdings.items()):
                print(f"\n{asset}:")
                print(f"  Quantity: {data['quantity']:.8f}")
                print(f"  Cost Basis: ${data['total_cost_basis']:,.2f}")
                print(f"  Avg Cost: ${data['average_cost']:,.2f}")
        
        elif args.command == "gains":
            gains = tracker.get_realized_gains(year=args.year)
            year_str = f" ({args.year})" if args.year else ""
            
            print(f"\n💰 Realized Gains/Losses{year_str}")
            print("=" * 60)
            print(f"Short-term: ${gains['short_term_gain']:+,.2f}")
            print(f"Long-term:  ${gains['long_term_gain']:+,.2f}")
            print(f"Total:      ${gains['total_gain']:+,.2f}")
            print(f"\nTransactions: {gains['num_transactions']}")
        
        elif args.command == "tax":
            report = tracker.generate_tax_report(args.year)
            
            print(f"\n📋 Tax Report for {args.year}")
            print("=" * 60)
            
            print("\nForm 8949 Part I (Short-term):")
            print(f"  Proceeds: ${report['form_8949_part_i']['total_proceeds']:,.2f}")
            print(f"  Cost Basis: ${report['form_8949_part_i']['total_cost_basis']:,.2f}")
            print(f"  Gain/Loss: ${report['form_8949_part_i']['total_gain_loss']:+,.2f}")
            
            print("\nForm 8949 Part II (Long-term):")
            print(f"  Proceeds: ${report['form_8949_part_ii']['total_proceeds']:,.2f}")
            print(f"  Cost Basis: ${report['form_8949_part_ii']['total_cost_basis']:,.2f}")
            print(f"  Gain/Loss: ${report['form_8949_part_ii']['total_gain_loss']:+,.2f}")
            
            print("\nSchedule D Summary:")
            print(f"  Net Gain/Loss: ${report['schedule_d_summary']['net_gain_loss']:+,.2f}")
            
            if args.export:
                tracker.export_to_csv(args.export, args.year)
        
        elif args.command == "buy":
            date = datetime.now()
            if args.date:
                date = datetime.strptime(args.date, "%Y-%m-%d")
            
            lot = tracker.add_purchase(
                asset=args.asset,
                quantity=args.quantity,
                cost_per_unit=args.price,
                purchase_date=date,
                exchange=args.exchange
            )
            print(f"✓ Recorded purchase: {args.quantity} {args.asset} @ ${args.price}")
            print(f"  Lot ID: {lot.lot_id}")
        
        elif args.command == "sell":
            date = datetime.now()
            if args.date:
                date = datetime.strptime(args.date, "%Y-%m-%d")
            
            sale = tracker.record_sale(
                asset=args.asset,
                quantity=args.quantity,
                sale_price_per_unit=args.price,
                sale_date=date,
                exchange=args.exchange
            )
            
            term = "Long-term" if sale.is_long_term else "Short-term"
            emoji = "🟢" if sale.gain_loss >= 0 else "🔴"
            
            print(f"✓ Recorded sale: {args.quantity} {args.asset} @ ${args.price}")
            print(f"  {emoji} {term} gain/loss: ${sale.gain_loss:+,.2f}")
        
        elif args.command == "method":
            method = AccountingMethod(args.method)
            tracker.set_accounting_method(method)
            print(f"✓ Accounting method set to {args.method.upper()}")
        
        else:
            parser.print_help()
    
    finally:
        tracker.close()


if __name__ == "__main__":
    main()
