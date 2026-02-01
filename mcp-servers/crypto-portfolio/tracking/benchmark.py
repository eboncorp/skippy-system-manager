"""
Portfolio performance benchmarking.

Compares portfolio performance against:
- BTC (Bitcoin)
- ETH (Ethereum)
- SPY (S&P 500 via Yahoo Finance)
- Custom benchmarks
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
import aiohttp
import statistics

from data.storage import db
from data.prices import PriceService


@dataclass
class PerformanceMetrics:
    """Performance metrics for a period."""
    start_value: Decimal
    end_value: Decimal
    absolute_return: Decimal
    percentage_return: Decimal
    annualized_return: Decimal
    volatility: Optional[Decimal] = None  # Standard deviation of returns
    sharpe_ratio: Optional[Decimal] = None  # Risk-adjusted return
    max_drawdown: Optional[Decimal] = None  # Largest peak-to-trough decline

    @property
    def return_multiple(self) -> Decimal:
        """How many X the investment grew."""
        if self.start_value == 0:
            return Decimal("0")
        return self.end_value / self.start_value


@dataclass
class BenchmarkComparison:
    """Comparison of portfolio against a benchmark."""
    portfolio: PerformanceMetrics
    benchmark: PerformanceMetrics
    benchmark_name: str
    alpha: Decimal  # Excess return over benchmark
    beta: Optional[Decimal] = None  # Correlation with benchmark
    outperformed: bool = False


@dataclass
class FullBenchmarkReport:
    """Complete benchmark comparison report."""
    period_start: datetime
    period_end: datetime
    period_days: int
    portfolio_metrics: PerformanceMetrics
    comparisons: List[BenchmarkComparison]


class PerformanceAnalyzer:
    """Analyzes portfolio performance and compares to benchmarks."""

    COINGECKO_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, price_service: Optional[PriceService] = None):
        self.price_service = price_service or PriceService()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_historical_prices(
        self,
        asset_id: str,
        days: int,
    ) -> List[Tuple[datetime, Decimal]]:
        """Get historical prices from CoinGecko."""
        session = await self._get_session()

        url = f"{self.COINGECKO_URL}/coins/{asset_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
        }

        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                prices = []
                for timestamp_ms, price in data.get("prices", []):
                    dt = datetime.fromtimestamp(timestamp_ms / 1000)
                    prices.append((dt, Decimal(str(price))))

                return prices
        except Exception as e:
            print(f"Failed to get historical prices for {asset_id}: {e}")
            return []

    def calculate_metrics(
        self,
        values: List[Tuple[datetime, Decimal]],
    ) -> PerformanceMetrics:
        """Calculate performance metrics from a series of values."""
        if len(values) < 2:
            return PerformanceMetrics(
                start_value=Decimal("0"),
                end_value=Decimal("0"),
                absolute_return=Decimal("0"),
                percentage_return=Decimal("0"),
                annualized_return=Decimal("0"),
            )

        start_date, start_value = values[0]
        end_date, end_value = values[-1]

        # Basic returns
        absolute_return = end_value - start_value
        percentage_return = (absolute_return / start_value * 100) if start_value > 0 else Decimal("0")

        # Annualized return
        days = (end_date - start_date).days
        if days > 0 and start_value > 0:
            years = Decimal(str(days)) / Decimal("365")
            if end_value > 0:
                annualized_return = ((end_value / start_value) ** (1 / years) - 1) * 100
            else:
                annualized_return = Decimal("-100")
        else:
            annualized_return = Decimal("0")

        # Calculate daily returns for volatility
        daily_returns = []
        for i in range(1, len(values)):
            prev_value = values[i-1][1]
            curr_value = values[i][1]
            if prev_value > 0:
                daily_return = float((curr_value - prev_value) / prev_value)
                daily_returns.append(daily_return)

        # Volatility (annualized standard deviation)
        volatility = None
        if len(daily_returns) > 1:
            std_dev = statistics.stdev(daily_returns)
            volatility = Decimal(str(std_dev * (252 ** 0.5) * 100))  # Annualized

        # Sharpe ratio (assuming 5% risk-free rate)
        sharpe_ratio = None
        if volatility and volatility > 0:
            risk_free_rate = Decimal("5")  # 5% annual
            excess_return = annualized_return - risk_free_rate
            sharpe_ratio = excess_return / volatility

        # Maximum drawdown
        max_drawdown = None
        if len(values) > 1:
            peak = values[0][1]
            max_dd = Decimal("0")

            for _, value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else Decimal("0")
                if drawdown > max_dd:
                    max_dd = drawdown

            max_drawdown = max_dd * 100

        return PerformanceMetrics(
            start_value=start_value,
            end_value=end_value,
            absolute_return=absolute_return,
            percentage_return=percentage_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
        )

    def get_portfolio_values(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Tuple[datetime, Decimal]]:
        """Get historical portfolio values from database."""
        snapshots = db.get_snapshots(start_date=start_date, end_date=end_date, limit=1000)

        # Sort by timestamp
        snapshots.sort(key=lambda x: x["timestamp"])

        return [(s["timestamp"], s["total_usd_value"]) for s in snapshots]

    async def compare_to_benchmark(
        self,
        portfolio_values: List[Tuple[datetime, Decimal]],
        benchmark_id: str,
        benchmark_name: str,
    ) -> BenchmarkComparison:
        """Compare portfolio to a single benchmark."""
        if not portfolio_values:
            raise ValueError("No portfolio values provided")

        start_date = portfolio_values[0][0]
        days = (portfolio_values[-1][0] - start_date).days

        # Get benchmark prices
        benchmark_prices = await self.get_historical_prices(benchmark_id, days + 1)

        # Normalize benchmark to same starting value as portfolio
        if benchmark_prices:
            start_value = portfolio_values[0][1]
            benchmark_start = benchmark_prices[0][1]

            if benchmark_start > 0:
                scale = start_value / benchmark_start
                benchmark_values = [
                    (dt, price * scale) for dt, price in benchmark_prices
                ]
            else:
                benchmark_values = benchmark_prices
        else:
            benchmark_values = []

        # Calculate metrics
        portfolio_metrics = self.calculate_metrics(portfolio_values)
        benchmark_metrics = self.calculate_metrics(benchmark_values)

        # Calculate alpha (excess return)
        alpha = portfolio_metrics.percentage_return - benchmark_metrics.percentage_return

        return BenchmarkComparison(
            portfolio=portfolio_metrics,
            benchmark=benchmark_metrics,
            benchmark_name=benchmark_name,
            alpha=alpha,
            outperformed=alpha > 0,
        )

    async def generate_benchmark_report(
        self,
        days: int = 30,
        benchmarks: Optional[List[Tuple[str, str]]] = None,
    ) -> FullBenchmarkReport:
        """
        Generate a full benchmark comparison report.

        Args:
            days: Number of days to analyze
            benchmarks: List of (coingecko_id, display_name) tuples

        Returns:
            Complete benchmark report
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Default benchmarks
        if benchmarks is None:
            benchmarks = [
                ("bitcoin", "Bitcoin"),
                ("ethereum", "Ethereum"),
                ("solana", "Solana"),
            ]

        # Get portfolio values
        portfolio_values = self.get_portfolio_values(start_date, end_date)

        if not portfolio_values:
            raise ValueError("No portfolio data available for the specified period")

        # Calculate portfolio metrics
        portfolio_metrics = self.calculate_metrics(portfolio_values)

        # Compare to each benchmark
        comparisons = []
        for benchmark_id, benchmark_name in benchmarks:
            try:
                comparison = await self.compare_to_benchmark(
                    portfolio_values, benchmark_id, benchmark_name
                )
                comparisons.append(comparison)
            except Exception as e:
                print(f"Failed to compare to {benchmark_name}: {e}")

        return FullBenchmarkReport(
            period_start=start_date,
            period_end=end_date,
            period_days=days,
            portfolio_metrics=portfolio_metrics,
            comparisons=comparisons,
        )

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


