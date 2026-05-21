# SiagaAI — Backend (FastAPI + Python)

REST API SiagaAI: Multi-model LLM (Groq/Llama) + Custom ML Model (Random Forest) + RAG.

## Struktur

```
backend/
├── main.py                  ← Entry point FastAPI + lifespan
├── requirements.txt         ← Python dependencies
├── .env.example             ← Template environment variables
├── SiagaAI_API.postman_collection.json
├── scripts/
│   └── seed_knowledge.py    ← Load dataset ke ChromaDB
├── models/                  ← Trained .pkl files (auto-generated)
├── app/
│   ├── core/                ← config, database, exceptions, logging
│   ├── models/              ← SQLAlchemy ORM (session, message, escalation)
│   ├── schemas/             ← Pydantic schemas (chat, location, ml, escalation)
│   ├── services/
│   │   ├── ai/              ← llm_factory, chatbot, intent, prompts, knowledge_base
│   │   ├── ml/              ← flood_predictor (Random Forest inference)
│   │   ├── weather/         ← bmkg, openweather
│   │   ├── location/        ← geocoder (Nominatim)
│   │   └── disaster/        ← risk_analyzer (4 jenis bencana)
│   ├── api/
│   │   ├── deps.py          ← Dependency injection
│   │   └── routes/          ← health, models, ml, chat, location, escalate, knowledge
│   └── data/
│       └── disaster_knowledge.json  ← 42 dokumen knowledge base
```

## Quick Start

```bash
# 1. Virtual environment
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env: isi GROQ_API_KEY dan OWM_API_KEY

# 4. Setup database
createdb siagaai

# 5. Train ML Model (auto-generate synthetic data)
python scripts/train_model.py

# 6. Load knowledge base
python scripts/seed_knowledge.py

# 7. Jalankan server
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint                            | Keterangan                    |
| ------ | ----------------------------------- | ----------------------------- |
| GET    | `/api/health`                     | Status semua services         |
| GET    | `/api/models/active`              | Daftar LLM model aktif        |
| POST   | `/api/models/test`                | Test koneksi model            |
| POST   | `/api/ml/predict-flood`           | Prediksi risiko banjir (ML)   |
| POST   | `/api/ml/predict-auto`            | Prediksi otomatis dari lokasi |
| GET    | `/api/ml/model-info`              | Info ML model                 |
| POST   | `/api/chat/sessions`              | Buat sesi chat                |
| POST   | `/api/chat/send`                  | Kirim pesan ke chatbot        |
| GET    | `/api/chat/sessions/{id}/history` | Riwayat pesan                 |
| POST   | `/api/location/status`            | Status cuaca + risiko         |
| GET    | `/api/location/geocode`           | Nama kota → koordinat        |
| POST   | `/api/escalate`                   | Laporkan situasi darurat      |
| GET    | `/api/knowledge/stats`            | Info knowledge base           |

Docs: **http://localhost:8000/docs**

## API Keys

| Service        | Link                   | Keterangan                                  |
| -------------- | ---------------------- | ------------------------------------------- |
| Groq           | console.groq.com       | **WAJIB** — LLM Llama 3.3 (gratis)   |
| OpenWeatherMap | openweathermap.org/api | **WAJIB** — cuaca real-time (gratis) |
| BMKG           | data.bmkg.go.id        | Otomatis — tidak perlu key                 |
