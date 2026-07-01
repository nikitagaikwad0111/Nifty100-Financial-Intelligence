import pytest
from src.analytics.cashflow_kpis import (
    compute_fcf, compute_cfo_quality_score, compute_capex_intensity,
    compute_fcf_conversion, classify_capital_allocation,
    detect_distress_pattern, detect_deleveraging
)


class TestFCF:

    def test_fcf_normal(self):
        assert compute_fcf(1000, -300) == 700

    def test_fcf_negative(self):
        assert compute_fcf(500, -800) == -300

    def test_fcf_none_input(self):
        assert compute_fcf(None, -300) is None


class TestCFOQuality:

    def test_high_quality(self):
        score, label = compute_cfo_quality_score([1200, 1300], [1000, 1000])
        assert label == "High Quality"

    def test_moderate(self):
        score, label = compute_cfo_quality_score([600], [1000])
        assert label == "Moderate"

    def test_accrual_risk(self):
        score, label = compute_cfo_quality_score([300], [1000])
        assert label == "Accrual Risk"

    def test_zero_pat_skipped(self):
        score, label = compute_cfo_quality_score([1000], [0])
        assert score is None
        assert label is None


class TestCapexIntensity:

    def test_asset_light(self):
        value, label = compute_capex_intensity(-200, 10000)
        assert label == "Asset Light"

    def test_capital_intensive(self):
        value, label = compute_capex_intensity(-1000, 10000)
        assert label == "Capital Intensive"

    def test_zero_sales(self):
        value, label = compute_capex_intensity(-200, 0)
        assert value is None


class TestFCFConversion:

    def test_efficient(self):
        result = compute_fcf_conversion(700, 1000)
        assert result == 70.0

    def test_zero_operating_profit(self):
        assert compute_fcf_conversion(700, 0) is None


class TestCapitalAllocation:

    def test_reinvestor(self):
        label, cfo, cfi, cff = classify_capital_allocation(1000, -500, -200)
        assert label == "Reinvestor"

    def test_distress_signal(self):
        label, cfo, cfi, cff = classify_capital_allocation(-500, 300, 600)
        assert label == "Distress Signal"

    def test_cash_accumulator(self):
        label, cfo, cfi, cff = classify_capital_allocation(1000, -200, 300)
        assert label == "Cash Accumulator"

    def test_growth_funded_by_debt(self):
        label, cfo, cfi, cff = classify_capital_allocation(-200, -500, 800)
        assert label == "Growth Funded by Debt"

    def test_pre_revenue(self):
        label, cfo, cfi, cff = classify_capital_allocation(-100, -200, -50)
        assert label == "Pre-Revenue"


class TestDistressDetection:

    def test_distress_true(self):
        assert detect_distress_pattern(-500, 600) is True

    def test_distress_false(self):
        assert detect_distress_pattern(500, 600) is False


class TestDeleveraging:

    def test_deleveraging_true(self):
        assert detect_deleveraging(-300, 800, 1000) is True

    def test_deleveraging_false_increasing_debt(self):
        assert detect_deleveraging(-300, 1200, 1000) is False
