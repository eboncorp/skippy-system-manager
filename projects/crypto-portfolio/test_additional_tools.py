"""
Tests for Additional MCP Tools
==============================

Tests for trading, staking management, DCA bots, alerts,
market data, NFTs, and tax reporting tools.
"""

import json
import pytest
from datetime import datetime

import sys
sys.path.insert(0, '..')

from additional_tools import (
    # Input Models
    PlaceOrderInput,
    CancelOrderInput,
    GetOpenOrdersInput,
    StakeAssetInput,
    UnstakeAssetInput,
    ClaimRewardsInput,
    CreateDCABotInput,
    ModifyDCABotInput,
    CreateAlertInput,
    DeleteAlertInput,
    GetPricesInput,
    GetPriceHistoryInput,
    MarketSentimentInput,
    NFTHoldingsInput,
    ExportTaxReportInput,
    # Enums
    OrderSide,
    OrderType,
    TimeInForce,
    AlertType,
    Frequency,
    ResponseFormat,
    Exchange,
)


# =============================================================================
# TRADING INPUT VALIDATION TESTS
# =============================================================================


class TestPlaceOrderInput:
    """Tests for PlaceOrderInput validation."""

    def test_valid_market_order(self):
        """Test valid market order input."""
        inp = PlaceOrderInput(
            exchange=Exchange.COINBASE,
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=0.1
        )
        assert inp.exchange == Exchange.COINBASE
        assert inp.symbol == "BTC-USD"
        assert inp.side == OrderSide.BUY
        assert inp.amount == 0.1

    def test_valid_limit_order(self):
        """Test valid limit order input."""
        inp = PlaceOrderInput(
            exchange=Exchange.KRAKEN,
            symbol="ETH-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            amount=1.5,
            price=3000.00
        )
        assert inp.order_type == OrderType.LIMIT
        assert inp.price == 3000.00

    def test_limit_order_requires_price(self):
        """Test that limit orders require price."""
        with pytest.raises(ValueError):
            PlaceOrderInput(
                exchange=Exchange.COINBASE,
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                amount=0.1
                # Missing price
            )

    def test_amount_must_be_positive(self):
        """Test amount must be positive."""
        with pytest.raises(ValueError):
            PlaceOrderInput(
                exchange=Exchange.COINBASE,
                symbol="BTC-USD",
                side=OrderSide.BUY,
                amount=-0.1
            )

    def test_all_order_types(self):
        """Test all order types are valid."""
        for order_type in OrderType:
            price = 45000.00 if order_type in [OrderType.LIMIT, OrderType.STOP_LOSS, OrderType.TAKE_PROFIT] else None
            inp = PlaceOrderInput(
                exchange=Exchange.COINBASE,
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=order_type,
                amount=0.1,
                price=price,
                stop_price=price
            )
            assert inp.order_type == order_type

    def test_all_time_in_force(self):
        """Test all time in force options."""
        for tif in TimeInForce:
            inp = PlaceOrderInput(
                exchange=Exchange.COINBASE,
                symbol="BTC-USD",
                side=OrderSide.BUY,
                amount=0.1,
                time_in_force=tif
            )
            assert inp.time_in_force == tif


class TestCancelOrderInput:
    """Tests for CancelOrderInput validation."""

    def test_valid_cancel(self):
        """Test valid cancel input."""
        inp = CancelOrderInput(
            exchange=Exchange.COINBASE,
            order_id="ord_123456"
        )
        assert inp.order_id == "ord_123456"

    def test_order_id_required(self):
        """Test order_id is required."""
        with pytest.raises(ValueError):
            CancelOrderInput(exchange=Exchange.COINBASE, order_id="")


# =============================================================================
# STAKING MANAGEMENT INPUT VALIDATION TESTS
# =============================================================================


class TestStakeAssetInput:
    """Tests for StakeAssetInput validation."""

    def test_valid_stake(self):
        """Test valid stake input."""
        inp = StakeAssetInput(
            exchange=Exchange.COINBASE,
            asset="ETH",
            amount=5.0
        )
        assert inp.asset == "ETH"
        assert inp.amount == 5.0

    def test_amount_must_be_positive(self):
        """Test amount must be positive."""
        with pytest.raises(ValueError):
            StakeAssetInput(
                exchange=Exchange.COINBASE,
                asset="ETH",
                amount=0
            )

    def test_optional_validator(self):
        """Test optional validator field."""
        inp = StakeAssetInput(
            exchange=Exchange.KRAKEN,
            asset="SOL",
            amount=100,
            validator="validator_pubkey_here"
        )
        assert inp.validator == "validator_pubkey_here"


