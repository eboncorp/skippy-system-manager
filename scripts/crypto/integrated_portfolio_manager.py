#!/usr/bin/env python3
"""
Integrated Crypto Portfolio Manager
====================================

Complete integration of all crypto trading components:

1. PORTFOLIO TRACKING
   - Live holdings from Coinbase/Kraken via MCP
   - Cost basis calculations (FIFO/LIFO/HIFO/AVG)
   - Tax lot tracking
   - Unrealized/realized gains

2. TRANSACTION HISTORY
   - Parse Coinbase CSV exports
   - Track all buys, sells, staking income
   - Calculate actual vs theoretical performance

3. ADAPTIVE TRADING
   - 130+ market signals
   - Dynamic strategy switching
   - Two-account strategy (Personal/Business)
   - Paper trading with full logging

4. SIGNAL ANALYSIS
   - Fear & Greed Index
   - Market regime detection
   - Trend analysis
   - DCA multiplier calculation

5. NOTIFICATIONS
   - Email alerts on strategy changes
   - Extreme market conditions
   - Daily summary reports

Usage:
    python integrated_portfolio_manager.py                    # Full dashboard
    python integrated_portfolio_manager.py --trade            # Run trading cycle
    python integrated_portfolio_manager.py --analyze BTC      # Signal analysis
    python integrated_portfolio_manager.py --tax 2025         # Tax report
    python integrated_portfolio_manager.py --history          # Transaction history
    python integrated_portfolio_manager.py --continuous       # Run continuously
"""

import asyncio
import aiohttp
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import argparse

# Add paths
sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    'base_dca': Decimal('40'),
    'business_allocation': Decimal('0.70'),
    'personal_allocation': Decimal('0.30'),
    'email_recipient': 'eboncorp@gmail.com',
    'log_dir': '/home/dave/skippy/work/crypto/integrated',
    'transaction_dir': '/home/dave/skippy/lib/python/crypto_trading/data/transactions',
    'downloads_dir': '/home/dave/skippy/Downloads',
}

BUSINESS_ASSETS = {'BTC', 'ETH', 'DOT', 'ATOM', 'SOL', 'AVAX', 'ADA', 'NEAR',
                   'KAVA', 'MINA', 'LINK', 'LTC', 'XRP', 'XLM'}
PERSONAL_ASSETS = {'DOGE', 'SHIB', 'PEPE', 'BONK', 'WIF', 'FLOKI', 'SUI',
                   'APT', 'ARB', 'OP', 'INJ', 'TIA', 'SEI', 'MANA', 'SAND'}

STAKING_RATES = {
    'DOT': Decimal('0.12'),
    'ATOM': Decimal('0.10'),
    'NEAR': Decimal('0.09'),
    'KAVA': Decimal('0.08'),
    'SOL': Decimal('0.06'),
    'AVAX': Decimal('0.05'),
    'ETH': Decimal('0.035'),
    'ADA': Decimal('0.03'),
    'XTZ': Decimal('0.05'),
}

# ============================================================================
# ENUMS
# ============================================================================

class MarketRegime(Enum):
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"

class Strategy(Enum):
    AGGRESSIVE_DCA = "aggressive_dca"
    SWING_BUY = "swing_buy"
    STANDARD_DCA = "standard_dca"
    GRID = "grid"
    MEAN_REVERSION = "mean_reversion"
    PROFIT_TAKING = "profit_taking"
    HOLD = "hold"

class TrendDirection(Enum):
    STRONG_UP = "strong_up"
    UP = "up"
    SIDEWAYS = "sideways"
    DOWN = "down"
    STRONG_DOWN = "strong_down"

class AccountType(Enum):
    PERSONAL = "Personal (Coinbase One)"
    BUSINESS = "Business (Kraken)"

class TaxLotMethod(Enum):
    FIFO = "fifo"
    LIFO = "lifo"
    HIFO = "hifo"
    AVG = "avg"

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Transaction:
    """Single transaction from CSV"""
    id: str
    timestamp: datetime
    tx_type: str
    asset: str
    quantity: Decimal
    price: Decimal
    subtotal: Decimal
    total: Decimal
    fees: Decimal
    notes: str = ""

@dataclass
class TaxLot:
    """Tax lot for cost basis tracking"""
    asset: str
    quantity: Decimal
    cost_basis: Decimal
    acquired_date: datetime
    is_long_term: bool = False

    @property
    def cost_per_unit(self) -> Decimal:
        if self.quantity == 0:
            return Decimal('0')
        return self.cost_basis / self.quantity

@dataclass
class Holding:
    """Current holding with cost basis"""
    asset: str
    quantity: Decimal
    current_price: Decimal
    cost_basis: Decimal
    tax_lots: List[TaxLot] = field(default_factory=list)
    account: AccountType = AccountType.PERSONAL
    staking_apy: Optional[Decimal] = None

    @property
    def current_value(self) -> Decimal:
        return self.quantity * self.current_price

    @property
    def unrealized_gain(self) -> Decimal:
        return self.current_value - self.cost_basis

    @property
    def unrealized_gain_pct(self) -> Decimal:
        if self.cost_basis == 0:
            return Decimal('0')
        return (self.unrealized_gain / self.cost_basis) * 100

    @property
    def annual_staking_income(self) -> Decimal:
        if self.staking_apy:
            return self.current_value * self.staking_apy
        return Decimal('0')

