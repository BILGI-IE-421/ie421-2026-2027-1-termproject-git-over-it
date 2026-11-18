"""Prepare the four refugee project datasets for 2008–2016 (inclusive)."""

import argparse
import csv
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


def parse_year(values):
    """Read a four-digit annual reporting year as a nullable integer."""
    return values.where(values.str.fullmatch(r"[0-9]{4}")).astype("Int64")


RAW_COLUMNS = {
    "year": "year",
    "country / territory of asylum/residence": "host_country",
    "origin": "origin_country",
    "population type": "population_type",
    "value": "refugee_count",
}
KEY = ["year", "origin_country", "host_country"]
MISSING_COUNTS = {"", "*", "-", "..", "...", "na", "n/a", "null"}
REFUGEE_LABEL = "Refugees (incl. refugee-like situations)"
SERBIA_KOSOVO = "Serbia and Kosovo (S/RES/1244 (1999))"
# UNHCR Global Trends 2014, Annex Table 1, end-of-year host population.
SERBIA_KOSOVO_2014_PUBLISHED_TOTAL = 43_751


def read_unhcr_source(path):
    # The legacy export may have a short description above its CSV header.
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        for row in reader:
            names = [value.strip().casefold() for value in row]
            if RAW_COLUMNS.keys() <= set(names):
                header_line = reader.line_num - 1
                break
            if reader.line_num >= 20:
                raise ValueError("Expected UNHCR column names were not found in the first 20 lines.")
        else:
            raise ValueError("Expected UNHCR column names were not found.")

    frame = pd.read_csv(path, skiprows=header_line, dtype="string", keep_default_na=False)
    frame.columns = frame.columns.str.strip().str.casefold()
    if frame.columns.has_duplicates:
        raise ValueError("The input has duplicate column names after normalization.")
    return frame


def reconcile_keys(data):
    repeated = data.duplicated(KEY, keep=False)
    if not repeated.any():
        return data

    # This archive uses a single host label for the 2014 Serbia/Kosovo rows.
    known_host_year = data["year"].eq(2014) & data["host_country"].eq(SERBIA_KOSOVO)
    host_counts = data.loc[known_host_year, "refugee_count"]
    if (
        (repeated & ~known_host_year).any()
        or host_counts.isna().any()
        or host_counts.sum() != SERBIA_KOSOVO_2014_PUBLISHED_TOTAL
    ):
        examples = data.loc[repeated, KEY + ["refugee_count"]].head(10)
        raise ValueError(
            f"{repeated.sum():,} rows share an origin/host/year key that could "
            f"not be reconciled.\n{examples.to_string(index=False)}"
        )

    matched = data.loc[repeated]
    combined = matched.groupby(KEY + ["population_type"], as_index=False)["refugee_count"].sum(min_count=1)
    print(f"Reconciled Serbia/Kosovo 2014: {len(matched)} rows → {len(combined)} keys.")
    print(f"Host-year sum matches the published UNHCR total: {host_counts.sum():,}.")
    return pd.concat([data.loc[~repeated], combined], ignore_index=True)


