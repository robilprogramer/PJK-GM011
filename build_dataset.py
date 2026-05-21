import pandas as pd
import random

cities = pd.read_csv(
    "indonesia_cities.csv"
)

weather = pd.read_csv(
    "weather_data.csv"
)

elevation = pd.read_csv(
    "elevation_data.csv"
)

soil = pd.read_csv(
    "soil_data.csv"
)

flood = pd.read_csv(
    "flood_history.csv"
)

# ========================================
# MERGE
# ========================================

df = weather.merge(
    elevation,
    on="city"
)

df = df.merge(
    soil,
    on="city"
)

df = df.merge(
    flood,
    on="city"
)

# ========================================
# MONTH & SEASON
# ========================================

months = []
seasons = []

for i in range(len(df)):

    month = random.randint(
        1,
        12
    )

    months.append(month)

    if month in [12, 1, 2, 10, 11]:
        season = "rainy"

    elif month in [3, 9]:
        season = "transition"

    else:
        season = "dry"

    seasons.append(season)

df["month"] = months
df["season"] = seasons

# ========================================
# DISTANCE TO RIVER
# ========================================

df["distance_to_river_km"] = [
    random.uniform(0.1, 20)
    for _ in range(len(df))
]

# ========================================
# RISK LEVEL
# ========================================

def generate_risk(score):

    if score >= 15:
        return "awas"

    elif score >= 10:
        return "waspada"

    elif score >= 5:
        return "siaga"

    else:
        return "aman"

df["risk_level"] = df[
    "flood_prone_score"
].apply(generate_risk)

# ========================================
# REORDER
# ========================================

df = df[
    [
        "city",
        "province",
        "lat",
        "lng",
        "month",
        "season",
        "rainfall_1h",
        "rainfall_3h",
        "rainfall_24h",
        "humidity",
        "temperature",
        "wind_speed",
        "elevation_m",
        "distance_to_river_km",
        "soil_type",
        "soil_type_encoded",
        "flood_prone_score",
        "risk_level"
    ]
]

# ========================================
# SAVE
# ========================================

df.to_csv(
    "flood_risk_dataset.csv",
    index=False
)

print(df.head())
print("Total rows:", len(df))