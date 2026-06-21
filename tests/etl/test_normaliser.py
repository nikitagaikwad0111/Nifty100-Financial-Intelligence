import pytest
from src.etl.normaliser import normalize_year, normalize_ticker


# ─── normalize_year tests ───────────────────────────────────────────────

class TestNormalizeYear:

    # Standard formats
    def test_mar23(self):
        assert normalize_year("Mar-23") == "2023-03"

    def test_mar_24(self):
        assert normalize_year("Mar-24") == "2024-03"

    def test_dec22(self):
        assert normalize_year("Dec-22") == "2022-12"

    def test_jun23(self):
        assert normalize_year("Jun-23") == "2023-06"

    def test_sep21(self):
        assert normalize_year("Sep-21") == "2021-09"

    def test_jan20(self):
        assert normalize_year("Jan-20") == "2020-01"

    # FY prefix formats
    def test_fy24(self):
        assert normalize_year("FY24") == "2024-03"

    def test_fy2023(self):
        assert normalize_year("FY2023") == "2023-03"

    def test_fy20(self):
        assert normalize_year("FY20") == "2020-03"

    def test_fy_lowercase(self):
        assert normalize_year("fy24") == "2024-03"

    # Plain integer year
    def test_plain_year_2023(self):
        assert normalize_year("2023") == "2023-03"

    def test_plain_year_2010(self):
        assert normalize_year("2010") == "2010-03"

    # Already normalised
    def test_already_normalised(self):
        assert normalize_year("2023-03") == "2023-03"

    def test_already_normalised_dec(self):
        assert normalize_year("2022-12") == "2022-12"

    # Full month names
    def test_march_2023(self):
        assert normalize_year("March-2023") == "2023-03"

    def test_december_2022(self):
        assert normalize_year("December-2022") == "2022-12"

    def test_march_space(self):
        assert normalize_year("Mar 23") == "2023-03"

    # Edge cases
    def test_none_input(self):
        assert normalize_year(None) == "PARSE_ERROR"

    def test_garbage_input(self):
        assert normalize_year("xyz") == "PARSE_ERROR"

    def test_empty_string(self):
        assert normalize_year("") == "PARSE_ERROR"


# ─── normalize_ticker tests ─────────────────────────────────────────────

class TestNormalizeTicker:

    # Standard cases
    def test_already_upper(self):
        assert normalize_ticker("TCS") == "TCS"

    def test_lowercase(self):
        assert normalize_ticker("tcs") == "TCS"

    def test_mixed_case(self):
        assert normalize_ticker("Tcs") == "TCS"

    def test_leading_space(self):
        assert normalize_ticker(" TCS") == "TCS"

    def test_trailing_space(self):
        assert normalize_ticker("TCS ") == "TCS"

    def test_both_spaces(self):
        assert normalize_ticker("  TCS  ") == "TCS"

    # Special characters preserved
    def test_hyphen(self):
        assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"

    def test_ampersand(self):
        assert normalize_ticker("M&M") == "M&M"

    def test_ampersand_lowercase(self):
        assert normalize_ticker("m&m") == "M&M"

    # More tickers
    def test_hdfcbank(self):
        assert normalize_ticker("hdfcbank") == "HDFCBANK"

    def test_infy(self):
        assert normalize_ticker("  INFY  ") == "INFY"

    def test_reliance(self):
        assert normalize_ticker("reliance") == "RELIANCE"

    def test_sbin(self):
        assert normalize_ticker("Sbin") == "SBIN"

    def test_sunpharma(self):
        assert normalize_ticker("sunpharma") == "SUNPHARMA"

    def test_none_input(self):
        assert normalize_ticker(None) == ""