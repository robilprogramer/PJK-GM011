import pandas as pd
import requests
import numpy as np
import time

cities = pd.read_csv(
    "indonesia_cities.csv"
)

weather_rows = []

for idx, row in cities.iterrows():

    city = row["city"]
    province = row["province"]
    lat = row["lat"]
    lng = row["lng"]

    if pd.isna(lat) or pd.isna(lng):
        continue

    print(f"Processing Weather: {city}")

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}"
        f"&longitude={lng}"
        f"&hourly="
        f"temperature_2m,"
        f"relative_humidity_2m,"
        f"precipitation,"
        f"wind_speed_10m"
        f"&forecast_days=1"
    )

    try:

        res = requests.get(weather_url)

        data = res.json()

        temp = np.mean(
            data["hourly"]["temperature_2m"]
        )

        humidity = np.mean(
            data["hourly"]["relative_humidity_2m"]
        )

        rainfall_24h = np.sum(
            data["hourly"]["precipitation"]
        )

        wind_speed = np.mean(
            data["hourly"]["wind_speed_10m"]
        )

        rainfall_1h = rainfall_24h * 0.1
        rainfall_3h = rainfall_24h * 0.3

        weather_rows.append({
            "city": city,
            "province": province,
            "lat": lat,
            "lng": lng,
            "rainfall_1h": rainfall_1h,
            "rainfall_3h": rainfall_3h,
            "rainfall_24h": rainfall_24h,
            "humidity": humidity,
            "temperature": temp,
            "wind_speed": wind_speed
        })

    except Exception as e:

        print("ERROR:", city, e)

    time.sleep(0.5)

df = pd.DataFrame(weather_rows)

df.to_csv(
    "weather_data.csv",
    index=False
)

print(df.head())