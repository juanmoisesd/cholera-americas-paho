import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import zipfile
import io
from datetime import datetime

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cholera in the Americas | PAHO Data Portal",
    page_icon="\u2623\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-title{font-size:2.4rem;font-weight:800;color:#1a3a5c;margin-bottom:0;}
.subtitle{font-size:1.1rem;color:#555;margin-bottom:1.5rem;}
.paper-box{background:#f0f7ff;border-left:5px solid #1a7abf;padding:1.2rem 1.5rem;
           border-radius:6px;margin-bottom:1.5rem;}
.citation{background:#fff8e1;border:1px solid #f0c040;padding:.8rem 1.2rem;
          border-radius:5px;font-size:.85rem;font-family:monospace;}
.stTabs [data-baseweb="tab"]{font-size:1rem;font-weight:600;}
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ─────────────────────────────────────────────────────────────
PAHO_ZIP_URL = (
    "https://opendata.paho.org/sites/default/files/data/"
    "2025-10/PAHO-Core-Indicators-2025-20251001.zip"
)

@st.cache_data(show_spinner="\u23f3 Loading PAHO Core Indicators...", ttl=86400)
def load_paho_data():
    resp = requests.get(PAHO_ZIP_URL, timeout=180)
    resp.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
    df = pd.read_csv(zf.open(csv_name), low_memory=False)
    return df

@st.cache_data(show_spinner=False)
def get_cholera(df):
    mask = df["indicator_name"].str.contains("Cholera", case=False, na=False)
    ch = df[mask].copy()
    ch["time_dim"] = pd.to_numeric(ch["time_dim"], errors="coerce")
    ch["numeric_value"] = pd.to_numeric(ch["numeric_value"], errors="coerce")
    ch = ch[ch["spatial_dim_type"] == "COUNTRY"]
    return ch.dropna(subset=["numeric_value", "time_dim"])

def generate_mini_paper(country, cdf, comparison_countries=None):
    if cdf.empty:
        return f"No cholera data available for {country}."
    peak_row   = cdf.loc[cdf["numeric_value"].idxmax()]
    recent_row = cdf.loc[cdf["time_dim"].idxmax()]
    first_row  = cdf.loc[cdf["time_dim"].idxmin()]
    trend = "declining" if recent_row["numeric_value"] < first_row["numeric_value"] else "rising or stable"
    period = f"{int(first_row['time_dim'])}\u2013{int(recent_row['time_dim'])}"
    comp_txt = ""
    if comparison_countries:
        comp_txt = (f" In comparison with {', '.join(comparison_countries)}, "
                    f"{country} shows a distinct epidemiological pattern that warrants further analysis.")

    paper = f"""## Cholera in {country}: A Data Brief ({period})

**Source:** PAHO Core Indicators Portal | **Generated:** {datetime.now().strftime('%B %d, %Y')}

---

### Abstract

This brief examines the burden of cholera in **{country}** using officially reported case data 
from the Pan American Health Organization (PAHO) Core Indicators Portal. 
The analysis covers {period} and provides summary statistics, trend assessment, 
and contextual interpretation for public health and policy audiences.

---

### Key Findings

| Indicator | Value |
|-----------|-------|
| First year with data | {int(first_row['time_dim'])} |
| Most recent year | {int(recent_row['time_dim'])} |
| **Peak cases** | **{int(peak_row['numeric_value']):,} cases in {int(peak_row['time_dim'])}** |
| Most recent cases | {int(recent_row['numeric_value']):,} cases ({int(recent_row['time_dim'])}) |
| Overall trend | {trend.capitalize()} |

---

### Epidemiological Context

Cholera (*Vibrio cholerae* O1/O139) remains a significant public health challenge in the Americas, 
disproportionately affecting populations with limited access to safe water and adequate sanitation. 
In {country}, the data reveal a {trend} trajectory between {period}.{comp_txt}

The peak of **{int(peak_row['numeric_value']):,} cases in {int(peak_row['time_dim'])}** likely reflects 
a period of acute outbreak or systemic vulnerability. Tracking these data points is essential for 
informing WASH infrastructure investments, emergency preparedness, and progress toward the 
PAHO 2030 Elimination Agenda.

---

### Discussion

Surveillance data represent reported cases only and are subject to under-reporting, 
changes in case definitions, and variations in health system capacity. 
Readers are encouraged to interpret these figures within the broader socioeconomic 
and environmental context of {country}.

---

### Data Source

Pan American Health Organization / World Health Organization.  
*Core Indicators Portal. Region of the Americas.*  
Available: https://opendata.paho.org/en/core-indicators  
Accessed: {datetime.now().strftime('%B %d, %Y')}

---

### Suggested Citation

> Cholera in the Americas PAHO Data Portal. *{country} Cholera Surveillance Brief.*  
> GitHub: https://github.com/juanmoisesd/cholera-americas-paho  
> Data: PAHO Core Indicators Portal. {datetime.now().year}.
"""
    return paper

# ── LOAD DATA ────────────────────────────────────────────────────────────────
try:
    raw_df  = load_paho_data()
    chol_df = get_cholera(raw_df)
    data_ok = True
except Exception as e:
    data_ok = False
    err_msg = str(e)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## \u2623\ufe0f Cholera in the Americas")
    st.markdown("**PAHO Core Indicators · 1995\u20132024**")
    st.divider()
    if data_ok:
        countries_list = sorted(chol_df["spatial_dim_en"].dropna().unique().tolist())
        page = st.radio(
            "Navigate to",
            ["\U0001f3e0 Overview",
             "\U0001f30e Country Profile",
             "\U0001f4ca Country Comparison",
             "\U0001f4c4 Mini-Papers Gallery",
             "\u2139\ufe0f About & Citation"],
        )
    else:
        page = "\U0001f3e0 Overview"
    st.divider()
    st.caption("Data source: opendata.paho.org")

if not data_ok:
    st.error(f"Data could not be loaded: {err_msg}")
    st.info("Please reload the app.")
    st.stop()

# ════════════════════════════════════════════════════════════════════
# PAGE 1 – OVERVIEW
# ════════════════════════════════════════════════════════════════════
if page == "\U0001f3e0 Overview":
    st.markdown('<p class="main-title">\u2623\ufe0f Cholera in the Americas</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Interactive portal based on PAHO Core Indicators · 1995\u20132024</p>', unsafe_allow_html=True)

    n_countries = chol_df["spatial_dim_en"].nunique()
    n_years = int(chol_df["time_dim"].max() - chol_df["time_dim"].min() + 1)
    total_cases = int(chol_df["numeric_value"].sum())
    n_records = len(chol_df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries with data", n_countries)
    c2.metric("Years covered", n_years)
    c3.metric("Data records", n_records)
    c4.metric("Cumulative cases", f"{total_cases:,}")

    st.divider()

    regional = (chol_df.groupby("time_dim")["numeric_value"]
                .sum().reset_index()
                .rename(columns={"time_dim": "Year", "numeric_value": "Cases"}))
    fig_reg = px.area(regional, x="Year", y="Cases",
                      title="Cholera Cases in the Americas – Regional Total",
                      color_discrete_sequence=["#1a7abf"])
    fig_reg.update_layout(hovermode="x unified")
    st.plotly_chart(fig_reg, use_container_width=True)

    # Heatmap
    pivot = chol_df.pivot_table(
        index="spatial_dim_en", columns="time_dim",
        values="numeric_value", aggfunc="sum"
    )
    fig_heat = px.imshow(
        pivot, aspect="auto", color_continuous_scale="Blues",
        title="Heatmap: Cholera Cases by Country and Year",
        labels={"x": "Year", "y": "Country", "color": "Cases"}
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("""
    <div class="paper-box">
    <b>About this portal</b><br>
    All data are fetched in real time from the <b>PAHO Core Indicators Portal</b>
    \u2014 no local database required. Use the sidebar to explore country profiles,
    compare countries, and download auto-generated mini-papers for academic or policy use.
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# PAGE 2 – COUNTRY PROFILE
# ════════════════════════════════════════════════════════════════════
elif page == "\U0001f30e Country Profile":
    st.markdown('<p class="main-title">\U0001f30e Country Profile</p>', unsafe_allow_html=True)
    country = st.selectbox("Select country", countries_list)
    cdf = chol_df[chol_df["spatial_dim_en"] == country].sort_values("time_dim")

    if cdf.empty:
        st.info(f"No cholera data for {country}.")
    else:
        peak_yr = int(cdf.loc[cdf["numeric_value"].idxmax(), "time_dim"])
        peak_v  = int(cdf["numeric_value"].max())
        rec_yr  = int(cdf["time_dim"].max())
        rec_v   = int(cdf.loc[cdf["time_dim"].idxmax(), "numeric_value"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Peak cases", f"{peak_v:,}", f"Year {peak_yr}")
        c2.metric("Most recent year", rec_yr)
        c3.metric("Most recent cases", f"{rec_v:,}")

        fig = px.bar(cdf, x="time_dim", y="numeric_value",
                     title=f"Cholera Cases in {country}",
                     labels={"time_dim": "Year", "numeric_value": "Cases"},
                     color="numeric_value", color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("\U0001f4c4 Auto-Generated Mini-Paper")
        paper = generate_mini_paper(country, cdf)
        st.markdown(paper)
        st.download_button(
            "\u2b07\ufe0f Download Mini-Paper (.md)",
            data=paper,
            file_name=f"cholera_{country.lower().replace(' ', '_')}_brief.md",
            mime="text/markdown"
        )
        st.subheader("\U0001f4cb Raw Data")
        st.dataframe(
            cdf[["time_dim", "numeric_value", "data_source_specific"]]
            .rename(columns={"time_dim": "Year", "numeric_value": "Cases",
                             "data_source_specific": "Source"}),
            use_container_width=True
        )

# ════════════════════════════════════════════════════════════════════
# PAGE 3 – COUNTRY COMPARISON
# ════════════════════════════════════════════════════════════════════
elif page == "\U0001f4ca Country Comparison":
    st.markdown('<p class="main-title">\U0001f4ca Country Comparison</p>', unsafe_allow_html=True)
    selected = st.multiselect(
        "Select 2 or more countries",
        countries_list,
        default=countries_list[:5] if len(countries_list) >= 5 else countries_list
    )
    if len(selected) < 2:
        st.warning("Please select at least 2 countries.")
        st.stop()

    cmp_df = chol_df[chol_df["spatial_dim_en"].isin(selected)].sort_values("time_dim")
    tab1, tab2, tab3 = st.tabs(["\U0001f4c8 Line Chart", "\U0001f4ca Bar Chart", "\U0001f5fa\ufe0f Bubble Map"])

    with tab1:
        fig = px.line(cmp_df, x="time_dim", y="numeric_value", color="spatial_dim_en", markers=True,
                      title="Cholera Cases – Line Comparison",
                      labels={"time_dim": "Year", "numeric_value": "Cases", "spatial_dim_en": "Country"})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = px.bar(cmp_df, x="time_dim", y="numeric_value", color="spatial_dim_en", barmode="group",
                      title="Cholera Cases – Bar Comparison",
                      labels={"time_dim": "Year", "numeric_value": "Cases", "spatial_dim_en": "Country"})
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        latest = (cmp_df.sort_values("time_dim")
                  .groupby(["spatial_dim_en", "spatial_dim"])
                  .last().reset_index())
        fig3 = px.scatter_geo(
            latest, locations="spatial_dim", locationmode="ISO-3",
            size="numeric_value", color="spatial_dim_en",
            hover_name="spatial_dim_en",
            title="Latest Reported Cholera Cases – Bubble Map",
            projection="natural earth",
        )
        fig3.update_geos(scope="south america", showcoastlines=True)
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("\U0001f4c4 Comparative Mini-Paper")
    lead = selected[0]
    lead_data = chol_df[chol_df["spatial_dim_en"] == lead]
    paper_comp = generate_mini_paper(lead, lead_data, comparison_countries=selected[1:])
    st.markdown(paper_comp)
    st.download_button(
        "\u2b07\ufe0f Download Comparative Mini-Paper (.md)",
        data=paper_comp,
        file_name=f"cholera_comparison_{'_vs_'.join(s[:3].lower() for s in selected)}.md",
        mime="text/markdown"
    )

# ════════════════════════════════════════════════════════════════════
# PAGE 4 – MINI-PAPERS GALLERY
# ════════════════════════════════════════════════════════════════════
elif page == "\U0001f4c4 Mini-Papers Gallery":
    st.markdown('<p class="main-title">\U0001f4c4 Mini-Papers Gallery</p>', unsafe_allow_html=True)
    st.markdown("One auto-generated data brief per country with cholera data in the PAHO database.")
    search = st.text_input("\U0001f50d Search country", "")
    filtered = [c for c in countries_list if search.lower() in c.lower()]
    st.caption(f"Showing {len(filtered)} countries")

    for country in filtered:
        cdf = chol_df[chol_df["spatial_dim_en"] == country].sort_values("time_dim")
        if cdf.empty:
            continue
        peak_v = int(cdf["numeric_value"].max())
        peak_y = int(cdf.loc[cdf["numeric_value"].idxmax(), "time_dim"])
        with st.expander(f"\u2623\ufe0f {country}  \u2014  Peak: {peak_v:,} cases ({peak_y})"):
            paper = generate_mini_paper(country, cdf)
            st.markdown(paper)
            st.download_button(
                f"\u2b07\ufe0f Download – {country}",
                data=paper,
                file_name=f"cholera_{country.lower().replace(' ', '_')}_brief.md",
                mime="text/markdown",
                key=f"dl_{country}"
            )

# ════════════════════════════════════════════════════════════════════
# PAGE 5 – ABOUT & CITATION
# ════════════════════════════════════════════════════════════════════
elif page == "\u2139\ufe0f About & Citation":
    st.markdown('<p class="main-title">\u2139\ufe0f About & How to Cite</p>', unsafe_allow_html=True)
    st.markdown("""
This portal makes PAHO cholera surveillance data **accessible, comparable, and citable**.
Data are fetched live from PAHO — no local database is used or maintained.

### Data Source
Pan American Health Organization / World Health Organization.  
*Core Indicators Portal. Region of the Americas.*  
https://opendata.paho.org/en/core-indicators

### How to Cite this Portal
""")
    citation_text = (
        f"Moises JD. Cholera in the Americas: Interactive Data Portal.\n"
        f"GitHub: https://github.com/juanmoisesd/cholera-americas-paho\n"
        f"Data: PAHO Core Indicators Portal. Accessed {datetime.now().strftime('%B %Y')}."
    )
    st.markdown(f'<div class="citation">{citation_text}</div>', unsafe_allow_html=True)
    st.markdown("""
### License
MIT – Free to use, share, and adapt with attribution.

### Update Frequency
Data are pulled live from PAHO each session and cached for 24 hours.

### Built with
- [Streamlit](https://streamlit.io) · [Plotly](https://plotly.com) · [Pandas](https://pandas.pydata.org)
- Data: [PAHO Core Indicators Portal](https://opendata.paho.org/en/core-indicators)
""")
