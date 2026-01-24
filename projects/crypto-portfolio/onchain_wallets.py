"""
On-Chain Wallet Tracker
Track balances from Ethereum, Bitcoin, and Solana wallets.

Supports:
- Ethereum (and EVM chains) via Web3
- Bitcoin via public APIs
- Solana via Solana RPC
- ERC-20 token balances
- Multiple wallets per chain
"""

import os
import json
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass
class WalletBalance:
    """Represents a wallet balance."""
    address: str
    chain: str
    asset: str
    balance: float
    usd_value: Optional[float] = None
    contract_address: Optional[str] = None  # For tokens
    label: Optional[str] = None


class EthereumWalletTracker:
    """Track Ethereum and EVM-compatible chain wallets."""
    
    # Common ERC-20 tokens to track
    COMMON_TOKENS = {
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "DAI": "0x6B175474E89094C44Da98b954EescdeCB5C4F27",
        "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
        "SHIB": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
        "MATIC": "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
        "stETH": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
        "cbETH": "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704",
    }
    
    # ERC-20 ABI for balanceOf
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }
    ]
    
    def __init__(self, rpc_url: str = None):
        """
        Initialize Ethereum tracker.
        
        Args:
            rpc_url: Ethereum RPC URL (defaults to public endpoint)
        """
        self.rpc_url = rpc_url or os.getenv(
            "ETH_RPC_URL",
            "https://eth.llamarpc.com"  # Free public RPC
        )
        self.web3 = None
        self._init_web3()
    
    def _init_web3(self):
        """Initialize Web3 connection."""
        try:
            from web3 import Web3
            self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.web3.is_connected():
                print("Warning: Could not connect to Ethereum RPC")
                self.web3 = None
        except ImportError:
            print("Warning: web3 not installed. Run: pip install web3")
            self.web3 = None
    
    def get_eth_balance(self, address: str) -> Optional[float]:
        """Get native ETH balance."""
        if not self.web3:
            return self._get_eth_balance_api(address)
        
        try:
            balance_wei = self.web3.eth.get_balance(
                self.web3.to_checksum_address(address)
            )
            return float(self.web3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            print(f"Error getting ETH balance: {e}")
            return None
    
    def _get_eth_balance_api(self, address: str) -> Optional[float]:
        """Fallback: Get ETH balance via Etherscan API."""
        api_key = os.getenv("ETHERSCAN_API_KEY", "")
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data["status"] == "1":
                return float(data["result"]) / 1e18
        except Exception as e:
            print(f"Error getting ETH balance from API: {e}")
        
        return None
    
    def get_token_balance(
        self,
        address: str,
        token_address: str,
        decimals: int = 18
    ) -> Optional[float]:
        """Get ERC-20 token balance."""
        if not self.web3:
            return self._get_token_balance_api(address, token_address)
        
        try:
            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )
            
            balance = contract.functions.balanceOf(
                self.web3.to_checksum_address(address)
            ).call()
            
            # Try to get decimals from contract
            try:
                decimals = contract.functions.decimals().call()
            except:
                pass
            
            return float(balance) / (10 ** decimals)
            
        except Exception as e:
            print(f"Error getting token balance: {e}")
            return None
    
    def _get_token_balance_api(
        self,
        address: str,
        token_address: str
    ) -> Optional[float]:
        """Fallback: Get token balance via Etherscan API."""
        api_key = os.getenv("ETHERSCAN_API_KEY", "")
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": token_address,
            "address": address,
            "tag": "latest",
            "apikey": api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data["status"] == "1":
                # Assume 18 decimals if we can't determine
                return float(data["result"]) / 1e18
        except Exception as e:
            print(f"Error getting token balance from API: {e}")
        
        return None
    
    def get_all_balances(
        self,
        address: str,
        include_tokens: bool = True
    ) -> List[WalletBalance]:
        """Get ETH and all common token balances."""
        balances = []
        
        # Get ETH balance
        eth_balance = self.get_eth_balance(address)
        if eth_balance and eth_balance > 0:
            balances.append(WalletBalance(
                address=address,
                chain="ethereum",
                asset="ETH",
                balance=eth_balance
            ))
        
        # Get token balances
        if include_tokens:
            for symbol, token_address in self.COMMON_TOKENS.items():
                balance = self.get_token_balance(address, token_address)
                if balance and balance > 0:
                    balances.append(WalletBalance(
                        address=address,
                        chain="ethereum",
                        asset=symbol,
                        balance=balance,
                        contract_address=token_address
                    ))
        
        return balances