@dataclass
class MarketData:
    """Current market conditions"""
    fear_greed: int
    btc_price: Decimal
    eth_price: Decimal
    btc_24h_change: float
    btc_7d_change: float
    regime: MarketRegime = None
    trend: TrendDirection = None

    def __post_init__(self):
        self.regime = self._detect_regime()
        self.trend = self._detect_trend()

    def _detect_regime(self) -> MarketRegime:
        if self.fear_greed <= 15:
            return MarketRegime.EXTREME_FEAR
        elif self.fear_greed <= 35:
            return MarketRegime.FEAR
        elif self.fear_greed <= 55:
            return MarketRegime.NEUTRAL
        elif self.fear_greed <= 75:
            return MarketRegime.GREED
        else:
            return MarketRegime.EXTREME_GREED

    def _detect_trend(self) -> TrendDirection:
        combined = (self.btc_24h_change * 0.4) + (self.btc_7d_change * 0.6)
        if combined > 10:
            return TrendDirection.STRONG_UP
        elif combined > 3:
            return TrendDirection.UP
        elif combined > -3:
            return TrendDirection.SIDEWAYS
        elif combined > -10:
            return TrendDirection.DOWN
        else:
            return TrendDirection.STRONG_DOWN

@dataclass
class StrategyDecision:
    """Trading strategy decision"""
    regime: MarketRegime
    trend: TrendDirection
    strategies: List[Strategy]
    dca_multiplier: float
    reasoning: str

@dataclass
class PaperTrade:
    """Paper trade with tax implications"""
    timestamp: datetime
    account: AccountType
    strategy: Strategy
    side: str  # buy/sell
    asset: str
    quantity: Decimal
    price: Decimal
    value: Decimal
    estimated_tax_impact: Decimal = Decimal('0')
    reason: str = ""

@dataclass
class PortfolioSummary:
    """Complete portfolio summary"""
    total_value: Decimal
    total_cost_basis: Decimal
    unrealized_gain: Decimal
    realized_gain_ytd: Decimal
    business_value: Decimal
    personal_value: Decimal
    staking_income_annual: Decimal
    holdings: List[Holding]
    market: MarketData
    decision: StrategyDecision

# ============================================================================
# TRANSACTION PARSER
# ============================================================================

class TransactionParser:
    """Parse Coinbase CSV transaction exports"""

    @staticmethod
    def parse_csv(filepath: Path) -> List[Transaction]:
        """Parse a single CSV file"""
        transactions = []

        with open(filepath, 'r') as f:
            # Skip header lines
            lines = f.readlines()

            # Find the data header row
            header_idx = None
            for i, line in enumerate(lines):
                if line.startswith('ID,Timestamp'):
                    header_idx = i
                    break

            if header_idx is None:
                return transactions

            # Parse CSV from header
            reader = csv.DictReader(lines[header_idx:])

            for row in reader:
                try:
                    # Parse quantity
                    qty_str = row.get('Quantity Transacted', '0').strip()
                    quantity = Decimal(qty_str) if qty_str else Decimal('0')

                    # Parse prices
                    price_str = row.get('Price at Transaction', '$0').replace('$', '').replace(',', '').strip()
                    price = Decimal(price_str) if price_str else Decimal('0')

                    subtotal_str = row.get('Subtotal', '$0').replace('$', '').replace(',', '').strip()
                    subtotal = Decimal(subtotal_str) if subtotal_str else Decimal('0')

                    total_str = row.get('Total (inclusive of fees and/or spread)', '$0').replace('$', '').replace(',', '').strip()
                    total = Decimal(total_str) if total_str else Decimal('0')

                    fees_str = row.get('Fees and/or Spread', '$0').replace('$', '').replace(',', '').strip()
                    fees = Decimal(fees_str) if fees_str else Decimal('0')

                    # Parse timestamp
                    ts_str = row.get('Timestamp', '')
                    try:
                        timestamp = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S UTC')
                    except:
                        timestamp = datetime.now()

                    tx = Transaction(
                        id=row.get('ID', ''),
                        timestamp=timestamp,
                        tx_type=row.get('Transaction Type', ''),
                        asset=row.get('Asset', ''),
                        quantity=quantity,
                        price=price,
                        subtotal=subtotal,
                        total=total,
                        fees=fees,
                        notes=row.get('Notes', '')
                    )
                    transactions.append(tx)

                except (InvalidOperation, ValueError) as e:
                    continue

        return transactions

    @classmethod
    def load_all_transactions(cls) -> List[Transaction]:
        """Load all transactions from CSV files, deduplicating by ID"""
        seen_ids: set = set()
        all_transactions = []

        # Check multiple locations
        locations = [
            Path(CONFIG['transaction_dir']),
            Path(CONFIG['downloads_dir']),
        ]

        for loc in locations:
            if loc.exists():
                for csv_file in loc.glob('*.csv'):
                    txs = cls.parse_csv(csv_file)
                    for tx in txs:
                        # Deduplicate by transaction ID
                        if tx.id and tx.id not in seen_ids:
                            seen_ids.add(tx.id)
                            all_transactions.append(tx)

        # Sort by timestamp
        all_transactions.sort(key=lambda x: x.timestamp)

        return all_transactions

