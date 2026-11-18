"""Prepare the four refugee project datasets for 2008–2016."""

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
