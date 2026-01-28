"""
EVM Wallet tracking for Coinbase Wallet and other EVM-compatible wallets.

Supports Ethereum, Polygon, Arbitrum, Base, Optimism, and other EVM chains.
Uses Alchemy or direct RPC for balance queries.
"""

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Any
import aiohttp

from config import settings


@dataclass
class ChainConfig:
    """Configuration for an EVM chain."""
    name: str
    chain_id: int
    rpc_url: str
    native_symbol: str
    native_decimals: int = 18
    explorer_url: str = ""
    alchemy_network: str = ""  # For Alchemy API


# Supported chains with free RPC endpoints
CHAINS: Dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        native_symbol="ETH",
        explorer_url="https://etherscan.io",
        alchemy_network="eth-mainnet",
    ),
    "polygon": ChainConfig(
        name="Polygon",
        chain_id=137,
        rpc_url="https://polygon-rpc.com",
        native_symbol="MATIC",
        explorer_url="https://polygonscan.com",
        alchemy_network="polygon-mainnet",
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum",
        chain_id=42161,
        rpc_url="https://arb1.arbitrum.io/rpc",
        native_symbol="ETH",
        explorer_url="https://arbiscan.io",
        alchemy_network="arb-mainnet",
    ),
    "optimism": ChainConfig(
        name="Optimism",
        chain_id=10,
        rpc_url="https://mainnet.optimism.io",
        native_symbol="ETH",
        explorer_url="https://optimistic.etherscan.io",
        alchemy_network="opt-mainnet",
    ),
    "base": ChainConfig(
        name="Base",
        chain_id=8453,
        rpc_url="https://mainnet.base.org",
        native_symbol="ETH",
        explorer_url="https://basescan.org",
        alchemy_network="base-mainnet",
    ),
    "avalanche": ChainConfig(
        name="Avalanche C-Chain",
        chain_id=43114,
        rpc_url="https://api.avax.network/ext/bc/C/rpc",
        native_symbol="AVAX",
        explorer_url="https://snowtrace.io",
        alchemy_network="",
    ),
    "bsc": ChainConfig(
        name="BNB Smart Chain",
        chain_id=56,
        rpc_url="https://bsc-dataseed.binance.org",
        native_symbol="BNB",
        explorer_url="https://bscscan.com",
        alchemy_network="",
    ),
}


# Common ERC-20 tokens to track (address -> symbol mapping per chain)
TRACKED_TOKENS: Dict[str, Dict[str, tuple]] = {
    "ethereum": {
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": ("USDC", 6),
        "0xdAC17F958D2ee523a2206206994597C13D831ec7": ("USDT", 6),
        "0x6B175474E89094C44Da98b954EescdeCb5BadAce": ("DAI", 18),
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": ("WBTC", 8),
        "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0": ("MATIC", 18),
        "0x514910771AF9Ca656af840dff83E8264EcF986CA": ("LINK", 18),
        "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": ("UNI", 18),
    },
    "polygon": {
        "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174": ("USDC", 6),
        "0xc2132D05D31c914a87C6611C10748AEb04B58e8F": ("USDT", 6),
        "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063": ("DAI", 18),
        "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6": ("WBTC", 8),
        "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619": ("WETH", 18),
    },
    "arbitrum": {
        "0xaf88d065e77c8cC2239327C5EDb3A432268e5831": ("USDC", 6),
        "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9": ("USDT", 6),
        "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f": ("WBTC", 8),
        "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1": ("WETH", 18),
    },
    "base": {
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": ("USDC", 6),
        "0x4200000000000000000000000000000000000006": ("WETH", 18),
    },
}


@dataclass
class TokenBalance:
    """Balance of a token on a specific chain."""
    symbol: str
    chain: str
    amount: Decimal
    decimals: int
    contract_address: Optional[str] = None  # None for native token
    
    @property
    def is_native(self) -> bool:
        return self.contract_address is None


@dataclass
class WalletSummary:
    """Summary of wallet holdings across all chains."""
    address: str
    balances: List[TokenBalance]
    total_by_symbol: Dict[str, Decimal]  # Aggregated across chains
    
    def get_balance(self, symbol: str, chain: Optional[str] = None) -> Decimal:
        """Get balance for a symbol, optionally filtered by chain."""
        total = Decimal("0")
        for bal in self.balances:
            if bal.symbol == symbol:
                if chain is None or bal.chain == chain:
                    total += bal.amount
        return total


