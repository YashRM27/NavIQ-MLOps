"""
fetch_schemes.py
----------------
Downloads the AMFI master fund list and filters to Large Cap equity funds only.
Saves result to data/scheme_list.csv

Run: python data/fetch_schemes.py
"""

import requests
import pandas as pd
import os

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "scheme_list.csv")


def fetch_amfi_data(url: str) -> list[dict]:
    """Download and parse the AMFI NAVAll.txt file into a list of fund dicts."""
    print("Fetching AMFI master list...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    funds = []
    current_category = ""

    for line in response.text.splitlines():
        line = line.strip()

        # Category header lines look like:
        # "Open Ended Schemes(Equity Scheme - Large Cap Fund)"
        if line.startswith("Open Ended Schemes") or line.startswith("Close Ended"):
            current_category = line
            continue

        # Data lines have semicolons: SchemeCode;ISINDiv;ISINGrowth;SchemeName;NAV;Date
        parts = line.split(";")
        if len(parts) < 6:
            continue

        scheme_code = parts[0].strip()
        scheme_name = parts[3].strip()
        nav = parts[4].strip()
        nav_date = parts[5].strip()

        if not scheme_code.isdigit():
            continue

        funds.append({
            "scheme_code": int(scheme_code),
            "scheme_name": scheme_name,
            "nav": nav,
            "nav_date": nav_date,
            "category_raw": current_category,
        })

    return funds


def filter_large_cap(funds: list[dict]) -> pd.DataFrame:
    """Keep only Large Cap equity funds (Growth option, Direct plan)."""
    df = pd.DataFrame(funds)

    # Filter to Large Cap category
    large_cap_mask = df["category_raw"].str.contains(
        "Large Cap", case=False, na=False
    )
    df = df[large_cap_mask].copy()

    # Keep only Growth option (avoids duplicate dividend variants)
    growth_mask = df["scheme_name"].str.contains(
        "Growth", case=False, na=False
    )
    df = df[growth_mask].copy()

    # Prefer Direct plans (lower expense ratio, cleaner data)
    direct_mask = df["scheme_name"].str.contains(
        "Direct", case=False, na=False
    )
    df_direct = df[direct_mask].copy()

    # If no direct plans found, fall back to all
    if df_direct.empty:
        print("Warning: No Direct plans found, using all growth plans.")
        df_direct = df

    # Clean up
    df_direct = df_direct.reset_index(drop=True)
    df_direct["nav"] = pd.to_numeric(df_direct["nav"], errors="coerce")

    return df_direct


def main():
    funds = fetch_amfi_data(AMFI_URL)
    print(f"Total funds fetched: {len(funds)}")

    df = filter_large_cap(funds)
    print(f"Large Cap (Direct Growth) funds found: {len(df)}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved to: {OUTPUT_FILE}")
    print("\nSample funds:")
    print(df[["scheme_code", "scheme_name", "nav"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
