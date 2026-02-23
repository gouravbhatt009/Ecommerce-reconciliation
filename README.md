# 🛍️ Myntra Seller Analytics Dashboard

A complete **Streamlit** dashboard for Myntra sellers to analyze sales, track settlements, and perform order-wise payment reconciliation.

## Features

| Tab | What it does |
|-----|-------------|
| 📊 Overview | KPIs, settlement calendar, payment mode split |
| 🔄 Payment Reconciliation | Order-wise PG Forward vs Sales sheet matching |
| 🛒 Sales Analysis | Order status, daily trend, article type revenue |
| ↩️ Returns Analysis | Return rate, type breakdown, SKU-level returns |
| 💳 Settlement Tracker | UTR-wise tracking, date-wise settlement amounts |
| 📦 SKU & Product | Top SKUs, high return SKUs, per-SKU P&L |
| 🌍 Geography | State-wise sales and returns |
| 💸 Charges Breakup | Commission, logistics, TCS/TDS per order |

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run myntra_app.py
```

## Uploading Files

When the app opens:
1. Use the **sidebar** to upload your 3 Myntra reports:
   - `PG Forward CSV` — Payment Gateway Forward (delivered orders)
   - `PG Reverse CSV` — Payment Gateway Reverse (returns)
   - `Sales Sheet XLSX/CSV` — Monthly sales report

2. Or click **"Use Sample Data"** if running with the sample Jan-26 files in the same folder.

## Files Expected

| File | Description |
|------|-------------|
| `PG_Forward_Jan-26.csv` | Forward PG report from Myntra seller portal |
| `PG_Reverse_Jan-26.csv` | Reverse PG report (returns/exchanges) |
| `Sales_Jan-26_-_Copy.xlsx` | Sales sheet from Myntra seller portal |

## Deploying on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set **Main file**: `myntra_app.py`
5. Deploy!

> Note: For Streamlit Cloud deployment, upload files via the sidebar (the local sample data path won't work on cloud).
