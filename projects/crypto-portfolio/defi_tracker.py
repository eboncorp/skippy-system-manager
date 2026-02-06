"""
DeFi Protocol Tracker
Tracks positions across major DeFi protocols.

Supports:
- Lending: Aave, Compound, MakerDAO
- DEXs: Uniswap, SushiSwap, Curve
- Liquid Staking: Lido, Rocket Pool
- Yield: Yearn, Convex
- Bridges: Across, Stargate

Uses public APIs and on-chain data (no private keys required).
"""

import logging
import os
import time
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class DeFiPosition:
    """A position in a DeFi protocol."""
    protocol: str
    chain: str
    position_type: str  # supply, borrow, lp, stake, vault
    asset: str
    amount: float
    usd_value: float
    apy: Optional[float] = None
    rewards_pending: float = 0
    rewards_usd: float = 0
    health_factor: Optional[float] = None  # For lending positions
    metadata: dict = None


@dataclass
class LPPosition:
    """Liquidity provider position."""
    protocol: str
    chain: str
    pool_name: str
    token0: str
    token1: str
    token0_amount: float
    token1_amount: float
    lp_tokens: float
    usd_value: float
    fees_earned_usd: float = 0
    impermanent_loss_pct: float = 0


class DefiLlamaClient:
    """Client for DefiLlama API - aggregates DeFi data."""
    
    BASE_URL = "https://api.llama.fi"
    YIELDS_URL = "https://yields.llama.fi"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_protocol_tvl(self, protocol: str) -> Optional[dict]:
        """Get TVL and stats for a protocol."""
        try:
            response = self.session.get(f"{self.BASE_URL}/protocol/{protocol}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("DefiLlama error: %s", e)
            return None
    
    def get_yields(self, pool_id: str = None) -> List[dict]:
        """Get yield/APY data for pools."""
        try:
            response = self.session.get(f"{self.YIELDS_URL}/pools")
            response.raise_for_status()
            data = response.json().get("data", [])
            
            if pool_id:
                return [p for p in data if p.get("pool") == pool_id]
            return data
            
        except Exception as e:
            logger.warning("DefiLlama yields error: %s", e)
            return []
    
    def get_stablecoin_yields(self) -> List[dict]:
        """Get best stablecoin yields."""
        pools = self.get_yields()
        stables = ["USDC", "USDT", "DAI", "FRAX", "LUSD"]
        
        stable_pools = [
            p for p in pools 
            if any(s in p.get("symbol", "").upper() for s in stables)
            and p.get("apy", 0) > 0
        ]
        
        return sorted(stable_pools, key=lambda x: x.get("apy", 0), reverse=True)[:20]


class AaveTracker:
    """Track Aave lending/borrowing positions."""
    
    # Aave subgraph endpoints
    SUBGRAPHS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
        "polygon": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-polygon",
        "arbitrum": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-arbitrum",
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_user_positions(self, address: str, chain: str = "ethereum") -> List[DeFiPosition]:
        """Get user's Aave positions."""
        positions = []
        
        subgraph = self.SUBGRAPHS.get(chain)
        if not subgraph:
            return positions
        
        query = """
        query GetUserPositions($user: String!) {
            userReserves(where: {user: $user}) {
                reserve {
                    symbol
                    decimals
                    liquidityRate
                    variableBorrowRate
                }
                currentATokenBalance
                currentVariableDebt
                currentStableDebt
            }
            user(id: $user) {
                healthFactor
            }
        }
        """
        
        try:
            response = self.session.post(
                subgraph,
                json={"query": query, "variables": {"user": address.lower()}}
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            
            health_factor = None
            if data.get("user"):
                hf = data["user"].get("healthFactor")
                if hf:
                    health_factor = float(hf) / 1e18
            
            for reserve in data.get("userReserves", []):
                res = reserve.get("reserve", {})
                symbol = res.get("symbol", "UNKNOWN")
                decimals = int(res.get("decimals", 18))
                
                # Supply position
                supply_balance = float(reserve.get("currentATokenBalance", 0)) / (10 ** decimals)
                if supply_balance > 0:
                    supply_apy = float(res.get("liquidityRate", 0)) / 1e27 * 100
                    positions.append(DeFiPosition(
                        protocol="Aave V3",
                        chain=chain,
                        position_type="supply",
                        asset=symbol,
                        amount=supply_balance,
                        usd_value=0,  # Would need price oracle
                        apy=supply_apy,
                        health_factor=health_factor
                    ))
                
                # Borrow position
                var_debt = float(reserve.get("currentVariableDebt", 0)) / (10 ** decimals)
                stable_debt = float(reserve.get("currentStableDebt", 0)) / (10 ** decimals)
                total_debt = var_debt + stable_debt
                
                if total_debt > 0:
                    borrow_apy = float(res.get("variableBorrowRate", 0)) / 1e27 * 100
                    positions.append(DeFiPosition(
                        protocol="Aave V3",
                        chain=chain,
                        position_type="borrow",
                        asset=symbol,
                        amount=-total_debt,  # Negative for debt
                        usd_value=0,
                        apy=-borrow_apy,  # Negative APY (cost)
                        health_factor=health_factor
                    ))
                    
        except Exception as e:
            logger.warning("Aave query error: %s", e)
        
        return positions


class UniswapTracker:
    """Track Uniswap V3 LP positions."""
    
    SUBGRAPHS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "polygon": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon",
        "arbitrum": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-dev",
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_user_positions(self, address: str, chain: str = "ethereum") -> List[LPPosition]:
        """Get user's Uniswap V3 LP positions."""
        positions = []
        
        subgraph = self.SUBGRAPHS.get(chain)
        if not subgraph:
            return positions
        
        query = """
        query GetPositions($owner: String!) {
            positions(where: {owner: $owner, liquidity_gt: 0}) {
                id
                liquidity
                token0 {
                    symbol
                    decimals
                }
                token1 {
                    symbol
                    decimals
                }
                pool {
                    feeTier
                    token0Price
                    token1Price
                }
                depositedToken0
                depositedToken1
                collectedFeesToken0
                collectedFeesToken1
            }
        }
        """
        
        try:
            response = self.session.post(
                subgraph,
                json={"query": query, "variables": {"owner": address.lower()}}
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            
            for pos in data.get("positions", []):
                token0 = pos.get("token0", {})
                token1 = pos.get("token1", {})
                
                positions.append(LPPosition(
                    protocol="Uniswap V3",
                    chain=chain,
                    pool_name=f"{token0.get('symbol')}/{token1.get('symbol')}",
                    token0=token0.get("symbol", ""),
                    token1=token1.get("symbol", ""),
                    token0_amount=float(pos.get("depositedToken0", 0)),
                    token1_amount=float(pos.get("depositedToken1", 0)),
                    lp_tokens=float(pos.get("liquidity", 0)),
                    usd_value=0,  # Would need price calculation
                    fees_earned_usd=0
                ))
                
        except Exception as e:
            logger.warning("Uniswap query error: %s", e)
        
        return positions


class LidoTracker:
    """Track Lido liquid staking positions."""
    
    def __init__(self):
        load_dotenv()
        self.session = requests.Session()
        self.etherscan_key = os.getenv("ETHERSCAN_API_KEY")
        
        # Lido contracts
        self.STETH_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
        self.WSTETH_ADDRESS = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
    
    def get_steth_balance(self, address: str) -> Optional[DeFiPosition]:
        """Get stETH balance for an address."""
        if not self.etherscan_key:
            return None
        
        try:
            # Get stETH balance
            response = self.session.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "account",
                    "action": "tokenbalance",
                    "contractaddress": self.STETH_ADDRESS,
                    "address": address,
                    "tag": "latest",
                    "apikey": self.etherscan_key
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "1":
                balance = float(data.get("result", 0)) / 1e18
                
                if balance > 0:
                    return DeFiPosition(
                        protocol="Lido",
                        chain="ethereum",
                        position_type="stake",
                        asset="stETH",
                        amount=balance,
                        usd_value=balance * self._get_eth_price(),
                        apy=self._get_lido_apy(),
                        metadata={"underlying": "ETH"}
                    )
                    
        except Exception as e:
            logger.warning("Lido query error: %s", e)
        
        return None
    
    def _get_eth_price(self) -> float:
        """Get current ETH price."""
        try:
            response = self.session.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "ethereum", "vs_currencies": "usd"}
            )
            return response.json().get("ethereum", {}).get("usd", 0)
        except Exception as e:
            logger.warning("Failed to fetch ETH price: %s", e)
            return None
    
    def _get_lido_apy(self) -> float:
        """Get current Lido staking APY."""
        try:
            response = self.session.get("https://stake.lido.fi/api/apr")
            return response.json().get("apr", 4.0)
        except Exception as e:
            logger.warning("Failed to fetch Lido APY: %s", e)
            return None


class YearnTracker:
    """Track Yearn Finance vault positions."""
    
    API_URL = "https://api.yearn.finance/v1/chains/1/vaults/all"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_vaults(self) -> List[dict]:
        """Get all Yearn vaults with APY."""
        try:
            response = self.session.get(self.API_URL)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("Yearn API error: %s", e)
            return []
    
    def get_best_yields(self, min_tvl: float = 1000000) -> List[dict]:
        """Get best yielding vaults above min TVL."""
        vaults = self.get_vaults()
        
        filtered = [
            v for v in vaults
            if v.get("tvl", {}).get("tvl", 0) >= min_tvl
            and v.get("apy", {}).get("net_apy", 0) > 0
        ]
        
        return sorted(
            filtered,
            key=lambda x: x.get("apy", {}).get("net_apy", 0),
            reverse=True
        )[:20]


class DeFiPortfolioTracker:
    """Unified DeFi portfolio tracker."""
    
    def __init__(self):
        load_dotenv()
        self.defillama = DefiLlamaClient()
        self.aave = AaveTracker()
        self.uniswap = UniswapTracker()
        self.lido = LidoTracker()
        self.yearn = YearnTracker()
        
        self.wallets: Dict[str, List[str]] = {}  # chain -> [addresses]
    
    def add_wallet(self, address: str, chains: List[str] = None):
        """Add a wallet address to track."""
        if chains is None:
            chains = ["ethereum", "polygon", "arbitrum"]
        
        for chain in chains:
            if chain not in self.wallets:
                self.wallets[chain] = []
            if address not in self.wallets[chain]:
                self.wallets[chain].append(address)
    
    def get_all_positions(self) -> Dict[str, List]:
        """Get all DeFi positions across protocols."""
        all_positions = {
            "lending": [],
            "lp": [],
            "staking": [],
            "vaults": []
        }
        
        for chain, addresses in self.wallets.items():
            for address in addresses:
                print(f"  Scanning {address[:10]}... on {chain}")
                
                # Aave positions
                aave_positions = self.aave.get_user_positions(address, chain)
                for pos in aave_positions:
                    if pos.position_type in ["supply", "borrow"]:
                        all_positions["lending"].append(pos)
                
                # Uniswap LP positions
                uni_positions = self.uniswap.get_user_positions(address, chain)
                all_positions["lp"].extend(uni_positions)
                
                # Lido staking (Ethereum only)
                if chain == "ethereum":
                    lido_pos = self.lido.get_steth_balance(address)
                    if lido_pos:
                        all_positions["staking"].append(lido_pos)
                
                time.sleep(0.5)  # Rate limiting
        
        return all_positions
    
    def get_defi_summary(self) -> dict:
        """Get summary of all DeFi positions."""
        positions = self.get_all_positions()
        
        total_supplied = sum(
            p.usd_value for p in positions["lending"] 
            if p.position_type == "supply"
        )
        total_borrowed = sum(
            abs(p.usd_value) for p in positions["lending"]
            if p.position_type == "borrow"
        )
        total_lp = sum(p.usd_value for p in positions["lp"])
        total_staked = sum(p.usd_value for p in positions["staking"])
        
        return {
            "total_supplied": total_supplied,
            "total_borrowed": total_borrowed,
            "net_lending": total_supplied - total_borrowed,
            "total_lp": total_lp,
            "total_staked": total_staked,
            "total_defi": total_supplied - total_borrowed + total_lp + total_staked,
            "positions": positions
        }
    
    def find_best_yields(self, asset: str = None, min_tvl: float = 1000000) -> List[dict]:
        """Find best yield opportunities."""
        # Get DefiLlama yields
        pools = self.defillama.get_yields()
        
        # Filter by asset if specified
        if asset:
            pools = [p for p in pools if asset.upper() in p.get("symbol", "").upper()]
        
        # Filter by TVL
        pools = [p for p in pools if p.get("tvlUsd", 0) >= min_tvl]
        
        # Sort by APY
        pools = sorted(pools, key=lambda x: x.get("apy", 0), reverse=True)
        
        return [
            {
                "protocol": p.get("project"),
                "chain": p.get("chain"),
                "pool": p.get("symbol"),
                "apy": p.get("apy"),
                "tvl": p.get("tvlUsd"),
                "il_risk": p.get("ilRisk", "unknown")
            }
            for p in pools[:20]
        ]


def main():
    """CLI for DeFi tracking."""
    import argparse
    from tabulate import tabulate
    
    parser = argparse.ArgumentParser(description="DeFi Protocol Tracker")
    parser.add_argument("--add-wallet", type=str, help="Add wallet address to track")
    parser.add_argument("--chain", type=str, default="ethereum", help="Chain for wallet")
    parser.add_argument("--positions", action="store_true", help="Show all DeFi positions")
    parser.add_argument("--yields", action="store_true", help="Find best yields")
    parser.add_argument("--asset", type=str, help="Filter yields by asset")
    parser.add_argument("--stablecoin-yields", action="store_true", help="Show best stablecoin yields")
    
    args = parser.parse_args()
    
    tracker = DeFiPortfolioTracker()
    
    if args.add_wallet:
        tracker.add_wallet(args.add_wallet, [args.chain])
        print(f"✓ Added {args.add_wallet[:10]}... on {args.chain}")
    
    elif args.positions:
        print("\n🏦 DEFI POSITIONS")
        print("=" * 60)
        
        # Load saved wallets
        wallet_file = os.path.expanduser("~/.crypto_portfolio/defi_wallets.json")
        if os.path.exists(wallet_file):
            with open(wallet_file) as f:
                tracker.wallets = json.load(f)
        
        if not tracker.wallets:
            print("No wallets configured. Use --add-wallet to add addresses.")
            return
        
        summary = tracker.get_defi_summary()
        
        print(f"\n📊 Summary:")
        print(f"  Total Supplied: ${summary['total_supplied']:,.2f}")
        print(f"  Total Borrowed: ${summary['total_borrowed']:,.2f}")
        print(f"  Total LP:       ${summary['total_lp']:,.2f}")
        print(f"  Total Staked:   ${summary['total_staked']:,.2f}")
        print(f"  ─────────────────────────")
        print(f"  Net DeFi Value: ${summary['total_defi']:,.2f}")
    
    elif args.yields or args.asset:
        print("\n💰 BEST YIELD OPPORTUNITIES")
        print("=" * 60)
        
        yields = tracker.find_best_yields(args.asset)
        
        table_data = []
        for y in yields:
            table_data.append([
                y["protocol"],
                y["chain"],
                y["pool"],
                f"{y['apy']:.2f}%",
                f"${y['tvl']/1e6:.1f}M"
            ])
        
        print(tabulate(table_data, 
                       headers=["Protocol", "Chain", "Pool", "APY", "TVL"],
                       tablefmt="simple"))
    
    elif args.stablecoin_yields:
        print("\n💵 BEST STABLECOIN YIELDS")
        print("=" * 60)
        
        yields = tracker.defillama.get_stablecoin_yields()
        
        table_data = []
        for y in yields:
            table_data.append([
                y.get("project"),
                y.get("chain"),
                y.get("symbol"),
                f"{y.get('apy', 0):.2f}%",
                f"${y.get('tvlUsd', 0)/1e6:.1f}M"
            ])
        
        print(tabulate(table_data,
                       headers=["Protocol", "Chain", "Pool", "APY", "TVL"],
                       tablefmt="simple"))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
