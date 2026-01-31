"""
Multi-Exchange Portfolio Aggregator
Combines holdings from multiple exchanges into a unified view.
"""

import asyncio
import json
import logging
import os
from decimal import Decimal
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

import aiohttp


STABLECOIN_ASSETS = frozenset({
    'USD', 'EUR', 'GBP', 'USDC', 'USDT', 'DAI', 'BUSD',
    'GUSD', 'USDP', 'TUSD', 'PYUSD',
})


@dataclass
class ExchangeConfig:
    """Configuration for an exchange connection."""
    name: str
    enabled: bool = True
    key_file: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class PortfolioAggregator:
    """Aggregates portfolio data from multiple exchanges."""

    # CoinGecko symbol -> ID mapping for manual holdings price lookup
    SYMBOL_TO_COINGECKO = {
        "CRO": "crypto-com-chain", "XRP": "ripple", "DOGE": "dogecoin",
        "HBAR": "hedera-hashgraph", "ALGO": "algorand", "TRX": "tron",
        "FIL": "filecoin", "BTC": "bitcoin", "BCH": "bitcoin-cash",
        "LTC": "litecoin", "DGB": "digibyte", "BTT": "bittorrent",
        "ONDO": "ondo-finance", "BONE": "bone-shibaswap", "XNO": "nano",
        "CLOUD": "cloud", "MXC": "mxc", "XAI": "xai",
        "GUSD": "gemini-dollar",
    }

    def __init__(self):
        self.exchanges = {}
        self.wallets: Dict[str, dict] = {}
        self.manual_holdings: dict = {}
        self._debank = None
        self._init_exchanges()
        self._init_wallets()
        self._init_manual_holdings()

    def _init_exchanges(self):
        """Initialize exchange clients based on available credentials."""

        # Coinbase (Personal)
        coinbase_key = os.path.expanduser("~/.config/coinbase/cdp_api_key.json")
        if os.path.exists(coinbase_key):
            try:
                from exchanges import CoinbaseClient
                self.exchanges['coinbase'] = {
                    'name': 'Coinbase',
                    'client': CoinbaseClient.from_key_file(coinbase_key),
                    'enabled': True,
                }
            except Exception as e:
                print(f"Failed to init Coinbase: {e}")

        # Coinbase GTI (Business)
        gti_key = os.path.expanduser("~/.config/coinbase/gti_cdp_api_key.json")
        if os.path.exists(gti_key):
            try:
                from exchanges import CoinbaseClient
                self.exchanges['coinbase_gti'] = {
                    'name': 'Coinbase GTI',
                    'client': CoinbaseClient.from_key_file(gti_key),
                    'enabled': True,
                }
            except Exception as e:
                print(f"Failed to init Coinbase GTI: {e}")

        # Crypto.com Exchange
        crypto_com_key = os.path.expanduser("~/.config/crypto_com/api_key.json")
        if os.path.exists(crypto_com_key):
            try:
                from exchanges import CryptoComClient
                self.exchanges['crypto_com'] = {
                    'name': 'Crypto.com Exchange',
                    'client': CryptoComClient.from_env(),
                    'enabled': True,
                }
            except Exception as e:
                print(f"Failed to init Crypto.com: {e}")

        # Kraken Business
        kraken_biz_key = os.path.expanduser("~/.config/kraken/business_api_key.json")
        if os.path.exists(kraken_biz_key):
            try:
                from exchanges import KrakenClient
                self.exchanges['kraken_business'] = {
                    'name': 'Kraken (Business)',
                    'client': KrakenClient.from_key_file(kraken_biz_key),
                    'enabled': True,
                }
            except Exception as e:
                print(f"Failed to init Kraken Business: {e}")

        # Kraken Personal
        kraken_personal_key = os.path.expanduser("~/.config/kraken/personal_api_key.json")
        if os.path.exists(kraken_personal_key):
            try:
                from exchanges import KrakenClient
                self.exchanges['kraken_personal'] = {
                    'name': 'Kraken (Personal)',
                    'client': KrakenClient.from_key_file(kraken_personal_key),
                    'enabled': True,
                }
            except Exception as e:
                print(f"Failed to init Kraken Personal: {e}")

    def _init_wallets(self):
        """Load on-chain wallet addresses from config."""
        wallets_path = os.path.expanduser("~/.crypto_portfolio/wallets.json")
        if os.path.exists(wallets_path):
            try:
                with open(wallets_path) as f:
                    self.wallets = json.load(f)
                # Initialize DeBank client for on-chain queries
                from debank_client import DeBankClient
                self._debank = DeBankClient()
            except Exception as e:
                logging.warning(f"Failed to load wallets: {e}")
                self.wallets = {}

    def _init_manual_holdings(self):
        """Load manual holdings (non-API sources) from config."""
        manual_path = os.path.expanduser("~/.crypto_portfolio/manual_holdings.json")
        if os.path.exists(manual_path):
            try:
                with open(manual_path) as f:
                    self.manual_holdings = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load manual holdings: {e}")
                self.manual_holdings = {}

    async def get_wallet_summary(self, address: str, label: str) -> Dict[str, Any]:
        """Get portfolio summary for a single on-chain wallet via DeBank.

        Args:
            address: Wallet address (0x...)
            label: Human-readable wallet label

        Returns:
            Dict with source, label, total_value_usd, and holdings list
        """
        if not self._debank:
            return {'source': 'wallet', 'label': label, 'error': 'DeBank client not initialized',
                    'total_value_usd': 0, 'holdings': []}
        try:
            total = await asyncio.to_thread(self._debank.get_total_balance, address)
            tokens = await asyncio.to_thread(self._debank.get_token_list, address)

            holdings = []
            for t in tokens:
                if t.value_usd < 0.01:
                    continue
                holdings.append({
                    'currency': t.symbol,
                    'balance': t.amount,
                    'value_usd': t.value_usd,
                    'chain': t.chain,
                })

            return {
                'source': 'wallet',
                'label': label,
                'address': address,
                'total_value_usd': total if total is not None else 0,
                'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
            }
        except Exception as e:
            logging.warning(f"Failed to fetch wallet {label} ({address[:10]}...): {e}")
            return {'source': 'wallet', 'label': label, 'address': address,
                    'error': str(e), 'total_value_usd': 0, 'holdings': []}

    async def get_all_wallet_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries for all configured on-chain wallets.

        Runs sequentially to respect DeBank free-tier rate limits (0.5s between requests).

        Returns:
            Dict of label -> wallet summary
        """
        results = {}
        for address, info in self.wallets.items():
            label = info.get('label', address[:10])
            results[label] = await self.get_wallet_summary(address, label)
        return results

    async def _fetch_coingecko_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch current USD prices from CoinGecko for a list of symbols.

        Args:
            symbols: List of ticker symbols (e.g. ["CRO", "XRP", "DOGE"])

        Returns:
            Dict of symbol -> USD price
        """
        ids = []
        for s in symbols:
            cg_id = self.SYMBOL_TO_COINGECKO.get(s, s.lower())
            if cg_id not in ids:
                ids.append(cg_id)

        if not ids:
            return {}

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies=usd"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 429:
                        logging.warning("CoinGecko rate limit hit, using estimated values")
                        return {}
                    data = await resp.json()

            # Reverse map: coingecko_id -> symbol
            id_to_symbol = {v: k for k, v in self.SYMBOL_TO_COINGECKO.items()}
            return {
                id_to_symbol.get(cg_id, cg_id.upper()): info["usd"]
                for cg_id, info in data.items()
                if isinstance(info, dict) and "usd" in info
            }
        except Exception as e:
            logging.warning(f"CoinGecko price fetch failed: {e}")
            return {}

    async def get_manual_holdings_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get valued summaries for all manual holding sources.

        Fetches current prices from CoinGecko, falls back to estimated values
        from the config file if prices unavailable.

        Returns:
            Dict of source_id -> summary with holdings and totals
        """
        if not self.manual_holdings:
            return {}

        # Collect all unique symbols across all manual sources
        all_symbols = set()
        for source_data in self.manual_holdings.values():
            for symbol in source_data.get('holdings', {}).keys():
                all_symbols.add(symbol)

        # Fetch prices in one batch
        prices = await self._fetch_coingecko_prices(list(all_symbols))

        results = {}
        for source_id, source_data in self.manual_holdings.items():
            label = source_data.get('label', source_id)
            holdings_config = source_data.get('holdings', {})
            estimated_total = source_data.get('estimated_value_usd', 0)

            holdings = []
            total_value = 0.0

            for symbol, info in holdings_config.items():
                amount = info.get('amount', 0)
                price = prices.get(symbol, 0)
                value = amount * price

                holdings.append({
                    'currency': symbol,
                    'balance': amount,
                    'value_usd': value,
                    'price': price,
                    'price_source': 'coingecko' if price > 0 else 'unavailable',
                })
                total_value += value

            # If CoinGecko returned no prices, use the estimated total
            if total_value < 0.01 and estimated_total > 0:
                total_value = estimated_total

            results[source_id] = {
                'source': 'manual',
                'label': label,
                'total_value_usd': total_value,
                'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
                'last_updated': source_data.get('last_updated', 'unknown'),
            }

        return results

    async def get_exchange_summary(self, exchange_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio summary for a single exchange."""
        if exchange_id not in self.exchanges:
            return None

        exchange = self.exchanges[exchange_id]
        if not exchange['enabled'] or exchange['client'] is None:
            return None

        try:
            client = exchange['client']

            # Get balances via the async API
            balances = await client.get_balances()

            if not balances:
                return {
                    'exchange': exchange['name'],
                    'exchange_id': exchange_id,
                    'total_value_usd': 0,
                    'total_staked_usd': 0,
                    'holdings_count': 0,
                    'holdings': [],
                }

            # Get prices for non-stablecoin assets
            price_assets = [
                sym for sym in balances.keys()
                if sym not in STABLECOIN_ASSETS
            ]
            prices = await client.get_all_prices(price_assets) if price_assets else {}

            holdings = []
            total_value = 0.0
            total_staked = 0.0

            for symbol, balance in balances.items():
                if symbol in STABLECOIN_ASSETS:
                    price = Decimal('1')
                else:
                    price = prices.get(symbol, Decimal('0'))

                value = float(balance.total * price)
                staked_value = float(balance.staked * price)

                holdings.append({
                    'currency': symbol,
                    'balance': float(balance.total),
                    'available': float(balance.available),
                    'staked_amount': float(balance.staked),
                    'value_usd': value,
                    'is_staked': balance.staked > 0,
                })

                total_value += value
                total_staked += staked_value

            return {
                'exchange': exchange['name'],
                'exchange_id': exchange_id,
                'total_value_usd': total_value,
                'total_staked_usd': total_staked,
                'holdings_count': len(holdings),
                'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
            }

        except Exception as e:
            return {
                'exchange': exchange['name'],
                'exchange_id': exchange_id,
                'error': str(e),
                'total_value_usd': 0,
                'total_staked_usd': 0,
                'holdings': [],
            }

    async def get_combined_portfolio(self) -> Dict[str, Any]:
        """Get combined portfolio across all exchanges, wallets, and manual holdings."""
        combined = {
            'timestamp': datetime.now().isoformat(),
            'total_value_usd': 0,
            'total_staked_usd': 0,
            'exchanges': {},
            'wallets': {},
            'manual_sources': {},
            'wallets_total_usd': 0,
            'manual_total_usd': 0,
            'all_holdings': [],
            'by_asset': {},
        }

        def _merge_holding(holding: dict, source_name: str):
            """Merge a single holding into combined all_holdings and by_asset."""
            currency = holding.get('currency', 'UNKNOWN')
            holding['exchange'] = source_name
            combined['all_holdings'].append(holding)

            if currency not in combined['by_asset']:
                combined['by_asset'][currency] = {
                    'currency': currency,
                    'total_balance': 0,
                    'total_value_usd': 0,
                    'exchanges': [],
                }

            combined['by_asset'][currency]['total_balance'] += holding.get('balance', 0)
            combined['by_asset'][currency]['total_value_usd'] += holding.get('value_usd', 0)
            combined['by_asset'][currency]['exchanges'].append({
                'exchange': source_name,
                'balance': holding.get('balance', 0),
                'value_usd': holding.get('value_usd', 0),
            })

        # --- 1. Fetch exchange summaries concurrently ---
        exchange_ids = list(self.exchanges.keys())
        results = await asyncio.gather(
            *(self.get_exchange_summary(ex_id) for ex_id in exchange_ids),
            return_exceptions=True,
        )

        for exchange_id, result in zip(exchange_ids, results):
            if isinstance(result, Exception):
                continue
            summary = result
            if summary:
                combined['exchanges'][exchange_id] = summary
                combined['total_value_usd'] += summary.get('total_value_usd', 0)
                combined['total_staked_usd'] += summary.get('total_staked_usd', 0)

                for holding in summary.get('holdings', []):
                    _merge_holding(holding, summary.get('exchange', exchange_id))

        # --- 2. Fetch on-chain wallet summaries (sequential for rate limits) ---
        if self.wallets and self._debank:
            try:
                wallet_results = await self.get_all_wallet_summaries()
                combined['wallets'] = wallet_results
                for label, w_summary in wallet_results.items():
                    w_value = w_summary.get('total_value_usd', 0)
                    combined['wallets_total_usd'] += w_value
                    combined['total_value_usd'] += w_value
                    for holding in w_summary.get('holdings', []):
                        _merge_holding(holding, label)
            except Exception as e:
                logging.warning(f"Wallet fetch failed: {e}")

        # --- 3. Fetch manual holdings with CoinGecko prices ---
        if self.manual_holdings:
            try:
                manual_results = await self.get_manual_holdings_summary()
                combined['manual_sources'] = manual_results
                for source_id, m_summary in manual_results.items():
                    m_value = m_summary.get('total_value_usd', 0)
                    combined['manual_total_usd'] += m_value
                    combined['total_value_usd'] += m_value
                    for holding in m_summary.get('holdings', []):
                        _merge_holding(holding, m_summary.get('label', source_id))
            except Exception as e:
                logging.warning(f"Manual holdings fetch failed: {e}")

        # Sort holdings by value
        combined['all_holdings'].sort(key=lambda x: x.get('value_usd', 0), reverse=True)

        # Convert by_asset to sorted list
        combined['assets_summary'] = sorted(
            combined['by_asset'].values(),
            key=lambda x: x['total_value_usd'],
            reverse=True
        )

        return combined

    async def print_summary(self):
        """Print a formatted portfolio summary."""
        portfolio = await self.get_combined_portfolio()

        print("=" * 70)
        print("MULTI-SOURCE PORTFOLIO SUMMARY")
        print("=" * 70)
        print(f"Timestamp: {portfolio['timestamp']}")
        print(f"Total Value: ${portfolio['total_value_usd']:,.2f}")
        print(f"Total Staked: ${portfolio['total_staked_usd']:,.2f}")
        print()

        print("By Exchange:")
        print("-" * 70)
        for ex_id, ex_data in portfolio['exchanges'].items():
            value = ex_data.get('total_value_usd', 0)
            count = ex_data.get('holdings_count', len(ex_data.get('holdings', [])))
            staked = ex_data.get('total_staked_usd', 0)
            print(f"  {ex_data.get('exchange', ex_id):20} ${value:>12,.2f}  ({count} holdings, ${staked:,.2f} staked)")

        if portfolio.get('wallets'):
            print()
            print(f"By Wallet (${portfolio.get('wallets_total_usd', 0):,.2f} total):")
            print("-" * 70)
            for label, w_data in portfolio['wallets'].items():
                value = w_data.get('total_value_usd', 0)
                count = len(w_data.get('holdings', []))
                err = f"  [ERROR: {w_data['error']}]" if w_data.get('error') else ""
                print(f"  {label:20} ${value:>12,.2f}  ({count} tokens){err}")

        if portfolio.get('manual_sources'):
            print()
            print(f"Manual Holdings (${portfolio.get('manual_total_usd', 0):,.2f} total):")
            print("-" * 70)
            for src_id, m_data in portfolio['manual_sources'].items():
                label = m_data.get('label', src_id)
                value = m_data.get('total_value_usd', 0)
                count = len(m_data.get('holdings', []))
                print(f"  {label:20} ${value:>12,.2f}  ({count} assets)")

        print()
        print("Top 20 Holdings (All Sources):")
        print("-" * 70)
        for h in portfolio['all_holdings'][:20]:
            exchange = h.get('exchange', 'Unknown')[:12]
            currency = h.get('currency', 'UNK')
            balance = h.get('balance', 0)
            value = h.get('value_usd', 0)
            staked = " [STAKED]" if h.get('is_staked') else ""
            print(f"  {exchange:12} {currency:8} {balance:>14.4f}  ${value:>10,.2f}{staked}")

        print()
        print("Top 10 Assets (Aggregated):")
        print("-" * 70)
        for asset in portfolio['assets_summary'][:10]:
            currency = asset['currency']
            total_val = asset['total_value_usd']
            sources = ", ".join([e['exchange'][:10] for e in asset['exchanges']])
            print(f"  {currency:8} ${total_val:>12,.2f}  ({sources})")


async def get_aggregated_portfolio() -> Dict[str, Any]:
    """Convenience function to get combined portfolio."""
    aggregator = PortfolioAggregator()
    return await aggregator.get_combined_portfolio()


if __name__ == "__main__":
    async def main():
        aggregator = PortfolioAggregator()
        await aggregator.print_summary()

    asyncio.run(main())
