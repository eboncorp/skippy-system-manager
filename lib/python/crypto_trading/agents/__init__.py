"""
Crypto Portfolio Manager - Agents Module

Complete signal analysis system with 130+ market indicators.

Signal Modules:
- extended_signals: Base 60 signals (technical, sentiment, on-chain, derivatives, macro, mining, institutional)
- expanded_signals: Additional 70 signals (smart money, DeFi, order flow, calendar, cross-chain, cycle)
- unified_analyzer: Master analyzer combining all 130+ signals

Usage:
    from agents import UnifiedSignalAnalyzer, quick_unified_analysis
    
    # Quick analysis
    result = await quick_unified_analysis("BTC")
    print(result)
    
    # Full analysis
    analyzer = UnifiedSignalAnalyzer()
    analysis = await analyzer.analyze("BTC")
    print(f"Composite: {analysis.composite_score}")
    print(f"DCA Multiplier: {analysis.primary_recommendation.dca_multiplier}x")
"""

# Base 60 Signals
from .extended_signals import (
    ExtendedSignalsAnalyzer,
    SignalStrength,
    SignalResult,
    ComprehensiveSignalAnalysis,
    CategorySummary,
    format_extended_signals,
)

# Additional 70 Signals
from .expanded_signals import (
    ExpandedSignalsAnalyzer,
    ExpandedSignalAnalysis,
    ExpandedCategorySummary,
    format_expanded_signals,
)

# Unified 130+ Signal Analyzer
from .unified_analyzer import (
    UnifiedSignalAnalyzer,
    UnifiedSignalAnalysis,
    MasterCategorySummary,
    ActionRecommendation,
    MarketCondition,
    CyclePhase,
    format_unified_analysis,
    quick_unified_analysis,
)

# Legacy modules (for backwards compatibility)
try:
    from .advanced_onchain import (
        AdvancedOnChainAnalyzer,
        AdvancedSignalResult,
        format_advanced_signals,
    )
except ImportError:
    AdvancedOnChainAnalyzer = None
    AdvancedSignalResult = None
    format_advanced_signals = None

try:
    from .unified_orchestrator import (
        UnifiedSignalOrchestrator,
        UnifiedAnalysis,
        MarketPhase,
        SignalCategory,
    )
except ImportError:
    UnifiedSignalOrchestrator = None
    UnifiedAnalysis = None
    MarketPhase = None
    SignalCategory = None


# Trading Agent
from .trading_agent import (
    TradingAgent,
    TradingConfig,
    TradingMode,
    RiskLimits,
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    Position,
    PositionSide,
    Trade,
    Portfolio,
    SignalAction,
    ExchangeInterface,
    PaperExchange,
    CoinbaseExchange,
    TradingStrategy,
    DCASignalStrategy,
    SwingStrategy,
    MeanReversionStrategy,
    GridStrategy,
    RebalanceStrategy,
    RiskManager,
    create_paper_agent,
)

# Backtester
from .backtester import (
    BacktestEngine,
    BacktestResult,
    BacktestTrade,
    PerformanceMetrics,
    PortfolioSnapshot,
    HistoricalDataProvider,
    SimulatedSignalGenerator,
    OHLCV,
    format_backtest_report,
    compare_strategies,
    run_strategy_backtest,
    compare_all_strategies,
)

# Index Manager (COIN50-style portfolio construction)
from .index_manager import (
    IndexBuilder,
    IndexConfig,
    IndexPortfolio,
    IndexAsset,
    IndexRebalancer,
    IndexReporter,
    HoldingsImporter,
    HoldingRecord,
    AccountType,
    AssetScore,
    quick_sort,
    STABLECOINS,
    WRAPPED_ASSETS,
    EXCHANGE_TOKENS,
    PRIVACY_COINS,
    ASSET_SCORES,
    STAKING_RATES,
)


__all__ = [
    # Base 60 Signals
    "ExtendedSignalsAnalyzer",
    "SignalStrength",
    "SignalResult",
    "ComprehensiveSignalAnalysis",
    "CategorySummary",
    "format_extended_signals",
    
    # Expanded 70 Signals
    "ExpandedSignalsAnalyzer",
    "ExpandedSignalAnalysis",
    "ExpandedCategorySummary",
    "format_expanded_signals",
    
    # Unified 130+ Analyzer (Primary)
    "UnifiedSignalAnalyzer",
    "UnifiedSignalAnalysis",
    "MasterCategorySummary",
    "ActionRecommendation",
    "MarketCondition",
    "CyclePhase",
    "format_unified_analysis",
    "quick_unified_analysis",
    
    # Trading Agent
    "TradingAgent",
    "TradingConfig",
    "TradingMode",
    "RiskLimits",
    "Order",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "Position",
    "PositionSide",
    "Trade",
    "Portfolio",
    "SignalAction",
    "ExchangeInterface",
    "PaperExchange",
    "CoinbaseExchange",
    "TradingStrategy",
    "DCASignalStrategy",
    "SwingStrategy",
    "MeanReversionStrategy",
    "GridStrategy",
    "RebalanceStrategy",
    "RiskManager",
    "create_paper_agent",
    
    # Backtester
    "BacktestEngine",
    "BacktestResult",
    "BacktestTrade",
    "PerformanceMetrics",
    "PortfolioSnapshot",
    "HistoricalDataProvider",
    "SimulatedSignalGenerator",
    "OHLCV",
    "format_backtest_report",
    "compare_strategies",
    "run_strategy_backtest",
    "compare_all_strategies",
    
    # Legacy (if available)
    "AdvancedOnChainAnalyzer",
    "AdvancedSignalResult",
    "format_advanced_signals",
    "UnifiedSignalOrchestrator",
    "UnifiedAnalysis",
    "MarketPhase",
    "SignalCategory",
    
    # Index Manager
    "IndexBuilder",
    "IndexConfig",
    "IndexPortfolio",
    "IndexAsset",
    "IndexRebalancer",
    "IndexReporter",
    "HoldingsImporter",
    "HoldingRecord",
    "AccountType",
    "AssetScore",
    "quick_sort",
    "STABLECOINS",
    "WRAPPED_ASSETS",
    "EXCHANGE_TOKENS",
    "PRIVACY_COINS",
    "ASSET_SCORES",
    "STAKING_RATES",
]
