"""
On-Chain Wallet Tracker
Tracks balances and transactions for self-custody wallets across multiple chains.

Supports:
- Ethereum (ETH + ERC-20 tokens)
- Solana (SOL + SPL tokens)
- Bitcoin (BTC)
- EVM-compatible chains (Polygon, Arbitrum, Base, etc.)

Uses public APIs (no private keys required - read-only).
"""

import logging
import os
import time
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)
from dotenv import load_dotenv


@dataclass
class WalletBalance:
    """Balance for a single asset in a wallet."""
    asset: str
    symbol: str
    balance: float
    usd_value: float
    contract_address: Optional[str] = None
    decimals: int = 18
    chain: str = "ethereum"


@dataclass
class WalletTransaction:
    """A transaction record from on-chain data."""
    hash: str
    chain: str
    timestamp: datetime
    from_address: str
    to_address: str
    asset: str
    amount: float
    usd_value: float
    fee: float
    fee_usd: float
    type: str  # send, receive, swap, contract_interaction
    status: str  # confirmed, pending, failed
    raw_data: dict = None


class EthereumTracker:
    """Track Ethereum and EVM-compatible chain wallets."""
    
    # Chain configurations
    CHAINS = {
        "ethereum": {
            "name": "Ethereum",
            "explorer_api": "https://api.etherscan.io/api",
            "env_key": "ETHERSCAN_API_KEY",
            "native_symbol": "ETH",
            "decimals": 18
        },
        "polygon": {
            "name": "Polygon",
            "explorer_api": "https://api.polygonscan.com/api",
            "env_key": "POLYGONSCAN_API_KEY",
            "native_symbol": "MATIC",
            "decimals": 18
        },
        "arbitrum": {
            "name": "Arbitrum",
            "explorer_api": "https://api.arbiscan.io/api",
            "env_key": "ARBISCAN_API_KEY",
            "native_symbol": "ETH",
            "decimals": 18
        },
        "base": {
            "name": "Base",
            "explorer_api": "https://api.basescan.org/api",
            "env_key": "BASESCAN_API_KEY",
            "native_symbol": "ETH",
            "decimals": 18
        },
        "optimism": {
            "name": "Optimism",
            "explorer_api": "https://api-optimistic.etherscan.io/api",
            "env_key": "OPTIMISM_API_KEY",
            "native_symbol": "ETH",
            "decimals": 18
        }
    }
    
    # Common ERC-20 tokens to track
    COMMON_TOKENS = {
        "ethereum": {
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "DAI": "0x6B175474E89094C44Da98b954EescdeCB5B4F90707",
            "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
            "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
        }
    }
    
    def __init__(self):
        load_dotenv()
        self.session = requests.Session()
        self.api_keys = {}
        
        for chain, config in self.CHAINS.items():
            key = os.getenv(config["env_key"])
            if key:
                self.api_keys[chain] = key
    
    def _make_request(self, chain: str, params: dict) -> Optional[dict]:
        """Make request to block explorer API."""
        if chain not in self.CHAINS:
            logger.warning("Unsupported chain: %s", chain)
            return None
        
        config = self.CHAINS[chain]
        api_key = self.api_keys.get(chain)
        
        if api_key:
            params["apikey"] = api_key
        
        try:
            response = self.session.get(config["explorer_api"], params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "1" or data.get("result"):
                return data.get("result")
            else:
                if "rate limit" in str(data.get("message", "")).lower():
                    logger.warning("Rate limited on %s, waiting...", chain)
                    time.sleep(1)
                return None
                
        except Exception as e:
            logger.warning("Error querying %s: %s", chain, e)
            return None
    
    def get_native_balance(self, address: str, chain: str = "ethereum") -> Optional[WalletBalance]:
        """Get native token balance (ETH, MATIC, etc.)."""
        config = self.CHAINS.get(chain)
        if not config:
            return None
        
        result = self._make_request(chain, {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest"
        })
        
        if result:
            balance = int(result) / (10 ** config["decimals"])
            # Get USD price (simplified - would use price API in production)
            usd_value = self._get_token_price(config["native_symbol"]) * balance
            
            return WalletBalance(
                asset=config["name"],
                symbol=config["native_symbol"],
                balance=balance,
                usd_value=usd_value,
                chain=chain,
                decimals=config["decimals"]
            )
        
        return None
    
    def get_token_balances(self, address: str, chain: str = "ethereum") -> List[WalletBalance]:
        """Get ERC-20 token balances."""
        balances = []
        
        # Get token transfers to find what tokens the address holds
        result = self._make_request(chain, {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc"
        })
        
        if not result:
            return balances
        
        # Find unique tokens
        seen_tokens = set()
        for tx in result[:100]:  # Check recent 100 transfers
            contract = tx.get("contractAddress", "")
            if contract and contract not in seen_tokens:
                seen_tokens.add(contract)
                
                # Get balance for this token
                balance_result = self._make_request(chain, {
                    "module": "account",
                    "action": "tokenbalance",
                    "contractaddress": contract,
                    "address": address,
                    "tag": "latest"
                })
                
                if balance_result:
                    decimals = int(tx.get("tokenDecimal", 18))
                    balance = int(balance_result) / (10 ** decimals)
                    
                    if balance > 0:
                        symbol = tx.get("tokenSymbol", "UNKNOWN")
                        price = self._get_token_price(symbol)
                        
                        balances.append(WalletBalance(
                            asset=tx.get("tokenName", symbol),
                            symbol=symbol,
                            balance=balance,
                            usd_value=balance * price,
                            contract_address=contract,
                            decimals=decimals,
                            chain=chain
                        ))
                
                time.sleep(0.2)  # Rate limiting
        
        return balances
    
    def get_transactions(self, address: str, chain: str = "ethereum", 
                         limit: int = 100) -> List[WalletTransaction]:
        """Get transaction history for an address."""
        transactions = []
        
        # Get normal transactions
        result = self._make_request(chain, {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc"
        })
        
        if result:
            config = self.CHAINS[chain]
            
            for tx in result[:limit]:
                try:
                    value = int(tx.get("value", 0)) / (10 ** config["decimals"])
                    gas_used = int(tx.get("gasUsed", 0))
                    gas_price = int(tx.get("gasPrice", 0))
                    fee = (gas_used * gas_price) / (10 ** config["decimals"])
                    
                    # Determine transaction type
                    from_addr = tx.get("from", "").lower()
                    to_addr = tx.get("to", "").lower()
                    addr_lower = address.lower()
                    
                    if from_addr == addr_lower:
                        tx_type = "send"
                    elif to_addr == addr_lower:
                        tx_type = "receive"
                    else:
                        tx_type = "contract_interaction"
                    
                    transactions.append(WalletTransaction(
                        hash=tx.get("hash", ""),
                        chain=chain,
                        timestamp=datetime.fromtimestamp(int(tx.get("timeStamp", 0))),
                        from_address=from_addr,
                        to_address=to_addr,
                        asset=config["native_symbol"],
                        amount=value,
                        usd_value=0,  # Would need historical price
                        fee=fee,
                        fee_usd=0,
                        type=tx_type,
                        status="confirmed" if tx.get("isError") == "0" else "failed",
                        raw_data=tx
                    ))
                except Exception as e:
                    logger.warning("Error parsing transaction: %s", e)
        
        return transactions
    
    def _get_token_price(self, symbol: str) -> float:
        """Get current USD price for a token (simplified)."""
        # In production, use CoinGecko, CoinMarketCap, or similar
        # This is a placeholder that returns approximate prices
        prices = {
            "ETH": 3500,
            "MATIC": 0.50,
            "USDC": 1.0,
            "USDT": 1.0,
            "DAI": 1.0,
            "WETH": 3500,
            "WBTC": 100000,
            "LINK": 15,
            "UNI": 8,
            "AAVE": 150,
        }
        return prices.get(symbol.upper(), 0)


class SolanaTracker:
    """Track Solana wallets and SPL tokens."""
    
    def __init__(self):
        load_dotenv()
        self.session = requests.Session()
        
        # Use Helius or public RPC
        self.rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self.helius_key = os.getenv("HELIUS_API_KEY")
        
        if self.helius_key:
            self.rpc_url = f"https://mainnet.helius-rpc.com/?api-key={self.helius_key}"
    
    def _rpc_request(self, method: str, params: list) -> Optional[dict]:
        """Make JSON-RPC request to Solana."""
        try:
            response = self.session.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if "result" in data:
                return data["result"]
            if "error" in data:
                logger.warning("Solana RPC error: %s", data['error'])
            return None
            
        except Exception as e:
            logger.warning("Solana request error: %s", e)
            return None
    
    def get_balance(self, address: str) -> Optional[WalletBalance]:
        """Get SOL balance for an address."""
        result = self._rpc_request("getBalance", [address])
        
        if result and "value" in result:
            balance = result["value"] / 1e9  # Lamports to SOL
            price = self._get_sol_price()
            
            return WalletBalance(
                asset="Solana",
                symbol="SOL",
                balance=balance,
                usd_value=balance * price,
                chain="solana",
                decimals=9
            )
        
        return None
    
    def get_token_balances(self, address: str) -> List[WalletBalance]:
        """Get SPL token balances."""
        balances = []
        
        result = self._rpc_request("getTokenAccountsByOwner", [
            address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ])
        
        if result and "value" in result:
            for account in result["value"]:
                try:
                    parsed = account.get("account", {}).get("data", {}).get("parsed", {})
                    info = parsed.get("info", {})
                    token_amount = info.get("tokenAmount", {})
                    
                    balance = float(token_amount.get("uiAmount", 0))
                    
                    if balance > 0:
                        mint = info.get("mint", "")
                        symbol = self._get_token_symbol(mint)
                        price = self._get_token_price(symbol)
                        
                        balances.append(WalletBalance(
                            asset=symbol,
                            symbol=symbol,
                            balance=balance,
                            usd_value=balance * price,
                            contract_address=mint,
                            decimals=int(token_amount.get("decimals", 9)),
                            chain="solana"
                        ))
                except Exception as e:
                    logger.warning("Error parsing SPL token: %s", e)
        
        return balances
    
    def get_transactions(self, address: str, limit: int = 100) -> List[WalletTransaction]:
        """Get transaction history."""
        transactions = []
        
        # Get signatures
        result = self._rpc_request("getSignaturesForAddress", [
            address,
            {"limit": limit}
        ])
        
        if result:
            for sig_info in result[:limit]:
                try:
                    # Get transaction details
                    tx_result = self._rpc_request("getTransaction", [
                        sig_info.get("signature"),
                        {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
                    ])
                    
                    if tx_result:
                        timestamp = datetime.fromtimestamp(sig_info.get("blockTime", 0))
                        
                        transactions.append(WalletTransaction(
                            hash=sig_info.get("signature", ""),
                            chain="solana",
                            timestamp=timestamp,
                            from_address="",
                            to_address="",
                            asset="SOL",
                            amount=0,
                            usd_value=0,
                            fee=tx_result.get("meta", {}).get("fee", 0) / 1e9,
                            fee_usd=0,
                            type="transfer",
                            status="confirmed" if not sig_info.get("err") else "failed",
                            raw_data=tx_result
                        ))
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    logger.warning("Error fetching Solana transaction: %s", e)
        
        return transactions
    
    def _get_sol_price(self) -> float:
        """Get current SOL price."""
        return 200  # Placeholder
    
    def _get_token_price(self, symbol: str) -> float:
        """Get price for SPL token."""
        prices = {
            "USDC": 1.0,
            "USDT": 1.0,
            "RAY": 2.5,
            "SRM": 0.05,
            "BONK": 0.00002,
            "JTO": 3.0,
            "JUP": 1.0,
        }
        return prices.get(symbol.upper(), 0)
    
    def _get_token_symbol(self, mint: str) -> str:
        """Get symbol for a token mint address."""
        # Common Solana tokens
        tokens = {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
            "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R": "RAY",
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": "BONK",
        }
        return tokens.get(mint, mint[:8] + "...")


class BitcoinTracker:
    """Track Bitcoin wallets."""
    
    def __init__(self):
        load_dotenv()
        self.session = requests.Session()
        self.api_url = "https://blockstream.info/api"
    
    def get_balance(self, address: str) -> Optional[WalletBalance]:
        """Get BTC balance for an address."""
        try:
            response = self.session.get(f"{self.api_url}/address/{address}")
            response.raise_for_status()
            data = response.json()
            
            # Calculate balance from chain stats
            funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
            spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
            balance = (funded - spent) / 1e8  # Satoshis to BTC
            
            price = self._get_btc_price()
            
            return WalletBalance(
                asset="Bitcoin",
                symbol="BTC",
                balance=balance,
                usd_value=balance * price,
                chain="bitcoin",
                decimals=8
            )
            
        except Exception as e:
            logger.warning("Error getting BTC balance: %s", e)
            return None
    
    def get_transactions(self, address: str, limit: int = 100) -> List[WalletTransaction]:
        """Get transaction history for a BTC address."""
        transactions = []
        
        try:
            response = self.session.get(f"{self.api_url}/address/{address}/txs")
            response.raise_for_status()
            txs = response.json()
            
            for tx in txs[:limit]:
                try:
                    # Calculate net amount for this address
                    net_amount = 0
                    
                    for vin in tx.get("vin", []):
                        if vin.get("prevout", {}).get("scriptpubkey_address") == address:
                            net_amount -= vin["prevout"].get("value", 0)
                    
                    for vout in tx.get("vout", []):
                        if vout.get("scriptpubkey_address") == address:
                            net_amount += vout.get("value", 0)
                    
                    net_amount_btc = net_amount / 1e8
                    fee = tx.get("fee", 0) / 1e8
                    
                    timestamp = datetime.fromtimestamp(
                        tx.get("status", {}).get("block_time", 0)
                    ) if tx.get("status", {}).get("confirmed") else datetime.now()
                    
                    transactions.append(WalletTransaction(
                        hash=tx.get("txid", ""),
                        chain="bitcoin",
                        timestamp=timestamp,
                        from_address="",
                        to_address="",
                        asset="BTC",
                        amount=abs(net_amount_btc),
                        usd_value=0,
                        fee=fee,
                        fee_usd=0,
                        type="receive" if net_amount > 0 else "send",
                        status="confirmed" if tx.get("status", {}).get("confirmed") else "pending",
                        raw_data=tx
                    ))
                    
                except Exception as e:
                    logger.warning("Error parsing BTC transaction: %s", e)
            
        except Exception as e:
            logger.warning("Error fetching BTC transactions: %s", e)
        
        return transactions
    
    def _get_btc_price(self) -> float:
        """Get current BTC price."""
        return 100000  # Placeholder


class OnChainWalletManager:
    """Unified manager for all on-chain wallets."""
    
    def __init__(self):
        self.eth_tracker = EthereumTracker()
        self.sol_tracker = SolanaTracker()
        self.btc_tracker = BitcoinTracker()
        
        self.wallets: Dict[str, dict] = {}  # address -> {chain, label}
    
    def add_wallet(self, address: str, chain: str, label: str = None):
        """Add a wallet to track."""
        self.wallets[address] = {
            "chain": chain,
            "label": label or address[:8] + "..."
        }
    
    def remove_wallet(self, address: str):
        """Remove a wallet from tracking."""
        if address in self.wallets:
            del self.wallets[address]
    
    def get_all_balances(self) -> Dict[str, List[WalletBalance]]:
        """Get balances for all tracked wallets."""
        all_balances = {}
        
        for address, info in self.wallets.items():
            chain = info["chain"]
            label = info["label"]
            balances = []
            
            print(f"  Fetching {label} ({chain})...")
            
            try:
                if chain in EthereumTracker.CHAINS:
                    # Native balance
                    native = self.eth_tracker.get_native_balance(address, chain)
                    if native:
                        balances.append(native)
                    
                    # Token balances
                    tokens = self.eth_tracker.get_token_balances(address, chain)
                    balances.extend(tokens)
                    
                elif chain == "solana":
                    # SOL balance
                    sol = self.sol_tracker.get_balance(address)
                    if sol:
                        balances.append(sol)
                    
                    # SPL tokens
                    tokens = self.sol_tracker.get_token_balances(address)
                    balances.extend(tokens)
                    
                elif chain == "bitcoin":
                    btc = self.btc_tracker.get_balance(address)
                    if btc:
                        balances.append(btc)
                
            except Exception as e:
                logger.warning("Error fetching wallet balances: %s", e)
            
            all_balances[address] = balances
        
        return all_balances
    
    def get_aggregated_balances(self) -> Dict[str, dict]:
        """Get balances aggregated by asset across all wallets."""
        all_balances = self.get_all_balances()
        aggregated = {}
        
        for address, balances in all_balances.items():
            label = self.wallets[address]["label"]
            
            for bal in balances:
                symbol = bal.symbol
                
                if symbol not in aggregated:
                    aggregated[symbol] = {
                        "total_balance": 0,
                        "total_usd": 0,
                        "wallets": []
                    }
                
                aggregated[symbol]["total_balance"] += bal.balance
                aggregated[symbol]["total_usd"] += bal.usd_value
                aggregated[symbol]["wallets"].append({
                    "address": address,
                    "label": label,
                    "chain": bal.chain,
                    "balance": bal.balance,
                    "usd_value": bal.usd_value
                })
        
        return aggregated
    
    def save_wallets(self, filepath: str = None):
        """Save wallet configuration."""
        if filepath is None:
            filepath = os.path.expanduser("~/.crypto_portfolio/wallets.json")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w") as f:
            json.dump(self.wallets, f, indent=2)
    
    def load_wallets(self, filepath: str = None) -> bool:
        """Load wallet configuration."""
        if filepath is None:
            filepath = os.path.expanduser("~/.crypto_portfolio/wallets.json")
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, "r") as f:
                self.wallets = json.load(f)
            return True
        except Exception as e:
            logger.warning("Error loading wallets: %s", e)
            return False


def main():
    """CLI for on-chain wallet tracking."""
    import argparse
    from tabulate import tabulate
    
    parser = argparse.ArgumentParser(description="On-Chain Wallet Tracker")
    parser.add_argument("--add", nargs=3, metavar=("ADDRESS", "CHAIN", "LABEL"),
                        help="Add wallet to track")
    parser.add_argument("--remove", type=str, help="Remove wallet by address")
    parser.add_argument("--list", action="store_true", help="List tracked wallets")
    parser.add_argument("--balances", action="store_true", help="Show all balances")
    parser.add_argument("--address", type=str, help="Check specific address")
    parser.add_argument("--chain", type=str, default="ethereum", 
                        help="Chain for --address query")
    
    args = parser.parse_args()
    
    manager = OnChainWalletManager()
    manager.load_wallets()
    
    if args.add:
        address, chain, label = args.add
        manager.add_wallet(address, chain, label)
        manager.save_wallets()
        print(f"✓ Added {label} ({chain})")
    
    elif args.remove:
        manager.remove_wallet(args.remove)
        manager.save_wallets()
        print(f"✓ Removed {args.remove}")
    
    elif args.list:
        print("\n📋 Tracked Wallets")
        print("-" * 60)
        for addr, info in manager.wallets.items():
            print(f"  {info['label']}: {addr[:20]}... ({info['chain']})")
    
    elif args.balances:
        print("\n💰 ON-CHAIN WALLET BALANCES")
        print("=" * 60)
        
        aggregated = manager.get_aggregated_balances()
        
        table_data = []
        total_usd = 0
        
        for symbol, data in sorted(aggregated.items(), 
                                    key=lambda x: x[1]["total_usd"], reverse=True):
            table_data.append([
                symbol,
                f"{data['total_balance']:.8f}".rstrip('0').rstrip('.'),
                f"${data['total_usd']:,.2f}",
                len(data["wallets"])
            ])
            total_usd += data["total_usd"]
        
        print(tabulate(table_data, 
                       headers=["Asset", "Balance", "USD Value", "Wallets"],
                       tablefmt="simple"))
        print(f"\n💎 Total On-Chain Value: ${total_usd:,.2f}")
    
    elif args.address:
        print(f"\n🔍 Checking {args.address[:20]}... on {args.chain}")
        print("-" * 50)
        
        manager.add_wallet(args.address, args.chain, "Query")
        balances = manager.get_all_balances().get(args.address, [])
        
        for bal in balances:
            print(f"  {bal.symbol}: {bal.balance:.8f} (${bal.usd_value:,.2f})")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
