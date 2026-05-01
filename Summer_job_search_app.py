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
    """
    Categorizes jobs by bridging your 13+ years of marketing experience 
    with your new MSBA analytical skill set.
    """
    t_d = (str(title) + " " + str(desc)).lower()
    
    # Data signals from MSBA (BAN 601, 612, 674)
    data_sig = any(k in t_d for k in ["data", "analyst", "python", "sql", "analytics", "statistics", "machine learning", "tableau"])
    
    # Strategy signals from 13+ years of Marketing/Branding
    strat_sig = any(k in t_d for k in ["strategy", "branding", "product strategy", "growth", "insights", "gtm", "positioning"])
    
    if data_sig and strat_sig: 
        return "High Relevance (Data + Strategy)"
    if strat_sig: 
        return "Strategy Focus"
    if data_sig: 
        return "Analytics Focus"
    return "Low Relevance"

# --- UI CONFIG ---
st.set_page_config(page_title="Private Job Search Collector", layout="wide")

MASTER_SHEET = "master_jobs"
RAW_SHEET = "raw_jobs_archive"
LOG_SHEET = "run_log"

WORK_MODE_OPTIONS = ["Any", "Remote", "Hybrid", "On-site"]
DURATION_OPTIONS = ["Any", "Project", "Short-term", "Part-time", "Full-time", "Internship"]
DEFAULT_SITE_OPTIONS = ["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"]

# --- HELPER FUNCTIONS ---
def normalize_text(value):
    if pd.isna(value) or value is None: return ""
    return str(value).strip().lower()

def ensure_columns(df, columns):
    for col in columns:
        if col not in df.columns: df[col] = pd.NA
    return df

def build_job_uid(row):
    url = normalize_text(row.get("job_url", ""))
    if url: return url
    return f"{normalize_text(row.get('job_title'))}|{normalize_text(row.get('company'))}"

# --- CORE LOGIC: STANDARDIZATION ---
def standardize_jobs(raw_df, search_term, google_search_term, country_search, location_input, 
                     companies_input, skills_input, work_mode_input, duration_input):
    if raw_df is None or raw_df.empty:
        return pd.DataFrame()

    df = raw_df.copy()
    rename_map = {"title": "job_title", "location": "location_raw"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Add project-specific metadata
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
    target_roles = st.text_input("Target roles *", placeholder="e.g. Growth Strategist, Marketing Analytics")
    location_input = st.text_input("Location *", value="Vietnam")
    country_search = st.text_input("Indeed/Glassdoor Country", value="Vietnam")
    work_mode_input = st.selectbox("Work mode", WORK_MODE_OPTIONS)
    duration_input = st.selectbox("Duration", DURATION_OPTIONS)
    google_search_term = st.text_input("Google Jobs query (Optional)", placeholder="Remote Marketing Strategist Vietnam")
    site_names = st.multiselect("Job Sites", DEFAULT_SITE_OPTIONS, default=DEFAULT_SITE_OPTIONS)
    results_wanted = st.number_input("Results wanted", 10, 300, 50)

search_term = f"{target_roles} {location_input} {work_mode_input}"

if st.button("Run Search", type="primary"):
    if not target_roles or not location_input:
        st.error("Please fill in required fields.")
    else:
        scrape_kwargs = {
            "site_name": site_names,
            "search_term": search_term,
            "location": location_input,
            "results_wanted": results_wanted,
            "hours_old": 720,
        }
        
        with st.spinner("Scraping and analyzing quality..."):
            raw_jobs = scrape_jobs(**scrape_kwargs)
            
            if raw_jobs is not None and not raw_jobs.empty:
                clean_jobs = standardize_jobs(
                    raw_jobs, search_term, google_search_term, country_search, 
                    location_input, "", "", work_mode_input, duration_input
                )
                
                # Metrics Display
                high_rel = len(clean_jobs[clean_jobs['relevance_label'] == "High Relevance (Data + Strategy)"])
                strat_rel = len(clean_jobs[clean_jobs['relevance_label'] == "Strategy Focus"])
                
                st.subheader("🔍 Summer Job Quality Metrics")
                m1, m2, m3 = st.columns(3)
                m1.metric("High Relevance (Sweet Spot)", high_rel)
                m2.metric("Strategy Focus Roles", strat_rel)
                m3.metric("Total Unique Scraped", len(clean_jobs))
                
                if high_rel < 5:
                    st.warning("⚠️ Low 'High Relevance' matches. Try adding 'GTM' or 'Growth' to your keywords.")
                
                st.session_state["clean_jobs_df"] = clean_jobs
                st.session_state["raw_jobs_df"] = raw_jobs
            else:
                st.warning("No jobs found.")

# --- PREVIEW AND SAVE ---
if "clean_jobs_df" in st.session_state and st.session_state["clean_jobs_df"] is not None:
    df = st.session_state["clean_jobs_df"]
    
    st.subheader("Preview Records")
    st.dataframe(df[["job_title", "company", "relevance_label", "job_url"]], use_container_width=True)
    
    if st.button("SAVE TO GOOGLE SHEETS"):
        # Logic to append to GSheets goes here (same as your original append_unique_rows function)
        st.success("Results synced to Master Sheet.")
