# SiagaAI — Frontend (Next.js 14)

## 🚀 Quick Start

```bash
npm install
cp .env.example .env.local    # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                   # http://localhost:3000
```

## 📁 Struktur

```
frontend/
├── app/
│   ├── layout.tsx      ← Root layout
│   ├── page.tsx        ← Halaman utama (chat + ML card + SOS)
│   └── globals.css
├── components/
│   ├── chat/
│   │   ├── ChatBubble.tsx   ← Bubble pesan + markdown + intent badge
│   │   ├── ChatInput.tsx    ← Input + quick suggestions
│   │   └── SOSModal.tsx     ← Modal darurat + form eskalasi
│   ├── location/
│   │   ├── LocationSetup.tsx     ← GPS auto + manual + quick cities
│   │   ├── WeatherCard.tsx       ← Cuaca real-time + risk badges
│   │   └── MLPredictionCard.tsx  ← SHAP chart + risk score
│   ├── layout/
│   │   └── AppHeader.tsx    ← Header + lokasi + model selector
│   └── ui/
│       ├── RiskBadge.tsx    ← Badge aman/waspada/siaga/awas
│       └── ModelSelector.tsx ← Dropdown ganti LLM dinamis
├── lib/
│   ├── api.ts          ← Semua API calls ke backend
│   ├── store.ts        ← Zustand: location, chat, settings
│   ├── utils.ts        ← cn, formatTime, generateId
│   └── hooks/useGeolocation.ts
└── types/index.ts      ← TypeScript global types
```

## 🔑 Environment

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📦 Deploy Vercel

```bash
npx vercel
# Set env: NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```
