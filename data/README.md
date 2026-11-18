# Data card

This project uses four datasets from three sources: UNHCR refugee data (Dataset 1), World Bank population and GDP per capita data (Datasets 2 and 3), and IDMC internal displacement data (Dataset 4). The analysis covers 2008–2016 and produces six cleaned and merged CSV files. The final section explains how the datasets are combined. Raw data is downloaded into "/content/IE421/data/raw/" using "scripts/download_data.py" and is not included in the repository.

## Dataset 1: UNHCR Cleaned Refugee Data (unhcr_clean.csv)
- **Source and URL:** UNHCR Refugee Data | [UNHCR Refugee Data](https://www.kaggle.com/datasets/unitednations/refugee-data)  
- **License:** [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)
- **Date accessed:** 18 November 2026
- **Time range and granularity:** 2008–2016; annual, country-level data.
- **Size:** 49,798 rows × 7 columns.
- **Columns used:** year, host_country, origin_country, population_type, refugee_count, host_iso3, origin_iso3
- **Known issues:** Missing refugee counts and unmatched country or territory names in ISO3 mapping. Some records contain duplicate country-year combinations, requiring reconciliation. Missing values may affect country comparisons and annual totals.
- **Cleaning decisions and why:** Filtered the data to 2008–2016 and the refugee population category. Removed exact duplicate records, converted refugee counts to numeric values, and added ISO3 country codes to support merging with other datasets. Missing refugee counts were preserved as missing rather than replaced with zero. 
- **How to regenerate:** Run scripts/download_data.py to download the raw datasets into data/raw/, then run scripts/preprocess_data.py to generate the cleaned datasets in data/processed/.

## Dataset 2: World Bank Population (worldbank_population_clean.csv)
- **Source and URL:** World Bank Population | [Total Population](https://data.worldbank.org/indicator/SP.POP.TOTL) 
- **License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Date accessed:** 18 November 2026
- **Time range and granularity:** 2008–2016; annual,country/level data.
- **Size:** 1,953 rows × 4 columns.
- **Columns used:** country_code, country_name, year, total_population.
- **Known issues:** Some population values may be missing. The original dataset includes regional and income-group aggregates alongside individual countries/economies. Country names may differ between World Bank and UNHCR datasets.
- **Cleaning decisions and why:** Selected the total population indicator (SP.POP.TOTL) and restricted the data to 2008–2016. Removed exact duplicate records, and converted population values to nullable integers while preserving missing values. Removed regional and income-group totals to keep only individual countries and economies. Retained country codes to support merging with UNHCR data.
- **How to regenerate:** Run scripts/download_data.py to download the raw datasets into data/raw/, then run scripts/preprocess_data.py to generate data/processed/worldbank_population_clean.csv.

## Dataset 3: World Bank GDP per Capita PPP (worldbank_gdp_clean.csv)
- **Source and URL:** World Bank GDP per Capita | [GDP per capita, PPP](https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD) 
- **License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Date accessed:** 18 November 2026
- **Time range and granularity:** 2008–2016; annual, country-level data.
- **Size:** 1,953 rows × 4 columns
- **Columns used:** country_code, country_name, year, gdp_per_capita_ppp.
- **Known issues:** GDP per capita PPP values may be missing for some countries and years, limiting comparisons. The indicator is expressed in constant 2021 international dollars rather than current US dollars. Country names may also differ from those in the UNHCR dataset.
- **Cleaning decisions and why:** Selected the GDP per capita PPP indicator (NY.GDP.PCAP.PP.KD) and restricted the data to 2008–2016. Removed exact duplicate records, reshaped the data from wide to long format, and converted GDP values to numeric format. Removed regional and income-group totals using World Bank country metadata to keep individual countries and economies. Retained country codes to support merging with UNHCR data.
- **How to regenerate:** Run scripts/download_data.py to download the raw World Bank data into data/raw/, then run scripts/preprocess_data.py to generate data/processed/worldbank_gdp_clean.csv.

## Dataset 4: IDMC Cleaned Internal Displacement Data (idmc_clean.csv)
- **Source and URL:** IDMC Global Internal Displacement Database |[IDMC Displacement Data](https://www.internal-displacement.org/database/displacement-data/) 
- **License:** [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO (CC BY-NC-SA 3.0 IGO)](https://creativecommons.org/licenses/by-nc-sa/3.0/igo/)
- **Date accessed:** 18 November 2026
- **Time range and granularity:** 2008–2016; annual, country-level data.
- **Size:** 1,125 rows × 5 columns
- **Columns used:** country_code, country_name, year, conflict_stock_people, disaster_stock_people.
- **Known issues:** Some conflict and disaster related displacement stock values may be missing. These figures represent people living in internal displacement, not refugees who have crossed international borders. Data availability may vary across countries and years, limiting direct comparisons with UNHCR refugee figures.
- **Cleaning decisions and why:** Selected the country identifiers, reporting year, and conflict- and disaster-related displacement stock columns from the IDMC Excel dataset. Removed exact duplicate rows and restricted the data to 2008–2016. Converted displacement counts to nullable integers while preserving missing values. Checked for missing country identifiers, invalid years, and duplicate country-year records. Retained ISO3 country codes to support merging with UNHCR origin-country data.
- **How to regenerate:** Run scripts/download_data.py to download the raw IDMC Excel file into data/raw/, then run scripts/preprocess_data.py to generate data/processed/idmc_clean.csv.

 ## Dataset 5: UNHCR and World Bank Integrated Dataset (unhcr_world_bank_origin_host_year.csv)
- **Source and URL:** UNHCR Refugee Data | [UNHCR Refugee Data](https://www.kaggle.com/datasets/unitednations/refugee-data), 
 World Bank Population | [Total Population](https://data.worldbank.org/indicator/SP.POP.TOTL), 
 World Bank GDP per Capita | [GDP per capita, PPP](https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD) 
- **License:** [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/), [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Date accessed:** 18 November 2026
- **Time range and granularity:** 2008–2016; annual, origin-country, host-country, year-level data.
- **Size:** 49,798 rows × 12 columns
- **Columns used:** origin_country, origin_iso3, host_country, host_iso3, year, reported_refugee_count, missing_refugee_count_rows, country_code, total_population, gdp_per_capita_ppp, country_name, reported_refugees_per_1000_residents.
- **Known issues:** Some country names may not match across UNHCR and World Bank datasets, resulting in missing country codes or unmatched records. Population and GDP values may also be missing for some countries and years. Refugee counts may be incomplete, affecting comparisons and calculated refugee rates.
- **Cleaning decisions and why:** Grouped UNHCR refugee records by origin country, host country, and year while preserving missing count information. Used ISO3 country codes to merge World Bank population and GDP per capita PPP data with the corresponding host country and year. Applied left joins to retain UNHCR records even when World Bank indicators were unavailable. Calculated reported refugees per 1,000 host-country residents to support comparisons across countries with different population sizes.
- **How to regenerate:** Run scripts/download_data.py to download the raw datasets into data/raw/, then run scripts/preprocess_data.py to clean and merge the datasets and generate data/processed/unhcr_world_bank_origin_host_year.csv.

 ## Dataset 6: UNHCR and IDMC Integrated Dataset (unhcr_idmc_origin_year.csv)
 - **Source and URL:** UNHCR Refugee Data | [UNHCR Refugee Data](https://www.kaggle.com/datasets/unitednations/refugee-data), IDMC Global Internal Displacement Database | [IDMC Displacement Data](https://www.internal-displacement.org/database/displacement-data/) 
- **License:** [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/), [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO (CC BY-NC-SA 3.0 IGO)](https://creativecommons.org/licenses/by-nc-sa/3.0/igo/)
- **Date accessed:** 18 November 2026
- **Time range and granularity:** 2008–2016; annual, country-level data.
- **Size:** 1,720 rows × 6 columns
- **Columns used:** origin_iso3, year, refugees_from_origin, country_code, conflict_stock_people, disaster_stock_people.
- **Known issues:** Some country-year records may not match between UNHCR and IDMC because of missing or unmatched country codes. Internal displacement figures may be unavailable for certain countries and years. UNHCR refugee counts represent people who have crossed international borders, while IDMC displacement stocks represent people displaced within their own countries, so these measures should not be treated as equivalent.
- **Cleaning decisions and why:** Aggregated UNHCR refugee counts by origin-country ISO3 code and year, preserving missing totals when no counts were reported. Merged these totals with IDMC conflict and disaster related internal displacement stocks using country codes and years. Used a left join to retain UNHCR origin-year records even when matching IDMC data was unavailable. 
- **How to regenerate:** Run scripts/download_data.py to download the raw datasets into data/raw/, then run scripts/preprocess_data.py to clean and merge the datasets and generate data/processed/unhcr_idmc_origin_year.csv.
