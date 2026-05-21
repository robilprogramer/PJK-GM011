import requests
import pandas as pd
import time

BASE_URL = "https://wilayah.id/api"

all_cities = []

# ============================================
# AMBIL PROVINSI
# ============================================

province_res = requests.get(
    f"{BASE_URL}/provinces.json"
)

province_json = province_res.json()

provinces = province_json["data"]

# ============================================
# LOOP PROVINSI
# ============================================

for prov in provinces:

    province_code = prov["code"]
    province_name = prov["name"]

    print(f"Processing Province: {province_name}")

    city_res = requests.get(
        f"{BASE_URL}/regencies/{province_code}.json"
    )

    city_json = city_res.json()

    cities = city_json["data"]

    # ============================================
    # LOOP KOTA
    # ============================================

    for city in cities:

        city_name = city["name"]

        print(f"  -> {city_name}")

        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city_name}"
            f"&count=1"
            f"&language=id"
            f"&format=json"
        )

        try:

            geo_res = requests.get(geo_url)

            geo_json = geo_res.json()

            if "results" in geo_json:

                lat = geo_json["results"][0]["latitude"]
                lng = geo_json["results"][0]["longitude"]

            else:

                lat = None
                lng = None

        except:

            lat = None
            lng = None

        row = {
            "city": city_name,
            "province": province_name,
            "lat": lat,
            "lng": lng
        }

        all_cities.append(row)

        time.sleep(0.2)

# ============================================
# SAVE
# ============================================

df = pd.DataFrame(all_cities)

df.to_csv(
    "indonesia_cities.csv",
    index=False
)

print(df.head())
print("Total cities:", len(df))