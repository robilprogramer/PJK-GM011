
# Flood Risk Dataset Indonesia

## Deskripsi Dataset

Dataset ini merupakan dataset prediksi risiko banjir di wilayah Indonesia yang dibangun menggunakan kombinasi data cuaca, geografis, lingkungan, dan histori kebencanaan.

Dataset digunakan untuk:

- Machine Learning
- Prediksi Risiko Banjir
- Early Warning System
- Analisis Bencana
- Dashboard Monitoring Banjir
- Penelitian AI/ML

Dataset mencakup kota dan kabupaten di Indonesia dengan berbagai parameter yang mempengaruhi potensi banjir.

---

# Informasi Dataset

| Informasi     | Nilai                     |
| ------------- | ------------------------- |
| Total Rows    | 18.800                    |
| Total Cities  | 47                        |
| Negara        | Indonesia                 |
| Jenis Dataset | Multiclass Classification |
| Target        | risk_level                |

---

# Struktur Dataset

| Kolom                | Tipe    | Deskripsi             |
| -------------------- | ------- | --------------------- |
| city                 | string  | Nama kota/kabupaten   |
| province             | string  | Nama provinsi         |
| lat                  | float   | Latitude wilayah      |
| lng                  | float   | Longitude wilayah     |
| month                | integer | Bulan pengamatan      |
| season               | string  | Musim/cuaca           |
| rainfall_1h          | float   | Curah hujan 1 jam     |
| rainfall_3h          | float   | Curah hujan 3 jam     |
| rainfall_24h         | float   | Curah hujan 24 jam    |
| humidity             | float   | Kelembapan udara      |
| temperature          | float   | Suhu udara            |
| wind_speed           | float   | Kecepatan angin       |
| elevation_m          | float   | Ketinggian wilayah    |
| distance_to_river_km | float   | Jarak ke sungai       |
| soil_type            | string  | Jenis tanah           |
| soil_type_encoded    | integer | Encoding jenis tanah  |
| flood_prone_score    | float   | Skor kerawanan banjir |
| risk_level           | string  | Label risiko banjir   |

---

# Label Klasifikasi

Dataset menggunakan 4 kelas risiko banjir:

| Label   | Deskripsi            |
| ------- | -------------------- |
| aman    | Risiko rendah        |
| siaga   | Risiko sedang        |
| waspada | Risiko tinggi        |
| awas    | Risiko sangat tinggi |

---

# Distribusi Kelas

| Kelas   | Jumlah | Persentase |
| ------- | ------ | ---------- |
| awas    | 8207   | 43.65%     |
| waspada | 5991   | 31.87%     |
| siaga   | 3370   | 17.93%     |
| aman    | 1232   | 6.55%      |

---

# Sumber Data

Dataset dibangun dari beberapa sumber data publik:

## 1. Data Wilayah Indonesia

- API Wilayah.id
- OpenStreetMap
- Nominatim API

Digunakan untuk:

- kota/kabupaten
- provinsi
- latitude
- longitude

---

## 2. Data Cuaca

- Open-Meteo API
- BMKG

Digunakan untuk:

- rainfall
- humidity
- temperature
- wind_speed

---

## 3. Data Elevasi

- DEMNAS BIG
- SRTM

Digunakan untuk:

- elevation_m

---

## 4. Data Jenis Tanah

- FAO Soil Map

Digunakan untuk:

- soil_type

---

## 5. Data Histori Banjir

- BNPB DIBI

Digunakan untuk:

- flood_prone_score
- risk_level

---

# Logika Penentuan Risiko

Risk level dihitung berdasarkan kombinasi beberapa parameter:

| Faktor             | Bobot    |
| ------------------ | -------- |
| Curah Hujan        | 50%      |
| Kelembapan         | 15%      |
| Jenis Tanah        | 15%      |
| Elevasi            | 10%      |
| Jarak Sungai       | 5%       |
| Flood Prone Factor | Tambahan |

Semakin tinggi curah hujan dan kelembapan serta semakin rendah elevasi wilayah, maka risiko banjir akan semakin tinggi.

---

# Preprocessing Dataset

Tahapan preprocessing yang dilakukan:

1. Data Cleaning
2. Missing Value Handling
3. Soil Type Encoding
4. Feature Engineering
5. Risk Level Labeling
6. Data Normalization

---

# Potensi Penggunaan

Dataset ini dapat digunakan untuk:

- Prediksi Risiko Banjir
- Klasifikasi Machine Learning
- Deep Learning
- Sistem Early Warning
- Dashboard Monitoring
- Analisis Geospasial
- Penelitian AI dan Data Science

---

# Struktur Output Final

```csv
city
province
lat
lng
month
season
rainfall_1h
rainfall_3h
rainfall_24h
humidity
temperature
wind_speed
elevation_m
distance_to_river_km
soil_type
soil_type_encoded
flood_prone_score
risk_level
```
