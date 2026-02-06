"""
Transaction History Aggregator
Fetches and aggregates transaction history across all exchanges with cost basis tracking.

Supports:
- Trade history from all 4 exchanges
- CSV/XLSX import from exchange exports (Coinbase, Kraken, Gemini, Crypto.com)
- Cost basis calculation (FIFO, LIFO, HIFO, Average Cost)
- Realized/unrealized gain/loss tracking
- Tax lot tracking
"""

import logging
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Import exchange clients
from exchanges import CoinbaseClient, KrakenClient, CryptoComClient, GeminiClient


class CostBasisMethod(Enum):
    """Cost basis calculation methods."""
    FIFO = "fifo"      # First In, First Out (default for US taxes)
    LIFO = "lifo"      # Last In, First Out
    HIFO = "hifo"      # Highest In, First Out (minimizes gains)
    AVERAGE = "average" # Average cost basis


@dataclass
class Transaction:
    """Normalized transaction record."""
    id: str
    exchange: str
    timestamp: datetime
    type: str  # buy, sell, transfer_in, transfer_out, reward, fee, staking_reward
    asset: str
    amount: float
    price_usd: float  # Price per unit at time of transaction
    total_usd: float  # Total value in USD
    fee_usd: float
    fee_asset: str
    related_asset: str  # For trades, the other side (e.g., USD for BTC buy)
    related_amount: float
    raw_data: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class TaxLot:
    """A tax lot representing a purchase of an asset."""
    id: str
    asset: str
    amount: float
    remaining_amount: float
    cost_basis_per_unit: float
    total_cost_basis: float
    acquired_date: datetime
    exchange: str
    transaction_id: str
    
    @property
    def is_long_term(self) -> bool:
        """Check if lot qualifies for long-term capital gains (held > 1 year)."""
        return (datetime.now() - self.acquired_date).days > 365


@dataclass 
class RealizedGain:
    """Record of a realized gain/loss from selling."""
    asset: str
    sell_date: datetime
    sell_amount: float
    proceeds_usd: float
    cost_basis_usd: float
    gain_loss_usd: float
    is_long_term: bool
    tax_lot_id: str
    sell_transaction_id: str


