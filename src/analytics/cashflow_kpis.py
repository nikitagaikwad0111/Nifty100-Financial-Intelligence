import logging

logger = logging.getLogger(__name__)


def compute_fcf(operating_activity, investing_activity):
    """Free Cash Flow = CFO + CFI. Negative value allowed."""
    if operating_activity is None or investing_activity is None:
        return None
    return round(operating_activity + investing_activity, 2)


def compute_cfo_quality_score(cfo_values: list, pat_values: list):
    """
    CFO Quality Score = average(CFO/PAT) over up to 5 years.
    >1.0 = High Quality, 0.5-1.0 = Moderate, <0.5 = Accrual Risk.
    Returns (score, label). None if PAT all zero.
    """
    ratios = []
    for cfo, pat in zip(cfo_values, pat_values):
        if pat is None or pat == 0:
            continue
        if cfo is None:
            continue
        ratios.append(cfo / pat)

    if not ratios:
        return None, None

    avg_ratio = round(sum(ratios) / len(ratios), 2)

    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_ratio, label


def compute_capex_intensity(investing_activity, sales):
    """
    CapEx Intensity = abs(investing_activity) / sales * 100.
    <3% = Asset Light, 3-8% = Moderate, >8% = Capital Intensive.
    Returns (value, label).
    """
    if sales is None or sales == 0 or investing_activity is None:
        return None, None

    intensity = round(abs(investing_activity) / sales * 100, 2)

    if intensity < 3:
        label = "Asset Light"
    elif intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def compute_fcf_conversion(fcf, operating_profit):
    """
    FCF Conversion Rate = FCF / operating_profit * 100.
    Returns None if operating_profit = 0.
    """
    if operating_profit is None or operating_profit == 0:
        return None
    if fcf is None:
        return None
    return round(fcf / operating_profit * 100, 2)


def classify_capital_allocation(cfo, cfi, cff):
    """
    Classify capital allocation pattern based on sign of CFO, CFI, CFF.
    Returns (pattern_label, cfo_sign, cfi_sign, cff_sign).
    """
    def sign(x):
        if x is None:
            return "?"
        return "+" if x > 0 else ("-" if x < 0 else "0")

    cfo_sign = sign(cfo)
    cfi_sign = sign(cfi)
    cff_sign = sign(cff)

    pattern_map = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "-", "+"): "Cash Accumulator",
        ("+", "+", "-"): "Liquidating Assets",
        ("+", "+", "+"): "Mixed",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("-", "-", "-"): "Pre-Revenue",
        ("-", "+", "-"): "Mixed",
    }

    key = (cfo_sign, cfi_sign, cff_sign)
    label = pattern_map.get(key, "Unclassified")

    return label, cfo_sign, cfi_sign, cff_sign


def detect_distress_pattern(cfo, cff):
    """CFO < 0 AND CFF > 0 = Distress Signal (raising funds to fund ops)."""
    if cfo is None or cff is None:
        return False
    return cfo < 0 and cff > 0


def detect_deleveraging(cff, borrowings_current, borrowings_prior):
    """CFF < 0 AND borrowings declining YoY = Deleveraging."""
    if cff is None or borrowings_current is None or borrowings_prior is None:
        return False
    return cff < 0 and borrowings_current < borrowings_prior
