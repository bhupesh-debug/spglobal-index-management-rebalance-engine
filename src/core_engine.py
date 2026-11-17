"""
S&P Dow Jones Indices Index Management & Divisor Recalibration Core Engine
Project Codename: SPDJI-Rebalance-Net
Author: Bhupesh Chandra Dimri
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class IndexConstituent:
    ticker: str
    name: str
    price: float
    shares: float
    iwf: float  # Investable Weight Factor (0.0 to 1.0)

    @property
    def float_market_cap(self) -> float:
        return self.price * self.shares * self.iwf


class IndexManagementEngine:
    """Enterprise index calculation, reconstitution, and corporate action engine."""

    def __init__(self, index_name: str = "S&P 500 Mock Index", initial_divisor: float = 10000000.0):
        self.index_name = index_name
        self.divisor = initial_divisor
        self.constituents: Dict[str, IndexConstituent] = {}

    def add_constituent(self, constituent: IndexConstituent):
        self.constituents[constituent.ticker] = constituent

    @property
    def total_float_market_cap(self) -> float:
        return sum(c.float_market_cap for c in self.constituents.values())

    @property
    def index_level(self) -> float:
        if self.divisor == 0:
            raise ZeroDivisionError("Index divisor cannot be zero.")
        return self.total_float_market_cap / self.divisor

    def process_stock_split(self, ticker: str, split_ratio: float) -> Dict[str, float]:
        """Processes a forward or reverse stock split (split_ratio k-for-1)."""
        if ticker not in self.constituents:
            raise KeyError(f"Ticker {ticker} not found.")

        c = self.constituents[ticker]
        pre_level = self.index_level
        pre_divisor = self.divisor

        c.price = c.price / split_ratio
        c.shares = c.shares * split_ratio

        post_level = self.index_level
        # Net market cap change is zero; divisor is invariant
        return {
            "ticker": ticker,
            "split_ratio": split_ratio,
            "pre_level": round(pre_level, 4),
            "post_level": round(post_level, 4),
            "pre_divisor": round(pre_divisor, 2),
            "post_divisor": round(self.divisor, 2),
            "drift": abs(post_level - pre_level)
        }

    def process_special_cash_dividend(self, ticker: str, dividend_per_share: float) -> Dict[str, float]:
        """Adjusts constituent price and recalibrates divisor for capital distribution."""
        if ticker not in self.constituents:
            raise KeyError(f"Ticker {ticker} not found.")

        c = self.constituents[ticker]
        pre_level = self.index_level
        pre_divisor = self.divisor
        pre_market_cap = self.total_float_market_cap

        # Price drops by dividend per share
        c.price -= dividend_per_share
        post_market_cap = self.total_float_market_cap

        # Divisor adjusts downward to maintain exact index level
        self.divisor = pre_divisor * (post_market_cap / pre_market_cap)
        post_level = self.index_level

        return {
            "ticker": ticker,
            "dividend_per_share": dividend_per_share,
            "pre_level": round(pre_level, 4),
            "post_level": round(post_level, 4),
            "pre_divisor": round(pre_divisor, 2),
            "post_divisor": round(self.divisor, 2),
            "delta_market_cap": round(post_market_cap - pre_market_cap, 2),
            "drift": abs(post_level - pre_level)
        }

    def process_constituent_replacement(
        self, removed_ticker: str, new_constituent: IndexConstituent
    ) -> Dict[str, float]:
        """Replaces a delisted/acquired constituent and recalibrates divisor."""
        if removed_ticker not in self.constituents:
            raise KeyError(f"Ticker {removed_ticker} not found.")

        pre_level = self.index_level
        pre_divisor = self.divisor
        pre_market_cap = self.total_float_market_cap

        del self.constituents[removed_ticker]
        self.add_constituent(new_constituent)

        post_market_cap = self.total_float_market_cap
        self.divisor = pre_divisor * (post_market_cap / pre_market_cap)
        post_level = self.index_level

        return {
            "removed_ticker": removed_ticker,
            "added_ticker": new_constituent.ticker,
            "pre_level": round(pre_level, 4),
            "post_level": round(post_level, 4),
            "pre_divisor": round(pre_divisor, 2),
            "post_divisor": round(self.divisor, 2),
            "net_market_cap_change": round(post_market_cap - pre_market_cap, 2),
            "drift": abs(post_level - pre_level)
        }

    def verify_reconciliation_feed(
        self, external_feed: Dict[str, Tuple[float, float]], tolerance_pct: float = 0.0005
    ) -> List[Dict[str, any]]:
        """Compares internal constituent prices & shares against external market feed."""
        discrepancies = []
        for ticker, (ext_price, ext_shares) in external_feed.items():
            if ticker in self.constituents:
                c = self.constituents[ticker]
                price_diff = abs(c.price - ext_price) / max(0.01, c.price)
                shares_diff = abs(c.shares - ext_shares) / max(1.0, c.shares)

                if price_diff > tolerance_pct or shares_diff > tolerance_pct:
                    discrepancies.append({
                        "ticker": ticker,
                        "internal_price": c.price,
                        "external_price": ext_price,
                        "price_diff_pct": round(price_diff * 100, 4),
                        "internal_shares": c.shares,
                        "external_shares": ext_shares,
                        "status": "FAIL_PRICE" if price_diff > tolerance_pct else "FAIL_SHARES"
                    })
        return discrepancies
