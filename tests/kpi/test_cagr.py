import pytest
from src.analytics.cagr import compute_cagr, compute_growth_metrics


class TestComputeCagr:

    def test_normal_positive_growth(self):
        cagr, flag = compute_cagr(100, 161.05, 5)
        assert cagr == pytest.approx(10.0, abs=0.1)
        assert flag is None

    def test_decline_to_loss(self):
        cagr, flag = compute_cagr(100, -50, 5)
        assert cagr is None
        assert flag == "DECLINE_TO_LOSS"

    def test_turnaround(self):
        cagr, flag = compute_cagr(-100, 200, 5)
        assert cagr is None
        assert flag == "TURNAROUND"

    def test_both_negative(self):
        cagr, flag = compute_cagr(-100, -50, 5)
        assert cagr is None
        assert flag == "BOTH_NEGATIVE"

    def test_zero_base(self):
        cagr, flag = compute_cagr(0, 100, 5)
        assert cagr is None
        assert flag == "ZERO_BASE"

    def test_insufficient_years(self):
        cagr, flag = compute_cagr(100, 150, 2)
        assert cagr is None
        assert flag == "INSUFFICIENT"

    def test_none_start_value(self):
        cagr, flag = compute_cagr(None, 150, 5)
        assert cagr is None
        assert flag == "INSUFFICIENT"

    def test_flat_growth(self):
        cagr, flag = compute_cagr(100, 100, 5)
        assert cagr == 0.0
        assert flag is None

    def test_high_growth(self):
        cagr, flag = compute_cagr(100, 300, 3)
        assert cagr > 40
        assert flag is None


class TestGrowthMetrics:

    def test_full_10yr_history(self):
        time_series = {
            "2014-03": 100, "2015-03": 110, "2016-03": 120,
            "2017-03": 135, "2018-03": 150, "2019-03": 165,
            "2020-03": 180, "2021-03": 195, "2022-03": 210,
            "2023-03": 225, "2024-03": 240
        }
        result = compute_growth_metrics(time_series, "2024-03")
        assert result["cagr_3yr"] is not None
        assert result["cagr_5yr"] is not None
        assert result["cagr_10yr"] is not None

    def test_insufficient_history(self):
        time_series = {
            "2023-03": 100, "2024-03": 110
        }
        result = compute_growth_metrics(time_series, "2024-03")
        assert result["cagr_3yr"] is None
        assert result["cagr_3yr_flag"] == "INSUFFICIENT"
