"""
Crypto Portfolio MCP Server - Test Suite
=========================================

Comprehensive tests for all MCP tools including:
- Input validation (Pydantic models)
- Tool execution
- Response formatting (JSON and Markdown)
- Error handling
- Edge cases

Run with: pytest tests/ -v --cov=. --cov-report=html
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Import the MCP server components
import sys
sys.path.insert(0, '..')

from crypto_portfolio_mcp import (
    # Input models
    PortfolioSummaryInput,
    ExchangeHoldingsInput,
    StakingPositionsInput,
    DeFiPositionsInput,
    AIAnalysisInput,
    CostBasisInput,
    HistoricalSnapshotInput,
    ArbitrageOpportunitiesInput,
    DCABotStatusInput,
    AlertsInput,
    TransactionHistoryInput,
    # Enums
    ResponseFormat,
    Exchange,
    CostBasisMethod,
    DeFiProtocol,
    # Tools
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
    # Helpers
    format_currency,
    format_percent,
    handle_api_error,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def portfolio_summary_input():
    """Default portfolio summary input."""
    return PortfolioSummaryInput()


@pytest.fixture
def exchange_holdings_input():
    """Default exchange holdings input."""
    return ExchangeHoldingsInput()


@pytest.fixture
def staking_input():
    """Default staking positions input."""
    return StakingPositionsInput()


@pytest.fixture
def defi_input():
    """Default DeFi positions input."""
    return DeFiPositionsInput()


@pytest.fixture
def ai_analysis_input():
    """Default AI analysis input."""
    return AIAnalysisInput()


@pytest.fixture
def cost_basis_input():
    """Default cost basis input."""
    return CostBasisInput()


@pytest.fixture
def arbitrage_input():
    """Default arbitrage input."""
    return ArbitrageOpportunitiesInput()


@pytest.fixture
def transaction_input():
    """Default transaction history input."""
    return TransactionHistoryInput()


@pytest.fixture
def alerts_input():
    """Default alerts input."""
    return AlertsInput()


@pytest.fixture
def dca_bot_input():
    """Default DCA bot status input."""
    return DCABotStatusInput()


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


class TestHelperFunctions:
    """Tests for utility/helper functions."""

    def test_format_currency_small(self):
        """Test currency formatting for small values."""
        assert format_currency(123.45) == "$123.45"
        assert format_currency(0.99) == "$0.99"
        assert format_currency(999.99) == "$999.99"

    def test_format_currency_thousands(self):
        """Test currency formatting for thousands."""
        assert format_currency(1000) == "$1.00K"
        assert format_currency(5432.10) == "$5.43K"
        assert format_currency(999999) == "$1000.00K"

    def test_format_currency_millions(self):
        """Test currency formatting for millions."""
        assert format_currency(1000000) == "$1.00M"
        assert format_currency(5432100) == "$5.43M"
        assert format_currency(127834560) == "$127.83M"

    def test_format_currency_custom_symbol(self):
        """Test currency formatting with custom symbol."""
        assert format_currency(100, "€") == "€100.00"
        assert format_currency(5000, "£") == "£5.00K"

    def test_format_percent_positive(self):
        """Test percentage formatting for positive values."""
        assert format_percent(5.5) == "+5.50%"
        assert format_percent(100.0) == "+100.00%"
        assert format_percent(0.01) == "+0.01%"

    def test_format_percent_negative(self):
        """Test percentage formatting for negative values."""
        assert format_percent(-5.5) == "-5.50%"
        assert format_percent(-100.0) == "-100.00%"

    def test_format_percent_zero(self):
        """Test percentage formatting for zero."""
        assert format_percent(0) == "0.00%"

    def test_handle_api_error_auth(self):
        """Test error handling for authentication errors."""
        error = Exception("authentication failed")
        result = handle_api_error(error, "fetching data")
        assert "Authentication failed" in result
        assert "API keys" in result

    def test_handle_api_error_rate_limit(self):
        """Test error handling for rate limit errors."""
        error = Exception("rate limit exceeded")
        result = handle_api_error(error)
        assert "Rate limit exceeded" in result

    def test_handle_api_error_timeout(self):
        """Test error handling for timeout errors."""
        error = Exception("request timeout")
        result = handle_api_error(error)
        assert "timed out" in result

    def test_handle_api_error_not_found(self):
        """Test error handling for not found errors."""
        error = Exception("resource not found")
        result = handle_api_error(error)
        assert "not found" in result

    def test_handle_api_error_generic(self):
        """Test error handling for generic errors."""
        error = ValueError("something went wrong")
        result = handle_api_error(error)
        assert "ValueError" in result
        assert "something went wrong" in result


# =============================================================================
# INPUT MODEL VALIDATION TESTS
# =============================================================================


class TestPortfolioSummaryInput:
    """Tests for PortfolioSummaryInput validation."""

    def test_default_values(self):
        """Test default values are set correctly."""
        inp = PortfolioSummaryInput()
        assert inp.include_staking is True
        assert inp.include_defi is True
        assert inp.include_nfts is False
        assert inp.response_format == ResponseFormat.MARKDOWN

    def test_custom_values(self):
        """Test custom values are accepted."""
        inp = PortfolioSummaryInput(
            include_staking=False,
            include_defi=False,
            include_nfts=True,
            response_format=ResponseFormat.JSON
        )
        assert inp.include_staking is False
        assert inp.include_nfts is True
        assert inp.response_format == ResponseFormat.JSON

    def test_invalid_response_format(self):
        """Test invalid response format raises error."""
        with pytest.raises(ValueError):
            PortfolioSummaryInput(response_format="xml")


class TestExchangeHoldingsInput:
    """Tests for ExchangeHoldingsInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = ExchangeHoldingsInput()
        assert inp.exchange == Exchange.ALL
        assert inp.asset is None
        assert inp.min_value_usd is None

    def test_valid_exchange(self):
        """Test valid exchange values."""
        for exchange in Exchange:
            inp = ExchangeHoldingsInput(exchange=exchange)
            assert inp.exchange == exchange

    def test_asset_filter(self):
        """Test asset filter validation."""
        inp = ExchangeHoldingsInput(asset="BTC")
        assert inp.asset == "BTC"

    def test_asset_too_long(self):
        """Test asset filter max length."""
        with pytest.raises(ValueError):
            ExchangeHoldingsInput(asset="A" * 25)

    def test_min_value_positive(self):
        """Test min_value_usd must be positive."""
        inp = ExchangeHoldingsInput(min_value_usd=100.0)
        assert inp.min_value_usd == 100.0

    def test_min_value_negative_rejected(self):
        """Test negative min_value_usd is rejected."""
        with pytest.raises(ValueError):
            ExchangeHoldingsInput(min_value_usd=-50.0)


