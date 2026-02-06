"""
Portfolio Rebalancer

Automatically rebalance your crypto portfolio to maintain target allocations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from coinbase_client import CoinbaseClient
from trading_engine import TradingEngine, TradeRecord
from config import TradingConfig, RebalanceConfig


@dataclass
class AllocationStatus:
    """Current vs target allocation for an asset."""
    asset: str
    current_value_usd: float
    current_percent: float
    target_percent: float
    deviation: float  # current - target
    action: str  # "BUY", "SELL", or "HOLD"
    trade_amount_usd: float


class Rebalancer:
    """
    Portfolio rebalancer that maintains target allocations.
    
    Features:
    - Calculate current vs target allocations
    - Generate rebalancing trades
    - Execute with safety guardrails
    - Support buy-only or full rebalancing
    """
    
    def __init__(
        self, 
        client: CoinbaseClient, 
        engine: TradingEngine,
        config: TradingConfig = None
    ):
        self.client = client
        self.engine = engine
        self.config = config or TradingConfig()
        self.rebalance_config = self.config.rebalance
    
    def get_current_allocations(self) -> Tuple[Dict[str, float], float]:
        """
        Get current portfolio allocations.
        Returns (allocations_dict, total_value_usd).
        """
        accounts = self.client.get_accounts()
        holdings = {}
        
        for account in accounts:
            balance = float(account.get("available_balance", {}).get("value", 0))
            currency = account.get("currency", "")
            
            if balance > 0 and currency != "USD":
                price = self.client.get_spot_price(currency)
                if price:
                    usd_value = balance * price
                    if usd_value >= self.config.safety.min_asset_value_usd:
                        holdings[currency] = {
                            "balance": balance,
                            "price": price,
                            "usd_value": usd_value
                        }
            elif balance > 0 and currency == "USD":
                holdings["USD"] = {
                    "balance": balance,
                    "price": 1.0,
                    "usd_value": balance
                }
        
        total_value = sum(h["usd_value"] for h in holdings.values())
        
        allocations = {}
        for asset, data in holdings.items():
            allocations[asset] = {
                "balance": data["balance"],
                "price": data["price"],
                "usd_value": data["usd_value"],
                "percent": (data["usd_value"] / total_value * 100) if total_value > 0 else 0
            }
        
        return allocations, total_value
    
    def calculate_rebalance_trades(
        self,
        target_allocations: Dict[str, float] = None
    ) -> List[AllocationStatus]:
        """
        Calculate what trades are needed to rebalance.
        
        Args:
            target_allocations: Override config targets. Format: {"BTC": 50, "ETH": 30}
        
        Returns:
            List of AllocationStatus objects describing needed trades.
        """
        targets = target_allocations or self.rebalance_config.target_allocations
        
        if not targets:
            raise ValueError("No target allocations defined")
        
        # Validate targets sum to 100 (allowing for rounding)
        total_target = sum(targets.values())
        if abs(total_target - 100) > 1:
            raise ValueError(f"Target allocations must sum to 100, got {total_target}")
        
        current, total_value = self.get_current_allocations()
        
        results = []
        
        # Analyze each target asset
        for asset, target_pct in targets.items():
            current_data = current.get(asset, {})
            current_pct = current_data.get("percent", 0)
            current_value = current_data.get("usd_value", 0)
            
            deviation = current_pct - target_pct
            target_value = total_value * (target_pct / 100)
            trade_value = target_value - current_value
            
            # Determine action
            if abs(deviation) < self.rebalance_config.rebalance_threshold:
                action = "HOLD"
                trade_value = 0
            elif deviation < 0:
                action = "BUY"
            else:
                action = "SELL" if self.rebalance_config.allow_sells else "HOLD"
                if action == "HOLD":
                    trade_value = 0
            
            # Check minimum trade size
            if abs(trade_value) < self.rebalance_config.min_rebalance_trade_usd:
                action = "HOLD"
                trade_value = 0
            
            results.append(AllocationStatus(
                asset=asset,
                current_value_usd=current_value,
                current_percent=current_pct,
                target_percent=target_pct,
                deviation=deviation,
                action=action,
                trade_amount_usd=abs(trade_value)
            ))
        
        # Check for assets we hold but aren't in targets
        for asset, data in current.items():
            if asset not in targets and asset != "USD":
                results.append(AllocationStatus(
                    asset=asset,
                    current_value_usd=data["usd_value"],
                    current_percent=data["percent"],
                    target_percent=0,
                    deviation=data["percent"],
                    action="SELL" if self.rebalance_config.allow_sells else "HOLD",
                    trade_amount_usd=data["usd_value"] if self.rebalance_config.allow_sells else 0
                ))
        
        # Sort by deviation magnitude (biggest first)
        results.sort(key=lambda x: abs(x.deviation), reverse=True)
        
        return results
    
    def preview_rebalance(self, target_allocations: Dict[str, float] = None) -> dict:
        """
        Preview rebalancing without executing any trades.
        Returns a detailed plan.
        """
        trades = self.calculate_rebalance_trades(target_allocations)
        current, total_value = self.get_current_allocations()
        
        sells = [t for t in trades if t.action == "SELL"]
        buys = [t for t in trades if t.action == "BUY"]
        holds = [t for t in trades if t.action == "HOLD"]
        
        # Calculate total sell proceeds and buy requirements
        total_sells = sum(t.trade_amount_usd for t in sells)
        total_buys = sum(t.trade_amount_usd for t in buys)
        
        # Check USD balance for additional buys
        usd_available = current.get("USD", {}).get("usd_value", 0) + total_sells
        funding_gap = max(0, total_buys - usd_available)
        
        return {
            "portfolio_value_usd": total_value,
            "current_allocations": {
                a: {"percent": d["percent"], "usd": d["usd_value"]} 
                for a, d in current.items()
            },
            "target_allocations": target_allocations or self.rebalance_config.target_allocations,
            "trades_needed": {
                "sells": [
                    {"asset": t.asset, "usd": t.trade_amount_usd, "deviation": t.deviation}
                    for t in sells
                ],
                "buys": [
                    {"asset": t.asset, "usd": t.trade_amount_usd, "deviation": t.deviation}
                    for t in buys
                ],
                "holds": [t.asset for t in holds]
            },
            "summary": {
                "total_sell_usd": total_sells,
                "total_buy_usd": total_buys,
                "usd_available": usd_available,
                "funding_gap": funding_gap,
                "num_trades": len(sells) + len(buys)
            }
        }
    
    def execute_rebalance(
        self,
        target_allocations: Dict[str, float] = None,
        dry_run: bool = True
    ) -> List[TradeRecord]:
        """
        Execute rebalancing trades.
        
        Args:
            target_allocations: Override config targets
            dry_run: If True, preview only without executing
        
        Returns:
            List of TradeRecords for executed trades.
        """
        trades = self.calculate_rebalance_trades(target_allocations)
        results = []
        
        # Execute sells first (to generate USD for buys)
        sells = [t for t in trades if t.action == "SELL"]
        buys = [t for t in trades if t.action == "BUY"]
        
        print("\n" + "="*60)
        print("📊 REBALANCING PLAN")
        print("="*60)
        
        if not sells and not buys:
            print("✅ Portfolio is already balanced within threshold!")
            return results
        
        if sells:
            print("\n🔴 SELLS:")
            for t in sells:
                current, _ = self.get_current_allocations()
                balance = current.get(t.asset, {}).get("balance", 0)
                price = current.get(t.asset, {}).get("price", 0)
                sell_amount = t.trade_amount_usd / price if price > 0 else 0
                
                print(f"  {t.asset}: Sell ${t.trade_amount_usd:.2f} ({sell_amount:.8f} {t.asset})")
                print(f"          Current: {t.current_percent:.1f}% → Target: {t.target_percent:.1f}%")
                
                if not dry_run:
                    record = self.engine.execute_trade(
                        product_id=f"{t.asset}-USD",
                        side="SELL",
                        asset_amount=sell_amount
                    )
                    results.append(record)
        
        if buys:
            print("\n🟢 BUYS:")
            for t in buys:
                print(f"  {t.asset}: Buy ${t.trade_amount_usd:.2f}")
                print(f"          Current: {t.current_percent:.1f}% → Target: {t.target_percent:.1f}%")
                
                if not dry_run:
                    record = self.engine.execute_trade(
                        product_id=f"{t.asset}-USD",
                        side="BUY",
                        usd_amount=t.trade_amount_usd
                    )
                    results.append(record)
        
        print("\n" + "="*60)
        
        if dry_run:
            print("ℹ️  DRY RUN - No trades executed")
            print("   Set dry_run=False to execute trades")
        else:
            executed = sum(1 for r in results if r.executed)
            print(f"✅ Executed {executed}/{len(results)} trades")
        
        return results
    
    def display_allocation_status(self):
        """Print a formatted view of current vs target allocations."""
        trades = self.calculate_rebalance_trades()
        current, total = self.get_current_allocations()
        
        print("\n" + "="*70)
        print("📊 PORTFOLIO ALLOCATION STATUS")
        print("="*70)
        print(f"Total Portfolio Value: ${total:,.2f}")
        print("-"*70)
        print(f"{'Asset':<8} {'Current %':>10} {'Target %':>10} {'Deviation':>10} {'Action':>10}")
        print("-"*70)
        
        for t in trades:
            deviation_str = f"{t.deviation:+.1f}%"
            action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(t.action, "")
            print(f"{t.asset:<8} {t.current_percent:>9.1f}% {t.target_percent:>9.1f}% {deviation_str:>10} {action_emoji} {t.action:>6}")
        
        print("-"*70)


def quick_rebalance(
    api_key: str,
    api_secret: str,
    targets: Dict[str, float],
    dry_run: bool = True
):
    """
    Convenience function for quick rebalancing.
    
    Example:
        quick_rebalance(key, secret, {"BTC": 50, "ETH": 30, "SOL": 20})
    """
    from config import TradingConfig, TradingMode
    
    client = CoinbaseClient(api_key, api_secret)
    config = TradingConfig(mode=TradingMode.CONFIRM)
    config.rebalance.target_allocations = targets
    
    engine = TradingEngine(client, config)
    rebalancer = Rebalancer(client, engine, config)
    
    rebalancer.display_allocation_status()
    return rebalancer.execute_rebalance(dry_run=dry_run)
