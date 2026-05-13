# ============================================================
# schema_detector.py — Smart CSV Schema Detection & Column Mapping
# Inspects any uploaded CSV, detects column types, and attempts
# to map them to the pipeline's expected column names.
# ============================================================

import pandas as pd
import numpy as np
from difflib import SequenceMatcher


# ── What the pipeline needs and what each column means ───────
PIPELINE_SCHEMA = {
    "customer_id": {
        "description": "Unique customer identifier",
        "dtype":       "id",
        "required":    True,
        "aliases":     ["customer id", "cust_id", "client_id", "user_id", "id", "customerid", "userid"],
    },
    "age": {
        "description": "Customer age (numeric)",
        "dtype":       "numeric",
        "required":    True,
        "aliases":     ["age", "customer_age", "age_years", "cust_age"],
    },
    "gender": {
        "description": "Customer gender (Male/Female)",
        "dtype":       "categorical",
        "required":    True,
        "aliases":     ["gender", "sex", "customer_gender"],
    },
    "item_purchased": {
        "description": "Name of the product bought",
        "dtype":       "text",
        "required":    True,
        "aliases":     ["item purchased", "item_purchased", "product", "product_name",
                        "item", "product purchased", "item_name"],
    },
    "category": {
        "description": "Product category (Clothing, Electronics, etc.)",
        "dtype":       "categorical",
        "required":    False,
        "aliases":     ["category", "product_category", "dept", "department", "cat"],
    },
    "purchase_amount": {
        "description": "Purchase value in USD (numeric)",
        "dtype":       "numeric",
        "required":    True,
        "aliases":     ["purchase amount (usd)", "purchase_amount", "amount", "price",
                        "sale_amount", "order_amount", "total", "revenue",
                        "discounted_price", "actual_price", "order_value"],
    },
    "location": {
        "description": "Customer location / state",
        "dtype":       "text",
        "required":    False,
        "aliases":     ["location", "state", "city", "region", "country", "address"],
    },
    "size": {
        "description": "Product size (S/M/L/XL)",
        "dtype":       "categorical",
        "required":    False,
        "aliases":     ["size", "product_size", "clothing_size"],
    },
    "color": {
        "description": "Product color",
        "dtype":       "categorical",
        "required":    False,
        "aliases":     ["color", "colour", "product_color"],
    },
    "season": {
        "description": "Season of purchase (Spring/Summer/Fall/Winter)",
        "dtype":       "categorical",
        "required":    False,
        "aliases":     ["season", "purchase_season", "quarter_season"],
    },
    "review_rating": {
        "description": "Customer review score (1–5)",
        "dtype":       "numeric",
        "required":    True,
        "aliases":     ["review rating", "review_rating", "rating", "score",
                        "stars", "customer_rating", "product_rating"],
    },
    "subscription_status": {
        "description": "Whether customer is subscribed (Yes/No)",
        "dtype":       "boolean_text",
        "required":    True,
        "aliases":     ["subscription status", "subscription_status", "subscribed",
                        "is_subscribed", "member", "membership"],
    },
    "shipping_type": {
        "description": "Shipping method used",
        "dtype":       "categorical",
        "required":    False,
        "aliases":     ["shipping type", "shipping_type", "delivery_type",
                        "shipping_method", "delivery_method"],
    },
    "discount_applied": {
        "description": "Whether a discount was used (Yes/No)",
        "dtype":       "boolean_text",
        "required":    False,
        "aliases":     ["discount applied", "discount_applied", "discount",
                        "promo_used", "coupon_used"],
    },
    "previous_purchases": {
        "description": "Number of past purchases (numeric)",
        "dtype":       "numeric",
        "required":    True,
        "aliases":     ["previous purchases", "previous_purchases", "purchase_count",
                        "num_purchases", "order_count", "total_orders",
                        "rating_count", "purchases"],
    },
    "payment_method": {
        "description": "How the customer paid",
        "dtype":       "categorical",
        "required":    False,
        "aliases":     ["payment method", "payment_method", "payment_type",
                        "payment", "pay_method"],
    },
    "frequency_of_purchases": {
        "description": "How often the customer buys (Weekly/Monthly/etc.)",
        "dtype":       "categorical",
        "required":    True,
        "aliases":     ["frequency of purchases", "frequency_of_purchases",
                        "purchase_frequency", "buy_frequency", "frequency",
                        "order_frequency"],
    },
}

REQUIRED_PIPELINE_COLS = {k for k, v in PIPELINE_SCHEMA.items() if v["required"]}


# ── Similarity helper ─────────────────────────────────────────
def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