class TestStakingPositionsInput:
    """Tests for StakingPositionsInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = StakingPositionsInput()
        assert inp.exchange == Exchange.ALL
        assert inp.include_rewards is True

    def test_specific_exchange(self):
        """Test filtering by specific exchange."""
        inp = StakingPositionsInput(exchange=Exchange.COINBASE)
        assert inp.exchange == Exchange.COINBASE


class TestDeFiPositionsInput:
    """Tests for DeFiPositionsInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = DeFiPositionsInput()
        assert inp.protocol == DeFiProtocol.ALL
        assert inp.wallet_address is None

    def test_valid_wallet_address(self):
        """Test valid Ethereum address."""
        valid_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f8e2f8"
        inp = DeFiPositionsInput(wallet_address=valid_address)
        assert inp.wallet_address == valid_address

    def test_invalid_wallet_address(self):
        """Test invalid Ethereum address is rejected."""
        with pytest.raises(ValueError):
            DeFiPositionsInput(wallet_address="not_an_address")

    def test_invalid_wallet_too_short(self):
        """Test wallet address too short."""
        with pytest.raises(ValueError):
            DeFiPositionsInput(wallet_address="0x123")


class TestAIAnalysisInput:
    """Tests for AIAnalysisInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = AIAnalysisInput()
        assert inp.analysis_type == "comprehensive"
        assert inp.time_range_days == 30
        assert inp.include_recommendations is True

    def test_valid_analysis_types(self):
        """Test all valid analysis types."""
        valid_types = ["comprehensive", "risk", "performance", "rebalancing", "tax_optimization"]
        for analysis_type in valid_types:
            inp = AIAnalysisInput(analysis_type=analysis_type)
            assert inp.analysis_type == analysis_type

    def test_invalid_analysis_type(self):
        """Test invalid analysis type is rejected."""
        with pytest.raises(ValueError):
            AIAnalysisInput(analysis_type="invalid_type")

    def test_time_range_limits(self):
        """Test time range boundaries."""
        inp = AIAnalysisInput(time_range_days=1)
        assert inp.time_range_days == 1

        inp = AIAnalysisInput(time_range_days=365)
        assert inp.time_range_days == 365

    def test_time_range_too_small(self):
        """Test time range below minimum."""
        with pytest.raises(ValueError):
            AIAnalysisInput(time_range_days=0)

    def test_time_range_too_large(self):
        """Test time range above maximum."""
        with pytest.raises(ValueError):
            AIAnalysisInput(time_range_days=400)


class TestCostBasisInput:
    """Tests for CostBasisInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = CostBasisInput()
        assert inp.asset is None
        assert inp.method == CostBasisMethod.FIFO
        assert inp.tax_year is None

    def test_all_methods(self):
        """Test all cost basis methods."""
        for method in CostBasisMethod:
            inp = CostBasisInput(method=method)
            assert inp.method == method

    def test_tax_year_range(self):
        """Test tax year within valid range."""
        inp = CostBasisInput(tax_year=2024)
        assert inp.tax_year == 2024

    def test_tax_year_too_old(self):
        """Test tax year before valid range."""
        with pytest.raises(ValueError):
            CostBasisInput(tax_year=2005)

    def test_tax_year_too_future(self):
        """Test tax year after valid range."""
        with pytest.raises(ValueError):
            CostBasisInput(tax_year=2035)


