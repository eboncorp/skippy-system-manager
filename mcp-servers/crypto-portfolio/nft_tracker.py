"""
NFT Portfolio Tracker
Tracks NFT holdings across Ethereum, Polygon, and Solana.

Features:
- NFT enumeration by wallet
- Floor price tracking
- Collection stats
- Rarity estimation
- Portfolio valuation

Uses public APIs (OpenSea, Magic Eden, etc.)
"""

import os
import time
import json
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class NFT:
    """An NFT asset."""
    token_id: str
    contract_address: str
    collection_name: str
    name: str
    image_url: str
    chain: str
    standard: str  # ERC-721, ERC-1155, etc.
    attributes: List[dict] = None
    rarity_rank: Optional[int] = None
    rarity_score: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_currency: str = "ETH"


@dataclass
class NFTCollection:
    """NFT collection stats."""
    name: str
    slug: str
    contract_address: str
    chain: str
    floor_price: float
    floor_currency: str
    total_supply: int
    num_owners: int
    total_volume: float
    one_day_volume: float
    one_day_change: float
    seven_day_volume: float
    seven_day_change: float
    image_url: str = None


class OpenSeaClient:
    """Client for OpenSea API (Ethereum, Polygon, etc.)."""

    BASE_URL = "https://api.opensea.io/api/v2"

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENSEA_API_KEY")
        self.session = requests.Session()

        if self.api_key:
            self.session.headers["X-API-KEY"] = self.api_key

    def get_nfts_by_wallet(self, address: str, chain: str = "ethereum",
                          limit: int = 50) -> List[NFT]:
        """Get NFTs owned by a wallet address."""
        nfts = []

        try:
            response = self.session.get(
                f"{self.BASE_URL}/chain/{chain}/account/{address}/nfts",
                params={"limit": limit}
            )

            if response.status_code == 401:
                print("OpenSea API key required for this endpoint")
                return nfts

            response.raise_for_status()
            data = response.json()

            for nft_data in data.get("nfts", []):
                nfts.append(NFT(
                    token_id=nft_data.get("identifier", ""),
                    contract_address=nft_data.get("contract", ""),
                    collection_name=nft_data.get("collection", "Unknown"),
                    name=nft_data.get("name", f"#{nft_data.get('identifier')}"),
                    image_url=nft_data.get("image_url", ""),
                    chain=chain,
                    standard=nft_data.get("token_standard", "ERC-721"),
                    attributes=nft_data.get("traits", [])
                ))

        except Exception as e:
            print(f"OpenSea error: {e}")

        return nfts

    def get_collection_stats(self, collection_slug: str) -> Optional[NFTCollection]:
        """Get collection statistics."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/collections/{collection_slug}/stats"
            )
            response.raise_for_status()
            stats = response.json()

            # Get collection info
            info_response = self.session.get(
                f"{self.BASE_URL}/collections/{collection_slug}"
            )
            info = info_response.json() if info_response.ok else {}

            return NFTCollection(
                name=info.get("name", collection_slug),
                slug=collection_slug,
                contract_address=info.get("contracts", [{}])[0].get("address", ""),
                chain=info.get("contracts", [{}])[0].get("chain", "ethereum"),
                floor_price=float(stats.get("total", {}).get("floor_price", 0) or 0),
                floor_currency="ETH",
                total_supply=int(stats.get("total", {}).get("num_items", 0) or 0),
                num_owners=int(stats.get("total", {}).get("num_owners", 0) or 0),
                total_volume=float(stats.get("total", {}).get("volume", 0) or 0),
                one_day_volume=float(stats.get("intervals", [{}])[0].get("volume", 0) or 0),
                one_day_change=float(stats.get("intervals", [{}])[0].get("volume_change", 0) or 0),
                seven_day_volume=0,
                seven_day_change=0,
                image_url=info.get("image_url")
            )

        except Exception as e:
            print(f"OpenSea collection error: {e}")
            return None

    def get_floor_price(self, collection_slug: str) -> Optional[float]:
        """Get collection floor price."""
        stats = self.get_collection_stats(collection_slug)
        return stats.floor_price if stats else None


class MagicEdenClient:
    """Client for Magic Eden API (Solana NFTs)."""

    BASE_URL = "https://api-mainnet.magiceden.dev/v2"

    def __init__(self):
        self.session = requests.Session()

    def get_nfts_by_wallet(self, address: str, limit: int = 50) -> List[NFT]:
        """Get NFTs owned by a Solana wallet."""
        nfts = []

        try:
            response = self.session.get(
                f"{self.BASE_URL}/wallets/{address}/tokens",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            for nft_data in data:
                nfts.append(NFT(
                    token_id=nft_data.get("mintAddress", ""),
                    contract_address=nft_data.get("collection", ""),
                    collection_name=nft_data.get("collectionName", "Unknown"),
                    name=nft_data.get("name", "Unknown"),
                    image_url=nft_data.get("image", ""),
                    chain="solana",
                    standard="SPL",
                    attributes=nft_data.get("attributes", [])
                ))

        except Exception as e:
            print(f"Magic Eden error: {e}")

        return nfts

    def get_collection_stats(self, symbol: str) -> Optional[NFTCollection]:
        """Get Solana collection statistics."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/collections/{symbol}/stats"
            )
            response.raise_for_status()
            stats = response.json()

            return NFTCollection(
                name=stats.get("name", symbol),
                slug=symbol,
                contract_address="",
                chain="solana",
                floor_price=float(stats.get("floorPrice", 0) or 0) / 1e9,  # Lamports to SOL
                floor_currency="SOL",
                total_supply=int(stats.get("totalItems", 0) or 0),
                num_owners=int(stats.get("owners", 0) or 0),
                total_volume=float(stats.get("volumeAll", 0) or 0) / 1e9,
                one_day_volume=float(stats.get("volume24hr", 0) or 0) / 1e9,
                one_day_change=float(stats.get("volumeChange24hr", 0) or 0),
                seven_day_volume=float(stats.get("volume7d", 0) or 0) / 1e9,
                seven_day_change=float(stats.get("volumeChange7d", 0) or 0),
                image_url=stats.get("image")
            )

        except Exception as e:
            print(f"Magic Eden collection error: {e}")
            return None


