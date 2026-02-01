#!/usr/bin/env python3
"""
Crypto Portfolio CLI
====================

Command-line interface for the crypto portfolio analyzer.

Usage:
    crypto-portfolio --help
    crypto-portfolio portfolio summary
    crypto-portfolio holdings --exchange coinbase
    crypto-portfolio staking list
    crypto-portfolio dca create BTC 100 weekly
    crypto-portfolio tax export 2024

Install:
    pip install -e .
    # or
    python cli.py --help
"""

import asyncio
import json
import os
import sys
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto_portfolio_mcp import (
    PortfolioSummaryInput,
    ExchangeHoldingsInput,
    StakingPositionsInput,
    DeFiPositionsInput,
    AIAnalysisInput,
    CostBasisInput,
    ArbitrageOpportunitiesInput,
    TransactionHistoryInput,
    AlertsInput,
    DCABotStatusInput,
    ResponseFormat,
    Exchange,
    CostBasisMethod,
    DeFiProtocol,
    crypto_portfolio_summary,
    crypto_exchange_holdings,
    crypto_staking_positions,
    crypto_defi_positions,
    crypto_ai_analysis,
    crypto_cost_basis,
    crypto_arbitrage_opportunities,
    crypto_transaction_history,
    crypto_alerts_status,
    crypto_dca_bot_status,
)

# Initialize Typer app
app = typer.Typer(
    name="crypto-portfolio",
    help="Multi-exchange cryptocurrency portfolio analyzer CLI",
    add_completion=True,
)

console = Console()

# Sub-apps for organization
portfolio_app = typer.Typer(help="Portfolio commands")
holdings_app = typer.Typer(help="Holdings commands")
staking_app = typer.Typer(help="Staking commands")
defi_app = typer.Typer(help="DeFi commands")
dca_app = typer.Typer(help="DCA bot commands")
alerts_app = typer.Typer(help="Alert commands")
tax_app = typer.Typer(help="Tax commands")
analysis_app = typer.Typer(help="Analysis commands")

app.add_typer(portfolio_app, name="portfolio")
app.add_typer(holdings_app, name="holdings")
app.add_typer(staking_app, name="staking")
app.add_typer(defi_app, name="defi")
app.add_typer(dca_app, name="dca")
app.add_typer(alerts_app, name="alerts")
app.add_typer(tax_app, name="tax")
app.add_typer(analysis_app, name="analyze")


# =============================================================================
# HELPERS
# =============================================================================


def run_async(coro):
    """Run async coroutine."""
    return asyncio.run(coro)


