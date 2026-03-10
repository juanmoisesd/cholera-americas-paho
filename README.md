# ☣️ Cholera in the Americas – PAHO Data Portal

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://cholera-americas-paho.streamlit.app)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Data: PAHO](https://img.shields.io/badge/Data-PAHO%20Core%20Indicators-blue)
![Updated: Oct 2025](https://img.shields.io/badge/Updated-Oct%202025-green)

> **An open, interactive portal for cholera surveillance data in the Americas.**  
> Data fetched live from PAHO — no local database required.

---

## 🌐 Live App

👉 **[https://cholera-americas-paho.streamlit.app](https://cholera-americas-paho.streamlit.app)**

---

## 📋 What is this?

This portal provides:

- **🏠 Overview** — Regional cholera trend (1995–present) and country heatmap
- **🌎 Country Profiles** — Individual country pages with charts, statistics, and downloadable mini-papers
- **📊 Country Comparison** — Multi-country line charts, bar charts, and geographic bubble maps
- **📄 Mini-Papers Gallery** — Auto-generated data briefs for every country with data
- **ℹ️ About & Citation** — How to cite this portal in academic or policy work

---

## 📦 Data Source

All data come directly from the **PAHO Core Indicators Portal**:

> Pan American Health Organization / World Health Organization.  
> *Core Indicators Portal. Region of the Americas.*  
> https://opendata.paho.org/en/core-indicators  
> Updated: October 1, 2025

The app fetches the dataset at runtime — no manual download needed.

---

## 🚀 Deploy Your Own Instance

### Option 1 – Streamlit Community Cloud (free, recommended)

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo, branch `main`, file `app.py`
5. Click **Deploy** — done!

### Option 2 – Run locally

```bash
git clone https://github.com/juanmoisesd/cholera-americas-paho.git
cd cholera-americas-paho
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Repository Structure

```
cholera-americas-paho/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── LICENSE             # MIT License
└── README.md           # This file
```

---

## 📄 How to Cite

If you use this portal or the mini-papers it generates, please cite:

```
Moises JD. Cholera in the Americas: Interactive Data Portal.
GitHub: https://github.com/juanmoisesd/cholera-americas-paho
Data source: Pan American Health Organization. Core Indicators Portal.
https://opendata.paho.org/en/core-indicators. Accessed 2025.
```

---

## 🔬 Keywords

`cholera` · `Americas` · `Latin America` · `PAHO` · `PAHO data` · `cholera surveillance`  
`epidemiology` · `public health` · `water sanitation` · `WASH` · `open data`  
`Vibrio cholerae` · `cholera cases` · `country comparison` · `health indicators`

---

## 🤝 Contributing

Pull requests welcome. If you add a new feature or indicator, please open an issue first.

---

## 📜 License

MIT © juanmoisesd — see [LICENSE](LICENSE) for details.  
Data: © PAHO/WHO Core Indicators Portal (open access).
