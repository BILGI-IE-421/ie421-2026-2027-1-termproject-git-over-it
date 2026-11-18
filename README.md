# IE 421 - Data Science for Engineers Term Project 

## The Global Refugee Landscape: Origins, Hosts, and Internal Displacement
Refugee movements around the world and the forced displacement of people do not occur at the same level everywhere.While some countries receive a significant numbers of refugees, others stand out as the regions from which refugees depart most frequently, and this distribution can vary over time. 

While preparing this project, we combined various data sources, including United Nations refugee data, World Bank statistics on GDP per capita based on population and purchasing power parity, and the IDMC’s reports on internal displacement. Using these datas, we analyze the relationships between refugee and displacement statistics and the economic conditions and population sizes of host countries. We also examine the main factors leading to the internal displacement of people within their own countries.

Ultimately, this project aims to a better understanding of global migration dynamics, highlight differences and imbalances among countries, and provide meaningful insights into the challenges faced by different regions.


## Group Members
Ece Özkanlı (123203036) · Sıla Doğan (122203077) · Yağmur Battal (123203104)

[The Global Refugee Landscape: Origins, Hosts, and Internal Displacement](https://8767-m-s-use1b11-2x2n6fajjluzt-b.us-east1.prod.r.colab.dev/index.html#research)

## Files (Explain each of them with a sentence)
- `data/`: Contains the datasets used in our project. Raw data is stored in `data/raw/`, while cleaned datasets are used for analysis.`unhcr_clean.csv`: Contains cleaned refugee data from 2008 to 2016, including host countries, origin countries, refugee counts, and ISO3 codes.
`data/README.md`: Provides detailed information about the datasets, their sources, and how they are prepared.
- `scripts/`: Contains the Python scripts used to download, clean, explore, and visualize the data.
- `download_data.py`: Downloads the raw datasets from UNHCR, the World Bank, and IDMC.
- `preprocess_data.py`: Cleans and prepares the datasets for analysis, including standardizing country codes.
- `eda_notebook.ipynb`: Explores the UNHCR dataset, checks missing values, compares refugee-hosting and refugee-origin countries, and creates a heatmap and grouped bar chart.
- `visual/`: Figure 1: Shows the annual changes in refugee populations originating from the top five refugee-origin countries between 2008 and 2016. Figure 2: Shows the changes in refugee populations across the top five refugee-hosting countries between 2008 and 2016.
- `index.html` and `css/`: Main webpage for GitHub Pages hosting.
- `PROPOSAL.md`, `AI_USAGE.md`: Your proposal and your AI usage statement.
- `requirements.txt`: Python libraries your scripts need.
- `.github/`: The automatic repository check. Leave it as it is.

## How to run
```
pip install -r requirements.txt
python scripts/download_data.py
python scripts/preprocess_data.py
python scripts/figures.py
```

## Key findings
Write your three main findings, one sentence each. Put the numbers in context. No visuals here.

## Hosting
The project is hosted using GitHub Pages (https://bilgi-ie-421.github.io/demo-repository).
Your page should be available as (https://bilgi-ie-421.github.io/ie421-2026-2027-1-termproject-yourteamname)
