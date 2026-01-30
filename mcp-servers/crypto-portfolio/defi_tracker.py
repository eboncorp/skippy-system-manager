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

import asyncio
import logging
import os
import time
import json
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Use aiohttp for non-blocking HTTP calls in async context
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    import requests

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
    """
    Async client for DefiLlama API - aggregates DeFi data.

    QA FIX: Converted from requests.Session to aiohttp for non-blocking HTTP.
    """

    BASE_URL = "https://api.llama.fi"
    YIELDS_URL = "https://yields.llama.fi"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations. Install with: pip install aiohttp")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_protocol_tvl(self, protocol: str) -> Optional[dict]:
        """Get TVL and stats for a protocol."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.BASE_URL}/protocol/{protocol}") as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"DefiLlama error fetching {protocol}: {e}")
            return None

    async def get_yields(self, pool_id: str = None) -> List[dict]:
        """Get yield/APY data for pools."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.YIELDS_URL}/pools") as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", [])

                if pool_id:
                    return [p for p in data if p.get("pool") == pool_id]
                return data

        except Exception as e:
            logger.error(f"DefiLlama yields error: {e}")
            return []

    async def get_stablecoin_yields(self) -> List[dict]:
        """Get best stablecoin yields."""
        pools = await self.get_yields()
        stables = ["USDC", "USDT", "DAI", "FRAX", "LUSD"]

        stable_pools = [
            p for p in pools
            if any(s in p.get("symbol", "").upper() for s in stables)
            and p.get("apy", 0) > 0
        ]

        return sorted(stable_pools, key=lambda x: x.get("apy", 0), reverse=True)[:20]


class AaveTracker:
    """
    Track Aave lending/borrowing positions.

    QA FIX: Converted to async aiohttp for non-blocking HTTP.
    """

    # Aave subgraph endpoints
    SUBGRAPHS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
        "polygon": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-polygon",
        "arbitrum": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3-arbitrum",
    }

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_user_positions(self, address: str, chain: str = "ethereum") -> List[DeFiPosition]:
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
            session = await self._get_session()
            async with session.post(
                subgraph,
                json={"query": query, "variables": {"user": address.lower()}}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})
            
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
            logger.error(f"Aave query error for {address}: {e}")

        return positions


class UniswapTracker:
    """
    Track Uniswap V3 LP positions.

    QA FIX: Converted to async aiohttp for non-blocking HTTP.
    """

    SUBGRAPHS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "polygon": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon",
        "arbitrum": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-dev",
    }

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_user_positions(self, address: str, chain: str = "ethereum") -> List[LPPosition]:
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
            session = await self._get_session()
            async with session.post(
                subgraph,
                json={"query": query, "variables": {"owner": address.lower()}}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})

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
            logger.error(f"Uniswap query error for {address}: {e}")

        return positions


class LidoTracker:
    """
    Track Lido liquid staking positions.

    QA FIX: Converted to async aiohttp for non-blocking HTTP.
    """

    def __init__(self):
        load_dotenv()
        self._session: Optional[aiohttp.ClientSession] = None
        self.etherscan_key = os.getenv("ETHERSCAN_API_KEY")

        # Lido contracts
        self.STETH_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
        self.WSTETH_ADDRESS = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_steth_balance(self, address: str) -> Optional[DeFiPosition]:
        """Get stETH balance for an address."""
        if not self.etherscan_key:
            return None

        try:
            session = await self._get_session()
            async with session.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "account",
                    "action": "tokenbalance",
                    "contractaddress": self.STETH_ADDRESS,
                    "address": address,
                    "tag": "latest",
                    "apikey": self.etherscan_key
                }
            ) as response:
                response.raise_for_status()
                data = await response.json()

            if data.get("status") == "1":
                balance = float(data.get("result", 0)) / 1e18

                if balance > 0:
                    eth_price = await self._get_eth_price()
                    lido_apy = await self._get_lido_apy()
                    return DeFiPosition(
                        protocol="Lido",
                        chain="ethereum",
                        position_type="stake",
                        asset="stETH",
                        amount=balance,
                        usd_value=balance * eth_price,
                        apy=lido_apy,
                        metadata={"underlying": "ETH"}
                    )

        except Exception as e:
            logger.error(f"Lido query error for {address}: {e}")

        return None

    async def _get_eth_price(self) -> float:
        """Get current ETH price."""
        try:
            session = await self._get_session()
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "ethereum", "vs_currencies": "usd"}
            ) as response:
                data = await response.json()
                return data.get("ethereum", {}).get("usd", 0)
        except Exception:
            return 3500  # Fallback

    async def _get_lido_apy(self) -> float:
        """Get current Lido staking APY."""
        try:
            session = await self._get_session()
            async with session.get("https://stake.lido.fi/api/apr") as response:
                data = await response.json()
                return data.get("apr", 4.0)
        except Exception:
            return 4.0  # Approximate


