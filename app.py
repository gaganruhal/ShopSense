import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import re
import io
import zipfile

st.set_page_config(page_title="ShopSense | Analytics", page_icon="ðŸ›ï¸", layout="wide")

st.markdown("""
<style>
.stApp {background:#f4f6fb;}
[data-testid="stSidebar"] {background:#111827;}
[data-testid="stSidebar"] * {color:#e5e7eb;}
.brand {font-size:1.65rem;font-weight:800;color:white;margin-bottom:0;}
.muted {color:#64748b;font-size:.9rem;}
div[data-testid="stMetric"] {background:white;border:1px solid #e5eaf2;padding:1rem;border-radius:15px;box-shadow:0 3px 12px #0f172a08;}
div[data-testid="stVerticalBlockBorderWrapper"] {background:white;border:1px solid #e5eaf2;border-radius:15px;padding:1rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load the bundled sample dataset from SQLite, creating the table if needed."""
    connection = sqlite3.connect("shopsense.db")
    try:
        table_exists = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'",
            connection,
        )
        if table_exists.empty:
            df_source = pd.read_csv("shopsense_sample_ecommerce.csv")
            df_source.to_sql("orders", connection, if_exists="replace", index=False)
        df = pd.read_sql_query("SELECT * FROM orders", connection)
    finally:
        connection.close()
    return prepare_dataset(df)


REQUIRED_COLUMNS = [
    "OrderID", "OrderDate", "CustomerID", "Product", "Category",
    "Country", "Quantity", "Sales", "Profit",
]
OPTIONAL_NUMERIC_COLUMNS = ["UnitPrice", "UnitCost"]
OPTIONAL_TEXT_COLUMNS = ["PaymentMethod", "SalesChannel"]


def prepare_dataset(source_df):
    """Validate and standardize a ShopSense-compatible e-commerce CSV/DataFrame."""
    if source_df is None or source_df.empty:
        raise ValueError("The dataset is empty. Please upload a CSV containing data rows.")

    df = source_df.copy()
    df.columns = [str(column).strip() for column in df.columns]
    if len(set(df.columns)) != len(df.columns):
        raise ValueError("The dataset contains duplicate column names. Rename them and try again.")

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(
            "This CSV is missing required columns: " + ", ".join(missing)
            + ". Required columns are: " + ", ".join(REQUIRED_COLUMNS)
        )

    for column in OPTIONAL_NUMERIC_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    for column in OPTIONAL_TEXT_COLUMNS:
        if column not in df.columns:
            df[column] = "Unknown"
        df[column] = df[column].fillna("Unknown").astype(str)

    df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce")
    for column in ["Quantity", "UnitPrice", "UnitCost", "Sales", "Profit"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # These columns are used for grouping/filtering throughout the existing dashboard.
    text_columns = ["OrderID", "CustomerID", "Product", "Category", "Country"]
    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

    df = df.dropna(subset=REQUIRED_COLUMNS).copy()
    df = df[
        (df["OrderID"] != "") & (df["CustomerID"] != "")
        & (df["Product"] != "") & (df["Category"] != "")
        & (df["Country"] != "") & (df["Quantity"] > 0)
        & (df["Sales"] >= 0)
    ].copy()
    if df.empty:
        raise ValueError(
            "No usable rows remain after validation. Check dates, required fields, quantity and sales values."
        )
    df["YearMonth"] = df["OrderDate"].dt.to_period("M").astype(str)
    return df.reset_index(drop=True)


def read_uploaded_csv(uploaded_file):
    """Read and validate an uploaded CSV without modifying the SQLite database."""
    try:
        uploaded_file.seek(0)
        source_df = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        try:
            source_df = pd.read_csv(uploaded_file, encoding="latin-1")
        except Exception as exc:
            raise ValueError(f"Could not decode this CSV file: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Could not read this CSV file: {exc}") from exc
    return prepare_dataset(source_df)





try:
    sample_df = load_data()
except FileNotFoundError:
    st.error("Dataset not found. Keep shopsense_sample_ecommerce.csv in the same folder as app.py.")
    st.stop()
except Exception as exc:
    st.error(f"Could not load the sample dataset: {exc}")
    st.stop()

with st.sidebar:
    st.markdown('<div class="brand">ðŸ›ï¸ ShopSense</div>', unsafe_allow_html=True)
    st.caption("E-COMMERCE INTELLIGENCE")
    st.markdown("---")
    st.subheader("Dataset source")
    data_source = st.radio(
        "Choose data source",
        ["Sample dataset", "Upload CSV"],
        key="shopsense_data_source",
        help="Uploaded files are used for this session only; the original SQLite database is not overwritten.",
    )
    uploaded_file = None
    if data_source == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload e-commerce CSV",
            type=["csv"],
            key="shopsense_csv_uploader",
            help="Required columns: OrderID, OrderDate, CustomerID, Product, Category, Country, Quantity, Sales and Profit.",
        )
        if uploaded_file is not None:
            try:
                df = read_uploaded_csv(uploaded_file)
                active_source_label = f"Uploaded CSV: {uploaded_file.name}"
            except ValueError as exc:
                st.error(str(exc))
                st.stop()
        else:
            df = sample_df
            active_source_label = "Sample dataset (waiting for upload)"
    else:
        df = sample_df
        active_source_label = "Built-in sample dataset"
    st.markdown("---")
    page = st.radio(
    "Navigation",
    [
        "Overview",
        "Revenue Analytics",
        "Product Performance",
        "Customers & Orders",
        "Dataset",
        "Data Upload",
        "Data Cleaning",
        "Data Quality Report",
        "SQL Workspace",
        "SQL Business Insights",
        "Business Insights & Recommendations",
        "Export Center",
    ]
)
    st.markdown("---")
    st.subheader("Filters")
    cats = ["All categories"] + sorted(df["Category"].dropna().unique().tolist())
    countries = ["All countries"] + sorted(df["Country"].dropna().unique().tolist())
    channels = ["All channels"] + sorted(df["SalesChannel"].dropna().unique().tolist())
    cat = st.selectbox("Category", cats)
    country = st.selectbox("Country", countries)
    channel = st.selectbox("Sales channel", channels)
    start, end = df["OrderDate"].min().date(), df["OrderDate"].max().date()
    date_range = st.date_input("Order date range", value=(start, end), min_value=start, max_value=end)
    search = st.text_input("Search product", placeholder="Type a product name")
    st.markdown("---")
    st.caption("Sample data is synthetic demo data.")
    st.markdown("---")
    theme_mode = st.radio("Appearance", ["Light", "Dark"], horizontal=True, key="shopsense_theme_mode")

