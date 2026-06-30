import pytest
from src.analytics.ratios import compute_de, compute_icr, compute_net_debt


class TestDebtToEquityEdgeCases:

    def test_de_zero_borrowings_returns_zero_not_none(self):
        de, flag = compute_de(0, 1000, 5000)
        assert de == 0.0
        assert de is not None

    def test_de_none_borrowings(self):
        de, flag = compute_de(None, 1000, 5000)
        assert de == 0.0

    def test_de_negative_equity_returns_none(self):
        de, flag = compute_de(1000, -2000, -500)
        assert de is None

    def test_de_boundary_exactly_5(self):
        de, flag = compute_de(5000, 1000, 0, "Industrials")
        assert de == 5.0
        assert flag is False

    def test_de_boundary_above_5(self):
        de, flag = compute_de(5001, 1000, 0, "Industrials")
        assert flag is True


class TestInterestCoverageEdgeCases:

    def test_icr_negative_operating_profit(self):
        icr, label = compute_icr(-500, 100, 200)
        assert icr is not None
        assert icr < 0

    def test_icr_label_stored_separately(self):
        icr, label = compute_icr(1000, 0, 0)
        assert icr is None
        assert label == "Debt Free"

    def test_icr_exactly_at_risk_boundary(self):
        icr, label = compute_icr(150, 0, 100)
        assert icr == 1.5
        assert label == "OK"

    def test_icr_just_below_boundary(self):
        icr, label = compute_icr(149, 0, 100)
        assert icr == 1.49
        assert label == "At Risk"


class TestNetDebt:

    def test_net_debt_positive(self):
        assert compute_net_debt(5000, 1000) == 4000

    def test_net_debt_negative_cash_rich(self):
        assert compute_net_debt(1000, 5000) == -4000

    def test_net_debt_debt_free(self):
        assert compute_net_debt(0, 2000) == -2000

    def test_net_debt_none_investments(self):
        assert compute_net_debt(3000, None) == 3000
