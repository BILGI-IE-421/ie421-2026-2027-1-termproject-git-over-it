
"""Download raw IE421 refugee project datasets."""

import os
import io
import zipfile
import shutil
import hashlib
import json

from pathlib import Path
from datetime import datetime, timezone

import requests
import kagglehub


BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"

RAW.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "UNHCR": "https://www.kaggle.com/datasets/unitednations/refugee-data",
    "Population": "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?downloadformat=csv",
    "GDP_PPP": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.PP.KD?downloadformat=csv",
    "IDMC": "https://www.internal-displacement.org/database/"
}


def save_file(source, destination):
    shutil.copyfile(source, destination)
    print("Saved:", destination.name)


# 1. UNHCR
def download_unhcr():
    print("\n[1/4] UNHCR")

    source_dir = Path(
        kagglehub.dataset_download(
            "unitednations/refugee-data"
        )
    )

    matches = list(source_dir.rglob("time_series.csv"))

    if len(matches) != 1:
        raise FileNotFoundError(
            "Expected one time_series.csv in Kaggle dataset."
        )

    save_file(
        matches[0],
        RAW / "time_series.csv"
    )


# 2. WORLD BANK
def download_world_bank(indicator):
    print(f"\nWorld Bank: {indicator}")

    url = (
        "https://api.worldbank.org/v2/"
        f"country/all/indicator/{indicator}"
    )

    response = requests.get(
        url,
        params={
            "downloadformat": "csv",
            "dataformat": "table"
        },
        timeout=120
    )
    response.raise_for_status()

    archive = io.BytesIO(response.content)

    if not zipfile.is_zipfile(archive):
        raise ValueError(
            f"{indicator}: World Bank did not return a ZIP file."
        )

    archive.seek(0)

    expected_prefixes = {
        "data": f"API_{indicator}",
        "country_metadata": f"Metadata_Country_API_{indicator}",
        "indicator_metadata": f"Metadata_Indicator_API_{indicator}"
    }

    found = {key: False for key in expected_prefixes}
    files_to_save = []

    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            filename = Path(name).name

            if not filename.lower().endswith(".csv"):
                continue

            for key, prefix in expected_prefixes.items():
                if filename.startswith(prefix):
                    found[key] = True
                    files_to_save.append((name, filename))
                    break

        missing = [
            key for key, exists in found.items()
            if not exists
        ]

        if missing:
            raise ValueError(
                f"{indicator}: Missing files: {missing}"
            )

        for name, filename in files_to_save:
            destination = RAW / filename

            with z.open(name) as source:
                with open(destination, "wb") as target:
                    shutil.copyfileobj(source, target)

            print("Saved:", destination.name)

    print(f"{indicator}: All 3 CSV files downloaded.")


# 3. IDMC
def download_idmc():
    print("\n[4/4] IDMC")

    url = (
        "https://helix-tools-api.idmcdb.org/"
        "external-api/gidd/displacements/displacement-export/"
    )

    params = {
        "client_id": "IDMCWSHSOLO009",
        "release_environment": "RELEASE"
    }

    response = requests.get(
        url,
        params=params,
        timeout=180
    )

    response.raise_for_status()

    content = response.content

    # Check whether the response is an Excel file
    if not (
        content.startswith(b"PK\x03\x04")
        or content.startswith(b"\xd0\xcf\x11\xe0")
    ):
        raise ValueError(
            "IDMC API did not return a valid Excel file."
        )

    destination = RAW / "idmc_displacement.xlsx"

    destination.write_bytes(content)

    print("Saved:", destination.name)


# 4. DOWNLOAD MANIFEST
def sha256_file(path):
    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def create_manifest(successful_sources, errors, downloaded_files):
    manifest_path = RAW / "download_manifest.json"

    files = []

    for path in sorted(downloaded_files):
        if not path.is_file():
            continue

        # Exclude the manifest itself
        if path.name == "download_manifest.json":
            continue

        files.append({
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path)
        })

    manifest = {
        "downloaded_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "sources": SOURCES,
        "successful_sources": successful_sources,
        "errors": errors,
        "files": files
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\nManifest saved:", manifest_path)


# 5. MAIN FUNCTION
def main():
    errors = {}
    successful_sources = []

    tasks = [
        ("UNHCR", download_unhcr),
        (
            "Population",
            lambda: download_world_bank("SP.POP.TOTL")
        ),
        (
            "GDP_PPP",
            lambda: download_world_bank("NY.GDP.PCAP.PP.KD")
        ),
        ("IDMC", download_idmc)
    ]

    downloaded_files = set()

    for name, function in tasks:
        print(f"\nDownloading {name}...")

        try:
            before = {p: (p.stat().st_mtime_ns, p.stat().st_size) for p in RAW.iterdir() if p.is_file()}
            function()
            after = {p: (p.stat().st_mtime_ns, p.stat().st_size) for p in RAW.iterdir() if p.is_file()}
            downloaded_files.update(p for p in after if p not in before or after[p] != before[p])
            successful_sources.append(name)
            print(f"{name}: SUCCESS")

        except Exception as e:
            errors[name] = str(e)
            print(f"{name}: FAILED ({e})")

    create_manifest(successful_sources, errors, downloaded_files)

    print("\n========== DOWNLOAD SUMMARY ==========")

    for name, _ in tasks:
        if name in successful_sources:
            print(f"{name}: SUCCESS")
        else:
            print(f"{name}: FAILED")

    print(
        f"\nSuccessful downloads: "
        f"{len(successful_sources)}/{len(tasks)}"
    )

    if errors:
        print("\nErrors:")
        for name, error in errors.items():
            print(f"- {name}: {error}")


if __name__ == "__main__":
    main()
