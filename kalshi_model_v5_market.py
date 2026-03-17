# Kalshi Temperature Model – Live Market Benchmark V1

import math
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Kalshi Temperature Model", layout="wide")
st.title("Kalshi Temperature Model – Live Market Benchmark V1")

CITIES = {
    "New York": {"lat":40.7812,"lon":-73.9665},
    "Dallas": {"lat":32.8998,"lon":-97.0403},
    "Atlanta": {"lat":33.6407,"lon":-84.4277},
    "Phoenix": {"lat":33.4342,"lon":-112.0116},
    "Boston": {"lat":42.3656,"lon":-71.0096},
    "Washington DC": {"lat":38.8512,"lon":-77.0402}
}

DEFAULT_LADDER = "44 or below | 45-46 | 47-48 | 49-50 | 51-52 | 53 or above"

def normal_cdf(x,mu,sigma):
    return 0.5*(1+math.erf((x-mu)/(sigma*math.sqrt(2))))

def parse_ladder(text):
    parts=[]
    for p in text.split("|"):
        p=p.strip()
        nums=[int(n) for n in ''.join([c if c.isdigit() else ' ' for c in p]).split()]
        if "below" in p:
            parts.append((p,None,nums[0]))
        elif "above" in p:
            parts.append((p,nums[0],None))
        elif len(nums)==2:
            parts.append((p,nums[0],nums[1]))
    return parts

def openmeteo(lat,lon):
    url="https://api.open-meteo.com/v1/forecast"
    params={
        "latitude":lat,
        "longitude":lon,
        "daily":"temperature_2m_max",
        "current":"temperature_2m",
        "temperature_unit":"fahrenheit",
        "timezone":"auto"
    }
    r=requests.get(url,params=params).json()
    current=r["current"]["temperature_2m"]
    high=r["daily"]["temperature_2m_max"][0]
    return current,high

city=st.selectbox("City",list(CITIES.keys()))
ladder_text=st.text_input("Temperature Ladder",DEFAULT_LADDER)

lat=CITIES[city]["lat"]
lon=CITIES[city]["lon"]

current,forecast_high=openmeteo(lat,lon)

st.subheader("Weather")
c1,c2=st.columns(2)
c1.metric("Current Temp",f"{current:.1f}°F")
c2.metric("Forecast High",f"{forecast_high:.1f}°F")

consensus=forecast_high
sigma=2.0

st.subheader("Model Output")
st.metric("Consensus High",f"{consensus:.1f}°F")

ladder=parse_ladder(ladder_text)

rows=[]
for label,lo,hi in ladder:

    if lo is None:
        p=normal_cdf(hi+0.5,consensus,sigma)
    elif hi is None:
        p=1-normal_cdf(lo-0.5,consensus,sigma)
    else:
        p=normal_cdf(hi+0.5,consensus,sigma)-normal_cdf(lo-0.5,consensus,sigma)

    rows.append({
        "Bracket":label,
        "Probability":f"{p*100:.1f}%",
        "Fair Value":f"{int(p*100)}¢"
    })

df=pd.DataFrame(rows).sort_values("Probability",ascending=False)

st.dataframe(df,use_container_width=True)
