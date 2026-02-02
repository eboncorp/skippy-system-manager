"""
Database Models
===============

SQLAlchemy models for persistent storage of portfolio data,
transactions, staking positions, DCA bots, alerts, and more.

Supports SQLite (development) and PostgreSQL (production).
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


# =============================================================================
# ENUMS
# =============================================================================


class TransactionType(str, PyEnum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    STAKE = "stake"
    UNSTAKE = "unstake"
    STAKING_REWARD = "staking_reward"
    AIRDROP = "airdrop"
    FEE = "fee"
    INTEREST = "interest"


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class StakingStatus(str, PyEnum):
    ACTIVE = "active"
    UNBONDING = "unbonding"
    INACTIVE = "inactive"


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


class CostBasisMethod(str, PyEnum):
    FIFO = "fifo"
    LIFO = "lifo"
    HIFO = "hifo"
    AVG = "avg"


# =============================================================================
# PORTFOLIO MODELS
# =============================================================================


class Portfolio(Base):
    """
    Represents a user's overall portfolio configuration.
    """
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, default="Default Portfolio")
    description = Column(Text, nullable=True)
    default_cost_basis_method = Column(
        Enum(CostBasisMethod),
        default=CostBasisMethod.FIFO
    )
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    exchange_connections = relationship("ExchangeConnection", back_populates="portfolio", cascade="all, delete-orphan")


class ExchangeConnection(Base):
    """
    Stores exchange API connection details (encrypted in production).
    """
    __tablename__ = "exchange_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    exchange = Column(String(50), nullable=False)  # coinbase, kraken, etc.
    api_key_encrypted = Column(Text, nullable=True)  # Encrypted API key
    api_secret_encrypted = Column(Text, nullable=True)  # Encrypted secret
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    sync_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="exchange_connections")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "exchange", name="uq_portfolio_exchange"),
    )


class Holding(Base):
    """
    Represents current holdings of a specific asset.
    """
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset = Column(String(20), nullable=False)
    exchange = Column(String(50), nullable=True)  # NULL for aggregated
    amount = Column(Numeric(28, 18), nullable=False, default=0)
    cost_basis_usd = Column(Numeric(18, 2), nullable=True)
    last_price_usd = Column(Numeric(18, 8), nullable=True)
    last_price_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset", "exchange", name="uq_holding"),
        Index("ix_holdings_asset", "asset"),
        Index("ix_holdings_exchange", "exchange"),
    )

    @property
    def value_usd(self) -> Optional[Decimal]:
        if self.last_price_usd and self.amount:
            return Decimal(str(self.amount)) * Decimal(str(self.last_price_usd))
        return None


# =============================================================================
# TRANSACTION MODELS
# =============================================================================


class Transaction(Base):
    """
    Records all transactions including trades, transfers, staking, etc.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    external_id = Column(String(100), nullable=True)  # Exchange transaction ID
    tx_type = Column(Enum(TransactionType), nullable=False)
    asset = Column(String(20), nullable=False)
    amount = Column(Numeric(28, 18), nullable=False)
    price_usd = Column(Numeric(18, 8), nullable=True)
    value_usd = Column(Numeric(18, 2), nullable=True)
    fee = Column(Numeric(18, 8), nullable=True, default=0)
    fee_asset = Column(String(20), nullable=True)
    exchange = Column(String(50), nullable=True)
    order_id = Column(String(100), nullable=True)
    wallet_address = Column(String(100), nullable=True)
    tx_hash = Column(String(100), nullable=True)  # On-chain tx hash
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # For tax lot tracking
    tax_lots = relationship("TaxLot", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_transactions_asset", "asset"),
        Index("ix_transactions_type", "tx_type"),
        Index("ix_transactions_exchange", "exchange"),
        Index("ix_transactions_timestamp", "timestamp"),
        Index("ix_transactions_external_id", "external_id"),
    )


class TaxLot(Base):
    """
    Tracks individual tax lots for cost basis calculation.
    """
    __tablename__ = "tax_lots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    asset = Column(String(20), nullable=False)
    amount = Column(Numeric(28, 18), nullable=False)
    remaining_amount = Column(Numeric(28, 18), nullable=False)
    cost_basis_usd = Column(Numeric(18, 2), nullable=False)
    cost_per_unit_usd = Column(Numeric(18, 8), nullable=False)
    acquired_at = Column(DateTime, nullable=False)
    is_long_term = Column(Boolean, default=False)  # Held > 1 year
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    transaction = relationship("Transaction", back_populates="tax_lots")
    disposals = relationship("TaxLotDisposal", back_populates="tax_lot", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tax_lots_asset", "asset"),
        Index("ix_tax_lots_acquired_at", "acquired_at"),
    )