class SimpleHashClient:
    """Client for SimpleHash API (multi-chain NFT data)."""

    BASE_URL = "https://api.simplehash.com/api/v0"

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("SIMPLEHASH_API_KEY")
        self.session = requests.Session()

        if self.api_key:
            self.session.headers["X-API-KEY"] = self.api_key

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_nfts_by_wallet(self, address: str, chains: List[str] = None) -> List[NFT]:
        """Get NFTs across multiple chains."""
        if not self.is_configured():
            print("SimpleHash API key not configured")
            return []

        if chains is None:
            chains = ["ethereum", "polygon", "solana"]

        nfts = []

        try:
            chain_str = ",".join(chains)
            response = self.session.get(
                f"{self.BASE_URL}/nfts/owners",
                params={
                    "chains": chain_str,
                    "wallet_addresses": address
                }
            )
            response.raise_for_status()
            data = response.json()

            for nft_data in data.get("nfts", []):
                nfts.append(NFT(
                    token_id=nft_data.get("token_id", ""),
                    contract_address=nft_data.get("contract_address", ""),
                    collection_name=nft_data.get("collection", {}).get("name", "Unknown"),
                    name=nft_data.get("name", "Unknown"),
                    image_url=nft_data.get("image_url", ""),
                    chain=nft_data.get("chain", ""),
                    standard=nft_data.get("contract", {}).get("type", ""),
                    attributes=nft_data.get("extra_metadata", {}).get("attributes", []),
                    rarity_rank=nft_data.get("rarity", {}).get("rank"),
                    rarity_score=nft_data.get("rarity", {}).get("score"),
                    last_sale_price=nft_data.get("last_sale", {}).get("unit_price"),
                    last_sale_currency=nft_data.get("last_sale", {}).get("payment_token", {}).get("symbol", "ETH")
                ))

        except Exception as e:
            print(f"SimpleHash error: {e}")

        return nfts


