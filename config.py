import os

# ── Base directory (absolute, works on Vercel) ───────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Paths (use /tmp for writes — Vercel filesystem is read-only) ──
RAW_DATA   = os.path.join(BASE_DIR, "customer_shopping_behavior.csv")
LOG_DIR    = "/tmp/logs"
OUTPUT_DIR = "/tmp/outputs"

# ── SQL Server (local only — not used on Vercel) ─────────────
SQL_SERVER   = os.environ.get("SQL_SERVER",   "localhost")
SQL_DATABASE = os.environ.get("SQL_DATABASE", "data_analysis_project")
SQL_DRIVER   = os.environ.get("SQL_DRIVER",   "ODBC Driver 17 for SQL Server")
SQL_TABLE    = "customer_behaviour_analysis"

# ── RFM config ───────────────────────────────────────────────
RFM_QUANTILES = 5

RFM_SEGMENT_MAP = {
    # Champions
    "555": "Champions", "554": "Champions", "544": "Champions",
    "545": "Champions", "454": "Champions", "455": "Champions",
    "445": "Champions",
    # Loyal customers
    "543": "Loyal customers", "444": "Loyal customers",
    "435": "Loyal customers", "355": "Loyal customers",
    "354": "Loyal customers", "345": "Loyal customers",
    "344": "Loyal customers", "335": "Loyal customers",
    # Potential loyalist
    "553": "Potential loyalist", "551": "Potential loyalist",
    "552": "Potential loyalist", "541": "Potential loyalist",
    "542": "Potential loyalist", "533": "Potential loyalist",
    "532": "Potential loyalist", "531": "Potential loyalist",
    "452": "Potential loyalist", "451": "Potential loyalist",
    "442": "Potential loyalist", "441": "Potential loyalist",
    "431": "Potential loyalist", "453": "Potential loyalist",
    "433": "Potential loyalist", "432": "Potential loyalist",
    "423": "Potential loyalist", "353": "Potential loyalist",
    "352": "Potential loyalist", "351": "Potential loyalist",
    "342": "Potential loyalist", "341": "Potential loyalist",
    "333": "Potential loyalist", "323": "Potential loyalist",
    # Recent customers
    "512": "Recent customers", "511": "Recent customers",
    "422": "Recent customers", "421": "Recent customers",
    "412": "Recent customers", "411": "Recent customers",
    "311": "Recent customers",
    # Promising
    "525": "Promising", "524": "Promising", "523": "Promising",
    "522": "Promising", "521": "Promising", "515": "Promising",
    "514": "Promising", "513": "Promising", "425": "Promising",
    "424": "Promising", "413": "Promising", "414": "Promising",
    "415": "Promising", "315": "Promising", "314": "Promising",
    "313": "Promising",
    # Need attention
    "535": "Need attention", "534": "Need attention",
    "443": "Need attention", "434": "Need attention",
    "343": "Need attention", "334": "Need attention",
    "325": "Need attention", "324": "Need attention",
    # About to sleep
    "331": "About to sleep", "321": "About to sleep",
    "312": "About to sleep", "221": "About to sleep",
    "213": "About to sleep", "231": "About to sleep",
    "241": "About to sleep", "251": "About to sleep",
    # At risk
    "255": "At risk", "254": "At risk", "245": "At risk",
    "244": "At risk", "253": "At risk", "252": "At risk",
    "243": "At risk", "242": "At risk", "235": "At risk",
    "234": "At risk", "225": "At risk", "224": "At risk",
    "153": "At risk", "152": "At risk", "145": "At risk",
    "143": "At risk", "142": "At risk", "135": "At risk",
    "134": "At risk", "133": "At risk", "125": "At risk",
    "124": "At risk",
    # Cannot lose them
    "155": "Cannot lose them", "154": "Cannot lose them",
    "144": "Cannot lose them", "214": "Cannot lose them",
    "215": "Cannot lose them", "115": "Cannot lose them",
    "114": "Cannot lose them", "113": "Cannot lose them",
    # Hibernating
    "332": "Hibernating", "322": "Hibernating",
    "233": "Hibernating", "232": "Hibernating",
    "223": "Hibernating", "222": "Hibernating",
    "132": "Hibernating", "123": "Hibernating",
    "122": "Hibernating", "212": "Hibernating",
    "211": "Hibernating",
    # Lost
    "111": "Lost", "112": "Lost", "121": "Lost",
    "131": "Lost", "141": "Lost", "151": "Lost",
}

# ── Frequency mapping (purchases per year) ───────────────────
FREQUENCY_MAP = {
    "Weekly":          52,
    "Bi-Weekly":       26,
    "Fortnightly":     26,
    "Monthly":         12,
    "Quarterly":        4,
    "Every 3 Months":   4,
    "Annually":         1,
}

# ── CLV config ───────────────────────────────────────────────
AVG_CUSTOMER_LIFESPAN_YEARS = 3
DISCOUNT_RATE               = 0.10   # 10% annual discount rate

# ── KMeans config ────────────────────────────────────────────
N_CLUSTERS   = 4
RANDOM_STATE = 42
CLUSTER_NAMES = {
    0: "Budget shoppers",
    1: "Mid-tier buyers",
    2: "High spenders",
    3: "Premium customers",
}

# ── Churn config ─────────────────────────────────────────────
CHURN_MAX_PREV_PURCHASES = 3
CHURN_SUBSCRIPTION_FLAG  = "No"