"""Unit tests for S&P Dow Jones Index Management & Divisor Recalibration Engine."""

import pytest
from src.core_engine import IndexConstituent, IndexManagementEngine


@pytest.fixture
def mock_index():
    engine = IndexManagementEngine(index_name="S&P Benchmark", initial_divisor=5000000.0)
    c1 = IndexConstituent("AAPL", "Apple Inc", 180.0, 15000000.0, 0.99)
    c2 = IndexConstituent("MSFT", "Microsoft Corp", 420.0, 7500000.0, 0.98)
    c3 = IndexConstituent("AMZN", "Amazon.com Inc", 175.0, 10000000.0, 0.90)
    c4 = IndexConstituent("TARGET_ACQ", "Acquired Co", 50.0, 2000000.0, 0.95)
    engine.add_constituent(c1)
    engine.add_constituent(c2)
    engine.add_constituent(c3)
    engine.add_constituent(c4)
    return engine


def test_index_level_and_market_cap(mock_index):
    assert mock_index.total_float_market_cap > 5000000000.0
    level = mock_index.index_level
    assert level > 0


def test_stock_split_neutrality(mock_index):
    pre_level = mock_index.index_level
    pre_div = mock_index.divisor
    # 2-for-1 forward split on AAPL
    res = mock_index.process_stock_split("AAPL", split_ratio=2.0)
    post_level = mock_index.index_level

    assert res["drift"] < 1e-6
    assert abs(post_level - pre_level) < 1e-6
    assert mock_index.divisor == pre_div
    assert mock_index.constituents["AAPL"].price == 90.0
    assert mock_index.constituents["AAPL"].shares == 30000000.0


def test_special_dividend_divisor_continuity(mock_index):
    pre_level = mock_index.index_level
    pre_div = mock_index.divisor
    res = mock_index.process_special_cash_dividend("MSFT", dividend_per_share=8.0)
    post_level = mock_index.index_level

    # Level must remain invariant; divisor must adjust downward
    assert res["drift"] < 1e-6
    assert abs(post_level - pre_level) < 1e-6
    assert mock_index.divisor < pre_div


def test_constituent_replacement(mock_index):
    pre_level = mock_index.index_level
    new_stock = IndexConstituent("NEW_CO", "Growth Tech Inc", 120.0, 5000000.0, 0.92)
    res = mock_index.process_constituent_replacement("TARGET_ACQ", new_stock)
    post_level = mock_index.index_level

    assert "TARGET_ACQ" not in mock_index.constituents
    assert "NEW_CO" in mock_index.constituents
    assert res["drift"] < 1e-6
    assert abs(post_level - pre_level) < 1e-6


def test_feed_reconciliation_discrepancy_detection(mock_index):
    # Feed matches within tolerance
    clean_feed = {"AAPL": (180.0, 15000000.0), "MSFT": (420.0, 7500000.0)}
    discrepancies = mock_index.verify_reconciliation_feed(clean_feed)
    assert len(discrepancies) == 0

    # Feed has pricing jump error
    dirty_feed = {"AAPL": (220.0, 15000000.0)}  # $220 vs $180
    discrepancies = mock_index.verify_reconciliation_feed(dirty_feed, tolerance_pct=0.01)
    assert len(discrepancies) == 1
    assert discrepancies[0]["ticker"] == "AAPL"
    assert discrepancies[0]["status"] == "FAIL_PRICE"
