"""
Base exchange client interface.
All exchange implementations should inherit from this class.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal


@dataclass
class Balance:
    """Represents a balance on an exchange."""
    asset: str
    total: Decimal
    available: Decimal
    staked: Decimal = Decimal("0")
    pending: Decimal = Decimal("0")
    
    @property
    def locked(self) -> Decimal:
        """Amount that is not available for trading."""
        return self.total - self.available


@dataclass
class StakingReward:
    """Represents a staking reward received."""
    asset: str
    amount: Decimal
    timestamp: datetime
    usd_value: Optional[Decimal] = None
    tx_hash: Optional[str] = None
    source: str = ""  # Exchange or protocol name


@dataclass
class Trade:
    """Represents a trade execution."""
    id: str
    timestamp: datetime
    asset: str
    side: str  # "buy" or "sell"
    amount: Decimal
    price: Decimal
    fee: Decimal
    fee_asset: str
    
    @property
    def total_usd(self) -> Decimal:
        """Total USD value of trade (amount * price)."""
        return self.amount * self.price


@dataclass
class OrderResult:
    """Result of placing an order."""
    success: bool
    order_id: Optional[str] = None
    filled_amount: Decimal = Decimal("0")
    filled_price: Decimal = Decimal("0")
    fee: Decimal = Decimal("0")
    error: Optional[str] = None


class ExchangeClient(ABC):
    """Abstract base class for exchange clients."""
    
    name: str = "base"
    
    @abstractmethod
    async def get_balances(self) -> Dict[str, Balance]:
        """
        Get all non-zero balances.
        
        Returns:
            Dict mapping asset symbol to Balance object.
        """
        pass
    
    @abstractmethod
    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """
        Get staking rewards history.
        
        Args:
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            
        Returns:
            List of StakingReward objects.
        """
        pass
    
    @abstractmethod
    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """
        Get trade history.
        
        Args:
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            asset: Filter by specific asset (optional)
            
        Returns:
            List of Trade objects.
        """
        pass
    
    @abstractmethod
    async def place_market_order(
        self,
        asset: str,
        side: str,  # "buy" or "sell"
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,  # USD amount for buys
    ) -> OrderResult:
        """
        Place a market order.
        
        Args:
            asset: Asset to trade (e.g., "BTC")
            side: "buy" or "sell"
            amount: Amount of asset to trade (for sells, or specific amount buys)
            quote_amount: USD amount to spend (for buys)
            
        Returns:
            OrderResult with execution details.
        """
        pass
    
    @abstractmethod
    async def get_ticker_price(self, asset: str) -> Decimal:
        """
        Get current price for an asset.
        
        Args:
            asset: Asset symbol (e.g., "BTC")
            
        Returns:
            Current USD price.
        """
        pass
    
    async def get_all_prices(self, assets: List[str]) -> Dict[str, Decimal]:
        """
        Get prices for multiple assets.
        
        Default implementation calls get_ticker_price for each.
        Override for batch API support.
        
        Args:
            assets: List of asset symbols
            
        Returns:
            Dict mapping asset to price.
        """
        prices = {}
        for asset in assets:
            try:
                prices[asset] = await self.get_ticker_price(asset)
            except Exception as e:
                logging.warning(f"Price fetch failed for {asset}: {e}")
        return prices
    
    @abstractmethod
    async def stake(self, asset: str, amount: Decimal) -> bool:
        """
        Stake an asset.
        
        Args:
            asset: Asset to stake
            amount: Amount to stake
            
        Returns:
            True if successful.
        """
        pass
    
    @abstractmethod
    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """
        Unstake an asset.
        
        Args:
            asset: Asset to unstake
            amount: Amount to unstake
            
        Returns:
            True if successful (may still have unbonding period).
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
