# SiagaAI — Backend (FastAPI)

REST API SiagaAI: **Custom ML Model (Random Forest)** + **Multi-model LLM (Groq/Llama)** + **RAG (ChromaDB)**

## 🚀 Quick Start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # isi GROQ_API_KEY + OWM_API_KEY
createdb siagaai
python scripts/seed_knowledge.py
uvicorn main:app --reload   # http://localhost:8000/docs
```

## 📁 Struktur

```
backend/
├── main.py                        ← Entry point + startup model load
├── models/                        ← Model ML dari ML Pipeline project
│   ├── flood_risk_model.pkl       ← Random Forest (99.1% accuracy)
│   ├── feature_scaler.pkl
│   ├── label_encoder.pkl
│   └── model_metadata.json
├── app/
│   ├── api/routes/
│   │   ├── ml.py         ← ML predict (manual + auto OWM + batch)
│   │   ├── chat.py       ← Chat session + send message
│   │   ├── location.py   ← Cuaca + geocode + BMKG
│   │   ├── escalate.py   ← SOS darurat
│   │   ├── knowledge.py  ← RAG knowledge base
│   │   ├── models.py     ← LLM model listing
│   │   └── health.py     ← Health check
│   ├── services/
│   │   ├── ml/flood_predictor.py  ← Load PKL + inference (NO training)
│   │   ├── ai/                    ← LLM factory + chatbot + RAG
│   │   ├── weather/               ← BMKG + OpenWeatherMap
│   │   ├── location/              ← Geocoder Nominatim
│   │   └── disaster/              ← Risk analyzer
│   └── data/
│       └── disaster_knowledge.json  ← 42 dokumen RAG
├── scripts/
│   └── seed_knowledge.py          ← Load KB ke ChromaDB
└── SiagaAI_API_Complete.postman_collection.json
```

## 📡 Endpoints

| Method | Endpoint | Keterangan |
|--------|----------|-----------|
| GET | `/api/health` | Status semua service |
| GET | `/api/ml/health` | Status ML model |
| GET | `/api/ml/model-info` | Info RF model |
| POST | `/api/ml/predict` | Prediksi manual |
| POST | `/api/ml/predict-auto` | Auto fetch OWM → ML |
| POST | `/api/ml/batch` | Batch prediksi |
| GET | `/api/models/active` | Daftar LLM aktif |
| POST | `/api/chat/sessions` | Buat sesi chat |
| POST | `/api/chat/send` | Kirim pesan |
| POST | `/api/location/status` | Cuaca + risiko |
| POST | `/api/escalate` | Laporan darurat |

## ⚠️ Catatan Model ML

Model PKL **sudah tersedia** di `models/`. Tidak perlu training ulang.
Untuk training ulang, gunakan project **03_SiagaAI_ML_Pipeline**.