class YearnTracker:
    """
    Track Yearn Finance vault positions.

    QA FIX: Converted to async aiohttp for non-blocking HTTP.
    """

    API_URL = "https://api.yearn.finance/v1/chains/1/vaults/all"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_vaults(self) -> List[dict]:
        """Get all Yearn vaults with APY."""
        try:
            session = await self._get_session()
            async with session.get(self.API_URL) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Yearn API error: {e}")
            return []

    async def get_best_yields(self, min_tvl: float = 1000000) -> List[dict]:
        """Get best yielding vaults above min TVL."""
        vaults = await self.get_vaults()

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


class SushiSwapTracker:
    """
    Track SushiSwap LP positions and staking.

    QA FIX: Converted to async aiohttp for non-blocking HTTP.
    """

    SUBGRAPHS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/sushiswap/exchange",
        "polygon": "https://api.thegraph.com/subgraphs/name/sushiswap/matic-exchange",
        "arbitrum": "https://api.thegraph.com/subgraphs/name/sushiswap/arbitrum-exchange",
    }

    MASTERCHEF_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/sushiswap/master-chefv2"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_user_lp_positions(self, address: str, chain: str = "ethereum") -> List[DeFiPosition]:
        """Get user's SushiSwap LP positions."""
        positions = []

        subgraph = self.SUBGRAPHS.get(chain)
        if not subgraph:
            return positions

        query = """
        query GetUserLPs($user: String!) {
            liquidityPositions(where: {user: $user, liquidityTokenBalance_gt: "0"}) {
                pair {
                    id
                    token0 { symbol }
                    token1 { symbol }
                    reserveUSD
                    totalSupply
                }
                liquidityTokenBalance
            }
        }
        """

        try:
            session = await self._get_session()
            async with session.post(
                subgraph,
                json={"query": query, "variables": {"user": address.lower()}}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})

            for lp in data.get("liquidityPositions", []):
                pair = lp.get("pair", {})
                token0 = pair.get("token0", {}).get("symbol", "?")
                token1 = pair.get("token1", {}).get("symbol", "?")
                balance = float(lp.get("liquidityTokenBalance", 0))
                total_supply = float(pair.get("totalSupply", 1))
                reserve_usd = float(pair.get("reserveUSD", 0))

                # Calculate user's share of the pool
                share = balance / total_supply if total_supply > 0 else 0
                usd_value = reserve_usd * share

                if usd_value > 1:  # Filter dust
                    positions.append(DeFiPosition(
                        protocol="SushiSwap",
                        chain=chain,
                        position_type="lp",
                        asset=f"{token0}-{token1}",
                        amount=balance,
                        usd_value=usd_value,
                        apy=0,  # Would need to query farming APY
                        pool_share=share * 100
                    ))

        except Exception as e:
            logger.error(f"SushiSwap query error for {address}: {e}")

        return positions

    async def get_staking_positions(self, address: str) -> List[DeFiPosition]:
        """Get user's xSUSHI and MasterChef positions."""
        positions = []

        # Query MasterChef v2 for staked positions
        query = """
        query GetUserStaking($user: String!) {
            users(where: {address: $user}) {
                pool {
                    pair
                    allocPoint
                }
                amount
                rewardDebt
            }
        }
        """

        try:
            session = await self._get_session()
            async with session.post(
                self.MASTERCHEF_SUBGRAPH,
                json={"query": query, "variables": {"user": address.lower()}}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})

            for user in data.get("users", []):
                amount = float(user.get("amount", 0))
                if amount > 0:
                    positions.append(DeFiPosition(
                        protocol="SushiSwap MasterChef",
                        chain="ethereum",
                        position_type="staking",
                        asset="SUSHI-LP",
                        amount=amount,
                        usd_value=0,  # Need price oracle
                        apy=0  # Variable based on allocation
                    ))

        except Exception as e:
            logger.error(f"SushiSwap staking query error for {address}: {e}")

        return positions


