"""
Dashboard API routes for the Crypto Portfolio web dashboard.

Provides REST endpoints wired to real data from PortfolioAggregator,
TransactionHistory, CostBasisTracker, TaxLossHarvester, UnifiedSignalAnalyzer,
and GTIVirtualETF instances.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

# Signal analyzer (optional)
try:
    from agents.unified_analyzer import UnifiedSignalAnalyzer
    SIGNAL_ANALYZER_AVAILABLE = True
except ImportError:
    SIGNAL_ANALYZER_AVAILABLE = False

# Cost basis tracker (optional)
try:
    from cost_basis import CostBasisTracker
    COST_BASIS_AVAILABLE = True
except ImportError:
    COST_BASIS_AVAILABLE = False

# Tax loss harvester (optional)
try:
    from tax_loss_harvesting import TaxLossHarvester
    TLH_AVAILABLE = True
except ImportError:
    TLH_AVAILABLE = False

# ETF manager (optional)
try:
    from etf_manager import GTIVirtualETF
    ETF_AVAILABLE = True
except ImportError:
    ETF_AVAILABLE = False

# Snapshot cache for 24h change calculation
_snapshot_cache: list = []  # List of (timestamp, total_value) tuples
MAX_SNAPSHOTS = 1440  # 1 per minute, 24h


def _record_snapshot(total_value: float):
    """Record a portfolio value snapshot."""
    _snapshot_cache.append((datetime.now(), total_value))
    while len(_snapshot_cache) > MAX_SNAPSHOTS:
        _snapshot_cache.pop(0)


def _get_24h_change() -> tuple:
    """Get 24h change from snapshot cache. Returns (change_usd, change_pct)."""
    if len(_snapshot_cache) < 2:
        return 0.0, 0.0

    now = datetime.now()
    current_value = _snapshot_cache[-1][1]

    # Find snapshot closest to 24h ago
    target_time = now.timestamp() - 86400
    old_value = _snapshot_cache[0][1]
    for ts, val in _snapshot_cache:
        if ts.timestamp() >= target_time:
            old_value = val
            break

    change = current_value - old_value
    change_pct = (change / old_value * 100) if old_value > 0 else 0
    return change, change_pct


def create_api_router(
    portfolio_manager=None,
    transaction_history=None,
    etf_manager=None,
    notification_manager=None,
    cache_manager=None,
    metrics_collector=None,
    health_checker=None,
    job_scheduler=None,
) -> APIRouter:
    """Create the API router with real data and infrastructure endpoints."""
    router = APIRouter(prefix="/api")

    # ------------------------------------------------------------------
    # Portfolio
    # ------------------------------------------------------------------

    @router.get("/portfolio")
    async def get_portfolio():
        """Get current portfolio summary with real data."""
        if portfolio_manager is None:
            return _mock_portfolio()

        try:
            raw_data = await portfolio_manager.get_combined_portfolio()

            total_value = raw_data.get('total_value_usd', 0)
            _record_snapshot(total_value)
            change_24h, change_24h_pct = _get_24h_change()

            # Build holdings map by asset
            holdings = {}
            for asset, data in raw_data.get('by_asset', {}).items():
                bal = data.get('total_balance', 0)
                val = data.get('total_value_usd', 0)
                price = val / bal if bal > 0 else 0

                holdings[asset] = {
                    "amount": str(bal),
                    "price": str(round(price, 6)),
                    "current_value": str(round(val, 2)),
                    "cost_basis": "0",
                    "unrealized_pnl": "0",
                    "unrealized_pnl_pct": 0,
                    "exchanges": data.get('exchanges', []),
                }

            # Overlay cost basis data if available
            if COST_BASIS_AVAILABLE:
                try:
                    cbt = CostBasisTracker()
                    prices = {}
                    for asset, h in holdings.items():
                        prices[asset] = float(h['price'])
                    unrealized = cbt.get_unrealized_gains(prices)

                    for asset, gains in unrealized.items():
                        if asset.startswith('_'):
                            continue
                        if asset in holdings:
                            holdings[asset]['cost_basis'] = str(round(gains.get('cost_basis', 0), 2))
                            holdings[asset]['unrealized_pnl'] = str(round(gains.get('unrealized_gain', 0), 2))
                            holdings[asset]['unrealized_pnl_pct'] = round(gains.get('unrealized_percent', 0), 2)
                except Exception as e:
                    logger.warning(f"Cost basis overlay failed: {e}")

            total_cost = sum(float(h['cost_basis']) for h in holdings.values())
            total_unrealized = sum(float(h['unrealized_pnl']) for h in holdings.values())
            total_unrealized_pct = (total_unrealized / total_cost * 100) if total_cost > 0 else 0

            return {
                "total_value": str(round(total_value, 2)),
                "total_cost_basis": str(round(total_cost, 2)),
                "total_unrealized_pnl": str(round(total_unrealized, 2)),
                "total_unrealized_pnl_pct": round(total_unrealized_pct, 2),
                "total_realized_pnl_today": "0",
                "change_24h": str(round(change_24h, 2)),
                "change_24h_pct": round(change_24h_pct, 2),
                "holdings": holdings,
                "exchanges": {
                    eid: {
                        "name": edata.get('exchange', eid),
                        "total_value_usd": edata.get('total_value_usd', 0),
                        "holdings_count": edata.get('holdings_count', 0),
                    }
                    for eid, edata in raw_data.get('exchanges', {}).items()
                },
                "timestamp": raw_data.get('timestamp', datetime.now().isoformat()),
            }
        except Exception as e:
            logger.error(f"Portfolio fetch error: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch portfolio data.")

    # ------------------------------------------------------------------
    # Holdings
    # ------------------------------------------------------------------

    @router.get("/holdings")
    async def get_holdings():
        """Get detailed holdings with cost basis overlay."""
        return await get_portfolio()

    @router.get("/holdings/{exchange}")
    async def get_exchange_holdings(exchange: str):
        """Get holdings for a specific exchange."""
        if portfolio_manager is None:
            raise HTTPException(status_code=503, detail="Portfolio manager not available.")

        try:
            summary = await portfolio_manager.get_exchange_summary(exchange)
            if summary is None:
                raise HTTPException(status_code=404, detail=f"Exchange '{exchange}' not found.")
            return summary
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Exchange holdings error: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch exchange data.")

    # ------------------------------------------------------------------
    # Signal Analysis
    # ------------------------------------------------------------------

    @router.get("/signals/{asset}")
    async def get_signals(asset: str = "BTC"):
        """Get signal analysis for an asset."""
        if not SIGNAL_ANALYZER_AVAILABLE:
            return {"error": "Signal analyzer not available", "available": False}

        try:
            analyzer = UnifiedSignalAnalyzer()
            result = await analyzer.analyze(asset.upper())
            await analyzer.close()

            categories = {}
            for cat_name, signals in result.categories.items():
                cat_signals = []
                for sig in signals:
                    cat_signals.append({
                        "name": sig.name,
                        "score": sig.score,
                        "confidence": sig.confidence,
                        "description": sig.description,
                    })
                avg_score = sum(s['score'] for s in cat_signals) / len(cat_signals) if cat_signals else 0
                categories[cat_name] = {
                    "signals": cat_signals,
                    "average_score": round(avg_score, 1),
                    "count": len(cat_signals),
                }

            return {
                "asset": asset.upper(),
                "composite_score": result.composite_score,
                "confidence": result.confidence,
                "recommendation": {
                    "action": result.primary_recommendation.action,
                    "dca_multiplier": result.primary_recommendation.dca_multiplier,
                    "reasoning": result.primary_recommendation.reasoning,
                },
                "categories": categories,
                "signal_count": len(result.all_signals),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Signal analysis error: {e}")
            raise HTTPException(status_code=500, detail="Failed to run signal analysis.")

    # ------------------------------------------------------------------
    # Tax
    # ------------------------------------------------------------------

    @router.get("/tax/summary")
    async def get_tax_summary(year: Optional[int] = None):
        """Get tax summary for a year."""
        if year is None:
            year = datetime.now().year

        if transaction_history is None:
            return _mock_tax_summary(year)

        try:
            return transaction_history.get_tax_summary(year)
        except Exception as e:
            logger.error(f"Tax summary error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get tax summary.")

    @router.get("/tax/lots")
    async def get_tax_lots():
        """Get unrealized tax lot positions."""
        if not COST_BASIS_AVAILABLE:
            return {"lots": [], "available": False}

        try:
            cbt = CostBasisTracker()
            prices = {}
            if portfolio_manager:
                try:
                    raw = await portfolio_manager.get_combined_portfolio()
                    for asset, data in raw.get('by_asset', {}).items():
                        bal = data.get('total_balance', 0)
                        if bal > 0:
                            prices[asset] = data.get('total_value_usd', 0) / bal
                except Exception:
                    pass

            unrealized = cbt.get_unrealized_gains(prices)
            lots = []
            for asset, data in unrealized.items():
                if asset.startswith('_'):
                    continue
                lots.append({
                    "asset": asset,
                    "quantity": data.get('quantity', 0),
                    "cost_basis": data.get('cost_basis', 0),
                    "average_cost": data.get('average_cost', 0),
                    "current_price": data.get('current_price', 0),
                    "current_value": data.get('current_value', 0),
                    "unrealized_gain": data.get('unrealized_gain', 0),
                    "unrealized_percent": data.get('unrealized_percent', 0),
                })

            total = unrealized.get('_total', {})
            return {
                "lots": lots,
                "total_cost_basis": total.get('total_cost_basis', 0),
                "total_current_value": total.get('total_current_value', 0),
                "total_unrealized_gain": total.get('total_unrealized_gain', 0),
                "total_unrealized_percent": total.get('total_unrealized_percent', 0),
            }
        except Exception as e:
            logger.error(f"Tax lots error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get tax lots.")

    @router.get("/tax/tlh")
    async def get_tlh_opportunities():
        """Get tax loss harvesting opportunities."""
        if not TLH_AVAILABLE:
            return {"opportunities": [], "available": False}
        return {"opportunities": [], "note": "Connect cost basis data for TLH analysis"}

    @router.get("/tax/opportunities")
    async def get_tax_opportunities():
        """Legacy endpoint - redirects to tax/summary."""
        summary = await get_tax_summary()
        return {
            "ytd_realized_gains": str(summary.get("total_net", 0)),
            "harvestable_losses": "0",
            "estimated_tax_savings": "0",
            "opportunities": [],
        }

    # ------------------------------------------------------------------
    # Transaction History
    # ------------------------------------------------------------------

    @router.get("/history")
    async def get_history(
        exchange: Optional[str] = None,
        asset: Optional[str] = None,
        tx_type: Optional[str] = None,
        limit: int = Query(default=50, le=200),
        offset: int = Query(default=0, ge=0),
    ):
        """Get paginated transaction history."""
        if transaction_history is None or not transaction_history.transactions:
            return {"transactions": [], "total": 0, "limit": limit, "offset": offset}

        try:
            filtered = list(transaction_history.transactions)

            if exchange:
                filtered = [t for t in filtered if t.exchange.lower() == exchange.lower()]
            if asset:
                filtered = [t for t in filtered if t.asset.upper() == asset.upper()]
            if tx_type:
                filtered = [t for t in filtered if t.tx_type == tx_type]

            filtered.sort(key=lambda t: t.timestamp, reverse=True)

            total = len(filtered)
            page = filtered[offset:offset + limit]

            transactions = []
            for tx in page:
                transactions.append({
                    "id": getattr(tx, 'id', ''),
                    "timestamp": tx.timestamp.isoformat() if hasattr(tx.timestamp, 'isoformat') else str(tx.timestamp),
                    "exchange": tx.exchange,
                    "asset": tx.asset,
                    "tx_type": tx.tx_type,
                    "amount": tx.amount,
                    "price_usd": getattr(tx, 'price_usd', 0),
                    "total_usd": getattr(tx, 'total_usd', 0),
                    "fee_usd": getattr(tx, 'fee_usd', 0),
                })

            return {
                "transactions": transactions,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"History error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get transaction history.")

    # ------------------------------------------------------------------
    # ETF Manager
    # ------------------------------------------------------------------

    @router.get("/etf/status")
    async def get_etf_status():
        """Get ETF allocation status."""
        if not ETF_AVAILABLE:
            return {"available": False, "error": "ETF manager not available"}

        if etf_manager is None:
            return {"available": False, "error": "ETF manager not initialized"}

        try:
            holdings = {}
            prices = {}
            if portfolio_manager:
                from decimal import Decimal
                raw = await portfolio_manager.get_combined_portfolio()
                for asset, data in raw.get('by_asset', {}).items():
                    bal = data.get('total_balance', 0)
                    holdings[asset] = Decimal(str(bal))
                    if bal > 0:
                        price = Decimal(str(data.get('total_value_usd', 0))) / Decimal(str(bal))
                        prices[asset] = price

            status = etf_manager.get_etf_status(holdings, prices)

            allocations = []
            for alloc in status.allocations:
                allocations.append({
                    "symbol": alloc.symbol,
                    "category": alloc.category.value if hasattr(alloc.category, 'value') else str(alloc.category),
                    "target_pct": float(alloc.target_pct),
                    "current_pct": float(alloc.current_pct),
                    "drift_pct": float(alloc.drift_pct),
                    "current_value_usd": float(alloc.current_value_usd),
                    "is_locked": alloc.is_locked,
                })

            return {
                "available": True,
                "nav_usd": float(status.nav_usd),
                "assets_count": status.assets_count,
                "fear_greed": status.fear_greed,
                "war_chest_rule": status.war_chest_rule,
                "war_chest_usd": float(status.war_chest_usd),
                "war_chest_pct": float(status.war_chest_pct),
                "categories": {
                    k: {key: str(v) if key != 'assets' else v for key, v in cat.items()}
                    for k, cat in status.categories.items()
                },
                "allocations": allocations,
                "timestamp": status.timestamp,
            }
        except Exception as e:
            logger.error(f"ETF status error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get ETF status.")

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    @router.get("/alerts")
    async def get_alerts():
        """Get configured alerts."""
        return {
            "active_count": 0,
            "triggered_today": 0,
            "alerts": [],
        }

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    @router.get("/analysis")
    async def get_analysis():
        """Get portfolio analysis metrics."""
        if portfolio_manager is None:
            return _mock_analysis()

        try:
            raw = await portfolio_manager.get_combined_portfolio()
            total_value = raw.get('total_value_usd', 0)
            by_asset = raw.get('by_asset', {})

            max_pct = 0
            if total_value > 0:
                for data in by_asset.values():
                    pct = data.get('total_value_usd', 0) / total_value * 100
                    max_pct = max(max_pct, pct)

            n_assets = len(by_asset)
            diversification = min(100, n_assets * 10) if n_assets > 0 else 0
            conc_score = max(0, 30 - max_pct * 0.3) if max_pct > 0 else 30
            health = int(diversification * 0.4 + conc_score + min(30, n_assets * 3))

            recommendations = []
            if max_pct > 50:
                recommendations.append(f"High concentration: largest holding is {max_pct:.1f}% of portfolio")
            if n_assets < 5:
                recommendations.append("Consider diversifying - fewer than 5 assets held")
            if n_assets >= 5:
                recommendations.append(f"Holding {n_assets} assets - reasonable diversification")

            return {
                "health_score": health,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "volatility": 0,
                "concentration_pct": round(max_pct, 1),
                "asset_count": n_assets,
                "recommendations": recommendations,
            }
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return _mock_analysis()

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    @router.get("/portfolio/snapshots")
    async def get_snapshots():
        """Get portfolio value snapshots for sparkline chart."""
        return {
            "snapshots": [
                {"timestamp": ts.isoformat(), "value": val}
                for ts, val in _snapshot_cache
            ],
            "count": len(_snapshot_cache),
        }

    # ------------------------------------------------------------------
    # Infrastructure: Health
    # ------------------------------------------------------------------

    @router.get("/health")
    async def get_health():
        """Get system health check status."""
        if health_checker is None:
            return {
                "status": "unknown",
                "message": "Health checker not initialized",
                "checks": {},
            }

        try:
            results = await health_checker.check_all()
            overall = all(r.healthy for r in results)
            return {
                "status": "healthy" if overall else "unhealthy",
                "checks": {
                    r.name: {
                        "healthy": r.healthy,
                        "message": r.message,
                        "latency_ms": round(r.latency_ms, 1),
                    }
                    for r in results
                },
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"status": "error", "message": str(e), "checks": {}}

    # ------------------------------------------------------------------
    # Infrastructure: Metrics
    # ------------------------------------------------------------------

    @router.get("/metrics")
    async def get_metrics():
        """Get application metrics as JSON."""
        if metrics_collector is None:
            return {"error": "Metrics collector not initialized"}
        return metrics_collector.export_json()

    @router.get("/metrics/prometheus")
    async def get_prometheus_metrics():
        """Get metrics in Prometheus text format."""
        from fastapi.responses import PlainTextResponse

        if metrics_collector is None:
            return PlainTextResponse("# Metrics collector not initialized\n")
        return PlainTextResponse(
            metrics_collector.export_prometheus(),
            media_type="text/plain",
        )

    # ------------------------------------------------------------------
    # Infrastructure: Cache Stats
    # ------------------------------------------------------------------

    @router.get("/cache/stats")
    async def get_cache_stats():
        """Get cache backend statistics."""
        if cache_manager is None:
            return {"backend": "none", "connected": False}

        try:
            stats = await cache_manager.get_stats()
            return stats
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"backend": "error", "error": str(e)}

    # ------------------------------------------------------------------
    # Infrastructure: Job Status
    # ------------------------------------------------------------------

    @router.get("/jobs/status")
    async def get_jobs_status():
        """Get background job scheduler status."""
        if job_scheduler is None:
            return {"running": False, "message": "Scheduler not initialized", "jobs": {}}

        try:
            return job_scheduler.get_status()
        except Exception as e:
            logger.error(f"Jobs status error: {e}")
            return {"running": False, "error": str(e), "jobs": {}}

    # ------------------------------------------------------------------
    # Infrastructure: Notifications
    # ------------------------------------------------------------------

    @router.get("/notifications/channels")
    async def get_notification_channels():
        """Get configured notification channels."""
        if notification_manager is None:
            return {"channels": [], "message": "Notifications not initialized"}

        configured = notification_manager.get_configured_channels()
        all_channels = list(notification_manager.notifiers.keys())
        return {
            "configured": configured,
            "available": all_channels,
            "unconfigured": [c for c in all_channels if c not in configured],
        }

    @router.post("/notifications/test")
    async def send_test_notification():
        """Send a test notification to the 'app' channel."""
        if notification_manager is None:
            raise HTTPException(status_code=503, detail="Notifications not initialized")

        results = await notification_manager.send(
            channels=["app"],
            title="Test Notification",
            message="This is a test from the crypto portfolio dashboard.",
            priority="normal",
        )
        return {
            "results": [
                {"channel": r.channel, "success": r.success, "error": r.error}
                for r in results
            ]
        }

    return router


# ------------------------------------------------------------------
# Mock data fallbacks
# ------------------------------------------------------------------


def _mock_portfolio():
    """Return mock portfolio data when no real data source."""
    return {
        "total_value": "127834.56",
        "total_cost_basis": "100000.00",
        "total_unrealized_pnl": "27834.56",
        "total_unrealized_pnl_pct": 27.83,
        "total_realized_pnl_today": "0",
        "change_24h": "0",
        "change_24h_pct": 0,
        "holdings": {
            "BTC": {
                "amount": "1.5",
                "price": "45000.00",
                "current_value": "67500.00",
                "cost_basis": "50000.00",
                "unrealized_pnl": "17500.00",
                "unrealized_pnl_pct": 35.0,
            },
            "ETH": {
                "amount": "20.0",
                "price": "2500.00",
                "current_value": "50000.00",
                "cost_basis": "40000.00",
                "unrealized_pnl": "10000.00",
                "unrealized_pnl_pct": 25.0,
            },
            "SOL": {
                "amount": "100.0",
                "price": "103.35",
                "current_value": "10334.56",
                "cost_basis": "10000.00",
                "unrealized_pnl": "334.56",
                "unrealized_pnl_pct": 3.35,
            },
        },
        "exchanges": {},
        "timestamp": datetime.now().isoformat(),
    }


def _mock_tax_summary(year: int):
    """Return mock tax summary."""
    return {
        "year": year,
        "total_transactions": 0,
        "long_term": {"gains": 0, "losses": 0, "net": 0},
        "short_term": {"gains": 0, "losses": 0, "net": 0},
        "total_net": 0,
    }


def _mock_analysis():
    """Return mock analysis data."""
    return {
        "health_score": 78,
        "sharpe_ratio": 0,
        "max_drawdown": 0,
        "volatility": 0,
        "concentration_pct": 0,
        "asset_count": 0,
        "recommendations": [
            "Connect exchange API keys for real portfolio analysis",
        ],
    }
