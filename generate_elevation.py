import pandas as pd
import random

cities = pd.read_csv(
    "indonesia_cities.csv"
)

rows = []

for idx, row in cities.iterrows():

    city = row["city"]

    elevation = random.uniform(
        1,
        1500
    )

    rows.append({
        "city": city,
        "elevation_m": round(elevation, 2)
    })

df = pd.DataFrame(rows)

df.to_csv(
    "elevation_data.csv",
    index=False
)

print(df.head())