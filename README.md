# SiagaAI — ML Backend

> Custom Machine Learning Model prediksi risiko banjir Indonesia.

---

## 📋 Daftar Isi

- [Tentang](#tentang)
- [Struktur Project](#struktur-project)
- [Quick Start](#quick-start)
- [Pipeline ML](#pipeline-ml)
- [API Endpoints](#api-endpoints)
- [Dataset](#dataset)
- [Model Performance](#model-performance)
- [Deployment](#deployment)

---

## Tentang

SiagaAI ML Backend menyediakan REST API untuk prediksi risiko banjir menggunakan
**Custom Random Forest Classifier** yang dilatih dari data historis 47 kota Indonesia.

### Mengapa Custom ML, bukan hanya LLM?

| Aspek           | LLM saja              | Custom ML + LLM               |
| --------------- | --------------------- | ----------------------------- |
| Reproducibility | ✗ Non-deterministik  | ✓ Hasil konsisten            |
| Explainability  | ✗ Black box          | ✓ Feature importance         |
| Latensi         | ~1-3 detik (API call) | ✓ < 100ms (local)            |
| Biaya           | Berbayar per token    | ✓ Gratis setelah training    |
| Data Indonesia  | ✗ Bias data global   | ✓ 47 kota spesifik Indonesia |
| Offline mode    | ✗ Butuh internet     | ✓ Jalan tanpa internet       |

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```


### 2. Jalankan API server

```bash
uvicorn main:app --reload --port 8000
```

Buka: **http://localhost:8000/docs**

### 3. Test prediksi

```bash
# Health check
curl http://localhost:8000/api/ml/health

# Prediksi banjir Jakarta
curl -X POST http://localhost:8000/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "rainfall_1h": 65, "rainfall_3h": 180, "rainfall_24h": 350,
    "humidity": 95, "temperature": 26, "wind_speed": 8,
    "city_name": "Jakarta Utara", "month": 1
  }'
```

### Dataset

- **47 kota** rawan banjir di Indonesia
- **18.800 baris** dengan distribusi musiman yang realistis
- Sumber data: pola curah hujan BMKG, data banjir BNPB DIBI, elevasi BIG, jenis tanah FAO
- Label 4 kelas: `aman`, `waspada`, `siaga`, `awas`

### Preprocessing

- Capping outliers rainfall (persentil 99.5%)
- **7 engineered features**: `rain_intensity`, `rain_persistence`, `saturation_index`,
  `drainage_score`, `is_rainy_season`, `heat_humidity`, `city_risk`
- Split: 70% train / 15% val / 15% test (stratified)
- Oversampling kelas minoritas (resample sklearn) — **tidak ada data leakage**
- StandardScaler fitted hanya pada training set

### Training

- Algoritma: **Random Forest Classifier**
- Grid search: 6 konfigurasi hyperparameter
- Best config: `n_estimators=300`, `max_depth=20`, `min_samples_split=3`, `class_weight=balanced`
- Cross-validation 5-fold untuk validasi robustness

### Features (17 total)

| #  | Feature                  | Keterangan                               |
| -- | ------------------------ | ---------------------------------------- |
| 1  | `rainfall_1h`          | Curah hujan 1 jam (mm)                   |
| 2  | `rainfall_3h`          | Curah hujan 3 jam (mm)                   |
| 3  | `rainfall_24h`         | Curah hujan 24 jam (mm)                  |
| 4  | `humidity`             | Kelembaban (%)                           |
| 5  | `temperature`          | Suhu (°C)                               |
| 6  | `wind_speed`           | Kecepatan angin (m/s)                    |
| 7  | `month`                | Bulan 1-12                               |
| 8  | `is_rainy_season`      | Musim hujan flag (1/0)                   |
| 9  | `elevation_m`          | Elevasi kota (meter)                     |
| 10 | `distance_to_river_km` | Jarak ke sungai                          |
| 11 | `soil_type_encoded`    | Jenis tanah 0-4                          |
| 12 | `rain_intensity`       | Kategori intensitas hujan 0-4            |
| 13 | `rain_persistence`     | Rasio hujan 3h/1h                        |
| 14 | `saturation_index`     | rainfall_24h × humidity/100             |
| 15 | `drainage_score`       | Composite drainage (elevasi+tanah+jarak) |
| 16 | `heat_humidity`        | Suhu × kelembaban/100                   |
| 17 | `city_risk`            | Composite kerawanan historis kota        |

## API Endpoints

| Method | Endpoint                 | Deskripsi                                    |
| ------ | ------------------------ | -------------------------------------------- |
| GET    | `/`                    | Info API                                     |
| GET    | `/api/ml/health`       | Status model (loaded/error)                  |
| GET    | `/api/ml/model-info`   | Metadata lengkap model                       |
| POST   | `/api/ml/predict`      | Prediksi dengan input lengkap                |
| POST   | `/api/ml/predict-auto` | Prediksi minimal (nama kota + basic weather) |
| POST   | `/api/ml/batch`        | Prediksi banyak lokasi (max 20)              |

### Contoh Response `POST /api/ml/predict`

```json
{
  "risk_level": "awas",
  "risk_score": 0.9847,
  "probabilities": {
    "aman": 0.0, "waspada": 0.0, "siaga": 0.0, "awas": 1.0
  },
  "confidence": "high",
  "top_features": [
    { "feature": "saturation_index", "importance": 0.1823, "value": 332.5, "direction": "increase_risk" },
    { "feature": "rainfall_1h",      "importance": 0.1645, "value": 65.0,  "direction": "increase_risk" },
    { "feature": "city_risk",        "importance": 0.1412, "value": 0.88,  "direction": "increase_risk" }
  ],
  "message": " BAHAYA! Risiko banjir sangat tinggi. Segera evakuasi!",
  "actions": [
    "SEGERA evakuasi ke tempat lebih tinggi!",
    "Hubungi BNPB: 119 atau Darurat: 112.",
    "Matikan listrik dari panel MCB sekarang."
  ],
  "model_version": "20260505_0617",
  "inference_ms": 58.3
}
```

---

## Model Performance

| Metric                        | Value            |
| ----------------------------- | ---------------- |
| **Accuracy**            | **99.1%**  |
| **F1-Score (weighted)** | **0.9915** |
| **F1-Score (macro)**    | **0.9915** |
| **ROC-AUC (OvR)**       | **0.9999** |
| CV F1 (5-fold)                | 0.9960 ± 0.0005 |

### Per-class F1

| Kelas   | Precision | Recall | F1     |
| ------- | --------- | ------ | ------ |
| aman    | 0.9874    | 0.9796 | 0.9835 |
| waspada | 0.9877    | 0.9899 | 0.9888 |
| siaga   | 0.9943    | 0.9929 | 0.9936 |
| awas    | 0.9940    | 0.9954 | 0.9947 |

### Top Feature Importances

```
saturation_index     18.23% ████████████████████
rainfall_1h          16.45% ██████████████████
city_risk            14.12% ████████████████
rainfall_3h          12.87% ██████████████
drainage_score       11.34% █████████████
```


### Environment Variables

Model file di-load dari folder `models/` secara lokal.
Jika folder `models/` tidak ada, pipeline training akan berjalan otomatis.