def clean_unhcr(source, refugee_label):
    print(f"Raw input: {len(source):,} rows × {len(source.columns)} columns")
    source_labels = source["population type"].str.strip()
    selected = source_labels.str.casefold().eq(refugee_label.casefold())
    if not selected.any():
        labels = ", ".join(sorted(source_labels.unique()))
        raise ValueError(f"Refugee category {refugee_label!r} not found. Available labels: {labels}")

    # Remove exact copies before selecting columns or normalizing values.
    refugees = source.loc[selected].drop_duplicates()
    exact_duplicates = int(selected.sum()) - len(refugees)
    data = refugees.loc[:, list(RAW_COLUMNS)].rename(columns=RAW_COLUMNS)
    data = data.apply(lambda column: column.str.strip())
    data["population_type"] = refugee_label

    year = parse_year(data["year"])
    valid_year = year.notna()
    in_period = year.between(2008, 2016).fillna(False)
    missing_country = data["origin_country"].eq("") | data["host_country"].eq("")
    print(f"Selected category rows: {selected.sum():,}")
    print(f"Exact duplicates removed in selected category: {exact_duplicates:,}")
    print(f"Invalid or missing year: {(~valid_year).sum():,}")
    print(f"Valid year outside 2008–2016: {(valid_year & ~in_period).sum():,}")
    print(f"Missing origin or host in period: {(in_period & missing_country).sum():,}")

    data = data.loc[in_period & ~missing_country].copy()
    if data.empty:
        raise ValueError("No records remain for the selected category and period.")

    data["year"] = year.loc[data.index].astype("int64")
    counts = data["refugee_count"]
    missing_count = counts.str.casefold().isin(MISSING_COUNTS)
    # Accept whole counts, with properly grouped commas if present.
    valid_count = counts.str.fullmatch(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.0+)?")
    invalid_count = ~missing_count & ~valid_count
    data["refugee_count"] = (
        counts.where(valid_count)
        .str.replace(",", "", regex=False)
        .str.replace(r"\.0+$", "", regex=True)
        .astype("Int64")
    )
    print(f"Missing or marked counts preserved as blank: {missing_count.sum():,}")
    print(f"Invalid counts preserved as blank: {invalid_count.sum():,}")
    if invalid_count.any():
        print("Invalid count examples:", ", ".join(counts[invalid_count].unique()[:8]))

    data = reconcile_keys(data)
    years = sorted(set(range(2008, 2017)) - set(data["year"]))
    print("Years without retained rows:", years)
    # Large counts can represent real refugee populations. Surface them for review.
    print("\nLargest reported counts for review (retained as reported):")
    print(data.dropna(subset=["refugee_count"]).nlargest(10, "refugee_count").to_string(index=False))
    return data.sort_values(KEY)


YEARS = [str(year) for year in range(2008, 2017)]
IDENTIFIERS = ["Country Name", "Country Code", "Indicator Code"]
INDICATORS = {
    "SP.POP.TOTL": "total_population",
    "NY.GDP.PCAP.CD": "gdp_per_capita_current_usd",
}


def keep_countries(annual, value_name, metadata_path):
    metadata = pd.read_csv(metadata_path, dtype="string", keep_default_na=False)
    required = {"Country Code", "Region"}
    if not required.issubset(metadata.columns):
        raise ValueError(f"{metadata_path.name}: expected Country Code and Region.")
    codes = metadata["Country Code"].str.strip()
    if codes.eq("").any() or codes.duplicated().any():
        raise ValueError(f"{metadata_path.name}: country codes must be nonblank and unique.")

    countries = codes[metadata["Region"].str.strip().ne("")]
    unclassified = ~annual["country_code"].isin(codes)
    if (unclassified & annual[value_name].notna()).any():
        unknown = annual.loc[unclassified & annual[value_name].notna(), "country_code"]
        raise ValueError(f"Codes missing from country metadata with values: {sorted(unknown.unique())}.")
    keep = annual["country_code"].isin(countries)
    print(f"Excluded {annual.loc[~keep & ~unclassified, 'country_code'].nunique()} aggregate codes.")
    print(f"Excluded unlisted codes with no values: {sorted(annual.loc[unclassified, 'country_code'].unique())}.")
    return annual.loc[keep]


