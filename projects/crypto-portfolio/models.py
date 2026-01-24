"""
Database Models
===============

SQLAlchemy models for persistent storage of portfolio data.

Tables:
- portfolios: Portfolio snapshots over time
- transactions: All buy/sell/transfer records
- tax_lots: Cost basis tracking per lot
- staking_positions: Staking history & rewards
- dca_bots: Bot configs & execution log
- alerts: Alert configs & trigger history
- price_cache: Cached price data
- wallets: Tracked wallet addresses
- defi_positions: DeFi protocol positions

Usage:
    from database.models import get_engine, get_session, Portfolio, Transaction
    
    engine = get_engine("sqlite:///portfolio.db")
    async with get_session(engine) as session:
        portfolio = Portfolio(...)
        session.add(portfolio)
        await session.commit()
"""

import os
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


# =============================================================================
# ENUMS
# =============================================================================


class TransactionType(str, PyEnum):
    BUY = "buy"
    SELL = "sell"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    FEE = "fee"
    AIRDROP = "airdrop"
    FORK = "fork"


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AlertType(str, PyEnum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PERCENT_CHANGE = "percent_change"
    PORTFOLIO_VALUE = "portfolio_value"


class AlertStatus(str, PyEnum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"


class DCAStatus(str, PyEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DELETED = "deleted"


class StakingStatus(str, PyEnum):
    ACTIVE = "active"
    UNBONDING = "unbonding"
    COMPLETED = "completed"


# =============================================================================
# MODELS
# =============================================================================


class Portfolio(Base):
    """Portfolio snapshot at a point in time."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Totals
    total_value_usd = Column(Numeric(20, 8), nullable=False)
    total_cost_basis_usd = Column(Numeric(20, 8), nullable=True)
    total_staking_value_usd = Column(Numeric(20, 8), default=0)
    total_defi_value_usd = Column(Numeric(20, 8), default=0)
    total_nft_value_usd = Column(Numeric(20, 8), default=0)
    
    # Breakdown stored as JSON
    holdings_by_asset = Column(JSON, nullable=True)  # {"BTC": {"amount": 1.5, "value_usd": 67500}}
    holdings_by_exchange = Column(JSON, nullable=True)  # {"coinbase": {"value_usd": 50000}}
    
    # Metadata
    snapshot_type = Column(String(20), default="scheduled")  # scheduled, manual, trade
    
    __table_args__ = (
        Index("ix_portfolios_timestamp_type", "timestamp", "snapshot_type"),
    )


class Transaction(Base):
    """Individual transaction record."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100), nullable=True, index=True)  # Exchange's transaction ID
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(30, 18), nullable=False)
    
    # Pricing
    price_usd = Column(Numeric(20, 8), nullable=True)
    total_usd = Column(Numeric(20, 8), nullable=True)
    fee_amount = Column(Numeric(20, 8), default=0)
    fee_currency = Column(String(20), nullable=True)
    fee_usd = Column(Numeric(20, 8), default=0)
    
    # Source/destination
    exchange = Column(String(50), nullable=True, index=True)
    wallet_address = Column(String(100), nullable=True)
    counterparty = Column(String(100), nullable=True)  # For transfers
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional data
    notes = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)  # Original API response
    
    # Relationships
    tax_lots = relationship("TaxLot", back_populates="transaction")
    
    __table_args__ = (
        Index("ix_transactions_asset_timestamp", "asset", "timestamp"),
        Index("ix_transactions_exchange_timestamp", "exchange", "timestamp"),
    )


class TaxLot(Base):
    """Individual tax lot for cost basis tracking."""
    
    __tablename__ = "tax_lots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    
    # Lot details
    asset = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(30, 18), nullable=False)
    remaining_amount = Column(Numeric(30, 18), nullable=False)  # After partial disposals
    cost_basis_usd = Column(Numeric(20, 8), nullable=False)
    cost_basis_per_unit = Column(Numeric(20, 8), nullable=False)
    
    # Acquisition info
    acquired_at = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(50), nullable=True)
    
    # Disposal info (if sold)
    disposed_at = Column(DateTime, nullable=True)
    proceeds_usd = Column(Numeric(20, 8), nullable=True)
    gain_loss_usd = Column(Numeric(20, 8), nullable=True)
    is_long_term = Column(Boolean, nullable=True)  # Held > 1 year
    
    # Status
    is_closed = Column(Boolean, default=False, index=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="tax_lots")
    
    __table_args__ = (
        Index("ix_tax_lots_asset_acquired", "asset", "acquired_at"),
        Index("ix_tax_lots_open", "asset", "is_closed", "acquired_at"),
    )


