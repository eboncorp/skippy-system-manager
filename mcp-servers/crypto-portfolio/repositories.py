"""
Database Repositories
=====================

Repository pattern implementation for clean data access.
Each repository handles CRUD operations for related models.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .database import (
    Alert,
    AlertStatus,
    AlertTrigger,
    AlertType,
    CostBasisMethod,
    DCABot,
    DCAExecution,
    DCAStatus,
    Holding,
    HoldingSnapshot,
    Portfolio,
    PortfolioSnapshot,
    PriceSnapshot,
    StakingPosition,
    StakingReward,
    StakingStatus,
    TaxLot,
    TaxLotDisposal,
    Transaction,
    TransactionType,
)


# =============================================================================
# BASE REPOSITORY
# =============================================================================


class BaseRepository:
    """Base repository with common operations."""

    def __init__(self, session: Session):
        self.session = session

    def commit(self):
        """Commit the current transaction."""
        self.session.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.session.rollback()

    def refresh(self, obj):
        """Refresh an object from the database."""
        self.session.refresh(obj)


# =============================================================================
# PORTFOLIO REPOSITORY
# =============================================================================


class PortfolioRepository(BaseRepository):
    """Repository for portfolio operations."""

    def create(self, name: str = "Default Portfolio", **kwargs) -> Portfolio:
        """Create a new portfolio."""
        portfolio = Portfolio(name=name, **kwargs)
        self.session.add(portfolio)
        self.commit()
        return portfolio

    def get_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        return self.session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def get_default(self) -> Portfolio:
        """Get or create the default portfolio."""
        portfolio = self.session.query(Portfolio).first()
        if not portfolio:
            portfolio = self.create()
        return portfolio

    def get_total_value(self, portfolio_id: int) -> Decimal:
        """Calculate total portfolio value."""
        holdings = self.session.query(Holding).filter(
            Holding.portfolio_id == portfolio_id
        ).all()

        total = Decimal("0")
        for h in holdings:
            if h.value_usd:
                total += Decimal(str(h.value_usd))
        return total


# =============================================================================
# HOLDING REPOSITORY
# =============================================================================


class HoldingRepository(BaseRepository):
    """Repository for holding operations."""

    def upsert(
        self,
        portfolio_id: int,
        asset: str,
        amount: Decimal,
        exchange: Optional[str] = None,
        cost_basis_usd: Optional[Decimal] = None
    ) -> Holding:
        """Create or update a holding."""
        holding = self.session.query(Holding).filter(
            and_(
                Holding.portfolio_id == portfolio_id,
                Holding.asset == asset,
                Holding.exchange == exchange
            )
        ).first()

        if holding:
            holding.amount = amount
            if cost_basis_usd is not None:
                holding.cost_basis_usd = cost_basis_usd
        else:
            holding = Holding(
                portfolio_id=portfolio_id,
                asset=asset,
                amount=amount,
                exchange=exchange,
                cost_basis_usd=cost_basis_usd
            )
            self.session.add(holding)

        self.commit()
        return holding

    def get_by_asset(
        self,
        portfolio_id: int,
        asset: str,
        exchange: Optional[str] = None
    ) -> Optional[Holding]:
        """Get holding by asset and optionally exchange."""
        query = self.session.query(Holding).filter(
            and_(
                Holding.portfolio_id == portfolio_id,
                Holding.asset == asset
            )
        )
        if exchange:
            query = query.filter(Holding.exchange == exchange)
        return query.first()

    def get_all(
        self,
        portfolio_id: int,
        exchange: Optional[str] = None,
        min_value_usd: Optional[Decimal] = None
    ) -> List[Holding]:
        """Get all holdings with optional filters."""
        query = self.session.query(Holding).filter(
            Holding.portfolio_id == portfolio_id
        )

        if exchange:
            query = query.filter(Holding.exchange == exchange)

        holdings = query.all()

        if min_value_usd:
            holdings = [h for h in holdings if h.value_usd and h.value_usd >= min_value_usd]

        return holdings

    def get_by_exchange(self, portfolio_id: int) -> Dict[str, List[Holding]]:
        """Get holdings grouped by exchange."""
        holdings = self.session.query(Holding).filter(
            Holding.portfolio_id == portfolio_id
        ).all()

        result: Dict[str, List[Holding]] = {}
        for h in holdings:
            exchange = h.exchange or "unknown"
            if exchange not in result:
                result[exchange] = []
            result[exchange].append(h)

        return result

    def update_price(
        self,
        portfolio_id: int,
        asset: str,
        price_usd: Decimal,
        exchange: Optional[str] = None
    ):
        """Update the price for a holding."""
        query = self.session.query(Holding).filter(
            and_(
                Holding.portfolio_id == portfolio_id,
                Holding.asset == asset
            )
        )
        if exchange:
            query = query.filter(Holding.exchange == exchange)

        query.update({
            "last_price_usd": price_usd,
            "last_price_updated_at": datetime.utcnow()
        })
        self.commit()


# =============================================================================
# TRANSACTION REPOSITORY
# =============================================================================


class TransactionRepository(BaseRepository):
    """Repository for transaction operations."""

    def create(
        self,
        portfolio_id: int,
        tx_type: TransactionType,
        asset: str,
        amount: Decimal,
        timestamp: datetime,
        **kwargs
    ) -> Transaction:
        """Create a new transaction."""
        tx = Transaction(
            portfolio_id=portfolio_id,
            tx_type=tx_type,
            asset=asset,
            amount=amount,
            timestamp=timestamp,
            **kwargs
        )
        self.session.add(tx)
        self.commit()
        return tx

    def get_by_id(self, tx_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""
        return self.session.query(Transaction).filter(Transaction.id == tx_id).first()

    def get_history(
        self,
        portfolio_id: int,
        asset: Optional[str] = None,
        tx_type: Optional[TransactionType] = None,
        exchange: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Transaction], int]:
        """Get transaction history with filters and pagination."""
        query = self.session.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id
        )

        if asset:
            query = query.filter(Transaction.asset == asset)
        if tx_type:
            query = query.filter(Transaction.tx_type == tx_type)
        if exchange:
            query = query.filter(Transaction.exchange == exchange)
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)

        total = query.count()
        transactions = query.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit).all()

        return transactions, total

    def get_by_external_id(self, external_id: str) -> Optional[Transaction]:
        """Get transaction by external (exchange) ID."""
        return self.session.query(Transaction).filter(
            Transaction.external_id == external_id
        ).first()

    def get_for_tax_year(
        self,
        portfolio_id: int,
        year: int,
        include_types: Optional[List[TransactionType]] = None
    ) -> List[Transaction]:
        """Get transactions for a specific tax year."""
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)

        query = self.session.query(Transaction).filter(
            and_(
                Transaction.portfolio_id == portfolio_id,
                Transaction.timestamp >= start,
                Transaction.timestamp <= end
            )
        )

        if include_types:
            query = query.filter(Transaction.tx_type.in_(include_types))

        return query.order_by(Transaction.timestamp).all()


# =============================================================================
# TAX LOT REPOSITORY
# =============================================================================


class TaxLotRepository(BaseRepository):
    """Repository for tax lot operations."""

    def create(
        self,
        transaction_id: int,
        asset: str,
        amount: Decimal,
        cost_basis_usd: Decimal,
        acquired_at: datetime
    ) -> TaxLot:
        """Create a new tax lot."""
        cost_per_unit = cost_basis_usd / amount if amount > 0 else Decimal("0")

        lot = TaxLot(
            transaction_id=transaction_id,
            asset=asset,
            amount=amount,
            remaining_amount=amount,
            cost_basis_usd=cost_basis_usd,
            cost_per_unit_usd=cost_per_unit,
            acquired_at=acquired_at
        )
        self.session.add(lot)
        self.commit()
        return lot

    def get_available_lots(
        self,
        asset: str,
        method: CostBasisMethod = CostBasisMethod.FIFO
    ) -> List[TaxLot]:
        """Get available tax lots for disposal, ordered by method."""
        query = self.session.query(TaxLot).filter(
            and_(
                TaxLot.asset == asset,
                TaxLot.remaining_amount > 0
            )
        )

        if method == CostBasisMethod.FIFO:
            query = query.order_by(TaxLot.acquired_at.asc())
        elif method == CostBasisMethod.LIFO:
            query = query.order_by(TaxLot.acquired_at.desc())
        elif method == CostBasisMethod.HIFO:
            query = query.order_by(TaxLot.cost_per_unit_usd.desc())

        return query.all()

    def dispose(
        self,
        lot: TaxLot,
        sell_transaction_id: int,
        amount: Decimal,
        proceeds_usd: Decimal,
        disposed_at: datetime
    ) -> TaxLotDisposal:
        """Record disposal of a tax lot."""
        cost_basis = lot.cost_per_unit_usd * amount
        gain_loss = proceeds_usd - cost_basis

        # Check if long-term (held > 1 year)
        holding_period = disposed_at - lot.acquired_at
        is_long_term = holding_period.days > 365

        disposal = TaxLotDisposal(
            tax_lot_id=lot.id,
            sell_transaction_id=sell_transaction_id,
            amount=amount,
            proceeds_usd=proceeds_usd,
            cost_basis_usd=cost_basis,
            gain_loss_usd=gain_loss,
            is_long_term=is_long_term,
            disposed_at=disposed_at
        )
        self.session.add(disposal)

        # Update remaining amount
        lot.remaining_amount -= amount
        lot.is_long_term = is_long_term

        self.commit()
        return disposal

    def get_unrealized_gains(self, asset: str, current_price: Decimal) -> Dict[str, Decimal]:
        """Calculate unrealized gains for an asset."""
        lots = self.session.query(TaxLot).filter(
            and_(
                TaxLot.asset == asset,
                TaxLot.remaining_amount > 0
            )
        ).all()

        total_amount = Decimal("0")
        total_cost_basis = Decimal("0")

        for lot in lots:
            total_amount += lot.remaining_amount
            total_cost_basis += lot.remaining_amount * lot.cost_per_unit_usd

        current_value = total_amount * current_price
        unrealized_gain = current_value - total_cost_basis

        return {
            "amount": total_amount,
            "cost_basis": total_cost_basis,
            "current_value": current_value,
            "unrealized_gain": unrealized_gain
        }


# =============================================================================
# STAKING REPOSITORY
# =============================================================================


class StakingRepository(BaseRepository):
    """Repository for staking operations."""

    def create_or_update(
        self,
        portfolio_id: int,
        exchange: str,
        asset: str,
        amount: Decimal,
        apy: Optional[Decimal] = None,
        **kwargs
    ) -> StakingPosition:
        """Create or update a staking position."""
        position = self.session.query(StakingPosition).filter(
            and_(
                StakingPosition.portfolio_id == portfolio_id,
                StakingPosition.exchange == exchange,
                StakingPosition.asset == asset
            )
        ).first()

        if position:
            position.amount = amount
            if apy is not None:
                position.apy = apy
            for key, value in kwargs.items():
                setattr(position, key, value)
        else:
            position = StakingPosition(
                portfolio_id=portfolio_id,
                exchange=exchange,
                asset=asset,
                amount=amount,
                apy=apy,
                started_at=datetime.utcnow(),
                **kwargs
            )
            self.session.add(position)

        self.commit()
        return position

    def get_all(
        self,
        portfolio_id: int,
        exchange: Optional[str] = None,
        status: Optional[StakingStatus] = None
    ) -> List[StakingPosition]:
        """Get all staking positions."""
        query = self.session.query(StakingPosition).filter(
            StakingPosition.portfolio_id == portfolio_id
        )

        if exchange:
            query = query.filter(StakingPosition.exchange == exchange)
        if status:
            query = query.filter(StakingPosition.status == status)

        return query.all()

    def record_reward(
        self,
        position_id: int,
        amount: Decimal,
        value_usd: Optional[Decimal] = None,
        reward_type: str = "staking"
    ) -> StakingReward:
        """Record a staking reward."""
        position = self.session.query(StakingPosition).filter(
            StakingPosition.id == position_id
        ).first()

        if position:
            position.rewards_earned += amount

        reward = StakingReward(
            position_id=position_id,
            asset=position.asset if position else "UNKNOWN",
            amount=amount,
            value_usd=value_usd,
            reward_type=reward_type,
            timestamp=datetime.utcnow()
        )
        self.session.add(reward)
        self.commit()
        return reward


# =============================================================================
# DCA BOT REPOSITORY
# =============================================================================


class DCABotRepository(BaseRepository):
    """Repository for DCA bot operations."""

    def create(
        self,
        portfolio_id: int,
        exchange: str,
        asset: str,
        amount: Decimal,
        frequency: str,
        **kwargs
    ) -> DCABot:
        """Create a new DCA bot."""
        bot = DCABot(
            portfolio_id=portfolio_id,
            exchange=exchange,
            asset=asset,
            amount=amount,
            frequency=frequency,
            **kwargs
        )

        # Set next execution time
        bot.next_execution_at = self._calculate_next_execution(frequency)

        self.session.add(bot)
        self.commit()
        return bot

    def _calculate_next_execution(self, frequency: str, from_time: Optional[datetime] = None) -> datetime:
        """Calculate next execution time based on frequency."""
        base = from_time or datetime.utcnow()

        intervals = {
            "hourly": timedelta(hours=1),
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "biweekly": timedelta(weeks=2),
            "monthly": timedelta(days=30),
        }

        return base + intervals.get(frequency, timedelta(days=1))

    def get_by_id(self, bot_id: int) -> Optional[DCABot]:
        """Get bot by ID."""
        return self.session.query(DCABot).filter(DCABot.id == bot_id).first()

    def get_active(self, portfolio_id: Optional[int] = None) -> List[DCABot]:
        """Get all active bots."""
        query = self.session.query(DCABot).filter(
            DCABot.status == DCAStatus.ACTIVE
        )
        if portfolio_id:
            query = query.filter(DCABot.portfolio_id == portfolio_id)
        return query.all()

    def get_due_for_execution(self) -> List[DCABot]:
        """Get bots due for execution."""
        return self.session.query(DCABot).filter(
            and_(
                DCABot.status == DCAStatus.ACTIVE,
                DCABot.next_execution_at <= datetime.utcnow()
            )
        ).all()

    def record_execution(
        self,
        bot_id: int,
        amount_invested: Decimal,
        amount_acquired: Decimal,
        price: Decimal,
        status: str = "success",
        transaction_id: Optional[int] = None,
        **kwargs
    ) -> DCAExecution:
        """Record a bot execution."""
        execution = DCAExecution(
            bot_id=bot_id,
            transaction_id=transaction_id,
            amount_invested=amount_invested,
            amount_acquired=amount_acquired,
            price=price,
            status=status,
            executed_at=datetime.utcnow(),
            **kwargs
        )
        self.session.add(execution)

        # Update bot stats
        bot = self.get_by_id(bot_id)
        if bot and status == "success":
            bot.total_invested += amount_invested
            bot.total_acquired += amount_acquired
            bot.execution_count += 1
            bot.last_execution_at = datetime.utcnow()
            bot.next_execution_at = self._calculate_next_execution(bot.frequency)

            # Check if max reached
            if bot.max_total and bot.total_invested >= bot.max_total:
                bot.status = DCAStatus.COMPLETED

        self.commit()
        return execution

    def update_status(self, bot_id: int, status: DCAStatus):
        """Update bot status."""
        self.session.query(DCABot).filter(DCABot.id == bot_id).update({"status": status})
        self.commit()


# =============================================================================
# ALERT REPOSITORY
# =============================================================================


class AlertRepository(BaseRepository):
    """Repository for alert operations."""

    def create(
        self,
        portfolio_id: int,
        alert_type: AlertType,
        threshold: Decimal,
        asset: Optional[str] = None,
        notification_channels: str = "app",
        **kwargs
    ) -> Alert:
        """Create a new alert."""
        alert = Alert(
            portfolio_id=portfolio_id,
            alert_type=alert_type,
            threshold=threshold,
            asset=asset,
            notification_channels=notification_channels,
            **kwargs
        )
        self.session.add(alert)
        self.commit()
        return alert

    def get_active(
        self,
        portfolio_id: Optional[int] = None,
        asset: Optional[str] = None
    ) -> List[Alert]:
        """Get active alerts."""
        query = self.session.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE
        )
        if portfolio_id:
            query = query.filter(Alert.portfolio_id == portfolio_id)
        if asset:
            query = query.filter(Alert.asset == asset)
        return query.all()

    def trigger(self, alert_id: int, triggered_value: Decimal) -> AlertTrigger:
        """Record an alert trigger."""
        alert = self.session.query(Alert).filter(Alert.id == alert_id).first()

        trigger = AlertTrigger(
            alert_id=alert_id,
            triggered_value=triggered_value,
            notification_channels=alert.notification_channels if alert else "app",
            triggered_at=datetime.utcnow()
        )
        self.session.add(trigger)

        if alert:
            alert.triggered_at = datetime.utcnow()
            alert.triggered_value = triggered_value
            if not alert.is_recurring:
                alert.status = AlertStatus.TRIGGERED

        self.commit()
        return trigger

    def delete(self, alert_id: int):
        """Delete an alert."""
        self.session.query(Alert).filter(Alert.id == alert_id).delete()
        self.commit()


# =============================================================================
# SNAPSHOT REPOSITORY
# =============================================================================


class SnapshotRepository(BaseRepository):
    """Repository for portfolio snapshots."""

    def create_portfolio_snapshot(
        self,
        portfolio_id: int,
        total_value_usd: Decimal,
        holdings: List[Dict],
        **kwargs
    ) -> PortfolioSnapshot:
        """Create a portfolio snapshot with holdings."""
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            total_value_usd=total_value_usd,
            snapshot_at=datetime.utcnow(),
            **kwargs
        )
        self.session.add(snapshot)
        self.session.flush()  # Get the ID

        # Add holding snapshots
        for h in holdings:
            holding_snapshot = HoldingSnapshot(
                portfolio_snapshot_id=snapshot.id,
                asset=h["asset"],
                amount=h["amount"],
                price_usd=h["price_usd"],
                value_usd=h["value_usd"],
                allocation_percent=h.get("allocation_percent")
            )
            self.session.add(holding_snapshot)

        self.commit()
        return snapshot

    def get_history(
        self,
        portfolio_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "daily"
    ) -> List[PortfolioSnapshot]:
        """Get snapshot history."""
        query = self.session.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id
        )

        if start_date:
            query = query.filter(PortfolioSnapshot.snapshot_at >= start_date)
        if end_date:
            query = query.filter(PortfolioSnapshot.snapshot_at <= end_date)

        return query.order_by(PortfolioSnapshot.snapshot_at).all()

    def save_price(
        self,
        asset: str,
        price_usd: Decimal,
        source: str = "api",
        **kwargs
    ) -> PriceSnapshot:
        """Save a price snapshot."""
        snapshot = PriceSnapshot(
            asset=asset,
            price_usd=price_usd,
            source=source,
            snapshot_at=datetime.utcnow(),
            **kwargs
        )
        self.session.add(snapshot)
        self.commit()
        return snapshot

    def get_latest_price(self, asset: str) -> Optional[PriceSnapshot]:
        """Get the latest price for an asset."""
        return self.session.query(PriceSnapshot).filter(
            PriceSnapshot.asset == asset
        ).order_by(PriceSnapshot.snapshot_at.desc()).first()
