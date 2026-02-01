"""
Cosmos ecosystem wallet tracking.

Tracks balances, staking delegations, and rewards across Cosmos SDK chains
using LCD (Light Client Daemon) REST endpoints.
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Any

import aiohttp


@dataclass
class CosmosChainConfig:
    """Configuration for a Cosmos SDK chain."""
    name: str
    chain_id: str
    lcd_url: str
    native_denom: str
    native_symbol: str
    decimals: int = 6
    explorer_url: str = ""


COSMOS_CHAINS: Dict[str, CosmosChainConfig] = {
    "juno": CosmosChainConfig(
        name="Juno",
        chain_id="juno-1",
        lcd_url="https://juno-api.polkachu.com",
        native_denom="ujuno",
        native_symbol="JUNO",
        decimals=6,
        explorer_url="https://www.mintscan.io/juno",
    ),
    "celestia": CosmosChainConfig(
        name="Celestia",
        chain_id="celestia",
        lcd_url="https://celestia-api.polkachu.com",
        native_denom="utia",
        native_symbol="TIA",
        decimals=6,
        explorer_url="https://www.mintscan.io/celestia",
    ),
    "kava": CosmosChainConfig(
        name="Kava",
        chain_id="kava_2222-10",
        lcd_url="https://api.data.kava.io",
        native_denom="ukava",
        native_symbol="KAVA",
        decimals=6,
        explorer_url="https://www.mintscan.io/kava",
    ),
    "sei": CosmosChainConfig(
        name="Sei",
        chain_id="pacific-1",
        lcd_url="https://rest.sei-apis.com",
        native_denom="usei",
        native_symbol="SEI",
        decimals=6,
        explorer_url="https://www.mintscan.io/sei",
    ),
}


@dataclass
class CosmosBalance:
    """A single balance on a Cosmos chain."""
    symbol: str
    amount: Decimal
    decimals: int
    denom: str
    chain: str


@dataclass
class CosmosWalletSummary:
    """Summary of a Cosmos wallet's holdings."""
    address: str
    chain: str
    balances: List[CosmosBalance] = field(default_factory=list)
    total_by_symbol: Dict[str, Decimal] = field(default_factory=dict)


