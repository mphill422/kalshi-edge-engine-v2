# Kalshi High Temperature Model - V4.5
# New in V4.5:
# - Auto-fetches NWS observed high so far today from obhistory table
# - Uses observed high as hard floor in consensus (can never go below what already happened)
# - Reads both the Temp column AND the 6-hour Max column (catches overnight spikes)
# - Shows "Obs High So Far" metric in Live Weather panel
# - Warning if observed high already busts your ladder range
# - Default city: New York
# - Straight quotes only

import math
import re
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Kalshi High Temp V4.5", layout="wide")
st.title("Kalshi High Temperature Model - V4.5")

SAVE_FILE = Path("saved_ladders.json")
HISTORY_FILE = Path("settlement_history.json")

HEADERS = {
    "User-Agent": "kalshi-temp-model/4.5",
    "Accept": "application/geo+json, application/json, text/html",
}

SERIES = {
    "Phoenix": "KXHIGHPHX", "Las Vegas": "KXHIGHLAS", "Los Angeles": "KXHIGHLAX",
    "Dallas": "KXHIGHDAL", "Austin": "KXHIGHAUS", "Houston": "KXHIGHHOU",
    "Atlanta": "KXHIGHATL", "Miami": "KXHIGHMIA", "New York": "KXHIGHNY",
    "San Antonio": "KXHIGHSAT", "New Orleans": "KXHIGHMSY", "Philadelphia": "KXHIGHPHL",
    "Boston": "KXHIGHBOS", "Denver": "KXHIGHDEN", "Oklahoma City": "KXHIGHOKC",
    "Minneapolis": "KXHIGHMSP", "Washington DC": "KXHIGHDCA",
}

STATIONS = {
    "Phoenix": "CLIPHX", "Las Vegas": "CLILAS", "Los Angeles": "CLILAX",
    "Dallas": "CLIDFW", "Austin": "CLIAUS", "Houston": "CLIHOU",
    "Atlanta": "CLIATL", "Miami": "CLIMIA", "New York": "KNYC",
    "San Antonio": "CLISAT", "New Orleans": "CLIMSY", "Philadelphia": "CLIPHL",
    "Boston": "CLIBOS", "Denver": "CLIDEN", "Oklahoma City": "CLIOKC",
    "Minneapolis": "CLIMSP", "Washington DC": "CLIDCA",
}

# ICAO codes for NWS obs history page
OBHISTORY_STATIONS = {
    "Phoenix": "KPHX", "Las Vegas": "KLAS", "Los Angeles": "KLAX",
    "Dallas": "KDFW", "Austin": "KAUS", "Houston": "KHOU",
    "Atlanta": "KATL", "Miami": "KMIA", "New York": "KNYC",
    "San Antonio": "KSAT", "New Orleans": "KMSY", "Philadelphia": "KPHL",
    "Boston": "KBOS", "Denver": "KDEN", "Oklahoma City": "KOKC",
    "Minneapolis": "KMSP", "Washington DC": "KDCA",
}

SETTLEMENT_LOCATION = {
    "Phoenix": "Phoenix Sky Harbor Airport",
    "Las Vegas": "Las Vegas Harry Reid Airport",
    "Los Angeles": "LA International Airport",
    "Dallas": "Dallas/Fort Worth Airport",
    "Austin": "Austin-Bergstrom Airport",
    "Houston": "Houston Hobby Airport",
    "Atlanta": "Atlanta Hartsfield Airport",
    "Miami": "Miami International Airport",
    "New York": "Central Park, Manhattan",
    "San Antonio": "San Antonio International Airport",
    "New Orleans": "New Orleans Armstrong Airport",
    "Philadelphia": "Philadelphia International Airport",
    "Boston": "Boston Logan Airport",
    "Denver": "Denver International Airport",
    "Oklahoma City": "Oklahoma City Will Rogers Airport",
    "Minneapolis": "Minneapolis-St. Paul Airport",
    "Washington DC": "Reagan National Airport",
}