class TestUnstakeAssetInput:
    """Tests for UnstakeAssetInput validation."""

    def test_unstake_all(self):
        """Test unstaking all (no amount specified)."""
        inp = UnstakeAssetInput(
            exchange=Exchange.COINBASE,
            asset="ETH"
        )
        assert inp.amount is None

    def test_unstake_partial(self):
        """Test unstaking partial amount."""
        inp = UnstakeAssetInput(
            exchange=Exchange.COINBASE,
            asset="ETH",
            amount=2.5
        )
        assert inp.amount == 2.5


# =============================================================================
# DCA BOT INPUT VALIDATION TESTS
# =============================================================================


class TestCreateDCABotInput:
    """Tests for CreateDCABotInput validation."""

    def test_valid_dca_bot(self):
        """Test valid DCA bot creation."""
        inp = CreateDCABotInput(
            exchange=Exchange.COINBASE,
            asset="BTC",
            amount_usd=100.0,
            frequency=Frequency.WEEKLY
        )
        assert inp.asset == "BTC"
        assert inp.amount_usd == 100.0
        assert inp.frequency == Frequency.WEEKLY

    def test_all_frequencies(self):
        """Test all frequency options."""
        for freq in Frequency:
            inp = CreateDCABotInput(
                exchange=Exchange.COINBASE,
                asset="BTC",
                amount_usd=50,
                frequency=freq
            )
            assert inp.frequency == freq

    def test_amount_limits(self):
        """Test amount USD limits."""
        # Minimum
        inp = CreateDCABotInput(
            exchange=Exchange.COINBASE,
            asset="BTC",
            amount_usd=1.0,
            frequency=Frequency.DAILY
        )
        assert inp.amount_usd == 1.0
        
        # Maximum
        inp = CreateDCABotInput(
            exchange=Exchange.COINBASE,
            asset="BTC",
            amount_usd=10000.0,
            frequency=Frequency.MONTHLY
        )
        assert inp.amount_usd == 10000.0

    def test_amount_below_minimum(self):
        """Test amount below minimum."""
        with pytest.raises(ValueError):
            CreateDCABotInput(
                exchange=Exchange.COINBASE,
                asset="BTC",
                amount_usd=0.5,
                frequency=Frequency.WEEKLY
            )

    def test_amount_above_maximum(self):
        """Test amount above maximum."""
        with pytest.raises(ValueError):
            CreateDCABotInput(
                exchange=Exchange.COINBASE,
                asset="BTC",
                amount_usd=15000.0,
                frequency=Frequency.WEEKLY
            )


class TestModifyDCABotInput:
    """Tests for ModifyDCABotInput validation."""

    def test_valid_actions(self):
        """Test all valid actions."""
        for action in ["pause", "resume", "delete"]:
            inp = ModifyDCABotInput(bot_id="dca_btc_weekly", action=action)
            assert inp.action == action

    def test_invalid_action(self):
        """Test invalid action rejected."""
        with pytest.raises(ValueError):
            ModifyDCABotInput(bot_id="dca_btc_weekly", action="start")


# =============================================================================
# ALERT INPUT VALIDATION TESTS
# =============================================================================


class TestCreateAlertInput:
    """Tests for CreateAlertInput validation."""

    def test_price_alert(self):
        """Test price alert creation."""
        inp = CreateAlertInput(
            alert_type=AlertType.PRICE_ABOVE,
            asset="BTC",
            threshold=50000.0
        )
        assert inp.alert_type == AlertType.PRICE_ABOVE
        assert inp.threshold == 50000.0

    def test_all_alert_types(self):
        """Test all alert types."""
        for alert_type in AlertType:
            inp = CreateAlertInput(
                alert_type=alert_type,
                asset="BTC" if alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_BELOW, AlertType.PERCENT_CHANGE] else None,
                threshold=50000.0 if alert_type != AlertType.PERCENT_CHANGE else 10.0
            )
            assert inp.alert_type == alert_type

    def test_notification_channels(self):
        """Test notification channels."""
        inp = CreateAlertInput(
            alert_type=AlertType.PRICE_BELOW,
            asset="ETH",
            threshold=2000.0,
            notification_channels=["email", "sms", "webhook"]
        )
        assert len(inp.notification_channels) == 3

    def test_optional_note(self):
        """Test optional note field."""
        inp = CreateAlertInput(
            alert_type=AlertType.PRICE_ABOVE,
            asset="BTC",
            threshold=100000.0,
            note="To the moon!"
        )
        assert inp.note == "To the moon!"


