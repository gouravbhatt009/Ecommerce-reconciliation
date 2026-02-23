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
    'total_commission_plus_tcs_tds_deduction',
    'forwardAdditionalCharges_prepaid',
    'forwardAdditionalCharges_postpaid'
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
    st.markdown('<div class="section-title">✅ Order Settlement Checker — Sales vs PG Forward</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#f0f9ff;border-left:4px solid #3b82f6;padding:12px 16px;border-radius:4px;margin-bottom:16px;font-size:0.9rem;">
    <b>How this works:</b> Every order from your <b>Sales Report</b> is the starting point.
    Each order is matched to the <b>PG Forward Report</b> by Order ID.<br><br>
    <b>Formula:</b>
    <code>Calculated Payment = Seller Price − Commission+TCS+TDS − Logistics − Fwd Additional (Prepaid) − Fwd Additional (Postpaid)</code><br>
    <code>Difference = Calculated Payment − total_actual_settlement (PG Forward Col AO)</code>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 1: Detect key columns in Sales sheet ──
    # Order ID = Col F
    sales_id_col = None
    for cand in ['order_release_id','Order_Release_Id','orderreleaseid','order_id']:
        if cand in sales.columns:
            sales_id_col = cand
            break
    if sales_id_col is None:
        sales_id_col = sales.columns[5]   # fallback Col F (index 5)
        st.info(f"Using **'{sales_id_col}'** (Col F) as Order ID from Sales sheet.")

    # Seller Price = Col AU
    sales_price_col = None
    for cand in ['seller_price','Seller_Price']:
        if cand in sales.columns:
            sales_price_col = cand
            break
    if sales_price_col is None:
        if len(sales.columns) > 46:
            sales_price_col = sales.columns[46]
            st.info(f"Using **'{sales_price_col}'** (Col AU) as Seller Price from Sales sheet.")
        else:
            st.error("Could not find seller_price column. Please check Col AU in Sales sheet.")
            st.stop()

    # Order status column
    sales_status_col = next((c for c in ['order_status','Order_Status'] if c in sales.columns), None)

    # ── Step 2: Build Sales base — one row per order ──
    sales_cols = [sales_id_col, sales_price_col]
    if sales_status_col:
        sales_cols.append(sales_status_col)
    for extra in ['SKU','sku_code','article_type','payment_method','invoiceamount']:
        if extra in sales.columns:
            sales_cols.append(extra)

    sales_base = sales[list(dict.fromkeys(sales_cols))].copy()  # dedupe cols
    sales_base[sales_id_col]    = sales_base[sales_id_col].astype(str).str.strip()
    sales_base[sales_price_col] = safe_num(sales_base[sales_price_col])
    sales_base = sales_base.drop_duplicates(subset=[sales_id_col])
    sales_base = sales_base.rename(columns={
        sales_id_col:    'order_release_id',
        sales_price_col: 'seller_price',
        **({' sales_status_col': 'sales_order_status'} if sales_status_col else {})
    })
    if sales_status_col and sales_status_col in sales_base.columns:
        sales_base = sales_base.rename(columns={sales_status_col: 'sales_order_status'})

    # ── Step 3: Build PG Forward lookup ──
    pg_cols_needed = ['order_release_id',
                      'total_commission_plus_tcs_tds_deduction',
                      'total_logistics_deduction',
                      'forwardAdditionalCharges_prepaid',
                      'forwardAdditionalCharges_postpaid',
                      'total_actual_settlement',
                      'total_expected_settlement',
                      'amount_pending_settlement',
                      'packet_id', 'sku_code']
    pg_avail = [c for c in pg_cols_needed if c in pg_fwd.columns]
    pg_lookup = pg_fwd[pg_avail].copy()
    pg_lookup['order_release_id'] = pg_lookup['order_release_id'].astype(str).str.strip()
    # Coerce numerics
    for c in pg_avail:
        if c not in ['order_release_id','packet_id','sku_code']:
            pg_lookup[c] = safe_num(pg_lookup[c])

    # ── Step 4: LEFT JOIN — Sales is the master ──
    # Every Sales order appears; PG columns are NaN if no match found
    df = sales_base.merge(pg_lookup, on='order_release_id', how='left', indicator=True)
    df['_in_pg'] = df['_merge'] == 'both'

    # ── Step 5: Fill numeric PG columns with 0 where no PG match ──
    for c in ['total_commission_plus_tcs_tds_deduction','total_logistics_deduction',
              'forwardAdditionalCharges_prepaid','forwardAdditionalCharges_postpaid',
              'total_actual_settlement','total_expected_settlement','amount_pending_settlement']:
        if c not in df.columns:
            df[c] = 0.0
        else:
            df[c] = df[c].fillna(0.0)

    # If commission col missing/zero, build from components
    if df['total_commission_plus_tcs_tds_deduction'].abs().sum() == 0:
        for c in ['total_commission','tcs_amount','tds_amount']:
            if c not in df.columns: df[c] = 0
        df['total_commission_plus_tcs_tds_deduction'] = (
            safe_num(df.get('total_commission',0)).abs() +
            safe_num(df.get('tcs_amount',0)).abs() +
            safe_num(df.get('tds_amount',0)).abs()
        )

    df['comm_tcs_tds']  = df['total_commission_plus_tcs_tds_deduction'].abs()
    df['logistics']     = df['total_logistics_deduction'].abs()
    df['add_prepaid']   = df['forwardAdditionalCharges_prepaid'].abs()
    df['add_postpaid']  = df['forwardAdditionalCharges_postpaid'].abs()
    df['actual_settle'] = df['total_actual_settlement']
    df['pending']       = df['amount_pending_settlement']

    # ── Step 6: Formula ──
    df['Calculated_Payment'] = (
        df['seller_price']
        - df['comm_tcs_tds']
        - df['logistics']
        - df['add_prepaid']
        - df['add_postpaid']
    ).round(2)

    df['Difference_Rs'] = (df['Calculated_Payment'] - df['actual_settle']).round(2)

    # ── Step 7: Status — Sales-first logic ──
    def settlement_status(row):
        if not row['_in_pg']:
            # Order in Sales, ZERO record in PG Forward
            return '🚨 Payment Not Received'
        if row['pending'] > 0:
            return '🕐 Settlement Pending'
        if row['actual_settle'] == 0 and row['Calculated_Payment'] > 0:
            return '🚨 Payment Not Received'
        if abs(row['Difference_Rs']) <= 2:
            return '✅ Matched'
        if row['Difference_Rs'] > 2:
            return '⚠️ Underpaid'
        return '⚠️ Overpaid / Excess Deduction'

    df['Status'] = df.apply(settlement_status, axis=1)

    # ── Step 8: KPIs ──
    total       = len(df)
    matched     = (df['Status'] == '✅ Matched').sum()
    not_recv    = (df['Status'] == '🚨 Payment Not Received').sum()
    pending_n   = (df['Status'] == '🕐 Settlement Pending').sum()
    underpaid   = (df['Status'] == '⚠️ Underpaid').sum()
    overpaid    = (df['Status'] == '⚠️ Overpaid / Excess Deduction').sum()
    not_recv_val= df.loc[df['Status'] == '🚨 Payment Not Received', 'seller_price'].sum()
    pending_val = df.loc[df['Status'] == '🕐 Settlement Pending', 'pending'].sum()
    net_diff    = df.loc[df['_in_pg'], 'Difference_Rs'].sum()

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.markdown(f'''<div class="kpi-card blue">
        <div class="kpi-label">Total Sales Orders</div>
        <div class="kpi-value">{total:,}</div>
        <div class="kpi-sub">From Sales report</div></div>''', unsafe_allow_html=True)
    k2.markdown(f'''<div class="kpi-card green">
        <div class="kpi-label">✅ Matched</div>
        <div class="kpi-value">{matched:,}</div>
        <div class="kpi-sub">{matched/max(total,1)*100:.1f}% of orders</div></div>''', unsafe_allow_html=True)
    k3.markdown(f'''<div class="kpi-card red">
        <div class="kpi-label">🚨 Payment Not Received</div>
        <div class="kpi-value">{not_recv:,}</div>
        <div class="kpi-sub">₹{not_recv_val:,.0f} at risk</div></div>''', unsafe_allow_html=True)
    k4.markdown(f'''<div class="kpi-card orange">
        <div class="kpi-label">🕐 Settlement Pending</div>
        <div class="kpi-value">{pending_n:,}</div>
        <div class="kpi-sub">₹{pending_val:,.0f} due</div></div>''', unsafe_allow_html=True)
    k5.markdown(f'''<div class="kpi-card red">
        <div class="kpi-label">⚠️ Underpaid</div>
        <div class="kpi-value">{underpaid:,}</div></div>''', unsafe_allow_html=True)
    k6.markdown(f'''<div class="kpi-card {'red' if net_diff < 0 else 'green'}">
        <div class="kpi-label">Net Difference</div>
        <div class="kpi-value">₹{net_diff:,.0f}</div>
        <div class="kpi-sub">Calc − Actual (matched orders)</div></div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Alert banner ──
    if not_recv > 0:
        st.markdown(f"""
        <div style="background:#fef2f2;border:1px solid #ef4444;border-left:6px solid #ef4444;
             padding:14px 18px;border-radius:6px;margin-bottom:16px;">
        <b>🚨 {not_recv} order(s) from your Sales Report have NO payment entry in PG Forward.</b><br>
        These orders were sold but Myntra has not processed any payment for them.<br>
        <b>Total Seller Price at risk: ₹{not_recv_val:,.2f}</b>
        </div>
        """, unsafe_allow_html=True)
    if pending_n > 0:
        st.markdown(f"""
        <div style="background:#fffbeb;border:1px solid #f59e0b;border-left:6px solid #f59e0b;
             padding:14px 18px;border-radius:6px;margin-bottom:16px;">
        <b>🕐 {pending_n} order(s) are in PG Forward but settlement is still pending.</b><br>
        <b>Total amount pending: ₹{pending_val:,.2f}</b>
        </div>
        """, unsafe_allow_html=True)

    # ── Filters ──
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        status_filter = st.multiselect(
            "Filter by Status",
            df['Status'].unique().tolist(),
            default=df['Status'].unique().tolist(),
            key="checker_status"
        )
    with cf2:
        search_ord = st.text_input("🔍 Search by Order ID", key="checker_search")
    with cf3:
        diff_thresh = st.number_input("Show |Difference| > ₹", min_value=0.0, value=0.0, step=1.0, key="checker_thresh")

    display_df = df[df['Status'].isin(status_filter)].copy()
    if search_ord:
        display_df = display_df[display_df['order_release_id'].astype(str).str.contains(search_ord, case=False, na=False)]
    if diff_thresh > 0:
        display_df = display_df[display_df['Difference_Rs'].abs() > diff_thresh]

    # ── Main table ──
    # Pick SKU col — prefer 'SKU', fallback 'sku_code', never both (avoids duplicate col names)
    sku_col = 'SKU' if 'SKU' in display_df.columns else ('sku_code' if 'sku_code' in display_df.columns else None)
    show_cols = ['order_release_id']
    for c in ['packet_id', sku_col, 'sales_order_status', 'payment_method']:
        if c and c in display_df.columns:
            show_cols.append(c)
    show_cols += ['seller_price','comm_tcs_tds','logistics','add_prepaid','add_postpaid',
                  'Calculated_Payment','actual_settle','Difference_Rs','pending','Status']
    # Deduplicate while preserving order, then keep only cols that exist
    seen = set()
    show_cols = [c for c in show_cols if c not in seen and not seen.add(c)]
    show_cols = [c for c in show_cols if c in display_df.columns]

    rename_map = {
        'order_release_id':  'Order ID (Sales)',
        'packet_id':         'Packet ID',
        'SKU':               'SKU',
        'sku_code':          'SKU',
        'sales_order_status':'Order Status',
        'payment_method':    'Payment Method',
        'seller_price':      'Seller Price (₹)',
        'comm_tcs_tds':      'Commission+TCS+TDS (₹)',
        'logistics':         'Logistics (₹)',
        'add_prepaid':       'Fwd Add. Prepaid (₹)',
        'add_postpaid':      'Fwd Add. Postpaid (₹)',
        'Calculated_Payment':'Calculated Payment (₹)',
        'actual_settle':     'Actual Settlement (₹)',
        'Difference_Rs':     'Difference (₹)',
        'pending':           'Pending (₹)',
        'Status':            'Status'
    }
    # Final safety: drop any duplicate column names before passing to st.dataframe
    out_df = display_df[show_cols].rename(columns=rename_map)
    out_df = out_df.loc[:, ~out_df.columns.duplicated()]
    st.dataframe(out_df, use_container_width=True, hide_index=True)
    st.caption(f"Showing **{len(display_df):,}** of {total:,} Sales orders")

    # ── Dedicated table: Payment Not Received ──
    not_recv_df = df[df['Status'] == '🚨 Payment Not Received'].copy()
    if not not_recv_df.empty:
        st.markdown('<div class="section-title">🚨 Orders from Sales Report — Payment Not Received from Myntra</div>', unsafe_allow_html=True)
        st.markdown("These Order IDs exist in your **Sales Report** but have **zero entry in PG Forward** — Myntra has not processed any payment for these orders.")
        nr_cols = ['order_release_id','seller_price']
        for c in ['sales_order_status','payment_method','invoiceamount','article_type']:
            if c in not_recv_df.columns: nr_cols.append(c)
        nr_rename = {
            'order_release_id':  'Order ID',
            'seller_price':      'Seller Price (₹)',
            'sales_order_status':'Order Status',
            'payment_method':    'Payment Method',
            'invoiceamount':     'Invoice Amount (₹)',
            'article_type':      'Article Type'
        }
        _nr_out = not_recv_df[nr_cols].rename(columns=nr_rename)
        _nr_out = _nr_out.loc[:, ~_nr_out.columns.duplicated()]
        st.dataframe(_nr_out, use_container_width=True, hide_index=True)
        m1, m2 = st.columns(2)
        m1.metric("Orders with No Payment", f"{len(not_recv_df):,}")
        m2.metric("Total Seller Price at Risk", f"₹{not_recv_df['seller_price'].sum():,.2f}")
        st.download_button("📥 Export – Payment Not Received (Excel)",
            data=to_excel(not_recv_df[nr_cols].rename(columns=nr_rename)),
            file_name="payment_not_received.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── Dedicated table: Settlement Pending ──
    pend_df = df[df['Status'] == '🕐 Settlement Pending'].copy()
    if not pend_df.empty:
        st.markdown('<div class="section-title">🕐 Orders in PG Forward — Settlement Still Pending</div>', unsafe_allow_html=True)
        st.markdown("These orders are recorded in PG Forward but `amount_pending_settlement > 0` — Myntra has acknowledged the order but not yet paid.")
        p_cols = ['order_release_id','seller_price','Calculated_Payment','actual_settle','pending']
        if 'sales_order_status' in pend_df.columns: p_cols.insert(2,'sales_order_status')
        p_cols = [c for c in p_cols if c in pend_df.columns]
        p_rename = {
            'order_release_id':  'Order ID',
            'seller_price':      'Seller Price (₹)',
            'sales_order_status':'Order Status',
            'Calculated_Payment':'Calculated Payment (₹)',
            'actual_settle':     'Actual Settlement (₹)',
            'pending':           'Amount Pending (₹)'
        }
        _p_out = pend_df[p_cols].rename(columns=p_rename)
        _p_out = _p_out.loc[:, ~_p_out.columns.duplicated()]
        st.dataframe(_p_out, use_container_width=True, hide_index=True)
        st.metric("Total Pending Amount", f"₹{pend_df['pending'].sum():,.2f}")
        st.download_button("📥 Export – Pending Settlement (Excel)",
            data=to_excel(pend_df[p_cols].rename(columns=p_rename)),
            file_name="settlement_pending.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── Summary table ──
    st.markdown('<div class="section-title">📊 Summary by Status</div>', unsafe_allow_html=True)
    summary = df.groupby('Status').agg(
        Orders=('order_release_id','count'),
        Total_Seller_Price=('seller_price','sum'),
        Total_Calculated=('Calculated_Payment','sum'),
        Total_Actual_Settlement=('actual_settle','sum'),
        Total_Difference=('Difference_Rs','sum'),
        Total_Pending=('pending','sum'),
    ).reset_index().round(2)
    summary = summary.loc[:, ~summary.columns.duplicated()]
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # ── Full export ──
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button("📥 Export All Orders (Excel)",
            data=to_excel(display_df[show_cols].rename(columns=rename_map)),
            file_name="order_settlement_check.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with ec2:
        st.download_button("📥 Export All Orders (CSV)",
            data=display_df[show_cols].rename(columns=rename_map).to_csv(index=False).encode(),
            file_name="order_settlement_check.csv", mime="text/csv"
        )