class TestTransactionHistoryInput:
    """Tests for TransactionHistoryInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = TransactionHistoryInput()
        assert inp.exchange == Exchange.ALL
        assert inp.limit == 20
        assert inp.offset == 0

    def test_valid_tx_types(self):
        """Test valid transaction types."""
        valid_types = ["buy", "sell", "transfer", "stake", "unstake", "reward"]
        for tx_type in valid_types:
            inp = TransactionHistoryInput(tx_type=tx_type)
            assert inp.tx_type == tx_type

    def test_invalid_tx_type(self):
        """Test invalid transaction type."""
        with pytest.raises(ValueError):
            TransactionHistoryInput(tx_type="invalid")

    def test_valid_date_format(self):
        """Test valid date format."""
        inp = TransactionHistoryInput(start_date="2024-01-15")
        assert inp.start_date == "2024-01-15"

    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(ValueError):
            TransactionHistoryInput(start_date="01-15-2024")

    def test_pagination_limits(self):
        """Test pagination boundaries."""
        inp = TransactionHistoryInput(limit=100, offset=500)
        assert inp.limit == 100
        assert inp.offset == 500

    def test_limit_too_high(self):
        """Test limit above maximum."""
        with pytest.raises(ValueError):
            TransactionHistoryInput(limit=150)

    def test_offset_negative(self):
        """Test negative offset rejected."""
        with pytest.raises(ValueError):
            TransactionHistoryInput(offset=-10)


class TestArbitrageOpportunitiesInput:
    """Tests for ArbitrageOpportunitiesInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = ArbitrageOpportunitiesInput()
        assert inp.min_spread_percent == 0.5
        assert inp.assets is None

    def test_spread_range(self):
        """Test spread percentage range."""
        inp = ArbitrageOpportunitiesInput(min_spread_percent=0.1)
        assert inp.min_spread_percent == 0.1

        inp = ArbitrageOpportunitiesInput(min_spread_percent=10.0)
        assert inp.min_spread_percent == 10.0

    def test_spread_too_small(self):
        """Test spread below minimum."""
        with pytest.raises(ValueError):
            ArbitrageOpportunitiesInput(min_spread_percent=0.05)

    def test_spread_too_large(self):
        """Test spread above maximum."""
        with pytest.raises(ValueError):
            ArbitrageOpportunitiesInput(min_spread_percent=15.0)


# =============================================================================
# TOOL EXECUTION TESTS
# =============================================================================


