import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests, zipfile, io
from datetime import datetime
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# AUTHOR & CONSTANTS
# ═══════════════════════════════════════════════════════════════════
AUTHOR_SHORT  = "De la Serna, J. M."
AUTHOR_FULL   = "De la Serna Tuya, J. M."
AUTHOR_LONG   = "De la Serna Tuya, Juan Moisés"
REPO_URL      = "https://github.com/juanmoisesd/cholera-americas-paho"
APP_URL       = "https://cholera-americas-paho.streamlit.app"
PAHO_URL      = "https://opendata.paho.org/en/core-indicators"
PAHO_ZIP_URL  = ("https://opendata.paho.org/sites/default/files/data/"
                 "2025-10/PAHO-Core-Indicators-2025-20251001.zip")
ACCESS_DATE   = datetime.now().strftime("%B %d, %Y")
ACCESS_YEAR   = datetime.now().year

SUBREGIONS = {
    "Caribbean":         ["Haiti","Dominican Republic","Cuba","Jamaica","Trinidad and Tobago",
                          "Barbados","Bahamas","Grenada","Saint Lucia",
                          "Saint Kitts and Nevis","Saint Vincent and the Grenadines",
                          "Antigua and Barbuda","Dominica","Belize"],
    "Central America":   ["Guatemala","Honduras","El Salvador","Nicaragua",
                          "Costa Rica","Panama","Mexico"],
    "Andean":            ["Colombia","Venezuela (Bolivarian Republic of)","Ecuador",
                          "Peru","Bolivia (the Plurinational State of)"],
    "Southern Cone":     ["Argentina","Chile","Uruguay","Paraguay","Brazil"],
    "North America":     ["United States of America","Canada"],
}

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG & CSS
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Cholera in the Americas | PAHO Data Portal",
    page_icon="\u2623\ufe0f", layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-title  {font-size:2.2rem;font-weight:800;color:#1a3a5c;margin-bottom:0;}
.subtitle    {font-size:1.05rem;color:#555;margin-top:0;}
.author-box  {background:#e8f4fd;border-left:5px solid #1a7abf;padding:.9rem 1.2rem;
              border-radius:6px;margin-bottom:1rem;}
.paper-box   {background:#f0f7ff;border-left:5px solid #1a7abf;padding:1.1rem 1.4rem;
              border-radius:6px;margin-bottom:1.2rem;}
.warn-box    {background:#fff8e1;border-left:5px solid #f0a500;padding:.9rem 1.2rem;
              border-radius:6px;margin-bottom:1rem;}
.citation    {background:#fff8e1;border:1px solid #f0c040;padding:.75rem 1rem;
              border-radius:5px;font-size:.84rem;font-family:monospace;white-space:pre-wrap;}
.footer-bar  {font-size:.78rem;color:#888;margin-top:2rem;border-top:1px solid #eee;
              padding-top:.6rem;}
.stTabs [data-baseweb="tab"]{font-size:.95rem;font-weight:600;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="\u23f3 Fetching PAHO Core Indicators...", ttl=86400)
def load_paho_data():
    r = requests.get(PAHO_ZIP_URL, timeout=180); r.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
    return pd.read_csv(zf.open(csv_name), low_memory=False)

@st.cache_data(show_spinner=False)
def get_cholera(df):
    ch = df[df["indicator_name"].str.contains("Cholera", case=False, na=False)].copy()
    ch["time_dim"]      = pd.to_numeric(ch["time_dim"],      errors="coerce")
    ch["numeric_value"] = pd.to_numeric(ch["numeric_value"], errors="coerce")
    ch = ch[ch["spatial_dim_type"] == "COUNTRY"]
    return ch.dropna(subset=["numeric_value","time_dim"]).sort_values(["spatial_dim_en","time_dim"])

# ═══════════════════════════════════════════════════════════════════
# HELPER: STATISTICS
# ═══════════════════════════════════════════════════════════════════
def country_stats(cdf):
    if cdf.empty: return {}
    vals = cdf["numeric_value"]
    yrs  = cdf["time_dim"]
    peak_row   = cdf.loc[vals.idxmax()]
    recent_row = cdf.loc[yrs.idxmax()]
    first_row  = cdf.loc[yrs.idxmin()]
    # Simple linear trend
    if len(cdf) >= 3:
        m = np.polyfit(yrs, vals, 1)[0]
        trend_label = "declining" if m < -50 else ("rising" if m > 50 else "stable")
        trend_rate  = f"{abs(m):.1f} cases/year"
    else:
        trend_label, trend_rate = "insufficient data", "n/a"
    pct_change = ((recent_row["numeric_value"] - first_row["numeric_value"])
                  / (first_row["numeric_value"] + 1)) * 100
    return dict(
        peak_cases=int(peak_row["numeric_value"]),
        peak_year=int(peak_row["time_dim"]),
        first_year=int(first_row["time_dim"]),
        last_year=int(recent_row["time_dim"]),
        last_cases=int(recent_row["numeric_value"]),
        mean_cases=round(float(vals.mean()), 1),
        total_cases=int(vals.sum()),
        n_years=int(yrs.nunique()),
        trend=trend_label,
        trend_rate=trend_rate,
        pct_change=round(pct_change, 1),
    )

# ═══════════════════════════════════════════════════════════════════
# HELPER: FOOTER
# ═══════════════════════════════════════════════════════════════════
def footer():
    st.markdown(f"""
<div class="footer-bar">
\u00a9 {ACCESS_YEAR} <b>{AUTHOR_FULL}</b> \u2014 Cholera in the Americas PAHO Data Portal \u2014
<a href="{REPO_URL}" target="_blank">GitHub</a> \u2014
Data: <a href="{PAHO_URL}" target="_blank">PAHO Core Indicators</a> \u2014 MIT License
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# HELPER: CITATION BOX
# ═══════════════════════════════════════════════════════════════════
def citation_box(context=""):
    ctx = f" [{context}]" if context else ""
    text = (f"{AUTHOR_SHORT} ({ACCESS_YEAR}). Cholera in the Americas: "
            f"Interactive PAHO Data Portal{ctx}.\n"
            f"Available at: {APP_URL}\n"
            f"Repository: {REPO_URL}\n"
            f"Data source: PAHO Core Indicators Portal. {PAHO_URL}\n"
            f"Accessed: {ACCESS_DATE}.")
    st.markdown(f'<div class="citation">{text}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# MINI-PAPER GENERATORS
# ═══════════════════════════════════════════════════════════════════
def paper_country(country, cdf):
    s = country_stats(cdf)
    if not s: return f"No cholera data available for {country}."
    period = f"{s['first_year']}\u2013{s['last_year']}"
    pct_txt = (f"a {abs(s['pct_change'])}% {'decrease' if s['pct_change']<0 else 'increase'} "
               f"from {s['first_year']} to {s['last_year']}")
    subregion = next((k for k,v in SUBREGIONS.items() if country in v), "the Americas")
    return f"""## Cholera in {country}: Epidemiological Data Brief ({period})

**Author:** {AUTHOR_FULL}  
**Portal:** {APP_URL}  
**Generated:** {ACCESS_DATE}  
**Data source:** PAHO Core Indicators Portal ({PAHO_URL})

---

### Abstract

This data brief presents a systematic review of officially reported cholera cases in **{country}**
({subregion}) based on data from the Pan American Health Organization (PAHO) Core Indicators Portal.
The analysis covers the period {period} ({s['n_years']} data points) and includes
summary statistics, temporal trend analysis, and contextual public health interpretation.

---

### 1. Introduction

Cholera (*Vibrio cholerae* O1 and O139) is an acute diarrheal disease transmitted primarily
through contaminated water and food. In the Americas, cholera re-emerged in 1991 after decades
of absence and has since remained a persistent public health challenge, particularly in countries
with limited access to safe water, sanitation, and hygiene (WASH) services.

{country}, located in {subregion}, represents a relevant case study for understanding
regional cholera dynamics. This brief contributes to the open-data literature on disease
surveillance and is part of the *Cholera in the Americas* series curated by {AUTHOR_FULL}.

---

### 2. Methods

Data were obtained directly from the PAHO Core Indicators Portal, which aggregates officially
reported national surveillance data submitted by Ministries of Health to PAHO/WHO. The indicator
used is *"Cholera cases"* (reported cases, annual). No data imputation was performed;
years with missing values were excluded. Statistical trend was estimated via ordinary least squares
linear regression on the annual case series.

---

### 3. Results

#### 3.1 Summary Statistics

| Indicator | Value |
|-----------|-------|
| **Analysis period** | {period} |
| **Data points available** | {s['n_years']} years |
| **Peak cases** | **{s['peak_cases']:,}** ({s['peak_year']}) |
| **Most recent report** | {s['last_cases']:,} cases ({s['last_year']}) |
| **Mean annual cases** | {s['mean_cases']:,} |
| **Cumulative cases (period)** | {s['total_cases']:,} |
| **Overall trend** | {s['trend'].capitalize()} ({s['trend_rate']}) |
| **Change {s['first_year']}\u2192{s['last_year']}** | {pct_txt} |

#### 3.2 Temporal Trend

The cholera case series in {country} shows a **{s['trend']}** trajectory over {period}.
The peak burden of **{s['peak_cases']:,} cases** was recorded in **{s['peak_year']}**.
The most recent data available ({s['last_year']}) reports {s['last_cases']:,} cases,
reflecting {pct_txt}.

---

### 4. Discussion

The pattern observed in {country} is consistent with regional dynamics in {subregion},
where cholera burden is largely shaped by access to clean water, sanitation infrastructure,
population displacement, and health system response capacity. The {'high' if s['peak_cases']>1000 else 'moderate' if s['peak_cases']>100 else 'low'} peak
burden recorded in {s['peak_year']} warrants continued epidemiological vigilance.

Surveillance data represent reported cases only. Under-reporting is a known limitation of
cholera surveillance systems, particularly in low-resource settings, and true incidence is
likely higher than officially recorded figures.

---

### 5. Conclusions

- {country} reported a peak of {s['peak_cases']:,} cholera cases in {s['peak_year']}.
- The overall trend from {s['first_year']} to {s['last_year']} is **{s['trend']}**.
- Continued investment in WASH infrastructure and active surveillance is recommended.
- These data contribute to the PAHO 2030 Cholera Elimination Roadmap monitoring framework.

---

### Data Source & Citation

> {AUTHOR_SHORT} ({ACCESS_YEAR}). *Cholera in {country}: Epidemiological Data Brief.*  
> Cholera in the Americas — PAHO Data Portal.  
> {APP_URL} | {REPO_URL}  
> Data: PAHO Core Indicators Portal. Accessed {ACCESS_DATE}.

---
*This brief was auto-generated by the Cholera in the Americas Portal · {AUTHOR_FULL}*
"""

def paper_comparison(c1, df1, c2, df2):
    s1, s2 = country_stats(df1), country_stats(df2)
    if not s1 or not s2: return "Insufficient data for comparison."
    higher_peak = c1 if s1['peak_cases'] >= s2['peak_cases'] else c2
    lower_peak  = c2 if higher_peak == c1 else c1
    sp1 = next((k for k,v in SUBREGIONS.items() if c1 in v), "the Americas")
    sp2 = next((k for k,v in SUBREGIONS.items() if c2 in v), "the Americas")
    common_start = max(s1['first_year'], s2['first_year'])
    common_end   = min(s1['last_year'],  s2['last_year'])
    return f"""## Comparative Cholera Analysis: {c1} vs. {c2}

**Author:** {AUTHOR_FULL}  
**Portal:** {APP_URL}  
**Generated:** {ACCESS_DATE}  
**Data source:** PAHO Core Indicators Portal ({PAHO_URL})

---

### Abstract

This comparative data brief examines cholera surveillance data for **{c1}** and **{c2}**
using PAHO Core Indicators. Both countries are analyzed across their available data series,
with a shared comparison window of {common_start}\u2013{common_end} where applicable.
The brief identifies divergent and convergent epidemiological patterns and discusses their
potential public health implications.

---

### 1. Introduction

Comparative country analyses are essential for identifying drivers of differential disease
burden, evaluating the effectiveness of public health interventions, and guiding resource
allocation. This brief compares cholera dynamics in {c1} ({sp1}) and {c2} ({sp2}) —
two countries that, despite geographic proximity or comparable socioeconomic contexts,
may exhibit distinct cholera trajectories.

This document is part of the *Cholera in the Americas* comparative series,
curated by {AUTHOR_FULL}.

---

### 2. Comparative Summary Statistics

| Indicator | {c1} | {c2} |
|-----------|{'-'*len(c1)}|{'-'*len(c2)}|
| **Analysis period** | {s1['first_year']}\u2013{s1['last_year']} | {s2['first_year']}\u2013{s2['last_year']} |
| **Data points** | {s1['n_years']} yrs | {s2['n_years']} yrs |
| **Peak cases** | **{s1['peak_cases']:,}** ({s1['peak_year']}) | **{s2['peak_cases']:,}** ({s2['peak_year']}) |
| **Most recent cases** | {s1['last_cases']:,} ({s1['last_year']}) | {s2['last_cases']:,} ({s2['last_year']}) |
| **Mean annual cases** | {s1['mean_cases']:,} | {s2['mean_cases']:,} |
| **Cumulative cases** | {s1['total_cases']:,} | {s2['total_cases']:,} |
| **Trend** | {s1['trend'].capitalize()} | {s2['trend'].capitalize()} |
| **Change (first\u2192last)** | {s1['pct_change']:+.1f}% | {s2['pct_change']:+.1f}% |

---

### 3. Key Findings

**3.1 Peak Burden**  
{higher_peak} recorded a substantially higher peak burden ({max(s1['peak_cases'],s2['peak_cases']):,} cases),
compared to {lower_peak} ({min(s1['peak_cases'],s2['peak_cases']):,} cases). This difference may reflect
{'outbreak-specific factors, population vulnerability, or differences in reporting capacity.' if abs(s1['peak_cases']-s2['peak_cases'])>500 else 'broadly similar epidemic dynamics in both countries.'}

**3.2 Temporal Trends**  
{c1} shows a **{s1['trend']}** trend ({s1['pct_change']:+.1f}% change),
while {c2} shows a **{s2['trend']}** trend ({s2['pct_change']:+.1f}% change).
{'Both countries show convergent trends, suggesting shared regional determinants.' if s1['trend']==s2['trend'] else 'The divergence in trends suggests country-specific factors, such as differences in WASH coverage, surveillance capacity, or public health response.'}

**3.3 Recent Situation**  
As of the most recent available data, {c1} reports {s1['last_cases']:,} cases ({s1['last_year']})
and {c2} reports {s2['last_cases']:,} cases ({s2['last_year']}).

---

### 4. Discussion

The comparison between {c1} and {c2} highlights the heterogeneous nature of cholera
epidemiology across the Americas. While both countries are subject to the same PAHO reporting
framework, differences in health system capacity, environmental conditions, and socioeconomic
determinants produce distinct surveillance profiles.

Limitations include potential under-reporting, changes in case definitions over time,
and variation in surveillance infrastructure between countries.

---

### 5. Conclusion

This comparative analysis of {c1} and {c2} contributes to the evidence base for
targeted cholera control in the Americas. Policy makers should consider the specific
epidemiological profile of each country when designing WASH interventions and
emergency preparedness plans.

---

### Citation

> {AUTHOR_SHORT} ({ACCESS_YEAR}). *Comparative Cholera Analysis: {c1} vs. {c2}.*  
> Cholera in the Americas — PAHO Data Portal.  
> {APP_URL} | {REPO_URL}  
> Data: PAHO Core Indicators Portal. Accessed {ACCESS_DATE}.

---
*Auto-generated by the Cholera in the Americas Portal · {AUTHOR_FULL}*
"""

def paper_subregion(subregion_name, countries, chol_df):
    sdf = chol_df[chol_df["spatial_dim_en"].isin(countries)]
    if sdf.empty: return "No data available for this subregion."
    regional = sdf.groupby("time_dim")["numeric_value"].sum().reset_index()
    peak_row   = regional.loc[regional["numeric_value"].idxmax()]
    best_ctry  = sdf.groupby("spatial_dim_en")["numeric_value"].sum().idxmax()
    n_countries = sdf["spatial_dim_en"].nunique()
    total = int(sdf["numeric_value"].sum())
    period = f"{int(regional['time_dim'].min())}\u2013{int(regional['time_dim'].max())}"
    return f"""## Cholera in {subregion_name}: Subregional Analysis ({period})

**Author:** {AUTHOR_FULL}  
**Portal:** {APP_URL}  
**Generated:** {ACCESS_DATE}

---

### Abstract

This subregional brief synthesizes cholera surveillance data for **{subregion_name}**
({n_countries} countries with data) from the PAHO Core Indicators Portal.
The analysis covers {period}, documenting aggregate burden, peak periods,
and country-level heterogeneity within the subregion.

---

### Summary Statistics

| Indicator | Value |
|-----------|-------|
| **Subregion** | {subregion_name} |
| **Countries with data** | {n_countries} |
| **Analysis period** | {period} |
| **Peak subregional year** | {int(peak_row['time_dim'])} ({int(peak_row['numeric_value']):,} cases) |
| **Highest burden country** | {best_ctry} |
| **Cumulative subregional cases** | {total:,} |

---

### Country-Level Overview

{"".join([f"- **{c}**: {int(sdf[sdf['spatial_dim_en']==c]['numeric_value'].sum()):,} cumulative cases" + chr(10) for c in sorted(countries) if c in sdf['spatial_dim_en'].values])}

---

### Citation

> {AUTHOR_SHORT} ({ACCESS_YEAR}). *Cholera in {subregion_name}: Subregional Analysis.*  
> Cholera in the Americas — PAHO Data Portal.  
> {APP_URL} | {REPO_URL}  
> Data: PAHO Core Indicators Portal. Accessed {ACCESS_DATE}.

---
*Auto-generated by the Cholera in the Americas Portal · {AUTHOR_FULL}*
"""


# ═══════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════
try:
    raw_df  = load_paho_data()
    chol_df = get_cholera(raw_df)
    countries_list = sorted(chol_df["spatial_dim_en"].dropna().unique().tolist())
    data_ok = True
except Exception as e:
    data_ok = False; err_msg = str(e)

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
<div class="author-box">
\u2623\ufe0f <b>Cholera in the Americas</b><br>
<small>By <b>{AUTHOR_FULL}</b></small><br>
<small>PAHO Core Indicators · 1995\u20132024</small>
</div>""", unsafe_allow_html=True)

    if data_ok:
        page = st.radio("Navigate to", [
            "\U0001f3e0 Overview",
            "\U0001f30e Country Profile",
            "\U0001f4ca Country vs Country",
            "\U0001f5fa\ufe0f Multi-Country Comparison",
            "\U0001f3f3\ufe0f Subregional Analysis",
            "\U0001f3c6 Rankings",
            "\U0001f4c4 Mini-Papers Gallery",
            "\u2139\ufe0f About & Citation",
        ])
    else:
        page = "\U0001f3e0 Overview"

    st.divider()
    st.caption(f"Author: {AUTHOR_SHORT}")
    st.caption("Data: opendata.paho.org")

if not data_ok:
    st.error(f"Data could not be loaded: {err_msg}"); st.stop()

# ═══════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════
if page == "\U0001f3e0 Overview":
    st.markdown('<p class="main-title">\u2623\ufe0f Cholera in the Americas</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">PAHO Core Indicators · 1995\u20132024 · Curated by <b>{AUTHOR_FULL}</b></p>', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Countries with data", chol_df["spatial_dim_en"].nunique())
    c2.metric("Years covered", int(chol_df["time_dim"].max()-chol_df["time_dim"].min()+1))
    c3.metric("Total records", len(chol_df))
    c4.metric("Cumulative cases", f"{int(chol_df['numeric_value'].sum()):,}")

    st.divider()

    # Regional trend
    reg = chol_df.groupby("time_dim")["numeric_value"].sum().reset_index()
    reg.columns = ["Year","Cases"]
    fig1 = px.area(reg, x="Year", y="Cases",
                   title="Cholera Cases in the Americas — Regional Total (all countries)",
                   color_discrete_sequence=["#1a7abf"])
    fig1.update_layout(hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    # Heatmap
    pivot = chol_df.pivot_table(index="spatial_dim_en", columns="time_dim",
                                 values="numeric_value", aggfunc="sum")
    fig2 = px.imshow(pivot, aspect="auto", color_continuous_scale="Blues",
                     title="Heatmap: Cholera Cases by Country and Year",
                     labels={"x":"Year","y":"Country","color":"Cases"})
    st.plotly_chart(fig2, use_container_width=True)

    # Top 5 bar
    top5 = chol_df.groupby("spatial_dim_en")["numeric_value"].sum().nlargest(10).reset_index()
    fig3 = px.bar(top5, x="spatial_dim_en", y="numeric_value",
                  title="Top 10 Countries by Cumulative Cholera Cases",
                  labels={"spatial_dim_en":"Country","numeric_value":"Cumulative Cases"},
                  color="numeric_value", color_continuous_scale="Reds")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown(f"""<div class="paper-box">
<b>About this portal</b><br>
This portal was developed and is maintained by <b>{AUTHOR_FULL}</b>.
All data are fetched in real time from the <b>PAHO Core Indicators Portal</b> — no local
database required. Use the sidebar to explore country profiles, compare countries,
analyse subregions, and download academic mini-papers.
</div>""", unsafe_allow_html=True)

    st.markdown("**Cite this portal:**")
    citation_box()
    footer()


# ═══════════════════════════════════════════════════════════════════
# PAGE 2 — COUNTRY PROFILE
# ═══════════════════════════════════════════════════════════════════
elif page == "\U0001f30e Country Profile":
    st.markdown('<p class="main-title">\U0001f30e Country Profile</p>', unsafe_allow_html=True)
    country = st.selectbox("Select country", countries_list)
    cdf = chol_df[chol_df["spatial_dim_en"]==country].sort_values("time_dim")

    if cdf.empty:
        st.info(f"No cholera data for {country}.")
    else:
        s = country_stats(cdf)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Peak cases", f"{s['peak_cases']:,}", f"Year {s['peak_year']}")
        c2.metric("Most recent year", s['last_year'])
        c3.metric("Most recent cases", f"{s['last_cases']:,}")
        c4.metric("Overall trend", s['trend'].capitalize())

        tab1, tab2, tab3 = st.tabs(["\U0001f4ca Bar Chart","\U0001f4c8 Line + Trend","\U0001f4cb Statistics"])

        with tab1:
            fig = px.bar(cdf, x="time_dim", y="numeric_value",
                         title=f"Cholera Cases in {country} ({s['first_year']}\u2013{s['last_year']})",
                         labels={"time_dim":"Year","numeric_value":"Cases"},
                         color="numeric_value", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=cdf["time_dim"], y=cdf["numeric_value"],
                                      mode="lines+markers", name="Cases",
                                      line=dict(color="#1a7abf", width=2)))
            if len(cdf) >= 3:
                m, b = np.polyfit(cdf["time_dim"], cdf["numeric_value"], 1)
                trend_y = m * cdf["time_dim"] + b
                fig2.add_trace(go.Scatter(x=cdf["time_dim"], y=trend_y,
                                          mode="lines", name="Linear trend",
                                          line=dict(color="red", dash="dash")))
            fig2.update_layout(title=f"Cholera Trend in {country}",
                               xaxis_title="Year", yaxis_title="Cases")
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            st.dataframe(cdf[["time_dim","numeric_value","data_source_specific"]]
                         .rename(columns={"time_dim":"Year","numeric_value":"Cases",
                                          "data_source_specific":"Source"}),
                         use_container_width=True)

        st.divider()
        st.subheader("\U0001f4c4 Auto-Generated Mini-Paper")
        paper = paper_country(country, cdf)
        st.markdown(paper)
        st.download_button(
            f"\u2b07\ufe0f Download Mini-Paper — {country} (.md)",
            data=paper,
            file_name=f"cholera_{country.lower().replace(' ','_')}_brief_{ACCESS_YEAR}.md",
            mime="text/markdown"
        )
        st.markdown("**Cite this country brief:**")
        citation_box(f"{country} Country Profile")
        footer()

# ═══════════════════════════════════════════════════════════════════
# PAGE 3 — COUNTRY vs COUNTRY
# ═══════════════════════════════════════════════════════════════════
elif page == "\U0001f4ca Country vs Country":
    st.markdown('<p class="main-title">\U0001f4ca Country vs Country</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Head-to-head comparison with full comparative mini-paper</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        c1_sel = st.selectbox("Country A", countries_list, index=0)
    with col2:
        default_b = 1 if len(countries_list) > 1 else 0
        c2_sel = st.selectbox("Country B", countries_list, index=default_b)

    if c1_sel == c2_sel:
        st.warning("Please select two different countries.")
        st.stop()

    df1 = chol_df[chol_df["spatial_dim_en"]==c1_sel].sort_values("time_dim")
    df2 = chol_df[chol_df["spatial_dim_en"]==c2_sel].sort_values("time_dim")
    s1, s2 = country_stats(df1), country_stats(df2)

    # KPI comparison
    kc1, kc2, kc3 = st.columns(3)
    kc1.metric(f"{c1_sel} peak", f"{s1.get('peak_cases',0):,}", f"{s1.get('peak_year','')}")
    kc2.metric(f"{c2_sel} peak", f"{s2.get('peak_cases',0):,}", f"{s2.get('peak_year','')}")
    kc3.metric("Ratio A/B", f"{(s1.get('peak_cases',1)/(s2.get('peak_cases',1) or 1)):.2f}x")

    tab1, tab2, tab3, tab4 = st.tabs([
        "\U0001f4c8 Line Chart","\U0001f4ca Bar Chart",
        "\U0001f5fa\ufe0f Map","\U0001f4c4 Comparative Mini-Paper"])

    with tab1:
        cmp = pd.concat([df1, df2])
        fig = px.line(cmp, x="time_dim", y="numeric_value", color="spatial_dim_en",
                      markers=True, title=f"Cholera: {c1_sel} vs {c2_sel}",
                      labels={"time_dim":"Year","numeric_value":"Cases","spatial_dim_en":"Country"})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        cmp = pd.concat([df1, df2])
        fig2 = px.bar(cmp, x="time_dim", y="numeric_value", color="spatial_dim_en",
                      barmode="group", title=f"Cholera Cases: {c1_sel} vs {c2_sel}",
                      labels={"time_dim":"Year","numeric_value":"Cases","spatial_dim_en":"Country"})
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        latest = pd.concat([
            df1.loc[[df1["time_dim"].idxmax()]],
            df2.loc[[df2["time_dim"].idxmax()]]
        ])
        fig3 = px.scatter_geo(latest, locations="spatial_dim", locationmode="ISO-3",
                              size="numeric_value", color="spatial_dim_en",
                              hover_name="spatial_dim_en",
                              title="Most Recent Cholera Cases — Geographic View",
                              projection="natural earth")
        fig3.update_geos(scope="south america", showcoastlines=True,
                         showland=True, landcolor="#f0f0f0")
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        paper = paper_comparison(c1_sel, df1, c2_sel, df2)
        st.markdown(paper)
        fname = f"cholera_{c1_sel[:5].lower()}_{c2_sel[:5].lower()}_comparison_{ACCESS_YEAR}.md"
        st.download_button(
            f"\u2b07\ufe0f Download Comparative Mini-Paper (.md)",
            data=paper, file_name=fname, mime="text/markdown"
        )
        st.markdown("**Cite this comparison:**")
        citation_box(f"{c1_sel} vs {c2_sel}")

    footer()


# ═══════════════════════════════════════════════════════════════════
# PAGE 4 — MULTI-COUNTRY COMPARISON
# ═══════════════════════════════════════════════════════════════════
elif page == "\U0001f5fa\ufe0f Multi-Country Comparison":
    st.markdown('<p class="main-title">\U0001f5fa\ufe0f Multi-Country Comparison</p>', unsafe_allow_html=True)
    selected = st.multiselect("Select countries (2 or more)",
                               countries_list,
                               default=countries_list[:6] if len(countries_list)>=6 else countries_list)
    if len(selected) < 2:
        st.warning("Please select at least 2 countries."); st.stop()

    cmp_df = chol_df[chol_df["spatial_dim_en"].isin(selected)].sort_values("time_dim")

    tab1,tab2,tab3,tab4,tab5 = st.tabs([
        "\U0001f4c8 Lines","\U0001f4ca Bars","\U0001f5fa\ufe0f Bubble Map",
        "\U0001f525 Normalized","\U0001f4c4 Group Mini-Paper"])

    with tab1:
        fig = px.line(cmp_df, x="time_dim", y="numeric_value", color="spatial_dim_en",
                      markers=True, title="Cholera Cases — Multi-Country Line Comparison",
                      labels={"time_dim":"Year","numeric_value":"Cases","spatial_dim_en":"Country"})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = px.bar(cmp_df, x="time_dim", y="numeric_value", color="spatial_dim_en",
                      barmode="group", title="Cholera Cases — Multi-Country Bar Comparison",
                      labels={"time_dim":"Year","numeric_value":"Cases","spatial_dim_en":"Country"})
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        latest = (cmp_df.sort_values("time_dim")
                  .groupby(["spatial_dim_en","spatial_dim"]).last().reset_index())
        fig3 = px.scatter_geo(latest, locations="spatial_dim", locationmode="ISO-3",
                              size="numeric_value", color="spatial_dim_en",
                              hover_name="spatial_dim_en",
                              title="Latest Cholera Cases — Geographic Bubble Map",
                              projection="natural earth")
        fig3.update_geos(scope="south america", showcoastlines=True, showland=True, landcolor="#f0f0f0")
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        # Normalize each country to its own max
        norm_frames = []
        for c in selected:
            cd = cmp_df[cmp_df["spatial_dim_en"]==c].copy()
            mx = cd["numeric_value"].max()
            if mx > 0:
                cd["normalized"] = cd["numeric_value"] / mx * 100
                norm_frames.append(cd)
        if norm_frames:
            norm_df = pd.concat(norm_frames)
            fig4 = px.line(norm_df, x="time_dim", y="normalized", color="spatial_dim_en",
                           markers=True,
                           title="Normalized Cholera Cases (% of each country's peak)",
                           labels={"time_dim":"Year","normalized":"% of Peak","spatial_dim_en":"Country"})
            st.plotly_chart(fig4, use_container_width=True)

    with tab5:
        st.markdown(f"**Multi-country comparative analysis — {', '.join(selected)}**")
        st.markdown(f"*Author: {AUTHOR_FULL} | Portal: {APP_URL}*")
        st.divider()
        # Summary table
        rows = []
        for c in selected:
            cd = chol_df[chol_df["spatial_dim_en"]==c]
            s = country_stats(cd)
            if s:
                rows.append({"Country":c,"Peak Cases":s['peak_cases'],
                             "Peak Year":s['peak_year'],"Last Cases":s['last_cases'],
                             "Last Year":s['last_year'],"Trend":s['trend'].capitalize(),
                             "Cumulative":s['total_cases']})
        if rows:
            tbl = pd.DataFrame(rows).sort_values("Peak Cases", ascending=False)
            st.dataframe(tbl, use_container_width=True)

            paper_group = f"""## Multi-Country Cholera Comparison: {', '.join(selected)}

**Author:** {AUTHOR_FULL}  
**Portal:** {APP_URL}  
**Generated:** {ACCESS_DATE}

---

### Abstract

This multi-country comparative brief analyses cholera surveillance data for
{len(selected)} countries in the Americas: {', '.join(selected)}.
Data are sourced from the PAHO Core Indicators Portal.

---

### Comparative Table

| Country | Peak Cases | Peak Year | Last Cases | Last Year | Trend | Cumulative |
|---------|-----------|-----------|-----------|-----------|-------|------------|
""" + "\n".join([f"| {r['Country']} | {r['Peak Cases']:,} | {r['Peak Year']} | {r['Last Cases']:,} | {r['Last Year']} | {r['Trend']} | {r['Cumulative']:,} |" for r in rows]) + f"""

---

### Citation

> {AUTHOR_SHORT} ({ACCESS_YEAR}). *Multi-Country Cholera Comparison: {', '.join(selected[:3])}{'...' if len(selected)>3 else ''}.*  
> Cholera in the Americas — PAHO Data Portal. {APP_URL}  
> Data: PAHO Core Indicators Portal. Accessed {ACCESS_DATE}.

---
*Auto-generated by the Cholera in the Americas Portal · {AUTHOR_FULL}*
"""
            st.markdown(paper_group)
            st.download_button("\u2b07\ufe0f Download Group Mini-Paper (.md)",
                               data=paper_group,
                               file_name=f"cholera_multicomparison_{ACCESS_YEAR}.md",
                               mime="text/markdown")
            citation_box(f"Multi-country: {', '.join(selected[:3])}")
    footer()

# ═══════════════════════════════════════════════════════════════════
# PAGE 5 — SUBREGIONAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════
elif page == "\U0001f3f3\ufe0f Subregional Analysis":
    st.markdown('<p class="main-title">\U0001f3f3\ufe0f Subregional Analysis</p>', unsafe_allow_html=True)
    subregion = st.selectbox("Select subregion", list(SUBREGIONS.keys()))
    countries_in_sr = SUBREGIONS[subregion]
    sdf = chol_df[chol_df["spatial_dim_en"].isin(countries_in_sr)]

    if sdf.empty:
        st.info(f"No data for {subregion}."); st.stop()

    available = sdf["spatial_dim_en"].unique().tolist()
    st.caption(f"Countries with data: {', '.join(sorted(available))}")

    tab1, tab2, tab3, tab4 = st.tabs([
        "\U0001f4c8 Regional Trend","\U0001f4ca By Country","\U0001f525 Heatmap","\U0001f4c4 Subregional Paper"])

    with tab1:
        reg = sdf.groupby("time_dim")["numeric_value"].sum().reset_index()
        reg.columns = ["Year","Cases"]
        fig = px.area(reg, x="Year", y="Cases",
                      title=f"Cholera Cases — {subregion} (Aggregate)",
                      color_discrete_sequence=["#1a7abf"])
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = px.line(sdf, x="time_dim", y="numeric_value", color="spatial_dim_en",
                       markers=True, title=f"Cholera by Country — {subregion}",
                       labels={"time_dim":"Year","numeric_value":"Cases","spatial_dim_en":"Country"})
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        pvt = sdf.pivot_table(index="spatial_dim_en", columns="time_dim",
                              values="numeric_value", aggfunc="sum")
        fig3 = px.imshow(pvt, aspect="auto", color_continuous_scale="Blues",
                         title=f"Heatmap — {subregion}",
                         labels={"x":"Year","y":"Country","color":"Cases"})
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        paper = paper_subregion(subregion, countries_in_sr, chol_df)
        st.markdown(paper)
        st.download_button(
            f"\u2b07\ufe0f Download Subregional Paper — {subregion} (.md)",
            data=paper,
            file_name=f"cholera_{subregion.lower().replace(' ','_')}_{ACCESS_YEAR}.md",
            mime="text/markdown"
        )
        citation_box(f"{subregion} Subregional Analysis")
    footer()

# ═══════════════════════════════════════════════════════════════════
# PAGE 6 — RANKINGS
# ═══════════════════════════════════════════════════════════════════
elif page == "\U0001f3c6 Rankings":
    st.markdown('<p class="main-title">\U0001f3c6 Country Rankings</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">All countries ranked by different indicators</p>', unsafe_allow_html=True)

    # Build rankings table
    rows = []
    for c in countries_list:
        cd = chol_df[chol_df["spatial_dim_en"]==c]
        s = country_stats(cd)
        if s:
            rows.append({"Country":c, "Peak Cases":s['peak_cases'],
                         "Peak Year":s['peak_year'],
                         "Most Recent Cases":s['last_cases'],
                         "Most Recent Year":s['last_year'],
                         "Mean Annual Cases":s['mean_cases'],
                         "Cumulative Cases":s['total_cases'],
                         "Years with Data":s['n_years'],
                         "Trend":s['trend'].capitalize(),
                         "Change (%)":s['pct_change']})
    rank_df = pd.DataFrame(rows)

    tab1, tab2, tab3, tab4 = st.tabs([
        "\U0001f947 By Cumulative","\U0001f525 By Peak","\U0001f4c9 By Trend","\U0001f4cb Full Table"])

    with tab1:
        top_cum = rank_df.sort_values("Cumulative Cases", ascending=False).head(20)
        fig = px.bar(top_cum, x="Country", y="Cumulative Cases",
                     title="Top 20 Countries — Cumulative Cholera Cases",
                     color="Cumulative Cases", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        top_pk = rank_df.sort_values("Peak Cases", ascending=False).head(20)
        fig2 = px.bar(top_pk, x="Country", y="Peak Cases",
                      title="Top 20 Countries — Peak Cholera Cases",
                      color="Peak Cases", color_continuous_scale="Oranges")
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        fig3 = px.scatter(rank_df, x="Mean Annual Cases", y="Change (%)",
                          color="Trend", hover_name="Country", size="Cumulative Cases",
                          title="Trend vs Mean Annual Cases",
                          labels={"Mean Annual Cases":"Mean Annual Cases","Change (%)":"Change (%)"})
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        st.dataframe(rank_df.sort_values("Cumulative Cases", ascending=False),
                     use_container_width=True)
        csv = rank_df.to_csv(index=False)
        st.download_button("\u2b07\ufe0f Download Rankings CSV",
                           data=csv, file_name=f"cholera_rankings_{ACCESS_YEAR}.csv",
                           mime="text/csv")

    st.markdown(f"*Rankings compiled by {AUTHOR_FULL} from PAHO Core Indicators data.*")
    citation_box("Rankings & Statistics")
    footer()


# ═══════════════════════════════════════════════════════════════════
# PAGE 7 — MINI-PAPERS GALLERY
# ═══════════════════════════════════════════════════════════════════
elif page == "\U0001f4c4 Mini-Papers Gallery":
    st.markdown('<p class="main-title">\U0001f4c4 Mini-Papers Gallery</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">Auto-generated academic data briefs · Author: <b>{AUTHOR_FULL}</b></p>', unsafe_allow_html=True)

    paper_type = st.radio("Paper type", [
        "\U0001f30e Country Briefs",
        "\U0001f4ca Country vs Country Briefs",
        "\U0001f3f3\ufe0f Subregional Briefs"
    ], horizontal=True)

    if paper_type == "\U0001f30e Country Briefs":
        search = st.text_input("\U0001f50d Search country", "")
        filtered = [c for c in countries_list if search.lower() in c.lower()]
        st.caption(f"Showing {len(filtered)} countries · Each brief cites {AUTHOR_SHORT}")

        for country in filtered:
            cdf = chol_df[chol_df["spatial_dim_en"]==country].sort_values("time_dim")
            if cdf.empty: continue
            s = country_stats(cdf)
            with st.expander(
                f"\u2623\ufe0f {country}  |  Peak: {s['peak_cases']:,} ({s['peak_year']})  "
                f"|  Trend: {s['trend']}  |  Last: {s['last_cases']:,} ({s['last_year']})"
            ):
                paper = paper_country(country, cdf)
                st.markdown(paper)
                st.download_button(
                    f"\u2b07\ufe0f Download — {country}",
                    data=paper,
                    file_name=f"cholera_{country.lower().replace(' ','_')}_{ACCESS_YEAR}.md",
                    mime="text/markdown", key=f"dl_{country}"
                )

    elif paper_type == "\U0001f4ca Country vs Country Briefs":
        st.info(f"Select any pair to generate a comparative mini-paper by {AUTHOR_SHORT}.")
        col1, col2 = st.columns(2)
        with col1: ca = st.selectbox("Country A", countries_list, key="gal_a")
        with col2: cb = st.selectbox("Country B", countries_list, index=1, key="gal_b")

        if ca != cb:
            dfa = chol_df[chol_df["spatial_dim_en"]==ca].sort_values("time_dim")
            dfb = chol_df[chol_df["spatial_dim_en"]==cb].sort_values("time_dim")
            paper = paper_comparison(ca, dfa, cb, dfb)
            st.markdown(paper)
            st.download_button(
                f"\u2b07\ufe0f Download — {ca} vs {cb}",
                data=paper,
                file_name=f"cholera_{ca[:6].lower()}_{cb[:6].lower()}_vs_{ACCESS_YEAR}.md",
                mime="text/markdown", key="gal_dl_vs"
            )

    elif paper_type == "\U0001f3f3\ufe0f Subregional Briefs":
        for sr_name, sr_countries in SUBREGIONS.items():
            sdf = chol_df[chol_df["spatial_dim_en"].isin(sr_countries)]
            if sdf.empty: continue
            with st.expander(f"\U0001f3f3\ufe0f {sr_name}  |  {sdf['spatial_dim_en'].nunique()} countries  |  {int(sdf['numeric_value'].sum()):,} cumulative cases"):
                paper = paper_subregion(sr_name, sr_countries, chol_df)
                st.markdown(paper)
                st.download_button(
                    f"\u2b07\ufe0f Download — {sr_name}",
                    data=paper,
                    file_name=f"cholera_{sr_name.lower().replace(' ','_')}_{ACCESS_YEAR}.md",
                    mime="text/markdown", key=f"dl_sr_{sr_name}"
                )
    footer()

# ═══════════════════════════════════════════════════════════════════
# PAGE 8 — ABOUT & CITATION
# ═══════════════════════════════════════════════════════════════════
elif page == "\u2139\ufe0f About & Citation":
    st.markdown('<p class="main-title">\u2139\ufe0f About & How to Cite</p>', unsafe_allow_html=True)

    st.markdown(f"""
<div class="author-box">
<h4>\U0001f393 About the Author</h4>
<b>{AUTHOR_LONG}</b><br>
This portal was developed and is maintained by <b>{AUTHOR_FULL}</b>.<br>
All data are fetched live from PAHO — no local database is maintained.<br>
For academic use, please cite as indicated below.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
### About This Portal

This portal provides open, reusable, and citable data briefs on cholera surveillance
in the Americas. It is designed to support academic research, public health policy,
and epidemiological education.

**Features:**
- Country profiles with trend analysis and downloadable mini-papers
- Head-to-head country comparisons (Country vs Country)
- Multi-country interactive comparisons
- Subregional analysis (Caribbean, Central America, Andean, Southern Cone)
- Country rankings by cumulative and peak burden
- Mini-papers gallery with downloadable academic briefs
""")

    st.divider()
    st.subheader("\U0001f4d1 How to Cite This Portal")
    citation_box()

    st.divider()
    st.subheader("\U0001f4d1 How to Cite a Country Brief")
    citation_box("Country Profile — [Country Name]")

    st.divider()
    st.subheader("\U0001f4d1 How to Cite a Comparative Brief")
    citation_box("Country vs Country — [Country A] vs [Country B]")

    st.divider()
    st.markdown("""
### Data Source

Pan American Health Organization / World Health Organization.  
*Core Indicators Portal. Region of the Americas.*  
https://opendata.paho.org/en/core-indicators  
Updated: October 1, 2025.

### License

MIT — Free to use, share, and adapt **with attribution to the author**.

### Technical Stack

Built with [Streamlit](https://streamlit.io) · [Plotly](https://plotly.com) ·
[Pandas](https://pandas.pydata.org) · [NumPy](https://numpy.org)
""")
    footer()
