# BizAnalytics — Customer Behaviour Web App

A production Flask web application that wraps your data pipeline into a shareable dashboard.

## Features
- **Login system** — email + password auth
- **CSV upload** — drag & drop, runs full pipeline on upload
- **Demo mode** — one click to run the bundled sample dataset
- **Live dashboard** — 6 charts + KPI cards + top customers table
- **No SQL Server needed** — runs entirely in-memory (PostgreSQL optional for prod)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://localhost:5000
```

## Demo Login
- Email: `admin@bizanalytics.com`
- Password: `admin123`

## Deploy to Render (free hosting)
1. Push this folder to a GitHub repo
2. Go to render.com → New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Done — live URL in ~2 minutes

## File Structure
```
inventory_app/
├── app.py                  ← Flask app (routes, auth, pipeline glue)
├── config.py               ← Settings (RFM rules, CLV constants)
├── data_cleaning.py        ← Step 1: clean CSV
├── feature_engineering.py  ← Step 2: RFM, CLV, churn, KMeans
├── utils.py                ← Logging helpers
├── requirements.txt
├── customer_shopping_behavior.csv  ← Demo dataset
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   └── upload.html
└── uploads/                ← Created automatically
```

## To Add Real Authentication (production)
Replace the `USERS` dict in `app.py` with a proper database:
```python
# Use Flask-SQLAlchemy + Flask-Login
# pip install flask-sqlalchemy flask-login
```