CITIES = {
    "Phoenix": {"lat": 33.4342, "lon": -112.0116},
    "Las Vegas": {"lat": 36.0840, "lon": -115.1537},
    "Los Angeles": {"lat": 33.9416, "lon": -118.4085},
    "Dallas": {"lat": 32.8998, "lon": -97.0403},
    "Austin": {"lat": 30.1945, "lon": -97.6699},
    "Houston": {"lat": 29.9902, "lon": -95.3368},
    "Atlanta": {"lat": 33.6407, "lon": -84.4277},
    "Miami": {"lat": 25.7959, "lon": -80.2870},
    "New York": {"lat": 40.7812, "lon": -73.9665},
    "San Antonio": {"lat": 29.5337, "lon": -98.4698},
    "New Orleans": {"lat": 29.9934, "lon": -90.2580},
    "Philadelphia": {"lat": 39.8744, "lon": -75.2424},
    "Boston": {"lat": 42.3656, "lon": -71.0096},
    "Denver": {"lat": 39.8561, "lon": -104.6737},
    "Oklahoma City": {"lat": 35.3931, "lon": -97.6007},
    "Minneapolis": {"lat": 44.8848, "lon": -93.2223},
    "Washington DC": {"lat": 38.8512, "lon": -77.0402},
}

DEFAULT_LADDERS = {
    "Phoenix": "74 or below | 75-76 | 77-78 | 79-80 | 81-82 | 83 or above",
    "Las Vegas": "74 or below | 75-76 | 77-78 | 79-80 | 81-82 | 83 or above",
    "Los Angeles": "66 or below | 67-68 | 69-70 | 71-72 | 73-74 | 75 or above",
    "Dallas": "78 or below | 79-80 | 81-82 | 83-84 | 85-86 | 87 or above",
    "Austin": "78 or below | 79-80 | 81-82 | 83-84 | 85-86 | 87 or above",
    "Houston": "79 or below | 80-81 | 82-83 | 84-85 | 86-87 | 88 or above",
    "Atlanta": "74 or below | 75-76 | 77-78 | 79-80 | 81-82 | 83 or above",
    "Miami": "76 or below | 77-78 | 79-80 | 81-82 | 83-84 | 85 or above",
    "New York": "46 or below | 47-48 | 49-50 | 51-52 | 53-54 | 55 or above",
    "San Antonio": "78 or below | 79-80 | 81-82 | 83-84 | 85-86 | 87 or above",
    "New Orleans": "80 or below | 81-82 | 83-84 | 85-86 | 87-88 | 89 or above",
    "Philadelphia": "73 or below | 74-75 | 76-77 | 78-79 | 80-81 | 82 or above",
    "Boston": "48 or below | 49-50 | 51-52 | 53-54 | 55-56 | 57 or above",
    "Denver": "65 or below | 66-67 | 68-69 | 70-71 | 72-73 | 74 or above",
    "Oklahoma City": "75 or below | 76-77 | 78-79 | 80-81 | 82-83 | 84 or above",
    "Minneapolis": "65 or below | 66-67 | 68-69 | 70-71 | 72-73 | 74 or above",
    "Washington DC": "76 or below | 77-78 | 79-80 | 81-82 | 83-84 | 85 or above",
}

BASE_SIGMA = {
    "New York": 1.5, "Philadelphia": 1.5, "Washington DC": 1.6, "Boston": 1.6,
    "Los Angeles": 1.4, "Denver": 1.6, "Miami": 1.7, "Minneapolis": 1.7,
    "New Orleans": 1.8, "Phoenix": 1.9, "Las Vegas": 1.9, "Atlanta": 2.0,
    "Dallas": 2.0, "Austin": 2.0, "Houston": 2.0, "San Antonio": 2.0,
    "Oklahoma City": 2.1,
}

DESERT_CITIES = {"Phoenix", "Las Vegas"}


