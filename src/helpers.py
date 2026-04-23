"""
helpers.py — Reusable utility functions for the Azzurri project.

These functions are imported into the notebooks to avoid repeating the same
code in multiple places. Keeping logic here also makes the notebooks cleaner
and easier to read.
"""

import numpy as np
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup


# ── Scraping helpers ──────────────────────────────────────────────────────────

# Transfermarkt blocks requests that don't look like a real browser.
# This header string makes our scraper look like Chrome on Windows.
TM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Mapping: country name → Transfermarkt competition code
# Top 10 UEFA-ranked nations (2025/26 country coefficients).
# Used to loop over leagues systematically.
LEAGUE_CODES = {
    "England":     "GB1",
    "Italy":       "IT1",
    "Spain":       "ES1",
    "Germany":     "L1",
    "France":      "FR1",
    "Netherlands": "NL1",
    "Portugal":    "PO1",
    "Belgium":     "BE1",
    "Turkey":      "TR1",
    "Czechia":     "TS1",
}

# Real league name slugs as they appear in Transfermarkt URLs.
LEAGUE_SLUGS = {
    "England":     "premier-league",
    "Italy":       "serie-a",
    "Spain":       "laliga",
    "Germany":     "1-bundesliga",
    "France":      "ligue-1",
    "Netherlands": "eredivisie",
    "Portugal":    "liga-nos",
    "Belgium":     "jupiler-pro-league",
    "Turkey":      "super-lig",
    "Czechia":     "czech-liga",
}

# Mapping: country → the nationality that counts as "domestic"
# Used when computing % foreign players.
DOMESTIC_NATIONALITY = {
    "England":     "ENG",
    "Italy":       "ITA",
    "Spain":       "ESP",
    "Germany":     "GER",
    "France":      "FRA",
    "Netherlands": "NED",
    "Portugal":    "POR",
    "Belgium":     "BEL",
    "Turkey":      "TUR",
    "Czechia":     "CZE",
}


def safe_get(url, headers=TM_HEADERS, sleep=3, retries=3):
    """
    Makes an HTTP GET request with retry logic.

    Why we need this:
    - Transfermarkt occasionally returns a 503 (server busy) or blocks us.
    - Retrying after a short wait usually fixes it.
    - The sleep avoids hammering the server and getting our IP banned.

    Args:
        url (str): The page to fetch.
        headers (dict): Browser-like headers to send.
        sleep (int): Seconds to wait between each attempt.
        retries (int): How many times to try before giving up.

    Returns:
        requests.Response or None if all attempts fail.
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                time.sleep(sleep)
                return response
            else:
                print(f"  ⚠️  Status {response.status_code} for {url} — attempt {attempt + 1}/{retries}")
                time.sleep(sleep * 2)  # wait longer after a bad response
        except requests.RequestException as e:
            print(f"  ❌ Request failed: {e} — attempt {attempt + 1}/{retries}")
            time.sleep(sleep * 2)
    print(f"  ✗ Gave up on {url} after {retries} attempts.")
    return None


# ── Data parsing helpers ──────────────────────────────────────────────────────

def parse_market_value(value_str):
    """
    Converts a Transfermarkt market value string into a float (millions of €).

    Transfermarkt formats values like:
        "€850.00m"  →  850.0  (already in millions)
        "€1.20bn"   →  1200.0 (billions converted to millions)
        "€500k"     →  0.5    (thousands converted to millions)
        "-"         →  NaN    (no data)

    Args:
        value_str (str): Raw string from the page.

    Returns:
        float: Market value in millions of euros, or NaN if unparseable.
    """
    if not isinstance(value_str, str):
        return np.nan

    v = value_str.strip().lower().replace("€", "").replace(",", "")

    if v in ["-", "", "n/a"]:
        return np.nan

    try:
        if "bn" in v:
            return float(v.replace("bn", "")) * 1000
        elif "m" in v:
            return float(v.replace("m", ""))
        elif "k" in v:
            return float(v.replace("k", "")) / 1000
        else:
            return float(v) / 1_000_000  # assume raw euros
    except ValueError:
        return np.nan


# ── Statistical helpers ───────────────────────────────────────────────────────

def gini(values):
    """
    Computes the Gini coefficient for an array of values.

    The Gini coefficient measures inequality:
        0 = perfect equality (all clubs have the same squad value)
        1 = perfect inequality (one club has everything)

    This is the standard formula from economics, adapted for discrete data.

    Args:
        values (array-like): Market values of each club in a league for one season.

    Returns:
        float: Gini coefficient between 0 and 1. NaN if fewer than 2 values.
    """
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]  # remove NaN entries

    if len(arr) < 2:
        return np.nan

    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * arr)) / (n * np.sum(arr)) - (n + 1) / n)


def compute_gini_by_group(df, group_cols, value_col):
    """
    Applies the Gini function across groups in a DataFrame.

    Example usage:
        compute_gini_by_group(squad_values_df, ['league', 'season'], 'market_value_m')

    Returns a DataFrame with columns: [*group_cols, 'gini_coefficient']
    """
    result = (
        df.groupby(group_cols)[value_col]
        .apply(gini)
        .reset_index()
        .rename(columns={value_col: "gini_coefficient"})
    )
    return result


# ── Formatting helpers ────────────────────────────────────────────────────────

def season_to_year(season_str):
    """
    Converts a season string like "2023-2024" to the start year integer 2023.
    Used for consistent x-axis plotting.
    """
    try:
        return int(str(season_str).split("-")[0])
    except (ValueError, AttributeError):
        return np.nan


def performance_score(result_str):
    """
    Converts a tournament result string to a numeric performance score.

    Score scale:
        7 = Winner
        6 = Runner-up (Final)
        5 = Semi-final
        4 = Quarter-final
        3 = Round of 16
        2 = Group Stage (eliminated)
        1 = Did Not Qualify

    Args:
        result_str (str): e.g. "Winner", "Semi-final", "Did Not Qualify"

    Returns:
        int: Score from 1 to 7.
    """
    mapping = {
        "winner":           7,
        "final":            6,
        "runner-up":        6,
        "semi-final":       5,
        "semi final":       5,
        "quarter-final":    4,
        "quarter final":    4,
        "round of 16":      3,
        "last 16":          3,
        "group stage":      2,
        "group":            2,
        "did not qualify":  1,
        "dnq":              1,
        "did not enter":    1,
    }
    key = str(result_str).strip().lower()
    return mapping.get(key, np.nan)