class BitcoinWalletTracker:
    """Track Bitcoin wallet balances."""
    
    def __init__(self):
        self.api_url = "https://blockchain.info"
    
    def get_balance(self, address: str) -> Optional[float]:
        """Get BTC balance for an address."""
        try:
            # Try blockchain.info API
            response = requests.get(
                f"{self.api_url}/rawaddr/{address}",
                params={"limit": 0}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Balance is in satoshis
                return float(data["final_balance"]) / 1e8
            
            # Fallback to balance endpoint
            response = requests.get(
                f"{self.api_url}/balance",
                params={"active": address}
            )
            
            if response.status_code == 200:
                data = response.json()
                if address in data:
                    return float(data[address]["final_balance"]) / 1e8
                    
        except Exception as e:
            print(f"Error getting BTC balance: {e}")
        
        return None
    
    def get_all_balances(self, address: str) -> List[WalletBalance]:
        """Get BTC balance for address."""
        balances = []
        
        balance = self.get_balance(address)
        if balance and balance > 0:
            balances.append(WalletBalance(
                address=address,
                chain="bitcoin",
                asset="BTC",
                balance=balance
            ))
        
        return balances


class SolanaWalletTracker:
    """Track Solana wallet balances."""
    
    # Common SPL tokens
    COMMON_TOKENS = {
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
        "mSOL": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
        "stSOL": "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",
        "JitoSOL": "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",
    }
    
    def __init__(self, rpc_url: str = None):
        """
        Initialize Solana tracker.
        
        Args:
            rpc_url: Solana RPC URL
        """
        self.rpc_url = rpc_url or os.getenv(
            "SOLANA_RPC_URL",
            "https://api.mainnet-beta.solana.com"
        )
    
    def _rpc_request(self, method: str, params: list) -> Optional[dict]:
        """Make RPC request to Solana."""
        try:
            response = requests.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params
                }
            )
            data = response.json()
            return data.get("result")
        except Exception as e:
            print(f"Solana RPC error: {e}")
            return None
    
    def get_sol_balance(self, address: str) -> Optional[float]:
        """Get native SOL balance."""
        result = self._rpc_request("getBalance", [address])
        if result:
            # Balance is in lamports (1 SOL = 1e9 lamports)
            return float(result["value"]) / 1e9
        return None
    
    def get_token_accounts(self, address: str) -> List[Dict]:
        """Get all SPL token accounts for a wallet."""
        result = self._rpc_request(
            "getTokenAccountsByOwner",
            [
                address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        )
        
        if result and "value" in result:
            return result["value"]
        return []
    
    def get_all_balances(self, address: str) -> List[WalletBalance]:
        """Get SOL and all token balances."""
        balances = []
        
        # Get SOL balance
        sol_balance = self.get_sol_balance(address)
        if sol_balance and sol_balance > 0:
            balances.append(WalletBalance(
                address=address,
                chain="solana",
                asset="SOL",
                balance=sol_balance
            ))
        
        # Get token accounts
        token_accounts = self.get_token_accounts(address)
        
        # Reverse lookup for token symbols
        mint_to_symbol = {v: k for k, v in self.COMMON_TOKENS.items()}
        
        for account in token_accounts:
            try:
                info = account["account"]["data"]["parsed"]["info"]
                mint = info["mint"]
                balance = float(info["tokenAmount"]["uiAmount"] or 0)
                
                if balance > 0:
                    symbol = mint_to_symbol.get(mint, mint[:8])
                    balances.append(WalletBalance(
                        address=address,
                        chain="solana",
                        asset=symbol,
                        balance=balance,
                        contract_address=mint
                    ))
            except (KeyError, TypeError):
                continue
        
        return balances


class OnChainWalletManager:
    """
    Manage multiple on-chain wallets across different chains.
    """
    
    CONFIG_FILE = "wallets.json"
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "data")
        
        self.config_dir = config_dir
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        
        self.config_path = os.path.join(config_dir, self.CONFIG_FILE)
        self.wallets = self._load_wallets()
        
        # Initialize chain trackers
        self.eth_tracker = EthereumWalletTracker()
        self.btc_tracker = BitcoinWalletTracker()
        self.sol_tracker = SolanaWalletTracker()
    
    def _load_wallets(self) -> Dict:
        """Load wallet configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {"ethereum": [], "bitcoin": [], "solana": []}
    
    def _save_wallets(self):
        """Save wallet configuration."""
        with open(self.config_path, 'w') as f:
            json.dump(self.wallets, f, indent=2)
    
    def add_wallet(self, chain: str, address: str, label: str = None):
        """Add a wallet to track."""
        chain = chain.lower()
        if chain not in self.wallets:
            self.wallets[chain] = []
        
        # Check for duplicates
        existing = [w for w in self.wallets[chain] if w["address"] == address]
        if existing:
            print(f"Wallet already tracked: {address}")
            return
        
        self.wallets[chain].append({
            "address": address,
            "label": label or f"{chain.title()} Wallet"
        })
        self._save_wallets()
        print(f"✓ Added {chain} wallet: {label or address}")
    
    def remove_wallet(self, chain: str, address: str):
        """Remove a wallet from tracking."""
        chain = chain.lower()
        if chain in self.wallets:
            self.wallets[chain] = [
                w for w in self.wallets[chain]
                if w["address"].lower() != address.lower()
            ]
            self._save_wallets()
            print(f"✓ Removed wallet: {address}")
    
    def list_wallets(self) -> Dict:
        """List all tracked wallets."""
        return self.wallets
    
    def get_all_balances(self) -> List[WalletBalance]:
        """Get balances for all tracked wallets."""
        all_balances = []
        
        # Ethereum wallets
        for wallet in self.wallets.get("ethereum", []):
            balances = self.eth_tracker.get_all_balances(wallet["address"])
            for b in balances:
                b.label = wallet.get("label")
            all_balances.extend(balances)
        
        # Bitcoin wallets
        for wallet in self.wallets.get("bitcoin", []):
            balances = self.btc_tracker.get_all_balances(wallet["address"])
            for b in balances:
                b.label = wallet.get("label")
            all_balances.extend(balances)
        
        # Solana wallets
        for wallet in self.wallets.get("solana", []):
            balances = self.sol_tracker.get_all_balances(wallet["address"])
            for b in balances:
                b.label = wallet.get("label")
            all_balances.extend(balances)
        
        return all_balances
    
    def get_aggregated_balances(self) -> Dict[str, Dict]:
        """Get aggregated balances by asset across all wallets."""
        balances = self.get_all_balances()
        
        aggregated = {}
        for b in balances:
            if b.asset not in aggregated:
                aggregated[b.asset] = {
                    "total_balance": 0,
                    "wallets": []
                }
            
            aggregated[b.asset]["total_balance"] += b.balance
            aggregated[b.asset]["wallets"].append({
                "address": b.address,
                "chain": b.chain,
                "balance": b.balance,
                "label": b.label
            })
        
        return aggregated
    
    def display_balances(self):
        """Display all wallet balances."""
        print("\n🔐 ON-CHAIN WALLET BALANCES")
        print("=" * 70)
        
        balances = self.get_all_balances()
        
        if not balances:
            print("No wallets configured or no balances found.")
            print("Add wallets with: python onchain_wallets.py add <chain> <address>")
            return
        
        # Group by chain
        by_chain = {}
        for b in balances:
            if b.chain not in by_chain:
                by_chain[b.chain] = []
            by_chain[b.chain].append(b)
        
        for chain, chain_balances in by_chain.items():
            print(f"\n📍 {chain.upper()}")
            print("-" * 50)
            
            for b in chain_balances:
                label = f" ({b.label})" if b.label else ""
                print(f"  {b.asset}: {b.balance:.8f}".rstrip('0').rstrip('.') + label)
        
        # Show aggregated totals
        print("\n" + "=" * 70)
        print("📊 AGGREGATED BY ASSET")
        print("-" * 50)
        
        aggregated = self.get_aggregated_balances()
        for asset, data in sorted(aggregated.items()):
            wallet_count = len(data["wallets"])
            plural = "s" if wallet_count > 1 else ""
            print(f"  {asset}: {data['total_balance']:.8f}".rstrip('0').rstrip('.') + 
                  f" ({wallet_count} wallet{plural})")


# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="On-Chain Wallet Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add wallet
    add_parser = subparsers.add_parser("add", help="Add a wallet to track")
    add_parser.add_argument("chain", choices=["ethereum", "bitcoin", "solana", "eth", "btc", "sol"])
    add_parser.add_argument("address", help="Wallet address")
    add_parser.add_argument("--label", "-l", help="Label for the wallet")
    
    # Remove wallet
    remove_parser = subparsers.add_parser("remove", help="Remove a wallet")
    remove_parser.add_argument("chain", choices=["ethereum", "bitcoin", "solana", "eth", "btc", "sol"])
    remove_parser.add_argument("address", help="Wallet address")
    
    # List wallets
    list_parser = subparsers.add_parser("list", help="List tracked wallets")
    
    # Show balances
    balances_parser = subparsers.add_parser("balances", help="Show all balances")
    
    # Check single address
    check_parser = subparsers.add_parser("check", help="Check balance of any address")
    check_parser.add_argument("chain", choices=["ethereum", "bitcoin", "solana", "eth", "btc", "sol"])
    check_parser.add_argument("address", help="Wallet address")
    
    args = parser.parse_args()
    
    # Normalize chain names
    chain_map = {"eth": "ethereum", "btc": "bitcoin", "sol": "solana"}
    
    manager = OnChainWalletManager()
    
    if args.command == "add":
        chain = chain_map.get(args.chain, args.chain)
        manager.add_wallet(chain, args.address, args.label)
    
    elif args.command == "remove":
        chain = chain_map.get(args.chain, args.chain)
        manager.remove_wallet(chain, args.address)
    
    elif args.command == "list":
        wallets = manager.list_wallets()
        print("\n📋 Tracked Wallets")
        print("=" * 60)
        
        for chain, addrs in wallets.items():
            if addrs:
                print(f"\n{chain.upper()}:")
                for w in addrs:
                    label = f" - {w['label']}" if w.get('label') else ""
                    print(f"  {w['address']}{label}")
    
    elif args.command == "balances":
        manager.display_balances()
    
    elif args.command == "check":
        chain = chain_map.get(args.chain, args.chain)
        print(f"\nChecking {chain} address: {args.address}")
        print("-" * 50)
        
        if chain == "ethereum":
            balances = manager.eth_tracker.get_all_balances(args.address)
        elif chain == "bitcoin":
            balances = manager.btc_tracker.get_all_balances(args.address)
        elif chain == "solana":
            balances = manager.sol_tracker.get_all_balances(args.address)
        else:
            balances = []
        
        if balances:
            for b in balances:
                print(f"  {b.asset}: {b.balance:.8f}".rstrip('0').rstrip('.'))
        else:
            print("  No balances found")
    
    else:
        # Default: show balances
        manager.display_balances()


if __name__ == "__main__":
    main()