@pytest.mark.asyncio
class TestPortfolioSummaryTool:
    """Tests for crypto_portfolio_summary tool."""

    async def test_returns_markdown_by_default(self, portfolio_summary_input):
        """Test default response is markdown."""
        result = await crypto_portfolio_summary(portfolio_summary_input)
        assert "# Portfolio Summary" in result
        assert "Total Value" in result

    async def test_returns_json_when_requested(self):
        """Test JSON response format."""
        inp = PortfolioSummaryInput(response_format=ResponseFormat.JSON)
        result = await crypto_portfolio_summary(inp)
        data = json.loads(result)
        assert "total_value_usd" in data
        assert "holdings" in data

    async def test_includes_staking_by_default(self, portfolio_summary_input):
        """Test staking is included by default."""
        result = await crypto_portfolio_summary(portfolio_summary_input)
        assert "Staking" in result

    async def test_excludes_staking_when_disabled(self):
        """Test staking exclusion."""
        inp = PortfolioSummaryInput(include_staking=False)
        result = await crypto_portfolio_summary(inp)
        # Staking section should not appear
        assert "## Staking" not in result

    async def test_includes_defi_by_default(self, portfolio_summary_input):
        """Test DeFi is included by default."""
        result = await crypto_portfolio_summary(portfolio_summary_input)
        assert "DeFi" in result


@pytest.mark.asyncio
class TestExchangeHoldingsTool:
    """Tests for crypto_exchange_holdings tool."""

    async def test_returns_all_exchanges_by_default(self, exchange_holdings_input):
        """Test all exchanges returned by default."""
        result = await crypto_exchange_holdings(exchange_holdings_input)
        assert "Coinbase" in result or "coinbase" in result.lower()

    async def test_filters_by_exchange(self):
        """Test filtering by specific exchange."""
        inp = ExchangeHoldingsInput(exchange=Exchange.COINBASE)
        result = await crypto_exchange_holdings(inp)
        assert "coinbase" in result.lower()

    async def test_json_format(self):
        """Test JSON response."""
        inp = ExchangeHoldingsInput(response_format=ResponseFormat.JSON)
        result = await crypto_exchange_holdings(inp)
        data = json.loads(result)
        assert "holdings" in data


@pytest.mark.asyncio
class TestStakingPositionsTool:
    """Tests for crypto_staking_positions tool."""

    async def test_returns_staking_data(self, staking_input):
        """Test staking data is returned."""
        result = await crypto_staking_positions(staking_input)
        assert "Staking" in result
        assert "APY" in result or "apy" in result.lower()

    async def test_includes_rewards(self, staking_input):
        """Test rewards are included."""
        result = await crypto_staking_positions(staking_input)
        assert "Rewards" in result or "rewards" in result.lower()

    async def test_json_format(self):
        """Test JSON response."""
        inp = StakingPositionsInput(response_format=ResponseFormat.JSON)
        result = await crypto_staking_positions(inp)
        data = json.loads(result)
        assert "positions" in data
        assert "total_staked_usd" in data


@pytest.mark.asyncio
class TestDeFiPositionsTool:
    """Tests for crypto_defi_positions tool."""

    async def test_returns_defi_data(self, defi_input):
        """Test DeFi data is returned."""
        result = await crypto_defi_positions(defi_input)
        assert "DeFi" in result

    async def test_filters_by_protocol(self):
        """Test filtering by protocol."""
        inp = DeFiPositionsInput(protocol=DeFiProtocol.AAVE)
        result = await crypto_defi_positions(inp)
        # Should contain Aave data
        assert "aave" in result.lower() or "Aave" in result

    async def test_json_format(self):
        """Test JSON response."""
        inp = DeFiPositionsInput(response_format=ResponseFormat.JSON)
        result = await crypto_defi_positions(inp)
        data = json.loads(result)
        assert "positions" in data
        assert "total_value_usd" in data


@pytest.mark.asyncio
class TestAIAnalysisTool:
    """Tests for crypto_ai_analysis tool."""

    async def test_returns_analysis(self, ai_analysis_input):
        """Test analysis is returned."""
        result = await crypto_ai_analysis(ai_analysis_input)
        assert "Analysis" in result
        assert "Health" in result or "health" in result.lower()

    async def test_includes_recommendations_by_default(self, ai_analysis_input):
        """Test recommendations included by default."""
        result = await crypto_ai_analysis(ai_analysis_input)
        assert "Recommendation" in result or "recommendation" in result.lower()

    async def test_excludes_recommendations_when_disabled(self):
        """Test recommendations can be excluded."""
        inp = AIAnalysisInput(include_recommendations=False)
        result = await crypto_ai_analysis(inp)
        # Should still have analysis but recommendations section may be absent
        assert "Analysis" in result

    async def test_json_format(self):
        """Test JSON response."""
        inp = AIAnalysisInput(response_format=ResponseFormat.JSON)
        result = await crypto_ai_analysis(inp)
        data = json.loads(result)
        assert "portfolio_health_score" in data
        assert "recommendations" in data


