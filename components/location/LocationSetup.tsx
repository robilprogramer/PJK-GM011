'use client'
import { useState } from 'react'
import { MapPin, Navigation, Search, Loader2, Shield, Zap, Brain } from 'lucide-react'
import { useGeolocation } from '@/lib/hooks/useGeolocation'
import { useLocationStore } from '@/lib/store'
import { cn } from '@/lib/utils'

export function LocationSetup() {
  const { detectAuto, setManual } = useGeolocation()
  const { isDetecting, error } = useLocationStore()
  const [cityInput, setCityInput] = useState('')

  const handleManual = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!cityInput.trim() || isDetecting) return
    await setManual(cityInput.trim())
    setCityInput('')
  }

  const QUICK_CITIES = ['Jakarta', 'Bandung', 'Surabaya', 'Yogyakarta', 'Medan', 'Makassar']

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        {/* Brand */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-red-100 rounded-3xl mb-4 shadow-sm">
            <span className="text-4xl">🚨</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-800">SiagaAI</h1>
          <p className="text-slate-500 mt-1.5 text-sm leading-relaxed">
            Sistem Prediksi & Mitigasi Bencana Alam Indonesia
            <br />
            <span className="text-xs">Didukung Custom ML + Llama 3.3 via Groq</span>
          </p>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2">
          {[
            { icon: Brain, label: 'ML Model Banjir' },
            { icon: Zap, label: 'BMKG Real-Time' },
            { icon: Shield, label: 'Panduan Evakuasi' },
          ].map(({ icon: Icon, label }) => (
            <span key={label} className="inline-flex items-center gap-1.5 text-xs bg-white border border-slate-200 text-slate-600 px-3 py-1.5 rounded-full shadow-sm">
              <Icon className="w-3.5 h-3.5 text-blue-500" />
              {label}
            </span>
          ))}
        </div>

        {/* GPS Button */}
        <button
          onClick={detectAuto}
          disabled={isDetecting}
          className={cn(
            'w-full flex items-center justify-center gap-3 font-semibold py-4 rounded-2xl transition-all shadow-sm',
            isDetecting
              ? 'bg-blue-400 text-white cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 active:scale-[0.98] text-white'
          )}
        >
          {isDetecting ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Navigation className="w-5 h-5" />
          )}
          {isDetecting ? 'Mendeteksi lokasi...' : 'Deteksi Lokasi Otomatis (GPS)'}
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-slate-200" />
          <span className="text-xs text-slate-400 font-medium px-1">atau ketik nama kota</span>
          <div className="flex-1 h-px bg-slate-200" />
        </div>

        {/* Manual input */}
        <form onSubmit={handleManual} className="flex gap-2">
          <div className="relative flex-1">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={cityInput}
              onChange={e => setCityInput(e.target.value)}
              placeholder="Contoh: Jakarta, Bandung, Surabaya…"
              disabled={isDetecting}
              className="w-full pl-10 pr-4 py-3.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm disabled:opacity-60"
            />
          </div>
          <button
            type="submit"
            disabled={isDetecting || !cityInput.trim()}
            className="px-4 py-3.5 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-xl transition-colors shadow-sm"
          >
            <Search className="w-4 h-4" />
          </button>
        </form>

        {/* Quick city chips */}
        <div className="flex flex-wrap gap-2 justify-center">
          {QUICK_CITIES.map(city => (
            <button
              key={city}
              onClick={() => setManual(city)}
              disabled={isDetecting}
              className="text-xs bg-white border border-slate-200 text-slate-600 hover:border-blue-400 hover:text-blue-600 px-3 py-1.5 rounded-full transition-colors disabled:opacity-50 shadow-sm"
            >
              📍 {city}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-2">
            <span className="flex-shrink-0 mt-0.5">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-center text-xs text-slate-400 leading-relaxed px-4">
          Lokasi digunakan hanya untuk menampilkan informasi risiko bencana yang relevan.
          Data tidak disimpan ke server.
        </p>
      </div>
    </div>
  )
}
