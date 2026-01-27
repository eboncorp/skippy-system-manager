"""
Target portfolio allocation configuration.

Customize this file to match your investment strategy.
All allocations should sum to 1.0 (100%).
"""

from typing import Dict
from dataclasses import dataclass


# =============================================================================
# TARGET ALLOCATION
# =============================================================================
# Strategy: Aggressive Income (4+ year horizon)
# Expected blended yield: ~7.2% annually

TARGET_ALLOCATION: Dict[str, float] = {
    # Tier 1: Core Anchor (30%)
    "ETH": 0.18,   # DeFi backbone, staking yield
    "BTC": 0.12,   # Store of value, volatility anchor
    
    # Tier 2: High-Yield L1s (35%)
    "ATOM": 0.12,  # ~17% APY, Cosmos hub
    "DOT": 0.10,   # ~12% APY, parachains
    "TIA": 0.08,   # ~12% APY, data availability
    "INJ": 0.05,   # ~15% APY, DeFi focused
    
    # Tier 3: Growth + Yield (27%)
    "SOL": 0.12,   # ~7% APY, ecosystem momentum
    "AVAX": 0.06,  # ~8% APY, subnet growth
    "NEAR": 0.05,  # ~9% APY, AI/chain abstraction
    "SUI": 0.04,   # ~4% APY, Move-based emerging
    
    # Tier 4: Cash Buffer (8%)
    "CASH": 0.08,  # USDC/USD - dry powder for dips
}


# =============================================================================
# STAKING CONFIGURATION
# =============================================================================

@dataclass
class StakingInfo:
    """Staking information for an asset."""
    stakeable: bool
    expected_apy: float  # Expected annual yield (0.05 = 5%)
    lockup_days: int  # Typical lockup period in days
    provider_commission: float  # Platform fee (0.25 = 25%)
    where_to_stake: str  # Recommended staking location


STAKING_CONFIG: Dict[str, StakingInfo] = {
    "BTC": StakingInfo(
        stakeable=False,
        expected_apy=0.0,
        lockup_days=0,
        provider_commission=0.0,
        where_to_stake="N/A - PoW, no native staking"
    ),
    "ETH": StakingInfo(
        stakeable=True,
        expected_apy=0.035,
        lockup_days=0,  # Liquid with exchange staking
        provider_commission=0.25,
        where_to_stake="Coinbase Prime (business) - institutional custody"
    ),
    "SOL": StakingInfo(
        stakeable=True,
        expected_apy=0.07,
        lockup_days=2,  # ~2 epoch cooldown
        provider_commission=0.20,
        where_to_stake="Coinbase Prime or Kraken"
    ),
    "DOT": StakingInfo(
        stakeable=True,
        expected_apy=0.12,
        lockup_days=28,
        provider_commission=0.15,
        where_to_stake="Kraken (lower commission than Coinbase)"
    ),
    "AVAX": StakingInfo(
        stakeable=True,
        expected_apy=0.08,
        lockup_days=14,
        provider_commission=0.20,
        where_to_stake="Coinbase Prime"
    ),
    "ATOM": StakingInfo(
        stakeable=True,
        expected_apy=0.17,
        lockup_days=21,
        provider_commission=0.15,
        where_to_stake="Kraken or Keplr wallet (native)"
    ),
    "TIA": StakingInfo(
        stakeable=True,
        expected_apy=0.12,
        lockup_days=21,
        provider_commission=0.10,
        where_to_stake="Keplr wallet (native) for best rates"
    ),
    "INJ": StakingInfo(
        stakeable=True,
        expected_apy=0.15,
        lockup_days=21,
        provider_commission=0.10,
        where_to_stake="Keplr wallet (native) - Cosmos-based"
    ),
    "NEAR": StakingInfo(
        stakeable=True,
        expected_apy=0.09,
        lockup_days=2,
        provider_commission=0.15,
        where_to_stake="Coinbase Prime or native wallet"
    ),
    "SUI": StakingInfo(
        stakeable=True,
        expected_apy=0.04,
        lockup_days=1,
        provider_commission=0.20,
        where_to_stake="Coinbase Prime - emerging support"
    ),
}


# =============================================================================
# DCA ALLOCATION
# =============================================================================
# Matches target allocation for consistent accumulation
# At $40/day = $1,200/month