# ── NWS Observed High Fetcher ─────────────────────────────────────────────────

def fetch_obs_high_today(icao):
    """
    Scrapes forecast.weather.gov/data/obhistory/KBOS.html
    Returns the highest temperature recorded at the station today (float or None).

    The table has these columns (0-indexed):
      0: Day   1: Time   2: Wind Dir   3: Wind Speed   4: Gust
      5: Vis   6: Weather   7: Sky   8: Temp(F)   9: Dewpoint
      10: 6hr Max   11: 6hr Min   12: Precip   13: Pressure   14: Altimeter

    We read column 8 (Temp) AND column 10 (6hr Max) for today's day number.
    The 6hr Max is the column that caught the 62 degree Boston spike - do not skip it.
    """
    url = "https://forecast.weather.gov/data/obhistory/" + icao + ".html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
    except Exception:
        return None, url

    soup = BeautifulSoup(r.text, "html.parser")

    # The obs table has class "observations" - fall back to largest table
    table = soup.find("table", {"class": "observations"})
    if not table:
        tables = soup.find_all("table")
        table = max(tables, key=lambda t: len(t.find_all("tr")), default=None) if tables else None
    if not table:
        return None, url

    today_day = str(datetime.now().day)
    highs = []

    for row in table.find_all("tr"):
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols or len(cols) < 9:
            continue

        # Column 0 is day number - only process today's rows
        if cols[0] != today_day:
            continue

        # Column 8: actual observed temp
        try:
            t = float(cols[8])
            if 0 < t < 130:
                highs.append(t)
        except (ValueError, IndexError):
            pass

        # Column 10: 6-hour maximum (may be empty for most rows)
        if len(cols) > 10:
            try:
                t6 = float(cols[10])
                if 0 < t6 < 130:
                    highs.append(t6)
            except (ValueError, IndexError):
                pass

    if highs:
        return round(max(highs), 1), url
    return None, url


# ── Math helpers ──────────────────────────────────────────────────────────────

def normal_cdf(x, mu, sigma):
    return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))


def choose_sigma(city, obs_high=None, forecast=None):
    s = BASE_SIGMA.get(city, 1.8)
    hour = datetime.now().hour
    s *= 1.00 if hour < 11 else 0.92 if hour < 14 else 0.86 if hour < 16 else 0.80
    if city in DESERT_CITIES:
        s *= 0.90
    # If observed high is close to forecast, tighten sigma further
    if obs_high is not None and forecast is not None:
        gap = abs(forecast - obs_high)
        if gap < 2:
            s *= 0.75
        elif gap < 4:
            s *= 0.85
    return max(1.10, min(2.40, s))


def late_day_floor(fc, obs, hour):
    gap = max(0.0, fc - obs)
    frac = 0.45 if hour < 12 else 0.62 if hour < 14 else 0.78 if hour < 16 else 0.90
    return obs + frac * gap


def compute_consensus(fc, cur, noaa, hour, obs_high=None):
    if noaa is not None:
        base = fc * 0.55 + cur * 0.20 + noaa * 0.25
    else:
        base = fc * 0.70 + cur * 0.30
    if abs(base - fc) > 2:
        base = fc - 1 if base < fc else fc + 1
    obs = noaa if noaa is not None else cur
    floor = late_day_floor(fc, obs, hour)
    consensus = max(base, floor)
    if consensus > fc + 0.6:
        consensus = fc + 0.6

    # Hard floor: consensus can never be below what already happened today
    if obs_high is not None and obs_high > consensus:
        consensus = obs_high

    return consensus


def normalize_label(label):
    label = label.strip()
    label = re.sub(r'(\d+)\s+to\s+(\d+)', lambda m: m.group(1) + "-" + m.group(2), label, flags=re.I)
    label = re.sub(r'(\d+)\s*-\s*(\d+)', lambda m: m.group(1) + "-" + m.group(2), label)
    label = re.sub(r'\s+or\s+below', ' or below', label, flags=re.I)
    label = re.sub(r'\s+or\s+above', ' or above', label, flags=re.I)
    label = label.replace("\u00b0", "").replace("deg", "")
    return label.strip()


