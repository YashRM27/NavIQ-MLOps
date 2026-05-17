"""
compute_metrics.py
------------------
Reads nav_history.parquet and scheme_list.csv
Computes for each fund:
  - CAGR (1Y, 3Y, 5Y)
  - Sharpe Ratio (3Y)
  - Sortino Ratio (3Y)

Saves result to data/fund_metrics.csv

Run: python processing/compute_metrics.py
"""

import pandas as pd
import numpy as np
import os

NAV_FILE     = os.path.join("data", "nav_history.parquet")
SCHEMES_FILE = os.path.join("data", "scheme_list.csv")
OUTPUT_FILE  = os.path.join("data", "fund_metrics.csv")

RISK_FREE_RATE = 0.065  # ~6.5% annual (approx Indian 10yr govt bond)
TRADING_DAYS   = 252


def compute_cagr(nav_series: pd.Series, years: int) -> float:
    """
    CAGR = (End NAV / Start NAV) ^ (1/years) - 1
    Returns NaN if not enough data.
    """
    nav_sorted = nav_series.sort_index()
    end_date   = nav_sorted.index.max()
    start_date = end_date - pd.DateOffset(years=years)

    # Find closest available date to start_date
    available = nav_sorted[nav_sorted.index >= start_date]
    if available.empty or len(available) < 30:
        return np.nan

    start_nav = available.iloc[0]
    end_nav   = nav_sorted.iloc[-1]

    if start_nav <= 0:
        return np.nan

    cagr = (end_nav / start_nav) ** (1 / years) - 1
    return round(cagr * 100, 2)   # as percentage


def compute_sharpe(daily_returns: pd.Series) -> float:
    """
    Sharpe = (Mean daily return - Daily risk free) / Std of daily returns
    Annualised by multiplying by sqrt(252)
    """
    if daily_returns.empty or daily_returns.std() == 0:
        return np.nan

    daily_rf   = RISK_FREE_RATE / TRADING_DAYS
    excess     = daily_returns - daily_rf
    sharpe     = (excess.mean() / excess.std()) * np.sqrt(TRADING_DAYS)
    return round(sharpe, 3)


def compute_sortino(daily_returns: pd.Series) -> float:
    """
    Sortino = (Mean daily return - Daily risk free) / Downside deviation
    Only penalises negative returns, unlike Sharpe which penalises all volatility.
    """
    if daily_returns.empty:
        return np.nan

    daily_rf       = RISK_FREE_RATE / TRADING_DAYS
    excess         = daily_returns - daily_rf
    downside       = daily_returns[daily_returns < 0]

    if downside.empty or downside.std() == 0:
        return np.nan

    downside_std   = downside.std() * np.sqrt(TRADING_DAYS)
    sortino        = (excess.mean() * TRADING_DAYS) / downside_std
    return round(sortino, 3)


def process_fund(scheme_code: int, nav_df: pd.DataFrame) -> dict:
    """Compute all metrics for one fund."""
    fund_nav = nav_df[nav_df["scheme_code"] == scheme_code].copy()
    fund_nav = fund_nav.set_index("date").sort_index()["nav"]

    # Remove duplicate dates (keep last)
    fund_nav = fund_nav[~fund_nav.index.duplicated(keep="last")]

    # Daily returns
    daily_returns = fund_nav.pct_change().dropna()

    # Last 3 years of returns for Sharpe/Sortino
    cutoff_3y     = fund_nav.index.max() - pd.DateOffset(years=3)
    returns_3y    = daily_returns[daily_returns.index >= cutoff_3y]

    return {
        "scheme_code" : scheme_code,
        "cagr_1y"     : compute_cagr(fund_nav, 1),
        "cagr_3y"     : compute_cagr(fund_nav, 3),
        "cagr_5y"     : compute_cagr(fund_nav, 5),
        "sharpe_3y"   : compute_sharpe(returns_3y),
        "sortino_3y"  : compute_sortino(returns_3y),
        "latest_nav"  : round(fund_nav.iloc[-1], 3) if not fund_nav.empty else np.nan,
        "data_points" : len(fund_nav),
    }


def main():
    print("Loading data...")
    nav_df   = pd.read_parquet(NAV_FILE)
    schemes  = pd.read_csv(SCHEMES_FILE)

    nav_df["date"] = pd.to_datetime(nav_df["date"])
    print(f"Funds to process: {schemes['scheme_code'].nunique()}")

    results = []
    for _, row in schemes.iterrows():
        code = int(row["scheme_code"])
        metrics = process_fund(code, nav_df)
        results.append(metrics)
        print(f"  {row['scheme_name'][:50]:<50} | "
              f"1Y: {metrics['cagr_1y']}%  "
              f"3Y: {metrics['cagr_3y']}%  "
              f"Sharpe: {metrics['sharpe_3y']}")

    metrics_df = pd.DataFrame(results)

    # Merge with scheme names and category
    metrics_df = metrics_df.merge(
        schemes[["scheme_code", "scheme_name", "category_raw"]],
        on="scheme_code", how="left"
    )

    # Drop funds with no data at all
    metrics_df = metrics_df.dropna(subset=["cagr_1y", "cagr_3y"])

    metrics_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(metrics_df)} funds to {OUTPUT_FILE}")
    print("\nTop 5 funds by 3Y CAGR:")
    top5 = metrics_df.nlargest(5, "cagr_3y")[["scheme_name", "cagr_3y", "sharpe_3y", "sortino_3y"]]
    print(top5.to_string(index=False))


if __name__ == "__main__":
    main()
