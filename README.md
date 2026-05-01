# Summer_job_search_app.py
Private App for personal use.
# Private Summer Job Search Tool

A personal Streamlit app for searching and organizing job opportunities for summer work, with a focus on:

- full-remote / global-first roles
- location-based searches (for example: Vietnam, Ho Chi Minh City, Hanoi)
- manual skill and company filters
- saving results into Google Sheets for tracking and review

This tool is adapted from my BAN 612 project workflow and customized for my private job search use.

---

## Features

- Search across multiple job platforms supported by `python-jobspy`
- Manual input for:
  - target roles
  - skills
  - companies
  - locations
- Filters for:
  - work mode: Remote / Hybrid / On-site / Any
  - duration: Project / Short-term / Part-time / Full-time / Internship / Any
- Automatic data cleaning and standardization
- Salary extraction and normalization (when available)
- Save clean job results to Google Sheets
- Keep a raw archive of scraped results
- Prevent duplicate job entries using a stable job ID

---

## Current Supported Job Platforms

This version is configured to search from:

- LinkedIn
- Indeed
- Glassdoor
- Google Jobs
- ZipRecruiter

> Coverage depends on the `python-jobspy` package and site availability.

---

## Project Structure

```text
.
├── app.py
├── README.md
├── requirements.txt
└── .streamlit/
    └── secrets.toml
