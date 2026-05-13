import pandas as pd
from utils import setup_logger, save_csv
from config import RAW_DATA

logger = setup_logger("data_cleaning")

CORRECT_CATEGORY_MAP = {
    "T-shirt": "Clothing", "Shirt": "Clothing", "Shorts": "Clothing",
    "Hoodie": "Clothing", "Pants": "Clothing", "Socks": "Clothing",
    "Jeans": "Clothing", "Blouse": "Clothing", "Skirt": "Clothing",
    "Sweater": "Clothing", "Dress": "Clothing",
    "Sunglasses": "Accessories", "Gloves": "Accessories",
    "Jewelry": "Accessories", "Hat": "Accessories",
    "Handbag": "Accessories", "Backpack": "Accessories",
    "Belt": "Accessories", "Scarf": "Accessories", "Bag": "Accessories",
    "Laptop": "Electronics", "Phone": "Electronics",
    "Headphones": "Electronics", "Watch": "Electronics",
    "Shoes": "Footwear", "Sandals": "Footwear",
    "Sneakers": "Footwear", "Boots": "Footwear",
    "Coat": "Outerwear", "Jacket": "Outerwear",
}


def load_raw(path: str = RAW_DATA) -> pd.DataFrame:
    logger.info(f"Loading raw data from: {path}")
    df = pd.read_csv(path)
    logger.info(f"Raw shape: {df.shape}")
    return df


def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\(\)\/]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.rstrip("_")
    )
    df = df.rename(columns={"purchase_amount_usd": "purchase_amount"})
    logger.info(f"Columns standardised: {list(df.columns)}")
    return df


def fix_categories(df: pd.DataFrame) -> pd.DataFrame:
    df["category"] = df["item_purchased"].map(CORRECT_CATEGORY_MAP)
    unmapped = df["category"].isna().sum()
    if unmapped:
        logger.warning(f"{unmapped} items had no category mapping — filled as 'Other'")
        df["category"] = df["category"].fillna("Other")
    return df


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    before = df.isnull().sum().sum()

    df.loc[df["category"] == "Electronics", "size"] = "Not Applicable"
    df.loc[df["category"] == "Accessories", "size"] = "Free Size"
    df.loc[df["category"] == "Footwear",    "size"] = "Numeric"

    clothing_mode = (
        df.loc[df["category"] == "Clothing", "size"].mode()[0]
        if df.loc[df["category"] == "Clothing", "size"].notna().any()
        else "M"
    )
    df.loc[(df["category"] == "Clothing") & df["size"].isna(), "size"] = clothing_mode

    df["review_rating"] = df["review_rating"].fillna(
        df.groupby("item_purchased")["review_rating"].transform("mean")
    ).round(2)

    df["purchase_amount"] = df["purchase_amount"].fillna(
        df.groupby("item_purchased")["purchase_amount"].transform("mean")
    ).round(2)

    df["previous_purchases"] = df["previous_purchases"].fillna(0).astype(int)

    after = df.isnull().sum().sum()
    logger.info(f"Nulls resolved: {before} → {after}")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first").reset_index(drop=True)
    logger.info(f"Duplicates removed: {before - len(df)} rows. Clean shape: {df.shape}")
    return df


def run_cleaning() -> pd.DataFrame:
    df = load_raw()
    df = standardise_columns(df)
    df = fix_categories(df)
    df = handle_nulls(df)
    df = remove_duplicates(df)
    save_csv(df, "01_cleaned_data.csv", logger)
    logger.info("✔ Cleaning complete")
    return df


if __name__ == "__main__":
    run_cleaning()