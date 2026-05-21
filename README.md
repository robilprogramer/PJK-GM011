# SiagaAI — Frontend

Antarmuka chatbot SiagaAI berbasis

## Struktur

```
frontend/
├── app/
│   ├── layout.tsx        ← Root layout + metadata
│   ├── page.tsx          ← Halaman utama (orchestrator)
│   └── globals.css       ← Global styles + Tailwind
├── components/
│   ├── chat/
│   │   ├── ChatBubble.tsx    ← Bubble pesan + intent badge + markdown
│   │   ├── ChatInput.tsx     ← Input textarea + quick suggestions
│   │   └── SOSModal.tsx      ← Modal panic button + form darurat
│   ├── location/
│   │   ├── LocationSetup.tsx     ← Onboarding GPS/manual input
│   │   ├── WeatherCard.tsx       ← Card cuaca + risk indicators
│   │   └── MLPredictionCard.tsx  ← SHAP chart + ML risk score
│   ├── layout/
│   │   └── AppHeader.tsx     ← Header: brand + lokasi + model selector
│   └── ui/
│       ├── RiskBadge.tsx     ← Badge: aman/waspada/siaga/awas
│       └── ModelSelector.tsx ← Dropdown pilih LLM model
├── lib/
│   ├── api.ts              ← Semua API calls ke FastAPI backend
│   ├── store.ts            ← Zustand state: location, chat, settings
│   ├── utils.ts            ← Helper: cn, formatTime, generateId
│   └── hooks/
│       └── useGeolocation.ts ← GPS detect + manual geocode
└── types/
    └── index.ts            ← Semua TypeScript types global
```

## Setup

```bash
# Install dependencies
npm install

# Setup environment
cp .env.example .env.local
# Isi: NEXT_PUBLIC_API_URL=http://localhost:8000

# Jalankan dev server
npm run dev
```

Buka: **http://localhost:3000**

## Environment Variables

| Variable                | Default                   | Keterangan          |
| ----------------------- | ------------------------- | ------------------- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL FastAPI backend |

## Build untuk Production

```bash
npm run build
npm run start
```

## Deploy ke Vercel

```bash
npx vercel
# Set env: NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```