class TransactionHistory:
    """Aggregates and manages transaction history across exchanges."""
    
    def __init__(self, data_dir: str = None):
        load_dotenv()
        self.clients = {}
        self.transactions: List[Transaction] = []
        self.tax_lots: Dict[str, List[TaxLot]] = {}  # asset -> list of lots
        self.realized_gains: List[RealizedGain] = []
        self.cost_basis_method = CostBasisMethod.FIFO
        
        # Data persistence
        self.data_dir = data_dir or os.path.expanduser("~/.crypto_portfolio")
        os.makedirs(self.data_dir, exist_ok=True)
        
    def connect_exchanges(self) -> int:
        """Connect to all configured exchanges."""
        connected = 0
        
        # Coinbase
        api_key = os.getenv("COINBASE_API_KEY")
        api_secret = os.getenv("COINBASE_API_SECRET")
        if api_key and api_secret:
            self.clients["Coinbase"] = CoinbaseClient(api_key, api_secret)
            connected += 1
        
        # Kraken
        api_key = os.getenv("KRAKEN_API_KEY")
        api_secret = os.getenv("KRAKEN_API_SECRET")
        if api_key and api_secret:
            self.clients["Kraken"] = KrakenClient(api_key, api_secret)
            connected += 1
        
        # Crypto.com
        api_key = os.getenv("CRYPTOCOM_API_KEY")
        api_secret = os.getenv("CRYPTOCOM_API_SECRET")
        if api_key and api_secret:
            self.clients["Crypto.com"] = CryptoComClient(api_key, api_secret)
            connected += 1
        
        # Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        api_secret = os.getenv("GEMINI_API_SECRET")
        if api_key and api_secret:
            self.clients["Gemini"] = GeminiClient(api_key, api_secret)
            connected += 1
        
        return connected
    
    # ==================== FETCH TRANSACTIONS ====================
    
    def fetch_all_history(self, since: datetime = None) -> List[Transaction]:
        """Fetch transaction history from all connected exchanges."""
        print("📜 Fetching transaction history from all exchanges...")
        
        all_transactions = []
        
        for name, client in self.clients.items():
            print(f"  Fetching from {name}...")
            try:
                if name == "Coinbase":
                    txns = self._fetch_coinbase_history(client, since)
                elif name == "Kraken":
                    txns = self._fetch_kraken_history(client, since)
                elif name == "Crypto.com":
                    txns = self._fetch_cryptocom_history(client, since)
                elif name == "Gemini":
                    txns = self._fetch_gemini_history(client, since)
                else:
                    txns = []
                
                all_transactions.extend(txns)
                print(f"    Found {len(txns)} transactions")
                
            except Exception as e:
                logger.warning("Error fetching from %s: %s", name, e)
        
        # Sort by timestamp
        all_transactions.sort(key=lambda x: x.timestamp)
        self.transactions = all_transactions
        
        print(f"\n📊 Total transactions: {len(all_transactions)}")
        return all_transactions
    
    def _fetch_coinbase_history(self, client: CoinbaseClient, since: datetime = None) -> List[Transaction]:
        """Fetch Coinbase transaction history."""
        transactions = []
        
        # Get fills (completed trades)
        fills = client.get_fills(limit=500)
        
        for fill in fills:
            try:
                timestamp = datetime.fromisoformat(fill.get("trade_time", "").replace("Z", "+00:00"))
                
                if since and timestamp < since:
                    continue
                
                product_id = fill.get("product_id", "")
                base_asset = product_id.split("-")[0] if "-" in product_id else product_id
                quote_asset = product_id.split("-")[1] if "-" in product_id else "USD"
                
                side = fill.get("side", "").upper()
                size = float(fill.get("size", 0))
                price = float(fill.get("price", 0))
                fee = float(fill.get("commission", 0))
                
                txn = Transaction(
                    id=fill.get("trade_id", str(time.time())),
                    exchange="Coinbase",
                    timestamp=timestamp,
                    type="buy" if side == "BUY" else "sell",
                    asset=base_asset,
                    amount=size,
                    price_usd=price,
                    total_usd=size * price,
                    fee_usd=fee,
                    fee_asset=quote_asset,
                    related_asset=quote_asset,
                    related_amount=size * price,
                    raw_data=fill
                )
                transactions.append(txn)
                
            except Exception as e:
                logger.warning("Error parsing Coinbase fill: %s", e)
        
        return transactions
    
    def _fetch_kraken_history(self, client: KrakenClient, since: datetime = None) -> List[Transaction]:
        """Fetch Kraken transaction history."""
        transactions = []
        
        # Get trade history
        trades = client.get_trade_history(limit=500)
        
        for trade in trades:
            try:
                timestamp = datetime.fromtimestamp(float(trade.get("time", 0)))
                
                if since and timestamp < since:
                    continue
                
                pair = trade.get("pair", "")
                # Parse Kraken pair format (e.g., XXBTZUSD)
                base_asset = client._denormalize_symbol(pair[:4] if len(pair) >= 6 else pair[:3])
                quote_asset = client._denormalize_symbol(pair[4:] if len(pair) >= 6 else pair[3:])
                
                trade_type = trade.get("type", "")  # buy or sell
                vol = float(trade.get("vol", 0))
                price = float(trade.get("price", 0))
                fee = float(trade.get("fee", 0))
                
                txn = Transaction(
                    id=trade.get("trade_id", str(time.time())),
                    exchange="Kraken",
                    timestamp=timestamp,
                    type=trade_type,
                    asset=base_asset,
                    amount=vol,
                    price_usd=price if "USD" in quote_asset else 0,  # May need conversion
                    total_usd=vol * price if "USD" in quote_asset else 0,
                    fee_usd=fee if "USD" in quote_asset else 0,
                    fee_asset=quote_asset,
                    related_asset=quote_asset,
                    related_amount=vol * price,
                    raw_data=trade
                )
                transactions.append(txn)
                
            except Exception as e:
                logger.warning("Error parsing Kraken trade: %s", e)
        
        return transactions
    
    def _fetch_cryptocom_history(self, client: CryptoComClient, since: datetime = None) -> List[Transaction]:
        """Fetch Crypto.com transaction history."""
        transactions = []
        
        # Get trade history
        trades = client.get_trade_history(limit=100)
        
        for trade in trades:
            try:
                timestamp = datetime.fromtimestamp(float(trade.get("create_time", 0)) / 1000)
                
                if since and timestamp < since:
                    continue
                
                instrument = trade.get("instrument_name", "")
                parts = instrument.split("_")
                base_asset = parts[0] if parts else instrument
                quote_asset = parts[1] if len(parts) > 1 else "USD"
                
                side = trade.get("side", "").lower()
                quantity = float(trade.get("traded_quantity", 0))
                price = float(trade.get("traded_price", 0))
                fee = float(trade.get("fee", 0))
                
                txn = Transaction(
                    id=trade.get("trade_id", str(time.time())),
                    exchange="Crypto.com",
                    timestamp=timestamp,
                    type=side,
                    asset=base_asset,
                    amount=quantity,
                    price_usd=price if quote_asset in ["USD", "USDT", "USDC"] else 0,
                    total_usd=quantity * price if quote_asset in ["USD", "USDT", "USDC"] else 0,
                    fee_usd=fee,
                    fee_asset=trade.get("fee_currency", quote_asset),
                    related_asset=quote_asset,
                    related_amount=quantity * price,
                    raw_data=trade
                )
                transactions.append(txn)
                
            except Exception as e:
                logger.warning("Error parsing Crypto.com trade: %s", e)
        
        return transactions
    
    def _fetch_gemini_history(self, client: GeminiClient, since: datetime = None) -> List[Transaction]:
        """Fetch Gemini transaction history."""
        transactions = []
        
        # Get trade history
        trades = client.get_trade_history(limit=500)
        
        for trade in trades:
            try:
                timestamp = datetime.fromtimestamp(float(trade.get("timestampms", 0)) / 1000)
                
                if since and timestamp < since:
                    continue
                
                symbol = trade.get("symbol", "")
                # Parse Gemini symbol (e.g., btcusd)
                base_asset = symbol[:-3].upper() if len(symbol) >= 6 else symbol[:3].upper()
                quote_asset = symbol[-3:].upper() if len(symbol) >= 6 else "USD"
                
                trade_type = trade.get("type", "").lower()  # Buy or Sell
                amount = float(trade.get("amount", 0))
                price = float(trade.get("price", 0))
                fee = float(trade.get("fee_amount", 0))
                
                txn = Transaction(
                    id=str(trade.get("tid", time.time())),
                    exchange="Gemini",
                    timestamp=timestamp,
                    type=trade_type,
                    asset=base_asset,
                    amount=amount,
                    price_usd=price,
                    total_usd=amount * price,
                    fee_usd=fee,
                    fee_asset=trade.get("fee_currency", quote_asset),
                    related_asset=quote_asset,
                    related_amount=amount * price,
                    raw_data=trade
                )
                transactions.append(txn)
                
            except Exception as e:
                logger.warning("Error parsing Gemini trade: %s", e)
        
        return transactions
    
    # ==================== COST BASIS TRACKING ====================
    
    def build_tax_lots(self):
        """Build tax lots from transaction history."""
        print("\n🧮 Building tax lots...")
        
        self.tax_lots = {}
        lot_counter = 0
        
        for txn in self.transactions:
            if txn.type == "buy" and txn.amount > 0:
                lot_counter += 1
                lot = TaxLot(
                    id=f"LOT-{lot_counter:06d}",
                    asset=txn.asset,
                    amount=txn.amount,
                    remaining_amount=txn.amount,
                    cost_basis_per_unit=txn.price_usd,
                    total_cost_basis=txn.total_usd + txn.fee_usd,
                    acquired_date=txn.timestamp,
                    exchange=txn.exchange,
                    transaction_id=txn.id
                )
                
                if txn.asset not in self.tax_lots:
                    self.tax_lots[txn.asset] = []
                self.tax_lots[txn.asset].append(lot)
        
        print(f"  Created {lot_counter} tax lots across {len(self.tax_lots)} assets")
    
    def calculate_realized_gains(self):
        """Calculate realized gains/losses from sales using selected cost basis method."""
        print(f"\n📈 Calculating realized gains ({self.cost_basis_method.value})...")
        
        self.realized_gains = []
        
        for txn in self.transactions:
            if txn.type != "sell" or txn.amount <= 0:
                continue
            
            asset = txn.asset
            if asset not in self.tax_lots:
                print(f"  Warning: Selling {asset} with no tax lots (possible transfer in)")
                continue
            
            amount_to_sell = txn.amount
            proceeds = txn.total_usd - txn.fee_usd
            
            # Get lots based on cost basis method
            lots = self._get_lots_for_sale(asset)
            
            for lot in lots:
                if amount_to_sell <= 0:
                    break
                
                if lot.remaining_amount <= 0:
                    continue
                
                # Calculate how much to take from this lot
                amount_from_lot = min(amount_to_sell, lot.remaining_amount)
                cost_basis = amount_from_lot * lot.cost_basis_per_unit
                lot_proceeds = (amount_from_lot / txn.amount) * proceeds
                
                gain = RealizedGain(
                    asset=asset,
                    sell_date=txn.timestamp,
                    sell_amount=amount_from_lot,
                    proceeds_usd=lot_proceeds,
                    cost_basis_usd=cost_basis,
                    gain_loss_usd=lot_proceeds - cost_basis,
                    is_long_term=lot.is_long_term,
                    tax_lot_id=lot.id,
                    sell_transaction_id=txn.id
                )
                self.realized_gains.append(gain)
                
                # Update lot
                lot.remaining_amount -= amount_from_lot
                amount_to_sell -= amount_from_lot
        
        total_gains = sum(g.gain_loss_usd for g in self.realized_gains)
        long_term = sum(g.gain_loss_usd for g in self.realized_gains if g.is_long_term)
        short_term = sum(g.gain_loss_usd for g in self.realized_gains if not g.is_long_term)
        
        print(f"  Total realized: ${total_gains:,.2f}")
        print(f"  Long-term: ${long_term:,.2f}")
        print(f"  Short-term: ${short_term:,.2f}")
    
    def _get_lots_for_sale(self, asset: str) -> List[TaxLot]:
        """Get tax lots ordered by cost basis method."""
        lots = self.tax_lots.get(asset, [])
        
        if self.cost_basis_method == CostBasisMethod.FIFO:
            return sorted(lots, key=lambda x: x.acquired_date)
        elif self.cost_basis_method == CostBasisMethod.LIFO:
            return sorted(lots, key=lambda x: x.acquired_date, reverse=True)
        elif self.cost_basis_method == CostBasisMethod.HIFO:
            return sorted(lots, key=lambda x: x.cost_basis_per_unit, reverse=True)
        elif self.cost_basis_method == CostBasisMethod.AVERAGE:
            # For average cost, we recalculate cost basis as weighted average
            return lots
        
        return lots
    
    def get_unrealized_gains(self, current_prices: Dict[str, float]) -> Dict[str, dict]:
        """Calculate unrealized gains for current holdings."""
        unrealized = {}
        
        for asset, lots in self.tax_lots.items():
            remaining_lots = [l for l in lots if l.remaining_amount > 0]
            
            if not remaining_lots:
                continue
            
            total_amount = sum(l.remaining_amount for l in remaining_lots)
            total_cost_basis = sum(l.remaining_amount * l.cost_basis_per_unit for l in remaining_lots)
            current_price = current_prices.get(asset, 0)
            current_value = total_amount * current_price
            
            unrealized[asset] = {
                "amount": total_amount,
                "cost_basis": total_cost_basis,
                "current_value": current_value,
                "unrealized_gain": current_value - total_cost_basis,
                "unrealized_gain_pct": ((current_value / total_cost_basis) - 1) * 100 if total_cost_basis > 0 else 0,
                "lots": len(remaining_lots),
                "avg_cost_basis": total_cost_basis / total_amount if total_amount > 0 else 0
            }
        
        return unrealized
    
    # ==================== TAX REPORTING ====================
    
    def get_tax_summary(self, year: int = None) -> dict:
        """Get tax summary for a given year."""
        if year is None:
            year = datetime.now().year
        
        year_gains = [g for g in self.realized_gains 
                      if g.sell_date.year == year]
        
        long_term_gains = sum(g.gain_loss_usd for g in year_gains if g.is_long_term and g.gain_loss_usd > 0)
        long_term_losses = sum(g.gain_loss_usd for g in year_gains if g.is_long_term and g.gain_loss_usd < 0)
        short_term_gains = sum(g.gain_loss_usd for g in year_gains if not g.is_long_term and g.gain_loss_usd > 0)
        short_term_losses = sum(g.gain_loss_usd for g in year_gains if not g.is_long_term and g.gain_loss_usd < 0)
        
        return {
            "year": year,
            "total_transactions": len(year_gains),
            "long_term": {
                "gains": long_term_gains,
                "losses": long_term_losses,
                "net": long_term_gains + long_term_losses
            },
            "short_term": {
                "gains": short_term_gains,
                "losses": short_term_losses,
                "net": short_term_gains + short_term_losses
            },
            "total_net": long_term_gains + long_term_losses + short_term_gains + short_term_losses
        }
    
    def generate_form_8949(self, year: int = None) -> List[dict]:
        """Generate data for IRS Form 8949 (Capital Gains)."""
        if year is None:
            year = datetime.now().year
        
        year_gains = [g for g in self.realized_gains if g.sell_date.year == year]
        
        form_data = []
        for gain in year_gains:
            form_data.append({
                "description": f"{gain.sell_amount:.8f} {gain.asset}",
                "date_acquired": self._get_acquisition_date(gain.tax_lot_id),
                "date_sold": gain.sell_date.strftime("%m/%d/%Y"),
                "proceeds": round(gain.proceeds_usd, 2),
                "cost_basis": round(gain.cost_basis_usd, 2),
                "gain_or_loss": round(gain.gain_loss_usd, 2),
                "long_term": gain.is_long_term
            })
        
        return form_data
    
    def _get_acquisition_date(self, lot_id: str) -> str:
        """Get acquisition date for a tax lot."""
        for asset, lots in self.tax_lots.items():
            for lot in lots:
                if lot.id == lot_id:
                    return lot.acquired_date.strftime("%m/%d/%Y")
        return "Various"
    
    # ==================== CSV/XLSX IMPORT ====================

    def import_from_files(self, file_paths: List[str], exchange_override: str = None) -> dict:
        """Import transactions from CSV/XLSX export files.

        Uses transaction_import module to parse exchange export files,
        merges with existing transactions, deduplicates, and rebuilds tax lots.

        Args:
            file_paths: List of file paths to import
            exchange_override: Force a specific parser for all files

        Returns:
            Summary dict with import statistics
        """
        from transaction_import import import_all

        new_transactions, summary = import_all(file_paths, exchange_override)

        # Merge with existing transactions
        existing_keys = set()
        for txn in self.transactions:
            key = (
                txn.exchange,
                txn.timestamp.strftime("%Y%m%d%H%M%S"),
                txn.asset,
                f"{txn.amount:.8f}",
                txn.type,
            )
            existing_keys.add(key)

        added = 0
        for txn in new_transactions:
            key = (
                txn.exchange,
                txn.timestamp.strftime("%Y%m%d%H%M%S"),
                txn.asset,
                f"{txn.amount:.8f}",
                txn.type,
            )
            if key not in existing_keys:
                self.transactions.append(txn)
                existing_keys.add(key)
                added += 1

        # Re-sort by timestamp
        self.transactions.sort(key=lambda x: x.timestamp)

        # Rebuild tax lots with merged data
        self.build_tax_lots()
        self.calculate_realized_gains()

        summary["newly_added"] = added
        summary["total_after_merge"] = len(self.transactions)

        return summary

    # ==================== PERSISTENCE ====================

    def save(self):
        """Save transaction history and tax lots to disk."""
        data = {
            "transactions": [t.to_dict() for t in self.transactions],
            "tax_lots": {
                asset: [asdict(lot) for lot in lots]
                for asset, lots in self.tax_lots.items()
            },
            "realized_gains": [asdict(g) for g in self.realized_gains],
            "cost_basis_method": self.cost_basis_method.value,
            "last_updated": datetime.now().isoformat()
        }
        
        # Convert datetime objects in tax_lots
        for asset, lots in data["tax_lots"].items():
            for lot in lots:
                lot["acquired_date"] = lot["acquired_date"].isoformat()
        
        # Convert datetime objects in realized_gains
        for gain in data["realized_gains"]:
            gain["sell_date"] = gain["sell_date"].isoformat()
        
        filepath = os.path.join(self.data_dir, "transaction_history.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved transaction history to {filepath}")
    
    def load(self) -> bool:
        """Load transaction history from disk."""
        filepath = os.path.join(self.data_dir, "transaction_history.json")
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            self.transactions = [Transaction.from_dict(t) for t in data.get("transactions", [])]
            
            self.tax_lots = {}
            for asset, lots in data.get("tax_lots", {}).items():
                self.tax_lots[asset] = []
                for lot_data in lots:
                    lot_data["acquired_date"] = datetime.fromisoformat(lot_data["acquired_date"])
                    self.tax_lots[asset].append(TaxLot(**lot_data))
            
            self.realized_gains = []
            for gain_data in data.get("realized_gains", []):
                gain_data["sell_date"] = datetime.fromisoformat(gain_data["sell_date"])
                self.realized_gains.append(RealizedGain(**gain_data))
            
            method = data.get("cost_basis_method", "fifo")
            self.cost_basis_method = CostBasisMethod(method)
            
            print(f"📂 Loaded {len(self.transactions)} transactions from {filepath}")
            return True
            
        except Exception as e:
            logger.warning("Error loading transaction history: %s", e)
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Transaction History & Cost Basis Tracker")
    parser.add_argument("--fetch", action="store_true", help="Fetch new transactions from exchanges")
    parser.add_argument("--since", type=str, help="Fetch transactions since date (YYYY-MM-DD)")
    parser.add_argument("--method", choices=["fifo", "lifo", "hifo", "average"], 
                        default="fifo", help="Cost basis method")
    parser.add_argument("--tax-year", type=int, help="Generate tax summary for year")
    parser.add_argument("--form-8949", action="store_true", help="Generate Form 8949 data")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📜 TRANSACTION HISTORY & COST BASIS TRACKER")
    print("=" * 60)
    
    history = TransactionHistory()
    history.cost_basis_method = CostBasisMethod(args.method)
    
    # Try to load existing data
    history.load()
    
    if args.fetch:
        connected = history.connect_exchanges()
        print(f"\nConnected to {connected} exchange(s)")
        
        since = None
        if args.since:
            since = datetime.strptime(args.since, "%Y-%m-%d")
        
        history.fetch_all_history(since)
        history.build_tax_lots()
        history.calculate_realized_gains()
        history.save()
    
    if args.tax_year or args.form_8949:
        year = args.tax_year or datetime.now().year
        
        print(f"\n📋 TAX SUMMARY FOR {year}")
        print("-" * 40)
        summary = history.get_tax_summary(year)
        
        print(f"Total transactions: {summary['total_transactions']}")
        print(f"\nLong-term capital gains/losses:")
        print(f"  Gains:  ${summary['long_term']['gains']:,.2f}")
        print(f"  Losses: ${summary['long_term']['losses']:,.2f}")
        print(f"  Net:    ${summary['long_term']['net']:,.2f}")
        print(f"\nShort-term capital gains/losses:")
        print(f"  Gains:  ${summary['short_term']['gains']:,.2f}")
        print(f"  Losses: ${summary['short_term']['losses']:,.2f}")
        print(f"  Net:    ${summary['short_term']['net']:,.2f}")
        print(f"\n💰 TOTAL NET: ${summary['total_net']:,.2f}")
        
        if args.form_8949:
            print(f"\n📄 FORM 8949 DATA")
            print("-" * 40)
            form_data = history.generate_form_8949(year)
            for row in form_data[:10]:  # Show first 10
                print(f"  {row['description']}: {row['date_acquired']} -> {row['date_sold']}")
                print(f"    Proceeds: ${row['proceeds']:,.2f}, Cost: ${row['cost_basis']:,.2f}, Gain: ${row['gain_or_loss']:,.2f}")


if __name__ == "__main__":
    main()
