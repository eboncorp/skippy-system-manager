"""
Multi-Exchange Portfolio Aggregator
Combines holdings from multiple exchanges into a unified view.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


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

    def __init__(self):
        self.exchanges = {}
        self._init_exchanges()

    def _init_exchanges(self):
        """Initialize exchange clients based on available credentials."""

        # Coinbase (Personal)
        coinbase_key = os.path.expanduser("~/.config/coinbase/cdp_api_key.json")
        if os.path.exists(coinbase_key):
            try:
                from coinbase_client import create_coinbase_client
                self.exchanges['coinbase'] = {
                    'name': 'Coinbase',
                    'client': create_coinbase_client(cdp_key_file=coinbase_key),
                    'enabled': True,
                }
            except Exception as e:
                logger.warning("Failed to init Coinbase: %s", e)

        # Coinbase GTI (Business)
        gti_key = os.path.expanduser("~/.config/coinbase/gti_cdp_api_key.json")
        if os.path.exists(gti_key):
            try:
                from coinbase_client import create_coinbase_client
                self.exchanges['coinbase_gti'] = {
                    'name': 'Coinbase GTI',
                    'client': create_coinbase_client(cdp_key_file=gti_key),
                    'enabled': True,
                }
            except Exception as e:
                logger.warning("Failed to init Coinbase GTI: %s", e)

        # Crypto.com Exchange
        crypto_com_key = os.path.expanduser("~/.config/crypto_com/api_key.json")
        if os.path.exists(crypto_com_key):
            try:
                from crypto_com_client import create_crypto_com_client
                self.exchanges['crypto_com'] = {
                    'name': 'Crypto.com Exchange',
                    'client': create_crypto_com_client(key_file=crypto_com_key),
                    'enabled': True,
                }
            except Exception as e:
                logger.warning("Failed to init Crypto.com: %s", e)

        # Kraken
        kraken_key = os.path.expanduser("~/.config/kraken/api_key.json")
        if os.path.exists(kraken_key):
            try:
                from kraken_client import create_kraken_client
                self.exchanges['kraken'] = {
                    'name': 'Kraken',
                    'client': create_kraken_client(key_file=kraken_key),
                    'enabled': True,
                }
            except Exception as e:
                logger.warning("Failed to init Kraken: %s", e)

    def get_exchange_summary(self, exchange_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio summary for a single exchange."""
        if exchange_id not in self.exchanges:
            return None

        exchange = self.exchanges[exchange_id]
        if not exchange['enabled']:
            return None

        try:
            summary = exchange['client'].get_portfolio_summary()
            summary['exchange'] = exchange['name']
            summary['exchange_id'] = exchange_id
            return summary
        except Exception as e:
            return {
                'exchange': exchange['name'],
                'exchange_id': exchange_id,
                'error': str(e),
                'total_value_usd': 0,
                'holdings': [],
            }

    def get_combined_portfolio(self) -> Dict[str, Any]:
        """Get combined portfolio across all exchanges."""
        combined = {
            'timestamp': datetime.now().isoformat(),
            'total_value_usd': 0,
            'total_staked_usd': 0,
            'exchanges': {},
            'all_holdings': [],
            'by_asset': {},
        }

        for exchange_id in self.exchanges:
            summary = self.get_exchange_summary(exchange_id)
            if summary:
                combined['exchanges'][exchange_id] = summary
                combined['total_value_usd'] += summary.get('total_value_usd', 0)
                combined['total_staked_usd'] += summary.get('total_staked_usd', 0)

                # Aggregate holdings by asset
                for holding in summary.get('holdings', []):
                    currency = holding.get('currency', 'UNKNOWN')
                    holding['exchange'] = summary.get('exchange', exchange_id)
                    combined['all_holdings'].append(holding)

                    # Aggregate by asset across exchanges
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
                        'exchange': summary.get('exchange'),
                        'balance': holding.get('balance', 0),
                        'value_usd': holding.get('value_usd', 0),
                    })

        # Sort holdings by value
        combined['all_holdings'].sort(key=lambda x: x.get('value_usd', 0), reverse=True)

        # Convert by_asset to sorted list
        combined['assets_summary'] = sorted(
            combined['by_asset'].values(),
            key=lambda x: x['total_value_usd'],
            reverse=True
        )

        return combined

    def print_summary(self):
        """Print a formatted portfolio summary."""
        portfolio = self.get_combined_portfolio()

        print("=" * 70)
        print("MULTI-EXCHANGE PORTFOLIO SUMMARY")
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

        print()
        print("Top 20 Holdings (All Exchanges):")
        print("-" * 70)
        for h in portfolio['all_holdings'][:20]:
            exchange = h.get('exchange', 'Unknown')[:10]
            currency = h.get('currency', 'UNK')
            balance = h.get('balance', 0)
            value = h.get('value_usd', 0)
            staked = " [STAKED]" if h.get('is_staked') else ""
            print(f"  {exchange:10} {currency:8} {balance:>14.4f}  ${value:>10,.2f}{staked}")

        print()
        print("Top 10 Assets (Aggregated):")
        print("-" * 70)
        for asset in portfolio['assets_summary'][:10]:
            currency = asset['currency']
            total_val = asset['total_value_usd']
            exchanges = ", ".join([e['exchange'][:8] for e in asset['exchanges']])
            print(f"  {currency:8} ${total_val:>12,.2f}  ({exchanges})")


def get_aggregated_portfolio() -> Dict[str, Any]:
    """Convenience function to get combined portfolio."""
    aggregator = PortfolioAggregator()
    return aggregator.get_combined_portfolio()


if __name__ == "__main__":
    aggregator = PortfolioAggregator()
    aggregator.print_summary()