class TaxLotDisposal(Base):
    """
    Records when tax lots are sold/disposed.
    """
    __tablename__ = "tax_lot_disposals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tax_lot_id = Column(Integer, ForeignKey("tax_lots.id"), nullable=False)
    sell_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    amount = Column(Numeric(28, 18), nullable=False)
    proceeds_usd = Column(Numeric(18, 2), nullable=False)
    cost_basis_usd = Column(Numeric(18, 2), nullable=False)
    gain_loss_usd = Column(Numeric(18, 2), nullable=False)
    is_long_term = Column(Boolean, nullable=False)
    disposed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tax_lot = relationship("TaxLot", back_populates="disposals")


# =============================================================================
# STAKING MODELS
# =============================================================================


class StakingPosition(Base):
    """
    Tracks staking positions across exchanges.
    """
    __tablename__ = "staking_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    exchange = Column(String(50), nullable=False)
    asset = Column(String(20), nullable=False)
    amount = Column(Numeric(28, 18), nullable=False)
    apy = Column(Numeric(8, 4), nullable=True)
    rewards_earned = Column(Numeric(28, 18), nullable=False, default=0)
    rewards_claimed = Column(Numeric(28, 18), nullable=False, default=0)
    status = Column(Enum(StakingStatus), default=StakingStatus.ACTIVE)
    validator = Column(String(100), nullable=True)
    lock_period_days = Column(Integer, nullable=True)
    unlock_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    rewards = relationship("StakingReward", back_populates="position", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_staking_positions_asset", "asset"),
        Index("ix_staking_positions_exchange", "exchange"),
        Index("ix_staking_positions_status", "status"),
    )


class StakingReward(Base):
    """
    Records individual staking reward distributions.
    """
    __tablename__ = "staking_rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(Integer, ForeignKey("staking_positions.id"), nullable=False)
    asset = Column(String(20), nullable=False)
    amount = Column(Numeric(28, 18), nullable=False)
    value_usd = Column(Numeric(18, 2), nullable=True)
    reward_type = Column(String(50), nullable=True)  # e.g., "staking", "inflation"
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    position = relationship("StakingPosition", back_populates="rewards")


# =============================================================================
# DEFI MODELS
# =============================================================================


class DeFiPosition(Base):
    """
    Tracks DeFi protocol positions.
    """
    __tablename__ = "defi_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    protocol = Column(String(50), nullable=False)  # aave, uniswap, lido, etc.
    chain = Column(String(50), nullable=False)  # ethereum, polygon, etc.
    position_type = Column(String(50), nullable=False)  # lending, borrowing, liquidity, staking
    wallet_address = Column(String(100), nullable=False)
    contract_address = Column(String(100), nullable=True)

    # Position details (flexible JSON-like columns)
    asset = Column(String(20), nullable=True)
    asset_amount = Column(Numeric(28, 18), nullable=True)
    asset2 = Column(String(20), nullable=True)  # For LP positions
    asset2_amount = Column(Numeric(28, 18), nullable=True)

    value_usd = Column(Numeric(18, 2), nullable=True)
    apy = Column(Numeric(8, 4), nullable=True)
    health_factor = Column(Numeric(8, 4), nullable=True)  # For lending

    is_active = Column(Boolean, default=True)
    last_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_defi_positions_protocol", "protocol"),
        Index("ix_defi_positions_chain", "chain"),
        Index("ix_defi_positions_wallet", "wallet_address"),
    )


# =============================================================================
# AUTOMATION MODELS
# =============================================================================


class DCABot(Base):
    """
    Dollar Cost Averaging bot configuration.
    """
    __tablename__ = "dca_bots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    name = Column(String(100), nullable=True)
    exchange = Column(String(50), nullable=False)
    asset = Column(String(20), nullable=False)
    quote_asset = Column(String(20), nullable=False, default="USD")
    amount = Column(Numeric(18, 2), nullable=False)  # Per execution
    frequency = Column(String(20), nullable=False)  # hourly, daily, weekly, biweekly, monthly

    # Execution tracking
    next_execution_at = Column(DateTime, nullable=True)
    last_execution_at = Column(DateTime, nullable=True)
    total_invested = Column(Numeric(18, 2), nullable=False, default=0)
    total_acquired = Column(Numeric(28, 18), nullable=False, default=0)
    execution_count = Column(Integer, nullable=False, default=0)

    # Limits
    max_total = Column(Numeric(18, 2), nullable=True)  # Max total investment
    end_date = Column(DateTime, nullable=True)

    status = Column(Enum(DCAStatus), default=DCAStatus.ACTIVE)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    executions = relationship("DCAExecution", back_populates="bot", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_dca_bots_status", "status"),
        Index("ix_dca_bots_next_execution", "next_execution_at"),
    )