def clean_world_bank(path, indicator, metadata_path=None):
    value_name = INDICATORS[indicator]
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        for row in reader:
            if set(IDENTIFIERS).issubset(row):
                header_row = reader.line_num - 1
                break
            if reader.line_num >= 20:
                raise ValueError(f"{path.name}: WDI header not found in the first 20 lines.")
        else:
            raise ValueError(f"{path.name}: WDI header not found.")

    raw = pd.read_csv(path, skiprows=header_row, dtype="string", keep_default_na=False)
    missing_years = sorted(set(YEARS) - set(raw.columns))
    if missing_years:
        raise ValueError(f"{path.name}: missing year columns {missing_years}.")

    selected = raw.loc[raw["Indicator Code"].str.strip().eq(indicator), IDENTIFIERS + YEARS]
    data = selected.apply(lambda column: column.str.strip()).drop(columns="Indicator Code")
    data = data.rename(columns={"Country Name": "country_name", "Country Code": "country_code"})
    if data.empty:
        raise ValueError(f"{path.name}: no rows for indicator {indicator}.")
    if data["country_code"].eq("").any() or data["country_name"].eq("").any():
        raise ValueError(f"{path.name}: blank country name or code.")

    without_duplicates = data.drop_duplicates()
    repeated_codes = without_duplicates["country_code"].duplicated(keep=False)
    if repeated_codes.any():
        codes = without_duplicates.loc[repeated_codes, "country_code"].unique().tolist()
        raise ValueError(f"{path.name}: conflicting records for country codes {codes}.")

    annual = without_duplicates.melt(
        id_vars=["country_code", "country_name"],
        value_vars=YEARS,
        var_name="year",
        value_name=value_name,
    )
    # Preserve blanks and check unexpected tokens before any downstream join.
    values = annual[value_name]
    numeric = pd.to_numeric(values.where(values.ne("")), errors="coerce")
    invalid = values.ne("") & (numeric.isna() | ~np.isfinite(numeric))
    if indicator == "SP.POP.TOTL":
        invalid |= numeric.lt(0).fillna(False) | numeric.mod(1).ne(0).fillna(False)
        numeric = numeric.mask(invalid)
        numeric = numeric.astype("Int64")
    if invalid.any():
        examples = values.loc[invalid].unique().tolist()[:8]
        raise ValueError(f"{path.name}: {invalid.sum()} invalid values, including {examples}.")
    annual[value_name] = numeric
    annual["year"] = parse_year(annual["year"].astype("string")).astype("int64")
    print(f"{path.name}: {len(raw):,} raw rows, {len(data) - len(without_duplicates):,} exact duplicates removed.")
    print(f"{len(annual):,} entity-year rows, {numeric.isna().sum():,} missing values.")
    if metadata_path is not None:
        annual = keep_countries(annual, value_name, metadata_path)
        print(f"Kept {len(annual):,} country/economy-year rows, {annual[value_name].isna().sum():,} missing values.")
    else:
        print("Source aggregates are retained here for review before the host-country join.")
    return annual.sort_values(["country_code", "year"], ignore_index=True)


# UNHCR labels that differ from the World Bank economy names in these files.
# Keep combined territories and entities without a World Bank code unmatched.
HOST_ALIASES = {
    "Bahamas": "BHS",
    "Bolivia (Plurinational State of)": "BOL",
    "Central African Rep.": "CAF",
    "China, Hong Kong SAR": "HKG",
    "China, Macao SAR": "MAC",
    "Congo": "COG",
    "Czech Rep.": "CZE",
    "Dem. People's Rep. of Korea": "PRK",
    "Dem. Rep. of the Congo": "COD",
    "Dominican Rep.": "DOM",
    "Egypt": "EGY",
    "Gambia": "GMB",
    "Iran (Islamic Rep. of)": "IRN",
    "Kyrgyzstan": "KGZ",
    "Micronesia (Federated States of)": "FSM",
    "Nauru": "NRU",
    "Rep. of Korea": "KOR",
    "Rep. of Moldova": "MDA",
    "Saint Kitts and Nevis": "KNA",
    "Saint Lucia": "LCA",
    "Slovakia": "SVK",
    "Somalia": "SOM",
    "Swaziland": "SWZ",
    "Syrian Arab Rep.": "SYR",
    "The former Yugoslav Republic of Macedonia": "MKD",
    "Turkey": "TUR",
    "United Rep. of Tanzania": "TZA",
    "United States of America": "USA",
    "Venezuela (Bolivarian Republic of)": "VEN",
    "Yemen": "YEM",
}
JOIN_KEY = ["country_code", "year"]


