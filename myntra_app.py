"""
Myntra Seller Analytics & Payment Reconciliation Dashboard
Brand: Sangria | January 2026
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Myntra Seller Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS — Clean professional dark-accent theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d1b2a 100%);
    padding: 28px 32px; border-radius: 16px; margin-bottom: 24px;
    border: 1px solid rgba(255,160,80,0.2);
    position: relative; overflow: hidden;
}
.main-header::before {
    content: ''; position: absolute; top: -50%; right: -10%;
    width: 400px; height: 400px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,140,50,0.08) 0%, transparent 70%);
}
.main-header h1 { color: #fff; font-size: 1.8rem; font-weight: 700; margin: 0; }
.main-header p  { color: rgba(255,255,255,0.6); margin: 4px 0 0; font-size: 0.9rem; }
.badge {
    display: inline-block; background: rgba(255,140,50,0.15);
    color: #ffa040; border: 1px solid rgba(255,140,50,0.3);
    padding: 2px 10px; border-radius: 20px; font-size: 0.75rem;
    font-weight: 600; letter-spacing: 0.5px; margin-top: 8px;
}

.kpi-card {
    background: #fff; border: 1px solid #eee;
    border-radius: 12px; padding: 20px 22px;
    border-top: 3px solid #ff6b35;
}
.kpi-card.blue  { border-top-color: #3b82f6; }
.kpi-card.green { border-top-color: #10b981; }
.kpi-card.red   { border-top-color: #ef4444; }
.kpi-card.purple{ border-top-color: #8b5cf6; }
.kpi-card.orange{ border-top-color: #f59e0b; }
.kpi-label { font-size: 0.75rem; color: #888; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { font-size: 1.7rem; font-weight: 700; color: #111; margin: 4px 0 0; font-family: 'DM Mono'; }
.kpi-sub   { font-size: 0.78rem; color: #aaa; margin-top: 2px; }

.section-title {
    font-size: 1rem; font-weight: 700; color: #111;
    padding: 10px 0; border-bottom: 2px solid #f0f0f0;
    margin-bottom: 16px;
}
.recon-match   { background: #f0fdf4; border-left: 4px solid #10b981; padding: 10px 14px; border-radius: 4px; margin: 4px 0; }
.recon-mismatch{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 10px 14px; border-radius: 4px; margin: 4px 0; }
.recon-pending { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 10px 14px; border-radius: 4px; margin: 4px 0; }
.info-chip {
    display: inline-block; background: #f3f4f6; color: #374151;
    padding: 3px 10px; border-radius: 6px; font-size: 0.8rem;
    font-weight: 500; margin: 2px;
}

stTabs [data-baseweb="tab-list"] { gap: 4px; }
stTabs [data-baseweb="tab"] {
    font-weight: 600; font-size: 0.85rem;
    padding: 8px 18px; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def to_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, index=False)
    return buf.getvalue()

def fmt_inr(val):
    try: return f"₹{float(val):,.2f}"
    except: return "₹0.00"

def fmt_num(val):
    try: return f"{int(val):,}"
    except: return "0"

def safe_num(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

# ─────────────────────────────────────────────
# Helper: coerce numeric columns
# ─────────────────────────────────────────────
MONEY_COLS_PG = [
    'seller_product_amount','mrp','total_discount_amount','total_commission',
    'total_logistics_deduction','total_expected_settlement','total_actual_settlement',
    'amount_pending_settlement','prepaid_amount','postpaid_amount',
    'tcs_amount','tds_amount','commission_percentage','platform_fees',
    'shipping_fee','customer_paid_amt','taxable_amount',
    'prepaid_payment','postpaid_payment',
    'total_commission_plus_tcs_tds_deduction'
]
MONEY_COLS_SALES = [
    'invoiceamount','shipment_value','base_value','seller_price','mrp',
    'discount','tax_amount','tcs_amount','tds_amount','net_amount'
]

def coerce_df(df, money_cols):
    for c in money_cols:
        if c in df.columns:
            df[c] = safe_num(df[c])
    if 'packet_id' in df.columns:
        df['packet_id'] = df['packet_id'].astype(str)
    return df

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🛍️ Myntra Seller Analytics Dashboard</h1>
  <p>Payment Gateway Reconciliation · Sales Analysis · Returns · Settlement Tracking</p>
  <span class="badge">BRAND: SANGRIA · JAN 2026</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar — file upload (always shown)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Data Files")
    st.markdown("Upload your Myntra PG reports and Sales sheet:")
    up_fwd   = st.file_uploader("PG Forward (Sales) CSV",   type=["csv"])
    up_rev   = st.file_uploader("PG Reverse (Returns) CSV", type=["csv"])
    up_sales = st.file_uploader("Sales Sheet (XLSX/CSV)",   type=["xlsx","csv","xls"])
    st.markdown("---")
    st.markdown("**About this Dashboard**")
    st.caption("Analyzes Myntra PG Forward/Reverse reports with Sales data for order-wise payment reconciliation.")

# ─────────────────────────────────────────────
# Load — only from uploads, no local fallback
# ─────────────────────────────────────────────
if not (up_fwd and up_rev and up_sales):
    st.info(
        "👈 **Please upload all three files in the sidebar to get started:**\n\n"
        "1. **PG Forward (Sales) CSV** — your `PG_Forward_*.csv`\n"
        "2. **PG Reverse (Returns) CSV** — your `PG_Reverse_*.csv`\n"
        "3. **Sales Sheet** — your `Sales_*.xlsx` or `.csv`"
    )
    st.stop()

def read_excel_safe(file):
    """Try openpyxl first, then xlrd, then ask user to convert to CSV."""
    fname = file.name.lower()
    if not fname.endswith(('.xlsx', '.xls')):
        return pd.read_csv(file)
    # Try openpyxl (for .xlsx)
    try:
        import openpyxl  # noqa
        file.seek(0)
        return pd.read_excel(file, engine='openpyxl')
    except ImportError:
        pass
    # Try xlrd (older .xls support)
    try:
        import xlrd  # noqa
        file.seek(0)
        return pd.read_excel(file, engine='xlrd')
    except ImportError:
        pass
    # Both missing — give user a clear action
    st.error(
        "❌ **Cannot read the Excel file** — neither `openpyxl` nor `xlrd` is installed "
        "in this environment.\n\n"
        "**Quick fix:** Open your Sales sheet in Excel, go to **File → Save As → CSV (.csv)**, "
        "then re-upload the CSV version instead."
    )
    st.stop()

try:
    pg_fwd = coerce_df(pd.read_csv(up_fwd), MONEY_COLS_PG)
    pg_rev = coerce_df(pd.read_csv(up_rev), MONEY_COLS_PG)
    sales  = coerce_df(read_excel_safe(up_sales), MONEY_COLS_SALES)
    pg_fwd['_type'] = 'Forward'
    pg_rev['_type'] = 'Return'
except SystemExit:
    raise
except Exception as e:
    st.error(f"❌ Error reading uploaded files: {e}")
    st.stop()

# ─────────────────────────────────────────────
# Settlement date columns
# ─────────────────────────────────────────────
SETTLE_COLS = [c for c in pg_fwd.columns if 'Settlement_on_2026' in c]
for c in SETTLE_COLS:
    pg_fwd[c] = safe_num(pg_fwd[c])
    pg_rev[c] = safe_num(pg_rev[c])

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tabs = st.tabs([
    "📊 Overview",
    "🔄 Payment Reconciliation",
    "🛒 Sales Analysis",
    "↩️ Returns Analysis",
    "💳 Settlement Tracker",
    "📦 SKU & Product",
    "🌍 Geography",
    "💸 Charges Breakup",
    "✅ Order Settlement Checker",
])
(t_overview, t_recon, t_sales, t_returns,
 t_settle, t_sku, t_geo, t_charges, t_checker) = tabs

# ══════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════
with t_overview:
    st.markdown('<div class="section-title">📊 January 2026 — Business Summary</div>', unsafe_allow_html=True)

    # KPI Row 1
    k1,k2,k3,k4,k5 = st.columns(5)
    total_orders   = len(pg_fwd)
    total_returns  = len(pg_rev)
    return_rate    = total_returns / total_orders * 100
    gmv            = pg_fwd['mrp'].sum()
    net_revenue    = pg_fwd['seller_product_amount'].sum()

    with k1:
        st.markdown(f"""<div class="kpi-card blue">
        <div class="kpi-label">Forward Orders</div>
        <div class="kpi-value">{fmt_num(total_orders)}</div>
        <div class="kpi-sub">Dispatched & Delivered</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card red">
        <div class="kpi-label">Total Returns</div>
        <div class="kpi-value">{fmt_num(total_returns)}</div>
        <div class="kpi-sub">Return rate: {return_rate:.1f}%</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card orange">
        <div class="kpi-label">Gross MRP Value</div>
        <div class="kpi-value">₹{gmv/100000:.2f}L</div>
        <div class="kpi-sub">Total MRP dispatched</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Seller Revenue</div>
        <div class="kpi-value">₹{net_revenue/100000:.2f}L</div>
        <div class="kpi-sub">After Myntra discount</div></div>""", unsafe_allow_html=True)
    with k5:
        net_settle = pg_fwd['total_actual_settlement'].sum() + pg_rev['total_actual_settlement'].sum()
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Net Settlement</div>
        <div class="kpi-value">₹{net_settle/100000:.2f}L</div>
        <div class="kpi-sub">Forward - Returns</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # KPI Row 2
    k6,k7,k8,k9,k10 = st.columns(5)
    fwd_settle    = pg_fwd['total_actual_settlement'].sum()
    rev_settle    = pg_rev['total_actual_settlement'].sum()
    total_comm    = pg_fwd['total_commission'].abs().sum()
    total_logist  = pg_fwd['total_logistics_deduction'].abs().sum()
    avg_order_val = pg_fwd['seller_product_amount'].mean()

    with k6:
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Forward Settlement</div>
        <div class="kpi-value">₹{fwd_settle/100000:.2f}L</div>
        <div class="kpi-sub">Received from Myntra</div></div>""", unsafe_allow_html=True)
    with k7:
        st.markdown(f"""<div class="kpi-card red">
        <div class="kpi-label">Return Deductions</div>
        <div class="kpi-value">₹{abs(rev_settle)/100000:.2f}L</div>
        <div class="kpi-sub">Money reclaimed by Myntra</div></div>""", unsafe_allow_html=True)
    with k8:
        st.markdown(f"""<div class="kpi-card purple">
        <div class="kpi-label">Commission Charged</div>
        <div class="kpi-value">₹{total_comm/100000:.2f}L</div>
        <div class="kpi-sub">Avg {pg_fwd['commission_percentage'].mean():.1f}%</div></div>""", unsafe_allow_html=True)
    with k9:
        st.markdown(f"""<div class="kpi-card orange">
        <div class="kpi-label">Logistics Charged</div>
        <div class="kpi-value">₹{total_logist/1000:.1f}K</div>
        <div class="kpi-sub">Shipping + fees</div></div>""", unsafe_allow_html=True)
    with k10:
        st.markdown(f"""<div class="kpi-card blue">
        <div class="kpi-label">Avg Order Value</div>
        <div class="kpi-value">{fmt_inr(avg_order_val)}</div>
        <div class="kpi-sub">Seller price per order</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">📦 Article Type Mix (Forward)</div>', unsafe_allow_html=True)
        art = pg_fwd['article_type'].value_counts().reset_index()
        art.columns = ['Article Type','Orders']
        art['Revenue (₹)'] = art['Article Type'].map(
            pg_fwd.groupby('article_type')['seller_product_amount'].sum().round(2))
        st.dataframe(art, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown('<div class="section-title">📬 Payment Mode Split</div>', unsafe_allow_html=True)
        prepaid_orders  = (pg_fwd['prepaid_amount']  > 0).sum()
        postpaid_orders = (pg_fwd['postpaid_amount'] > 0).sum()
        prepaid_val     = pg_fwd['prepaid_amount'].sum()
        postpaid_val    = pg_fwd['postpaid_amount'].sum()
        pay_df = pd.DataFrame({
            'Mode':    ['Prepaid (Online)', 'Postpaid (COD)'],
            'Orders':  [prepaid_orders, postpaid_orders],
            'Value (₹)': [f"{prepaid_val:,.2f}", f"{postpaid_val:,.2f}"],
            'Share %': [f"{prepaid_orders/total_orders*100:.1f}%", f"{postpaid_orders/total_orders*100:.1f}%"]
        })
        st.dataframe(pay_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">🗓️ Settlement by Date</div>', unsafe_allow_html=True)
    settle_summary = []
    for c in SETTLE_COLS:
        dt = c.replace('Settlement_on_','').replace('_','-')
        fwd_amt = pg_fwd[c].sum()
        rev_amt = pg_rev[c].sum() if c in pg_rev.columns else 0
        if fwd_amt != 0 or rev_amt != 0:
            settle_summary.append({'Date': dt, 'Forward (₹)': round(fwd_amt,2),
                                   'Return Deduction (₹)': round(rev_amt,2),
                                   'Net (₹)': round(fwd_amt+rev_amt,2)})
    if settle_summary:
        sdf = pd.DataFrame(settle_summary)
        st.dataframe(sdf, use_container_width=True, hide_index=True)
        # Bar chart
        st.bar_chart(sdf.set_index('Date')[['Forward (₹)','Return Deduction (₹)']])

# ══════════════════════════════════════════════
# TAB 2 — PAYMENT RECONCILIATION
# ══════════════════════════════════════════════
with t_recon:
    st.markdown('<div class="section-title">🔄 Order-wise Payment Reconciliation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-chip">Reconciles PG Forward report vs Sales sheet by packet_id. '
        'Flags matched, mismatched and missing records.</div><br>',
        unsafe_allow_html=True
    )

    # Build reconciliation: match PG Forward ↔ Sales by packet_id
    fwd_recon = pg_fwd[[
        'packet_id','order_release_id','invoice_number','sku_code',
        'seller_product_amount','mrp','total_discount_amount',
        'prepaid_amount','postpaid_amount',
        'total_commission','total_logistics_deduction',
        'total_expected_settlement','total_actual_settlement',
        'amount_pending_settlement','tcs_amount','tds_amount',
        'commission_percentage','bank_utr_no_prepaid_payment',
        'bank_utr_no_postpaid_payment','article_type'
    ]].copy()
    fwd_recon.columns = ['packet_id','order_release_id','invoice_number','sku',
        'seller_amount','mrp','discount',
        'prepaid_amt','postpaid_amt',
        'commission','logistics',
        'expected_settlement','actual_settlement',
        'pending_settlement','tcs','tds',
        'commission_pct','utr_prepaid','utr_postpaid','article_type']

    sales_recon = sales[[
        'packet_id','order_id','SKU','payment_method',
        'invoiceamount','shipment_value','mrp','discount',
        'tax_amount','tcs_amount','tds_amount'
    ]].copy() if all(c in sales.columns for c in ['packet_id','order_id','SKU','payment_method','invoiceamount']) else pd.DataFrame()

    if not sales_recon.empty:
        sales_recon.columns = ['packet_id','order_id','sku_sales','payment_method',
            'invoice_amount','shipment_value','mrp_sales','discount_sales',
            'tax_amount','tcs_sales','tds_sales']
        merged = fwd_recon.merge(sales_recon, on='packet_id', how='outer', indicator=True)
    else:
        merged = fwd_recon.copy()
        merged['_merge'] = 'left_only'

    # Classify
    def classify(row):
        if row.get('_merge','left_only') == 'both':
            if 'invoice_amount' in row and abs(safe_num(pd.Series([row['seller_amount']])).values[0] -
               safe_num(pd.Series([row.get('invoice_amount',0)])).values[0]) < 2:
                return '✅ Matched'
            else:
                return '⚠️ Amount Mismatch'
        elif row.get('_merge','left_only') == 'left_only':
            if safe_num(pd.Series([row.get('pending_settlement',0)])).values[0] > 0:
                return '🕐 PG Only – Settlement Pending'
            return '✅ PG Only – Settled'
        else:
            return '❓ Sales Only – Not in PG'

    merged['Recon_Status'] = merged.apply(classify, axis=1)

    # Summary
    status_counts = merged['Recon_Status'].value_counts()
    rc1,rc2,rc3,rc4 = st.columns(4)
    matched   = status_counts.get('✅ Matched',0) + status_counts.get('✅ PG Only – Settled',0)
    mismatch  = status_counts.get('⚠️ Amount Mismatch',0)
    pending   = status_counts.get('🕐 PG Only – Settlement Pending',0)
    sales_only= status_counts.get('❓ Sales Only – Not in PG',0)

    rc1.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Matched / Settled</div>
        <div class="kpi-value">{matched}</div></div>""", unsafe_allow_html=True)
    rc2.markdown(f"""<div class="kpi-card orange">
        <div class="kpi-label">Amount Mismatch</div>
        <div class="kpi-value">{mismatch}</div></div>""", unsafe_allow_html=True)
    rc3.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Settlement Pending</div>
        <div class="kpi-value">{pending}</div></div>""", unsafe_allow_html=True)
    rc4.markdown(f"""<div class="kpi-card red">
        <div class="kpi-label">Sales Not in PG</div>
        <div class="kpi-value">{sales_only}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filter
    filt_status = st.multiselect("Filter by Reconciliation Status",
        merged['Recon_Status'].unique().tolist(),
        default=merged['Recon_Status'].unique().tolist())
    filtered_recon = merged[merged['Recon_Status'].isin(filt_status)].copy()

    # Search by order_release_id or packet_id
    search = st.text_input("🔍 Search by Order Release ID / Packet ID / Invoice No")
    if search:
        mask = (
            filtered_recon['packet_id'].astype(str).str.contains(search, case=False, na=False) |
            filtered_recon['order_release_id'].astype(str).str.contains(search, case=False, na=False) |
            filtered_recon['invoice_number'].astype(str).str.contains(search, case=False, na=False)
        )
        filtered_recon = filtered_recon[mask]

    show_cols = ['packet_id','order_release_id','invoice_number','sku','seller_amount',
                 'expected_settlement','actual_settlement','pending_settlement',
                 'commission','logistics','tcs','tds','utr_prepaid','utr_postpaid','Recon_Status']
    show_cols = [c for c in show_cols if c in filtered_recon.columns]
    st.dataframe(filtered_recon[show_cols], use_container_width=True, hide_index=True)

    st.markdown(f"**Showing {len(filtered_recon)} records**")

    ex1,ex2 = st.columns(2)
    with ex1:
        st.download_button("📥 Download Reconciliation (Excel)",
            data=to_excel(filtered_recon), file_name="recon_Jan26.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with ex2:
        st.download_button("📥 Download Reconciliation (CSV)",
            data=filtered_recon.to_csv(index=False).encode(),
            file_name="recon_Jan26.csv", mime="text/csv")

    st.markdown("---")
    st.markdown('<div class="section-title">↔️ Forward ↔ Reverse Reconciliation</div>', unsafe_allow_html=True)
    st.markdown("Orders that appear in both Forward (delivered) and Reverse (returned) — potential double-deduction check.")
    common_order_ids = set(pg_fwd['order_release_id'].astype(str)) & set(pg_rev['order_release_id'].astype(str))
    if common_order_ids:
        fwd_common = pg_fwd[pg_fwd['order_release_id'].astype(str).isin(common_order_ids)][
            ['order_release_id','packet_id','seller_product_amount','total_actual_settlement','article_type','sku_code']
        ].rename(columns={'seller_product_amount':'fwd_amount','total_actual_settlement':'fwd_settlement'})
        rev_common = pg_rev[pg_rev['order_release_id'].astype(str).isin(common_order_ids)][
            ['order_release_id','return_type','total_actual_settlement','return_date']
        ].rename(columns={'total_actual_settlement':'rev_settlement'})
        cross = fwd_common.merge(rev_common, on='order_release_id', how='inner')
        cross['net_effect'] = safe_num(cross['fwd_settlement']) + safe_num(cross['rev_settlement'])
        st.dataframe(cross, use_container_width=True, hide_index=True)
        st.info(f"⚠️ {len(cross)} orders appear in both Forward and Reverse. Net effect: {fmt_inr(cross['net_effect'].sum())}")
    else:
        st.success("✅ No order appears in both Forward and Reverse — no double entries detected.")

# ══════════════════════════════════════════════
# TAB 3 — SALES ANALYSIS
# ══════════════════════════════════════════════
with t_sales:
    st.markdown('<div class="section-title">🛒 Sales Sheet Analysis</div>', unsafe_allow_html=True)

    # Overview metrics
    completed = sales[sales['order_status']=='C'] if 'order_status' in sales.columns else sales
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Total Records in Sales", fmt_num(len(sales)))
    s2.metric("Completed Orders (C)", fmt_num(len(completed)))
    s3.metric("Total Invoice Amount", fmt_inr(sales['invoiceamount'].sum()))
    s4.metric("Avg Invoice Value", fmt_inr(sales['invoiceamount'].mean()))

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Order Status Breakdown</div>', unsafe_allow_html=True)
        status_map = {'C':'Completed','F':'Forward (in transit)','SH':'Shipped',
                      'RTO':'Return to Origin','PK':'Packed'}
        if 'order_status' in sales.columns:
            os_df = sales['order_status'].value_counts().reset_index()
            os_df.columns = ['Code','Count']
            os_df['Status'] = os_df['Code'].map(status_map).fillna(os_df['Code'])
            os_df['Revenue (₹)'] = os_df['Code'].map(
                sales.groupby('order_status')['invoiceamount'].sum().round(2))
            st.dataframe(os_df[['Status','Count','Revenue (₹)']], use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<div class="section-title">Payment Method Split</div>', unsafe_allow_html=True)
        if 'payment_method' in sales.columns:
            pm = sales.groupby('payment_method').agg(
                Orders=('packet_id','count'),
                Revenue=('invoiceamount','sum')
            ).reset_index()
            pm['Revenue'] = pm['Revenue'].round(2)
            pm['payment_method'] = pm['payment_method'].map({'on':'Online (Prepaid)','cod':'COD (Postpaid)'}).fillna(pm['payment_method'])
            st.dataframe(pm, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Article Type Revenue</div>', unsafe_allow_html=True)
    if 'article_type' in sales.columns:
        at = sales.groupby('article_type').agg(
            Orders=('packet_id','count'),
            Total_Invoice=('invoiceamount','sum'),
            Avg_Invoice=('invoiceamount','mean'),
            Total_Discount=('discount','sum')
        ).reset_index().sort_values('Total_Invoice', ascending=False)
        at['Total_Invoice'] = at['Total_Invoice'].round(2)
        at['Avg_Invoice']   = at['Avg_Invoice'].round(2)
        at['Total_Discount']= at['Total_Discount'].round(2)
        st.dataframe(at, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Daily Order Trend</div>', unsafe_allow_html=True)
    if 'order_packed_date' in sales.columns:
        sales['packed_date_dt'] = pd.to_datetime(sales['order_packed_date'], errors='coerce')
        daily = sales.groupby(sales['packed_date_dt'].dt.date).agg(
            Orders=('packet_id','count'),
            Revenue=('invoiceamount','sum')
        ).reset_index()
        daily.columns = ['Date','Orders','Revenue']
        daily = daily.dropna()
        if not daily.empty:
            st.line_chart(daily.set_index('Date')[['Orders','Revenue']])

# ══════════════════════════════════════════════
# TAB 4 — RETURNS ANALYSIS
# ══════════════════════════════════════════════
with t_returns:
    st.markdown('<div class="section-title">↩️ Returns & Reverse Analysis</div>', unsafe_allow_html=True)

    r1,r2,r3,r4 = st.columns(4)
    total_returns  = len(pg_rev)
    return_refunds = (pg_rev['return_type']=='return_refund').sum()
    exchanges      = (pg_rev['return_type']=='exchange').sum()
    total_rev_deb  = abs(pg_rev['total_actual_settlement'].sum())

    r1.metric("Total Returns", fmt_num(total_returns))
    r2.metric("Return Refunds", fmt_num(return_refunds))
    r3.metric("Exchanges", fmt_num(exchanges))
    r4.metric("Total Amount Debited Back", fmt_inr(total_rev_deb))

    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Return Type Breakdown</div>', unsafe_allow_html=True)
        rt = pg_rev.groupby('return_type').agg(
            Count=('order_release_id','count'),
            Total_Debited=('total_actual_settlement','sum'),
            Avg_Debited=('total_actual_settlement','mean')
        ).reset_index()
        rt['Total_Debited'] = rt['Total_Debited'].round(2)
        rt['Avg_Debited']   = rt['Avg_Debited'].round(2)
        st.dataframe(rt, use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<div class="section-title">Article Type Returns</div>', unsafe_allow_html=True)
        if 'article_type' in pg_rev.columns:
            art_ret = pg_rev.groupby('article_type').agg(
                Returns=('order_release_id','count'),
                Total_Debited=('total_actual_settlement','sum')
            ).reset_index().sort_values('Returns', ascending=False)
            art_ret['Total_Debited'] = art_ret['Total_Debited'].round(2)
            st.dataframe(art_ret, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Return Rate by Article Type</div>', unsafe_allow_html=True)
    fwd_by_art = pg_fwd['article_type'].value_counts().rename('Forward_Orders')
    rev_by_art = pg_rev['article_type'].value_counts().rename('Returns')
    rr_df = pd.concat([fwd_by_art, rev_by_art], axis=1).fillna(0).astype(int)
    rr_df['Return_Rate_%'] = (rr_df['Returns'] / rr_df['Forward_Orders'] * 100).round(1)
    st.dataframe(rr_df.reset_index().rename(columns={'index':'Article Type'}), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">📋 Return Details</div>', unsafe_allow_html=True)
    ret_cols = ['order_release_id','packet_id','return_type','return_date','sku_code',
                'seller_product_amount','total_actual_settlement','article_type',
                'prepaid_amount','postpaid_amount']
    ret_cols = [c for c in ret_cols if c in pg_rev.columns]
    st.dataframe(pg_rev[ret_cols].head(200), use_container_width=True, hide_index=True)

    st.download_button("📥 Download Returns Report",
        data=to_excel(pg_rev[ret_cols]),
        file_name="returns_Jan26.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ══════════════════════════════════════════════
# TAB 5 — SETTLEMENT TRACKER
# ══════════════════════════════════════════════
with t_settle:
    st.markdown('<div class="section-title">💳 UTR-wise Settlement Tracker</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-chip">Track each settlement by UTR number and date. '
        'Verify which orders are settled and which are pending.</div><br>',
        unsafe_allow_html=True
    )

    # Build UTR-level tracker for Forward
    utr_rows = []
    for _, row in pg_fwd.iterrows():
        for pay_type, utr_col, date_col, amt_col in [
            ('Prepaid – Commission', 'bank_utr_no_prepaid_comm_deduction',
             'settlement_date_prepaid_comm_deduction', 'prepaid_commission_deduction'),
            ('Prepaid – Logistics',  'bank_utr_no_prepaid_logistics_deduction',
             'settlement_date_prepaid_logistics_deduction', 'prepaid_logistics_deduction'),
            ('Prepaid – Payment',    'bank_utr_no_prepaid_payment',
             'settlement_date_prepaid_payment', 'prepaid_payment'),
            ('Postpaid – Commission','bank_utr_no_postpaid_comm_deduction',
             'settlement_date_postpaid_comm_deduction', 'postpaid_commission_deduction'),
            ('Postpaid – Logistics', 'bank_utr_no_postpaid_logistics_deduction',
             'settlement_date_postpaid_logistics_deduction', 'postpaid_logistics_deduction'),
            ('Postpaid – Payment',   'bank_utr_no_postpaid_payment',
             'settlement_date_postpaid_payment', 'postpaid_payment'),
        ]:
            utr = row.get(utr_col, None)
            dt  = row.get(date_col, None)
            amt = row.get(amt_col, 0)
            if pd.notna(utr) and str(utr).strip() not in ('','nan'):
                utr_rows.append({
                    'Order_ID':    row['order_release_id'],
                    'Packet_ID':   row['packet_id'],
                    'SKU':         row.get('sku_code',''),
                    'Type':        pay_type,
                    'UTR':         str(utr).strip(),
                    'Settle_Date': str(dt)[:10] if pd.notna(dt) else '',
                    'Amount':      round(float(amt) if pd.notna(amt) else 0, 2),
                    'Status':      '✅ Settled' if pd.notna(utr) and str(utr).strip() else '🕐 Pending'
                })

    if utr_rows:
        utr_df = pd.DataFrame(utr_rows)
        settled_amt   = utr_df[utr_df['Status']=='✅ Settled']['Amount'].sum()
        total_utrs    = utr_df['UTR'].nunique()
        settle_dates  = utr_df['Settle_Date'].nunique()

        su1,su2,su3 = st.columns(3)
        su1.metric("Unique UTR Numbers", fmt_num(total_utrs))
        su2.metric("Settlement Dates", fmt_num(settle_dates))
        su3.metric("Total Amount Tracked", fmt_inr(settled_amt))

        st.markdown("<br>", unsafe_allow_html=True)

        # UTR search
        utr_search = st.text_input("🔍 Search by UTR Number")
        utr_display = utr_df[utr_df['UTR'].str.contains(utr_search, case=False, na=False)] if utr_search else utr_df

        date_sel = st.selectbox("Filter by Settlement Date",
            ['All'] + sorted(utr_df['Settle_Date'].unique().tolist()))
        if date_sel != 'All':
            utr_display = utr_display[utr_display['Settle_Date']==date_sel]

        st.dataframe(utr_display, use_container_width=True, hide_index=True)

        # UTR summary
        st.markdown('<div class="section-title">UTR Summary (Total per UTR)</div>', unsafe_allow_html=True)
        utr_summary = utr_df.groupby('UTR').agg(
            Settle_Date=('Settle_Date','first'),
            Orders=('Order_ID','count'),
            Total_Amount=('Amount','sum')
        ).reset_index().sort_values('Settle_Date')
        utr_summary['Total_Amount'] = utr_summary['Total_Amount'].round(2)
        st.dataframe(utr_summary, use_container_width=True, hide_index=True)

        st.download_button("📥 Download Settlement Tracker",
            data=to_excel(utr_df), file_name="settlement_tracker_Jan26.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("No UTR data found in the PG Forward file.")

# ══════════════════════════════════════════════
# TAB 6 — SKU & PRODUCT
# ══════════════════════════════════════════════
with t_sku:
    st.markdown('<div class="section-title">📦 SKU-wise Performance</div>', unsafe_allow_html=True)

    sku_fwd = pg_fwd.groupby('sku_code').agg(
        Orders=('order_release_id','count'),
        Total_MRP=('mrp','sum'),
        Seller_Revenue=('seller_product_amount','sum'),
        Total_Settlement=('total_actual_settlement','sum'),
        Avg_Commission_Pct=('commission_percentage','mean'),
        Article_Type=('article_type','first')
    ).reset_index().sort_values('Orders', ascending=False)

    sku_rev = pg_rev.groupby('sku_code').agg(
        Returns=('order_release_id','count'),
        Return_Deduction=('total_actual_settlement','sum')
    ).reset_index()

    sku_all = sku_fwd.merge(sku_rev, on='sku_code', how='left').fillna(0)
    sku_all['Return_Rate_%'] = (sku_all['Returns'] / sku_all['Orders'] * 100).round(1)
    sku_all['Net_Settlement'] = (sku_all['Total_Settlement'] + sku_all['Return_Deduction']).round(2)
    sku_all['Seller_Revenue'] = sku_all['Seller_Revenue'].round(2)
    sku_all['Total_Settlement']= sku_all['Total_Settlement'].round(2)
    sku_all['Avg_Commission_Pct']= sku_all['Avg_Commission_Pct'].round(2)

    # SKU search
    sku_search = st.text_input("🔍 Search SKU")
    sku_disp = sku_all[sku_all['sku_code'].str.contains(sku_search, case=False, na=False)] if sku_search else sku_all

    st.dataframe(sku_disp, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">🔝 Top 10 SKUs by Revenue</div>', unsafe_allow_html=True)
    top10 = sku_all.nlargest(10,'Seller_Revenue')[['sku_code','Article_Type','Orders','Seller_Revenue','Returns','Return_Rate_%']]
    st.dataframe(top10, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">⚠️ High Return Rate SKUs (>50%)</div>', unsafe_allow_html=True)
    high_ret = sku_all[(sku_all['Return_Rate_%']>50) & (sku_all['Orders']>=3)].sort_values('Return_Rate_%', ascending=False)
    if not high_ret.empty:
        st.dataframe(high_ret, use_container_width=True, hide_index=True)
    else:
        st.success("No SKU has return rate >50% with at least 3 orders.")

    st.download_button("📥 Download SKU Report",
        data=to_excel(sku_all), file_name="sku_report_Jan26.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ══════════════════════════════════════════════
# TAB 7 — GEOGRAPHY
# ══════════════════════════════════════════════
with t_geo:
    st.markdown('<div class="section-title">🌍 Geography Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">State-wise Sales (Forward)</div>', unsafe_allow_html=True)
        if 'shipping_state' in pg_fwd.columns:
            state_fwd = pg_fwd.groupby('shipping_state').agg(
                Orders=('order_release_id','count'),
                Revenue=('seller_product_amount','sum'),
                Settlement=('total_actual_settlement','sum')
            ).reset_index().sort_values('Orders', ascending=False)
            state_fwd['Revenue'] = state_fwd['Revenue'].round(2)
            state_fwd['Settlement'] = state_fwd['Settlement'].round(2)
            st.dataframe(state_fwd, use_container_width=True, hide_index=True)

    with col2:
        st.markdown('<div class="section-title">State-wise Returns</div>', unsafe_allow_html=True)
        if 'shipping_state' in pg_rev.columns:
            state_rev = pg_rev.groupby('shipping_state').agg(
                Returns=('order_release_id','count'),
                Total_Debited=('total_actual_settlement','sum')
            ).reset_index().sort_values('Returns', ascending=False)
            state_rev['Total_Debited'] = state_rev['Total_Debited'].round(2)
            st.dataframe(state_rev, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Shipment Zone Distribution</div>', unsafe_allow_html=True)
    z1,z2 = st.columns(2)
    with z1:
        zone_fwd = pg_fwd['shipment_zone_classification'].value_counts().reset_index()
        zone_fwd.columns = ['Zone','Forward Orders']
        zone_fwd['Settlement'] = zone_fwd['Zone'].map(
            pg_fwd.groupby('shipment_zone_classification')['total_actual_settlement'].sum().round(2))
        st.markdown("**Forward (Delivered)**")
        st.dataframe(zone_fwd, use_container_width=True, hide_index=True)
    with z2:
        zone_rev = pg_rev['shipment_zone_classification'].value_counts().reset_index()
        zone_rev.columns = ['Zone','Return Orders']
        st.markdown("**Reverse (Returns)**")
        st.dataframe(zone_rev, use_container_width=True, hide_index=True)

    # Sales state analysis
    if 'state' in sales.columns:
        st.markdown('<div class="section-title">Sales Sheet — State Orders</div>', unsafe_allow_html=True)
        sales_state = sales.groupby('state').agg(
            Orders=('packet_id','count'),
            Revenue=('invoiceamount','sum')
        ).reset_index().sort_values('Orders', ascending=False)
        sales_state['Revenue'] = sales_state['Revenue'].round(2)
        st.dataframe(sales_state, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
# TAB 8 — CHARGES BREAKUP
# ══════════════════════════════════════════════
with t_charges:
    st.markdown('<div class="section-title">💸 Charges & Deductions Breakup</div>', unsafe_allow_html=True)

    ch1,ch2,ch3,ch4,ch5 = st.columns(5)
    total_comm    = pg_fwd['total_commission'].abs().sum()
    total_logist  = pg_fwd['total_logistics_deduction'].abs().sum()
    total_ship    = safe_num(pg_fwd['shipping_fee']).sum()
    total_tcs     = pg_fwd['tcs_amount'].sum()
    total_tds     = pg_fwd['tds_amount'].sum()

    ch1.metric("Commission (Platform Fees)", fmt_inr(total_comm))
    ch2.metric("Total Logistics Deduction",  fmt_inr(total_logist))
    ch3.metric("Shipping Fee",               fmt_inr(total_ship))
    ch4.metric("TCS Deducted",               fmt_inr(total_tcs))
    ch5.metric("TDS Deducted",               fmt_inr(total_tds))

    st.markdown("<br>", unsafe_allow_html=True)

    # Commission by article type
    st.markdown('<div class="section-title">Commission by Article Type</div>', unsafe_allow_html=True)
    comm_art = pg_fwd.groupby('article_type').agg(
        Orders=('order_release_id','count'),
        Avg_Commission_Pct=('commission_percentage','mean'),
        Total_Commission=('total_commission','sum'),
        Seller_Revenue=('seller_product_amount','sum')
    ).reset_index()
    comm_art['Commission_Pct_of_Revenue'] = (
        comm_art['Total_Commission'].abs() / comm_art['Seller_Revenue'].replace(0,1) * 100
    ).round(2)
    comm_art['Avg_Commission_Pct'] = comm_art['Avg_Commission_Pct'].round(2)
    comm_art['Total_Commission']   = comm_art['Total_Commission'].round(2)
    st.dataframe(comm_art, use_container_width=True, hide_index=True)

    # Detailed per-order charges
    st.markdown('<div class="section-title">Order-level Charges (Forward)</div>', unsafe_allow_html=True)
    charge_cols = ['order_release_id','packet_id','sku_code','article_type',
                   'seller_product_amount','mrp','total_discount_amount',
                   'commission_percentage','total_commission',
                   'shipping_fee','total_logistics_deduction',
                   'tcs_amount','tds_amount',
                   'total_expected_settlement','total_actual_settlement']
    charge_cols = [c for c in charge_cols if c in pg_fwd.columns]
    charge_search = st.text_input("🔍 Search Order ID / Packet ID", key="charge_search")
    charge_df = pg_fwd[charge_cols].copy()
    if charge_search:
        charge_df = charge_df[
            charge_df['order_release_id'].astype(str).str.contains(charge_search, na=False) |
            charge_df['packet_id'].astype(str).str.contains(charge_search, na=False)
        ]
    st.dataframe(charge_df.head(500), use_container_width=True, hide_index=True)

    st.download_button("📥 Download Charges Report",
        data=to_excel(pg_fwd[charge_cols]),
        file_name="charges_Jan26.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Footer
st.markdown("---")
st.markdown(
    "🛍️ **Myntra Seller Dashboard** — Sangria Brand · January 2026 · "
    "PG Forward + Reverse + Sales Reconciliation",
    unsafe_allow_html=True
)

# ══════════════════════════════════════════════
# TAB 9 — ORDER SETTLEMENT CHECKER
# ══════════════════════════════════════════════
with t_checker:
    st.markdown('<div class="section-title">✅ Order-wise Settlement Checker</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#f0f9ff;border-left:4px solid #3b82f6;padding:12px 16px;border-radius:4px;margin-bottom:16px;font-size:0.9rem;">
    <b>Formula applied per order:</b><br>
    <code>Calculated Payment = seller_price (Sales) − total_commission_plus_tcs_tds_deduction − total_logistics_deduction</code><br><br>
    <b>Settlement Check:</b> Calculated Payment is then compared against <code>total_actual_settlement</code> (PG Forward Col AO).<br>
    Orders are flagged as ✅ Matched, ⚠️ Difference, or 🕐 Pending based on the gap.
    </div>
    """, unsafe_allow_html=True)

    # ── Join Sales (order_release_id = col F) with PG Forward (order_release_id = col A) ──
    # Detect the order ID column in sales sheet — could be 'order_release_id', 'order_id', or column F
    sales_id_col = None
    for candidate in ['order_release_id', 'order_id', 'orderreleaseid', 'Order_Release_Id']:
        if candidate in sales.columns:
            sales_id_col = candidate
            break
    if sales_id_col is None:
        # Fallback: use column index F (index 5)
        sales_id_col = sales.columns[5]
        st.info(f"ℹ️ Using column **'{sales_id_col}'** (Col F) as Order ID from Sales sheet.")

    # Detect seller_price column — col AU
    sales_price_col = None
    for candidate in ['seller_price', 'Seller_Price', 'seller price']:
        if candidate in sales.columns:
            sales_price_col = candidate
            break
    if sales_price_col is None:
        # Fallback: column AU = index 46
        if len(sales.columns) > 46:
            sales_price_col = sales.columns[46]
            st.info(f"ℹ️ Using column **'{sales_price_col}'** (Col AU) as Seller Price from Sales sheet.")
        else:
            st.error("❌ Could not find seller_price column in Sales sheet. Please check column AU.")
            st.stop()

    # Build sales lookup: order_id → seller_price
    sales_lookup = sales[[sales_id_col, sales_price_col]].copy()
    sales_lookup[sales_id_col]   = sales_lookup[sales_id_col].astype(str).str.strip()
    sales_lookup[sales_price_col] = safe_num(sales_lookup[sales_price_col])
    sales_lookup = sales_lookup.drop_duplicates(subset=[sales_id_col])
    sales_lookup.columns = ['order_release_id', 'seller_price']

    # Build PG Forward working set
    needed_pg = ['order_release_id', 'packet_id', 'sku_code', 'article_type',
                 'total_commission_plus_tcs_tds_deduction', 'total_logistics_deduction',
                 'total_actual_settlement', 'total_expected_settlement',
                 'amount_pending_settlement', 'seller_product_amount']
    available_pg = [c for c in needed_pg if c in pg_fwd.columns]
    pg_work = pg_fwd[available_pg].copy()
    pg_work['order_release_id'] = pg_work['order_release_id'].astype(str).str.strip()

    # Merge
    checker_df = pg_work.merge(sales_lookup, on='order_release_id', how='left')

    # ── Apply formula ──
    # If total_commission_plus_tcs_tds_deduction is missing, build it from components
    if 'total_commission_plus_tcs_tds_deduction' not in checker_df.columns or checker_df['total_commission_plus_tcs_tds_deduction'].fillna(0).abs().sum() == 0:
        for c in ['total_commission', 'tcs_amount', 'tds_amount']:
            if c not in checker_df.columns:
                checker_df[c] = 0
        checker_df['total_commission_plus_tcs_tds_deduction'] = (
            safe_num(checker_df.get('total_commission', 0)).abs() +
            safe_num(checker_df.get('tcs_amount', 0)).abs() +
            safe_num(checker_df.get('tds_amount', 0)).abs()
        )
        st.info("ℹ️ `total_commission_plus_tcs_tds_deduction` column not found — computed from commission + TCS + TDS.")

    checker_df['comm_tcs_tds']   = safe_num(checker_df['total_commission_plus_tcs_tds_deduction']).abs()
    checker_df['logistics']      = safe_num(checker_df['total_logistics_deduction']).abs()
    checker_df['seller_price']   = safe_num(checker_df['seller_price'])
    checker_df['actual_settle']  = safe_num(checker_df['total_actual_settlement'])
    checker_df['expected_settle']= safe_num(checker_df.get('total_expected_settlement', 0))
    checker_df['pending']        = safe_num(checker_df.get('amount_pending_settlement', 0))

    # Core formula
    checker_df['Calculated_Payment'] = (
        checker_df['seller_price'] - checker_df['comm_tcs_tds'] - checker_df['logistics']
    ).round(2)

    checker_df['Difference_Rs'] = (
        checker_df['Calculated_Payment'] - checker_df['actual_settle']
    ).round(2)

    # Status classification
    def settlement_status(row):
        if abs(row['Difference_Rs']) <= 2:          # allow ₹2 rounding tolerance
            return '✅ Matched'
        elif row['pending'] > 0:
            return '🕐 Settlement Pending'
        elif row['seller_price'] == 0:
            return '❓ No Sales Data'
        elif row['Difference_Rs'] > 2:
            return '⚠️ Underpaid'
        else:
            return '⚠️ Overpaid / Deduction Higher'

    checker_df['Status'] = checker_df.apply(settlement_status, axis=1)

    # ── Summary KPIs ──
    total_orders  = len(checker_df)
    matched       = (checker_df['Status'] == '✅ Matched').sum()
    underpaid     = (checker_df['Status'] == '⚠️ Underpaid').sum()
    overpaid      = (checker_df['Status'] == '⚠️ Overpaid / Deduction Higher').sum()
    pending_count = (checker_df['Status'] == '🕐 Settlement Pending').sum()
    no_data       = (checker_df['Status'] == '❓ No Sales Data').sum()
    total_diff    = checker_df['Difference_Rs'].sum()

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.markdown(f"""<div class="kpi-card blue">
        <div class="kpi-label">Total Orders</div>
        <div class="kpi-value">{total_orders:,}</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">✅ Matched</div>
        <div class="kpi-value">{matched:,}</div>
        <div class="kpi-sub">{matched/total_orders*100:.1f}%</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="kpi-card red">
        <div class="kpi-label">⚠️ Underpaid</div>
        <div class="kpi-value">{underpaid:,}</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="kpi-card orange">
        <div class="kpi-label">⚠️ Overpaid</div>
        <div class="kpi-value">{overpaid:,}</div></div>""", unsafe_allow_html=True)
    k5.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">🕐 Pending</div>
        <div class="kpi-value">{pending_count:,}</div></div>""", unsafe_allow_html=True)
    k6.markdown(f"""<div class="kpi-card {'red' if total_diff < 0 else 'green'}">
        <div class="kpi-label">Net Diff (Calc − Actual)</div>
        <div class="kpi-value">₹{total_diff:,.0f}</div>
        <div class="kpi-sub">{'Shortfall' if total_diff < 0 else 'Surplus'}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filters ──
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.multiselect(
            "Filter by Status",
            checker_df['Status'].unique().tolist(),
            default=checker_df['Status'].unique().tolist(),
            key="checker_status"
        )
    with col_f2:
        search_order = st.text_input("🔍 Search Order ID / Packet ID / SKU", key="checker_search")
    with col_f3:
        diff_threshold = st.number_input(
            "Show only where |Difference| > ₹", min_value=0.0, value=0.0, step=1.0, key="checker_thresh"
        )

    display_df = checker_df[checker_df['Status'].isin(status_filter)].copy()
    if search_order:
        mask = (
            display_df['order_release_id'].astype(str).str.contains(search_order, case=False, na=False) |
            display_df['packet_id'].astype(str).str.contains(search_order, case=False, na=False) |
            display_df.get('sku_code', pd.Series(dtype=str)).astype(str).str.contains(search_order, case=False, na=False)
        )
        display_df = display_df[mask]
    if diff_threshold > 0:
        display_df = display_df[display_df['Difference_Rs'].abs() > diff_threshold]

    # ── Main table ──
    show_cols = [
        'order_release_id', 'packet_id', 'sku_code',
        'seller_price', 'comm_tcs_tds', 'logistics',
        'Calculated_Payment', 'actual_settle', 'Difference_Rs',
        'pending', 'Status'
    ]
    show_cols = [c for c in show_cols if c in display_df.columns]

    rename_map = {
        'order_release_id':   'Order ID',
        'packet_id':          'Packet ID',
        'sku_code':           'SKU',
        'seller_price':       'Seller Price (₹)',
        'comm_tcs_tds':       'Commission+TCS+TDS (₹)',
        'logistics':          'Logistics (₹)',
        'Calculated_Payment': 'Calculated Payment (₹)',
        'actual_settle':      'Actual Settlement (₹)',
        'Difference_Rs':      'Difference (₹)',
        'pending':            'Pending (₹)',
        'Status':             'Status'
    }
    st.dataframe(
        display_df[show_cols].rename(columns=rename_map),
        use_container_width=True, hide_index=True
    )
    st.caption(f"Showing **{len(display_df):,}** of {total_orders:,} orders  |  Tolerance: ±₹2 for 'Matched'")

    # ── Formula breakdown expander ──
    with st.expander("📐 Formula Reference"):
        st.markdown("""
| Step | Formula |
|------|---------|
| **Calculated Payment** | `Seller Price` − `total_commission_plus_tcs_tds_deduction` − `total_logistics_deduction` |
| **Difference** | `Calculated Payment` − `total_actual_settlement` |
| **✅ Matched** | |Difference| ≤ ₹2 (rounding tolerance) |
| **⚠️ Underpaid** | Difference > ₹2 (you received less than calculated) |
| **⚠️ Overpaid** | Difference < −₹2 (more deducted than expected) |
| **🕐 Pending** | `amount_pending_settlement` > 0 |
        """)
        st.markdown("**Column sources:**")
        st.markdown("- `Seller Price` → Sales Sheet, Column F (order_release_id) joined with Column AU (seller_price)")
        st.markdown("- `total_commission_plus_tcs_tds_deduction` → PG Forward report (Expenses)")
        st.markdown("- `total_logistics_deduction` → PG Forward report")
        st.markdown("- `total_actual_settlement` → PG Forward report, Column AO")

    # ── Summary by status ──
    st.markdown('<div class="section-title">📊 Summary by Status</div>', unsafe_allow_html=True)
    summary = checker_df.groupby('Status').agg(
        Orders=('order_release_id', 'count'),
        Total_Seller_Price=('seller_price', 'sum'),
        Total_Calculated=('Calculated_Payment', 'sum'),
        Total_Actual_Settlement=('actual_settle', 'sum'),
        Total_Difference=('Difference_Rs', 'sum'),
    ).reset_index()
    summary = summary.round(2)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # ── Export ──
    export_df = display_df[show_cols].rename(columns=rename_map)
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "📥 Export Settlement Check (Excel)",
            data=to_excel(export_df),
            file_name="order_settlement_check.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with ec2:
        st.download_button(
            "📥 Export Settlement Check (CSV)",
            data=export_df.to_csv(index=False).encode(),
            file_name="order_settlement_check.csv",
            mime="text/csv"
        )
