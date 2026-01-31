"""
Trading Engine with Safety Guardrails

This module provides the core trading execution layer with built-in
safety checks, logging, and confirmation prompts.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass, field

from exchanges import CoinbaseClient
from config import TradingConfig, TradingMode, SafetyLimits


@dataclass
class TradeRecord:
    """Record of an executed or attempted trade."""
    timestamp: datetime
    product_id: str
    side: str  # BUY or SELL
    order_type: str
    requested_amount: float
    requested_usd: float
    executed: bool
    order_id: Optional[str] = None
    fill_price: Optional[float] = None
    fill_amount: Optional[float] = None
    fees: Optional[float] = None
    error: Optional[str] = None


class TradingEngine:
    """
    Core trading engine with safety guardrails.
    
    Features:
    - Multiple trading modes (paper, confirm, live)
    - Safety limit enforcement
    - Trade logging and history
    - Preview before execution
    - Cooldown tracking
    """
    
    def __init__(self, client: CoinbaseClient, config: TradingConfig = None):
        self.client = client
        self.config = config or TradingConfig()
        
        # Trade tracking
        self.trade_history: list[TradeRecord] = []
        self.daily_trades: int = 0
        self.daily_volume_usd: float = 0.0
        self.daily_reset_time: datetime = datetime.now()
        self.last_trade_time: dict[str, datetime] = {}  # Per-asset cooldowns
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for trade activity."""
        self.logger = logging.getLogger("TradingEngine")
        self.logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
        
        # File handler
        fh = logging.FileHandler(self.config.log_file)
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def _reset_daily_limits(self):
        """Reset daily trade counters if a new day has started."""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.daily_trades = 0
            self.daily_volume_usd = 0.0
            self.daily_reset_time = now
            self.logger.info("Daily trade limits reset")
    
    def _check_safety_limits(
        self, 
        product_id: str, 
        side: str, 
        usd_amount: float,
        asset_amount: Optional[float] = None,
        total_asset_value: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Check if a trade passes all safety limits.
        Returns (passed, reason).
        """
        self._reset_daily_limits()
        safety = self.config.safety
        asset = product_id.split("-")[0]
        
        # Check blacklist
        if asset in safety.blacklist:
            return False, f"{asset} is blacklisted"
        
        # Check whitelist
        if safety.whitelist and asset not in safety.whitelist:
            return False, f"{asset} is not in whitelist"
        
        # Check max trade size
        if usd_amount > safety.max_trade_usd:
            return False, f"Trade ${usd_amount:.2f} exceeds max ${safety.max_trade_usd:.2f}"
        
        # Check daily trade count
        if self.daily_trades >= safety.max_trades_per_day:
            return False, f"Daily trade limit reached ({safety.max_trades_per_day})"
        
        # Check daily volume
        if self.daily_volume_usd + usd_amount > safety.max_daily_volume_usd:
            remaining = safety.max_daily_volume_usd - self.daily_volume_usd
            return False, f"Would exceed daily volume limit. Remaining: ${remaining:.2f}"
        
        # Check sell percentage limit
        if side == "SELL" and total_asset_value and asset_amount:
            current_price = usd_amount / asset_amount if asset_amount > 0 else 0
            sell_value = asset_amount * current_price
            sell_percent = (sell_value / total_asset_value) * 100 if total_asset_value > 0 else 0
            
            if sell_percent > safety.max_sell_percent:
                return False, f"Sell {sell_percent:.1f}% exceeds max {safety.max_sell_percent:.1f}%"
        
        # Check cooldown
        if asset in self.last_trade_time:
            elapsed = (datetime.now() - self.last_trade_time[asset]).total_seconds()
            if elapsed < safety.trade_cooldown_seconds:
                remaining = safety.trade_cooldown_seconds - elapsed
                return False, f"Cooldown active for {asset}. {remaining:.0f}s remaining"
        
        return True, "All checks passed"
    
    def preview_trade(
        self,
        product_id: str,
        side: str,
        usd_amount: Optional[float] = None,
        asset_amount: Optional[float] = None
    ) -> dict:
        """
        Preview a trade without executing it.
        Returns estimated execution details.
        """
        result = {
            "product_id": product_id,
            "side": side,
            "mode": self.config.mode.value,
            "safety_check": None,
            "estimate": None,
            "warnings": []
        }
        
        # Get current price for estimates
        asset = product_id.split("-")[0]
        current_price = self.client.get_spot_price(asset)
        
        if not current_price:
            result["warnings"].append(f"Could not get price for {asset}")
            return result
        
        # Calculate amounts
        if usd_amount:
            estimated_asset = usd_amount / current_price
        elif asset_amount:
            usd_amount = asset_amount * current_price
            estimated_asset = asset_amount
        else:
            result["warnings"].append("Must specify usd_amount or asset_amount")
            return result
        
        # Safety check
        passed, reason = self._check_safety_limits(product_id, side, usd_amount)
        result["safety_check"] = {"passed": passed, "reason": reason}
        
        # Get estimate from Coinbase
        try:
            if side.upper() == "BUY":
                preview = self.client.preview_order(
                    product_id=product_id,
                    side="BUY",
                    order_type="MARKET",
                    quote_size=str(round(usd_amount, 2))
                )
            else:
                preview = self.client.preview_order(
                    product_id=product_id,
                    side="SELL",
                    order_type="MARKET",
                    size=str(estimated_asset)
                )
            
            if preview:
                result["estimate"] = {
                    "current_price": current_price,
                    "usd_amount": usd_amount,
                    "asset_amount": estimated_asset,
                    "coinbase_preview": preview
                }
        except Exception as e:
            result["warnings"].append(f"Preview failed: {str(e)}")
            result["estimate"] = {
                "current_price": current_price,
                "usd_amount": usd_amount,
                "asset_amount": estimated_asset
            }
        
        return result
    
    def _confirm_trade(self, product_id: str, side: str, usd_amount: float, asset_amount: float) -> bool:
        """Prompt user for trade confirmation."""
        print("\n" + "="*60)
        print("⚠️  TRADE CONFIRMATION REQUIRED")
        print("="*60)
        print(f"  Action:  {side} {product_id.split('-')[0]}")
        print(f"  Amount:  {asset_amount:.8f} {product_id.split('-')[0]}")
        print(f"  Value:   ${usd_amount:.2f} USD")
        print(f"  Mode:    {self.config.mode.value}")
        print("="*60)
        
        response = input("\nExecute this trade? (yes/no): ").strip().lower()
        return response in ["yes", "y"]
    
    def execute_trade(
        self,
        product_id: str,
        side: str,
        usd_amount: Optional[float] = None,
        asset_amount: Optional[float] = None,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        skip_confirmation: bool = False
    ) -> TradeRecord:
        """
        Execute a trade with safety checks.
        
        Args:
            product_id: Trading pair (e.g., "BTC-USD")
            side: "BUY" or "SELL"
            usd_amount: Amount in USD (for buys)
            asset_amount: Amount of asset (for sells)
            order_type: "MARKET" or "LIMIT"
            limit_price: Price for limit orders
            skip_confirmation: Skip manual confirmation (use with caution)
        
        Returns:
            TradeRecord with execution details
        """
        asset = product_id.split("-")[0]
        side = side.upper()
        
        # Get current price
        current_price = self.client.get_spot_price(asset) or 0
        
        # Normalize amounts
        if side == "BUY":
            if not usd_amount:
                self.logger.error("BUY orders require usd_amount")
                return TradeRecord(
                    timestamp=datetime.now(),
                    product_id=product_id,
                    side=side,
                    order_type=order_type,
                    requested_amount=0,
                    requested_usd=0,
                    executed=False,
                    error="BUY orders require usd_amount"
                )
            calc_asset_amount = usd_amount / current_price if current_price > 0 else 0
        else:  # SELL
            if not asset_amount:
                self.logger.error("SELL orders require asset_amount")
                return TradeRecord(
                    timestamp=datetime.now(),
                    product_id=product_id,
                    side=side,
                    order_type=order_type,
                    requested_amount=0,
                    requested_usd=0,
                    executed=False,
                    error="SELL orders require asset_amount"
                )
            usd_amount = asset_amount * current_price
            calc_asset_amount = asset_amount
        
        # Safety checks
        passed, reason = self._check_safety_limits(product_id, side, usd_amount)
        if not passed:
            self.logger.warning(f"Trade blocked: {reason}")
            return TradeRecord(
                timestamp=datetime.now(),
                product_id=product_id,
                side=side,
                order_type=order_type,
                requested_amount=calc_asset_amount,
                requested_usd=usd_amount,
                executed=False,
                error=f"Safety check failed: {reason}"
            )
        
        # Paper trading mode - simulate only
        if self.config.mode == TradingMode.PAPER:
            self.logger.info(f"[PAPER] {side} {calc_asset_amount:.8f} {asset} (${usd_amount:.2f})")
            record = TradeRecord(
                timestamp=datetime.now(),
                product_id=product_id,
                side=side,
                order_type=order_type,
                requested_amount=calc_asset_amount,
                requested_usd=usd_amount,
                executed=True,
                order_id="PAPER-" + datetime.now().strftime("%Y%m%d%H%M%S"),
                fill_price=current_price,
                fill_amount=calc_asset_amount,
                fees=usd_amount * 0.006  # Estimate 0.6% fee
            )
            self._record_trade(record, asset)
            return record
        
        # Confirmation mode - require approval
        if self.config.mode == TradingMode.CONFIRM and not skip_confirmation:
            if not self._confirm_trade(product_id, side, usd_amount, calc_asset_amount):
                self.logger.info("Trade cancelled by user")
                return TradeRecord(
                    timestamp=datetime.now(),
                    product_id=product_id,
                    side=side,
                    order_type=order_type,
                    requested_amount=calc_asset_amount,
                    requested_usd=usd_amount,
                    executed=False,
                    error="Cancelled by user"
                )
        
        # Execute the actual trade
        self.logger.info(f"Executing {side} order: {calc_asset_amount:.8f} {asset} (${usd_amount:.2f})")
        
        try:
            if order_type == "MARKET":
                if side == "BUY":
                    result = self.client.market_buy(product_id, usd_amount)
                else:
                    result = self.client.market_sell(product_id, calc_asset_amount)
            else:  # LIMIT
                if not limit_price:
                    raise ValueError("Limit orders require limit_price")
                if side == "BUY":
                    result = self.client.limit_buy(product_id, calc_asset_amount, limit_price)
                else:
                    result = self.client.limit_sell(product_id, calc_asset_amount, limit_price)
            
            if result and result.get("success"):
                order_id = result.get("order_id") or result.get("success_response", {}).get("order_id")
                self.logger.info(f"Order placed successfully: {order_id}")
                
                record = TradeRecord(
                    timestamp=datetime.now(),
                    product_id=product_id,
                    side=side,
                    order_type=order_type,
                    requested_amount=calc_asset_amount,
                    requested_usd=usd_amount,
                    executed=True,
                    order_id=order_id,
                    fill_price=current_price,
                    fill_amount=calc_asset_amount
                )
                self._record_trade(record, asset)
                return record
            else:
                error_msg = result.get("error_response", {}).get("message") if result else "Unknown error"
                self.logger.error(f"Order failed: {error_msg}")
                return TradeRecord(
                    timestamp=datetime.now(),
                    product_id=product_id,
                    side=side,
                    order_type=order_type,
                    requested_amount=calc_asset_amount,
                    requested_usd=usd_amount,
                    executed=False,
                    error=error_msg
                )
                
        except Exception as e:
            self.logger.error(f"Trade execution error: {str(e)}")
            return TradeRecord(
                timestamp=datetime.now(),
                product_id=product_id,
                side=side,
                order_type=order_type,
                requested_amount=calc_asset_amount,
                requested_usd=usd_amount,
                executed=False,
                error=str(e)
            )
    
    def _record_trade(self, record: TradeRecord, asset: str):
        """Record a successful trade and update counters."""
        self.trade_history.append(record)
        self.daily_trades += 1
        self.daily_volume_usd += record.requested_usd
        self.last_trade_time[asset] = record.timestamp
    
    def get_trade_summary(self) -> dict:
        """Get summary of today's trading activity."""
        self._reset_daily_limits()
        
        return {
            "mode": self.config.mode.value,
            "today": {
                "trades": self.daily_trades,
                "volume_usd": self.daily_volume_usd,
                "remaining_trades": self.config.safety.max_trades_per_day - self.daily_trades,
                "remaining_volume": self.config.safety.max_daily_volume_usd - self.daily_volume_usd
            },
            "limits": {
                "max_trade_usd": self.config.safety.max_trade_usd,
                "max_trades_per_day": self.config.safety.max_trades_per_day,
                "max_daily_volume_usd": self.config.safety.max_daily_volume_usd
            },
            "recent_trades": [
                {
                    "time": t.timestamp.isoformat(),
                    "product": t.product_id,
                    "side": t.side,
                    "usd": t.requested_usd,
                    "executed": t.executed
                }
                for t in self.trade_history[-10:]
            ]
        }
    
    def buy(self, asset: str, usd_amount: float) -> TradeRecord:
        """Convenience method: Buy asset with USD."""
        return self.execute_trade(
            product_id=f"{asset}-USD",
            side="BUY",
            usd_amount=usd_amount
        )
    
    def sell(self, asset: str, amount: float) -> TradeRecord:
        """Convenience method: Sell asset amount."""
        return self.execute_trade(
            product_id=f"{asset}-USD",
            side="SELL",
            asset_amount=amount
        )
