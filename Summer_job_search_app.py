# -*- coding: utf-8 -*-
import re
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st
from jobspy import scrape_jobs
from streamlit_gsheets import GSheetsConnection

# --- RELEVANCE CLASSIFICATION LOGIC ---
def classify_relevance(title, desc):
    t_d = (str(title) + " " + str(desc)).lower()
    data_sig = any(k in t_d for k in ["data", "analyst", "python", "sql", "analytics", "statistics", "machine learning", "tableau"])
    strat_sig = any(k in t_d for k in ["strategy", "branding", "product strategy", "growth", "insights", "gtm", "positioning", "go-to-market", "cross-border"])
    
    if data_sig and strat_sig: return "High Relevance (Data + Strategy)"
    if strat_sig: return "Strategy Focus"
    if data_sig: return "Analytics Focus"
    return "Low Relevance"

# --- UI CONFIG ---
st.set_page_config(page_title="Private Job Search Collector", layout="wide")

MASTER_SHEET = "master_jobs"
RAW_SHEET = "raw_jobs_archive"

WORK_MODE_OPTIONS = ["Any", "Remote", "Hybrid", "On-site"]
DURATION_OPTIONS = ["Any", "Project", "Short-term", "Part-time", "Full-time", "Internship"]
DEFAULT_SITE_OPTIONS = ["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"]

# --- DATA SAVING HELPERS ---
def read_sheet_safe(conn, worksheet):
    try:
        df = conn.read(worksheet=worksheet, ttl=0)
        return df if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

def append_unique_rows(conn, worksheet, new_df, key_col="job_uid"):
    existing = read_sheet_safe(conn, worksheet)
    if existing.empty:
        conn.update(worksheet=worksheet, data=new_df)
        return len(new_df)
    
    # Filter out duplicates already in the sheet
    existing_keys = set(existing[key_col].astype(str).tolist())
    to_save = new_df[~new_df[key_col].astype(str).isin(existing_keys)]
    
    if not to_save.empty:
        updated = pd.concat([existing, to_save], ignore_index=True)
        conn.update(worksheet=worksheet, data=updated)
    return len(to_save)

# --- HELPER FUNCTIONS ---
def build_job_uid(row):
    url = str(row.get("job_url", "")).strip().lower()
    if url and url != 'nan': return url
    return f"{str(row.get('job_title')).lower()}|{str(row.get('company')).lower()}"

def standardize_jobs(raw_df, search_term):
    if raw_df is None or raw_df.empty: return pd.DataFrame()
    df = raw_df.copy()
    df = df.rename(columns={"title": "job_title", "location": "location_raw"})
    df["job_uid"] = df.apply(build_job_uid, axis=1)
    df["date_scraped"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["search_term"] = search_term
    df["relevance_label"] = df.apply(lambda x: classify_relevance(x.get('job_title', ''), x.get('description', '')), axis=1)
    return df

# --- STREAMLIT UI ---
st.title("Private Job Search Collector")
st.caption("Summer Search: Strategy & Analytics focus")

conn = st.connection("gsheets", type=GSheetsConnection)

with st.sidebar:
    st.header("Search Setup")
    target_roles = st.text_input("Target roles *", value="Growth Strategy, Marketing Analytics, Customer Insights, Product Strategy, GTM, Go-To-Market, Product Marketing")
    location_input = st.text_input("Location *", value="US")
    country_search = st.text_input("Indeed/Glassdoor Country", value="US")
    work_mode_input = st.selectbox("Work mode", WORK_MODE_OPTIONS, index=1) # Default Remote
    google_search_term = st.text_input("Google Jobs query (Optional)", value="Distributed, Async, Location Agnostic, Cross-Border")
    site_names = st.multiselect("Job Sites", DEFAULT_SITE_OPTIONS, default=DEFAULT_SITE_OPTIONS)
    results_wanted = st.number_input("Results wanted", 10, 300, 200)

search_term = f"{target_roles} {location_input} {work_mode_input}"

if st.button("Run Search", type="primary"):
    scrape_kwargs = {"site_name": site_names, "search_term": search_term, "location": location_input, "results_wanted": results_wanted, "hours_old": 720}
    if google_search_term: scrape_kwargs["google_search_term"] = google_search_term
    
    with st.spinner("Scraping..."):
        raw_jobs = scrape_jobs(**scrape_kwargs)
        if raw_jobs is not None and not raw_jobs.empty:
            st.session_state["clean_jobs_df"] = standardize_jobs(raw_jobs, search_term)
            
            # Show Metrics
            df = st.session_state["clean_jobs_df"]
            high_rel = len(df[df['relevance_label'] == "High Relevance (Data + Strategy)"])
            st.metric("High Relevance Found", high_rel)

if "clean_jobs_df" in st.session_state:
    df = st.session_state["clean_jobs_df"]
    st.dataframe(df[["job_title", "company", "relevance_label", "job_url"]], use_container_width=True)
    
    if st.button("SAVE TO GOOGLE SHEETS"):
        with st.spinner("Syncing to Master Sheet..."):
            saved_count = append_unique_rows(conn, MASTER_SHEET, df)
            st.success(f"Successfully saved {saved_count} new records to '{MASTER_SHEET}'.")
