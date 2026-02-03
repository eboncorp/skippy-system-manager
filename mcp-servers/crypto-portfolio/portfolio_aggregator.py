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
        # Solana ecosystem
        "SOL": "solana", "JUP": "jupiter-exchange-solana", "BONK": "bonk",
        "ORCA": "orca", "HNT": "helium", "SBR": "saber",
        "HONEY": "hivemapper", "ACS": "access-protocol",
        # Cosmos ecosystem
        "JUNO": "juno-network", "TIA": "celestia", "KAVA": "kava",
        "SEI": "sei-network",
    }

    def __init__(self):
        self.exchanges = {}
        self.wallets: Dict[str, dict] = {}
        self.manual_holdings: dict = {}
        self._evm_tracker = None
        self._solana_tracker = None
        self._cosmos_tracker = None
        self._solana_wallets: Dict[str, dict] = {}
        self._cosmos_wallets: Dict[str, dict] = {}
        self._init_exchanges()
        self._init_wallets()
        self._init_manual_holdings()
        self._init_ccxt_clients()

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
        # EVM wallets from wallets.json
        wallets_path = os.path.expanduser("~/.crypto_portfolio/wallets.json")
        if os.path.exists(wallets_path):
            try:
                with open(wallets_path) as f:
                    self.wallets = json.load(f)
                from wallets.evm_wallet import EVMWalletTracker
                addresses = list(self.wallets.keys())
                alchemy_key = self._load_alchemy_key()
                self._evm_tracker = EVMWalletTracker(addresses, alchemy_api_key=alchemy_key)
                if alchemy_key:
                    logging.info("EVM wallet tracker initialized with Alchemy RPC")
                else:
                    logging.info("EVM wallet tracker initialized with public RPCs")
            except Exception as e:
                logging.warning(f"Failed to load EVM wallets: {e}")
                self.wallets = {}

        # Solana + Cosmos wallets from all_wallets_reference.json
        ref_path = os.path.expanduser("~/.crypto_portfolio/all_wallets_reference.json")
        if os.path.exists(ref_path):
            try:
                with open(ref_path) as f:
                    ref_data = json.load(f)

                # Solana
                solana_section = ref_data.get("solana", {})
                solana_addresses = [
                    addr for addr in solana_section
                    if not addr.startswith("_")
                ]
                if solana_addresses:
                    from wallets.solana_wallet import SolanaWalletTracker
                    self._solana_wallets = {
                        addr: solana_section[addr]
                        for addr in solana_addresses
                    }
                    self._solana_tracker = SolanaWalletTracker(solana_addresses)
                    logging.info(f"Solana wallet tracker initialized with {len(solana_addresses)} address(es)")

                # Cosmos
                cosmos_section = ref_data.get("cosmos", {})
                cosmos_addr_to_chain = {}
                cosmos_meta = {}
                for addr, info in cosmos_section.items():
                    if addr.startswith("_"):
                        continue
                    chain = info.get("chain", "")
                    if chain:
                        cosmos_addr_to_chain[addr] = chain
                        cosmos_meta[addr] = info
                if cosmos_addr_to_chain:
                    from wallets.cosmos_wallet import CosmosWalletTracker
                    self._cosmos_wallets = cosmos_meta
                    self._cosmos_tracker = CosmosWalletTracker(cosmos_addr_to_chain)
                    logging.info(f"Cosmos wallet tracker initialized with {len(cosmos_addr_to_chain)} address(es)")

            except Exception as e:
                logging.warning(f"Failed to load Solana/Cosmos wallets: {e}")

    @staticmethod
    def _load_alchemy_key() -> Optional[str]:
        """Load Alchemy API key from env var or config file."""
        key = os.environ.get("ALCHEMY_API_KEY")
        if key:
            return key
        key_path = os.path.expanduser("~/.config/alchemy/api_key.json")
        if os.path.exists(key_path):
            try:
                with open(key_path) as f:
                    data = json.load(f)
                return data.get("api_key") or data.get("key")
            except Exception:
                pass
        return None

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

    def _init_ccxt_clients(self):
        """Initialize CCXT-based exchange clients from CCXT_EXCHANGES env var.

        Reads CCXT_EXCHANGES (comma-separated exchange IDs) and creates
        CCXTClient instances for any that aren't already covered by native
        exchange clients.

        Environment:
            CCXT_EXCHANGES: e.g. "bitfinex,kucoin,bybit"
            {EXCHANGE}_API_KEY: API key per exchange
            {EXCHANGE}_API_SECRET: API secret per exchange
        """
        ccxt_exchanges_str = os.environ.get("CCXT_EXCHANGES", "").strip()
        if not ccxt_exchanges_str:
            return

        try:
            from exchanges.ccxt_fallback import create_ccxt_client, CCXT_AVAILABLE
        except ImportError:
            logging.info("CCXT not available, skipping CCXT exchange init")
            return

        if not CCXT_AVAILABLE:
            logging.info("ccxt package not installed, skipping CCXT exchanges")
            return

        # Native exchange names to skip (already have dedicated clients)
        native_names = {
            "coinbase", "coinbase_gti", "kraken_business", "kraken_personal",
            "crypto_com",
        }

        for exchange_id in ccxt_exchanges_str.split(","):
            exchange_id = exchange_id.strip().lower()
            if not exchange_id:
                continue

            # Skip if already covered by a native client
            if exchange_id in native_names or exchange_id in self.exchanges:
                logging.debug(f"Skipping CCXT {exchange_id}: native client exists")
                continue

            client = create_ccxt_client(exchange_id)
            if client:
                self.exchanges[f"ccxt_{exchange_id}"] = {
                    'name': f'CCXT {exchange_id.title()}',
                    'client': client,
                    'enabled': True,
                }
                logging.info(f"CCXT client initialized for {exchange_id}")

    async def get_wallet_summary(self, address: str, label: str,
                                 prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Get portfolio summary for a single on-chain wallet via direct RPC.

        Args:
            address: Wallet address (0x...)
            label: Human-readable wallet label
            prices: Pre-fetched price map (skips CoinGecko call if provided)

        Returns:
            Dict with source, label, total_value_usd, and holdings list
        """
        if not self._evm_tracker:
            return {'source': 'wallet', 'label': label, 'error': 'EVM tracker not initialized',
                    'total_value_usd': 0, 'holdings': []}
        try:
            wallet_summary = await self._evm_tracker.get_wallet_summary(address)

            # Get prices for the tokens we found (skip if pre-fetched)
            if prices is None:
                symbols = list(wallet_summary.total_by_symbol.keys())
                prices = await self._fetch_coingecko_prices(symbols) if symbols else {}

            holdings = []
            total_value = 0.0

            for bal in wallet_summary.balances:
                if bal.amount <= 0:
                    continue
                price = prices.get(bal.symbol, 0)
                value = float(bal.amount) * price

                holdings.append({
                    'currency': bal.symbol,
                    'balance': float(bal.amount),
                    'value_usd': value,
                    'chain': bal.chain,
                })
                total_value += value

            return {
                'source': 'wallet',
                'label': label,
                'address': address,
                'total_value_usd': total_value,
                'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
            }
        except Exception as e:
            logging.warning(f"Failed to fetch wallet {label} ({address[:10]}...): {e}")
            return {'source': 'wallet', 'label': label, 'address': address,
                    'error': str(e), 'total_value_usd': 0, 'holdings': []}

    async def _get_solana_wallet_summary(self, address: str, label: str,
                                         prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Get portfolio summary for a Solana wallet."""
        if not self._solana_tracker:
            return {'source': 'wallet-solana', 'label': label, 'error': 'Solana tracker not initialized',
                    'total_value_usd': 0, 'holdings': []}
        try:
            summary = await self._solana_tracker.get_wallet_summary(address)
            if prices is None:
                symbols = list(summary.total_by_symbol.keys())
                prices = await self._fetch_coingecko_prices(symbols) if symbols else {}

            holdings = []
            total_value = 0.0
            for bal in summary.balances:
                if bal.amount <= 0:
                    continue
                price = prices.get(bal.symbol, 0)
                value = float(bal.amount) * price
                holdings.append({
                    'currency': bal.symbol,
                    'balance': float(bal.amount),
                    'value_usd': value,
                    'chain': 'solana',
                })
                total_value += value

            return {
                'source': 'wallet-solana',
                'label': label,
                'address': address,
                'total_value_usd': total_value,
                'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
            }
        except Exception as e:
            logging.warning(f"Failed to fetch Solana wallet {label} ({address[:10]}...): {e}")
            return {'source': 'wallet-solana', 'label': label, 'address': address,
                    'error': str(e), 'total_value_usd': 0, 'holdings': []}

    async def _get_cosmos_wallet_summary(self, address: str, chain: str, label: str,
                                         prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Get portfolio summary for a Cosmos wallet."""
        if not self._cosmos_tracker:
            return {'source': 'wallet-cosmos', 'label': label, 'error': 'Cosmos tracker not initialized',
                    'total_value_usd': 0, 'holdings': []}
        try:
            summary = await self._cosmos_tracker.get_wallet_summary(address, chain)
            if prices is None:
                # Collect base symbols (strip -staked/-rewards suffixes for pricing)
                base_symbols = set()
                for sym in summary.total_by_symbol:
                    base = sym.split("-")[0]
                    base_symbols.add(base)
                prices = await self._fetch_coingecko_prices(list(base_symbols)) if base_symbols else {}

            holdings = []
            total_value = 0.0
            for bal in summary.balances:
                if bal.amount <= 0:
                    continue
                base_sym = bal.symbol.split("-")[0]
                price = prices.get(base_sym, 0)
                value = float(bal.amount) * price
                holdings.append({
                    'currency': bal.symbol,
                    'balance': float(bal.amount),
                    'value_usd': value,
                    'chain': chain,
                })
                total_value += value

            return {
                'source': 'wallet-cosmos',
                'label': label,
                'address': address,
                'total_value_usd': total_value,
                'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
            }
        except Exception as e:
            logging.warning(f"Failed to fetch Cosmos wallet {label} ({address[:12]}...): {e}")
            return {'source': 'wallet-cosmos', 'label': label, 'address': address,
                    'error': str(e), 'total_value_usd': 0, 'holdings': []}

    async def get_all_wallet_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries for all configured on-chain wallets (EVM, Solana, Cosmos).

        Fetches all wallet balances first, then makes a single batched price
        call to avoid CoinGecko rate limiting.

        Returns:
            Dict of label -> wallet summary
        """
        # Phase 1: Collect all raw balances (no price fetches)
        all_symbols: set = set()
        raw_wallets: list = []

        # EVM wallets
        for address, info in self.wallets.items():
            label = info.get('label', address[:10])
            if self._evm_tracker:
                try:
                    summary = await self._evm_tracker.get_wallet_summary(address)
                    symbols = list(summary.total_by_symbol.keys())
                    all_symbols.update(symbols)
                    raw_wallets.append(('evm', address, label, summary))
                except Exception as e:
                    logging.warning(f"Failed to fetch wallet {label} ({address[:10]}...): {e}")
                    raw_wallets.append(('evm', address, label, e))

        # Solana wallets
        for address, info in self._solana_wallets.items():
            label = info.get('label', address[:10])
            if self._solana_tracker:
                try:
                    summary = await self._solana_tracker.get_wallet_summary(address)
                    symbols = list(summary.total_by_symbol.keys())
                    all_symbols.update(symbols)
                    raw_wallets.append(('solana', address, label, summary))
                except Exception as e:
                    logging.warning(f"Failed to fetch Solana wallet {label} ({address[:10]}...): {e}")
                    raw_wallets.append(('solana', address, label, e))

        # Cosmos wallets
        for address, info in self._cosmos_wallets.items():
            label = info.get('label', address[:12])
            chain = info.get('chain', '')
            if self._cosmos_tracker:
                try:
                    summary = await self._cosmos_tracker.get_wallet_summary(address, chain)
                    for sym in summary.total_by_symbol:
                        all_symbols.add(sym.split("-")[0])
                    raw_wallets.append(('cosmos', address, label, summary, chain))
                except Exception as e:
                    logging.warning(f"Failed to fetch Cosmos wallet {label} ({address[:12]}...): {e}")
                    raw_wallets.append(('cosmos', address, label, e, chain))

        # Phase 2: Single batched price fetch for all symbols
        prices = await self._fetch_coingecko_prices(list(all_symbols)) if all_symbols else {}

        # Phase 3: Apply prices to all wallets
        results = {}
        for entry in raw_wallets:
            wallet_type = entry[0]
            address = entry[1]
            label = entry[2]
            data = entry[3]

            if isinstance(data, Exception):
                source = 'wallet' if wallet_type == 'evm' else f'wallet-{wallet_type}'
                results[label] = {'source': source, 'label': label, 'address': address,
                                  'error': str(data), 'total_value_usd': 0, 'holdings': []}
                continue

            if wallet_type == 'cosmos':
                chain = entry[4]
                results[label] = self._apply_prices_cosmos(data, prices, address, label, chain)
            elif wallet_type == 'solana':
                results[label] = self._apply_prices_solana(data, prices, address, label)
            else:
                results[label] = self._apply_prices_evm(data, prices, address, label)

        return results

    @staticmethod
    def _apply_prices_evm(summary, prices: Dict[str, float],
                          address: str, label: str) -> Dict[str, Any]:
        holdings = []
        total_value = 0.0
        for bal in summary.balances:
            if bal.amount <= 0:
                continue
            price = prices.get(bal.symbol, 0)
            value = float(bal.amount) * price
            holdings.append({
                'currency': bal.symbol, 'balance': float(bal.amount),
                'value_usd': value, 'chain': bal.chain,
            })
            total_value += value
        return {
            'source': 'wallet', 'label': label, 'address': address,
            'total_value_usd': total_value,
            'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
        }

    @staticmethod
    def _apply_prices_solana(summary, prices: Dict[str, float],
                             address: str, label: str) -> Dict[str, Any]:
        holdings = []
        total_value = 0.0
        for bal in summary.balances:
            if bal.amount <= 0:
                continue
            price = prices.get(bal.symbol, 0)
            value = float(bal.amount) * price
            holdings.append({
                'currency': bal.symbol, 'balance': float(bal.amount),
                'value_usd': value, 'chain': 'solana',
            })
            total_value += value
        return {
            'source': 'wallet-solana', 'label': label, 'address': address,
            'total_value_usd': total_value,
            'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
        }

    @staticmethod
    def _apply_prices_cosmos(summary, prices: Dict[str, float],
                             address: str, label: str, chain: str) -> Dict[str, Any]:
        holdings = []
        total_value = 0.0
        for bal in summary.balances:
            if bal.amount <= 0:
                continue
            base_sym = bal.symbol.split("-")[0]
            price = prices.get(base_sym, 0)
            value = float(bal.amount) * price
            holdings.append({
                'currency': bal.symbol, 'balance': float(bal.amount),
                'value_usd': value, 'chain': chain,
            })
            total_value += value
        return {
            'source': 'wallet-cosmos', 'label': label, 'address': address,
            'total_value_usd': total_value,
            'holdings': sorted(holdings, key=lambda x: x['value_usd'], reverse=True),
        }

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

        # --- 2. Fetch on-chain wallet summaries (EVM + Solana + Cosmos) ---
        has_wallets = (
            (self.wallets and self._evm_tracker)
            or self._solana_tracker
            or self._cosmos_tracker
        )
        if has_wallets:
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