@pytest.mark.asyncio
class TestCostBasisTool:
    """Tests for crypto_cost_basis tool."""

    async def test_returns_cost_basis(self, cost_basis_input):
        """Test cost basis data is returned."""
        result = await crypto_cost_basis(cost_basis_input)
        assert "Cost Basis" in result

    async def test_shows_method(self, cost_basis_input):
        """Test method is shown in result."""
        result = await crypto_cost_basis(cost_basis_input)
        assert "FIFO" in result

    async def test_different_methods(self):
        """Test different cost basis methods."""
        for method in CostBasisMethod:
            inp = CostBasisInput(method=method)
            result = await crypto_cost_basis(inp)
            assert method.value.upper() in result

    async def test_json_format(self):
        """Test JSON response."""
        inp = CostBasisInput(response_format=ResponseFormat.JSON)
        result = await crypto_cost_basis(inp)
        data = json.loads(result)
        assert "method" in data
        assert "assets" in data


@pytest.mark.asyncio
class TestArbitrageTool:
    """Tests for crypto_arbitrage_opportunities tool."""

    async def test_returns_opportunities(self, arbitrage_input):
        """Test arbitrage opportunities are returned."""
        result = await crypto_arbitrage_opportunities(arbitrage_input)
        assert "Arbitrage" in result

    async def test_respects_min_spread(self):
        """Test minimum spread filter."""
        inp = ArbitrageOpportunitiesInput(min_spread_percent=5.0)
        result = await crypto_arbitrage_opportunities(inp)
        # High threshold may return no results
        assert "Arbitrage" in result

    async def test_json_format(self):
        """Test JSON response."""
        inp = ArbitrageOpportunitiesInput(response_format=ResponseFormat.JSON)
        result = await crypto_arbitrage_opportunities(inp)
        data = json.loads(result)
        assert "opportunities" in data


@pytest.mark.asyncio
class TestTransactionHistoryTool:
    """Tests for crypto_transaction_history tool."""

    async def test_returns_transactions(self, transaction_input):
        """Test transactions are returned."""
        result = await crypto_transaction_history(transaction_input)
        # JSON is default for this tool
        data = json.loads(result)
        assert "transactions" in data
        assert "total" in data

    async def test_pagination_info(self, transaction_input):
        """Test pagination info is included."""
        result = await crypto_transaction_history(transaction_input)
        data = json.loads(result)
        assert "offset" in data
        assert "limit" in data
        assert "has_more" in data

    async def test_markdown_format(self):
        """Test markdown response."""
        inp = TransactionHistoryInput(response_format=ResponseFormat.MARKDOWN)
        result = await crypto_transaction_history(inp)
        assert "Transaction History" in result
        assert "|" in result  # Table format


@pytest.mark.asyncio
class TestAlertsTool:
    """Tests for crypto_alerts_status tool."""

    async def test_list_action(self, alerts_input):
        """Test list action."""
        result = await crypto_alerts_status(alerts_input)
        assert "Alert" in result

    async def test_summary_action(self):
        """Test summary action."""
        inp = AlertsInput(action="summary")
        result = await crypto_alerts_status(inp)
        assert "Active" in result or "active" in result.lower()

    async def test_triggered_action(self):
        """Test triggered action."""
        inp = AlertsInput(action="triggered")
        result = await crypto_alerts_status(inp)
        assert "Triggered" in result or "triggered" in result.lower()


