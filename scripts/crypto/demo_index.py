"""Demo of Index Manager with sample data (no API needed)"""
import asyncio
from decimal import Decimal
from datetime import datetime
from agents.index_manager import (
    AssetData, AssetScore, IndexAsset, IndexConfig, IndexPortfolio,
    IndexReporter, AccountType, ASSET_SCORES, STAKING_RATES
)

# Sample data representing ~50 top assets
SAMPLE_ASSETS = [
    ("BTC", "Bitcoin", 1800000000000, 91500, 45000000000),
    ("ETH", "Ethereum", 380000000000, 3150, 18000000000),
    ("XRP", "XRP", 125000000000, 2.15, 5500000000),
    ("SOL", "Solana", 95000000000, 195, 4500000000),
    ("DOGE", "Dogecoin", 52000000000, 0.35, 3200000000),
    ("ADA", "Cardano", 35000000000, 0.98, 950000000),
    ("AVAX", "Avalanche", 32000000000, 78, 1200000000),
    ("LINK", "Chainlink", 28000000000, 47, 980000000),
    ("DOT", "Polkadot", 12000000000, 8.5, 420000000),
    ("MATIC", "Polygon", 8500000000, 0.85, 380000000),
    ("ATOM", "Cosmos", 7800000000, 10.2, 320000000),
    ("LTC", "Litecoin", 7500000000, 105, 450000000),
    ("UNI", "Uniswap", 6200000000, 12.5, 280000000),
    ("NEAR", "NEAR Protocol", 5800000000, 5.2, 240000000),
    ("APT", "Aptos", 5500000000, 12.8, 195000000),
    ("FIL", "Filecoin", 4800000000, 8.2, 180000000),
    ("ARB", "Arbitrum", 4200000000, 1.05, 320000000),
    ("OP", "Optimism", 3800000000, 3.2, 280000000),
    ("INJ", "Injective", 3500000000, 38, 145000000),
    ("RENDER", "Render", 3200000000, 8.5, 165000000),
    ("ALGO", "Algorand", 2800000000, 0.38, 95000000),
    ("XTZ", "Tezos", 2600000000, 2.8, 75000000),
    ("MINA", "Mina", 1800000000, 1.8, 45000000),
    ("FLOW", "Flow", 1500000000, 0.95, 38000000),
    ("OSMO", "Osmosis", 1200000000, 1.2, 42000000),
]

def build_demo_portfolio():
    config = IndexConfig(
        target_count=25,
        max_weight_pct=Decimal("40"),
        personal_target_pct=Decimal("40"),
        business_target_pct=Decimal("60"),
    )
    
    # Build assets
    assets = []
    total_mcap = sum(a[2] for a in SAMPLE_ASSETS)
    
    for i, (symbol, name, mcap, price, vol) in enumerate(SAMPLE_ASSETS):
        # Get or create score
        if symbol in ASSET_SCORES:
            score = ASSET_SCORES[symbol]
        else:
            score = AssetScore(symbol)
        
        # Calculate weights
        raw_weight = Decimal(str(mcap)) / Decimal(str(total_mcap)) * 100
        capped_weight = min(raw_weight, config.max_weight_pct)
        
        # Staking rates
        cb_stake = STAKING_RATES["coinbase"].get(symbol)
        kr_stake = STAKING_RATES["kraken"].get(symbol)
        
        data = AssetData(
            symbol=symbol,
            name=name,
            market_cap=Decimal(str(mcap)),
            price=Decimal(str(price)),
            volume_24h=Decimal(str(vol)),
            price_change_24h=0,
            price_change_7d=0,
            price_change_30d=0,
            circulating_supply=Decimal(str(mcap/price)),
            total_supply=None,
            max_supply=None,
            ath=Decimal(str(price*1.5)),
            ath_date=None,
            atl=Decimal(str(price*0.3)),
            atl_date=None,
            last_updated=datetime.now(),
            on_coinbase=True,
            on_kraken=True,
            staking_apy_coinbase=cb_stake,
            staking_apy_kraken=kr_stake,
        )
        
        asset = IndexAsset(
            symbol=symbol,
            name=name,
            data=data,
            score=score,
            rank=i+1,
            raw_weight=raw_weight,
            capped_weight=capped_weight,
            account=score.recommended_account,
        )
        assets.append(asset)
    
    # Sort into personal/business
    personal = [a for a in assets if a.account in [AccountType.PERSONAL, AccountType.SPLIT]]
    business = [a for a in assets if a.account in [AccountType.BUSINESS, AccountType.SPLIT]]
    
    # Recalculate weights within each portfolio
    personal_total = sum(float(a.capped_weight) for a in personal)
    business_total = sum(float(a.capped_weight) for a in business)
    
    for a in personal:
        a.personal_weight = a.capped_weight / Decimal(str(personal_total)) * 100 if personal_total > 0 else Decimal("0")
    for a in business:
        a.business_weight = a.capped_weight / Decimal(str(business_total)) * 100 if business_total > 0 else Decimal("0")
    
    portfolio = IndexPortfolio(
        name="Dave's COIN50",
        config=config,
        created_at=datetime.now(),
        assets=assets,
        excluded=[],
        personal_assets=sorted(personal, key=lambda x: x.personal_weight, reverse=True),
        business_assets=sorted(business, key=lambda x: x.business_weight, reverse=True),
        total_value=Decimal("100000"),
        personal_value=Decimal("40000"),
        business_value=Decimal("60000"),
    )
    
    return portfolio

if __name__ == "__main__":
    portfolio = build_demo_portfolio()
    print(IndexReporter.summary(portfolio))
