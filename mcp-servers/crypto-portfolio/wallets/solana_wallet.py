"""
Solana wallet tracking for Coinbase Wallet.

Tracks SOL balance and SPL tokens on Solana mainnet.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging

import aiohttp


# Common SPL tokens to track (mint address -> (symbol, decimals))
TRACKED_SPL_TOKENS: Dict[str, tuple] = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": ("USDC", 6),
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": ("USDT", 6),
    "So11111111111111111111111111111111111111112": ("WSOL", 9),
    "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj": ("stSOL", 9),  # Lido staked SOL
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": ("mSOL", 9),   # Marinade staked SOL
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn": ("jitoSOL", 9),  # Jito staked SOL
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": ("BONK", 5),
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": ("JUP", 6),
    "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm": ("WIF", 6),
    "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3": ("PYTH", 6),
    "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof": ("RNDR", 8),
    "Saber2gLauYim4Mvftnrasomsv6NvAuncvMEZwcLpD1": ("SBR", 6),
    "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE": ("ORCA", 6),
    "hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux": ("HNT", 8),
    "4vMsoUT2BWatFweudnQM1xedRLfJgJ7hswhcpz4xgBTy": ("HONEY", 9),
    "5MAYDfq5yxtudAhtfyuMBuHZjgAbaS9tbEyEQYAhDS5y": ("ACS", 6),
}


@dataclass
class SolanaBalance:
    """Balance on Solana."""
    symbol: str
    amount: Decimal
    decimals: int
    mint_address: Optional[str] = None  # None for native SOL
    
    @property
    def is_native(self) -> bool:
        return self.mint_address is None


@dataclass
class SolanaWalletSummary:
    """Summary of Solana wallet holdings."""
    address: str
    sol_balance: Decimal
    balances: List[SolanaBalance]
    total_by_symbol: Dict[str, Decimal]


class SolanaWalletTracker:
    """Tracks Solana wallet balances."""
    
    def __init__(
        self,
        addresses: List[str],
        rpc_url: Optional[str] = None,
    ):
        self.addresses = addresses
        self.rpc_url = rpc_url or "https://api.mainnet-beta.solana.com"
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _rpc_call(self, method: str, params: List[Any]) -> Any:
        """Make an RPC call to Solana."""
        session = await self._get_session()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        
        async with session.post(self.rpc_url, json=payload) as resp:
            data = await resp.json()
            if "error" in data:
                raise Exception(f"Solana RPC error: {data['error']}")
            return data.get("result")
    
    async def get_sol_balance(self, address: str) -> Decimal:
        """Get native SOL balance."""
        result = await self._rpc_call("getBalance", [address])
        
        if result is None:
            return Decimal("0")
        
        lamports = result.get("value", 0)
        return Decimal(lamports) / Decimal(10 ** 9)
    
    async def get_token_accounts(self, address: str) -> List[Dict]:
        """Get all SPL token accounts for an address."""
        result = await self._rpc_call(
            "getTokenAccountsByOwner",
            [
                address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ]
        )
        
        if result is None:
            return []
        
        return result.get("value", [])
    
    async def get_all_balances(self, address: str) -> List[SolanaBalance]:
        """Get all balances for an address."""
        balances = []
        
        # Get native SOL
        try:
            sol_balance = await self.get_sol_balance(address)
            if sol_balance > 0:
                balances.append(SolanaBalance(
                    symbol="SOL",
                    amount=sol_balance,
                    decimals=9,
                ))
        except Exception as e:
            logging.warning(f"Failed to get SOL balance: {e}")
        
        # Get SPL tokens
        try:
            token_accounts = await self.get_token_accounts(address)
            
            for account in token_accounts:
                try:
                    parsed = account.get("account", {}).get("data", {}).get("parsed", {})
                    info = parsed.get("info", {})
                    
                    mint = info.get("mint", "")
                    token_amount = info.get("tokenAmount", {})
                    
                    amount = Decimal(token_amount.get("uiAmountString", "0"))
                    decimals = token_amount.get("decimals", 0)
                    
                    if amount <= 0:
                        continue
                    
                    # Look up symbol
                    if mint in TRACKED_SPL_TOKENS:
                        symbol, _ = TRACKED_SPL_TOKENS[mint]
                    else:
                        # Unknown token - use shortened mint address
                        symbol = f"SPL:{mint[:8]}"
                    
                    balances.append(SolanaBalance(
                        symbol=symbol,
                        amount=amount,
                        decimals=decimals,
                        mint_address=mint,
                    ))
                    
                except Exception as e:
                    logging.warning(f"Failed to parse token account: {e}")
                    continue
                    
        except Exception as e:
            logging.warning(f"Failed to get token accounts: {e}")
        
        return balances
    
    async def get_wallet_summary(self, address: str) -> SolanaWalletSummary:
        """Get complete wallet summary."""
        balances = await self.get_all_balances(address)
        
        # Aggregate by symbol
        total_by_symbol: Dict[str, Decimal] = {}
        sol_balance = Decimal("0")
        
        for bal in balances:
            if bal.symbol == "SOL":
                sol_balance = bal.amount
            
            if bal.symbol not in total_by_symbol:
                total_by_symbol[bal.symbol] = Decimal("0")
            total_by_symbol[bal.symbol] += bal.amount
        
        return SolanaWalletSummary(
            address=address,
            sol_balance=sol_balance,
            balances=balances,
            total_by_symbol=total_by_symbol,
        )
    
    async def get_all_wallets_summary(self) -> Dict[str, SolanaWalletSummary]:
        """Get summaries for all configured addresses."""
        summaries = {}
        
        for address in self.addresses:
            try:
                summaries[address] = await self.get_wallet_summary(address)
            except Exception as e:
                logging.warning(f"Failed to get summary for {address}: {e}")
        
        return summaries
    
    async def get_staking_info(self, address: str) -> List[Dict]:
        """Get staking account information."""
        try:
            result = await self._rpc_call(
                "getProgramAccounts",
                [
                    "Stake11111111111111111111111111111111111111",
                    {
                        "encoding": "jsonParsed",
                        "filters": [
                            {
                                "memcmp": {
                                    "offset": 12,
                                    "bytes": address,
                                }
                            }
                        ],
                    },
                ]
            )
            
            stakes = []
            for account in result or []:
                parsed = account.get("account", {}).get("data", {}).get("parsed", {})
                info = parsed.get("info", {})
                stake_info = info.get("stake", {})
                
                if stake_info:
                    delegation = stake_info.get("delegation", {})
                    stakes.append({
                        "pubkey": account.get("pubkey"),
                        "stake_amount": Decimal(delegation.get("stake", 0)) / Decimal(10 ** 9),
                        "voter": delegation.get("voter"),
                        "activation_epoch": delegation.get("activationEpoch"),
                    })
            
            return stakes
            
        except Exception as e:
            logging.warning(f"Failed to get staking info: {e}")
            return []
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


def format_solana_summary(summary: SolanaWalletSummary) -> str:
    """Format Solana wallet summary for display."""
    lines = []
    lines.append(f"Solana Wallet: {summary.address[:8]}...{summary.address[-6:]}")
    lines.append("=" * 50)
    lines.append(f"SOL Balance: {float(summary.sol_balance):.4f} SOL")
    lines.append("")
    
    if len(summary.balances) > 1:
        lines.append("Token Balances:")
        for bal in sorted(summary.balances, key=lambda x: x.symbol):
            if bal.symbol != "SOL":
                lines.append(f"  {bal.symbol}: {float(bal.amount):.6f}")
    
    return "\n".join(lines)


# Convenience function
async def get_solana_balances(addresses: List[str]) -> Dict[str, SolanaWalletSummary]:
    """Quick function to get Solana wallet balances."""
    tracker = SolanaWalletTracker(addresses)
    try:
        return await tracker.get_all_wallets_summary()
    finally:
        await tracker.close()