def normalize_name(name):
    plain = unicodedata.normalize("NFKD", name.casefold())
    return re.sub(r"[^a-z0-9]", "", plain)


def join_host_indicators(unhcr, population, gdp):
    names = population[["country_code", "country_name"]].drop_duplicates()
    names = names.assign(name_key=names["country_name"].map(normalize_name))
    if names["name_key"].duplicated().any() or names["country_code"].duplicated().any():
        raise ValueError("World Bank economy names and codes must map uniquely.")
    name_to_code = names.set_index("name_key")["country_code"].to_dict()
    economy_names = names.set_index("country_code")["country_name"]

    by_host = unhcr.groupby(["host_country", "year"], sort=True)["refugee_count"]
    hosts = by_host.sum(min_count=1).rename("reported_refugee_count").to_frame()
    hosts["missing_refugee_count_rows"] = by_host.size() - by_host.count()
    hosts = hosts.reset_index()
    host_codes = hosts["host_country"].map(HOST_ALIASES)
    normalized_codes = hosts["host_country"].map(normalize_name).map(name_to_code)
    disagreement = host_codes.notna() & normalized_codes.notna() & host_codes.ne(normalized_codes)
    if disagreement.any():
        raise ValueError("An explicit UNHCR alias conflicts with a World Bank name match.")
    hosts["country_code"] = host_codes.fillna(normalized_codes).astype("string")
    if not set(hosts["country_code"].dropna()).issubset(economy_names.index):
        raise ValueError("A mapped UNHCR code is absent from the World Bank economy table.")
    present = hosts["country_code"].notna()
    if hosts.loc[present].duplicated(JOIN_KEY).any():
        raise ValueError("Different UNHCR labels map to the same World Bank economy and year.")
    if population[JOIN_KEY].isna().any().any() or gdp[JOIN_KEY].isna().any().any():
        raise ValueError("World Bank join keys must be populated.")

    result = hosts.merge(
        population[JOIN_KEY + ["total_population"]], on=JOIN_KEY, how="left", validate="many_to_one"
    ).merge(
        gdp[JOIN_KEY + ["gdp_per_capita_current_usd"]], on=JOIN_KEY, how="left", validate="many_to_one"
    )
    if len(result) != len(hosts):
        raise ValueError("The join changed the number of UNHCR host-year rows.")
    result["country_name"] = result["country_code"].map(economy_names)
    positive_population = result["total_population"].where(result["total_population"].gt(0))
    result["reported_refugees_per_1000_residents"] = (
        result["reported_refugee_count"] / positive_population * 1000
    )
    print(f"UNHCR host-year rows: {len(result):,}")
    print(f"With population: {result['total_population'].notna().sum():,}")
    print(f"With GDP per capita: {result['gdp_per_capita_current_usd'].notna().sum():,}")
    print("Unmatched host labels:", sorted(result.loc[result["country_code"].isna(), "host_country"].unique()))
    return result


IDMC_SHEET = "1_Displacement_data"
IDMC_COLUMNS = {
    "ISO3": "country_code",
    "Name": "country_name",
    "Year": "year",
    "Conflict Stock Displacement (Raw)": "conflict_stock_people",
    "Disaster Stock Displacement (Raw)": "disaster_stock_people",
}