class ConvexTracker:
    """
    Track Convex Finance positions (Curve LP staking + CVX rewards).

    QA FIX: Converted to async aiohttp for non-blocking HTTP.
    """

    API_URL = "https://www.convexfinance.com/api/curve-apys"
    SUBGRAPH = "https://api.thegraph.com/subgraphs/name/convex-community/curve-pools"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_pool_apys(self) -> Dict[str, float]:
        """Get APYs for all Convex pools."""
        try:
            session = await self._get_session()
            async with session.get(self.API_URL) as response:
                response.raise_for_status()
                data = await response.json()

            apys = {}
            for pool_name, pool_data in data.get("apys", {}).items():
                base_apy = pool_data.get("baseApy", 0)
                cvx_apy = pool_data.get("cvxApy", 0)
                crv_apy = pool_data.get("crvApy", 0)
                total_apy = base_apy + cvx_apy + crv_apy
                apys[pool_name] = total_apy

            return apys

        except Exception as e:
            logger.error(f"Convex API error: {e}")
            return {}

    async def get_user_positions(self, address: str) -> List[DeFiPosition]:
        """Get user's Convex staking positions."""
        positions = []

        # Query for user's staked positions
        query = """
        query GetUserPositions($user: String!) {
            accounts(where: {id: $user}) {
                poolBalances {
                    pool {
                        name
                        lpToken {
                            symbol
                        }
                        tvl
                    }
                    balance
                }
            }
        }
        """

        try:
            session = await self._get_session()
            async with session.post(
                self.SUBGRAPH,
                json={"query": query, "variables": {"user": address.lower()}}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})

            # Get current APYs
            apys = await self.get_pool_apys()

            for account in data.get("accounts", []):
                for pool_balance in account.get("poolBalances", []):
                    pool = pool_balance.get("pool", {})
                    balance = float(pool_balance.get("balance", 0))

                    if balance > 0:
                        pool_name = pool.get("name", "Unknown")
                        apy = apys.get(pool_name, 0)

                        positions.append(DeFiPosition(
                            protocol="Convex",
                            chain="ethereum",
                            position_type="staking",
                            asset=pool.get("lpToken", {}).get("symbol", pool_name),
                            amount=balance,
                            usd_value=0,  # Would need to calculate from balance
                            apy=apy,
                            rewards_earned={}
                        ))

        except Exception as e:
            logger.error(f"Convex query error for {address}: {e}")

        return positions

    async def get_best_pools(self, min_tvl: float = 10000000) -> List[Dict]:
        """Get highest APY Convex pools."""
        apys = await self.get_pool_apys()

        pools = [
            {"name": name, "apy": apy}
            for name, apy in apys.items()
            if apy > 0
        ]

        return sorted(pools, key=lambda x: x["apy"], reverse=True)[:20]