def format_benchmark_report(report: FullBenchmarkReport) -> str:
    """Format benchmark report for display."""
    lines = []
    lines.append("=" * 70)
    lines.append("PORTFOLIO PERFORMANCE BENCHMARK REPORT")
    lines.append("=" * 70)
    lines.append(f"Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')} ({report.period_days} days)")
    lines.append("")

    # Portfolio metrics
    pm = report.portfolio_metrics
    lines.append("PORTFOLIO PERFORMANCE")
    lines.append("-" * 40)
    lines.append(f"  Starting Value:     ${float(pm.start_value):>12,.2f}")
    lines.append(f"  Ending Value:       ${float(pm.end_value):>12,.2f}")
    lines.append(f"  Absolute Return:    ${float(pm.absolute_return):>+12,.2f}")
    lines.append(f"  Percentage Return:  {float(pm.percentage_return):>+12.2f}%")
    lines.append(f"  Annualized Return:  {float(pm.annualized_return):>+12.2f}%")

    if pm.volatility is not None:
        lines.append(f"  Volatility (Ann.):  {float(pm.volatility):>12.2f}%")
    if pm.sharpe_ratio is not None:
        lines.append(f"  Sharpe Ratio:       {float(pm.sharpe_ratio):>12.2f}")
    if pm.max_drawdown is not None:
        lines.append(f"  Max Drawdown:       {float(pm.max_drawdown):>12.2f}%")

    lines.append("")

    # Benchmark comparisons
    lines.append("BENCHMARK COMPARISONS")
    lines.append("-" * 40)
    lines.append(f"{'Benchmark':<15} {'Return':>10} {'Alpha':>10} {'Result':>12}")
    lines.append("-" * 50)

    for comp in report.comparisons:
        result = "✅ Beat" if comp.outperformed else "❌ Lagged"
        lines.append(
            f"{comp.benchmark_name:<15} "
            f"{float(comp.benchmark.percentage_return):>+9.2f}% "
            f"{float(comp.alpha):>+9.2f}% "
            f"{result:>12}"
        )

    lines.append("")

    # Summary
    beat_count = sum(1 for c in report.comparisons if c.outperformed)
    total = len(report.comparisons)

    if beat_count == total:
        lines.append(f"🏆 Portfolio outperformed all {total} benchmarks!")
    elif beat_count > 0:
        lines.append(f"📊 Portfolio beat {beat_count}/{total} benchmarks")
    else:
        lines.append("📉 Portfolio underperformed all benchmarks")

    return "\n".join(lines)


# Convenience function
async def get_benchmark_report(days: int = 30) -> FullBenchmarkReport:
    """Quick function to get benchmark report."""
    analyzer = PerformanceAnalyzer()
    try:
        return await analyzer.generate_benchmark_report(days)
    finally:
        await analyzer.close()
