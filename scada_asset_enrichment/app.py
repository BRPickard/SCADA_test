"""Streamlit MVP app for SCADA asset enrichment."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DB_PATH, OUTPUTS_DIR, UPLOADS_DIR
from src.database import Database
from src.ui.workflow import ingest_and_persist, run_full_pipeline, save_uploaded_documents

st.set_page_config(page_title="SCADA Asset Enrichment MVP", layout="wide")
st.title("SCADA / Industrial Controls Asset Enrichment MVP")

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

db = Database(DB_PATH)
db.init_db()

page = st.sidebar.radio(
    "Pages",
    [
        "Upload Inventory",
        "Review Canonical Assets",
        "Product Master",
        "Upload Datasheets / Manuals",
        "Review Queue",
        "Maintenance Calendar / Due Work",
        "Export Outputs",
    ],
)

if page == "Upload Inventory":
    st.subheader("Upload Inventory Workbook")
    wb = st.file_uploader("Upload .xlsx workbook", type=["xlsx"])
    if wb:
        path = UPLOADS_DIR / wb.name
        path.write_bytes(wb.read())
        normalized = ingest_and_persist(path, db)
        st.success(f"Loaded {len(normalized)} assets from {normalized['source_sheet'].nunique()} sheets")
        st.dataframe(normalized.head(50), use_container_width=True)

elif page == "Review Canonical Assets":
    df = db.fetch_df("SELECT * FROM asset_instances")
    st.subheader("Canonical Asset Instances")
    if df.empty:
        st.info("No assets loaded yet.")
    else:
        site_filter = st.multiselect("Site", sorted(df["site_name_normalized"].dropna().unique()))
        comp_filter = st.multiselect("Component Type", sorted(df["component_type_normalized"].dropna().unique()))
        manu_filter = st.multiselect("Manufacturer", sorted(df["manufacturer_normalized"].dropna().unique()))
        filtered = df.copy()
        if site_filter:
            filtered = filtered[filtered["site_name_normalized"].isin(site_filter)]
        if comp_filter:
            filtered = filtered[filtered["component_type_normalized"].isin(comp_filter)]
        if manu_filter:
            filtered = filtered[filtered["manufacturer_normalized"].isin(manu_filter)]
        st.metric("Total Assets", len(filtered))
        st.dataframe(filtered, use_container_width=True)

elif page == "Product Master":
    if st.button("Run Product Enrichment Pipeline"):
        run_full_pipeline(db)
        st.success("Pipeline complete.")
    products = db.fetch_df("SELECT * FROM product_master")
    if products.empty:
        st.info("Run enrichment pipeline to build product master.")
    else:
        lifecycle_filter = st.multiselect("Lifecycle Status", sorted(products["lifecycle_status"].dropna().unique()))
        review_filter = st.selectbox("Review Required", ["all", "yes", "no"])
        filtered = products.copy()
        if lifecycle_filter:
            filtered = filtered[filtered["lifecycle_status"].isin(lifecycle_filter)]
        if review_filter != "all":
            filtered = filtered[filtered["review_required"] == (1 if review_filter == "yes" else 0)]
        st.metric("Unique Products", len(filtered))
        st.data_editor(filtered, use_container_width=True, key="product_editor")

elif page == "Upload Datasheets / Manuals":
    st.subheader("Upload Vendor Manuals / Datasheets")
    files = st.file_uploader("Upload docs", accept_multiple_files=True)
    if files:
        paths = []
        for f in files:
            p = UPLOADS_DIR / f.name
            p.write_bytes(f.read())
            paths.append(p)
        docs = save_uploaded_documents(paths, db)
        st.success(f"Saved {len(docs)} documents")
        st.dataframe(docs)

elif page == "Review Queue":
    review = db.fetch_df("SELECT * FROM review_queue")
    if review.empty:
        st.info("No review items yet. Run pipeline first.")
    else:
        st.metric("Open Review Items", len(review[review["status"] == "open"]) if "status" in review.columns else len(review))
        st.dataframe(review, use_container_width=True)

elif page == "Maintenance Calendar / Due Work":
    sched = db.fetch_df("SELECT * FROM maintenance_schedule")
    cal = pd.read_csv(OUTPUTS_DIR / "maintenance_calendar_monthly.csv") if (OUTPUTS_DIR / "maintenance_calendar_monthly.csv").exists() else pd.DataFrame()
    if sched.empty:
        st.info("No schedule yet. Run pipeline first.")
    else:
        overdue = (pd.to_datetime(sched["due_date"]) < pd.Timestamp.utcnow()).sum()
        st.metric("Overdue Items", int(overdue))
        st.dataframe(sched, use_container_width=True)
        st.subheader("Monthly Summary")
        st.dataframe(cal, use_container_width=True)

elif page == "Export Outputs":
    st.subheader("Export Files")
    files = [
        "enriched_inventory.csv",
        "enriched_inventory.xlsx",
        "product_master.csv",
        "review_queue.csv",
        "maintenance_schedule.csv",
        "maintenance_calendar_monthly.csv",
    ]
    for fn in files:
        path = OUTPUTS_DIR / fn
        if path.exists():
            st.write(f"✅ {fn}")
            with open(path, "rb") as f:
                st.download_button(f"Download {fn}", data=f.read(), file_name=fn)
        else:
            st.write(f"⚠️ {fn} not generated yet")
