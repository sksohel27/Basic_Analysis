import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from utils import setup_logger, save_csv
from config import (
    RFM_QUANTILES, RFM_SEGMENT_MAP,
    FREQUENCY_MAP, AVG_CUSTOMER_LIFESPAN_YEARS, DISCOUNT_RATE,
    N_CLUSTERS, RANDOM_STATE, CLUSTER_NAMES,
    CHURN_MAX_PREV_PURCHASES, CHURN_SUBSCRIPTION_FLAG,
)

logger = setup_logger("feature_engineering")


# ── RFM Scoring ──────────────────────────────────────────────

def add_rfm_scores(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Calculating RFM scores...")

    freq_rank = {
        "Weekly": 7, "Bi-Weekly": 6, "Fortnightly": 6,
        "Monthly": 5, "Quarterly": 4, "Every 3 Months": 4,
        "Annually": 1,
    }
    df["recency_proxy"] = df["frequency_of_purchases"].map(freq_rank).fillna(3)

    df["r_score"] = pd.qcut(df["recency_proxy"],     q=RFM_QUANTILES, labels=False, duplicates="drop") + 1
    df["f_score"] = pd.qcut(df["previous_purchases"], q=RFM_QUANTILES, labels=False, duplicates="drop") + 1
    df["m_score"] = pd.qcut(df["purchase_amount"],    q=RFM_QUANTILES, labels=False, duplicates="drop") + 1

    for col in ["r_score", "f_score", "m_score"]:
        df[col] = df[col].fillna(3).astype(int)

    df["rfm_score"] = (
        df["r_score"].astype(str)
        + df["f_score"].astype(str)
        + df["m_score"].astype(str)
    )

    df["rfm_total"] = (
        df["r_score"] * 0.25
        + df["f_score"] * 0.30
        + df["m_score"] * 0.45
    ).round(2)

    df["rfm_segment"] = df["rfm_score"].map(RFM_SEGMENT_MAP).fillna(
        df["rfm_total"].apply(_fallback_segment)
    )

    dist = df["rfm_segment"].value_counts()
    logger.info(f"RFM segments distribution:\n{dist.to_string()}")
    return df


def _fallback_segment(score: float) -> str:
    if score >= 4.0:
        return "Champions"
    elif score >= 3.0:
        return "Loyal customers"
    elif score >= 2.0:
        return "Need attention"
    else:
        return "Lost"


# ── Customer Lifetime Value ───────────────────────────────────

def add_clv(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Calculating Customer Lifetime Value (CLV)...")

    df["annual_purchase_freq"] = df["frequency_of_purchases"].map(FREQUENCY_MAP).fillna(6)

    df["clv"] = (
        df["purchase_amount"]
        * df["annual_purchase_freq"]
        * AVG_CUSTOMER_LIFESPAN_YEARS
    ).round(2)

    df["clv_discounted"] = (
        df["purchase_amount"]
        * df["annual_purchase_freq"]
        * (1 - (1 / (1 + DISCOUNT_RATE) ** AVG_CUSTOMER_LIFESPAN_YEARS))
        / DISCOUNT_RATE
    ).round(2)

    clv_pcts = df["clv"].quantile([0.33, 0.66])
    df["clv_tier"] = pd.cut(
        df["clv"],
        bins=[-np.inf, clv_pcts[0.33], clv_pcts[0.66], np.inf],
        labels=["Low value", "Mid value", "High value"],
    )

    logger.info(
        f"CLV stats — min: ${df['clv'].min():.0f} | "
        f"avg: ${df['clv'].mean():.0f} | "
        f"max: ${df['clv'].max():.0f}"
    )
    return df


# ── Churn Risk Flag ───────────────────────────────────────────

def add_churn_flag(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Calculating churn risk flags...")

    low_purchases  = df["previous_purchases"] <= CHURN_MAX_PREV_PURCHASES
    no_sub         = df["subscription_status"].str.strip().str.title() == CHURN_SUBSCRIPTION_FLAG.title()
    low_frequency  = df["frequency_of_purchases"].isin(["Annually", "Every 3 Months", "Quarterly"])
    low_rating     = df["review_rating"] < 3.0
    low_spend      = df["purchase_amount"] < df["purchase_amount"].quantile(0.25)

    df["churn_risk_score"] = (
        low_purchases.astype(int)
        + no_sub.astype(int)
        + low_frequency.astype(int)
        + low_rating.astype(int)
        + low_spend.astype(int)
    )

    df["churn_risk"] = pd.cut(
        df["churn_risk_score"],
        bins=[-1, 1, 3, 5],
        labels=["Low", "Medium", "High"],
    )

    high_risk = (df["churn_risk"] == "High").sum()
    logger.info(f"High churn risk customers: {high_risk:,} ({high_risk/len(df)*100:.1f}%)")
    return df


# ── KMeans Customer Segmentation ─────────────────────────────

def add_kmeans_segments(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Running KMeans clustering with k={N_CLUSTERS}...")

    features = ["purchase_amount", "previous_purchases", "review_rating", "rfm_total"]
    X = df[features].fillna(0)

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    df["cluster_id"] = km.fit_predict(X_scaled)

    cluster_spend = (
        df.groupby("cluster_id")["purchase_amount"].mean().sort_values()
    )
    spend_rank = {cid: rank for rank, cid in enumerate(cluster_spend.index)}

    df["customer_segment"] = df["cluster_id"].map(
        {cid: CLUSTER_NAMES.get(spend_rank[cid], f"Segment {cid}") for cid in df["cluster_id"].unique()}
    )

    dist = df["customer_segment"].value_counts()
    logger.info(f"Cluster distribution:\n{dist.to_string()}")
    return df


# ── Main ─────────────────────────────────────────────────────

def run_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = add_rfm_scores(df)
    df = add_clv(df)
    df = add_churn_flag(df)
    df = add_kmeans_segments(df)
    save_csv(df, "02_featured_data.csv", logger)
    logger.info("✔ Feature engineering complete")
    return df


if __name__ == "__main__":
    from data_cleaning import run_cleaning
    df = run_cleaning()
    run_feature_engineering(df)