"""
build_chunks.py
---------------
Reads fund_metrics.csv and builds one human-readable text document
per fund. These chunks are what gets embedded and stored in ChromaDB.

Good chunk = structured text that answers the question a user might ask.
Bad chunk  = raw numbers with no context.

Saves to data/chunks.jsonl (one JSON object per line)

Run: python processing/build_chunks.py
"""

import pandas as pd
import json
import os
import numpy as np

METRICS_FILE = os.path.join("data", "fund_metrics.csv")
OUTPUT_FILE  = os.path.join("data", "chunks.jsonl")


def rating(cagr_3y: float, sharpe: float) -> str:
    """Simple human-readable rating based on returns + risk-adjusted score."""
    if pd.isna(cagr_3y) or pd.isna(sharpe):
        return "Insufficient data"
    if cagr_3y >= 15 and sharpe >= 1.0:
        return "Strong performer — high returns with good risk management"
    elif cagr_3y >= 12 and sharpe >= 0.7:
        return "Good performer — above average returns, moderate risk"
    elif cagr_3y >= 8:
        return "Average performer — steady but not exceptional"
    else:
        return "Below average — consider alternatives in this category"


def clean_name(name: str) -> str:
    """Extract a short readable fund name."""
    # Remove common suffixes for cleaner display
    for suffix in [" - Direct Plan - Growth", " - Direct Plan-Growth",
                   " Direct Plan Growth", "-Direct Plan-Growth",
                   " Direct Growth", "- Growth"]:
        name = name.replace(suffix, "")
    return name.strip()


def build_chunk(row: pd.Series) -> dict:
    """
    Build a natural language chunk for one fund.
    Format is designed so the LLM can answer questions like:
      - 'Which large cap fund gave best 3 year returns?'
      - 'Kaun sa fund kam risk mein accha return deta hai?'
      - 'SBI vs HDFC large cap fund comparison'
    """
    name      = clean_name(str(row["scheme_name"]))
    cagr_1y   = row["cagr_1y"]
    cagr_3y   = row["cagr_3y"]
    cagr_5y   = row["cagr_5y"]
    sharpe    = row["sharpe_3y"]
    sortino   = row["sortino_3y"]
    nav       = row["latest_nav"]
    fund_rating = rating(cagr_3y, sharpe)

    # Handle missing values gracefully
    def fmt(val, suffix="%"):
        return f"{val}{suffix}" if not pd.isna(val) else "N/A"

    chunk_text = f"""Fund Name: {name}
Category: Large Cap Equity Fund (Direct Plan - Growth)
Latest NAV: ₹{fmt(nav, '')}

Performance:
- 1 Year Return (CAGR): {fmt(cagr_1y)}
- 3 Year Return (CAGR): {fmt(cagr_3y)}
- 5 Year Return (CAGR): {fmt(cagr_5y)}

Risk-Adjusted Metrics:
- Sharpe Ratio (3Y): {fmt(sharpe, '')} — measures return earned per unit of total risk
- Sortino Ratio (3Y): {fmt(sortino, '')} — measures return earned per unit of downside risk only

Overall Assessment: {fund_rating}

Suitable for: Long-term investors (3-5+ years) seeking equity growth with lower volatility than mid/small cap funds. Large cap funds invest in top 100 companies by market capitalisation.
"""

    return {
        "scheme_code" : int(row["scheme_code"]),
        "fund_name"   : name,
        "chunk_text"  : chunk_text,
        "metadata"    : {
            "category"  : "Large Cap",
            "cagr_1y"   : None if pd.isna(cagr_1y)  else float(cagr_1y),
            "cagr_3y"   : None if pd.isna(cagr_3y)  else float(cagr_3y),
            "cagr_5y"   : None if pd.isna(cagr_5y)  else float(cagr_5y),
            "sharpe_3y" : None if pd.isna(sharpe)    else float(sharpe),
            "sortino_3y": None if pd.isna(sortino)   else float(sortino),
            "latest_nav": None if pd.isna(nav)        else float(nav),
        }
    }


def main():
    print("Loading metrics...")
    df = pd.read_csv(METRICS_FILE)
    print(f"Funds loaded: {len(df)}")

    chunks = []
    for _, row in df.iterrows():
        chunk = build_chunk(row)
        chunks.append(chunk)
        print(f"  Built chunk: {chunk['fund_name'][:55]}")

    # Save as JSONL (one JSON object per line — standard for RAG pipelines)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(chunks)} chunks to {OUTPUT_FILE}")
    print("\nSample chunk:\n")
    print(chunks[0]["chunk_text"])


if __name__ == "__main__":
    main()