# Responsive layout and selectable theme overrides. These styles complement Streamlit's layout.
st.markdown("""
<style>
/* Responsive polish */
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }
h1, h2, h3 { overflow-wrap: anywhere; }
[data-testid="stDataFrame"], [data-testid="stTable"] { max-width: 100%; }
[data-testid="stMetric"] { min-width: 0; overflow-wrap: anywhere; }
button, [role="button"] { min-height: 2.5rem; }
input, textarea, [data-baseweb="select"] { max-width: 100%; }
img, svg { max-width: 100%; }
@media (max-width: 900px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; }
  [data-testid="stMetric"] { padding: .75rem !important; }
}
@media (max-width: 600px) {
  .block-container { padding-top: .75rem; padding-left: .65rem; padding-right: .65rem; }
  h1 { font-size: 1.65rem !important; line-height: 1.25 !important; }
  h2 { font-size: 1.35rem !important; }
  h3 { font-size: 1.1rem !important; }
  [data-testid="stMetric"] { padding: .6rem !important; border-radius: 10px !important; }
  [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
  [data-testid="stSidebar"] { min-width: 0; }
  .stDownloadButton button, .stButton button { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

if theme_mode == "Light":
    # Explicit light-theme foreground colours. Streamlit may inherit white text
    # from a dark base theme, so setting only the page background is not enough.
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] { color: #1e293b !important; }
    [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] h4,
    [data-testid="stMain"] p, [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stMetricLabel"],
    [data-testid="stMain"] [data-testid="stMetricValue"],
    [data-testid="stMain"] [data-testid="stMetricDelta"] {
        color: #1e293b !important;
    }
    [data-testid="stMain"] [data-testid="stMetric"] {
        background: #ffffff !important;
        border-color: #e5eaf2 !important;
    }
    [data-testid="stMain"] [data-testid="stMetricLabel"] *,
    [data-testid="stMain"] [data-testid="stMetricValue"] *,
    [data-testid="stMain"] [data-testid="stMetricDelta"] * {
        color: #1e293b !important;
    }
    </style>
    """, unsafe_allow_html=True)