class CosmosWalletTracker:
    """Tracks wallet balances across Cosmos SDK chains via LCD REST APIs."""

    def __init__(self, wallets: Dict[str, str]):
        """
        Args:
            wallets: Mapping of address -> chain key (e.g. "juno", "celestia")
        """
        self.wallets = wallets
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _lcd_get(self, url: str) -> Any:
        """Make a GET request to a Cosmos LCD endpoint."""
        session = await self._get_session()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"LCD request failed ({resp.status}): {text[:200]}")
            return await resp.json()

    def _get_chain_config(self, chain: str) -> CosmosChainConfig:
        if chain not in COSMOS_CHAINS:
            raise ValueError(f"Unknown Cosmos chain: {chain}. Supported: {list(COSMOS_CHAINS.keys())}")
        return COSMOS_CHAINS[chain]

    def _convert_amount(self, raw_amount: str, config: CosmosChainConfig) -> Decimal:
        """Convert micro-denom amount to human-readable."""
        return Decimal(raw_amount) / Decimal(10 ** config.decimals)

    async def get_balances(self, address: str, chain: str) -> List[CosmosBalance]:
        """Query bank balances for an address."""
        config = self._get_chain_config(chain)
        url = f"{config.lcd_url}/cosmos/bank/v1beta1/balances/{address}"

        try:
            data = await self._lcd_get(url)
        except Exception as e:
            logging.warning(f"Failed to get balances for {address} on {chain}: {e}")
            return []

        balances = []
        for bal in data.get("balances", []):
            denom = bal.get("denom", "")
            raw = bal.get("amount", "0")

            if denom == config.native_denom:
                amount = self._convert_amount(raw, config)
                if amount > 0:
                    balances.append(CosmosBalance(
                        symbol=config.native_symbol,
                        amount=amount,
                        decimals=config.decimals,
                        denom=denom,
                        chain=chain,
                    ))
            else:
                # Non-native IBC or CW20 token -- store raw for now
                amount = Decimal(raw)
                if amount > 0:
                    balances.append(CosmosBalance(
                        symbol=denom[:16],
                        amount=amount,
                        decimals=0,
                        denom=denom,
                        chain=chain,
                    ))

        return balances

    async def get_staking(self, address: str, chain: str) -> List[CosmosBalance]:
        """Query staking delegations for an address."""
        config = self._get_chain_config(chain)
        url = f"{config.lcd_url}/cosmos/staking/v1beta1/delegations/{address}"

        try:
            data = await self._lcd_get(url)
        except Exception as e:
            logging.warning(f"Failed to get staking for {address} on {chain}: {e}")
            return []

        balances = []
        for delegation in data.get("delegation_responses", []):
            bal = delegation.get("balance", {})
            denom = bal.get("denom", "")
            raw = bal.get("amount", "0")

            if denom == config.native_denom:
                amount = self._convert_amount(raw, config)
                if amount > 0:
                    balances.append(CosmosBalance(
                        symbol=f"{config.native_symbol}-staked",
                        amount=amount,
                        decimals=config.decimals,
                        denom=denom,
                        chain=chain,
                    ))

        return balances

    async def get_rewards(self, address: str, chain: str) -> List[CosmosBalance]:
        """Query pending staking rewards for an address."""
        config = self._get_chain_config(chain)
        url = f"{config.lcd_url}/cosmos/distribution/v1beta1/delegators/{address}/rewards"

        try:
            data = await self._lcd_get(url)
        except Exception as e:
            logging.warning(f"Failed to get rewards for {address} on {chain}: {e}")
            return []

        balances = []
        for reward in data.get("total", []):
            denom = reward.get("denom", "")
            # Rewards come as decimal strings (e.g. "123456.789")
            raw = reward.get("amount", "0")

            if denom == config.native_denom:
                # Truncate to integer micro-units first, then convert
                micro = Decimal(raw).to_integral_value()
                amount = micro / Decimal(10 ** config.decimals)
                if amount > 0:
                    balances.append(CosmosBalance(
                        symbol=f"{config.native_symbol}-rewards",
                        amount=amount,
                        decimals=config.decimals,
                        denom=denom,
                        chain=chain,
                    ))

        return balances

    async def get_wallet_summary(self, address: str, chain: str) -> CosmosWalletSummary:
        """Get combined balances, staking, and rewards for a wallet."""
        all_balances: List[CosmosBalance] = []

        bank = await self.get_balances(address, chain)
        all_balances.extend(bank)

        staking = await self.get_staking(address, chain)
        all_balances.extend(staking)

        rewards = await self.get_rewards(address, chain)
        all_balances.extend(rewards)

        total_by_symbol: Dict[str, Decimal] = {}
        for bal in all_balances:
            if bal.symbol not in total_by_symbol:
                total_by_symbol[bal.symbol] = Decimal("0")
            total_by_symbol[bal.symbol] += bal.amount

        return CosmosWalletSummary(
            address=address,
            chain=chain,
            balances=all_balances,
            total_by_symbol=total_by_symbol,
        )

    async def get_all_wallets_summary(self) -> Dict[str, CosmosWalletSummary]:
        """Get summaries for all configured wallets."""
        summaries = {}
        for address, chain in self.wallets.items():
            try:
                summaries[address] = await self.get_wallet_summary(address, chain)
            except Exception as e:
                logging.warning(f"Failed to get Cosmos summary for {address} on {chain}: {e}")
        return summaries

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()


def format_cosmos_summary(summary: CosmosWalletSummary) -> str:
    """Format Cosmos wallet summary for display."""
    lines = [
        f"Cosmos Wallet ({summary.chain}): {summary.address[:12]}...{summary.address[-6:]}",
        "=" * 50,
    ]

    for bal in summary.balances:
        lines.append(f"  {bal.symbol}: {float(bal.amount):.6f}")

    return "\n".join(lines)


async def get_cosmos_balances(wallets: Dict[str, str]) -> Dict[str, CosmosWalletSummary]:
    """Quick function to get Cosmos wallet balances."""
    tracker = CosmosWalletTracker(wallets)
    try:
        return await tracker.get_all_wallets_summary()
    finally:
        await tracker.close()