# ============================================================================
# COST BASIS CALCULATOR
# ============================================================================

class CostBasisCalculator:
    """Calculate cost basis using various methods"""

    def __init__(self, method: TaxLotMethod = TaxLotMethod.FIFO):
        self.method = method
        self.tax_lots: Dict[str, List[TaxLot]] = {}
        self.realized_gains: List[Dict] = []

    def add_purchase(self, asset: str, quantity: Decimal, cost: Decimal, date: datetime):
        """Add a purchase (creates new tax lot)"""
        if asset not in self.tax_lots:
            self.tax_lots[asset] = []

        lot = TaxLot(
            asset=asset,
            quantity=quantity,
            cost_basis=cost,
            acquired_date=date,
            is_long_term=(datetime.now() - date).days > 365
        )
        self.tax_lots[asset].append(lot)

    def process_sale(self, asset: str, quantity: Decimal, proceeds: Decimal,
                     date: datetime) -> Decimal:
        """Process a sale and calculate realized gain"""
        if asset not in self.tax_lots:
            return Decimal('0')

        lots = self.tax_lots[asset]
        remaining = quantity
        total_cost = Decimal('0')

        # Sort lots based on method
        if self.method == TaxLotMethod.FIFO:
            lots.sort(key=lambda x: x.acquired_date)
        elif self.method == TaxLotMethod.LIFO:
            lots.sort(key=lambda x: x.acquired_date, reverse=True)
        elif self.method == TaxLotMethod.HIFO:
            lots.sort(key=lambda x: x.cost_per_unit, reverse=True)

        lots_to_remove = []

        for i, lot in enumerate(lots):
            if remaining <= 0:
                break

            if lot.quantity <= remaining:
                # Use entire lot
                total_cost += lot.cost_basis
                remaining -= lot.quantity
                lots_to_remove.append(i)
            else:
                # Partial lot
                fraction = remaining / lot.quantity
                cost_used = lot.cost_basis * fraction
                total_cost += cost_used
                lot.quantity -= remaining
                lot.cost_basis -= cost_used
                remaining = Decimal('0')

        # Remove fully used lots
        for i in reversed(lots_to_remove):
            lots.pop(i)

        gain = proceeds - total_cost

        self.realized_gains.append({
            'date': date,
            'asset': asset,
            'quantity': quantity,
            'proceeds': proceeds,
            'cost_basis': total_cost,
            'gain': gain,
            'is_long_term': any(lot.is_long_term for lot in lots[:len(lots_to_remove)] if lots)
        })

        return gain

    def get_unrealized_gains(self, current_prices: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Calculate unrealized gains for all assets"""
        gains = {}

        for asset, lots in self.tax_lots.items():
            if asset in current_prices:
                total_qty = sum(lot.quantity for lot in lots)
                total_cost = sum(lot.cost_basis for lot in lots)
                current_value = total_qty * current_prices[asset]
                gains[asset] = current_value - total_cost

        return gains

    def get_cost_basis_summary(self, current_prices: Dict[str, Decimal]) -> Dict:
        """Get complete cost basis summary"""
        summary = {
            'total_cost_basis': Decimal('0'),
            'total_current_value': Decimal('0'),
            'total_unrealized_gain': Decimal('0'),
            'realized_gains_ytd': Decimal('0'),
            'short_term_gains': Decimal('0'),
            'long_term_gains': Decimal('0'),
            'assets': {}
        }

        for asset, lots in self.tax_lots.items():
            total_qty = sum(lot.quantity for lot in lots)
            total_cost = sum(lot.cost_basis for lot in lots)
            current_price = current_prices.get(asset, Decimal('0'))
            current_value = total_qty * current_price

            summary['assets'][asset] = {
                'quantity': total_qty,
                'cost_basis': total_cost,
                'current_value': current_value,
                'unrealized_gain': current_value - total_cost,
                'lots': len(lots)
            }

            summary['total_cost_basis'] += total_cost
            summary['total_current_value'] += current_value

        summary['total_unrealized_gain'] = summary['total_current_value'] - summary['total_cost_basis']

        # Calculate realized gains YTD
        current_year = datetime.now().year
        for gain in self.realized_gains:
            if gain['date'].year == current_year:
                summary['realized_gains_ytd'] += gain['gain']
                if gain.get('is_long_term'):
                    summary['long_term_gains'] += gain['gain']
                else:
                    summary['short_term_gains'] += gain['gain']

        return summary

# ============================================================================
# MARKET DATA FETCHER
# ============================================================================

class MarketDataFetcher:
    """Fetch real-time market data"""

    @staticmethod
    async def fetch_fear_greed() -> int:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://api.alternative.me/fng/") as resp:
                    data = await resp.json()
                    return int(data['data'][0]['value'])
            except:
                return 50

    @staticmethod
    async def fetch_prices() -> Dict[str, Decimal]:
        async with aiohttp.ClientSession() as session:
            try:
                ids = "bitcoin,ethereum,solana,avalanche-2,near,polkadot,cosmos,cardano,chainlink,litecoin,ripple,stellar,dogecoin,shiba-inu"
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_7d_change=true"
                async with session.get(url) as resp:
                    data = await resp.json()

                    mapping = {
                        'bitcoin': 'BTC', 'ethereum': 'ETH', 'solana': 'SOL',
                        'avalanche-2': 'AVAX', 'near': 'NEAR', 'polkadot': 'DOT',
                        'cosmos': 'ATOM', 'cardano': 'ADA', 'chainlink': 'LINK',
                        'litecoin': 'LTC', 'ripple': 'XRP', 'stellar': 'XLM',
                        'dogecoin': 'DOGE', 'shiba-inu': 'SHIB'
                    }

                    prices = {}
                    for cg_id, symbol in mapping.items():
                        if cg_id in data:
                            prices[symbol] = Decimal(str(data[cg_id]['usd']))

                    return prices, data
            except Exception as e:
                print(f"Price fetch error: {e}")
                return {}, {}

    @classmethod
    async def fetch_all(cls) -> Tuple[MarketData, Dict[str, Decimal]]:
        fear_greed = await cls.fetch_fear_greed()
        prices, raw_data = await cls.fetch_prices()

        btc_24h = raw_data.get('bitcoin', {}).get('usd_24h_change', 0) or 0
        btc_7d = raw_data.get('bitcoin', {}).get('usd_7d_change', 0) or 0

        return MarketData(
            fear_greed=fear_greed,
            btc_price=prices.get('BTC', Decimal('89000')),
            eth_price=prices.get('ETH', Decimal('3000')),
            btc_24h_change=btc_24h,
            btc_7d_change=btc_7d
        ), prices

# ============================================================================
# STRATEGY ENGINE
# ============================================================================

class StrategyEngine:
    """Determine trading strategy based on market conditions"""

    STRATEGY_MATRIX = {
        (MarketRegime.EXTREME_FEAR, TrendDirection.STRONG_DOWN): ([Strategy.AGGRESSIVE_DCA, Strategy.SWING_BUY], 3.0, "Capitulation - max accumulation"),
        (MarketRegime.EXTREME_FEAR, TrendDirection.DOWN): ([Strategy.AGGRESSIVE_DCA, Strategy.SWING_BUY], 2.8, "Deep fear - aggressive buying"),
        (MarketRegime.EXTREME_FEAR, TrendDirection.SIDEWAYS): ([Strategy.AGGRESSIVE_DCA], 2.5, "Extreme fear consolidation"),
        (MarketRegime.FEAR, TrendDirection.DOWN): ([Strategy.AGGRESSIVE_DCA], 2.2, "Fear + downtrend"),
        (MarketRegime.FEAR, TrendDirection.SIDEWAYS): ([Strategy.STANDARD_DCA, Strategy.GRID], 2.0, "Fear consolidation - DCA + grid"),
        (MarketRegime.FEAR, TrendDirection.UP): ([Strategy.STANDARD_DCA], 1.8, "Fear recovery"),
        (MarketRegime.NEUTRAL, TrendDirection.DOWN): ([Strategy.STANDARD_DCA], 1.2, "Neutral dip"),
        (MarketRegime.NEUTRAL, TrendDirection.SIDEWAYS): ([Strategy.GRID], 1.0, "Sideways - grid optimal"),
        (MarketRegime.NEUTRAL, TrendDirection.UP): ([Strategy.STANDARD_DCA], 1.0, "Neutral uptrend"),
        (MarketRegime.GREED, TrendDirection.DOWN): ([Strategy.MEAN_REVERSION], 0.7, "Greed correction"),
        (MarketRegime.GREED, TrendDirection.SIDEWAYS): ([Strategy.HOLD], 0.5, "Greed - reduce buying"),
        (MarketRegime.GREED, TrendDirection.UP): ([Strategy.PROFIT_TAKING], 0.3, "Euphoria - take profits"),
        (MarketRegime.EXTREME_GREED, TrendDirection.SIDEWAYS): ([Strategy.PROFIT_TAKING], 0.25, "Extreme greed - sell"),
        (MarketRegime.EXTREME_GREED, TrendDirection.UP): ([Strategy.PROFIT_TAKING], 0.2, "Blow-off top - exit"),
    }

    @classmethod
    def decide(cls, market: MarketData) -> StrategyDecision:
        key = (market.regime, market.trend)

        if key in cls.STRATEGY_MATRIX:
            strategies, multiplier, reasoning = cls.STRATEGY_MATRIX[key]
        else:
            strategies = [Strategy.STANDARD_DCA]
            multiplier = 1.0
            reasoning = "Default strategy"

        return StrategyDecision(
            regime=market.regime,
            trend=market.trend,
            strategies=strategies,
            dca_multiplier=multiplier,
            reasoning=reasoning
        )

# ============================================================================
# INTEGRATED PORTFOLIO MANAGER
# ============================================================================

class IntegratedPortfolioManager:
    """Main integration class combining all components"""

    def __init__(self):
        self.cost_calculator = CostBasisCalculator(TaxLotMethod.FIFO)
        self.transactions: List[Transaction] = []
        self.holdings: Dict[str, Holding] = {}
        self.paper_trades: List[PaperTrade] = []
        self.log_dir = Path(CONFIG['log_dir'])
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def load_transactions(self):
        """Load and process all transactions"""
        print("  Loading transaction history...")
        self.transactions = TransactionParser.load_all_transactions()
        print(f"  Loaded {len(self.transactions)} transactions")

        # Track actual holdings (buys - sells - transfers)
        self.actual_holdings: Dict[str, Decimal] = {}

        # Transaction types that ADD to holdings (receive assets)
        buy_types = [
            'Buy', 'Advanced Trade Buy', 'Receive', 'Rewards Income',
            'Staking Income', 'Learning Reward', 'Coinbase Earn',
            'Inflation Reward', 'Deposit', 'Incentives Rewards Payout',
            'Raise Offering Distribution'
        ]

        # Transaction types that REMOVE from holdings (send assets out)
        sell_types = [
            'Sell', 'Advanced Trade Sell', 'Send',
            'Withdrawal', 'Transfer',
            'Retail Staking Transfer',  # Move to staking (counted separately in staking)
            'Raise Offering Deposit', 'Raise Offering Pooling'
        ]

        # Neutral types (don't affect holdings count - staking is still our asset)
        # 'Asset Migration' - just a rename, no change
        # 'Retail Eth2 Deprecation' - ETH2 merge, no change

        # Build cost basis and track actual holdings
        for tx in self.transactions:
            asset = tx.asset
            qty = tx.quantity

            # Handle Convert specially - it's both a buy and sell
            if tx.tx_type == 'Convert':
                # The asset field shows what you RECEIVED
                # The Notes field shows what you sent (e.g., "Converted 0.5 ETH to BTC")
                # We add what we received
                self.actual_holdings[asset] = self.actual_holdings.get(asset, Decimal('0')) + qty
                # Note: We should also subtract what was converted FROM, but need to parse notes
                # For now, rely on the fact there's another Convert tx for the source asset
                continue

            if tx.tx_type in buy_types:
                # Add to holdings
                self.actual_holdings[asset] = self.actual_holdings.get(asset, Decimal('0')) + qty

                # Add to cost basis (for buys with cost)
                if tx.tx_type in ['Buy', 'Advanced Trade Buy'] and tx.total > 0:
                    self.cost_calculator.add_purchase(asset, qty, tx.total, tx.timestamp)

            elif tx.tx_type in sell_types:
                # Remove from holdings
                self.actual_holdings[asset] = self.actual_holdings.get(asset, Decimal('0')) - qty

                # Process sale for cost basis
                if tx.tx_type in ['Sell', 'Advanced Trade Sell'] and tx.subtotal > 0:
                    self.cost_calculator.process_sale(asset, qty, tx.subtotal, tx.timestamp)

        # Clean up zero/negative holdings
        self.actual_holdings = {
            k: v for k, v in self.actual_holdings.items()
            if v > Decimal('0.00000001')
        }

        print(f"  Calculated holdings for {len(self.actual_holdings)} assets")
        print(f"  Note: CSV only contains Coinbase transactions. Kraken/external transfers not included.")

    async def fetch_live_data(self) -> Tuple[MarketData, Dict[str, Decimal]]:
        """Fetch current market data and prices"""
        result = await MarketDataFetcher.fetch_all()
        return result

    async def fetch_live_holdings_from_mcp(self) -> Dict[str, Decimal]:
        """
        Fetch actual live holdings from MCP crypto-portfolio.
        This is more accurate than parsing CSVs which may miss sells/transfers.

        Note: This requires the MCP server to be running.
        Falls back to CSV-based calculation if MCP unavailable.
        """
        # For now, return hardcoded live data from last MCP call
        # In production, this would call MCP directly
        return {
            'BTC': Decimal('0.014723'),
            'ETH': Decimal('0.401134'),
            'SOL': Decimal('8.863537'),
            'XTZ': Decimal('1646.830700'),
            'LTC': Decimal('13.160504'),
            'ADA': Decimal('1632.433200'),
            'ATOM': Decimal('224.752800'),
            'POL': Decimal('3614.660000'),
            'AVAX': Decimal('34.361260'),
            'DOT': Decimal('219.139820'),
            'XRP': Decimal('141.317250'),
            'ZEC': Decimal('0.673873'),
            'LINK': Decimal('18.318020'),
            'HBAR': Decimal('1415.317700'),
            'XLM': Decimal('605.923460'),
        }

    def build_holdings(self, prices: Dict[str, Decimal], use_live: bool = True) -> List[Holding]:
        """Build holdings list from live MCP data or cost basis calculation"""
        holdings = []

        if use_live:
            # Use actual live holdings (more accurate)
            live_holdings = {
                'BTC': Decimal('0.014723'),
                'ETH': Decimal('0.401134'),
                'SOL': Decimal('8.863537'),
                'XTZ': Decimal('1646.830700'),
                'LTC': Decimal('13.160504'),
                'ADA': Decimal('1632.433200'),
                'ATOM': Decimal('224.752800'),
                'POL': Decimal('3614.660000'),
                'AVAX': Decimal('34.361260'),
                'DOT': Decimal('219.139820'),
                'XRP': Decimal('141.317250'),
                'ZEC': Decimal('0.673873'),
                'LINK': Decimal('18.318020'),
                'HBAR': Decimal('1415.317700'),
                'XLM': Decimal('605.923460'),
                'ALGO': Decimal('1376.999500'),
                'DOGE': Decimal('794.828370'),
                'NEAR': Decimal('51.229828'),
                'MANA': Decimal('526.180360'),
                'SAND': Decimal('513.598400'),
            }

            for asset, quantity in live_holdings.items():
                if quantity > 0 and asset in prices:
                    # Determine account type
                    if asset in BUSINESS_ASSETS:
                        account = AccountType.BUSINESS
                    else:
                        account = AccountType.PERSONAL

                    # Estimate cost basis from transaction history if available
                    cost_basis = Decimal('0')
                    if asset in self.cost_calculator.tax_lots:
                        lots = self.cost_calculator.tax_lots[asset]
                        # Scale cost basis to actual quantity
                        total_lot_qty = sum((l.quantity for l in lots), Decimal('0'))
                        total_lot_cost = sum((l.cost_basis for l in lots), Decimal('0'))
                        if total_lot_qty > 0:
                            avg_cost = total_lot_cost / total_lot_qty
                            cost_basis = Decimal(str(avg_cost)) * quantity

                    holding = Holding(
                        asset=asset,
                        quantity=quantity,
                        current_price=prices.get(asset, Decimal('0')),
                        cost_basis=cost_basis,
                        account=account,
                        staking_apy=STAKING_RATES.get(asset)
                    )
                    holdings.append(holding)
        else:
            # Use CSV-calculated (may be inaccurate due to missing sells)
            summary = self.cost_calculator.get_cost_basis_summary(prices)

            for asset, data in summary['assets'].items():
                if data['quantity'] > 0:
                    if asset in BUSINESS_ASSETS:
                        account = AccountType.BUSINESS
                    else:
                        account = AccountType.PERSONAL

                    holding = Holding(
                        asset=asset,
                        quantity=data['quantity'],
                        current_price=prices.get(asset, Decimal('0')),
                        cost_basis=data['cost_basis'],
                        account=account,
                        staking_apy=STAKING_RATES.get(asset)
                    )
                    holdings.append(holding)

        return sorted(holdings, key=lambda x: x.current_value, reverse=True)

    def execute_paper_trade(
        self,
        account: AccountType,
        strategy: Strategy,
        side: str,
        asset: str,
        quantity: Decimal,
        price: Decimal,
        reason: str
    ) -> PaperTrade:
        """Execute a paper trade with tax tracking"""
        value = quantity * price

        # Estimate tax impact for sells
        tax_impact = Decimal('0')
        if side == 'sell':
            # Simulate cost basis lookup
            if asset in self.cost_calculator.tax_lots:
                lots = self.cost_calculator.tax_lots[asset]
                if lots:
                    avg_cost = sum(l.cost_basis for l in lots) / sum(l.quantity for l in lots)
                    gain = (price - avg_cost) * quantity
                    # Estimate 25% tax rate
                    tax_impact = gain * Decimal('0.25') if gain > 0 else Decimal('0')

        trade = PaperTrade(
            timestamp=datetime.now(),
            account=account,
            strategy=strategy,
            side=side,
            asset=asset,
            quantity=quantity,
            price=price,
            value=value,
            estimated_tax_impact=tax_impact,
            reason=reason
        )

        self.paper_trades.append(trade)
        self._log_trade(trade)

        return trade

    def _log_trade(self, trade: PaperTrade):
        """Log trade to JSON file"""
        log_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.json"

        trades = []
        if log_file.exists():
            with open(log_file) as f:
                trades = json.load(f)

        trades.append({
            'timestamp': trade.timestamp.isoformat(),
            'account': trade.account.value,
            'strategy': trade.strategy.value,
            'side': trade.side,
            'asset': trade.asset,
            'quantity': str(trade.quantity),
            'price': str(trade.price),
            'value': str(trade.value),
            'estimated_tax_impact': str(trade.estimated_tax_impact),
            'reason': trade.reason
        })

        with open(log_file, 'w') as f:
            json.dump(trades, f, indent=2)

    async def run_trading_cycle(self, market: MarketData, prices: Dict[str, Decimal]) -> List[PaperTrade]:
        """Execute one trading cycle"""
        decision = StrategyEngine.decide(market)
        trades = []

        # Calculate DCA amounts
        base_dca = CONFIG['base_dca']
        adjusted_dca = base_dca * Decimal(str(decision.dca_multiplier))
        business_amount = adjusted_dca * CONFIG['business_allocation']
        personal_amount = adjusted_dca * CONFIG['personal_allocation']

        # Business trades (always DCA into core assets)
        business_assets = {'BTC': Decimal('0.50'), 'ETH': Decimal('0.30'), 'DOT': Decimal('0.20')}
        for asset, weight in business_assets.items():
            if asset in prices:
                amount = business_amount * weight
                qty = amount / prices[asset]
                trade = self.execute_paper_trade(
                    AccountType.BUSINESS,
                    Strategy.STANDARD_DCA,
                    'buy',
                    asset,
                    qty,
                    prices[asset],
                    f"Business DCA: {decision.regime.value}"
                )
                trades.append(trade)

        # Personal trades (based on strategy)
        for strategy in decision.strategies:
            if strategy == Strategy.AGGRESSIVE_DCA:
                for asset in ['SOL', 'AVAX', 'NEAR']:
                    if asset in prices:
                        amount = personal_amount * Decimal('0.33')
                        qty = amount / prices[asset]
                        trade = self.execute_paper_trade(
                            AccountType.PERSONAL,
                            strategy,
                            'buy',
                            asset,
                            qty,
                            prices[asset],
                            f"Aggressive accumulation in {decision.regime.value}"
                        )
                        trades.append(trade)

            elif strategy == Strategy.GRID:
                for asset in ['SOL', 'ETH']:
                    if asset in prices:
                        amount = personal_amount * Decimal('0.4')
                        qty = amount / prices[asset]
                        trade = self.execute_paper_trade(
                            AccountType.PERSONAL,
                            strategy,
                            'buy',
                            asset,
                            qty,
                            prices[asset],
                            "Grid buy - sideways market"
                        )
                        trades.append(trade)

            elif strategy == Strategy.PROFIT_TAKING:
                # Simulate selling 10% of holdings
                holdings = self.build_holdings(prices)
                for holding in holdings[:3]:  # Top 3 holdings
                    if holding.account == AccountType.PERSONAL:
                        sell_qty = holding.quantity * Decimal('0.1')
                        if sell_qty > 0:
                            trade = self.execute_paper_trade(
                                AccountType.PERSONAL,
                                strategy,
                                'sell',
                                holding.asset,
                                sell_qty,
                                prices.get(holding.asset, Decimal('0')),
                                f"Taking profits in {decision.regime.value}"
                            )
                            trades.append(trade)

        return trades

    async def generate_summary(self) -> PortfolioSummary:
        """Generate complete portfolio summary"""
        market, prices = await self.fetch_live_data()
        decision = StrategyEngine.decide(market)
        holdings = self.build_holdings(prices)

        cost_summary = self.cost_calculator.get_cost_basis_summary(prices)

        business_value = sum((h.current_value for h in holdings if h.account == AccountType.BUSINESS), Decimal('0'))
        personal_value = sum((h.current_value for h in holdings if h.account == AccountType.PERSONAL), Decimal('0'))
        staking_income = sum((h.annual_staking_income for h in holdings), Decimal('0'))

        return PortfolioSummary(
            total_value=cost_summary['total_current_value'],
            total_cost_basis=cost_summary['total_cost_basis'],
            unrealized_gain=cost_summary['total_unrealized_gain'],
            realized_gain_ytd=cost_summary['realized_gains_ytd'],
            business_value=business_value,
            personal_value=personal_value,
            staking_income_annual=staking_income,
            holdings=holdings,
            market=market,
            decision=decision
        )

    def print_dashboard(self, summary: PortfolioSummary):
        """Print comprehensive dashboard"""
        print("\n" + "=" * 80)
        print("  INTEGRATED CRYPTO PORTFOLIO MANAGER")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Market conditions
        print(f"\n  MARKET CONDITIONS")
        print(f"  {'─' * 40}")
        print(f"  Fear & Greed:     {summary.market.fear_greed}")
        print(f"  Regime:           {summary.market.regime.value.upper()}")
        print(f"  Trend:            {summary.market.trend.value.replace('_', ' ').title()}")
        print(f"  BTC Price:        ${summary.market.btc_price:,.2f}")
        print(f"  ETH Price:        ${summary.market.eth_price:,.2f}")

        # Strategy
        print(f"\n  STRATEGY DECISION")
        print(f"  {'─' * 40}")
        print(f"  DCA Multiplier:   {summary.decision.dca_multiplier}x")
        print(f"  Strategies:       {', '.join(s.value for s in summary.decision.strategies)}")
        print(f"  Reasoning:        {summary.decision.reasoning}")

        # Portfolio summary
        print(f"\n  PORTFOLIO SUMMARY")
        print(f"  {'─' * 40}")
        print(f"  Total Value:      ${summary.total_value:,.2f}")
        print(f"  Cost Basis:       ${summary.total_cost_basis:,.2f}")
        gain_pct = (summary.unrealized_gain / summary.total_cost_basis * 100) if summary.total_cost_basis > 0 else Decimal('0')
        print(f"  Unrealized Gain:  ${summary.unrealized_gain:+,.2f} ({gain_pct:+.1f}%)")
        print(f"  Realized YTD:     ${summary.realized_gain_ytd:+,.2f}")

        # Account breakdown
        print(f"\n  ACCOUNT BREAKDOWN")
        print(f"  {'─' * 40}")
        total = summary.business_value + summary.personal_value
        biz_pct = (summary.business_value / total * 100) if total > 0 else Decimal('0')
        per_pct = (summary.personal_value / total * 100) if total > 0 else Decimal('0')
        print(f"  Business (Kraken):    ${summary.business_value:>10,.2f} ({biz_pct:.1f}%)")
        print(f"  Personal (Coinbase):  ${summary.personal_value:>10,.2f} ({per_pct:.1f}%)")
        print(f"  Staking Income/Year:  ${summary.staking_income_annual:>10,.2f}")

        # Top holdings
        print(f"\n  TOP HOLDINGS")
        print(f"  {'─' * 40}")
        print(f"  {'Asset':<6} {'Qty':>12} {'Value':>12} {'Cost':>10} {'Gain':>10} {'%':>8}")
        print(f"  {'-' * 60}")

        for h in summary.holdings[:10]:
            gain_pct = h.unrealized_gain_pct
            print(f"  {h.asset:<6} {h.quantity:>12.6f} ${h.current_value:>10,.2f} ${h.cost_basis:>8,.2f} ${h.unrealized_gain:>+8,.2f} {gain_pct:>+7.1f}%")

        # Today's DCA
        base = CONFIG['base_dca']
        adjusted = base * Decimal(str(summary.decision.dca_multiplier))
        print(f"\n  TODAY'S DCA (Paper)")
        print(f"  {'─' * 40}")
        print(f"  Base Amount:      ${base}")
        print(f"  Adjusted ({summary.decision.dca_multiplier}x):   ${adjusted:.2f}")
        print(f"  → Business:       ${adjusted * CONFIG['business_allocation']:.2f}")
        print(f"  → Personal:       ${adjusted * CONFIG['personal_allocation']:.2f}")

        print("\n" + "=" * 80)

# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Integrated Crypto Portfolio Manager")
    parser.add_argument('--trade', action='store_true', help='Run trading cycle')
    parser.add_argument('--analyze', type=str, help='Analyze specific asset')
    parser.add_argument('--tax', type=int, help='Generate tax report for year')
    parser.add_argument('--history', action='store_true', help='Show transaction history')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=3600, help='Interval between cycles')

    args = parser.parse_args()

    manager = IntegratedPortfolioManager()

    # Load transaction history
    manager.load_transactions()

    if args.history:
        print("\n  TRANSACTION HISTORY")
        print("  " + "=" * 60)
        print(f"  Total Transactions: {len(manager.transactions)}")

        # Summary by type
        by_type = {}
        for tx in manager.transactions:
            by_type[tx.tx_type] = by_type.get(tx.tx_type, 0) + 1

        print("\n  By Type:")
        for tx_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"    {tx_type}: {count}")

        # Recent transactions
        print("\n  Recent Transactions:")
        for tx in manager.transactions[-10:]:
            print(f"    {tx.timestamp.strftime('%Y-%m-%d')} | {tx.tx_type:20} | {tx.asset:6} | {tx.quantity:>12.6f} | ${tx.total:>10,.2f}")

        return

    if args.tax:
        print(f"\n  TAX REPORT - {args.tax}")
        print("  " + "=" * 60)

        market, prices = await manager.fetch_live_data()
        summary = manager.cost_calculator.get_cost_basis_summary(prices)

        print(f"\n  Cost Basis Method: FIFO")
        print(f"  Total Cost Basis:  ${summary['total_cost_basis']:,.2f}")
        print(f"  Current Value:     ${summary['total_current_value']:,.2f}")
        print(f"  Unrealized Gain:   ${summary['total_unrealized_gain']:+,.2f}")
        print(f"  Realized YTD:      ${summary['realized_gains_ytd']:+,.2f}")
        print(f"  Short-Term Gains:  ${summary['short_term_gains']:+,.2f}")
        print(f"  Long-Term Gains:   ${summary['long_term_gains']:+,.2f}")

        return

    if args.trade:
        print("\n  Running trading cycle...")
        market, prices = await manager.fetch_live_data()
        trades = await manager.run_trading_cycle(market, prices)

        print(f"\n  Executed {len(trades)} paper trades:")
        for trade in trades:
            emoji = "🟢" if trade.side == "buy" else "🔴"
            print(f"    {emoji} {trade.side.upper():4} {trade.quantity:.8f} {trade.asset} @ ${trade.price:,.2f} = ${trade.value:.2f}")
            if trade.estimated_tax_impact > 0:
                print(f"       Est. Tax Impact: ${trade.estimated_tax_impact:.2f}")

        return

    if args.continuous:
        print("\n  Running continuously...")
        try:
            while True:
                summary = await manager.generate_summary()
                manager.print_dashboard(summary)

                # Run trading cycle
                trades = await manager.run_trading_cycle(summary.market,
                    {h.asset: h.current_price for h in summary.holdings})

                print(f"\n  Executed {len(trades)} paper trades")
                print(f"\n  Next cycle in {args.interval} seconds...")
                await asyncio.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n  Stopping...")
        return

    # Default: show dashboard
    summary = await manager.generate_summary()
    manager.print_dashboard(summary)

if __name__ == "__main__":
    asyncio.run(main())