class NFTPortfolioTracker:
    """Unified NFT portfolio tracker."""

    def __init__(self):
        load_dotenv()
        self.opensea = OpenSeaClient()
        self.magiceden = MagicEdenClient()
        self.simplehash = SimpleHashClient()

        self.wallets: Dict[str, List[str]] = {}  # chain -> [addresses]
        self.collection_cache: Dict[str, NFTCollection] = {}

        # Price cache (would use actual price feeds in production)
        self.prices = {
            "ETH": 3500,
            "SOL": 200,
            "MATIC": 0.50,
            "WETH": 3500
        }

    def add_wallet(self, address: str, chain: str = "ethereum"):
        """Add wallet to track."""
        if chain not in self.wallets:
            self.wallets[chain] = []
        if address not in self.wallets[chain]:
            self.wallets[chain].append(address)

    def get_all_nfts(self) -> Dict[str, List[NFT]]:
        """Get all NFTs from tracked wallets."""
        all_nfts = {}

        for chain, addresses in self.wallets.items():
            all_nfts[chain] = []

            for address in addresses:
                print(f"  Fetching NFTs for {address[:10]}... on {chain}")

                # Try SimpleHash first (multi-chain)
                if self.simplehash.is_configured():
                    nfts = self.simplehash.get_nfts_by_wallet(address, [chain])
                    all_nfts[chain].extend(nfts)

                # Fallback to chain-specific APIs
                elif chain == "solana":
                    nfts = self.magiceden.get_nfts_by_wallet(address)
                    all_nfts[chain].extend(nfts)
                else:
                    nfts = self.opensea.get_nfts_by_wallet(address, chain)
                    all_nfts[chain].extend(nfts)

                time.sleep(0.5)  # Rate limiting

        return all_nfts

    def get_collection_floor(self, collection_slug: str, chain: str = "ethereum") -> Optional[float]:
        """Get floor price for a collection."""
        cache_key = f"{chain}:{collection_slug}"

        if cache_key in self.collection_cache:
            cached = self.collection_cache[cache_key]
            return cached.floor_price

        if chain == "solana":
            stats = self.magiceden.get_collection_stats(collection_slug)
        else:
            stats = self.opensea.get_collection_stats(collection_slug)

        if stats:
            self.collection_cache[cache_key] = stats
            return stats.floor_price

        return None

    def estimate_portfolio_value(self) -> dict:
        """Estimate total NFT portfolio value based on floor prices."""
        all_nfts = self.get_all_nfts()

        total_value_usd = 0
        by_collection = {}
        by_chain = {}

        for chain, nfts in all_nfts.items():
            if chain not in by_chain:
                by_chain[chain] = {"count": 0, "value_usd": 0}

            for nft in nfts:
                by_chain[chain]["count"] += 1

                # Get floor price for collection
                # Note: In production, you'd map collection_name to slug properly
                floor = self.get_collection_floor(
                    nft.collection_name.lower().replace(" ", "-"),
                    chain
                )

                if floor is None:
                    floor = 0

                # Convert to USD
                currency = "SOL" if chain == "solana" else "ETH"
                floor_usd = floor * self.prices.get(currency, 0)

                total_value_usd += floor_usd
                by_chain[chain]["value_usd"] += floor_usd

                # Track by collection
                if nft.collection_name not in by_collection:
                    by_collection[nft.collection_name] = {
                        "count": 0,
                        "floor_price": floor,
                        "currency": currency,
                        "value_usd": 0,
                        "chain": chain
                    }

                by_collection[nft.collection_name]["count"] += 1
                by_collection[nft.collection_name]["value_usd"] += floor_usd

        return {
            "total_nfts": sum(c["count"] for c in by_chain.values()),
            "total_value_usd": total_value_usd,
            "by_chain": by_chain,
            "by_collection": dict(sorted(
                by_collection.items(),
                key=lambda x: x[1]["value_usd"],
                reverse=True
            ))
        }

    def get_portfolio_summary(self) -> dict:
        """Get summary of NFT portfolio."""
        valuation = self.estimate_portfolio_value()

        # Top collections
        top_collections = list(valuation["by_collection"].items())[:5]

        return {
            "total_nfts": valuation["total_nfts"],
            "estimated_value_usd": valuation["total_value_usd"],
            "chains": valuation["by_chain"],
            "top_collections": [
                {
                    "name": name,
                    "count": data["count"],
                    "floor": f"{data['floor_price']:.4f} {data['currency']}",
                    "value_usd": data["value_usd"]
                }
                for name, data in top_collections
            ]
        }

    def save_wallets(self, filepath: str = None):
        """Save wallet configuration."""
        if filepath is None:
            filepath = os.path.expanduser("~/.crypto_portfolio/nft_wallets.json")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.wallets, f, indent=2)

    def load_wallets(self, filepath: str = None) -> bool:
        """Load wallet configuration."""
        if filepath is None:
            filepath = os.path.expanduser("~/.crypto_portfolio/nft_wallets.json")

        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "r") as f:
                self.wallets = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading NFT wallets: {e}")
            return False


