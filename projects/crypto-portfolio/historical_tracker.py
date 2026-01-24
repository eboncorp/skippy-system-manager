"""
Historical Portfolio Tracker
Track portfolio value over time with database storage and visualization.

Features:
- Automatic snapshots on schedule
- Historical value charts
- Performance analytics
- Comparison vs benchmarks (BTC, ETH, S&P 500)
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path
import schedule
import time


@dataclass
class PortfolioSnapshot:
    """A point-in-time snapshot of portfolio value."""
    timestamp: datetime
    total_value_usd: float
    holdings: Dict[str, Dict]  # {asset: {balance, price, value}}
    exchange_breakdown: Dict[str, float]  # {exchange: value}
    staked_value: float = 0
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_value_usd": self.total_value_usd,
            "holdings": self.holdings,
            "exchange_breakdown": self.exchange_breakdown,
            "staked_value": self.staked_value
        }


class HistoricalTracker:
    """Track and store historical portfolio data."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "data",
                "portfolio_history.db"
            )
        
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        cursor = self.conn.cursor()
        
        # Main snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_value_usd REAL NOT NULL,
                staked_value REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Holdings per snapshot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                asset TEXT NOT NULL,
                balance REAL NOT NULL,
                price REAL,
                value_usd REAL,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
            )
        """)
        
        # Exchange breakdown per snapshot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_exchanges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                exchange TEXT NOT NULL,
                value_usd REAL NOT NULL,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
            )
        """)
        
        # Benchmark prices for comparison
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                btc_price REAL,
                eth_price REAL,
                sp500_price REAL
            )
        """)
        
        # Indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_holdings_snapshot ON snapshot_holdings(snapshot_id)"
        )
        
        self.conn.commit()
    
    def save_snapshot(self, snapshot: PortfolioSnapshot) -> int:
        """Save a portfolio snapshot to the database."""
        cursor = self.conn.cursor()
        
        # Insert main snapshot
        cursor.execute("""
            INSERT INTO snapshots (timestamp, total_value_usd, staked_value)
            VALUES (?, ?, ?)
        """, (
            snapshot.timestamp.isoformat(),
            snapshot.total_value_usd,
            snapshot.staked_value
        ))
        
        snapshot_id = cursor.lastrowid
        
        # Insert holdings
        for asset, data in snapshot.holdings.items():
            cursor.execute("""
                INSERT INTO snapshot_holdings 
                (snapshot_id, asset, balance, price, value_usd)
                VALUES (?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                asset,
                data.get("balance", 0),
                data.get("price", 0),
                data.get("value", 0)
            ))
        
        # Insert exchange breakdown
        for exchange, value in snapshot.exchange_breakdown.items():
            cursor.execute("""
                INSERT INTO snapshot_exchanges (snapshot_id, exchange, value_usd)
                VALUES (?, ?, ?)
            """, (snapshot_id, exchange, value))
        
        self.conn.commit()
        return snapshot_id
    
    def get_snapshots(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = None
    ) -> List[PortfolioSnapshot]:
        """Retrieve historical snapshots."""
        cursor = self.conn.cursor()
        
        query = "SELECT id, timestamp, total_value_usd, staked_value FROM snapshots WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        
        snapshots = []
        for row in cursor.fetchall():
            snapshot_id, timestamp, total_value, staked_value = row
            
            # Get holdings
            cursor.execute("""
                SELECT asset, balance, price, value_usd
                FROM snapshot_holdings WHERE snapshot_id = ?
            """, (snapshot_id,))
            
            holdings = {}
            for h_row in cursor.fetchall():
                holdings[h_row[0]] = {
                    "balance": h_row[1],
                    "price": h_row[2],
                    "value": h_row[3]
                }
            
            # Get exchange breakdown
            cursor.execute("""
                SELECT exchange, value_usd
                FROM snapshot_exchanges WHERE snapshot_id = ?
            """, (snapshot_id,))
            
            exchange_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
            
            snapshots.append(PortfolioSnapshot(
                timestamp=datetime.fromisoformat(timestamp),
                total_value_usd=total_value,
                holdings=holdings,
                exchange_breakdown=exchange_breakdown,
                staked_value=staked_value
            ))
        
        return snapshots
    
    def get_latest_snapshot(self) -> Optional[PortfolioSnapshot]:
        """Get the most recent snapshot."""
        snapshots = self.get_snapshots(limit=1)
        return snapshots[0] if snapshots else None
    
    def get_value_history(
        self,
        days: int = 30,
        interval: str = "daily"  # "hourly", "daily", "weekly"
    ) -> List[Tuple[datetime, float]]:
        """Get portfolio value history for charting."""
        cursor = self.conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Group by interval
        if interval == "hourly":
            group_format = "%Y-%m-%d %H:00:00"
        elif interval == "weekly":
            group_format = "%Y-%W"
        else:  # daily
            group_format = "%Y-%m-%d"
        
        cursor.execute("""
            SELECT strftime(?, timestamp) as period,
                   AVG(total_value_usd) as avg_value,
                   MAX(timestamp) as latest_timestamp
            FROM snapshots
            WHERE timestamp >= ?
            GROUP BY period
            ORDER BY period
        """, (group_format, start_date.isoformat()))
        
        history = []
        for row in cursor.fetchall():
            period, avg_value, latest_ts = row
            # Parse timestamp for the period
            if interval == "weekly":
                # Weekly format is different
                ts = datetime.strptime(latest_ts, "%Y-%m-%dT%H:%M:%S.%f") if "." in latest_ts else datetime.fromisoformat(latest_ts)
            else:
                ts = datetime.fromisoformat(latest_ts) if latest_ts else datetime.now()
            history.append((ts, avg_value))
        
        return history
    
    def get_performance_stats(
        self,
        days: int = 30
    ) -> Dict:
        """Calculate performance statistics."""
        snapshots = self.get_snapshots(
            start_date=datetime.now() - timedelta(days=days)
        )
        
        if len(snapshots) < 2:
            return {"error": "Insufficient data for analysis"}
        
        # Sort by timestamp (oldest first)
        snapshots.sort(key=lambda x: x.timestamp)
        
        values = [s.total_value_usd for s in snapshots]
        
        start_value = values[0]
        end_value = values[-1]
        max_value = max(values)
        min_value = min(values)
        
        # Calculate returns
        total_return = end_value - start_value
        total_return_pct = (total_return / start_value * 100) if start_value > 0 else 0
        
        # Calculate max drawdown
        peak = values[0]
        max_drawdown = 0
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # Daily returns for volatility
        daily_returns = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                daily_returns.append((values[i] - values[i-1]) / values[i-1])
        
        # Volatility (standard deviation of returns)
        if daily_returns:
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = variance ** 0.5 * 100
        else:
            volatility = 0
        
        return {
            "period_days": days,
            "start_value": start_value,
            "end_value": end_value,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "max_value": max_value,
            "min_value": min_value,
            "max_drawdown_pct": max_drawdown,
            "volatility_pct": volatility,
            "num_snapshots": len(snapshots)
        }
    
    def get_asset_performance(
        self,
        asset: str,
        days: int = 30
    ) -> Dict:
        """Get performance stats for a specific asset."""
        cursor = self.conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT s.timestamp, h.balance, h.price, h.value_usd
            FROM snapshots s
            JOIN snapshot_holdings h ON s.id = h.snapshot_id
            WHERE h.asset = ? AND s.timestamp >= ?
            ORDER BY s.timestamp
        """, (asset, start_date.isoformat()))
        
        data = cursor.fetchall()
        
        if len(data) < 2:
            return {"error": f"Insufficient data for {asset}"}
        
        start_balance = data[0][1]
        end_balance = data[-1][1]
        start_price = data[0][2]
        end_price = data[-1][2]
        
        price_change = ((end_price - start_price) / start_price * 100) if start_price else 0
        balance_change = end_balance - start_balance
        
        return {
            "asset": asset,
            "period_days": days,
            "start_balance": start_balance,
            "end_balance": end_balance,
            "balance_change": balance_change,
            "start_price": start_price,
            "end_price": end_price,
            "price_change_pct": price_change
        }
    
    def generate_chart(
        self,
        days: int = 30,
        output_path: str = None,
        show: bool = True
    ) -> Optional[str]:
        """Generate portfolio value chart."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError:
            print("matplotlib not installed. Run: pip install matplotlib")
            return None
        
        history = self.get_value_history(days=days)
        
        if not history:
            print("No historical data available")
            return None
        
        dates = [h[0] for h in history]
        values = [h[1] for h in history]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot
        ax.plot(dates, values, 'b-', linewidth=2)
        ax.fill_between(dates, values, alpha=0.3)
        
        # Formatting
        ax.set_title(f'Portfolio Value - Last {days} Days', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value (USD)')
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add stats annotation
        stats = self.get_performance_stats(days)
        if "error" not in stats:
            stats_text = f"Return: ${stats['total_return']:+,.0f} ({stats['total_return_pct']:+.1f}%)\n"
            stats_text += f"Max Drawdown: {stats['max_drawdown_pct']:.1f}%"
            
            ax.annotate(
                stats_text,
                xy=(0.02, 0.98),
                xycoords='axes fraction',
                verticalalignment='top',
                fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
        
        plt.tight_layout()
        
        # Save or show
        if output_path:
            plt.savefig(output_path, dpi=150)
            print(f"Chart saved to {output_path}")
        
        if show:
            plt.show()
        
        plt.close()
        
        return output_path
    
    def generate_allocation_chart(
        self,
        output_path: str = None,
        show: bool = True
    ) -> Optional[str]:
        """Generate asset allocation pie chart."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not installed")
            return None
        
        latest = self.get_latest_snapshot()
        if not latest:
            print("No snapshot data available")
            return None
        
        # Get top assets
        holdings = sorted(
            latest.holdings.items(),
            key=lambda x: x[1].get("value", 0),
            reverse=True
        )
        
        # Combine small holdings into "Other"
        threshold = latest.total_value_usd * 0.02  # 2% threshold
        main_holdings = []
        other_value = 0
        
        for asset, data in holdings:
            value = data.get("value", 0)
            if value >= threshold:
                main_holdings.append((asset, value))
            else:
                other_value += value
        
        if other_value > 0:
            main_holdings.append(("Other", other_value))
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = [h[0] for h in main_holdings]
        sizes = [h[1] for h in main_holdings]
        
        # Colors
        colors = plt.cm.Set3(range(len(main_holdings)))
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
            colors=colors,
            startangle=90
        )
        
        ax.set_title(
            f'Portfolio Allocation\nTotal: ${latest.total_value_usd:,.0f}',
            fontsize=14,
            fontweight='bold'
        )
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150)
            print(f"Chart saved to {output_path}")
        
        if show:
            plt.show()
        
        plt.close()
        
        return output_path
    
    def cleanup_old_data(self, keep_days: int = 365):
        """Remove snapshots older than specified days."""
        cursor = self.conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        # Get snapshot IDs to delete
        cursor.execute("""
            SELECT id FROM snapshots WHERE timestamp < ?
        """, (cutoff.isoformat(),))
        
        ids_to_delete = [row[0] for row in cursor.fetchall()]
        
        if ids_to_delete:
            # Delete related records
            cursor.execute("""
                DELETE FROM snapshot_holdings WHERE snapshot_id IN ({})
            """.format(",".join("?" * len(ids_to_delete))), ids_to_delete)
            
            cursor.execute("""
                DELETE FROM snapshot_exchanges WHERE snapshot_id IN ({})
            """.format(",".join("?" * len(ids_to_delete))), ids_to_delete)
            
            # Delete snapshots
            cursor.execute("""
                DELETE FROM snapshots WHERE id IN ({})
            """.format(",".join("?" * len(ids_to_delete))), ids_to_delete)
            
            self.conn.commit()
            print(f"Deleted {len(ids_to_delete)} old snapshots")
    
    def close(self):
        """Close database connection."""
        self.conn.close()


class SnapshotScheduler:
    """Schedule automatic portfolio snapshots."""
    
    def __init__(
        self,
        tracker: HistoricalTracker,
        portfolio_fetcher  # Callable that returns PortfolioSnapshot
    ):
        self.tracker = tracker
        self.portfolio_fetcher = portfolio_fetcher
        self.running = False
    
    def take_snapshot(self):
        """Take a snapshot now."""
        try:
            snapshot = self.portfolio_fetcher()
            if snapshot:
                snapshot_id = self.tracker.save_snapshot(snapshot)
                print(f"[{datetime.now()}] Snapshot saved (ID: {snapshot_id})")
                print(f"  Total value: ${snapshot.total_value_usd:,.2f}")
            else:
                print(f"[{datetime.now()}] Failed to get portfolio data")
        except Exception as e:
            print(f"[{datetime.now()}] Snapshot error: {e}")
    
    def schedule_snapshots(
        self,
        interval_hours: int = 1,
        daily_time: str = None  # e.g., "09:00" for daily at 9 AM
    ):
        """Configure snapshot schedule."""
        if daily_time:
            schedule.every().day.at(daily_time).do(self.take_snapshot)
            print(f"Scheduled daily snapshot at {daily_time}")
        else:
            schedule.every(interval_hours).hours.do(self.take_snapshot)
            print(f"Scheduled snapshot every {interval_hours} hour(s)")
    
    def run(self, take_immediate: bool = True):
        """Run the scheduler."""
        if take_immediate:
            self.take_snapshot()
        
        self.running = True
        print("Snapshot scheduler running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            self.running = False
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False


# Integration with MultiExchangeAnalyzer
def create_snapshot_from_analyzer(analyzer) -> PortfolioSnapshot:
    """
    Create a PortfolioSnapshot from MultiExchangeAnalyzer data.
    
    Args:
        analyzer: A MultiExchangeAnalyzer instance that has fetched data
    
    Returns:
        PortfolioSnapshot
    """
    # Calculate totals
    total_value = sum(
        h["total_usd_value"]
        for h in analyzer.aggregated_holdings.values()
    )
    
    # Build holdings dict
    holdings = {}
    for asset, data in analyzer.aggregated_holdings.items():
        holdings[asset] = {
            "balance": data["total_balance"],
            "price": data.get("price", 0),
            "value": data["total_usd_value"]
        }
    
    # Build exchange breakdown
    exchange_breakdown = {}
    for exchange, exchange_holdings in analyzer.holdings_by_exchange.items():
        exchange_breakdown[exchange] = sum(
            h["usd_value"] for h in exchange_holdings.values()
        )
    
    # Calculate staked value
    staked_value = sum(
        data.get("staked_usd_value", 0)
        for data in analyzer.aggregated_holdings.values()
    )
    
    return PortfolioSnapshot(
        timestamp=datetime.now(),
        total_value_usd=total_value,
        holdings=holdings,
        exchange_breakdown=exchange_breakdown,
        staked_value=staked_value
    )


# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Historical Portfolio Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show performance stats")
    stats_parser.add_argument("--days", "-d", type=int, default=30, help="Period in days")
    
    # Chart command
    chart_parser = subparsers.add_parser("chart", help="Generate portfolio chart")
    chart_parser.add_argument("--days", "-d", type=int, default=30, help="Period in days")
    chart_parser.add_argument("--output", "-o", help="Output file path")
    chart_parser.add_argument("--no-show", action="store_true", help="Don't display chart")
    
    # Allocation command
    alloc_parser = subparsers.add_parser("allocation", help="Show allocation chart")
    alloc_parser.add_argument("--output", "-o", help="Output file path")
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show value history")
    history_parser.add_argument("--days", "-d", type=int, default=7, help="Period in days")
    
    # Snapshot command
    snap_parser = subparsers.add_parser("snapshot", help="Take a snapshot now")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove old data")
    cleanup_parser.add_argument("--keep-days", type=int, default=365, help="Days to keep")
    
    args = parser.parse_args()
    
    tracker = HistoricalTracker()
    
    try:
        if args.command == "stats":
            stats = tracker.get_performance_stats(args.days)
            
            if "error" in stats:
                print(f"Error: {stats['error']}")
                return
            
            print(f"\n📈 Portfolio Performance ({args.days} days)")
            print("=" * 50)
            print(f"Start Value:    ${stats['start_value']:,.2f}")
            print(f"End Value:      ${stats['end_value']:,.2f}")
            print(f"Total Return:   ${stats['total_return']:+,.2f} ({stats['total_return_pct']:+.2f}%)")
            print(f"Max Value:      ${stats['max_value']:,.2f}")
            print(f"Min Value:      ${stats['min_value']:,.2f}")
            print(f"Max Drawdown:   {stats['max_drawdown_pct']:.2f}%")
            print(f"Volatility:     {stats['volatility_pct']:.2f}%")
            print(f"Data Points:    {stats['num_snapshots']}")
        
        elif args.command == "chart":
            tracker.generate_chart(
                days=args.days,
                output_path=args.output,
                show=not args.no_show
            )
        
        elif args.command == "allocation":
            tracker.generate_allocation_chart(
                output_path=args.output,
                show=True
            )
        
        elif args.command == "history":
            history = tracker.get_value_history(days=args.days)
            
            print(f"\n📊 Portfolio Value History ({args.days} days)")
            print("=" * 50)
            
            for timestamp, value in history[-20:]:  # Show last 20
                print(f"  {timestamp.strftime('%Y-%m-%d %H:%M')}: ${value:,.2f}")
        
        elif args.command == "snapshot":
            # This requires the analyzer to be set up
            print("To take a snapshot, use the integrated scheduler.")
            print("Example:")
            print("  from historical_tracker import HistoricalTracker, create_snapshot_from_analyzer")
            print("  from multi_exchange_analyzer import MultiExchangeAnalyzer")
            print("")
            print("  analyzer = MultiExchangeAnalyzer()")
            print("  analyzer.connect_all()")
            print("  analyzer.fetch_all_holdings()")
            print("")
            print("  tracker = HistoricalTracker()")
            print("  snapshot = create_snapshot_from_analyzer(analyzer)")
            print("  tracker.save_snapshot(snapshot)")
        
        elif args.command == "cleanup":
            tracker.cleanup_old_data(args.keep_days)
        
        else:
            # Default: show recent stats
            latest = tracker.get_latest_snapshot()
            if latest:
                print(f"\n📊 Latest Snapshot")
                print("=" * 50)
                print(f"Time: {latest.timestamp}")
                print(f"Total Value: ${latest.total_value_usd:,.2f}")
                print(f"Staked: ${latest.staked_value:,.2f}")
                print(f"Assets: {len(latest.holdings)}")
            else:
                print("No snapshots found. Take your first snapshot to start tracking.")
    
    finally:
        tracker.close()


if __name__ == "__main__":
    main()