def parse_ladder(text):
    out = []
    for p in text.split("|"):
        p = normalize_label(p)
        nums = [int(x) for x in re.findall(r"\d+", p)]
        if not nums:
            continue
        low = p.lower()
        if "below" in low:
            out.append((p, None, nums[0]))
        elif "above" in low:
            out.append((p, nums[0], None))
        elif len(nums) >= 2:
            out.append((p, nums[0], nums[1]))
    return out


def bracket_probs(mu, ladder_text, city, obs_high=None, forecast=None):
    sigma = choose_sigma(city, obs_high=obs_high, forecast=forecast)
    rows = []
    for label, lo, hi in parse_ladder(ladder_text):
        # If obs_high already rules out a bracket, set probability to 0
        if obs_high is not None:
            if hi is not None and obs_high > hi + 0.4:
                rows.append((label, 0.0))
                continue

        if lo is None:
            p = normal_cdf(hi + 0.5, mu, sigma)
        elif hi is None:
            p = 1 - normal_cdf(lo - 0.5, mu, sigma)
        else:
            p = normal_cdf(hi + 0.5, mu, sigma) - normal_cdf(lo - 0.5, mu, sigma)
        rows.append((label, max(0.0, min(1.0, p))))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows, sigma


def two_degree_call(mu, ladder_text, obs_high=None):
    best_label, best_dist = None, float("inf")
    for label, lo, hi in parse_ladder(ladder_text):
        if lo is None or hi is None:
            continue
        # Skip brackets already ruled out by observed high
        if obs_high is not None and obs_high > hi + 0.4:
            continue
        center = (lo + hi) / 2
        dist = abs(center - mu)
        if dist < best_dist:
            best_dist = dist
            best_label = label
    return best_label


def ladder_to_boxes(text):
    parts = [normalize_label(p) for p in text.split("|")]
    while len(parts) < 6:
        parts.append("")
    return parts[:6]


def boxes_to_ladder(parts):
    cleaned = []
    for i, p in enumerate(parts):
        t = normalize_label(p)
        if not t:
            continue
        nums = re.findall(r"\d+", t)
        low = t.lower()
        if "below" in low or "above" in low or "-" in t:
            cleaned.append(t)
        elif len(nums) == 1:
            n = int(nums[0])
            if i == 0:
                cleaned.append(str(n) + " or below")
            elif i == 5:
                cleaned.append(str(n) + " or above")
            else:
                cleaned.append(str(n))
        else:
            cleaned.append(t)
    return " | ".join(cleaned)