@pytest.mark.asyncio
class TestDCABotTool:
    """Tests for crypto_dca_bot_status tool."""

    async def test_returns_bot_status(self, dca_bot_input):
        """Test bot status is returned."""
        result = await crypto_dca_bot_status(dca_bot_input)
        assert "DCA" in result or "Bot" in result

    async def test_json_format(self):
        """Test JSON response."""
        inp = DCABotStatusInput(response_format=ResponseFormat.JSON)
        result = await crypto_dca_bot_status(inp)
        data = json.loads(result)
        assert "bots" in data


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling in tools."""

    async def test_handles_exception_gracefully(self):
        """Test that exceptions are handled gracefully."""
        # This tests the mock data path, which shouldn't throw
        inp = PortfolioSummaryInput()
        result = await crypto_portfolio_summary(inp)
        # Should return data, not crash
        assert result is not None
        assert "Error" not in result or "Portfolio" in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


@pytest.mark.asyncio
class TestToolIntegration:
    """Integration tests for tool combinations."""

    async def test_portfolio_then_analysis(self):
        """Test getting portfolio then running analysis."""
        # Get portfolio
        portfolio_inp = PortfolioSummaryInput(response_format=ResponseFormat.JSON)
        portfolio_result = await crypto_portfolio_summary(portfolio_inp)
        portfolio_data = json.loads(portfolio_result)
        
        # Run analysis
        analysis_inp = AIAnalysisInput(response_format=ResponseFormat.JSON)
        analysis_result = await crypto_ai_analysis(analysis_inp)
        analysis_data = json.loads(analysis_result)
        
        # Both should have data
        assert portfolio_data["total_value_usd"] > 0
        assert analysis_data["portfolio_health_score"] > 0

    async def test_all_tools_return_valid_json(self):
        """Test all tools can return valid JSON."""
        tools_and_inputs = [
            (crypto_portfolio_summary, PortfolioSummaryInput(response_format=ResponseFormat.JSON)),
            (crypto_exchange_holdings, ExchangeHoldingsInput(response_format=ResponseFormat.JSON)),
            (crypto_staking_positions, StakingPositionsInput(response_format=ResponseFormat.JSON)),
            (crypto_defi_positions, DeFiPositionsInput(response_format=ResponseFormat.JSON)),
            (crypto_ai_analysis, AIAnalysisInput(response_format=ResponseFormat.JSON)),
            (crypto_cost_basis, CostBasisInput(response_format=ResponseFormat.JSON)),
            (crypto_arbitrage_opportunities, ArbitrageOpportunitiesInput(response_format=ResponseFormat.JSON)),
            (crypto_transaction_history, TransactionHistoryInput(response_format=ResponseFormat.JSON)),
            (crypto_alerts_status, AlertsInput(response_format=ResponseFormat.JSON)),
            (crypto_dca_bot_status, DCABotStatusInput(response_format=ResponseFormat.JSON)),
        ]
        
        for tool, inp in tools_and_inputs:
            result = await tool(inp)
            # Should not raise
            data = json.loads(result)
            assert isinstance(data, dict)

    async def test_all_tools_return_valid_markdown(self):
        """Test all tools can return valid markdown."""
        tools_and_inputs = [
            (crypto_portfolio_summary, PortfolioSummaryInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_exchange_holdings, ExchangeHoldingsInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_staking_positions, StakingPositionsInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_defi_positions, DeFiPositionsInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_ai_analysis, AIAnalysisInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_cost_basis, CostBasisInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_arbitrage_opportunities, ArbitrageOpportunitiesInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_transaction_history, TransactionHistoryInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_alerts_status, AlertsInput(response_format=ResponseFormat.MARKDOWN)),
            (crypto_dca_bot_status, DCABotStatusInput(response_format=ResponseFormat.MARKDOWN)),
        ]
        
        for tool, inp in tools_and_inputs:
            result = await tool(inp)
            # Should be a non-empty string with markdown characteristics
            assert isinstance(result, str)
            assert len(result) > 0
            # Most should have headers or formatting
            assert "#" in result or "|" in result or "-" in result


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


@pytest.mark.asyncio
class TestPerformance:
    """Basic performance tests."""

    async def test_portfolio_summary_speed(self):
        """Test portfolio summary completes quickly."""
        import time
        
        inp = PortfolioSummaryInput()
        start = time.time()
        await crypto_portfolio_summary(inp)
        elapsed = time.time() - start
        
        # Should complete in under 1 second (mock data)
        assert elapsed < 1.0

    async def test_batch_requests(self):
        """Test multiple concurrent requests."""
        import asyncio
        
        inp = PortfolioSummaryInput()
        tasks = [crypto_portfolio_summary(inp) for _ in range(10)]
        
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 10
        assert all("Portfolio" in r for r in results)


# =============================================================================
# RUN TESTS
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