def clean_idmc(path):
    raw = pd.read_excel(path, sheet_name=IDMC_SHEET, dtype="string", keep_default_na=False)
    missing = sorted(set(IDMC_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"{path.name}: missing IDMC columns {missing}.")
    print(f"IDMC: {len(raw):,} raw rows × {len(raw.columns)} columns.")
    unique = raw.drop_duplicates()
    print(f"IDMC: {len(raw) - len(unique):,} identical rows removed.")
    data = unique[list(IDMC_COLUMNS)].rename(columns=IDMC_COLUMNS)
    data = data.apply(lambda column: column.str.strip())
    year = parse_year(data["year"])
    if year.isna().any():
        raise ValueError(f"{path.name}: invalid or missing IDMC year.")
    in_period = year.between(2008, 2016)
    data = data.loc[in_period].copy()
    data["year"] = year.loc[in_period].astype("int64")
    if data[["country_code", "country_name"]].eq("").any().any():
        raise ValueError(f"{path.name}: missing IDMC country or territory identifier.")
    if data.duplicated(JOIN_KEY).any():
        raise ValueError(f"{path.name}: conflicting IDMC records for a country code and year.")
    if set(data["year"]) != set(range(2008, 2017)):
        raise ValueError(f"{path.name}: expected all nine IDMC years from 2008 through 2016.")

    stock_columns = ["conflict_stock_people", "disaster_stock_people"]
    for column in stock_columns:
        counts = data[column]
        number = counts.str.fullmatch(r"[0-9]+")
        invalid = counts.ne("") & ~number
        if invalid.any():
            raise ValueError(f"{path.name}: invalid IDMC values in {column}.")
        data[column] = counts.where(number).astype("Int64")
        print(f"IDMC {column}: {data[column].notna().sum():,} reported, {data[column].isna().sum():,} missing.")
    print(f"IDMC rows with both stocks reported: {data[stock_columns].notna().all(axis=1).sum():,}.")
    return data.sort_values(JOIN_KEY, ignore_index=True)


def find_input(directory, patterns, label):
    matches = sorted({path for pattern in patterns for path in directory.glob(pattern) if path.is_file()})
    if len(matches) != 1:
        found = ", ".join(path.name for path in matches) or "none"
        raise ValueError(
            f"{label}: expected exactly one file in {directory} matching "
            f"{', '.join(patterns)}. Found: {found}."
        )
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    raw = args.raw_dir

    try:
        if raw.resolve() == args.output_dir.resolve():
            raise ValueError("The input and output directories must differ.")
        unhcr_path = find_input(raw, ["time_series.csv"], "UNHCR")
        population_path = find_input(
            raw, ["worldbankpopulation.csv", "API_SP.POP.TOTL*.csv"], "World Bank population"
        )
        gdp_path = find_input(raw, ["API_NY.GDP.PCAP.CD*.csv"], "World Bank GDP per capita")
        metadata_path = find_input(
            raw, ["Metadata_Country_API_SP.POP.TOTL*.csv"], "World Bank country metadata"
        )
        idmc_path = find_input(
            raw, ["IDMC_Internal_Displacement_Conflict-Violence_Disasters*.xlsx"], "IDMC"
        )

        unhcr = clean_unhcr(read_unhcr_source(unhcr_path), REFUGEE_LABEL)
        population = clean_world_bank(population_path, "SP.POP.TOTL", metadata_path)
        gdp = clean_world_bank(gdp_path, "NY.GDP.PCAP.CD", metadata_path)
        idmc = clean_idmc(idmc_path)
        joined = join_host_indicators(unhcr, population, gdp)

        outputs = {
            "unhcr_clean.csv": unhcr,
            "worldbank_population_clean.csv": population,
            "worldbank_gdp_clean.csv": gdp,
            "idmc_clean.csv": idmc,
            "unhcr_world_bank_host_year.csv": joined,
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, table in outputs.items():
            target = args.output_dir / name
            table.to_csv(target, index=False)
            print(f"Saved {target}: {len(table):,} rows × {len(table.columns)} columns.")
    except (OSError, UnicodeError, ValueError, csv.Error, ImportError) as error:
        parser.exit(1, f"Data preparation failed: {error}\n")


if __name__ == "__main__":
    main()