def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def safe_get(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def c_to_f(c):
    return c * 9 / 5 + 32


def fetch_open_meteo(lat, lon):
    data = safe_get("https://api.open-meteo.com/v1/forecast", {
        "latitude": lat, "longitude": lon,
        "daily": "temperature_2m_max",
        "current": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "timezone": "auto",
        "forecast_days": 2,
    })
    if not data:
        return None, None
    today = datetime.now().strftime("%Y-%m-%d")
    times = data.get("daily", {}).get("time", [])
    idx = next((i for i, t in enumerate(times) if t.startswith(today)), 0)
    fc = data.get("daily", {}).get("temperature_2m_max", [None])[idx]
    cur = data.get("current", {}).get("temperature_2m")
    return (float(fc) if fc is not None else None,
            float(cur) if cur is not None else None)


def fetch_noaa(lat, lon, station_id):
    if station_id:
        obs = safe_get("https://api.weather.gov/stations/" + station_id + "/observations/latest")
        if obs:
            temp_c = obs.get("properties", {}).get("temperature", {}).get("value")
            if temp_c is not None:
                return station_id, float(c_to_f(temp_c))
    points = safe_get("https://api.weather.gov/points/" + str(lat) + "," + str(lon))
    if not points:
        return station_id, None
    stations_url = points.get("properties", {}).get("observationStations")
    if not stations_url:
        return station_id, None
    stations = safe_get(stations_url)
    if not stations or not stations.get("observationStations"):
        return station_id, None
    first = stations["observationStations"][0]
    sid = first.rstrip("/").split("/")[-1]
    obs = safe_get(first + "/observations/latest")
    if not obs:
        return sid, None
    temp_c = obs.get("properties", {}).get("temperature", {}).get("value")
    if temp_c is None:
        return sid, None
    return sid, float(c_to_f(temp_c))


def parse_market_label(m):
    s = (m.get("subtitle") or "").replace("\u00b0", "").replace("deg", "").strip()
    if s:
        s = normalize_label(s)
        below = re.match(r"^(\d+)\s*or\s*below$", s, re.I)
        above = re.match(r"^(\d+)\s*or\s*above$", s, re.I)
        rng = re.match(r"^(\d+)-(\d+)$", s)
        if below:
            return below.group(1) + " or below", int(below.group(1)) - 10000
        if above:
            return above.group(1) + " or above", int(above.group(1)) + 10000
        if rng:
            return rng.group(1) + "-" + rng.group(2), int(rng.group(1))

    title = (m.get("title") or "").replace("\u00b0", "").replace("**", "").replace("deg", "")
    if title:
        ma = re.search(r'be\s*[>=]+\s*(\d+)', title, re.I)
        if ma:
            n = int(ma.group(1))
            return str(n) + " or above", n + 10000
        mb = re.search(r'be\s*[<=]+\s*(\d+)', title, re.I)
        if mb:
            n = int(mb.group(1))
            return str(n) + " or below", n - 10000
        mr = re.search(r'be\s*(\d+)\s*(?:to|-)\s*(\d+)', title, re.I)
        if mr:
            lo, hi = int(mr.group(1)), int(mr.group(2))
            return str(lo) + "-" + str(hi), lo
        nums = re.findall(r'\d+', title)
        if len(nums) >= 2:
            lo, hi = int(nums[-2]), int(nums[-1])
            if 0 < hi - lo <= 5:
                return str(lo) + "-" + str(hi), lo

    for field in ["short_title", "market_title", "name"]:
        val = (m.get(field) or "").replace("\u00b0", "").strip()
        if val:
            val = normalize_label(val)
            rng = re.match(r"^(\d+)-(\d+)$", val)
            below = re.match(r"^(\d+)\s*or\s*below$", val, re.I)
            above = re.match(r"^(\d+)\s*or\s*above$", val, re.I)
            if rng:
                return rng.group(1) + "-" + rng.group(2), int(rng.group(1))
            if below:
                return below.group(1) + " or below", int(below.group(1)) - 10000
            if above:
                return above.group(1) + " or above", int(above.group(1)) + 10000

    return None, None


def get_price_cents(m):
    yes_ask = None
    no_ask = None
    for field in ["yes_ask_dollars", "yes_bid_dollars"]:
        val = m.get(field)
        if val:
            try:
                yes_ask = round(float(val) * 100)
                break
            except Exception:
                pass
    for field in ["no_ask_dollars", "no_bid_dollars"]:
        val = m.get(field)
        if val:
            try:
                no_ask = round(float(val) * 100)
                break
            except Exception:
                pass
    if yes_ask is None:
        raw = m.get("yes_ask") or m.get("yes_bid")
        if raw is not None:
            try:
                yes_ask = int(raw)
            except Exception:
                pass
    if no_ask is None:
        raw = m.get("no_ask") or m.get("no_bid")
        if raw is not None:
            try:
                no_ask = int(raw)
            except Exception:
                pass
    return yes_ask, no_ask


def fetch_kalshi_brackets(series):
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"series_ticker": series, "status": "open", "limit": 30}
    data = safe_get(url, params)
    if not data or not data.get("markets"):
        return None
    all_markets = data["markets"]

    today_upper = datetime.now().strftime("%y%b%d").upper()
    today_upper2 = datetime.now().strftime("%d%b%y").upper()
    today_date = datetime.now().strftime("%Y-%m-%d")

    markets = [m for m in all_markets if
               today_upper in (m.get("ticker") or "").upper() or
               today_upper2 in (m.get("ticker") or "").upper()]
    if not markets:
        markets = [m for m in all_markets if (m.get("close_time") or "").startswith(today_date)]
    if not markets:
        markets = all_markets

    parsed = []
    for m in markets:
        label, key = parse_market_label(m)
        if label is None:
            continue
        yes_ask, no_ask = get_price_cents(m)
        parsed.append((key, label, yes_ask, no_ask))

    if len(parsed) < 2:
        return None

    parsed.sort(key=lambda x: x[0])
    return [(label, yes_ask, no_ask) for _, label, yes_ask, no_ask in parsed]