class MakerDAOTracker:
    """
    Track MakerDAO (DAI) positions - CDPs/Vaults.

    QA FIX: Converted to async aiohttp for non-blocking HTTP.
    """

    SUBGRAPH = "https://api.thegraph.com/subgraphs/name/protofire/maker-protocol"

    # Current DSR (DAI Savings Rate) - would normally be fetched from chain
    DSR_APY = 5.0  # Approximate, should be fetched dynamically

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        """Get or create aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp required for async operations")
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_user_vaults(self, address: str) -> List[DeFiPosition]:
        """Get user's MakerDAO vaults (CDPs)."""
        positions = []

        query = """
        query GetUserVaults($user: String!) {
            vaults(where: {owner: $user}) {
                id
                collateralType {
                    id
                    price {
                        value
                    }
                    liquidationRatio
                }
                collateral
                debt
            }
        }
        """

        try:
            session = await self._get_session()
            async with session.post(
                self.SUBGRAPH,
                json={"query": query, "variables": {"user": address.lower()}}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})

            for vault in data.get("vaults", []):
                collateral = float(vault.get("collateral", 0))
                debt = float(vault.get("debt", 0))

                if collateral > 0 or debt > 0:
                    col_type = vault.get("collateralType", {})
                    col_id = col_type.get("id", "UNKNOWN")
                    price = float(col_type.get("price", {}).get("value", 0))
                    liq_ratio = float(col_type.get("liquidationRatio", 150))

                    collateral_usd = collateral * price
                    health_factor = (collateral_usd / debt * 100 / liq_ratio) if debt > 0 else float('inf')

                    # Collateral position
                    if collateral > 0:
                        positions.append(DeFiPosition(
                            protocol="MakerDAO",
                            chain="ethereum",
                            position_type="collateral",
                            asset=col_id.split("-")[0],
                            amount=collateral,
                            usd_value=collateral_usd,
                            health_factor=health_factor,
                            liquidation_price=debt * liq_ratio / 100 / collateral if collateral > 0 else 0
                        ))

                    # Debt position
                    if debt > 0:
                        positions.append(DeFiPosition(
                            protocol="MakerDAO",
                            chain="ethereum",
                            position_type="borrow",
                            asset="DAI",
                            amount=-debt,
                            usd_value=-debt,
                            apy=-5.0,  # Stability fee varies
                            health_factor=health_factor
                        ))

        except Exception as e:
            logger.error(f"MakerDAO query error for {address}: {e}")

        return positions

    async def get_dsr_balance(self, address: str) -> Optional[DeFiPosition]:
        """Get user's DAI Savings Rate balance."""
        # Would need to query DSR contract directly
        # This is a placeholder for the pattern

        query = """
        query GetDSRBalance($user: String!) {
            user(id: $user) {
                dsrBalance
            }
        }
        """

        try:
            session = await self._get_session()
            async with session.post(
                self.SUBGRAPH,
                json={"query": query, "variables": {"user": address.lower()}}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})

            user = data.get("user")
            if user:
                balance = float(user.get("dsrBalance", 0))
                if balance > 0:
                    return DeFiPosition(
                        protocol="MakerDAO DSR",
                        chain="ethereum",
                        position_type="savings",
                        asset="DAI",
                        amount=balance,
                        usd_value=balance,
                        apy=self.DSR_APY
                    )

        except Exception as e:
            logger.error(f"MakerDAO DSR query error for {address}: {e}")

        return None

    async def get_protocol_stats(self) -> Dict:
        """Get overall MakerDAO protocol statistics."""
        try:
            query = """
            query GetProtocolStats {
                systemState(id: "current") {
                    totalDebt
                    totalCollateral
                }
            }
            """

            session = await self._get_session()
            async with session.post(
                self.SUBGRAPH,
                json={"query": query}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                data = result.get("data", {})

            state = data.get("systemState", {})
            return {
                "total_dai_debt": float(state.get("totalDebt", 0)),
                "total_collateral_usd": float(state.get("totalCollateral", 0)),
                "dsr_apy": self.DSR_APY
            }

        except Exception as e:
            logger.error(f"MakerDAO stats error: {e}")
            return {}


class DeFiPortfolioTracker:
    """
    Unified DeFi portfolio tracker.

    QA FIX: Converted to async for non-blocking operations.
    """

    def __init__(self):
        load_dotenv()
        self.defillama = DefiLlamaClient()
        self.aave = AaveTracker()
        self.uniswap = UniswapTracker()
        self.lido = LidoTracker()
        self.yearn = YearnTracker()
        self.sushiswap = SushiSwapTracker()
        self.convex = ConvexTracker()
        self.makerdao = MakerDAOTracker()

        self.wallets: Dict[str, List[str]] = {}  # chain -> [addresses]

    async def close(self):
        """Close all tracker sessions."""
        await self.defillama.close()
        await self.aave.close()
        await self.uniswap.close()
        await self.lido.close()
        await self.yearn.close()
        await self.sushiswap.close()
        await self.convex.close()
        await self.makerdao.close()

    def add_wallet(self, address: str, chains: List[str] = None):
        """Add a wallet address to track."""
        if chains is None:
            chains = ["ethereum", "polygon", "arbitrum"]

        for chain in chains:
            if chain not in self.wallets:
                self.wallets[chain] = []
            if address not in self.wallets[chain]:
                self.wallets[chain].append(address)

    async def get_all_positions(self) -> Dict[str, List]:
        """Get all DeFi positions across protocols."""
        all_positions = {
            "lending": [],
            "lp": [],
            "staking": [],
            "vaults": [],
            "cdp": []  # Collateralized debt positions (MakerDAO)
        }

        for chain, addresses in self.wallets.items():
            for address in addresses:
                logger.info(f"Scanning {address[:10]}... on {chain}")

                # Aave positions
                aave_positions = await self.aave.get_user_positions(address, chain)
                for pos in aave_positions:
                    if pos.position_type in ["supply", "borrow"]:
                        all_positions["lending"].append(pos)

                # Uniswap LP positions
                uni_positions = await self.uniswap.get_user_positions(address, chain)
                all_positions["lp"].extend(uni_positions)

                # SushiSwap LP positions
                sushi_positions = await self.sushiswap.get_user_lp_positions(address, chain)
                all_positions["lp"].extend(sushi_positions)

                # Lido staking (Ethereum only)
                if chain == "ethereum":
                    lido_pos = await self.lido.get_steth_balance(address)
                    if lido_pos:
                        all_positions["staking"].append(lido_pos)

                    # SushiSwap staking
                    sushi_staking = await self.sushiswap.get_staking_positions(address)
                    all_positions["staking"].extend(sushi_staking)

                    # Convex staking
                    convex_positions = await self.convex.get_user_positions(address)
                    all_positions["staking"].extend(convex_positions)

                    # MakerDAO vaults/CDPs
                    maker_positions = await self.makerdao.get_user_vaults(address)
                    for pos in maker_positions:
                        if pos.position_type == "collateral":
                            all_positions["cdp"].append(pos)
                        elif pos.position_type == "borrow":
                            all_positions["lending"].append(pos)

                    # MakerDAO DSR
                    dsr_balance = await self.makerdao.get_dsr_balance(address)
                    if dsr_balance:
                        all_positions["staking"].append(dsr_balance)

                await asyncio.sleep(0.5)  # Rate limiting

        return all_positions

    async def get_defi_summary(self) -> dict:
        """Get summary of all DeFi positions."""
        positions = await self.get_all_positions()

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
        total_cdp_collateral = sum(p.usd_value for p in positions.get("cdp", []))

        # Group by protocol
        protocols = {}
        for category, pos_list in positions.items():
            for pos in pos_list:
                protocol = pos.protocol
                if protocol not in protocols:
                    protocols[protocol] = {"total_usd": 0, "positions": 0}
                protocols[protocol]["total_usd"] += abs(pos.usd_value)
                protocols[protocol]["positions"] += 1

        return {
            "total_supplied": total_supplied,
            "total_borrowed": total_borrowed,
            "net_lending": total_supplied - total_borrowed,
            "total_lp": total_lp,
            "total_staked": total_staked,
            "total_cdp_collateral": total_cdp_collateral,
            "total_defi": total_supplied - total_borrowed + total_lp + total_staked + total_cdp_collateral,
            "by_protocol": protocols,
            "positions": positions
        }
    
    async def find_best_yields(self, asset: str = None, min_tvl: float = 1000000) -> List[dict]:
        """Find best yield opportunities."""
        # Get DefiLlama yields
        pools = await self.defillama.get_yields()
        
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
