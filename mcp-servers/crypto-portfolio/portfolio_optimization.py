"""
Portfolio Optimization using Modern Portfolio Theory.

Implements:
- Mean-Variance Optimization (Markowitz)
- Efficient Frontier calculation
- Risk-adjusted return optimization (Sharpe ratio)
- Correlation matrix analysis
- Target allocation recommendations
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class AssetMetrics:
    """Historical metrics for an asset."""
    symbol: str
    expected_return: float  # Annualized return
    volatility: float  # Annualized standard deviation
    sharpe_ratio: float
    max_drawdown: float
    current_weight: float = 0.0

    @property
    def risk_adjusted_score(self) -> float:
        """Custom risk-adjusted score."""
        if self.volatility == 0:
            return 0
        return (self.expected_return / self.volatility) * (1 - self.max_drawdown)


@dataclass
class PortfolioAllocation:
    """Represents a portfolio allocation."""
    weights: Dict[str, float]  # Asset -> weight (0-1)
    expected_return: float
    volatility: float
    sharpe_ratio: float

    @property
    def is_valid(self) -> bool:
        """Check if weights sum to 1."""
        total = sum(self.weights.values())
        return abs(total - 1.0) < 0.001


@dataclass
class EfficientFrontierPoint:
    """A point on the efficient frontier."""
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: Dict[str, float]


@dataclass
class RebalanceRecommendation:
    """Recommendation for rebalancing."""
    asset: str
    current_weight: float
    target_weight: float
    action: str  # "BUY", "SELL", "HOLD"
    amount_usd: float
    priority: int  # 1 = highest


class CorrelationMatrix:
    """Handles correlation calculations between assets."""

    def __init__(self, returns_data: Dict[str, List[float]]):
        """
        Initialize with historical returns.

        Args:
            returns_data: Dict mapping asset symbol to list of daily returns
        """
        self.assets = list(returns_data.keys())
        self.returns = returns_data
        self._matrix: Optional[Dict[str, Dict[str, float]]] = None

    def calculate(self) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix."""
        if self._matrix is not None:
            return self._matrix

        n = len(self.assets)
        matrix = {a: {b: 0.0 for b in self.assets} for a in self.assets}

        for i, asset_a in enumerate(self.assets):
            for j, asset_b in enumerate(self.assets):
                if i == j:
                    matrix[asset_a][asset_b] = 1.0
                elif i < j:
                    corr = self._pearson_correlation(
                        self.returns[asset_a],
                        self.returns[asset_b]
                    )
                    matrix[asset_a][asset_b] = corr
                    matrix[asset_b][asset_a] = corr

        self._matrix = matrix
        return matrix

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation between two series."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0

        x = x[:n]
        y = y[:n]

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))

        var_x = sum((xi - mean_x) ** 2 for xi in x)
        var_y = sum((yi - mean_y) ** 2 for yi in y)

        denominator = math.sqrt(var_x * var_y)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def get_correlation(self, asset_a: str, asset_b: str) -> float:
        """Get correlation between two assets."""
        matrix = self.calculate()
        return matrix.get(asset_a, {}).get(asset_b, 0.0)

    def find_diversifiers(self, asset: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """
        Find assets with low correlation to the given asset.

        Args:
            asset: Asset to find diversifiers for
            threshold: Maximum correlation threshold

        Returns:
            List of (asset, correlation) tuples
        """
        matrix = self.calculate()

        if asset not in matrix:
            return []

        diversifiers = [
            (other, corr)
            for other, corr in matrix[asset].items()
            if other != asset and abs(corr) < threshold
        ]

        diversifiers.sort(key=lambda x: abs(x[1]))
        return diversifiers

    def to_dict(self) -> Dict:
        """Export matrix as dict for JSON serialization."""
        return self.calculate()


class PortfolioOptimizer:
    """
    Optimizes portfolio allocation using Modern Portfolio Theory.

    Supports:
    - Maximum Sharpe ratio optimization
    - Minimum volatility optimization
    - Target return optimization
    - Risk parity allocation
    """

    def __init__(
        self,
        risk_free_rate: float = 0.05,  # 5% default
        max_weight: float = 0.40,  # Max 40% in single asset
        min_weight: float = 0.02,  # Min 2% if included
    ):
        self.risk_free_rate = risk_free_rate
        self.max_weight = max_weight
        self.min_weight = min_weight

    def calculate_metrics(
        self,
        returns: List[float],
        trading_days: int = 365,  # Crypto trades 365 days
    ) -> Tuple[float, float]:
        """
        Calculate expected return and volatility from historical returns.

        Args:
            returns: List of daily returns (as decimals, e.g., 0.05 for 5%)
            trading_days: Trading days per year

        Returns:
            Tuple of (annualized_return, annualized_volatility)
        """
        if not returns:
            return 0.0, 0.0

        # Daily metrics
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        daily_vol = math.sqrt(variance)

        # Annualize
        annual_return = mean_return * trading_days
        annual_vol = daily_vol * math.sqrt(trading_days)

        return annual_return, annual_vol

    def calculate_portfolio_metrics(
        self,
        weights: Dict[str, float],
        asset_metrics: Dict[str, AssetMetrics],
        correlation_matrix: CorrelationMatrix,
    ) -> Tuple[float, float, float]:
        """
        Calculate portfolio expected return, volatility, and Sharpe ratio.

        Args:
            weights: Asset weights (must sum to 1)
            asset_metrics: Metrics for each asset
            correlation_matrix: Correlation between assets

        Returns:
            Tuple of (expected_return, volatility, sharpe_ratio)
        """
        # Portfolio return is weighted sum of individual returns
        portfolio_return = sum(
            weights.get(asset, 0) * metrics.expected_return
            for asset, metrics in asset_metrics.items()
        )

        # Portfolio variance considers correlations
        assets = list(weights.keys())
        portfolio_variance = 0.0

        for i, asset_i in enumerate(assets):
            for j, asset_j in enumerate(assets):
                w_i = weights.get(asset_i, 0)
                w_j = weights.get(asset_j, 0)
                vol_i = asset_metrics.get(asset_i, AssetMetrics(asset_i, 0, 0, 0, 0)).volatility
                vol_j = asset_metrics.get(asset_j, AssetMetrics(asset_j, 0, 0, 0, 0)).volatility
                corr = correlation_matrix.get_correlation(asset_i, asset_j)

                portfolio_variance += w_i * w_j * vol_i * vol_j * corr

        portfolio_vol = math.sqrt(max(0, portfolio_variance))

        # Sharpe ratio
        if portfolio_vol > 0:
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
        else:
            sharpe = 0.0

        return portfolio_return, portfolio_vol, sharpe

    def optimize_sharpe(
        self,
        asset_metrics: Dict[str, AssetMetrics],
        correlation_matrix: CorrelationMatrix,
        iterations: int = 10000,
    ) -> PortfolioAllocation:
        """
        Find allocation that maximizes Sharpe ratio.

        Uses Monte Carlo simulation to explore the solution space.

        Args:
            asset_metrics: Metrics for each asset
            correlation_matrix: Correlation matrix
            iterations: Number of random portfolios to generate

        Returns:
            Optimal PortfolioAllocation
        """
        import random

        assets = list(asset_metrics.keys())
        n_assets = len(assets)

        if n_assets == 0:
            return PortfolioAllocation({}, 0, 0, 0)

        best_sharpe = float("-inf")
        best_weights = {a: 1.0 / n_assets for a in assets}
        best_return = 0.0
        best_vol = 0.0

        for _ in range(iterations):
            # Generate random weights
            raw_weights = [random.random() for _ in range(n_assets)]
            total = sum(raw_weights)
            weights = {
                assets[i]: raw_weights[i] / total
                for i in range(n_assets)
            }

            # Apply constraints
            weights = self._apply_constraints(weights)

            # Calculate metrics
            ret, vol, sharpe = self.calculate_portfolio_metrics(
                weights, asset_metrics, correlation_matrix
            )

            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights
                best_return = ret
                best_vol = vol

        return PortfolioAllocation(
            weights=best_weights,
            expected_return=best_return,
            volatility=best_vol,
            sharpe_ratio=best_sharpe,
        )

    def optimize_min_volatility(
        self,
        asset_metrics: Dict[str, AssetMetrics],
        correlation_matrix: CorrelationMatrix,
        target_return: Optional[float] = None,
        iterations: int = 10000,
    ) -> PortfolioAllocation:
        """
        Find allocation that minimizes volatility.

        Args:
            asset_metrics: Metrics for each asset
            correlation_matrix: Correlation matrix
            target_return: Optional minimum return constraint
            iterations: Number of random portfolios to generate

        Returns:
            Optimal PortfolioAllocation
        """
        import random

        assets = list(asset_metrics.keys())
        n_assets = len(assets)

        if n_assets == 0:
            return PortfolioAllocation({}, 0, 0, 0)

        best_vol = float("inf")
        best_weights = {a: 1.0 / n_assets for a in assets}
        best_return = 0.0
        best_sharpe = 0.0

        for _ in range(iterations):
            # Generate random weights
            raw_weights = [random.random() for _ in range(n_assets)]
            total = sum(raw_weights)
            weights = {
                assets[i]: raw_weights[i] / total
                for i in range(n_assets)
            }

            # Apply constraints
            weights = self._apply_constraints(weights)

            # Calculate metrics
            ret, vol, sharpe = self.calculate_portfolio_metrics(
                weights, asset_metrics, correlation_matrix
            )

            # Check return constraint
            if target_return is not None and ret < target_return:
                continue

            if vol < best_vol:
                best_vol = vol
                best_weights = weights
                best_return = ret
                best_sharpe = sharpe

        return PortfolioAllocation(
            weights=best_weights,
            expected_return=best_return,
            volatility=best_vol,
            sharpe_ratio=best_sharpe,
        )

    def risk_parity(
        self,
        asset_metrics: Dict[str, AssetMetrics],
    ) -> PortfolioAllocation:
        """
        Calculate risk parity allocation.

        Each asset contributes equally to portfolio risk.

        Args:
            asset_metrics: Metrics for each asset

        Returns:
            Risk parity PortfolioAllocation
        """
        assets = list(asset_metrics.keys())

        if not assets:
            return PortfolioAllocation({}, 0, 0, 0)

        # Inverse volatility weighting (simplified risk parity)
        inv_vols = {}
        total_inv_vol = 0.0

        for asset, metrics in asset_metrics.items():
            if metrics.volatility > 0:
                inv_vol = 1.0 / metrics.volatility
            else:
                inv_vol = 1.0
            inv_vols[asset] = inv_vol
            total_inv_vol += inv_vol

        weights = {
            asset: inv_vol / total_inv_vol
            for asset, inv_vol in inv_vols.items()
        }

        # Apply constraints
        weights = self._apply_constraints(weights)

        # Calculate portfolio metrics (need correlation matrix for proper calc)
        # Simplified calculation without correlation
        portfolio_return = sum(
            weights[a] * asset_metrics[a].expected_return
            for a in assets
        )
        portfolio_vol = sum(
            weights[a] * asset_metrics[a].volatility
            for a in assets
        )

        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0

        return PortfolioAllocation(
            weights=weights,
            expected_return=portfolio_return,
            volatility=portfolio_vol,
            sharpe_ratio=sharpe,
        )

    def calculate_efficient_frontier(
        self,
        asset_metrics: Dict[str, AssetMetrics],
        correlation_matrix: CorrelationMatrix,
        points: int = 50,
    ) -> List[EfficientFrontierPoint]:
        """
        Calculate points along the efficient frontier.

        Args:
            asset_metrics: Metrics for each asset
            correlation_matrix: Correlation matrix
            points: Number of points to calculate

        Returns:
            List of EfficientFrontierPoint objects
        """
        # Find return range
        returns = [m.expected_return for m in asset_metrics.values()]
        min_return = min(returns) if returns else 0
        max_return = max(returns) if returns else 0

        frontier = []

        for i in range(points):
            target_return = min_return + (max_return - min_return) * (i / (points - 1))

            allocation = self.optimize_min_volatility(
                asset_metrics,
                correlation_matrix,
                target_return=target_return,
                iterations=5000,
            )

            if allocation.volatility < float("inf"):
                frontier.append(EfficientFrontierPoint(
                    expected_return=allocation.expected_return,
                    volatility=allocation.volatility,
                    sharpe_ratio=allocation.sharpe_ratio,
                    weights=allocation.weights,
                ))

        return frontier

    def _apply_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Apply min/max weight constraints."""
        # Remove assets below minimum
        weights = {
            asset: weight
            for asset, weight in weights.items()
            if weight >= self.min_weight
        }

        # Cap at maximum
        weights = {
            asset: min(weight, self.max_weight)
            for asset, weight in weights.items()
        }

        # Renormalize to sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {asset: weight / total for asset, weight in weights.items()}

        return weights

    def get_rebalance_recommendations(
        self,
        current_weights: Dict[str, float],
        target_allocation: PortfolioAllocation,
        portfolio_value: float,
        min_trade_usd: float = 50.0,
    ) -> List[RebalanceRecommendation]:
        """
        Generate rebalancing recommendations.

        Args:
            current_weights: Current portfolio weights
            target_allocation: Target allocation
            portfolio_value: Total portfolio value in USD
            min_trade_usd: Minimum trade size

        Returns:
            List of RebalanceRecommendation objects
        """
        recommendations = []

        all_assets = set(current_weights.keys()) | set(target_allocation.weights.keys())

        for asset in all_assets:
            current = current_weights.get(asset, 0)
            target = target_allocation.weights.get(asset, 0)
            diff = target - current
            amount_usd = abs(diff) * portfolio_value

            if amount_usd < min_trade_usd:
                continue

            if diff > 0.01:  # Buy if underweight by more than 1%
                action = "BUY"
                priority = 1 if diff > 0.05 else 2
            elif diff < -0.01:  # Sell if overweight by more than 1%
                action = "SELL"
                priority = 1 if diff < -0.05 else 2
            else:
                continue

            recommendations.append(RebalanceRecommendation(
                asset=asset,
                current_weight=current,
                target_weight=target,
                action=action,
                amount_usd=amount_usd,
                priority=priority,
            ))

        # Sort by priority then amount
        recommendations.sort(key=lambda x: (x.priority, -x.amount_usd))

        return recommendations


async def optimize_portfolio(
    portfolio_manager,  # Portfolio manager instance
    optimization_target: str = "sharpe",  # "sharpe", "min_vol", "risk_parity"
    lookback_days: int = 365,
) -> Dict:
    """
    Convenience function to optimize portfolio allocation.

    Args:
        portfolio_manager: Portfolio manager with historical data
        optimization_target: Optimization objective
        lookback_days: Days of historical data to use

    Returns:
        Dict with optimization results
    """
    # Get historical returns
    returns_data = await portfolio_manager.get_historical_returns(lookback_days)
    current_holdings = await portfolio_manager.get_holdings()

    # Calculate metrics for each asset
    optimizer = PortfolioOptimizer()
    asset_metrics = {}

    for asset, returns in returns_data.items():
        ann_return, ann_vol = optimizer.calculate_metrics(returns)
        sharpe = (ann_return - optimizer.risk_free_rate) / ann_vol if ann_vol > 0 else 0

        # Calculate max drawdown from returns
        cumulative = 1.0
        peak = 1.0
        max_dd = 0.0

        for r in returns:
            cumulative *= (1 + r)
            peak = max(peak, cumulative)
            dd = (peak - cumulative) / peak
            max_dd = max(max_dd, dd)

        current_weight = current_holdings.get(asset, {}).get("weight", 0)

        asset_metrics[asset] = AssetMetrics(
            symbol=asset,
            expected_return=ann_return,
            volatility=ann_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            current_weight=current_weight,
        )

    # Build correlation matrix
    correlation_matrix = CorrelationMatrix(returns_data)

    # Optimize based on target
    if optimization_target == "sharpe":
        optimal = optimizer.optimize_sharpe(asset_metrics, correlation_matrix)
    elif optimization_target == "min_vol":
        optimal = optimizer.optimize_min_volatility(asset_metrics, correlation_matrix)
    else:
        optimal = optimizer.risk_parity(asset_metrics)

    # Get efficient frontier
    frontier = optimizer.calculate_efficient_frontier(
        asset_metrics, correlation_matrix, points=20
    )

    # Get rebalance recommendations
    current_weights = {
        asset: metrics.current_weight
        for asset, metrics in asset_metrics.items()
    }
    portfolio_value = sum(
        h.get("value_usd", 0)
        for h in current_holdings.values()
    )

    recommendations = optimizer.get_rebalance_recommendations(
        current_weights, optimal, portfolio_value
    )

    return {
        "optimal_allocation": {
            "weights": optimal.weights,
            "expected_return": f"{optimal.expected_return:.2%}",
            "volatility": f"{optimal.volatility:.2%}",
            "sharpe_ratio": round(optimal.sharpe_ratio, 2),
        },
        "current_metrics": {
            asset: {
                "expected_return": f"{m.expected_return:.2%}",
                "volatility": f"{m.volatility:.2%}",
                "sharpe_ratio": round(m.sharpe_ratio, 2),
                "max_drawdown": f"{m.max_drawdown:.2%}",
                "current_weight": f"{m.current_weight:.2%}",
            }
            for asset, m in asset_metrics.items()
        },
        "correlation_matrix": correlation_matrix.to_dict(),
        "efficient_frontier": [
            {
                "return": f"{p.expected_return:.2%}",
                "volatility": f"{p.volatility:.2%}",
                "sharpe": round(p.sharpe_ratio, 2),
            }
            for p in frontier
        ],
        "rebalance_recommendations": [
            {
                "asset": r.asset,
                "action": r.action,
                "current_weight": f"{r.current_weight:.2%}",
                "target_weight": f"{r.target_weight:.2%}",
                "amount_usd": f"${r.amount_usd:,.2f}",
                "priority": r.priority,
            }
            for r in recommendations
        ],
        "diversification_opportunities": {
            asset: correlation_matrix.find_diversifiers(asset)[:3]
            for asset in list(asset_metrics.keys())[:5]
        },
    }