DCA_ALLOCATION: Dict[str, float] = {
    # Core
    "ETH": 0.18,   # $216/mo
    "BTC": 0.12,   # $144/mo
    
    # High-Yield
    "ATOM": 0.12,  # $144/mo
    "DOT": 0.10,   # $120/mo
    "TIA": 0.08,   # $96/mo
    "INJ": 0.05,   # $60/mo
    
    # Growth + Yield
    "SOL": 0.12,   # $144/mo
    "AVAX": 0.06,  # $72/mo
    "NEAR": 0.05,  # $60/mo
    "SUI": 0.04,   # $48/mo
    
    # Cash buffer accumulates separately or via rebalancing
    # Not included in DCA - let it build from staking rewards
}


# =============================================================================
# REBALANCING RULES
# =============================================================================

@dataclass
class RebalanceRule:
    """Rules for when and how to rebalance."""
    # Threshold before triggering rebalance (5% = 0.05)
    drift_threshold: float = 0.05
    
    # Maximum single trade size as % of position
    max_trade_pct: float = 0.25
    
    # Minimum trade size in USD
    min_trade_usd: float = 10.0
    
    # Tax-loss harvesting: sell losers before winners
    prefer_tax_loss_harvest: bool = True
    
    # Avoid short-term gains (assets held < 1 year)
    avoid_short_term_gains: bool = True


REBALANCE_RULES = RebalanceRule()


# =============================================================================
# ASSET METADATA
# =============================================================================

# Map of asset symbols to CoinGecko IDs for price fetching
COINGECKO_IDS: Dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "ATOM": "cosmos",
    "TIA": "celestia",
    "INJ": "injective-protocol",
    "NEAR": "near",
    "SUI": "sui",
    "USDC": "usd-coin",
    "USDT": "tether",
}

# Map of asset symbols to exchange-specific symbols
EXCHANGE_SYMBOLS: Dict[str, Dict[str, str]] = {
    "BTC": {"coinbase": "BTC", "kraken": "XBT"},
    "ETH": {"coinbase": "ETH", "kraken": "ETH"},
    "SOL": {"coinbase": "SOL", "kraken": "SOL"},
    "DOT": {"coinbase": "DOT", "kraken": "DOT"},
    "AVAX": {"coinbase": "AVAX", "kraken": "AVAX"},
    "ATOM": {"coinbase": "ATOM", "kraken": "ATOM"},
    "TIA": {"coinbase": "TIA", "kraken": "TIA"},
    "INJ": {"coinbase": "INJ", "kraken": "INJ"},
    "NEAR": {"coinbase": "NEAR", "kraken": "NEAR"},
    "SUI": {"coinbase": "SUI", "kraken": "SUI"},
}


# =============================================================================
# VALIDATION
# =============================================================================

def validate_allocation(allocation: Dict[str, float]) -> bool:
    """Validate that allocation sums to 1.0."""
    total = sum(allocation.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(f"Allocation must sum to 1.0, got {total}")
    return True


def get_net_staking_yield(asset: str) -> float:
    """Calculate net staking yield after platform commission."""
    if asset not in STAKING_CONFIG:
        return 0.0
    
    config = STAKING_CONFIG[asset]
    if not config.stakeable:
        return 0.0
    
    return config.expected_apy * (1 - config.provider_commission)


def calculate_blended_yield() -> float:
    """Calculate expected portfolio yield from staking."""
    total_yield = 0.0
    
    for asset, weight in TARGET_ALLOCATION.items():
        if asset == "CASH":
            continue
        net_yield = get_net_staking_yield(asset)
        total_yield += weight * net_yield
    
    return total_yield


# Validate on import
validate_allocation(TARGET_ALLOCATION)

if __name__ == "__main__":
    print("Target Allocation:")
    for asset, weight in sorted(TARGET_ALLOCATION.items(), key=lambda x: -x[1]):
        net_yield = get_net_staking_yield(asset)
        yield_str = f"{net_yield*100:.1f}%" if net_yield > 0 else "N/A"
        print(f"  {asset}: {weight*100:.1f}% (net yield: {yield_str})")
    
    print(f"\nBlended Portfolio Yield: {calculate_blended_yield()*100:.2f}%")
    
    print("\nDCA Allocation (daily at $40):")
    for asset, weight in sorted(DCA_ALLOCATION.items(), key=lambda x: -x[1]):
        daily = weight * 40
        print(f"  {asset}: ${daily:.2f}/day")
