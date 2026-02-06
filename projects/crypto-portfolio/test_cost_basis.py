"""
Tests for CostBasisTracker — tax lot tracking and gain/loss calculation.

Covers:
- Purchase lot creation
- FIFO, LIFO, HIFO lot selection
- Gain/loss calculation (short-term and long-term)
- Partial lot depletion
- Insufficient lots error handling
- Holdings and unrealized gains
"""

import pytest
from datetime import datetime, timedelta, timezone
from cost_basis import CostBasisTracker, AccountingMethod


@pytest.fixture
def tracker(tmp_path):
    """Create a CostBasisTracker with a temp database."""
    db_path = str(tmp_path / "test_cost_basis.db")
    return CostBasisTracker(db_path=db_path)


@pytest.fixture
def tracker_with_lots(tracker):
    """Tracker pre-loaded with 3 BTC lots at different prices and dates."""
    # Lot 1: oldest, cheapest
    tracker.add_purchase(
        asset="BTC", quantity=1.0, cost_per_unit=30000.0,
        purchase_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
        exchange="coinbase"
    )
    # Lot 2: middle age, most expensive
    tracker.add_purchase(
        asset="BTC", quantity=0.5, cost_per_unit=60000.0,
        purchase_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
        exchange="kraken"
    )
    # Lot 3: newest, mid-price
    tracker.add_purchase(
        asset="BTC", quantity=2.0, cost_per_unit=45000.0,
        purchase_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        exchange="coinbase"
    )
    return tracker


class TestAddPurchase:
    """Test lot creation."""

    def test_creates_lot(self, tracker):
        lot = tracker.add_purchase(
            asset="BTC", quantity=0.5, cost_per_unit=50000.0,
            purchase_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            exchange="coinbase"
        )
        assert lot.asset == "BTC"
        assert lot.quantity == 0.5
        assert lot.total_cost == 25000.0
        assert lot.remaining_quantity == 0.5

    def test_normalizes_asset_to_uppercase(self, tracker):
        lot = tracker.add_purchase(
            asset="eth", quantity=1.0, cost_per_unit=3000.0,
            purchase_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            exchange="coinbase"
        )
        assert lot.asset == "ETH"

    def test_multiple_lots_tracked(self, tracker_with_lots):
        holdings = tracker_with_lots.get_current_holdings()
        assert "BTC" in holdings
        assert holdings["BTC"]["quantity"] == pytest.approx(3.5)  # 1.0 + 0.5 + 2.0


class TestFIFO:
    """Test FIFO (First In, First Out) lot selection."""

    def test_fifo_uses_oldest_lot_first(self, tracker_with_lots):
        tracker_with_lots.set_accounting_method(AccountingMethod.FIFO)

        sale = tracker_with_lots.record_sale(
            asset="BTC", quantity=0.5, sale_price_per_unit=55000.0,
            sale_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            exchange="coinbase"
        )
        # FIFO: should use lot 1 (cost $30,000/BTC)
        assert sale.total_cost_basis == pytest.approx(15000.0)  # 0.5 * $30k
        assert sale.total_proceeds == pytest.approx(27500.0)    # 0.5 * $55k
        assert sale.gain_loss == pytest.approx(12500.0)

    def test_fifo_spans_multiple_lots(self, tracker_with_lots):
        tracker_with_lots.set_accounting_method(AccountingMethod.FIFO)

        sale = tracker_with_lots.record_sale(
            asset="BTC", quantity=1.3, sale_price_per_unit=55000.0,
            sale_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            exchange="coinbase"
        )
        # FIFO: 1.0 from lot 1 ($30k) + 0.3 from lot 2 ($60k)
        expected_cost = (1.0 * 30000) + (0.3 * 60000)  # 30000 + 18000 = 48000
        assert sale.total_cost_basis == pytest.approx(expected_cost)


class TestLIFO:
    """Test LIFO (Last In, First Out) lot selection."""

    def test_lifo_uses_newest_lot_first(self, tracker_with_lots):
        tracker_with_lots.set_accounting_method(AccountingMethod.LIFO)

        sale = tracker_with_lots.record_sale(
            asset="BTC", quantity=0.5, sale_price_per_unit=55000.0,
            sale_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            exchange="coinbase"
        )
        # LIFO: should use lot 3 (cost $45,000/BTC)
        assert sale.total_cost_basis == pytest.approx(22500.0)  # 0.5 * $45k
        assert sale.gain_loss == pytest.approx(5000.0)  # 27500 - 22500


