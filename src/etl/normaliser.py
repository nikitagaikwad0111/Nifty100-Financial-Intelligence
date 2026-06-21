import re
import logging

logger = logging.getLogger(__name__)

MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03", "april": "04",
    "june": "06", "july": "07", "august": "08", "september": "09",
    "october": "10", "november": "11", "december": "12"
}


def normalize_year(raw) -> str:
    """Convert raw year labels like 'Mar-23', 'FY24', 'Dec-22' to 'YYYY-MM'."""
    if raw is None:
        return "PARSE_ERROR"
    raw = str(raw).strip()

    # Already normalised
    if re.match(r"^\d{4}-\d{2}$", raw):
        return raw

    # Plain integer year e.g. 2023
    if re.match(r"^\d{4}$", raw):
        return f"{raw}-03"

    # FY prefix e.g. FY23, FY2023
    fy = re.match(r"^FY(\d{2,4})$", raw, re.IGNORECASE)
    if fy:
        yr = fy.group(1)
        yr = ("20" + yr) if len(yr) == 2 else yr
        return f"{yr}-03"

    # Mon-YY or Mon-YYYY or Month-YYYY e.g. Mar-23, March-2023
    m = re.match(r"^([a-zA-Z]+)[\s\-](\d{2,4})$", raw)
    if m:
        mon_str = m.group(1).lower()
        yr = m.group(2)
        yr = ("20" + yr) if len(yr) == 2 else yr
        mon_num = MONTH_MAP.get(mon_str)
        if mon_num:
            return f"{yr}-{mon_num}"

    logger.warning(f"normalize_year: could not parse '{raw}'")
    return "PARSE_ERROR"


def normalize_ticker(raw) -> str:
    """Strip whitespace and uppercase a ticker symbol."""
    if raw is None:
        return ""
    cleaned = str(raw).strip().upper()
    if len(cleaned) < 2 or len(cleaned) > 12:
        logger.warning(f"normalize_ticker: unusual length '{cleaned}'")
    return cleaned