import pandas as pd
import random

cities = pd.read_csv(
    "indonesia_cities.csv"
)

rows = []

for idx, row in cities.iterrows():

    city = row["city"]

    flood_score = random.uniform(
        1,
        20
    )

    rows.append({
        "city": city,
        "flood_prone_score": round(
            flood_score,
            2
        )
    })

df = pd.DataFrame(rows)

df.to_csv(
    "flood_history.csv",
    index=False
)

print(df.head())