def main():
    """CLI for NFT tracking."""
    import argparse
    from tabulate import tabulate

    parser = argparse.ArgumentParser(description="NFT Portfolio Tracker")
    parser.add_argument("--add-wallet", type=str, help="Add wallet address")
    parser.add_argument("--chain", type=str, default="ethereum",
                        help="Chain for wallet (ethereum, polygon, solana)")
    parser.add_argument("--list", action="store_true", help="List all NFTs")
    parser.add_argument("--value", action="store_true", help="Estimate portfolio value")
    parser.add_argument("--collection", type=str, help="Get collection stats")
    parser.add_argument("--floor", type=str, help="Get floor price for collection")

    args = parser.parse_args()

    tracker = NFTPortfolioTracker()
    tracker.load_wallets()

    if args.add_wallet:
        tracker.add_wallet(args.add_wallet, args.chain)
        tracker.save_wallets()
        print(f"✓ Added {args.add_wallet[:10]}... on {args.chain}")

    elif args.list:
        print("\n🖼️  NFT PORTFOLIO")
        print("=" * 60)

        if not tracker.wallets:
            print("No wallets configured. Use --add-wallet to add addresses.")
            return

        all_nfts = tracker.get_all_nfts()

        for chain, nfts in all_nfts.items():
            if nfts:
                print(f"\n{chain.upper()} ({len(nfts)} NFTs):")
                print("-" * 40)

                for nft in nfts[:20]:  # Show first 20
                    print(f"  • {nft.name}")
                    print(f"    Collection: {nft.collection_name}")
                    if nft.rarity_rank:
                        print(f"    Rarity: #{nft.rarity_rank}")

    elif args.value:
        print("\n💎 NFT PORTFOLIO VALUATION")
        print("=" * 60)

        if not tracker.wallets:
            print("No wallets configured.")
            return

        summary = tracker.get_portfolio_summary()

        print("\n📊 Summary:")
        print(f"  Total NFTs:      {summary['total_nfts']}")
        print(f"  Estimated Value: ${summary['estimated_value_usd']:,.2f}")

        if summary["top_collections"]:
            print("\n🏆 Top Collections:")
            table_data = []
            for col in summary["top_collections"]:
                table_data.append([
                    col["name"][:30],
                    col["count"],
                    col["floor"],
                    f"${col['value_usd']:,.2f}"
                ])

            print(tabulate(table_data,
                           headers=["Collection", "Count", "Floor", "Value"],
                           tablefmt="simple"))

    elif args.collection:
        print(f"\n📈 Collection Stats: {args.collection}")
        print("-" * 40)

        stats = tracker.opensea.get_collection_stats(args.collection)
        if stats:
            print(f"  Name:        {stats.name}")
            print(f"  Floor:       {stats.floor_price:.4f} {stats.floor_currency}")
            print(f"  Supply:      {stats.total_supply:,}")
            print(f"  Owners:      {stats.num_owners:,}")
            print(f"  Volume:      {stats.total_volume:,.2f} {stats.floor_currency}")
            print(f"  24h Volume:  {stats.one_day_volume:,.2f} {stats.floor_currency}")
        else:
            print("  Collection not found")

    elif args.floor:
        floor = tracker.get_collection_floor(args.floor, args.chain)
        currency = "SOL" if args.chain == "solana" else "ETH"
        if floor:
            print(f"\n{args.floor} floor: {floor:.4f} {currency}")
        else:
            print(f"\nCould not get floor for {args.floor}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
