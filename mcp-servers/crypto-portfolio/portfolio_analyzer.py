#!/usr/bin/env python3
"""
Coinbase Portfolio Analyzer
Analyzes your Coinbase holdings and identifies underperforming assets.
"""

import os
import csv
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Coinbase SDK
from coinbase.rest import RESTClient


def get_client():
    """Initialize the Coinbase REST client with CDP API credentials."""
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "Missing API credentials. Please set COINBASE_API_KEY and "
            "COINBASE_API_SECRET in your .env file."
        )

    return RESTClient(api_key=api_key, api_secret=api_secret)


def get_accounts(client):
    """Fetch all accounts with non-zero balances."""
    accounts = []
    cursor = None

    while True:
        response = client.get_accounts(cursor=cursor, limit=250)

        for account in response.accounts:
            balance = Decimal(account.available_balance.value)
            if balance > 0:
                accounts.append({
                    "uuid": account.uuid,
                    "currency": account.currency,
                    "name": account.name,
                    "balance": balance,
                })

        if not response.has_next:
            break
        cursor = response.cursor

    return accounts


def get_current_prices(client, currencies):
    """Fetch current USD prices for a list of currencies."""
    prices = {}

    for currency in currencies:
        if currency == "USD":
            prices["USD"] = Decimal("1.0")
            continue

        product_id = f"{currency}-USD"
        try:
            product = client.get_product(product_id)
            prices[currency] = Decimal(product.price)
        except Exception:
            # Try USDC pair as fallback
            try:
                product_id = f"{currency}-USDC"
                product = client.get_product(product_id)
                prices[currency] = Decimal(product.price)
            except Exception:
                prices[currency] = None

    return prices


def get_transaction_history(client, account_id):
    """
    Fetch transaction history for cost basis calculation.
    Note: This uses the Coinbase API fills endpoint for trade history.
    """
    # For now, we'll skip cost basis - it requires more complex logic
    # with the fills endpoint and order history
    return []


def analyze_portfolio(client):
    """Main analysis function."""
    print("\n" + "=" * 60)
    print("COINBASE PORTFOLIO ANALYZER")
    print("=" * 60)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # Get accounts
    print("\nFetching accounts...")
    accounts = get_accounts(client)

    if not accounts:
        print("No accounts with balances found.")
        return

    print(f"Found {len(accounts)} accounts with balances")

    # Get current prices
    currencies = list(set(a["currency"] for a in accounts))
    print(f"\nFetching prices for {len(currencies)} currencies...")
    prices = get_current_prices(client, currencies)

    # Calculate portfolio values
    portfolio = []
    total_value = Decimal("0")

    for account in accounts:
        currency = account["currency"]
        balance = account["balance"]
        price = prices.get(currency)

        if price is not None:
            usd_value = balance * price
            total_value += usd_value
        else:
            usd_value = None

        portfolio.append({
            "currency": currency,
            "balance": balance,
            "price": price,
            "usd_value": usd_value,
        })

    # Sort by USD value (descending)
    portfolio.sort(key=lambda x: x["usd_value"] or Decimal("0"), reverse=True)

    # Display results
    print("\n" + "=" * 60)
    print("PORTFOLIO HOLDINGS")
    print("=" * 60)
    print(f"{'Asset':<10} {'Balance':>15} {'Price':>12} {'Value (USD)':>15} {'% of Port':>10}")
    print("-" * 60)

    for holding in portfolio:
        currency = holding["currency"]
        balance = holding["balance"]
        price = holding["price"]
        usd_value = holding["usd_value"]

        if usd_value is not None and total_value > 0:
            pct = (usd_value / total_value) * 100
            print(f"{currency:<10} {float(balance):>15.6f} ${float(price):>11.2f} ${float(usd_value):>14.2f} {float(pct):>9.1f}%")
        elif price is not None:
            print(f"{currency:<10} {float(balance):>15.6f} ${float(price):>11.2f} {'N/A':>15} {'N/A':>10}")
        else:
            print(f"{currency:<10} {float(balance):>15.6f} {'No price':>12} {'N/A':>15} {'N/A':>10}")

    print("-" * 60)
    print(f"{'TOTAL':<10} {'':<15} {'':<12} ${float(total_value):>14.2f} {'100.0%':>10}")

    # Identify potential issues
    print("\n" + "=" * 60)
    print("ANALYSIS NOTES")
    print("=" * 60)

    # Small holdings (dust)
    dust = [h for h in portfolio if h["usd_value"] and h["usd_value"] < Decimal("1")]
    if dust:
        print(f"\n⚠️  Dust positions (< $1): {', '.join(h['currency'] for h in dust)}")

    # No price data
    no_price = [h for h in portfolio if h["price"] is None]
    if no_price:
        print(f"\n⚠️  No price data available: {', '.join(h['currency'] for h in no_price)}")

    # Concentration warning
    if portfolio and portfolio[0]["usd_value"]:
        top_pct = (portfolio[0]["usd_value"] / total_value) * 100 if total_value > 0 else 0
        if top_pct > 50:
            print(f"\n⚠️  High concentration: {portfolio[0]['currency']} is {top_pct:.1f}% of portfolio")

    # Export to CSV
    export_to_csv(portfolio, total_value)

    return portfolio, total_value


def export_to_csv(portfolio, total_value):
    """Export portfolio to CSV file."""
    filename = "portfolio_report.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Currency", "Balance", "Price (USD)", "Value (USD)", "% of Portfolio"])

        for holding in portfolio:
            pct = ""
            if holding["usd_value"] and total_value > 0:
                pct = f"{(holding['usd_value'] / total_value) * 100:.2f}%"

            writer.writerow([
                holding["currency"],
                float(holding["balance"]),
                float(holding["price"]) if holding["price"] else "N/A",
                float(holding["usd_value"]) if holding["usd_value"] else "N/A",
                pct
            ])

        writer.writerow([])
        writer.writerow(["TOTAL", "", "", float(total_value), "100%"])

    print(f"\n✅ Report exported to {filename}")


def main():
    try:
        client = get_client()
        analyze_portfolio(client)

        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)
        print("""
To add more features, use Claude Code:

  claude "Add 24h price change for each asset"
  claude "Show which assets are down more than 10% from their all-time high"
  claude "Create a pie chart of my portfolio allocation"
  claude "Add historical performance tracking"
        """)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your API credentials in .env")
        print("  2. Ensure your API key has 'View' permissions")
        print("  3. Make sure you're using CDP keys (not legacy keys)")
        raise


if __name__ == "__main__":
    main()
