"""
fetch_nav.py
------------
For each scheme in scheme_list.csv, fetches 5 years of daily NAV
from mfapi.in and saves everything to data/nav_history.parquet

Run AFTER fetch_schemes.py:
    python data/fetch_nav.py

Expected time: ~2-5 min for 30-40 funds (free API, rate limited politely)
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta

SCHEMES_FILE = os.path.join(os.path.dirname(__file__), "scheme_list.csv")
OUTPUT_FILE  = os.path.join(os.path.dirname(__file__), "nav_history.parquet")

MFAPI_URL    = "https://api.mfapi.in/mf/{scheme_code}"
YEARS_BACK   = 5
SLEEP_SEC    = 0.5   # polite delay between API calls


def fetch_nav_for_scheme(scheme_code: int) -> pd.DataFrame:
    """
    Fetch full NAV history for one scheme from mfapi.in
    Returns a DataFrame with columns: scheme_code, date, nav
    """
    url = MFAPI_URL.format(scheme_code=scheme_code)
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  ERROR fetching {scheme_code}: {e}")
        return pd.DataFrame()

    records = data.get("data", [])
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)           # columns: date, nav
    df["scheme_code"] = scheme_code
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"]  = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["date", "nav"])

    return df[["scheme_code", "date", "nav"]]


def filter_last_n_years(df: pd.DataFrame, years: int) -> pd.DataFrame:
    """Keep only rows within the last `years` years."""
    cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
    return df[df["date"] >= cutoff]


def main():
    # Load scheme list
    if not os.path.exists(SCHEMES_FILE):
        raise FileNotFoundError(
            f"{SCHEMES_FILE} not found.\nRun fetch_schemes.py first."
        )

    schemes = pd.read_csv(SCHEMES_FILE)
    print(f"Schemes to fetch NAV for: {len(schemes)}")
    print(f"Fetching {YEARS_BACK} years of daily NAV from mfapi.in...\n")

    all_nav = []
    failed  = []

    for i, row in schemes.iterrows():
        code = int(row["scheme_code"])
        name = row["scheme_name"][:55]   # truncate for display
        print(f"[{i+1}/{len(schemes)}] {code} — {name}")

        nav_df = fetch_nav_for_scheme(code)

        if nav_df.empty:
            print(f"  Skipped (no data)")
            failed.append(code)
        else:
            nav_df = filter_last_n_years(nav_df, YEARS_BACK)
            all_nav.append(nav_df)
            print(f"  {len(nav_df)} rows | "
                  f"{nav_df['date'].min().date()} → {nav_df['date'].max().date()}")

        time.sleep(SLEEP_SEC)

    if not all_nav:
        print("No NAV data collected. Check API connectivity.")
        return

    # Combine and save
    combined = pd.concat(all_nav, ignore_index=True)
    combined = combined.sort_values(["scheme_code", "date"]).reset_index(drop=True)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    combined.to_parquet(OUTPUT_FILE, index=False)

    print(f"\nDone!")
    print(f"Total rows saved : {len(combined):,}")
    print(f"Schemes succeeded: {len(all_nav)}")
    print(f"Schemes failed   : {len(failed)} {failed if failed else ''}")
    print(f"Saved to         : {OUTPUT_FILE}")
    print(f"\nDate range: {combined['date'].min().date()} → {combined['date'].max().date()}")


if __name__ == "__main__":
    main()
