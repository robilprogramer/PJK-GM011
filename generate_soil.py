import pandas as pd
import random
from sklearn.preprocessing import LabelEncoder

cities = pd.read_csv(
    "indonesia_cities.csv"
)

soil_types = [
    "alluvial",
    "clay",
    "sandy",
    "peat",
    "loam"
]

rows = []

for idx, row in cities.iterrows():

    city = row["city"]

    soil_type = random.choice(
        soil_types
    )

    rows.append({
        "city": city,
        "soil_type": soil_type
    })

df = pd.DataFrame(rows)

encoder = LabelEncoder()

df["soil_type_encoded"] = encoder.fit_transform(
    df["soil_type"]
)

df.to_csv(
    "soil_data.csv",
    index=False
)

print(df.head())