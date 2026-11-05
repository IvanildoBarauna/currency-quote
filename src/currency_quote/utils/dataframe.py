# src/currency_quote/utils/dataframe.py
"""Optional pandas export for quote results."""
from typing import Any, List

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:  # pragma: no cover - exercised via the |pandas extra
    pd = None
    HAS_PANDAS = False

PANDAS_INSTALL_HINT = (
    "pandas is required for DataFrame exports. "
    "Install it with: pip install 'currency-quote[pandas]'"
)


def build_dataframe(rows: List[dict]) -> Any:
    """Build a ``pandas.DataFrame`` from quote dicts (raises if pandas is missing)."""
    if not HAS_PANDAS:
        raise ImportError(PANDAS_INSTALL_HINT)
    return pd.DataFrame(rows)