class StakingPosition(Base):
    """Staking position record."""
    
    __tablename__ = "staking_positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100), nullable=True)
    
    # Position details
    exchange = Column(String(50), nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(30, 18), nullable=False)
    
    # Yield info
    apy = Column(Numeric(10, 4), nullable=True)
    rewards_earned = Column(Numeric(30, 18), default=0)
    rewards_claimed = Column(Numeric(30, 18), default=0)
    
    # Status
    status = Column(Enum(StakingStatus), default=StakingStatus.ACTIVE, index=True)
    validator = Column(String(200), nullable=True)
    
    # Timestamps
    staked_at = Column(DateTime, nullable=False)
    unbonding_at = Column(DateTime, nullable=True)
    unstaked_at = Column(DateTime, nullable=True)
    
    # Lock info
    lock_period_days = Column(Integer, nullable=True)
    unlock_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_staking_exchange_asset", "exchange", "asset"),
    )


class DCABot(Base):
    """Dollar Cost Averaging bot configuration."""
    
    __tablename__ = "dca_bots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    
    # Configuration
    exchange = Column(String(50), nullable=False)
    asset = Column(String(20), nullable=False)
    quote_currency = Column(String(20), default="USD")
    amount_per_execution = Column(Numeric(20, 8), nullable=False)
    frequency = Column(String(20), nullable=False)  # hourly, daily, weekly, biweekly, monthly
    
    # Limits
    max_total_amount = Column(Numeric(20, 8), nullable=True)
    max_executions = Column(Integer, nullable=True)
    
    # Status
    status = Column(Enum(DCAStatus), default=DCAStatus.ACTIVE, index=True)
    
    # Execution tracking
    total_invested = Column(Numeric(20, 8), default=0)
    total_acquired = Column(Numeric(30, 18), default=0)
    execution_count = Column(Integer, default=0)
    average_price = Column(Numeric(20, 8), nullable=True)
    
    # Scheduling
    next_execution_at = Column(DateTime, nullable=True, index=True)
    last_execution_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("DCAExecution", back_populates="bot")


