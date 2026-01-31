"""
Transaction History Aggregator
Fetches and normalizes transaction history from all exchanges and on-chain sources.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from database import (
    get_db, Transaction, TransactionType, SourceType, AssetType,
    DatabaseManager
)
from logging_config import get_logger

logger = get_logger("transactions")


class TransactionAggregator:
    """Aggregates transactions from all sources into unified format."""
    
    def __init__(self):
        load_dotenv()
        self.db = get_db()
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """Initialize exchange clients."""
        # Coinbase
        coinbase_key = os.getenv("COINBASE_API_KEY")
        coinbase_secret = os.getenv("COINBASE_API_SECRET")
        if coinbase_key and coinbase_secret:
            from exchanges import CoinbaseClient
            self.clients["coinbase"] = CoinbaseClient(coinbase_key, coinbase_secret)
            logger.info("Coinbase client initialized")

        # Kraken
        kraken_key = os.getenv("KRAKEN_API_KEY")
        kraken_secret = os.getenv("KRAKEN_API_SECRET")
        if kraken_key and kraken_secret:
            from exchanges import KrakenClient
            self.clients["kraken"] = KrakenClient(kraken_key, kraken_secret)
            logger.info("Kraken client initialized")

        # Crypto.com
        cryptocom_key = os.getenv("CRYPTOCOM_API_KEY")
        cryptocom_secret = os.getenv("CRYPTOCOM_API_SECRET")
        if cryptocom_key and cryptocom_secret:
            from exchanges import CryptoComClient
            self.clients["cryptocom"] = CryptoComClient(cryptocom_key, cryptocom_secret)
            logger.info("Crypto.com client initialized")

        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        gemini_secret = os.getenv("GEMINI_API_SECRET")
        if gemini_key and gemini_secret:
            from exchanges import GeminiClient
            self.clients["gemini"] = GeminiClient(gemini_key, gemini_secret)
            logger.info("Gemini client initialized")
    
    def sync_all(self, full_sync: bool = False) -> Dict[str, int]:
        """
        Sync transactions from all sources.
        
        Args:
            full_sync: If True, fetch all available history. If False, incremental.
        
        Returns:
            Dict of source -> number of new transactions
        """
        results = {}
        
        for source_name, client in self.clients.items():
            try:
                logger.info(f"Syncing {source_name}...")
                count = self._sync_exchange(source_name, client, full_sync)
                results[source_name] = count
                logger.info(f"Synced {count} new transactions from {source_name}")
            except Exception as e:
                logger.error(f"Error syncing {source_name}: {e}")
                results[source_name] = -1
        
        return results
    
    def _sync_exchange(self, name: str, client, full_sync: bool) -> int:
        """Sync transactions from a specific exchange."""
        source = SourceType(name.lower().replace(".", ""))
        
        if name == "coinbase":
            return self._sync_coinbase(client, source, full_sync)
        elif name == "kraken":
            return self._sync_kraken(client, source, full_sync)
        elif name == "cryptocom":
            return self._sync_cryptocom(client, source, full_sync)
        elif name == "gemini":
            return self._sync_gemini(client, source, full_sync)
        
        return 0
    
    def _sync_coinbase(self, client, source: SourceType, full_sync: bool) -> int:
        """Sync Coinbase transactions."""
        new_count = 0
        
        # Get fills (completed trades)
        fills = client.get_fills(limit=1000 if full_sync else 100)
        
        for fill in fills:
            source_id = fill.get("trade_id") or fill.get("order_id")
            
            if self.db.transaction_exists(source, str(source_id)):
                continue
            
            # Parse the fill
            product_id = fill.get("product_id", "")
            parts = product_id.split("-")
            base_asset = parts[0] if parts else "UNKNOWN"
            quote_asset = parts[1] if len(parts) > 1 else "USD"
            
            side = fill.get("side", "").upper()
            tx_type = TransactionType.BUY if side == "BUY" else TransactionType.SELL
            
            size = float(fill.get("size", 0))
            price = float(fill.get("price", 0))
            fee = float(fill.get("commission", 0))
            
            timestamp = fill.get("trade_time")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            
            self.db.add_transaction(
                source=source,
                source_id=str(source_id),
                type=tx_type,
                timestamp=timestamp or datetime.now(timezone.utc),
                asset=base_asset,
                amount=size,
                price_usd=price,
                value_usd=size * price,
                counter_asset=quote_asset,
                counter_amount=size * price,
                fee_amount=fee,
                fee_asset=quote_asset,
                fee_usd=fee,
                raw_data=str(fill)
            )
            new_count += 1
        
        return new_count
    
    def _sync_kraken(self, client, source: SourceType, full_sync: bool) -> int:
        """Sync Kraken transactions."""
        new_count = 0
        
        # Get trade history
        trades = client.get_trade_history(limit=1000 if full_sync else 100)
        
        for trade in trades:
            trade_id = trade.get("trade_id", "")
            
            if self.db.transaction_exists(source, str(trade_id)):
                continue
            
            pair = trade.get("pair", "")
            tx_type_str = trade.get("type", "buy")
            tx_type = TransactionType.BUY if tx_type_str == "buy" else TransactionType.SELL
            
            vol = float(trade.get("vol", 0))
            price = float(trade.get("price", 0))
            fee = float(trade.get("fee", 0))
            timestamp = float(trade.get("time", 0))
            
            # Parse pair (e.g., XXBTZUSD -> XBT, USD)
            base_asset = client._denormalize_symbol(pair[:len(pair)//2])
            quote_asset = client._denormalize_symbol(pair[len(pair)//2:])
            
            self.db.add_transaction(
                source=source,
                source_id=str(trade_id),
                type=tx_type,
                timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
                asset=base_asset,
                amount=vol,
                price_usd=price,
                value_usd=vol * price,
                counter_asset=quote_asset,
                counter_amount=vol * price,
                fee_amount=fee,
                fee_asset=quote_asset,
                fee_usd=fee,
                raw_data=str(trade)
            )
            new_count += 1
        
        return new_count
    
    def _sync_cryptocom(self, client, source: SourceType, full_sync: bool) -> int:
        """Sync Crypto.com transactions."""
        new_count = 0
        
        trades = client.get_trade_history(limit=1000 if full_sync else 100)
        
        for trade in trades:
            trade_id = trade.get("trade_id", "")
            
            if self.db.transaction_exists(source, str(trade_id)):
                continue
            
            instrument = trade.get("instrument_name", "")
            parts = instrument.split("_")
            base_asset = parts[0] if parts else "UNKNOWN"
            quote_asset = parts[1] if len(parts) > 1 else "USD"
            
            side = trade.get("side", "BUY").upper()
            tx_type = TransactionType.BUY if side == "BUY" else TransactionType.SELL
            
            quantity = float(trade.get("traded_quantity", 0))
            price = float(trade.get("traded_price", 0))
            fee = float(trade.get("fee", 0))
            timestamp = trade.get("create_time", 0) / 1000  # milliseconds to seconds
            
            self.db.add_transaction(
                source=source,
                source_id=str(trade_id),
                type=tx_type,
                timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
                asset=base_asset,
                amount=quantity,
                price_usd=price,
                value_usd=quantity * price,
                counter_asset=quote_asset,
                counter_amount=quantity * price,
                fee_amount=fee,
                fee_asset=quote_asset,
                raw_data=str(trade)
            )
            new_count += 1
        
        return new_count
    
    def _sync_gemini(self, client, source: SourceType, full_sync: bool) -> int:
        """Sync Gemini transactions."""
        new_count = 0
        
        trades = client.get_trade_history(limit=500 if full_sync else 100)
        
        for trade in trades:
            trade_id = trade.get("tid", "")
            
            if self.db.transaction_exists(source, str(trade_id)):
                continue
            
            symbol = trade.get("symbol", "")
            # Parse symbol (e.g., "btcusd" -> BTC, USD)
            if len(symbol) >= 6:
                base_asset = symbol[:-3].upper()
                quote_asset = symbol[-3:].upper()
            else:
                base_asset = symbol.upper()
                quote_asset = "USD"
            
            tx_type_str = trade.get("type", "Buy")
            tx_type = TransactionType.BUY if tx_type_str.lower() == "buy" else TransactionType.SELL
            
            amount = float(trade.get("amount", 0))
            price = float(trade.get("price", 0))
            fee = float(trade.get("fee_amount", 0))
            timestamp = trade.get("timestampms", 0) / 1000
            
            self.db.add_transaction(
                source=source,
                source_id=str(trade_id),
                type=tx_type,
                timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
                asset=base_asset,
                amount=amount,
                price_usd=price,
                value_usd=amount * price,
                counter_asset=quote_asset,
                counter_amount=amount * price,
                fee_amount=fee,
                fee_asset=trade.get("fee_currency", quote_asset),
                raw_data=str(trade)
            )
            new_count += 1
        
        return new_count
    
    def get_all_transactions(
        self,
        asset: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        tx_type: TransactionType = None,
        source: SourceType = None,
        limit: int = None
    ) -> List[Transaction]:
        """Get transactions with optional filters."""
        return self.db.get_transactions(
            asset=asset,
            source=source,
            start_date=start_date,
            end_date=end_date,
            tx_type=tx_type,
            limit=limit
        )
    
    def get_transaction_summary(self) -> Dict[str, Any]:
        """Get summary of all transactions."""
        session = self.db.get_session()
        try:
            from sqlalchemy import func
            
            # Total counts by source
            source_counts = session.query(
                Transaction.source,
                func.count(Transaction.id)
            ).group_by(Transaction.source).all()
            
            # Total counts by type
            type_counts = session.query(
                Transaction.type,
                func.count(Transaction.id)
            ).group_by(Transaction.type).all()
            
            # Date range
            first_tx = session.query(
                func.min(Transaction.timestamp)
            ).scalar()
            
            last_tx = session.query(
                func.max(Transaction.timestamp)
            ).scalar()
            
            # Total volume
            total_volume = session.query(
                func.sum(Transaction.value_usd)
            ).scalar() or 0
            
            return {
                "by_source": {s.value: c for s, c in source_counts},
                "by_type": {t.value: c for t, c in type_counts},
                "first_transaction": first_tx,
                "last_transaction": last_tx,
                "total_volume_usd": total_volume,
                "total_transactions": sum(c for _, c in source_counts)
            }
        finally:
            session.close()
    
    def export_transactions(
        self,
        format: str = "csv",
        filepath: str = None,
        **filters
    ) -> str:
        """Export transactions to file."""
        import pandas as pd
        
        transactions = self.get_all_transactions(**filters)
        
        data = []
        for tx in transactions:
            data.append({
                "Date": tx.timestamp.isoformat(),
                "Type": tx.type.value,
                "Asset": tx.asset,
                "Amount": tx.amount,
                "Price (USD)": tx.price_usd,
                "Value (USD)": tx.value_usd,
                "Fee": tx.fee_amount,
                "Fee Asset": tx.fee_asset,
                "Source": tx.source.value,
                "TX ID": tx.source_id
            })
        
        df = pd.DataFrame(data)
        
        if filepath is None:
            filepath = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        if format == "csv":
            df.to_csv(filepath, index=False)
        elif format == "excel":
            df.to_excel(filepath, index=False)
        elif format == "json":
            df.to_json(filepath, orient="records", indent=2)
        
        logger.info(f"Exported {len(data)} transactions to {filepath}")
        return filepath


def main():
    """CLI for transaction aggregator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Transaction History Aggregator")
    parser.add_argument("--sync", action="store_true", help="Sync transactions from exchanges")
    parser.add_argument("--full", action="store_true", help="Full sync (all history)")
    parser.add_argument("--summary", action="store_true", help="Show transaction summary")
    parser.add_argument("--export", choices=["csv", "excel", "json"], help="Export format")
    parser.add_argument("--asset", help="Filter by asset")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    aggregator = TransactionAggregator()
    
    if args.sync:
        print("Syncing transactions from all exchanges...")
        results = aggregator.sync_all(full_sync=args.full)
        print("\nSync Results:")
        for source, count in results.items():
            status = f"{count} new" if count >= 0 else "ERROR"
            print(f"  {source}: {status}")
    
    if args.summary:
        summary = aggregator.get_transaction_summary()
        print("\n📊 Transaction Summary")
        print("=" * 50)
        print(f"Total Transactions: {summary['total_transactions']:,}")
        print(f"Total Volume: ${summary['total_volume_usd']:,.2f}")
        print(f"First Transaction: {summary['first_transaction']}")
        print(f"Last Transaction: {summary['last_transaction']}")
        print("\nBy Source:")
        for source, count in summary['by_source'].items():
            print(f"  {source}: {count:,}")
        print("\nBy Type:")
        for tx_type, count in summary['by_type'].items():
            print(f"  {tx_type}: {count:,}")
    
    if args.export:
        filepath = aggregator.export_transactions(
            format=args.export,
            filepath=args.output,
            asset=args.asset
        )
        print(f"\nExported to: {filepath}")


if __name__ == "__main__":
    main()