# ── App ───────────────────────────────────────────────────────────────────────

saved_ladders = load_json(SAVE_FILE)
history = load_json(HISTORY_FILE)
if not isinstance(history, list):
    history = []

city = st.selectbox("City", list(CITIES.keys()), index=list(CITIES.keys()).index("New York"))
lat = CITIES[city]["lat"]
lon = CITIES[city]["lon"]
station = STATIONS[city]
series = SERIES[city]
obs_icao = OBHISTORY_STATIONS.get(city, "KNYC")
obs_url = "https://forecast.weather.gov/data/obhistory/" + obs_icao + ".html"

st.caption("Settlement: " + STATIONS[city] + " - " + SETTLEMENT_LOCATION[city] + " - Series: " + series)

# ── Kalshi Ladder ─────────────────────────────────────────────────────────────
st.subheader("Kalshi Ladder")

fetch_brackets = st.button("Fetch Live Brackets from Kalshi")

kalshi_markets = None
raw_debug = None
if fetch_brackets:
    with st.spinner("Fetching from Kalshi..."):
        kalshi_markets = fetch_kalshi_brackets(series)
        raw_debug = safe_get("https://api.elections.kalshi.com/trade-api/v2/markets",
                             {"series_ticker": series, "status": "open", "limit": 30})

    if kalshi_markets:
        labels = [normalize_label(m[0]) for m in kalshi_markets]
        while len(labels) < 6:
            labels.append("")
        saved_ladders[city] = " | ".join(labels[:6])
        save_json(SAVE_FILE, saved_ladders)
        st.success("Loaded " + str(len(kalshi_markets)) + " brackets from Kalshi")
        for m in kalshi_markets:
            yes_str = str(m[1]) + "c" if m[1] is not None else "no price"
            no_str = str(m[2]) + "c" if m[2] is not None else "no price"
            st.caption("  " + m[0] + " | YES: " + yes_str + " | NO: " + no_str)
    else:
        st.warning("Could not fetch from Kalshi API. Edit brackets manually below.")

    with st.expander("Debug - Raw Kalshi API Response", expanded=not bool(kalshi_markets)):
        if raw_debug and raw_debug.get("markets"):
            today_upper = datetime.now().strftime("%y%b%d").upper()
            st.caption("Looking for ticker suffix: " + today_upper)
            st.caption("Total markets returned: " + str(len(raw_debug["markets"])))
            for m in raw_debug["markets"]:
                ticker = m.get("ticker", "")
                subtitle = m.get("subtitle", "")
                title = m.get("title", "")
                close_time = (m.get("close_time") or "")[:10]
                yes_bid = m.get("yes_bid_dollars") or m.get("yes_ask_dollars") or m.get("yes_bid") or "none"
                st.caption(
                    "TICKER: " + ticker +
                    " | SUBTITLE: " + (subtitle or "EMPTY") +
                    " | TITLE: " + (title[:40] if title else "EMPTY") +
                    " | CLOSE: " + close_time +
                    " | YES: " + str(yes_bid)
                )
        else:
            st.error("No data returned from Kalshi API at all")

