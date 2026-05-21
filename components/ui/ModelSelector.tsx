'use client'
import { useState, useEffect } from 'react'
import { Cpu, ChevronDown, Check, Zap, Wifi } from 'lucide-react'
import { useSettingsStore } from '@/lib/store'
import { getActiveModels } from '@/lib/api'
import type { LLMModel } from '@/types'

const PROVIDER_BADGE: Record<string, string> = {
  groq:   'bg-orange-100 text-orange-700',
  openai: 'bg-green-100 text-green-700',
  gemini: 'bg-blue-100 text-blue-700',
}

export function ModelSelector() {
  const { selectedModel, availableModels, setModel, setAvailableModels } = useSettingsStore()
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    ;(async () => {
      if (availableModels.length > 0) return
      setLoading(true)
      try {
        const res = await getActiveModels()
        setAvailableModels(res.models)
        if (!selectedModel && res.default_model) setModel(res.default_model)
      } catch {
        // silent — keep stored value
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const current = availableModels.find(m => m.model_id === selectedModel)
  const displayName = loading
    ? 'Memuat model...'
    : current?.display_name ?? selectedModel.split('-').slice(0, 2).join(' ')

  return (
    <div className="relative">
      {/* Trigger button */}
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 text-sm bg-white border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-slate-50 transition-colors shadow-sm"
      >
        <Cpu className="w-4 h-4 text-indigo-500 flex-shrink-0" />
        <span className="text-slate-700 font-medium max-w-[130px] truncate">{displayName}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform flex-shrink-0 ${open ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1.5 z-20 w-80 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden">
            <div className="px-3 py-2.5 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Pilih Model AI</p>
              <div className="flex items-center gap-1 text-xs text-slate-400">
                <Wifi className="w-3 h-3" />
                {availableModels.length} tersedia
              </div>
            </div>

            <div className="max-h-72 overflow-y-auto">
              {availableModels.length === 0 && (
                <div className="px-4 py-6 text-center text-sm text-slate-400">
                  {loading ? 'Memuat daftar model...' : 'Tidak ada model aktif. Cek API key di .env'}
                </div>
              )}
              {availableModels.map(m => (
                <button
                  key={m.model_id}
                  onClick={() => { setModel(m.model_id); setOpen(false) }}
                  className="w-full text-left px-3 py-2.5 hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-medium text-slate-800 truncate">{m.display_name}</span>
                        {m.is_free && (
                          <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium flex-shrink-0">
                            Gratis
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${PROVIDER_BADGE[m.provider] || 'bg-gray-100 text-gray-600'}`}>
                          {m.provider}
                        </span>
                        <span className="text-xs text-slate-400">
                          {(m.context_window / 1000).toFixed(0)}K ctx
                        </span>
                        {m.tags.includes('recommended') && (
                          <span className="flex items-center gap-0.5 text-xs text-amber-600 flex-shrink-0">
                            <Zap className="w-3 h-3" />Rekomendasi
                          </span>
                        )}
                      </div>
                    </div>
                    {selectedModel === m.model_id && (
                      <Check className="w-4 h-4 text-blue-600 flex-shrink-0 mt-1" />
                    )}
                  </div>
                </button>
              ))}
            </div>

            <div className="px-3 py-2 border-t border-slate-100 bg-slate-50">
              <p className="text-xs text-slate-400 text-center">
                Model bisa diganti per percakapan tanpa restart server
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