class DCAExecution(Base):
    """
    Records individual DCA bot executions.
    """
    __tablename__ = "dca_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey("dca_bots.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    amount_invested = Column(Numeric(18, 2), nullable=False)
    amount_acquired = Column(Numeric(28, 18), nullable=False)
    price = Column(Numeric(18, 8), nullable=False)
    fee = Column(Numeric(18, 8), nullable=True)
    status = Column(String(20), nullable=False)  # success, failed, skipped
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    bot = relationship("DCABot", back_populates="executions")


class Alert(Base):
    """
    Price and portfolio alerts.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    name = Column(String(100), nullable=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    asset = Column(String(20), nullable=True)  # For price alerts
    threshold = Column(Numeric(18, 8), nullable=False)

    # Notification settings (stored as comma-separated)
    notification_channels = Column(String(200), nullable=False, default="app")

    # Trigger tracking
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    triggered_at = Column(DateTime, nullable=True)
    triggered_value = Column(Numeric(18, 8), nullable=True)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    cooldown_minutes = Column(Integer, nullable=True)  # Min time between triggers

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    triggers = relationship("AlertTrigger", back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_asset", "asset"),
    )


class AlertTrigger(Base):
    """
    Records alert trigger history.
    """
    __tablename__ = "alert_triggers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    triggered_value = Column(Numeric(18, 8), nullable=False)
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(String(200), nullable=True)
    triggered_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    alert = relationship("Alert", back_populates="triggers")


# =============================================================================
# SNAPSHOT MODELS
# =============================================================================


class PortfolioSnapshot(Base):
    """
    Historical portfolio value snapshots.
    """
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    total_value_usd = Column(Numeric(18, 2), nullable=False)
    total_cost_basis_usd = Column(Numeric(18, 2), nullable=True)
    unrealized_pnl_usd = Column(Numeric(18, 2), nullable=True)
    realized_pnl_usd = Column(Numeric(18, 2), nullable=True)

    # Breakdown by category
    spot_value_usd = Column(Numeric(18, 2), nullable=True)
    staking_value_usd = Column(Numeric(18, 2), nullable=True)
    defi_value_usd = Column(Numeric(18, 2), nullable=True)
    nft_value_usd = Column(Numeric(18, 2), nullable=True)

    snapshot_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
    holdings = relationship("HoldingSnapshot", back_populates="portfolio_snapshot", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_portfolio_snapshots_at", "snapshot_at"),
    )


class HoldingSnapshot(Base):
    """
    Individual holding values at snapshot time.
    """
    __tablename__ = "holding_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_snapshot_id = Column(Integer, ForeignKey("portfolio_snapshots.id"), nullable=False)
    asset = Column(String(20), nullable=False)
    amount = Column(Numeric(28, 18), nullable=False)
    price_usd = Column(Numeric(18, 8), nullable=False)
    value_usd = Column(Numeric(18, 2), nullable=False)
    allocation_percent = Column(Numeric(8, 4), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    portfolio_snapshot = relationship("PortfolioSnapshot", back_populates="holdings")

    __table_args__ = (
        Index("ix_holding_snapshots_asset", "asset"),
    )


class PriceSnapshot(Base):
    """
    Historical price data cache.
    """
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset = Column(String(20), nullable=False)
    price_usd = Column(Numeric(18, 8), nullable=False)
    volume_24h_usd = Column(Numeric(24, 2), nullable=True)
    market_cap_usd = Column(Numeric(24, 2), nullable=True)
    change_24h_percent = Column(Numeric(8, 4), nullable=True)
    source = Column(String(50), nullable=True)  # coingecko, exchange, etc.
    snapshot_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_price_snapshots_asset_at", "asset", "snapshot_at"),
    )


# =============================================================================
# DATABASE UTILITIES
# =============================================================================


def create_database(database_url: str = "sqlite:///portfolio.db", echo: bool = False):
    """
    Create database engine and all tables.

    Args:
        database_url: SQLAlchemy database URL
        echo: Enable SQL query logging

    Returns:
        Tuple of (engine, session_factory)
    """
    engine = create_engine(database_url, echo=echo)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def get_session(database_url: str = "sqlite:///portfolio.db"):
    """
    Get a database session.

    Args:
        database_url: SQLAlchemy database URL

    Returns:
        Session instance
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()


# =============================================================================
# ASYNC SUPPORT (for use with async SQLAlchemy)
# =============================================================================

# For async support, use:
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
#
# async_engine = create_async_engine("sqlite+aiosqlite:///portfolio.db")
# async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