if city not in saved_ladders:
    saved_ladders[city] = DEFAULT_LADDERS.get(city, "")

box_values = ladder_to_boxes(saved_ladders[city])

with st.expander("Edit Brackets", expanded=False):
    cols = st.columns(6)
    new_boxes = []
    for i, col in enumerate(cols):
        with col:
            new_boxes.append(st.text_input("Box " + str(i + 1), value=box_values[i], key=city + "_b" + str(i)))
    if st.button("Save Ladder"):
        ladder_text = boxes_to_ladder(new_boxes)
        saved_ladders[city] = ladder_text
        save_json(SAVE_FILE, saved_ladders)
        st.success("Saved")
        st.rerun()

ladder_text = saved_ladders[city]
st.caption("Current ladder: " + ladder_text)

# ── Live Weather ──────────────────────────────────────────────────────────────
st.subheader("Live Weather")

with st.spinner("Fetching weather and observed high..."):
    forecast_auto, current_auto = fetch_open_meteo(lat, lon)
    noaa_station, noaa_obs = fetch_noaa(lat, lon, station)
    obs_high_today, obs_high_url = fetch_obs_high_today(obs_icao)

hour = datetime.now().hour

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Forecast High", str(round(forecast_auto, 1)) + " F" if forecast_auto else "unavailable")
with col2:
    st.metric("Current Temp", str(round(current_auto, 1)) + " F" if current_auto else "unavailable")
with col3:
    if noaa_obs is not None:
        st.metric("NOAA Obs", str(round(noaa_obs, 1)) + " F")
        st.caption("Station: " + noaa_station)
    else:
        st.metric("NOAA Obs", "Unavailable")
with col4:
    if obs_high_today is not None:
        st.metric("Obs High So Far", str(obs_high_today) + " F", delta="floor active")
        st.caption("[NWS table](" + obs_url + ")")
    else:
        st.metric("Obs High So Far", "Unavailable")
        st.caption("[NWS table](" + obs_url + ")")

# Warn if observed high already busts bottom brackets
if obs_high_today is not None:
    for label, lo, hi in parse_ladder(ladder_text):
        if hi is not None and obs_high_today > hi + 0.4:
            st.warning("BUST: " + label + " is already eliminated - observed high " + str(obs_high_today) + "F exceeds " + str(hi) + "F")

# Manual override
with st.expander("Override weather inputs (use when auto values look wrong)", expanded=False):
    ov1, ov2, ov3, ov4 = st.columns(4)
    with ov1:
        override_fc = st.number_input("Forecast High F", min_value=0.0, max_value=130.0, value=0.0, step=0.5, key="ov_fc")
    with ov2:
        override_cur = st.number_input("Current Temp F", min_value=0.0, max_value=130.0, value=0.0, step=0.5, key="ov_cur")
    with ov3:
        override_noaa = st.number_input("NOAA Obs F", min_value=0.0, max_value=130.0, value=0.0, step=0.5, key="ov_noaa")
    with ov4:
        override_obs_high = st.number_input("Obs High Override F", min_value=0.0, max_value=130.0, value=0.0, step=0.5, key="ov_obs")
    if override_fc > 0 or override_cur > 0 or override_obs_high > 0:
        st.info("Using manual overrides - set back to 0.0 to use auto values")

forecast = override_fc if override_fc > 0 else forecast_auto
current = override_cur if override_cur > 0 else current_auto
noaa_final = override_noaa if override_noaa > 0 else noaa_obs
obs_high_final = override_obs_high if override_obs_high > 0 else obs_high_today