class EVMWalletTracker:
    """Tracks balances across multiple EVM chains."""
    
    def __init__(
        self,
        addresses: List[str],
        chains: Optional[List[str]] = None,
        alchemy_api_key: Optional[str] = None,
    ):
        self.addresses = [addr.lower() for addr in addresses]
        self.chains = chains or list(CHAINS.keys())
        self.alchemy_api_key = alchemy_api_key
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _rpc_call(
        self,
        chain: str,
        method: str,
        params: List[Any],
    ) -> Any:
        """Make an RPC call to a chain."""
        config = CHAINS.get(chain)
        if not config:
            raise ValueError(f"Unknown chain: {chain}")
        
        # Use Alchemy if available and chain is supported
        if self.alchemy_api_key and config.alchemy_network:
            url = f"https://{config.alchemy_network}.g.alchemy.com/v2/{self.alchemy_api_key}"
        else:
            url = config.rpc_url
        
        session = await self._get_session()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            if "error" in data:
                raise Exception(f"RPC error: {data['error']}")
            return data.get("result")
    
    async def get_native_balance(self, address: str, chain: str) -> Decimal:
        """Get native token balance for an address on a chain."""
        result = await self._rpc_call(chain, "eth_getBalance", [address, "latest"])
        
        if result is None:
            return Decimal("0")
        
        # Convert from hex wei to decimal
        wei = int(result, 16)
        config = CHAINS[chain]
        return Decimal(wei) / Decimal(10 ** config.native_decimals)
    
    async def get_token_balance(
        self,
        address: str,
        chain: str,
        token_address: str,
        decimals: int,
    ) -> Decimal:
        """Get ERC-20 token balance."""
        # balanceOf(address) function selector
        data = f"0x70a08231000000000000000000000000{address[2:]}"
        
        result = await self._rpc_call(
            chain,
            "eth_call",
            [{"to": token_address, "data": data}, "latest"]
        )
        
        if result is None or result == "0x":
            return Decimal("0")
        
        balance = int(result, 16)
        return Decimal(balance) / Decimal(10 ** decimals)
    
    async def get_all_balances(self, address: str) -> List[TokenBalance]:
        """Get all balances for an address across all configured chains."""
        balances = []
        tasks = []
        
        for chain in self.chains:
            config = CHAINS.get(chain)
            if not config:
                continue
            
            # Native balance task
            tasks.append(self._get_native_balance_task(address, chain, config))
            
            # Token balance tasks
            if chain in TRACKED_TOKENS:
                for token_addr, (symbol, decimals) in TRACKED_TOKENS[chain].items():
                    tasks.append(
                        self._get_token_balance_task(
                            address, chain, token_addr, symbol, decimals
                        )
                    )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, TokenBalance) and result.amount > 0:
                balances.append(result)
        
        return balances
    
    async def _get_native_balance_task(
        self,
        address: str,
        chain: str,
        config: ChainConfig,
    ) -> TokenBalance:
        """Task wrapper for native balance fetch."""
        try:
            amount = await self.get_native_balance(address, chain)
            return TokenBalance(
                symbol=config.native_symbol,
                chain=chain,
                amount=amount,
                decimals=config.native_decimals,
            )
        except Exception as e:
            print(f"Warning: Failed to get {chain} native balance: {e}")
            return TokenBalance(
                symbol=config.native_symbol,
                chain=chain,
                amount=Decimal("0"),
                decimals=config.native_decimals,
            )
    
    async def _get_token_balance_task(
        self,
        address: str,
        chain: str,
        token_address: str,
        symbol: str,
        decimals: int,
    ) -> TokenBalance:
        """Task wrapper for token balance fetch."""
        try:
            amount = await self.get_token_balance(address, chain, token_address, decimals)
            return TokenBalance(
                symbol=symbol,
                chain=chain,
                amount=amount,
                decimals=decimals,
                contract_address=token_address,
            )
        except Exception as e:
            print(f"Warning: Failed to get {symbol} on {chain}: {e}")
            return TokenBalance(
                symbol=symbol,
                chain=chain,
                amount=Decimal("0"),
                decimals=decimals,
                contract_address=token_address,
            )
    
    async def get_wallet_summary(self, address: str) -> WalletSummary:
        """Get complete wallet summary for an address."""
        balances = await self.get_all_balances(address)
        
        # Aggregate by symbol
        total_by_symbol: Dict[str, Decimal] = {}
        for bal in balances:
            if bal.symbol not in total_by_symbol:
                total_by_symbol[bal.symbol] = Decimal("0")
            total_by_symbol[bal.symbol] += bal.amount
        
        return WalletSummary(
            address=address,
            balances=balances,
            total_by_symbol=total_by_symbol,
        )
    
    async def get_all_wallets_summary(self) -> Dict[str, WalletSummary]:
        """Get summaries for all configured addresses."""
        summaries = {}
        
        for address in self.addresses:
            summaries[address] = await self.get_wallet_summary(address)
        
        return summaries
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


def format_wallet_summary(summary: WalletSummary) -> str:
    """Format wallet summary for display."""
    lines = []
    lines.append(f"Wallet: {summary.address[:8]}...{summary.address[-6:]}")
    lines.append("=" * 50)
    
    # Group by symbol
    lines.append(f"{'Symbol':<8} {'Chain':<12} {'Amount':>18}")
    lines.append("-" * 50)
    
    # Sort by symbol then chain
    sorted_balances = sorted(summary.balances, key=lambda x: (x.symbol, x.chain))
    
    for bal in sorted_balances:
        lines.append(f"{bal.symbol:<8} {bal.chain:<12} {float(bal.amount):>18.6f}")
    
    lines.append("-" * 50)
    lines.append("\nTotals by Symbol:")
    
    for symbol, total in sorted(summary.total_by_symbol.items(), key=lambda x: -float(x[1])):
        lines.append(f"  {symbol}: {float(total):.6f}")
    
    return "\n".join(lines)


# Convenience function
async def get_wallet_balances(
    addresses: List[str],
    chains: Optional[List[str]] = None,
) -> Dict[str, WalletSummary]:
    """Quick function to get wallet balances."""
    tracker = EVMWalletTracker(addresses, chains)
    try:
        return await tracker.get_all_wallets_summary()
    finally:
        await tracker.close()
