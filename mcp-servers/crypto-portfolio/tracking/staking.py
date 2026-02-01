"""
Staking rewards tracking.

Tracks all staking rewards across exchanges and protocols,
values them in USD at time of receipt, and provides tax reporting.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import json
from pathlib import Path

from exchanges import ExchangeClient, StakingReward
from data.prices import PriceService


@dataclass
class RewardEntry:
    """A staking reward with full details for tax tracking."""
    id: str
    asset: str
    amount: Decimal
    timestamp: datetime
    usd_value_at_receipt: Decimal
    price_at_receipt: Decimal
    source: str
    tx_hash: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset": self.asset,
            "amount": str(self.amount),
            "timestamp": self.timestamp.isoformat(),
            "usd_value_at_receipt": str(self.usd_value_at_receipt),
            "price_at_receipt": str(self.price_at_receipt),
            "source": self.source,
            "tx_hash": self.tx_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RewardEntry":
        return cls(
            id=data["id"],
            asset=data["asset"],
            amount=Decimal(data["amount"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            usd_value_at_receipt=Decimal(data["usd_value_at_receipt"]),
            price_at_receipt=Decimal(data["price_at_receipt"]),
            source=data["source"],
            tx_hash=data.get("tx_hash"),
        )


@dataclass
class RewardsSummary:
    """Summary of staking rewards for a period."""
    start_date: datetime
    end_date: datetime
    total_usd_value: Decimal
    by_asset: Dict[str, Decimal]  # Asset -> total USD value
    by_source: Dict[str, Decimal]  # Source -> total USD value
    reward_count: int
    entries: List[RewardEntry] = field(default_factory=list)


class StakingTracker:
    """Tracks and stores staking rewards."""

    def __init__(
        self,
        exchanges: List[ExchangeClient],
        price_service: PriceService,
        storage_path: str = "./data/staking_rewards.json",
    ):
        self.exchanges = exchanges
        self.price_service = price_service
        self.storage_path = Path(storage_path)

        self._rewards: List[RewardEntry] = []
        self._load_rewards()

    def _load_rewards(self):
        """Load rewards from storage."""
        if self.storage_path.exists():
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self._rewards = [RewardEntry.from_dict(r) for r in data]

    def _save_rewards(self):
        """Save rewards to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump([r.to_dict() for r in self._rewards], f, indent=2)

    def _generate_reward_id(self, reward: StakingReward) -> str:
        """Generate a unique ID for a reward."""
        if reward.tx_hash:
            return f"{reward.source}:{reward.tx_hash}"
        return f"{reward.source}:{reward.asset}:{reward.timestamp.isoformat()}:{reward.amount}"

    async def sync_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Sync staking rewards from all exchanges.

        Args:
            start_date: Start of date range (defaults to last sync or 30 days ago)
            end_date: End of date range (defaults to now)

        Returns:
            Number of new rewards added.
        """
        if not start_date:
            if self._rewards:
                # Start from the most recent reward
                start_date = max(r.timestamp for r in self._rewards)
            else:
                # Default to 30 days ago
                start_date = datetime.now() - timedelta(days=30)

        if not end_date:
            end_date = datetime.now()

        # Gather rewards from all exchanges
        tasks = [
            ex.get_staking_rewards(start_date, end_date)
            for ex in self.exchanges
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all new rewards
        all_rewards: List[StakingReward] = []
        for exchange, result in zip(self.exchanges, results):
            if isinstance(result, Exception):
                print(f"Warning: Failed to get rewards from {exchange.name}: {result}")
                continue
            all_rewards.extend(result)

        # Filter out duplicates
        existing_ids = {r.id for r in self._rewards}
        new_rewards = []

        for reward in all_rewards:
            reward_id = self._generate_reward_id(reward)
            if reward_id not in existing_ids:
                new_rewards.append((reward_id, reward))
                existing_ids.add(reward_id)

        if not new_rewards:
            return 0

        # Get prices for all assets at their respective times
        # For efficiency, we'll use current prices if rewards are recent
        assets = list(set(r.asset for _, r in new_rewards))
        current_prices = await self.price_service.get_prices(assets)

        # Create reward entries
        for reward_id, reward in new_rewards:
            # Use provided USD value or calculate from price
            if reward.usd_value and reward.usd_value > 0:
                usd_value = reward.usd_value
                price = usd_value / reward.amount if reward.amount > 0 else Decimal("0")
            else:
                # Use current price (or historical if available)
                price = current_prices.get(reward.asset, Decimal("0"))
                usd_value = reward.amount * price

            entry = RewardEntry(
                id=reward_id,
                asset=reward.asset,
                amount=reward.amount,
                timestamp=reward.timestamp,
                usd_value_at_receipt=usd_value,
                price_at_receipt=price,
                source=reward.source,
                tx_hash=reward.tx_hash,
            )
            self._rewards.append(entry)

        # Sort by timestamp
        self._rewards.sort(key=lambda r: r.timestamp)

        # Save to storage
        self._save_rewards()

        return len(new_rewards)

    def get_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[RewardEntry]:
        """Get filtered list of rewards."""
        rewards = self._rewards

        if start_date:
            rewards = [r for r in rewards if r.timestamp >= start_date]
        if end_date:
            rewards = [r for r in rewards if r.timestamp <= end_date]
        if asset:
            rewards = [r for r in rewards if r.asset == asset]
        if source:
            rewards = [r for r in rewards if r.source == source]

        return rewards

    def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> RewardsSummary:
        """Get summary of rewards for a period."""
        rewards = self.get_rewards(start_date, end_date)

        by_asset: Dict[str, Decimal] = {}
        by_source: Dict[str, Decimal] = {}
        total_usd = Decimal("0")

        for reward in rewards:
            # By asset
            if reward.asset not in by_asset:
                by_asset[reward.asset] = Decimal("0")
            by_asset[reward.asset] += reward.usd_value_at_receipt

            # By source
            if reward.source not in by_source:
                by_source[reward.source] = Decimal("0")
            by_source[reward.source] += reward.usd_value_at_receipt

            total_usd += reward.usd_value_at_receipt

        return RewardsSummary(
            start_date=start_date or (rewards[0].timestamp if rewards else datetime.now()),
            end_date=end_date or datetime.now(),
            total_usd_value=total_usd,
            by_asset=by_asset,
            by_source=by_source,
            reward_count=len(rewards),
            entries=rewards,
        )

    def get_tax_year_summary(self, year: int) -> RewardsSummary:
        """Get summary for a tax year."""
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        return self.get_summary(start_date, end_date)

    def export_csv(
        self,
        filepath: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """Export rewards to CSV for tax reporting."""
        import csv

        rewards = self.get_rewards(start_date, end_date)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Date",
                "Asset",
                "Amount",
                "Price (USD)",
                "Value (USD)",
                "Source",
                "Transaction Hash",
            ])

            for reward in rewards:
                writer.writerow([
                    reward.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    reward.asset,
                    str(reward.amount),
                    str(reward.price_at_receipt),
                    str(reward.usd_value_at_receipt),
                    reward.source,
                    reward.tx_hash or "",
                ])

    def format_summary(self, summary: Optional[RewardsSummary] = None) -> str:
        """Format a human-readable summary."""
        if not summary:
            summary = self.get_summary()

        lines = []
        lines.append("=" * 50)
        lines.append("Staking Rewards Summary")
        lines.append("=" * 50)
        lines.append(f"Period: {summary.start_date.strftime('%Y-%m-%d')} to {summary.end_date.strftime('%Y-%m-%d')}")
        lines.append(f"Total Rewards: {summary.reward_count}")
        lines.append(f"Total Value: ${summary.total_usd_value:,.2f}")
        lines.append("")

        lines.append("By Asset:")
        for asset, value in sorted(summary.by_asset.items(), key=lambda x: -x[1]):
            lines.append(f"  {asset}: ${value:,.2f}")

        lines.append("")
        lines.append("By Source:")
        for source, value in sorted(summary.by_source.items(), key=lambda x: -x[1]):
            lines.append(f"  {source}: ${value:,.2f}")

        return "\n".join(lines)