# ── Model Output ──────────────────────────────────────────────────────────────
if forecast is not None and current is not None:
    consensus = compute_consensus(forecast, current, noaa_final, hour, obs_high=obs_high_final)
    rows, sigma = bracket_probs(consensus, ladder_text, city, obs_high=obs_high_final, forecast=forecast)
    call = two_degree_call(consensus, ladder_text, obs_high=obs_high_final)

    st.subheader("Model Output")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Consensus High", str(round(consensus, 1)) + " F")
    with c2:
        st.metric("2 Degree Call", call or "none")
    with c3:
        st.metric("Sigma", str(round(sigma, 2)) + " F")
    with c4:
        if obs_high_final is not None:
            floor_active = obs_high_final >= consensus - 0.1
            st.metric("Obs Floor", str(obs_high_final) + " F",
                      delta="controlling" if floor_active else "not binding")

    st.caption("Time: " + str(hour) + ":00 local - Late-day floor active")

    import pandas as pd
    df_rows = []
    for label, prob in rows:
        fair = round(prob * 100)
        yes_ask = no_ask = None
        if kalshi_markets:
            norm_label = normalize_label(label)
            match = next((m for m in kalshi_markets if normalize_label(m[0]) == norm_label), None)
            if match:
                yes_ask = match[1]
                no_ask = match[2]
        edge = (fair - yes_ask) if yes_ask is not None else None

        # Mark busted brackets
        busted = False
        if obs_high_final is not None:
            for lbl, lo, hi in parse_ladder(ladder_text):
                if normalize_label(lbl) == normalize_label(label):
                    if hi is not None and obs_high_final > hi + 0.4:
                        busted = True

        df_rows.append({
            "Bracket": label + (" BUSTED" if busted else ""),
            "Model %": str(round(prob * 100, 1)) + "%",
            "Fair": str(fair) + "c",
            "YES ask": str(yes_ask) + "c" if yes_ask is not None else "none",
            "NO ask": str(no_ask) + "c" if no_ask is not None else "none",
            "Edge": ("+" + str(edge) + "c") if edge and edge > 0 else (str(edge) + "c" if edge is not None else "none"),
        })

    df = pd.DataFrame(df_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    parsed = parse_ladder(ladder_text)
    top_b = next((b for b in parsed if b[2] is None), None)
    bot_b = next((b for b in parsed if b[1] is None), None)
    if (top_b and consensus > top_b[1] + 5) or (bot_b and consensus < bot_b[2] - 5):
        st.warning("Ladder does not cover consensus of " + str(round(consensus, 1)) + " F - update brackets.")

else:
    st.error("Weather data unavailable.")

# ── Settlement Logger ─────────────────────────────────────────────────────────
st.subheader("Log Actual High (after settlement)")
with st.form("log_form"):
    actual = st.number_input("Actual NWS High F", min_value=0.0, max_value=130.0, step=0.1)
    submitted = st.form_submit_button("Log Settlement")
    if submitted and forecast is not None:
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "city": city,
            "actual": actual,
            "forecast": round(forecast, 1),
            "consensus": round(consensus, 1),
            "obs_high": obs_high_final,
            "error": round(actual - consensus, 1),
        }
        history.append(entry)
        save_json(HISTORY_FILE, history[-300:])
        st.success("Logged - actual=" + str(actual) + "F  consensus=" + str(round(consensus, 1)) + "F  error=" + str(entry["error"]) + "F")

# ── History ───────────────────────────────────────────────────────────────────
if history:
    st.subheader("Settlement History")
    import pandas as pd
    df_h = pd.DataFrame(history[-50:][::-1])
    wd = [h for h in history if h.get("consensus") and h.get("actual")]
    if wd:
        mae = sum(abs(h["actual"] - h["consensus"]) for h in wd) / len(wd)
        w1 = sum(1 for h in wd if abs(h["actual"] - h["consensus"]) <= 1) / len(wd)
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            st.metric("Records", len(history))
        with hc2:
            st.metric("Model MAE", str(round(mae, 2)) + " F")
        with hc3:
            st.metric("Within 1 degree", str(round(w1 * 100, 0)) + "%")
    st.dataframe(df_h, use_container_width=True, hide_index=True)