if theme_mode == "Dark":
    st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #0b1220 !important; color: #e5e7eb !important; }
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] { color: #e5e7eb !important; }
    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stMetric"], [data-testid="stExpander"],
    [data-testid="stDataFrame"], [data-testid="stTable"] {
      background: #111827 !important; color: #e5e7eb !important; border-color: #334155 !important;
    }
    [data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"], [data-testid="stMetricDelta"] { color: #f8fafc !important; }
    .muted, [data-testid="stCaptionContainer"], p, label, h1, h2, h3, h4, li { color: #e2e8f0; }
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea {
      background: #1f2937 !important; color: #f8fafc !important; border-color: #475569 !important;
    }
    [data-baseweb="select"] > div { background: #1f2937 !important; color: #f8fafc !important; border-color: #475569 !important; }
    [data-testid="stSidebar"] { background: #080d18 !important; }
    [data-testid="stSidebar"] * { color: #e5e7eb; }
    [data-testid="stAlert"] { color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

filtered = df.copy()
if cat != "All categories":
    filtered = filtered[filtered["Category"] == cat]
if country != "All countries":
    filtered = filtered[filtered["Country"] == country]
if channel != "All channels":
    filtered = filtered[filtered["SalesChannel"] == channel]
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    filtered = filtered[(filtered["OrderDate"].dt.date >= date_range[0]) & (filtered["OrderDate"].dt.date <= date_range[1])]
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    filtered = filtered[filtered["OrderDate"].dt.date == date_range[0]]
if search.strip():
    filtered = filtered[filtered["Product"].astype("string").str.contains(search.strip(), case=False, na=False, regex=False)]

st.markdown('<p style="color:#64748b;letter-spacing:2px;font-size:12px;font-weight:700;margin-bottom:0;">ANALYTICS WORKSPACE / E-COMMERCE</p>', unsafe_allow_html=True)
st.title("ðŸ“‚ Data Upload & Preview" if page == "Data Upload" else "Business overview")
st.markdown('<p class="muted">Upload, inspect and validate your dataset.</p>' if page == "Data Upload" else '<p class="muted">Track revenue, product performance and customer activity in one place.</p>', unsafe_allow_html=True)
head1, head2 = st.columns([5,1])
head1.caption(f"Showing {len(filtered):,} of {len(df):,} rows after filters")
head2.download_button("â¬‡ Export data", filtered.to_csv(index=False).encode("utf-8"), "shopsense_filtered_orders.csv", "text/csv")

if filtered.empty:
    st.warning("No records match these filters. Clear a filter or widen the date range.")
    st.stop()

revenue = float(filtered["Sales"].sum())
profit = float(filtered["Profit"].sum())
orders = int(filtered["OrderID"].nunique())
customers = int(filtered["CustomerID"].nunique())
products = int(filtered["Product"].nunique())
aov = revenue / orders if orders else 0
margin = profit / revenue * 100 if revenue else 0

if page != "Dataset":
    a,b,c,d = st.columns(4)
    a.metric("Total revenue", f"{revenue:,.2f}")
    b.metric("Average order value", f"{aov:,.2f}")
    c.metric("Total customers", f"{customers:,}")
    d.metric("Active products", f"{products:,}")
    st.write("")

def chart_style(fig):
    fig.patch.set_facecolor("white")
    for ax in fig.axes:
        ax.set_facecolor("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", color="#e9edf5", linewidth=.7)
        ax.set_axisbelow(True)
        ax.tick_params(colors="#64748b", labelsize=8)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

def heading(title, subtitle):
    st.markdown(f"### {title}")
    st.caption(subtitle)

if page == "Overview":
    left, right = st.columns([1.6,1], gap="large")
    with left:
        with st.container(border=True):
            heading("ðŸ“ˆ Revenue trend", "Monthly revenue for the selected period")
            monthly = filtered.groupby("YearMonth", as_index=False)["Sales"].sum().sort_values("YearMonth")
            fig, ax = plt.subplots(figsize=(8,3.2))
            ax.plot(monthly["YearMonth"], monthly["Sales"], marker="o", linewidth=2.5)
            ax.fill_between(range(len(monthly)), monthly["Sales"].values, alpha=.08)
            ax.set_xticks(range(len(monthly)))
            ax.set_xticklabels(monthly["YearMonth"], rotation=35, ha="right")
            ax.set_ylabel("Revenue")
            chart_style(fig)
    with right:
        with st.container(border=True):
            heading("ðŸŒ Revenue by country", "Top countries by revenue")
            country_sales = filtered.groupby("Country")["Sales"].sum().sort_values().tail(8)
            fig, ax = plt.subplots(figsize=(5,3.2))
            country_sales.plot(kind="barh", ax=ax)
            ax.set_xlabel("Revenue")
            ax.set_ylabel("")
            chart_style(fig)
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            heading("ðŸ“Š Category performance", "Revenue and profit by category")
            category = filtered.groupby("Category")[["Sales","Profit"]].sum().sort_values("Sales", ascending=False)
            fig, ax = plt.subplots(figsize=(6,3.2))
            category.plot(kind="bar", ax=ax)
            ax.set_ylabel("Amount")
            ax.tick_params(axis="x", rotation=20)
            ax.legend(["Revenue","Profit"], frameon=False)
            chart_style(fig)
    with right:
        with st.container(border=True):
            heading("ðŸ† Best-selling products", "Top 10 products ranked by revenue")
            best = filtered.groupby("Product", as_index=False).agg(Quantity_Sold=("Quantity","sum"), Revenue=("Sales","sum"), Profit=("Profit","sum")).sort_values("Revenue", ascending=False).head(10)
            best = best.rename(columns={"Quantity_Sold":"Quantity sold"})
            st.dataframe(best, use_container_width=True, hide_index=True)
    p1,p2,p3 = st.columns(3)
    p1.metric("Total profit", f"{profit:,.2f}")
    p2.metric("Profit margin", f"{margin:.1f}%")
    p3.metric("Distinct orders", f"{orders:,}")

elif page == "Revenue Analytics":
    left,right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            heading("Monthly revenue", "Revenue by calendar month")
            monthly = filtered.groupby("YearMonth")["Sales"].sum().sort_index()
            fig,ax=plt.subplots(figsize=(7,3.5))
            monthly.plot(kind="line", marker="o", ax=ax)
            ax.set_ylabel("Revenue")
            ax.tick_params(axis="x", rotation=35)
            chart_style(fig)
    with right:
        with st.container(border=True):
            heading("Revenue by sales channel", "Compare sales channels")
            ch = filtered.groupby("SalesChannel")["Sales"].sum().sort_values(ascending=False)
            fig,ax=plt.subplots(figsize=(7,3.5))
            ch.plot(kind="bar", ax=ax)
            ax.set_ylabel("Revenue")
            ax.tick_params(axis="x", rotation=15)
            chart_style(fig)
    summary = filtered.groupby("Country").agg(Revenue=("Sales","sum"), Profit=("Profit","sum"), Orders=("OrderID","nunique"), Customers=("CustomerID","nunique")).sort_values("Revenue",ascending=False).reset_index()
    with st.container(border=True):
        heading("Country summary", "Revenue, profit, orders and customers by country")
        st.dataframe(summary, use_container_width=True, hide_index=True)
        st.download_button("â¬‡ Download country summary", summary.to_csv(index=False).encode("utf-8"), "shopsense_country_summary.csv", "text/csv")

elif page == "Product Performance":
    summary = filtered.groupby(["Product","Category"], as_index=False).agg(Quantity_Sold=("Quantity","sum"), Revenue=("Sales","sum"), Profit=("Profit","sum"), Orders=("OrderID","nunique")).sort_values("Revenue",ascending=False)
    left,right=st.columns(2,gap="large")
    with left:
        with st.container(border=True):
            heading("Top products by revenue", "Top 10 products in this selection")
            top=summary.head(10).sort_values("Revenue")
            fig,ax=plt.subplots(figsize=(7,4))
            ax.barh(top["Product"],top["Revenue"])
            ax.set_xlabel("Revenue")
            chart_style(fig)
    with right:
        with st.container(border=True):
            heading("Top products by profit", "Products ranked by profit")
            top=summary.sort_values("Profit").tail(10)
            fig,ax=plt.subplots(figsize=(7,4))
            ax.barh(top["Product"],top["Profit"])
            ax.set_xlabel("Profit")
            chart_style(fig)
    with st.container(border=True):
        heading("Product performance table", "Compare product-level results")
        st.dataframe(summary.rename(columns={"Quantity_Sold":"Quantity sold"}), use_container_width=True, hide_index=True)
        st.download_button("â¬‡ Download product report", summary.to_csv(index=False).encode("utf-8"), "shopsense_product_report.csv", "text/csv")

elif page == "Customers & Orders":
    left,right=st.columns(2,gap="large")
    with left:
        with st.container(border=True):
            heading("Orders by payment method", "Distinct order count")
            payment=filtered.groupby("PaymentMethod")["OrderID"].nunique().sort_values(ascending=False)
            fig,ax=plt.subplots(figsize=(7,3.5))
            payment.plot(kind="bar",ax=ax)
            ax.set_ylabel("Orders")
            ax.tick_params(axis="x",rotation=20)
            chart_style(fig)
    with right:
        with st.container(border=True):
            heading("Orders by sales channel", "Distinct orders by channel")
            channels=filtered.groupby("SalesChannel")["OrderID"].nunique().sort_values(ascending=False)
            fig,ax=plt.subplots(figsize=(7,3.5))
            channels.plot(kind="bar",ax=ax)
            ax.set_ylabel("Orders")
            ax.tick_params(axis="x",rotation=15)
            chart_style(fig)
    customer_summary=filtered.groupby("CustomerID",as_index=False).agg(Orders=("OrderID","nunique"),Revenue=("Sales","sum"),Profit=("Profit","sum"),Last_Order=("OrderDate","max")).sort_values("Revenue",ascending=False)
    with st.container(border=True):
        heading("Customer summary", "Customer-level order and revenue summary")
        st.dataframe(customer_summary,use_container_width=True,hide_index=True)
        st.download_button("â¬‡ Download customer report",customer_summary.to_csv(index=False).encode("utf-8"),"shopsense_customer_summary.csv","text/csv")

elif page == "Dataset":
    with st.container(border=True):
        heading("Filtered dataset", "Records matching the selected filters")
        st.dataframe(filtered,use_container_width=True,hide_index=True)
        st.caption(f"{len(filtered):,} rows â€¢ {len(filtered.columns)} columns")
        st.download_button("â¬‡ Download filtered dataset",filtered.to_csv(index=False).encode("utf-8"),"shopsense_filtered_orders.csv","text/csv")
    with st.container(border=True):
        heading("Data quality", "Basic checks after cleaning")
        q1,q2,q3=st.columns(3)
        q1.metric("Duplicate rows",int(filtered.duplicated().sum()))
        q2.metric("Missing cells",int(filtered.isna().sum().sum()))
        q3.metric("Columns",len(filtered.columns))

elif page == "Data Upload":
    st.title("ðŸ“‚ Data Upload & Preview")
    st.caption("Inspect the active dataset before using the analytics pages.")
    st.info(f"Active source: {active_source_label}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Valid rows", f"{len(df):,}")
    m2.metric("Columns", f"{len(df.columns):,}")
    m3.metric("Duplicate rows", f"{int(df.duplicated().sum()):,}")
    with st.container(border=True):
        heading("Dataset preview", "Showing up to the first 100 rows of the active dataset")
        st.dataframe(df.head(100), use_container_width=True, hide_index=True)
    with st.container(border=True):
        heading("Column information", "Column names, inferred data types and missing values")
        column_info = pd.DataFrame({
            "Column": df.columns.astype(str),
            "Data type": [str(dtype) for dtype in df.dtypes],
            "Missing values": [int(df[column].isna().sum()) for column in df.columns],
            "Unique values": [int(df[column].nunique(dropna=True)) for column in df.columns],
        })
        st.dataframe(column_info, use_container_width=True, hide_index=True)
    st.download_button(
        "â¬‡ Download active dataset",
        df.to_csv(index=False).encode("utf-8"),
        "shopsense_active_dataset.csv",
        "text/csv",
    )

elif page == "Data Cleaning":
    st.title("ðŸ§¹ Data Cleaning Workspace")
    st.caption("Prepare a cleaner copy of the active dataset without overwriting your original CSV or SQLite database.")
    st.info(f"Active source: {active_source_label}")
    st.warning(
        "Note: the current dataset loader validates required fields before this page opens. "
        "Rows with missing required fields or invalid core values may already have been excluded. "
        "This workspace cleans a separate copy of the active, validated dataset."
    )

    before_rows = len(df)
    before_duplicates = int(df.duplicated().sum())
    before_missing = int(df.isna().sum().sum())
    q1, q2, q3 = st.columns(3)
    q1.metric("Rows before cleaning", f"{before_rows:,}")
    q2.metric("Duplicate rows", f"{before_duplicates:,}")
    q3.metric("Missing cells", f"{before_missing:,}")

    with st.form("shopsense_cleaning_form"):
        st.subheader("Choose cleaning operations")
        remove_duplicates = st.checkbox("Remove exact duplicate rows", value=True)
        trim_text = st.checkbox("Trim extra spaces from text values", value=True)
        fill_missing = st.checkbox("Fill remaining missing values", value=False)
        numeric_fill = st.selectbox(
            "Numeric columns: fill missing values with",
            ["Median", "Zero"],
            disabled=not fill_missing,
        )
        text_fill = st.selectbox(
            "Text columns: fill missing values with",
            ["Unknown", "Most frequent value"],
            disabled=not fill_missing,
        )
        run_cleaning = st.form_submit_button("Apply cleaning to a copy", type="primary")

    if run_cleaning:
        cleaned_df = df.copy()
        if trim_text:
            text_cols = cleaned_df.select_dtypes(include=["object", "string"]).columns
            for column in text_cols:
                cleaned_df[column] = cleaned_df[column].map(
                    lambda value: value.strip() if isinstance(value, str) else value
                )
        if remove_duplicates:
            cleaned_df = cleaned_df.drop_duplicates().copy()
        if fill_missing:
            for column in cleaned_df.columns:
                if not cleaned_df[column].isna().any():
                    continue
                if pd.api.types.is_numeric_dtype(cleaned_df[column]):
                    if numeric_fill == "Zero":
                        fill_value = 0
                    else:
                        median_value = cleaned_df[column].median()
                        fill_value = 0 if pd.isna(median_value) else median_value
                    cleaned_df[column] = cleaned_df[column].fillna(fill_value)
                elif pd.api.types.is_datetime64_any_dtype(cleaned_df[column]):
                    # Keep missing dates missing rather than inventing dates.
                    continue
                elif text_fill == "Unknown":
                    cleaned_df[column] = cleaned_df[column].fillna("Unknown")
                else:
                    modes = cleaned_df[column].mode(dropna=True)
                    if not modes.empty:
                        cleaned_df[column] = cleaned_df[column].fillna(modes.iloc[0])
                    else:
                        cleaned_df[column] = cleaned_df[column].fillna("Unknown")

        after_rows = len(cleaned_df)
        after_duplicates = int(cleaned_df.duplicated().sum())
        after_missing = int(cleaned_df.isna().sum().sum())
        st.success("Cleaning completed on a separate copy. Your source dataset and SQLite database were not changed.")
        r1, r2, r3 = st.columns(3)
        r1.metric("Rows after cleaning", f"{after_rows:,}", delta=f"{after_rows - before_rows:+,} rows")
        r2.metric("Duplicate rows remaining", f"{after_duplicates:,}", delta=f"{before_duplicates - after_duplicates:+,} removed")
        r3.metric("Missing cells remaining", f"{after_missing:,}", delta=f"{before_missing - after_missing:+,} handled")

        with st.container(border=True):
            heading("Cleaned dataset preview", "Review the result before downloading")
            st.dataframe(cleaned_df.head(100), use_container_width=True, hide_index=True)
        st.download_button(
            "â¬‡ Download cleaned CSV",
            cleaned_df.to_csv(index=False).encode("utf-8-sig"),
            "shopsense_cleaned_dataset.csv",
            "text/csv",
            key="download_cleaned_dataset",
        )
    else:
        st.caption("Choose the operations you want, then click Apply cleaning to a copy. Nothing is changed until you apply the operations.")



elif page == "Data Quality Report":
    st.title("ðŸ©º Data Quality Report")
    st.caption("Review completeness, duplicates, column types, and selected data checks for the active dataset.")
    st.info(f"Active source: {active_source_label}")
    st.warning(
        "This report analyses the active dataset after the current loader's validation. "
        "Some invalid rows may already have been excluded during upload; this is not a raw-file audit."
    )

    quality_df = df.copy()
    row_count, column_count = quality_df.shape
    total_cells = row_count * column_count
    missing_cells = int(quality_df.isna().sum().sum())
    duplicate_rows = int(quality_df.duplicated().sum())
    completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells else 100.0

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Rows", f"{row_count:,}")
    metric2.metric("Columns", f"{column_count:,}")
    metric3.metric("Duplicate rows", f"{duplicate_rows:,}")
    metric4.metric("Completeness", f"{completeness:.2f}%")

    st.subheader("Missing values by column")
    missing_report = pd.DataFrame({
        "Column": quality_df.columns.astype(str),
        "Data type": [str(dtype) for dtype in quality_df.dtypes],
        "Missing values": [int(quality_df[col].isna().sum()) for col in quality_df.columns],
        "Missing %": [round(float(quality_df[col].isna().mean() * 100), 2) if row_count else 0.0 for col in quality_df.columns],
        "Unique values": [int(quality_df[col].nunique(dropna=True)) for col in quality_df.columns],
    })
    st.dataframe(missing_report, use_container_width=True, hide_index=True)

    st.subheader("Selected data checks")
    checks = []
    def add_check(name, count, meaning):
        checks.append({"Check": name, "Flagged rows": int(count), "Meaning": meaning})

    if "Quantity" in quality_df.columns:
        quantity_values = pd.to_numeric(quality_df["Quantity"], errors="coerce")
        add_check("Quantity is zero or negative", (quantity_values <= 0).sum(), "Review rows where quantity is not positive.")
        add_check("Quantity is missing or non-numeric", quantity_values.isna().sum(), "Values could not be interpreted as numbers or are missing.")
    if "Sales" in quality_df.columns:
        sales_values = pd.to_numeric(quality_df["Sales"], errors="coerce")
        add_check("Sales is negative", (sales_values < 0).sum(), "Negative sales may need review; refunds/returns can be legitimate.")
        add_check("Sales is missing or non-numeric", sales_values.isna().sum(), "Values could not be interpreted as numbers or are missing.")
    if "UnitPrice" in quality_df.columns:
        price_values = pd.to_numeric(quality_df["UnitPrice"], errors="coerce")
        add_check("Unit price is negative", (price_values < 0).sum(), "Negative prices may need review.")
        add_check("Unit price is missing or non-numeric", price_values.isna().sum(), "Values could not be interpreted as numbers or are missing.")
    if "OrderDate" in quality_df.columns:
        parsed_dates = pd.to_datetime(quality_df["OrderDate"], errors="coerce")
        add_check("Order date is missing or invalid", parsed_dates.isna().sum(), "Date is missing or could not be parsed.")
    if not checks:
        checks.append({"Check": "No predefined checks available", "Flagged rows": 0, "Meaning": "This dataset does not contain the columns used by the current checks."})
    checks_df = pd.DataFrame(checks)
    st.dataframe(checks_df, use_container_width=True, hide_index=True)

    st.subheader("Overall assessment")
    if missing_cells == 0 and duplicate_rows == 0 and all(item["Flagged rows"] == 0 for item in checks):
        st.success("No issues were flagged by the checks available in this report.")
    else:
        st.info("Review the flagged counts above. A flagged value is a prompt for review, not always proof of an error (for example, negative sales may represent a return).")

    summary_rows = [
        {"Metric": "Rows", "Value": row_count},
        {"Metric": "Columns", "Value": column_count},
        {"Metric": "Missing cells", "Value": missing_cells},
        {"Metric": "Duplicate rows", "Value": duplicate_rows},
        {"Metric": "Completeness percent", "Value": round(completeness, 2)},
    ]
    summary_rows.extend({"Metric": f"Check: {item['Check']}", "Value": item["Flagged rows"]} for item in checks)
    report_csv = pd.DataFrame(summary_rows).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "â¬‡ Download quality report (CSV)",
        report_csv,
        "shopsense_data_quality_report.csv",
        "text/csv",
        key="download_quality_report",
    )
    st.download_button(
        "â¬‡ Download column profile (CSV)",
        missing_report.to_csv(index=False).encode("utf-8-sig"),
        "shopsense_column_quality_profile.csv",
        "text/csv",
        key="download_column_quality_profile",
    )

elif page == "Export Center":
    st.title("ðŸ“¦ Export Center")
    st.caption("Download the active dataset and useful business reports in one place. Exports use the current dataset and sidebar filters.")
    st.info(f"Active source: {active_source_label} Â· {len(filtered):,} filtered rows")

    if filtered.empty:
        st.warning("No rows match the current filters. Adjust the filters in the sidebar to export data.")
    else:
        export_df = filtered.copy()
        export_df["OrderDate"] = pd.to_datetime(export_df["OrderDate"], errors="coerce")
        def csv_bytes(frame):
            return frame.to_csv(index=False).encode("utf-8-sig")

        st.subheader("1. Dataset export")
        st.download_button(
            "â¬‡ Download filtered dataset (CSV)",
            csv_bytes(export_df),
            "shopsense_filtered_dataset.csv",
            "text/csv",
            key="export_center_filtered_dataset",
        )
        st.caption("This export includes rows matching the selected category, country, channel, date range and product search.")

        st.subheader("2. Business reports")
        report_frames = {}

        if "Category" in export_df.columns:
            category_report = export_df.groupby("Category", dropna=False).agg(
                Total_Orders=("OrderID", "nunique"),
                Total_Units=("Quantity", "sum"),
                Total_Revenue=("Sales", "sum"),
                Total_Profit=("Profit", "sum"),
            ).reset_index()
            category_report["Profit_Margin_Percent"] = (category_report["Total_Profit"].div(category_report["Total_Revenue"].replace(0, float("nan"))) * 100).round(2)
            category_report = category_report.sort_values("Total_Revenue", ascending=False)
            report_frames["category_summary"] = category_report

        monthly_source = export_df.dropna(subset=["OrderDate"]).copy()
        if not monthly_source.empty:
            monthly_source["YearMonth"] = monthly_source["OrderDate"].dt.to_period("M").astype(str)
            monthly_report = monthly_source.groupby("YearMonth", dropna=False).agg(
                Total_Orders=("OrderID", "nunique"),
                Total_Revenue=("Sales", "sum"),
                Total_Profit=("Profit", "sum"),
            ).reset_index().sort_values("YearMonth")
            report_frames["monthly_summary"] = monthly_report

        if "Product" in export_df.columns:
            product_report = export_df.groupby("Product", dropna=False).agg(
                Total_Orders=("OrderID", "nunique"),
                Total_Units=("Quantity", "sum"),
                Total_Revenue=("Sales", "sum"),
                Total_Profit=("Profit", "sum"),
            ).reset_index().sort_values("Total_Revenue", ascending=False)
            report_frames["product_performance"] = product_report

        if "CustomerID" in export_df.columns:
            customer_report = export_df.groupby("CustomerID", dropna=False).agg(
                Total_Orders=("OrderID", "nunique"),
                Total_Revenue=("Sales", "sum"),
                Total_Profit=("Profit", "sum"),
            ).reset_index().sort_values("Total_Revenue", ascending=False)
            report_frames["customer_summary"] = customer_report

        if "SalesChannel" in export_df.columns:
            channel_report = export_df.groupby("SalesChannel", dropna=False).agg(
                Total_Orders=("OrderID", "nunique"),
                Total_Revenue=("Sales", "sum"),
                Total_Profit=("Profit", "sum"),
            ).reset_index()
            channel_report["Profit_Margin_Percent"] = (channel_report["Total_Profit"].div(channel_report["Total_Revenue"].replace(0, float("nan"))) * 100).round(2)
            report_frames["sales_channel_summary"] = channel_report.sort_values("Total_Revenue", ascending=False)

        total_cells = int(export_df.shape[0] * export_df.shape[1])
        missing_cells = int(export_df.isna().sum().sum())
        completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells else 100.0
        column_profile = pd.DataFrame({
            "Column": export_df.columns.astype(str),
            "Data_Type": [str(dtype) for dtype in export_df.dtypes],
            "Missing_Values": [int(export_df[col].isna().sum()) for col in export_df.columns],
            "Missing_Percent": [round(float(export_df[col].isna().mean() * 100), 2) if len(export_df) else 0.0 for col in export_df.columns],
            "Unique_Values": [int(export_df[col].nunique(dropna=True)) for col in export_df.columns],
        })
        quality_summary = pd.DataFrame([
            {"Metric": "Rows", "Value": len(export_df)},
            {"Metric": "Columns", "Value": len(export_df.columns)},
            {"Metric": "Duplicate rows", "Value": int(export_df.duplicated().sum())},
            {"Metric": "Missing cells", "Value": missing_cells},
            {"Metric": "Completeness percent", "Value": round(completeness, 2)},
        ])
        report_frames["column_quality_profile"] = column_profile
        report_frames["quality_summary"] = quality_summary

        cols = st.columns(2)
        for idx, (report_name, report_df) in enumerate(report_frames.items()):
            with cols[idx % 2]:
                st.download_button(
                    f"â¬‡ {report_name.replace('_', ' ').title()} (CSV)",
                    csv_bytes(report_df),
                    f"shopsense_{report_name}.csv",
                    "text/csv",
                    key=f"export_center_{report_name}",
                )

        st.subheader("3. Download all exports together")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("shopsense_filtered_dataset.csv", csv_bytes(export_df))
            for report_name, report_df in report_frames.items():
                archive.writestr(f"shopsense_{report_name}.csv", csv_bytes(report_df))
            readme = (
                "ShopSense Export Center\n"
                f"Active source: {active_source_label}\n"
                f"Rows exported after filters: {len(export_df)}\n"
                "Reports are calculated from the active dataset after the current sidebar filters.\n"
                "Completeness percent is based only on non-missing cells; it is not an overall quality score.\n"
            )
            archive.writestr("README_export_notes.txt", readme)
        st.download_button(
            "ðŸ“¦ Download complete export bundle (ZIP)",
            zip_buffer.getvalue(),
            "shopsense_export_bundle.zip",
            "application/zip",
            key="export_center_bundle",
            type="primary",
        )
        st.caption("Exports are generated in memory. The original CSV and SQLite database are not overwritten.")

elif page == "SQL Workspace":
    st.title("ðŸ§ª SQL Workspace")
    st.caption("Write and run read-only SQL queries against the active dataset. Results can be previewed and downloaded.")
    st.info(f"Active source: {active_source_label}")
    st.warning(
        "Safety: this workspace runs queries against a temporary in-memory database. "
        "Only SELECT/CTE queries are allowed; your original CSV and shopsense.db are not modified."
    )

    example_queries = {
        "Choose an exampleâ€¦": "",
        "Top 10 products by revenue": """SELECT Product, ROUND(SUM(Sales), 2) AS Revenue
FROM orders
GROUP BY Product
ORDER BY Revenue DESC
LIMIT 10""",
        "Revenue by category": """SELECT Category, ROUND(SUM(Sales), 2) AS Revenue,
       ROUND(SUM(Profit), 2) AS Profit
FROM orders
GROUP BY Category
ORDER BY Revenue DESC""",
        "Monthly revenue": """SELECT strftime('%Y-%m', OrderDate) AS Month,
       ROUND(SUM(Sales), 2) AS Revenue
FROM orders
GROUP BY Month
ORDER BY Month""",
        "Top countries by sales": """SELECT Country, ROUND(SUM(Sales), 2) AS Revenue,
       COUNT(DISTINCT OrderID) AS Orders
FROM orders
GROUP BY Country
ORDER BY Revenue DESC
LIMIT 10""",
        "Order summary": """SELECT COUNT(DISTINCT OrderID) AS Total_Orders,
       COUNT(DISTINCT CustomerID) AS Total_Customers,
       ROUND(SUM(Sales), 2) AS Total_Revenue,
       ROUND(SUM(Profit), 2) AS Total_Profit
FROM orders""",
        "Low-profit products": """SELECT Product, Category,
       ROUND(SUM(Sales), 2) AS Revenue,
       ROUND(SUM(Profit), 2) AS Profit
FROM orders
GROUP BY Product, Category
ORDER BY Profit ASC
LIMIT 10""",
    }
    selected_example = st.selectbox("Load an example query", list(example_queries.keys()))
    default_query = example_queries[selected_example] or "SELECT * FROM orders LIMIT 10;"
    query = st.text_area("SQL query", value=default_query, height=220, key="shopsense_sql_query")
    st.caption("Available table: `orders` Â· Use SQLite syntax. Example: SELECT Category, SUM(Sales) FROM orders GROUP BY Category;")

    if st.button("â–¶ Run query", type="primary", key="run_readonly_sql"):
        cleaned_query = query.strip()
        # Permit a single SELECT or WITH statement only; reject additional statements.
        without_trailing_semicolon = cleaned_query[:-1].rstrip() if cleaned_query.endswith(";") else cleaned_query
        if not without_trailing_semicolon:
            st.error("Please enter a SQL query.")
        elif ";" in without_trailing_semicolon:
            st.error("Only one SQL statement is allowed at a time.")
        elif not re.match(r"(?is)^(SELECT|WITH)\b", without_trailing_semicolon):
            st.error("Only SELECT queries (including WITH/CTE queries) are allowed.")
        else:
            sql_connection = sqlite3.connect(":memory:")
            try:
                # The active dataframe is copied into a temporary database; no disk DB is touched.
                sql_df = df.copy()
                if "OrderDate" in sql_df.columns:
                    sql_df["OrderDate"] = pd.to_datetime(sql_df["OrderDate"], errors="coerce").dt.strftime("%Y-%m-%d")
                sql_df.to_sql("orders", sql_connection, index=False, if_exists="replace")

                denied_actions = {
                    getattr(sqlite3, name) for name in [
                        "SQLITE_INSERT", "SQLITE_UPDATE", "SQLITE_DELETE",
                        "SQLITE_CREATE_INDEX", "SQLITE_CREATE_TABLE", "SQLITE_CREATE_TEMP_INDEX",
                        "SQLITE_CREATE_TEMP_TABLE", "SQLITE_CREATE_TEMP_TRIGGER", "SQLITE_CREATE_TEMP_VIEW",
                        "SQLITE_CREATE_TRIGGER", "SQLITE_CREATE_VIEW", "SQLITE_DROP_INDEX",
                        "SQLITE_DROP_TABLE", "SQLITE_DROP_TEMP_INDEX", "SQLITE_DROP_TEMP_TABLE",
                        "SQLITE_DROP_TEMP_TRIGGER", "SQLITE_DROP_TEMP_VIEW", "SQLITE_DROP_TRIGGER",
                        "SQLITE_DROP_VIEW", "SQLITE_ALTER_TABLE", "SQLITE_ATTACH", "SQLITE_DETACH",
                        "SQLITE_PRAGMA", "SQLITE_TRANSACTION", "SQLITE_SAVEPOINT", "SQLITE_REINDEX",
                        "SQLITE_ANALYZE",
                    ] if hasattr(sqlite3, name)
                }
                def readonly_authorizer(action, arg1, arg2, database_name, trigger_name):
                    return sqlite3.SQLITE_DENY if action in denied_actions else sqlite3.SQLITE_OK
                sql_connection.set_authorizer(readonly_authorizer)
                result_df = pd.read_sql_query(without_trailing_semicolon, sql_connection)
                st.session_state["shopsense_sql_last_result"] = result_df
                st.session_state["shopsense_sql_last_query"] = cleaned_query
                st.success(f"Query ran successfully Â· {len(result_df):,} rows returned.")
            except Exception as exc:
                st.error(f"Query could not run: {exc}")
            finally:
                sql_connection.close()

    if "shopsense_sql_last_result" in st.session_state:
        result_df = st.session_state["shopsense_sql_last_result"]
        st.subheader("Query results")
        st.caption(f"Last query: {st.session_state.get('shopsense_sql_last_query', '')}")
        st.metric("Rows returned", f"{len(result_df):,}")
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        st.download_button(
            "â¬‡ Download query results (CSV)",
            result_df.to_csv(index=False).encode("utf-8-sig"),
            "shopsense_sql_results.csv",
            "text/csv",
            key="download_sql_results",
        )

elif page == "SQL Business Insights":
    st.title("ðŸ§  SQL Business Insights")
    st.write("SQL queries current dataset aur sidebar filters par run hoti hain. Uploaded CSV se SQLite in-memory table banti hai; saved shopsense.db change nahi hota.")

    # Use an in-memory SQLite database populated from the active filtered data.
    # This keeps SQL results consistent with uploaded CSVs and the sidebar filters.
    connection = sqlite3.connect(":memory:")
    try:
        sql_source = filtered.copy()
        sql_source.to_sql("orders", connection, if_exists="replace", index=False)

        sql_kpis = pd.read_sql_query("""
            SELECT
                ROUND(COALESCE(SUM(Sales), 0), 2) AS Total_Revenue,
                COUNT(DISTINCT OrderID) AS Total_Orders,
                COUNT(DISTINCT CustomerID) AS Total_Customers,
                ROUND(SUM(Sales) * 1.0 / NULLIF(COUNT(DISTINCT OrderID), 0), 2) AS Average_Order_Value
            FROM orders
        """, connection)
        kpi = sql_kpis.iloc[0]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Revenue", f"â‚¹{float(kpi['Total_Revenue'] or 0):,.2f}")
        k2.metric("Total Orders", f"{int(kpi['Total_Orders'] or 0):,}")
        k3.metric("Total Customers", f"{int(kpi['Total_Customers'] or 0):,}")
        aov_value = 0.0 if pd.isna(kpi["Average_Order_Value"]) else float(kpi["Average_Order_Value"])
        k4.metric("Average Order Value", f"â‚¹{aov_value:,.2f}")

        st.subheader("ðŸ† Top 5 Products by Revenue")
        top_products = pd.read_sql_query("""
            SELECT Product, ROUND(SUM(Sales), 2) AS Revenue
            FROM orders
            GROUP BY Product
            ORDER BY Revenue DESC, Product ASC
            LIMIT 5
        """, connection)
        st.dataframe(top_products, hide_index=True, use_container_width=True)

        st.subheader("ðŸ“¦ Revenue by Category")
        category_sql = pd.read_sql_query("""
            SELECT Category, ROUND(SUM(Sales), 2) AS Revenue,
                   ROUND(SUM(Profit), 2) AS Profit,
                   COUNT(DISTINCT OrderID) AS Orders
            FROM orders
            GROUP BY Category
            ORDER BY Revenue DESC
        """, connection)
        st.dataframe(category_sql, hide_index=True, use_container_width=True)
        if not category_sql.empty:
            st.bar_chart(category_sql.set_index("Category")["Revenue"])

        st.subheader("ðŸ›’ Sales Channel Performance")
        channel_sql = pd.read_sql_query("""
            SELECT SalesChannel, ROUND(SUM(Sales), 2) AS Revenue,
                   ROUND(SUM(Profit), 2) AS Profit,
                   COUNT(DISTINCT OrderID) AS Orders
            FROM orders
            GROUP BY SalesChannel
            ORDER BY Revenue DESC
        """, connection)
        st.dataframe(channel_sql, hide_index=True, use_container_width=True)

        st.download_button(
            "â¬‡ Download SQL Business Insights (CSV)",
            top_products.to_csv(index=False).encode("utf-8-sig"),
            "shopsense_sql_business_insights_top_products.csv",
            "text/csv",
            key="download_sql_business_insights_top_products",
        )
        with st.expander("View SQL used for this page"):
            st.code("""SELECT Product, ROUND(SUM(Sales), 2) AS Revenue
FROM orders
GROUP BY Product
ORDER BY Revenue DESC, Product ASC
LIMIT 5;""", language="sql")
    finally:
        connection.close()

elif page == "Business Insights & Recommendations":
    st.title("ðŸ’¡ Business Insights & Recommendations")
    st.write("Filtered sales data se business performance samjho aur actionable recommendations pao.")

    if filtered.empty:
        st.warning("Selected filters ke liye koi data available nahi hai.")
    else:
        # 1. Category performance
        category_summary = (
            filtered.groupby("Category", as_index=False)
            .agg(
                Revenue=("Sales", "sum"),
                Profit=("Profit", "sum"),
                Quantity_Sold=("Quantity", "sum")
            )
            .sort_values("Revenue", ascending=False)
        )

        # 2. Country performance
        country_summary = (
            filtered.groupby("Country", as_index=False)
            .agg(
                Revenue=("Sales", "sum"),
                Profit=("Profit", "sum")
            )
            .sort_values("Revenue", ascending=False)
        )

        # 3. Product performance and profit margin
        product_summary = (
            filtered.groupby("Product", as_index=False)
            .agg(
                Revenue=("Sales", "sum"),
                Profit=("Profit", "sum"),
                Quantity_Sold=("Quantity", "sum")
            )
        )

        product_summary["Profit_Margin_%"] = (
            product_summary["Profit"]
            .div(product_summary["Revenue"].replace(0, float("nan")))
            .mul(100)
            .round(2)
        )

        # 4. Monthly revenue
        monthly_revenue = (
            filtered.groupby("YearMonth", as_index=False)
            .agg(Revenue=("Sales", "sum"))
            .sort_values("YearMonth")
        )

        # KPI cards
        total_revenue = filtered["Sales"].sum()
        total_profit = filtered["Profit"].sum()
        profit_margin = (
            total_profit / total_revenue * 100
            if total_revenue != 0 else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Revenue", f"â‚¹{total_revenue:,.2f}")
        c2.metric("Total Profit", f"â‚¹{total_profit:,.2f}")
        c3.metric("Profit Margin", f"{profit_margin:.2f}%")

        st.markdown("---")

        # Category insights
        st.subheader("ðŸ“¦ Category Performance")

        left, right = st.columns(2, gap="large")

        with left:
            st.write("**Revenue by Category**")
            st.bar_chart(category_summary.set_index("Category")["Revenue"])

        with right:
            st.write("**Profit by Category**")
            st.bar_chart(category_summary.set_index("Category")["Profit"])

        best_category = category_summary.iloc[0]

        st.info(
            f"Highest-revenue category: **{best_category['Category']}** "
            f"with revenue of â‚¹{best_category['Revenue']:,.2f}."
        )

        st.dataframe(
            category_summary,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        # Country insights
        st.subheader("ðŸŒ Country Performance")

        best_country = country_summary.iloc[0]

        st.success(
            f"Highest-revenue country: **{best_country['Country']}** "
            f"with revenue of â‚¹{best_country['Revenue']:,.2f}."
        )

        st.bar_chart(country_summary.set_index("Country")["Revenue"])

        st.dataframe(
            country_summary,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        # Product insights
        st.subheader("ðŸ† Product Profitability")

        low_margin_products = (
            product_summary[
                (product_summary["Revenue"] > 0)
                & (product_summary["Profit_Margin_%"] < 10)
            ]
            .sort_values("Revenue", ascending=False)
        )

        if not low_margin_products.empty:
            st.warning(
                "These products have a profit margin below 10%. "
                "Review their costs, pricing and discounts."
            )

            st.dataframe(
                low_margin_products,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(
                "No products with positive revenue and a profit margin "
                "below 10% were found in this selection."
            )

        st.markdown("---")

        # Monthly revenue trend
        st.subheader("ðŸ“ˆ Monthly Revenue Trend")

        if not monthly_revenue.empty:
            st.line_chart(
                monthly_revenue.set_index("YearMonth")["Revenue"]
            )

            if len(monthly_revenue) >= 2:
                previous_revenue = monthly_revenue.iloc[-2]["Revenue"]
                latest_revenue = monthly_revenue.iloc[-1]["Revenue"]

                if previous_revenue != 0:
                    change = (
                        (latest_revenue - previous_revenue)
                        / abs(previous_revenue)
                    ) * 100

                    if change > 0:
                        st.success(
                            f"Revenue increased by {change:.2f}% "
                            "compared with the previous available month."
                        )
                    elif change < 0:
                        st.warning(
                            f"Revenue decreased by {abs(change):.2f}% "
                            "compared with the previous available month."
                        )
                    else:
                        st.info(
                            "Revenue remained unchanged compared with "
                            "the previous available month."
                        )

        st.markdown("---")

        # Recommendations
        st.subheader("ðŸŽ¯ Business Recommendations")

        st.markdown(
            f"""
            1. **Focus on the leading category:** Review what's driving
               revenue in {best_category['Category']} and identify ways
               to sustain its performance.

            2. **Review country-level performance:** Investigate why
               {best_country['Country']} generates the highest revenue
               in the selected data.

            3. **Improve product profitability:** Review costs, pricing
               and discounting for products with low profit margins.

            4. **Monitor monthly trends:** Compare revenue across months
               to identify periods of growth and decline.

            5. **Use filters for comparisons:** Repeat the analysis by
               category, country and sales channel to identify
               differences in performance.
            """
        )

        st.markdown("---")

        # Phase 5: additional data-driven insights
        st.subheader("ðŸ›ï¸ Sales Channel Analysis")
        channel_summary = (
            filtered.groupby("SalesChannel", as_index=False)
            .agg(
                Orders=("OrderID", "nunique"),
                Revenue=("Sales", "sum"),
                Profit=("Profit", "sum"),
            )
            .sort_values("Revenue", ascending=False)
        )
        if not channel_summary.empty:
            channel_summary["Profit_Margin_%"] = (
                channel_summary["Profit"]
                .div(channel_summary["Revenue"].replace(0, float("nan")))
                .mul(100)
                .round(2)
            )
            st.bar_chart(channel_summary.set_index("SalesChannel")[["Revenue", "Profit"]])
            st.dataframe(channel_summary, use_container_width=True, hide_index=True)
            best_channel = channel_summary.iloc[0]
            st.info(
                f"Highest-revenue sales channel in the current filtered data: "
                f"**{best_channel['SalesChannel']}** (â‚¹{best_channel['Revenue']:,.2f}). "
                "Compare its profit margin as well before increasing investment."
            )

        st.markdown("---")
        st.subheader("ðŸ‘¥ Customer Snapshot")
        customer_summary = (
            filtered.groupby("CustomerID", as_index=False)
            .agg(
                Orders=("OrderID", "nunique"),
                Revenue=("Sales", "sum"),
                Profit=("Profit", "sum"),
            )
            .sort_values("Revenue", ascending=False)
        )
        repeat_customers = int((customer_summary["Orders"] > 1).sum()) if not customer_summary.empty else 0
        total_customers = int(customer_summary["CustomerID"].nunique()) if not customer_summary.empty else 0
        total_orders = int(filtered["OrderID"].nunique())
        avg_order_value = float(filtered["Sales"].sum() / total_orders) if total_orders else 0.0
        m1, m2, m3 = st.columns(3)
        m1.metric("Unique Customers", f"{total_customers:,}")
        m2.metric("Repeat Customers", f"{repeat_customers:,}")
        m3.metric("Average Order Value", f"â‚¹{avg_order_value:,.2f}")
        if not customer_summary.empty:
            st.caption("Top customers are ranked by revenue in the currently filtered dataset.")
            st.dataframe(customer_summary.head(10), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("ðŸ§  Automatically Generated Observations")
        observations = []
        if not category_summary.empty:
            top_cat = category_summary.iloc[0]
            observations.append(
                f"**Revenue leader:** {top_cat['Category']} has the highest category revenue "
                f"(â‚¹{top_cat['Revenue']:,.2f}) in the current selection."
            )
            lowest_profit_cat = category_summary.sort_values("Profit").iloc[0]
            observations.append(
                f"**Profit to review:** {lowest_profit_cat['Category']} has the lowest total profit "
                f"(â‚¹{lowest_profit_cat['Profit']:,.2f}) among the displayed categories."
            )
        if not product_summary.empty:
            negative_profit_products = product_summary[product_summary["Profit"] < 0]
            if not negative_profit_products.empty:
                observations.append(
                    f"**Potential loss-making products:** {len(negative_profit_products)} product(s) "
                    "have negative total profit in the current selection. Review costs, discounts, "
                    "returns and data quality before taking action."
                )
            if not low_margin_products.empty:
                observations.append(
                    f"**Low-margin watchlist:** {len(low_margin_products)} product(s) have a margin "
                    "below 10% while revenue is positive."
                )
        if len(monthly_revenue) >= 2:
            prev_val = float(monthly_revenue.iloc[-2]["Revenue"])
            latest_val = float(monthly_revenue.iloc[-1]["Revenue"])
            if prev_val != 0:
                monthly_change = (latest_val - prev_val) / abs(prev_val) * 100
                observations.append(
                    f"**Latest month movement:** revenue changed by {monthly_change:+.2f}% "
                    "versus the previous available month. This is a comparison, not a forecast."
                )
        if not channel_summary.empty:
            profitable_channels = int((channel_summary["Profit"] > 0).sum())
            observations.append(
                f"**Channel check:** {profitable_channels} of {len(channel_summary)} sales channel(s) "
                "show positive total profit in this selection."
            )
        for observation in observations:
            st.markdown(f"- {observation}")
        st.caption(
            "These observations are rule-based summaries of the selected data, not predictions. "
            "Investigate business context and data quality before making decisions."
        )

        # Download reports
        st.download_button(
            "â¬‡ Download Category Report",
            category_summary.to_csv(index=False).encode("utf-8"),
            "shopsense_category_insights.csv",
            "text/csv"
        )

        st.download_button(
            "â¬‡ Download Product Profitability Report",
            product_summary.to_csv(index=False).encode("utf-8"),
            "shopsense_product_profitability.csv",
            "text/csv"
        )

        st.download_button(
            "â¬‡ Download Sales Channel Report",
            channel_summary.to_csv(index=False).encode("utf-8"),
            "shopsense_sales_channel_report.csv",
            "text/csv"
        )

        st.download_button(
            "â¬‡ Download Customer Report",
            customer_summary.to_csv(index=False).encode("utf-8"),
            "shopsense_customer_report.csv",
            "text/csv"
        )


        # Top products are calculated from the same filtered DataFrame as the rest of this page.
        st.subheader("ðŸ† Top 5 Products by Revenue")
        top_products = (
            product_summary[["Product", "Revenue"]]
            .sort_values(["Revenue", "Product"], ascending=[False, True])
            .head(5)
            .copy()
        )
        st.dataframe(top_products, hide_index=True, use_container_width=True)
        st.download_button(
            "â¬‡ï¸ Download Top Products",
            top_products.to_csv(index=False).encode("utf-8-sig"),
            "top_products.csv",
            "text/csv",
            key="download_insights_top_products",
        )


    st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6fb;
        color: #1e293b;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp p,
    .stApp label,
    .stApp span,
    .stApp div {
        color: #1e293b;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #e5e7eb;
    }

    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5eaf2;
        padding: 1rem;
        border-radius: 15px;
    }

    [data-testid="stMetricLabel"] *,
    [data-testid="stMetricValue"] *,
    [data-testid="stMetricDelta"] * {
        color: #1e293b !important;
    }

    .stCaption,
    small {
        color: #64748b !important;
    }
    /* Download button styling */
    .stDownloadButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #2563eb !important;
        border-radius: 10px !important;
        padding: 0.65rem 1rem !important;
        font-weight: 600 !important;
    }

    .stDownloadButton > button:hover {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        border-color: #1d4ed8 !important;
    }

    .stDownloadButton > button p,
    .stDownloadButton > button span,
    .stDownloadButton > button svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)