class TestHIFO:
    """Test HIFO (Highest In, First Out) lot selection — most tax efficient."""

    def test_hifo_uses_highest_cost_first(self, tracker_with_lots):
        tracker_with_lots.set_accounting_method(AccountingMethod.HIFO)

        sale = tracker_with_lots.record_sale(
            asset="BTC", quantity=0.5, sale_price_per_unit=55000.0,
            sale_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            exchange="coinbase"
        )
        # HIFO: should use lot 2 (cost $60,000/BTC — highest)
        assert sale.total_cost_basis == pytest.approx(30000.0)  # 0.5 * $60k
        assert sale.gain_loss == pytest.approx(-2500.0)  # Loss! 27500 - 30000

    def test_hifo_minimizes_gains(self, tracker_with_lots):
        """HIFO should produce the smallest gain (or largest loss)."""
        methods = [AccountingMethod.FIFO, AccountingMethod.LIFO, AccountingMethod.HIFO]
        gains = {}

        for method in methods:
            # Fresh tracker for each
            t = CostBasisTracker(db_path=":memory:")
            t.add_purchase("BTC", 1.0, 30000.0, datetime(2023, 1, 1, tzinfo=timezone.utc), "cb")
            t.add_purchase("BTC", 0.5, 60000.0, datetime(2024, 6, 1, tzinfo=timezone.utc), "kr")
            t.add_purchase("BTC", 2.0, 45000.0, datetime(2025, 1, 1, tzinfo=timezone.utc), "cb")
            t.set_accounting_method(method)

            sale = t.record_sale("BTC", 0.5, 55000.0, datetime(2026, 1, 1, tzinfo=timezone.utc), "cb")
            gains[method.value] = sale.gain_loss

        assert gains["hifo"] <= gains["fifo"]
        assert gains["hifo"] <= gains["lifo"]


class TestGainLossCalculation:
    """Test gain/loss and holding period determination."""

    def test_short_term_gain(self, tracker):
        tracker.add_purchase(
            "BTC", 1.0, 50000.0,
            datetime(2025, 7, 1, tzinfo=timezone.utc), "coinbase"
        )
        sale = tracker.record_sale(
            "BTC", 1.0, 55000.0,
            datetime(2025, 12, 1, tzinfo=timezone.utc), "coinbase"
        )
        assert sale.gain_loss == pytest.approx(5000.0)
        assert not sale.is_long_term  # Held < 1 year

    def test_long_term_gain(self, tracker):
        tracker.add_purchase(
            "BTC", 1.0, 30000.0,
            datetime(2024, 1, 1, tzinfo=timezone.utc), "coinbase"
        )
        sale = tracker.record_sale(
            "BTC", 1.0, 55000.0,
            datetime(2025, 6, 1, tzinfo=timezone.utc), "coinbase"
        )
        assert sale.gain_loss == pytest.approx(25000.0)
        assert sale.is_long_term  # Held > 1 year

    def test_loss_calculation(self, tracker):
        tracker.add_purchase(
            "BTC", 1.0, 60000.0,
            datetime(2025, 1, 1, tzinfo=timezone.utc), "coinbase"
        )
        sale = tracker.record_sale(
            "BTC", 1.0, 45000.0,
            datetime(2025, 6, 1, tzinfo=timezone.utc), "coinbase"
        )
        assert sale.gain_loss == pytest.approx(-15000.0)


class TestPartialSales:
    """Test selling partial lots."""

    def test_partial_lot_depletion(self, tracker):
        tracker.add_purchase(
            "BTC", 2.0, 40000.0,
            datetime(2025, 1, 1, tzinfo=timezone.utc), "coinbase"
        )
        tracker.record_sale(
            "BTC", 0.5, 50000.0,
            datetime(2025, 6, 1, tzinfo=timezone.utc), "coinbase"
        )
        holdings = tracker.get_current_holdings()
        assert holdings["BTC"]["quantity"] == pytest.approx(1.5)

    def test_multiple_partial_sales(self, tracker):
        tracker.add_purchase(
            "BTC", 2.0, 40000.0,
            datetime(2025, 1, 1, tzinfo=timezone.utc), "coinbase"
        )
        for _ in range(4):
            tracker.record_sale(
                "BTC", 0.5, 50000.0,
                datetime(2025, 6, 1, tzinfo=timezone.utc), "coinbase"
            )
        holdings = tracker.get_current_holdings()
        assert "BTC" not in holdings  # Fully depleted

    def test_insufficient_lots_raises(self, tracker):
        tracker.add_purchase(
            "BTC", 1.0, 40000.0,
            datetime(2025, 1, 1, tzinfo=timezone.utc), "coinbase"
        )
        with pytest.raises(ValueError, match="Insufficient cost basis lots"):
            tracker.record_sale(
                "BTC", 2.0, 50000.0,
                datetime(2025, 6, 1, tzinfo=timezone.utc), "coinbase"
            )

    def test_no_lots_raises(self, tracker):
        with pytest.raises(ValueError, match="No cost basis lots found"):
            tracker.record_sale(
                "BTC", 1.0, 50000.0,
                datetime(2025, 6, 1, tzinfo=timezone.utc), "coinbase"
            )


class TestUnrealizedGains:
    """Test unrealized gain/loss calculations."""

    def test_unrealized_gains(self, tracker_with_lots):
        prices = {"BTC": 55000.0}
        result = tracker_with_lots.get_unrealized_gains(prices)

        # Total cost: 1.0*30k + 0.5*60k + 2.0*45k = 30k + 30k + 90k = 150k
        # Total value: 3.5 * 55k = 192.5k
        # Unrealized: 192.5k - 150k = 42.5k
        assert "BTC" in result
        assert result["BTC"]["unrealized_gain"] == pytest.approx(42500.0)

    def test_unrealized_with_missing_price(self, tracker_with_lots):
        prices = {}  # No price for BTC
        result = tracker_with_lots.get_unrealized_gains(prices)
        # With price=0, value=0, so unrealized = -cost_basis
        assert result["BTC"]["current_value"] == 0