class DCAExecution(Base):
    """Individual DCA bot execution record."""
    
    __tablename__ = "dca_executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey("dca_bots.id"), nullable=False)
    
    # Execution details
    amount_usd = Column(Numeric(20, 8), nullable=False)
    amount_acquired = Column(Numeric(30, 18), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    fee_usd = Column(Numeric(20, 8), default=0)
    
    # Status
    status = Column(String(20), nullable=False)  # success, failed, skipped
    error_message = Column(Text, nullable=True)
    
    # Order reference
    order_id = Column(String(100), nullable=True)
    
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    bot = relationship("DCABot", back_populates="executions")


class Alert(Base):
    """Price and portfolio alerts."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Alert configuration
    alert_type = Column(Enum(AlertType), nullable=False)
    asset = Column(String(20), nullable=True)  # For price alerts
    threshold = Column(Numeric(20, 8), nullable=False)
    comparison = Column(String(10), nullable=True)  # above, below, change
    
    # Notification settings
    notification_channels = Column(JSON, default=["app"])  # app, email, sms, webhook
    cooldown_minutes = Column(Integer, default=60)  # Min time between triggers
    
    # Status
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, index=True)
    
    # Trigger tracking
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)
    last_value = Column(Numeric(20, 8), nullable=True)
    
    # Metadata
    note = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    triggers = relationship("AlertTrigger", back_populates="alert")


class AlertTrigger(Base):
    """Alert trigger history."""
    
    __tablename__ = "alert_triggers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    
    # Trigger details
    triggered_value = Column(Numeric(20, 8), nullable=False)
    threshold = Column(Numeric(20, 8), nullable=False)
    
    # Notification status
    notifications_sent = Column(JSON, nullable=True)  # {"email": true, "sms": false}
    
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    alert = relationship("Alert", back_populates="triggers")


class Wallet(Base):
    """Tracked wallet addresses."""
    
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Wallet info
    address = Column(String(100), nullable=False, unique=True)
    chain = Column(String(20), nullable=False)  # ethereum, polygon, arbitrum, etc.
    label = Column(String(100), nullable=True)
    
    # Tracking settings
    track_transactions = Column(Boolean, default=True)
    track_defi = Column(Boolean, default=True)
    track_nfts = Column(Boolean, default=False)
    
    # Last sync
    last_synced_at = Column(DateTime, nullable=True)
    last_block_synced = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_wallets_chain_address", "chain", "address"),
    )


class DeFiPosition(Base):
    """DeFi protocol position."""
    
    __tablename__ = "defi_positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Position identification
    protocol = Column(String(50), nullable=False, index=True)
    chain = Column(String(20), nullable=False)
    wallet_address = Column(String(100), nullable=False, index=True)
    position_type = Column(String(30), nullable=False)  # lending, borrowing, liquidity, staking
    
    # Position details
    pool_address = Column(String(100), nullable=True)
    pool_name = Column(String(100), nullable=True)
    
    # For single asset positions
    asset = Column(String(20), nullable=True)
    amount = Column(Numeric(30, 18), nullable=True)
    
    # For LP positions
    token0 = Column(String(20), nullable=True)
    token1 = Column(String(20), nullable=True)
    token0_amount = Column(Numeric(30, 18), nullable=True)
    token1_amount = Column(Numeric(30, 18), nullable=True)
    
    # Value tracking
    value_usd = Column(Numeric(20, 8), nullable=True)
    apy = Column(Numeric(10, 4), nullable=True)
    
    # Risk metrics
    health_factor = Column(Numeric(10, 4), nullable=True)  # For lending
    impermanent_loss_percent = Column(Numeric(10, 4), nullable=True)  # For LP
    
    # Earnings
    earnings_usd = Column(Numeric(20, 8), default=0)
    fees_earned_usd = Column(Numeric(20, 8), default=0)
    rewards_earned_usd = Column(Numeric(20, 8), default=0)
    
    # Timestamps
    opened_at = Column(DateTime, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_defi_protocol_wallet", "protocol", "wallet_address"),
    )


class PriceCache(Base):
    """Cached price data."""
    
    __tablename__ = "price_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    asset = Column(String(20), nullable=False, index=True)
    price_usd = Column(Numeric(20, 8), nullable=False)
    
    # 24h data
    price_24h_ago = Column(Numeric(20, 8), nullable=True)
    change_24h_percent = Column(Numeric(10, 4), nullable=True)
    high_24h = Column(Numeric(20, 8), nullable=True)
    low_24h = Column(Numeric(20, 8), nullable=True)
    volume_24h_usd = Column(Numeric(20, 8), nullable=True)
    
    # Market data
    market_cap_usd = Column(Numeric(30, 8), nullable=True)
    circulating_supply = Column(Numeric(30, 8), nullable=True)
    
    # Source
    source = Column(String(30), nullable=True)  # coingecko, coinbase, etc.
    
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        UniqueConstraint("asset", name="uq_price_cache_asset"),
    )


class Setting(Base):
    """Application settings storage."""
    
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(JSON, nullable=True)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# DATABASE UTILITIES
# =============================================================================


def get_database_url(url: Optional[str] = None) -> str:
    """Get database URL from parameter or environment."""
    if url:
        return url
    return os.getenv("DATABASE_URL", "sqlite:///portfolio.db")


def get_async_database_url(url: Optional[str] = None) -> str:
    """Convert database URL to async version."""
    url = get_database_url(url)
    
    if url.startswith("sqlite:"):
        return url.replace("sqlite:", "sqlite+aiosqlite:")
    elif url.startswith("postgresql:"):
        return url.replace("postgresql:", "postgresql+asyncpg:")
    
    return url


def get_engine(url: Optional[str] = None, echo: bool = False):
    """Create synchronous database engine."""
    database_url = get_database_url(url)
    engine = create_engine(database_url, echo=echo)
    
    # Enable foreign keys for SQLite
    if database_url.startswith("sqlite:"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    return engine


def get_async_engine(url: Optional[str] = None, echo: bool = False):
    """Create asynchronous database engine."""
    database_url = get_async_database_url(url)
    return create_async_engine(database_url, echo=echo)


def get_session_factory(engine):
    """Create synchronous session factory."""
    return sessionmaker(bind=engine)


def get_async_session_factory(engine):
    """Create asynchronous session factory."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session(engine):
    """Context manager for async database sessions."""
    factory = get_async_session_factory(engine)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def create_tables(engine):
    """Create all tables."""
    Base.metadata.create_all(engine)


async def create_tables_async(engine):
    """Create all tables asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def drop_tables(engine):
    """Drop all tables."""
    Base.metadata.drop_all(engine)


async def drop_tables_async(engine):
    """Drop all tables asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate database usage."""
    from datetime import datetime
    from decimal import Decimal
    
    # Create async engine
    engine = get_async_engine("sqlite+aiosqlite:///test_portfolio.db")
    
    # Create tables
    await create_tables_async(engine)
    
    # Use session
    async with get_session(engine) as session:
        # Create portfolio snapshot
        portfolio = Portfolio(
            total_value_usd=Decimal("127834.56"),
            total_cost_basis_usd=Decimal("98500.00"),
            holdings_by_asset={
                "BTC": {"amount": "1.5234", "value_usd": "68553.00"},
                "ETH": {"amount": "12.847", "value_usd": "35169.49"}
            }
        )
        session.add(portfolio)
        
        # Create transaction
        transaction = Transaction(
            transaction_type=TransactionType.BUY,
            asset="BTC",
            amount=Decimal("0.5"),
            price_usd=Decimal("45000"),
            total_usd=Decimal("22500"),
            exchange="coinbase",
            timestamp=datetime.utcnow()
        )
        session.add(transaction)
        
        # Commit is automatic via context manager
    
    print("Database example completed!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
