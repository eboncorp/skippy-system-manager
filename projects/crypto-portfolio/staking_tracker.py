"""
Staking Tracker
Tracks staked assets and rewards across exchanges and DeFi protocols.
"""

import os
from typing import Dict, List, Optional, Any
from coinbase.rest import RESTClient


# Staking token mappings
STAKED_TOKENS = {
    # Coinbase staked ETH
    "CBETH": {
        "base_asset": "ETH",
        "provider": "Coinbase",
        "type": "liquid_staking",
        "apy_estimate": 3.2,
    },
    # Lido staked ETH
    "STETH": {
        "base_asset": "ETH",
        "provider": "Lido",
        "type": "liquid_staking",
        "apy_estimate": 3.5,
    },
    # Rocket Pool ETH
    "RETH": {
        "base_asset": "ETH",
        "provider": "Rocket Pool",
        "type": "liquid_staking",
        "apy_estimate": 3.4,
    },
    # Marinade staked SOL
    "MSOL": {
        "base_asset": "SOL",
        "provider": "Marinade",
        "type": "liquid_staking",
        "apy_estimate": 7.0,
    },
    # Lido staked SOL
    "STSOL": {
        "base_asset": "SOL",
        "provider": "Lido",
        "type": "liquid_staking",
        "apy_estimate": 6.5,
    },
    # Jito staked SOL
    "JITOSOL": {
        "base_asset": "SOL",
        "provider": "Jito",
        "type": "liquid_staking",
        "apy_estimate": 7.5,
    },
}


class StakingTracker:
    """Track staking positions and estimated rewards."""

    def __init__(self, cdp_key_file: str = None):
        """Initialize with CDP key file path."""
        key_file = cdp_key_file or os.getenv(
            "CDP_API_KEY_FILE",
            os.path.expanduser("~/.config/coinbase/cdp_api_key.json")
        )
        self.client = RESTClient(key_file=key_file)

    def get_staking_positions(self) -> List[Dict[str, Any]]:
        """Get all staking positions from Coinbase."""
        positions = []
        accounts = self.client.get_accounts()

        for acc in accounts.accounts:
            currency = getattr(acc, 'currency', '')

            if currency in STAKED_TOKENS:
                token_info = STAKED_TOKENS[currency]

                # Get balance
                try:
                    if hasattr(acc.available_balance, 'value'):
                        balance = float(acc.available_balance.value)
                    else:
                        balance = float(acc.available_balance) if acc.available_balance else 0
                except:
                    balance = 0

                if balance > 0:
                    # Get current price
                    try:
                        product = self.client.get_product(f"{currency}-USD")
                        price = float(product.price) if product.price else 0
                    except:
                        # Try base asset price as fallback
                        try:
                            product = self.client.get_product(f"{token_info['base_asset']}-USD")
                            price = float(product.price) if product.price else 0
                        except:
                            price = 0

                    usd_value = balance * price

                    positions.append({
                        "token": currency,
                        "balance": balance,
                        "usd_value": usd_value,
                        "base_asset": token_info["base_asset"],
                        "provider": token_info["provider"],
                        "type": token_info["type"],
                        "apy_estimate": token_info["apy_estimate"],
                        "estimated_daily_reward_usd": usd_value * (token_info["apy_estimate"] / 100 / 365),
                        "estimated_yearly_reward_usd": usd_value * (token_info["apy_estimate"] / 100),
                    })

        return positions

    def get_staking_summary(self) -> Dict[str, Any]:
        """Get summary of all staking positions."""
        positions = self.get_staking_positions()

        total_staked_usd = sum(p["usd_value"] for p in positions)
        total_daily_rewards = sum(p["estimated_daily_reward_usd"] for p in positions)
        total_yearly_rewards = sum(p["estimated_yearly_reward_usd"] for p in positions)

        # Group by base asset
        by_asset = {}
        for p in positions:
            asset = p["base_asset"]
            if asset not in by_asset:
                by_asset[asset] = {"positions": [], "total_usd": 0}
            by_asset[asset]["positions"].append(p)
            by_asset[asset]["total_usd"] += p["usd_value"]

        return {
            "total_staked_usd": total_staked_usd,
            "estimated_daily_rewards_usd": total_daily_rewards,
            "estimated_yearly_rewards_usd": total_yearly_rewards,
            "average_apy": (total_yearly_rewards / total_staked_usd * 100) if total_staked_usd > 0 else 0,
            "positions": positions,
            "by_asset": by_asset,
        }


def main():
    """Test staking tracker."""
    tracker = StakingTracker()

    print("=== STAKING POSITIONS ===\n")

    summary = tracker.get_staking_summary()

    if summary["positions"]:
        print(f"{'Token':<10} {'Balance':>15} {'USD Value':>12} {'Provider':<12} {'APY':>6}")
        print("-" * 60)

        for p in summary["positions"]:
            print(f"{p['token']:<10} {p['balance']:>15.6f} ${p['usd_value']:>11,.2f} {p['provider']:<12} {p['apy_estimate']:>5.1f}%")

        print("-" * 60)
        print(f"\nTotal Staked: ${summary['total_staked_usd']:,.2f}")
        print(f"Est. Daily Rewards: ${summary['estimated_daily_rewards_usd']:.2f}")
        print(f"Est. Yearly Rewards: ${summary['estimated_yearly_rewards_usd']:.2f}")
        print(f"Weighted Avg APY: {summary['average_apy']:.2f}%")
    else:
        print("No staking positions found.")


if __name__ == "__main__":
    main()
