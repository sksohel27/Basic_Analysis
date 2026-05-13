import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ── App setup ────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod-" + str(uuid.uuid4()))

# FIX 1: Use /tmp for writes — Vercel filesystem is read-only
OUTPUT_FOLDER = Path("/tmp/outputs")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# FIX 2: Absolute base path so CSV is always found on Vercel
BASE_DIR = Path(__file__).parent.resolve()

@app.template_filter("format_number")
def format_number(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return value

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Demo users ───────────────────────────────────────────────
USERS = {
    "admin@bizanalytics.com": {
        "name": "Admin",
        "password": generate_password_hash("admin123"),
        "role": "admin",
    },
    "jinat@bizanalytics.com": {
        "name": "Jinat",
        "password": generate_password_hash("jinat123"),
        "role": "analyst",
    },
}


# ── Auth helpers ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Pipeline ─────────────────────────────────────────────────
def run_pipeline_on_df(df: pd.DataFrame) -> pd.DataFrame:
    """Run cleaning + feature engineering in memory."""
    from data_cleaning import (
        standardise_columns, fix_categories,
        handle_nulls, remove_duplicates
    )
    from feature_engineering import (
        add_rfm_scores, add_clv, add_churn_flag, add_kmeans_segments
    )
    df = standardise_columns(df)
    df = fix_categories(df)
    df = handle_nulls(df)
    df = remove_duplicates(df)
    df = add_rfm_scores(df)
    df = add_clv(df)
    df = add_churn_flag(df)
    df = add_kmeans_segments(df)
    return df


def compute_analytics(df: pd.DataFrame) -> dict:
    """Compute all KPIs and chart data from the enriched DataFrame."""
    total_customers = len(df)
    total_revenue   = round(df["purchase_amount"].sum(), 2)
    avg_clv         = round(df["clv"].mean(), 2)
    high_churn_pct  = round((df["churn_risk"] == "High").sum() / total_customers * 100, 1)

    rfm_dist = df["rfm_segment"].value_counts().head(8)
    rfm_chart = {"labels": rfm_dist.index.tolist(), "values": rfm_dist.values.tolist()}

    clv_tier = df.groupby("clv_tier", observed=True)["clv"].mean().round(2)
    clv_chart = {"labels": clv_tier.index.astype(str).tolist(), "values": clv_tier.values.tolist()}

    churn_dist = df["churn_risk"].value_counts()
    churn_chart = {"labels": churn_dist.index.astype(str).tolist(), "values": churn_dist.values.tolist()}

    cat_rev = df.groupby("category")["purchase_amount"].sum().sort_values(ascending=False)
    category_chart = {"labels": cat_rev.index.tolist(), "values": cat_rev.round(2).values.tolist()}

    seg_dist = df["customer_segment"].value_counts()
    segment_chart = {"labels": seg_dist.index.tolist(), "values": seg_dist.values.tolist()}

    age_bins = pd.cut(df["age"], bins=[0, 25, 35, 45, 55, 100],
                      labels=["18-25", "26-35", "36-45", "46-55", "55+"])
    age_dist = age_bins.value_counts().sort_index()
    age_chart = {"labels": age_dist.index.astype(str).tolist(), "values": age_dist.values.tolist()}

    top_customers = (
        df.nlargest(10, "clv")[
            ["customer_id", "age", "gender", "clv", "rfm_segment",
             "churn_risk", "customer_segment", "purchase_amount"]
        ]
        .round(2)
        .to_dict("records")
    )

    freq_dist = df["frequency_of_purchases"].value_counts()
    freq_chart = {"labels": freq_dist.index.tolist(), "values": freq_dist.values.tolist()}

    return {
        "kpis": {
            "total_customers": f"{total_customers:,}",
            "total_revenue":   f"${total_revenue:,.0f}",
            "avg_clv":         f"${avg_clv:,.0f}",
            "high_churn_pct":  f"{high_churn_pct}%",
        },
        "charts": {
            "rfm":      rfm_chart,
            "clv":      clv_chart,
            "churn":    churn_chart,
            "category": category_chart,
            "segment":  segment_chart,
            "age":      age_chart,
            "frequency": freq_chart,
        },
        "top_customers": top_customers,
        "row_count": total_customers,
        "processed_at": datetime.now().strftime("%d %b %Y, %H:%M"),
    }


# ── Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user     = USERS.get(email)

        if user and check_password_hash(user["password"], password):
            session["user"]  = email
            session["name"]  = user["name"]
            session["role"]  = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    analytics = session.get("analytics")
    return render_template(
        "dashboard.html",
        user_name=session["name"],
        analytics=analytics,
    )


@app.route("/run-demo")
@login_required
def run_demo():
    """Run the pipeline on the bundled sample dataset."""
    # FIX 3: Use absolute path to find the CSV
    demo_path = BASE_DIR / "customer_shopping_behavior.csv"
    if not demo_path.exists():
        flash("Demo dataset not found.", "error")
        return redirect(url_for("dashboard"))

    try:
        df = pd.read_csv(demo_path)
        df = run_pipeline_on_df(df)
        analytics = compute_analytics(df)

        # FIX 4: Sanitize before storing in session (avoid non-serializable types)
        analytics = json.loads(json.dumps(analytics, default=str))
        session["analytics"] = analytics

        # FIX 5: Write to /tmp instead of local outputs folder
        out_path = OUTPUT_FOLDER / "demo_enriched.csv"
        try:
            df.to_csv(out_path, index=False)
            session["enriched_file"] = str(out_path)
        except (OSError, PermissionError):
            pass  # Non-critical: skip file save if filesystem is restricted

        flash(f"✔ Demo pipeline complete — {analytics['row_count']:,} customers processed.", "success")
    except Exception as e:
        logger.exception("Demo pipeline error")
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for("dashboard"))


@app.route("/api/analytics")
@login_required
def api_analytics():
    analytics = session.get("analytics")
    if not analytics:
        return jsonify({"error": "No data processed yet"}), 404
    return jsonify(analytics)


# FIX 6: Only run dev server when called directly — not on Vercel import
if __name__ == "__main__":
    app.run(debug=True, port=5000)