# ── Detect column data type from actual values ────────────────
def _detect_dtype(series: pd.Series) -> str:
    sample = series.dropna().head(50)
    if sample.empty:
        return "unknown"

    # Try numeric
    try:
        pd.to_numeric(sample.str.replace(r"[$,%]", "", regex=True) if sample.dtype == object else sample)
        return "numeric"
    except Exception:
        pass

    if sample.dtype in [np.int64, np.float64, int, float]:
        return "numeric"

    unique_vals = set(str(v).strip().lower() for v in sample.unique())

    # Boolean-like
    bool_vals = {"yes", "no", "true", "false", "1", "0", "y", "n"}
    if unique_vals.issubset(bool_vals):
        return "boolean_text"

    # ID-like (all unique, looks like numbers or codes)
    if series.nunique() / max(len(series), 1) > 0.9:
        return "id"

    # Low cardinality = categorical
    if series.nunique() <= 20:
        return "categorical"

    return "text"


# ── Try to map one uploaded column to a pipeline column ──────
def _find_best_match(col_name: str, col_series: pd.Series) -> tuple[str | None, float]:
    col_lower    = col_name.lower().strip()
    detected_type = _detect_dtype(col_series)
    best_match   = None
    best_score   = 0.0

    for pipeline_col, meta in PIPELINE_SCHEMA.items():
        # Check exact alias match first
        if col_lower in [a.lower() for a in meta["aliases"]]:
            return pipeline_col, 1.0

        # Fuzzy match against all aliases
        for alias in meta["aliases"]:
            score = _similarity(col_lower, alias)
            # Boost score if data types also match
            if score > 0.6 and detected_type == meta["dtype"]:
                score = min(score + 0.15, 1.0)
            if score > best_score:
                best_score = score
                best_match = pipeline_col

    if best_score >= 0.65:
        return best_match, best_score
    return None, 0.0


# ── Main detection function ───────────────────────────────────
def detect_and_map(df: pd.DataFrame) -> dict:
    """
    Analyses an uploaded DataFrame and returns a full schema report:
    - column_map:   {uploaded_col -> pipeline_col} for confident matches
    - unmatched:    uploaded columns with no confident match
    - missing:      required pipeline columns with no match found
    - can_remap:    True if all required columns can be mapped
    - column_info:  detailed info about each uploaded column
    - confidence:   overall confidence score (0–1)
    """
    column_map  = {}   # uploaded_col  -> pipeline_col
    used_targets = set()
    column_info = {}

    # Analyse each uploaded column
    for col in df.columns:
        series    = df[col]
        dtype     = _detect_dtype(series)
        sample    = series.dropna().head(5).tolist()
        n_unique  = series.nunique()
        n_null    = series.isna().sum()

        column_info[col] = {
            "detected_type": dtype,
            "unique_values": n_unique,
            "null_count":    n_null,
            "sample":        [str(s) for s in sample],
        }

        match, score = _find_best_match(col, series)
        if match and match not in used_targets:
            column_map[col]  = {"maps_to": match, "confidence": round(score, 2)}
            used_targets.add(match)

    # Find which required pipeline columns are still missing
    mapped_targets = {v["maps_to"] for v in column_map.values()}
    missing_required = REQUIRED_PIPELINE_COLS - mapped_targets
    missing_optional = set(PIPELINE_SCHEMA.keys()) - REQUIRED_PIPELINE_COLS - mapped_targets

    # Unmatched uploaded columns
    unmatched = [c for c in df.columns if c not in column_map]

    can_remap   = len(missing_required) == 0
    confidence  = round(len(mapped_targets & REQUIRED_PIPELINE_COLS) / len(REQUIRED_PIPELINE_COLS), 2)

    return {
        "can_remap":        can_remap,
        "confidence":       confidence,
        "column_map":       column_map,
        "missing_required": sorted(missing_required),
        "missing_optional": sorted(missing_optional),
        "unmatched":        unmatched,
        "column_info":      column_info,
        "total_rows":       len(df),
        "total_cols":       len(df.columns),
    }


# ── Apply the mapping to rename columns ──────────────────────
def apply_column_map(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """Rename uploaded columns to pipeline column names based on detected mapping."""
    rename_dict = {col: info["maps_to"] for col, info in column_map.items()}
    return df.rename(columns=rename_dict)


# ── Human-readable summary for the UI ────────────────────────
def schema_report_for_ui(report: dict) -> dict:
    """Converts the raw report into a clean dict for rendering in the template."""
    mapped = []
    for col, info in report["column_map"].items():
        conf = info["confidence"]
        mapped.append({
            "from":       col,
            "to":         info["maps_to"],
            "confidence": conf,
            "badge":      "high" if conf >= 0.9 else "medium" if conf >= 0.7 else "low",
            "pct":        int(conf * 100),
        })

    return {
        "can_remap":        report["can_remap"],
        "confidence_pct":   int(report["confidence"] * 100),
        "mapped":           sorted(mapped, key=lambda x: -x["confidence"]),
        "missing_required": report["missing_required"],
        "missing_optional": report["missing_optional"],
        "unmatched":        report["unmatched"],
        "total_rows":       report["total_rows"],
        "total_cols":       report["total_cols"],
    }