import logging

logger = logging.getLogger(__name__)


def compute_cagr(start_value, end_value, n_years):
    """
    Compute CAGR = ((end/start)^(1/n) - 1) * 100.
    Returns (cagr_value, flag).
    Flags: None, DECLINE_TO_LOSS, TURNAROUND, BOTH_NEGATIVE,
           ZERO_BASE, INSUFFICIENT
    """
    if n_years < 3:
        return None, "INSUFFICIENT"

    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value > 0:
        cagr = ((end_value / start_value) ** (1 / n_years) - 1) * 100
        return round(cagr, 2), None

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    return None, "INSUFFICIENT"


def get_value_n_years_ago(time_series: dict, current_year: str, n: int):
    """
    time_series: dict of {year: value}, years in 'YYYY-MM' format.
    Returns the value from n years before current_year, or None.
    """
    try:
        current_yr_num = int(current_year[:4])
        target_yr = current_yr_num - n
        for year_key, value in time_series.items():
            if int(year_key[:4]) == target_yr:
                return value
        return None
    except (ValueError, TypeError):
        return None


def compute_growth_metrics(time_series: dict, current_year: str) -> dict:
    """
    Compute 3yr, 5yr, 10yr CAGR for a single metric (e.g. revenue).
    time_series: {year: value} for one company, one metric.
    Returns dict with cagr values and flags for each window.
    """
    result = {}
    current_value = time_series.get(current_year)

    for window in [3, 5, 10]:
        start_value = get_value_n_years_ago(time_series, current_year, window)
        n_years_available = len([
            y for y in time_series.keys()
            if int(y[:4]) <= int(current_year[:4])
        ])

        if n_years_available < window:
            result[f"cagr_{window}yr"] = None
            result[f"cagr_{window}yr_flag"] = "INSUFFICIENT"
            continue

        cagr, flag = compute_cagr(start_value, current_value, window)
        result[f"cagr_{window}yr"] = cagr
        result[f"cagr_{window}yr_flag"] = flag

    return result


def compute_revenue_cagr(time_series: dict, current_year: str) -> dict:
    """Revenue CAGR for 3/5/10yr windows."""
    metrics = compute_growth_metrics(time_series, current_year)
    return {
        "revenue_cagr_3yr": metrics["cagr_3yr"],
        "revenue_cagr_3yr_flag": metrics["cagr_3yr_flag"],
        "revenue_cagr_5yr": metrics["cagr_5yr"],
        "revenue_cagr_5yr_flag": metrics["cagr_5yr_flag"],
        "revenue_cagr_10yr": metrics["cagr_10yr"],
        "revenue_cagr_10yr_flag": metrics["cagr_10yr_flag"],
    }


def compute_pat_cagr(time_series: dict, current_year: str) -> dict:
    """PAT (net profit) CAGR for 3/5/10yr windows."""
    metrics = compute_growth_metrics(time_series, current_year)
    return {
        "pat_cagr_3yr": metrics["cagr_3yr"],
        "pat_cagr_3yr_flag": metrics["cagr_3yr_flag"],
        "pat_cagr_5yr": metrics["cagr_5yr"],
        "pat_cagr_5yr_flag": metrics["cagr_5yr_flag"],
        "pat_cagr_10yr": metrics["cagr_10yr"],
        "pat_cagr_10yr_flag": metrics["cagr_10yr_flag"],
    }


def compute_eps_cagr(time_series: dict, current_year: str) -> dict:
    """EPS CAGR for 3/5/10yr windows."""
    metrics = compute_growth_metrics(time_series, current_year)
    return {
        "eps_cagr_3yr": metrics["cagr_3yr"],
        "eps_cagr_3yr_flag": metrics["cagr_3yr_flag"],
        "eps_cagr_5yr": metrics["cagr_5yr"],
        "eps_cagr_5yr_flag": metrics["cagr_5yr_flag"],
        "eps_cagr_10yr": metrics["cagr_10yr"],
        "eps_cagr_10yr_flag": metrics["cagr_10yr_flag"],
    }
