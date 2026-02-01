"""
DeBank API Client
=================

Client for DeBank Cloud API to fetch on-chain wallet data.
Supports portfolio balances, token holdings, and DeFi positions
across 80+ EVM chains.

API Docs: https://docs.cloud.debank.com/en/readme/api-pro-reference

Usage:
    client = DeBankClient(api_key="your_key")  # or use free tier
    balance = client.get_total_balance(wallet_address)
    tokens = client.get_token_list(wallet_address)
"""

import os
import time
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TokenBalance:
    """Token balance for a wallet."""
    chain: str
    symbol: str
    name: str
    amount: float
    price: float
    value_usd: float
    contract_address: Optional[str] = None
    logo_url: Optional[str] = None


@dataclass
class DeFiPosition:
    """DeFi protocol position."""
    chain: str
    protocol: str
    protocol_logo: str
    position_type: str  # lending, liquidity, staking, etc.
    assets: List[Dict]
    value_usd: float
    net_value_usd: float
    detail: Dict


@dataclass
class WalletSummary:
    """Complete wallet summary."""
    address: str
    total_usd: float
    chains: Dict[str, float]  # chain -> value
    token_count: int
    protocol_count: int


class DeBankClient:
    """Client for DeBank Cloud API."""

    # Free tier base URL (limited)
    FREE_BASE_URL = "https://api.debank.com"

    # Pro tier base URL
    PRO_BASE_URL = "https://pro-openapi.debank.com"

    # Supported chains
    CHAINS = [
        "eth", "bsc", "xdai", "matic", "ftm", "okt", "heco",
        "avax", "arb", "celo", "movr", "cro", "boba", "metis",
        "btt", "aurora", "mobm", "sbch", "fuse", "hmy", "palm",
        "astar", "sdn", "klay", "rsk", "iotx", "kcc", "wan",
        "op", "base", "linea", "zksync", "scroll", "mnt"
    ]

    def __init__(self, api_key: Optional[str] = None):
        """Initialize DeBank client.

        Args:
            api_key: DeBank Pro API key. If None, uses free tier (limited).
        """
        self.api_key = api_key or os.getenv("DEBANK_API_KEY")
        self.session = requests.Session()

        if self.api_key:
            self.base_url = self.PRO_BASE_URL
            self.session.headers["AccessKey"] = self.api_key
        else:
            self.base_url = self.FREE_BASE_URL

        self.session.headers["accept"] = "application/json"
        self._last_request = 0
        self._rate_limit = 0.5  # seconds between requests for free tier

    def _rate_limit_wait(self):
        """Respect rate limits."""
        elapsed = time.time() - self._last_request
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        self._last_request = time.time()

    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting."""
        self._rate_limit_wait()

        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"DeBank API error: {e}")
            return None

    def get_total_balance(self, address: str) -> Optional[float]:
        """Get total USD balance across all chains.

        Args:
            address: Wallet address (0x...)

        Returns:
            Total USD value or None on error
        """
        data = self._request("/v1/user/total_balance", {"id": address.lower()})
        if data:
            return data.get("total_usd_value", 0)
        return None

    def get_chain_balances(self, address: str) -> Dict[str, float]:
        """Get USD balance breakdown by chain.

        Args:
            address: Wallet address

        Returns:
            Dict of chain -> USD value
        """
        data = self._request("/v1/user/chain_balance", {"id": address.lower()})
        if data:
            return {item["id"]: item.get("usd_value", 0) for item in data}
        return {}

    def get_token_list(self, address: str, chain: str = None) -> List[TokenBalance]:
        """Get all token balances for a wallet.

        Args:
            address: Wallet address
            chain: Specific chain or None for all chains

        Returns:
            List of TokenBalance objects
        """
        params = {"id": address.lower()}
        if chain:
            params["chain_id"] = chain
            endpoint = "/v1/user/token_list"
        else:
            endpoint = "/v1/user/all_token_list"

        data = self._request(endpoint, params)
        if not data:
            return []

        tokens = []
        for item in data:
            tokens.append(TokenBalance(
                chain=item.get("chain", "eth"),
                symbol=item.get("symbol", "?"),
                name=item.get("name", "Unknown"),
                amount=item.get("amount", 0),
                price=item.get("price", 0),
                value_usd=item.get("amount", 0) * item.get("price", 0),
                contract_address=item.get("id"),
                logo_url=item.get("logo_url")
            ))

        # Sort by value
        tokens.sort(key=lambda x: x.value_usd, reverse=True)
        return tokens

    def get_protocol_list(self, address: str, chain: str = None) -> List[DeFiPosition]:
        """Get DeFi protocol positions for a wallet.

        Args:
            address: Wallet address
            chain: Specific chain or None for all chains

        Returns:
            List of DeFiPosition objects
        """
        params = {"id": address.lower()}
        if chain:
            params["chain_id"] = chain
            endpoint = "/v1/user/protocol_list"
        else:
            endpoint = "/v1/user/all_simple_protocol_list"

        data = self._request(endpoint, params)
        if not data:
            return []

        positions = []
        for protocol in data:
            for item in protocol.get("portfolio_item_list", []):
                positions.append(DeFiPosition(
                    chain=protocol.get("chain", "eth"),
                    protocol=protocol.get("name", "Unknown"),
                    protocol_logo=protocol.get("logo_url", ""),
                    position_type=item.get("name", "unknown"),
                    assets=item.get("asset_token_list", []),
                    value_usd=item.get("stats", {}).get("asset_usd_value", 0),
                    net_value_usd=item.get("stats", {}).get("net_usd_value", 0),
                    detail=item.get("detail", {})
                ))

        # Sort by value
        positions.sort(key=lambda x: x.value_usd, reverse=True)
        return positions

    def get_wallet_summary(self, address: str) -> Optional[WalletSummary]:
        """Get complete wallet summary.

        Args:
            address: Wallet address

        Returns:
            WalletSummary object or None on error
        """
        total = self.get_total_balance(address)
        if total is None:
            return None

        chains = self.get_chain_balances(address)
        tokens = self.get_token_list(address)
        protocols = self.get_protocol_list(address)

        return WalletSummary(
            address=address,
            total_usd=total,
            chains=chains,
            token_count=len(tokens),
            protocol_count=len(set(p.protocol for p in protocols))
        )

    def get_multi_wallet_summary(self, addresses: List[str]) -> Dict[str, WalletSummary]:
        """Get summaries for multiple wallets.

        Args:
            addresses: List of wallet addresses

        Returns:
            Dict of address -> WalletSummary
        """
        results = {}
        for addr in addresses:
            summary = self.get_wallet_summary(addr)
            if summary:
                results[addr] = summary
            time.sleep(0.5)  # Rate limiting
        return results


# Wallet label mapping (can be loaded from config)
WALLET_LABELS = {
    "0x19C3136369bb33cDFa409b3Adbf962BA97Ec1985": "gti-inc.eth",
    "0x34C761EDAfCBA14e7D921C3b1C38bD267498498d": "ebon.eth",
    "0x73732CC83a75FeC009D646A777993959d769E21f": "paperwerk.eth",
    "0xCA4cac9A3190aC5A863cb0E174d420E616Dd55Bc": "biggers.eth",
    "0x46A15b9002291d619D86164C6606185B6d6e27a0": "parkfield.eth",
    "0x9D552E0D404e20ef7480535CF42813ecFEdC0feF": "pennybrooke.eth",
    "0x8e7F9112D44e122b2Ae0f2f8c0A255dD60E78798": "ebon-link.eth",
    "0xd2Ef13A83bABb4776D85BBC136646071F2cFF5f7": "exodus-evm",
    "0x5a94861e9f99fC8749C9e55eC1BfA774a498E296": "crypto-defi-wallet",
}


def main():
    """CLI for DeBank wallet queries."""
    import argparse

    parser = argparse.ArgumentParser(description="DeBank Wallet Tracker")
    parser.add_argument("--address", "-a", type=str, help="Wallet address to query")
    parser.add_argument("--all", action="store_true", help="Query all configured wallets")
    parser.add_argument("--tokens", action="store_true", help="Show token list")
    parser.add_argument("--defi", action="store_true", help="Show DeFi positions")

    args = parser.parse_args()

    client = DeBankClient()

    if args.all:
        addresses = list(WALLET_LABELS.keys())
    elif args.address:
        addresses = [args.address]
    else:
        print("Specify --address or --all")
        return

    print("\n" + "=" * 60)
    print("  DeBank Wallet Summary")
    print("=" * 60 + "\n")

    total_value = 0
    for addr in addresses:
        label = WALLET_LABELS.get(addr, addr[:10] + "...")
        summary = client.get_wallet_summary(addr)

        if summary:
            total_value += summary.total_usd
            print(f"{label:20} ${summary.total_usd:>10,.2f}  ({summary.token_count} tokens)")

            if args.tokens:
                tokens = client.get_token_list(addr)
                for t in tokens[:10]:
                    print(f"  {t.symbol:10} {t.amount:>15,.4f}  ${t.value_usd:>10,.2f}")

            if args.defi:
                positions = client.get_protocol_list(addr)
                for p in positions[:5]:
                    print(f"  [{p.protocol}] {p.position_type}: ${p.value_usd:,.2f}")
        else:
            print(f"{label:20} Error fetching data")

        print()

    print("-" * 60)
    print(f"{'TOTAL':20} ${total_value:>10,.2f}")
    print()


if __name__ == "__main__":
    main()