# =============================================================================
# MARKET DATA INPUT VALIDATION TESTS
# =============================================================================


class TestGetPricesInput:
    """Tests for GetPricesInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = GetPricesInput()
        assert inp.assets is None
        assert inp.include_24h_change is True

    def test_specific_assets(self):
        """Test specific assets list."""
        inp = GetPricesInput(assets=["BTC", "ETH", "SOL"])
        assert len(inp.assets) == 3


class TestGetPriceHistoryInput:
    """Tests for GetPriceHistoryInput validation."""

    def test_valid_input(self):
        """Test valid price history input."""
        inp = GetPriceHistoryInput(asset="BTC", interval="1d", limit=30)
        assert inp.asset == "BTC"
        assert inp.interval == "1d"
        assert inp.limit == 30

    def test_valid_intervals(self):
        """Test all valid intervals."""
        for interval in ["1h", "4h", "1d", "1w"]:
            inp = GetPriceHistoryInput(asset="BTC", interval=interval)
            assert inp.interval == interval

    def test_invalid_interval(self):
        """Test invalid interval rejected."""
        with pytest.raises(ValueError):
            GetPriceHistoryInput(asset="BTC", interval="5m")

    def test_limit_range(self):
        """Test limit must be in valid range."""
        inp = GetPriceHistoryInput(asset="BTC", limit=365)
        assert inp.limit == 365
        
        with pytest.raises(ValueError):
            GetPriceHistoryInput(asset="BTC", limit=400)


class TestMarketSentimentInput:
    """Tests for MarketSentimentInput validation."""

    def test_default_all_included(self):
        """Test all data included by default."""
        inp = MarketSentimentInput()
        assert inp.include_fear_greed is True
        assert inp.include_dominance is True
        assert inp.include_trending is True

    def test_selective_inclusion(self):
        """Test selective data inclusion."""
        inp = MarketSentimentInput(
            include_fear_greed=True,
            include_dominance=False,
            include_trending=False
        )
        assert inp.include_fear_greed is True
        assert inp.include_dominance is False


# =============================================================================
# NFT INPUT VALIDATION TESTS
# =============================================================================


class TestNFTHoldingsInput:
    """Tests for NFTHoldingsInput validation."""

    def test_default_values(self):
        """Test default values."""
        inp = NFTHoldingsInput()
        assert inp.wallet_address is None
        assert inp.include_floor_prices is True

    def test_valid_wallet_address(self):
        """Test valid Ethereum address."""
        inp = NFTHoldingsInput(
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f8e2f8"
        )
        assert inp.wallet_address is not None

    def test_invalid_wallet_address(self):
        """Test invalid address rejected."""
        with pytest.raises(ValueError):
            NFTHoldingsInput(wallet_address="invalid")


# =============================================================================
# TAX TOOLS INPUT VALIDATION TESTS
# =============================================================================


class TestExportTaxReportInput:
    """Tests for ExportTaxReportInput validation."""

    def test_valid_export(self):
        """Test valid export input."""
        inp = ExportTaxReportInput(tax_year=2024)
        assert inp.tax_year == 2024
        assert inp.format == "csv"
        assert inp.cost_basis_method == "fifo"

    def test_all_formats(self):
        """Test all export formats."""
        for fmt in ["csv", "pdf", "turbotax", "taxact"]:
            inp = ExportTaxReportInput(tax_year=2024, format=fmt)
            assert inp.format == fmt

    def test_invalid_format(self):
        """Test invalid format rejected."""
        with pytest.raises(ValueError):
            ExportTaxReportInput(tax_year=2024, format="excel")

    def test_all_cost_basis_methods(self):
        """Test all cost basis methods."""
        for method in ["fifo", "lifo", "hifo", "avg"]:
            inp = ExportTaxReportInput(tax_year=2024, cost_basis_method=method)
            assert inp.cost_basis_method == method

    def test_tax_year_range(self):
        """Test tax year valid range."""
        inp = ExportTaxReportInput(tax_year=2015)
        assert inp.tax_year == 2015
        
        inp = ExportTaxReportInput(tax_year=2030)
        assert inp.tax_year == 2030
        
        with pytest.raises(ValueError):
            ExportTaxReportInput(tax_year=2010)


# =============================================================================
# RUN TESTS
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