def output_result(result: str, output_json: bool = False):
    """Output result in appropriate format."""
    if output_json:
        # Try to parse and pretty-print JSON
        try:
            data = json.loads(result)
            rprint(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            rprint(result)
    else:
        # Markdown output with rich formatting
        rprint(Panel(result, title="Result", border_style="blue"))


def show_spinner(message: str):
    """Create a spinner context manager."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


# =============================================================================
# PORTFOLIO COMMANDS
# =============================================================================


@portfolio_app.command("summary")
def portfolio_summary(
    include_staking: bool = typer.Option(True, "--staking/--no-staking", help="Include staking positions"),
    include_defi: bool = typer.Option(True, "--defi/--no-defi", help="Include DeFi positions"),
    include_nfts: bool = typer.Option(False, "--nfts/--no-nfts", help="Include NFT holdings"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Get portfolio summary across all exchanges."""
    with show_spinner("Fetching portfolio summary...") as progress:
        progress.add_task("Loading...", total=None)

        inp = PortfolioSummaryInput(
            include_staking=include_staking,
            include_defi=include_defi,
            include_nfts=include_nfts,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_portfolio_summary(inp))

    output_result(result, json_output)


@portfolio_app.command("history")
def portfolio_history(
    days: int = typer.Option(30, "--days", "-d", help="Number of days of history"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Get portfolio value history."""
    rprint(f"[yellow]Portfolio history for last {days} days[/yellow]")
    rprint("[dim]Feature coming soon...[/dim]")


# =============================================================================
# HOLDINGS COMMANDS
# =============================================================================


@holdings_app.command("list")
@app.command("holdings", hidden=True)  # Also available as top-level command
def list_holdings(
    exchange: str = typer.Option("all", "--exchange", "-e", help="Exchange to query"),
    asset: Optional[str] = typer.Option(None, "--asset", "-a", help="Filter by asset"),
    min_value: Optional[float] = typer.Option(None, "--min-value", help="Minimum USD value"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List holdings by exchange."""
    with show_spinner("Fetching holdings...") as progress:
        progress.add_task("Loading...", total=None)

        try:
            exchange_enum = Exchange(exchange.lower())
        except ValueError:
            exchange_enum = Exchange.ALL

        inp = ExchangeHoldingsInput(
            exchange=exchange_enum,
            asset=asset,
            min_value_usd=min_value,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_exchange_holdings(inp))

    output_result(result, json_output)


# =============================================================================
# STAKING COMMANDS
# =============================================================================


@staking_app.command("list")
def list_staking(
    exchange: str = typer.Option("all", "--exchange", "-e", help="Exchange to query"),
    include_rewards: bool = typer.Option(True, "--rewards/--no-rewards", help="Include rewards"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List staking positions."""
    with show_spinner("Fetching staking positions...") as progress:
        progress.add_task("Loading...", total=None)

        try:
            exchange_enum = Exchange(exchange.lower())
        except ValueError:
            exchange_enum = Exchange.ALL

        inp = StakingPositionsInput(
            exchange=exchange_enum,
            include_rewards=include_rewards,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_staking_positions(inp))

    output_result(result, json_output)


@staking_app.command("stake")
def stake_asset(
    asset: str = typer.Argument(..., help="Asset to stake (e.g., ETH)"),
    amount: float = typer.Argument(..., help="Amount to stake"),
    exchange: str = typer.Option("coinbase", "--exchange", "-e", help="Exchange"),
):
    """Stake an asset."""
    rprint(f"[yellow]Staking {amount} {asset} on {exchange}...[/yellow]")
    rprint("[dim]Feature requires trading permissions. Use --paper-trade for simulation.[/dim]")


@staking_app.command("unstake")
def unstake_asset(
    asset: str = typer.Argument(..., help="Asset to unstake"),
    amount: Optional[float] = typer.Argument(None, help="Amount (all if not specified)"),
    exchange: str = typer.Option("coinbase", "--exchange", "-e", help="Exchange"),
):
    """Unstake an asset."""
    amount_str = f"{amount}" if amount else "all"
    rprint(f"[yellow]Unstaking {amount_str} {asset} from {exchange}...[/yellow]")
    rprint("[dim]Feature requires trading permissions.[/dim]")


# =============================================================================
# DEFI COMMANDS
# =============================================================================


@defi_app.command("list")
def list_defi(
    protocol: str = typer.Option("all", "--protocol", "-p", help="Protocol to query"),
    wallet: Optional[str] = typer.Option(None, "--wallet", "-w", help="Wallet address"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List DeFi positions."""
    with show_spinner("Fetching DeFi positions...") as progress:
        progress.add_task("Loading...", total=None)

        try:
            protocol_enum = DeFiProtocol(protocol.lower())
        except ValueError:
            protocol_enum = DeFiProtocol.ALL

        inp = DeFiPositionsInput(
            protocol=protocol_enum,
            wallet_address=wallet,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_defi_positions(inp))

    output_result(result, json_output)


# =============================================================================
# DCA BOT COMMANDS
# =============================================================================


@dca_app.command("list")
def list_dca_bots(
    bot_id: Optional[str] = typer.Option(None, "--id", help="Specific bot ID"),
    include_history: bool = typer.Option(False, "--history", "-h", help="Include execution history"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List DCA bots."""
    with show_spinner("Fetching DCA bots...") as progress:
        progress.add_task("Loading...", total=None)

        inp = DCABotStatusInput(
            bot_id=bot_id,
            include_history=include_history,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_dca_bot_status(inp))

    output_result(result, json_output)


@dca_app.command("create")
def create_dca_bot(
    asset: str = typer.Argument(..., help="Asset to accumulate (e.g., BTC)"),
    amount: float = typer.Argument(..., help="USD amount per execution"),
    frequency: str = typer.Argument(..., help="Frequency: hourly, daily, weekly, biweekly, monthly"),
    exchange: str = typer.Option("coinbase", "--exchange", "-e", help="Exchange"),
    max_total: Optional[float] = typer.Option(None, "--max-total", help="Maximum total to invest"),
):
    """Create a new DCA bot."""
    rprint("[green]Creating DCA bot:[/green]")
    rprint(f"  Asset: {asset}")
    rprint(f"  Amount: ${amount}/execution")
    rprint(f"  Frequency: {frequency}")
    rprint(f"  Exchange: {exchange}")
    if max_total:
        rprint(f"  Max Total: ${max_total}")
    rprint("[dim]Feature requires trading permissions.[/dim]")


@dca_app.command("pause")
def pause_dca_bot(bot_id: str = typer.Argument(..., help="Bot ID to pause")):
    """Pause a DCA bot."""
    rprint(f"[yellow]Pausing bot {bot_id}...[/yellow]")


@dca_app.command("resume")
def resume_dca_bot(bot_id: str = typer.Argument(..., help="Bot ID to resume")):
    """Resume a paused DCA bot."""
    rprint(f"[green]Resuming bot {bot_id}...[/green]")


@dca_app.command("delete")
def delete_dca_bot(
    bot_id: str = typer.Argument(..., help="Bot ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a DCA bot."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete bot {bot_id}?")
        if not confirm:
            raise typer.Abort()
    rprint(f"[red]Deleting bot {bot_id}...[/red]")


# =============================================================================
# ALERTS COMMANDS
# =============================================================================


@alerts_app.command("list")
def list_alerts(
    action: str = typer.Option("list", "--action", "-a", help="Action: list, triggered, summary"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max alerts to show"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List alerts."""
    with show_spinner("Fetching alerts...") as progress:
        progress.add_task("Loading...", total=None)

        inp = AlertsInput(
            action=action,
            limit=limit,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_alerts_status(inp))

    output_result(result, json_output)


@alerts_app.command("create")
def create_alert(
    alert_type: str = typer.Argument(..., help="Type: price_above, price_below, percent_change, portfolio_value"),
    threshold: float = typer.Argument(..., help="Trigger threshold"),
    asset: Optional[str] = typer.Option(None, "--asset", "-a", help="Asset for price alerts"),
    channels: str = typer.Option("app", "--channels", "-c", help="Notification channels (comma-separated)"),
    note: Optional[str] = typer.Option(None, "--note", "-n", help="Alert note"),
):
    """Create an alert."""
    rprint("[green]Creating alert:[/green]")
    rprint(f"  Type: {alert_type}")
    rprint(f"  Threshold: {threshold}")
    if asset:
        rprint(f"  Asset: {asset}")
    rprint(f"  Channels: {channels}")


@alerts_app.command("delete")
def delete_alert(alert_id: str = typer.Argument(..., help="Alert ID to delete")):
    """Delete an alert."""
    rprint(f"[red]Deleting alert {alert_id}...[/red]")


# =============================================================================
# TAX COMMANDS
# =============================================================================


@tax_app.command("cost-basis")
def calculate_cost_basis(
    asset: Optional[str] = typer.Option(None, "--asset", "-a", help="Specific asset"),
    method: str = typer.Option("fifo", "--method", "-m", help="Method: fifo, lifo, hifo, avg"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Tax year"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Calculate cost basis for tax reporting."""
    with show_spinner("Calculating cost basis...") as progress:
        progress.add_task("Loading...", total=None)

        try:
            method_enum = CostBasisMethod(method.lower())
        except ValueError:
            method_enum = CostBasisMethod.FIFO

        inp = CostBasisInput(
            asset=asset,
            method=method_enum,
            tax_year=year,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_cost_basis(inp))

    output_result(result, json_output)


@tax_app.command("export")
def export_tax_report(
    year: int = typer.Argument(..., help="Tax year to export"),
    format: str = typer.Option("csv", "--format", "-f", help="Format: csv, pdf, turbotax, taxact"),
    method: str = typer.Option("fifo", "--method", "-m", help="Cost basis method"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export tax report."""
    rprint(f"[green]Exporting {year} tax report[/green]")
    rprint(f"  Format: {format}")
    rprint(f"  Method: {method}")
    rprint(f"  Output: {output_path or f'tax_report_{year}.{format}'}")
    rprint("[dim]Generating report...[/dim]")


# =============================================================================
# ANALYSIS COMMANDS
# =============================================================================


@analysis_app.command("run")
@app.command("analyze", hidden=True)  # Also available as top-level command
def run_analysis(
    analysis_type: str = typer.Option("comprehensive", "--type", "-t",
                                       help="Type: comprehensive, risk, performance, rebalancing, tax_optimization"),
    days: int = typer.Option(30, "--days", "-d", help="Days to analyze"),
    recommendations: bool = typer.Option(True, "--recommendations/--no-recommendations",
                                          help="Include recommendations"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Run AI-powered portfolio analysis."""
    with show_spinner(f"Running {analysis_type} analysis...") as progress:
        progress.add_task("Loading...", total=None)

        inp = AIAnalysisInput(
            analysis_type=analysis_type,
            time_range_days=days,
            include_recommendations=recommendations,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_ai_analysis(inp))

    output_result(result, json_output)


# =============================================================================
# ARBITRAGE COMMANDS
# =============================================================================


@app.command("arbitrage")
def scan_arbitrage(
    min_spread: float = typer.Option(0.5, "--min-spread", "-m", help="Minimum spread percentage"),
    assets: Optional[str] = typer.Option(None, "--assets", "-a", help="Assets to check (comma-separated)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Scan for arbitrage opportunities."""
    with show_spinner("Scanning for arbitrage opportunities...") as progress:
        progress.add_task("Loading...", total=None)

        asset_list = assets.split(",") if assets else None

        inp = ArbitrageOpportunitiesInput(
            min_spread_percent=min_spread,
            assets=asset_list,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_arbitrage_opportunities(inp))

    output_result(result, json_output)


# =============================================================================
# TRANSACTIONS COMMANDS
# =============================================================================


@app.command("transactions")
def list_transactions(
    exchange: str = typer.Option("all", "--exchange", "-e", help="Exchange filter"),
    asset: Optional[str] = typer.Option(None, "--asset", "-a", help="Asset filter"),
    tx_type: Optional[str] = typer.Option(None, "--type", "-t", help="Transaction type"),
    start_date: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max transactions"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List transaction history."""
    with show_spinner("Fetching transactions...") as progress:
        progress.add_task("Loading...", total=None)

        try:
            exchange_enum = Exchange(exchange.lower())
        except ValueError:
            exchange_enum = Exchange.ALL

        inp = TransactionHistoryInput(
            exchange=exchange_enum,
            asset=asset,
            tx_type=tx_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            response_format=ResponseFormat.JSON if json_output else ResponseFormat.MARKDOWN,
        )
        result = run_async(crypto_transaction_history(inp))

    output_result(result, json_output)


# =============================================================================
# CONFIG COMMANDS
# =============================================================================


@app.command("config")
def show_config():
    """Show current configuration."""
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Paper Trading", os.getenv("PAPER_TRADING", "true"))
    table.add_row("Database", os.getenv("DATABASE_URL", "sqlite:///portfolio.db"))
    table.add_row("Redis", os.getenv("REDIS_URL", "not configured"))

    # Check configured exchanges
    exchanges = []
    for ex in ["COINBASE", "KRAKEN", "CRYPTO_COM", "GEMINI"]:
        if os.getenv(f"{ex}_API_KEY"):
            exchanges.append(ex.lower())
    table.add_row("Exchanges", ", ".join(exchanges) if exchanges else "none")

    # Check wallets
    wallets = []
    for i in range(1, 6):
        if os.getenv(f"ETH_WALLET_{i}"):
            wallets.append(f"ETH_WALLET_{i}")
    table.add_row("Wallets", ", ".join(wallets) if wallets else "none")

    console.print(table)


# =============================================================================
# VERSION
# =============================================================================


@app.command("version")
def show_version():
    """Show version information."""
    rprint("[bold]Crypto Portfolio Analyzer[/bold]")
    rprint("Version: 1.0.0")
    rprint("Python: " + sys.version.split()[0])


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
