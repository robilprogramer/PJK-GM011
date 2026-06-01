'use client'
import { useState, useEffect } from 'react'
import { Cpu, ChevronDown, Check, Zap } from 'lucide-react'
import { useSettingsStore } from '@/lib/store'
import { getActiveModels }  from '@/lib/api'

const PROVIDER_BADGE: Record<string,string> = {
  groq:   'bg-orange-100 text-orange-700',
  openai: 'bg-green-100 text-green-700',
  gemini: 'bg-blue-100 text-blue-700',
}

export function ModelSelector() {
  const { selectedModel, availableModels, setModel, setAvailableModels } = useSettingsStore()
  const [open,    setOpen]    = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (availableModels.length > 0) return
    setLoading(true)
    getActiveModels()
      .then(res => {
        setAvailableModels(res.models)
        if (!selectedModel && res.default_model) setModel(res.default_model)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const current     = availableModels.find(m => m.model_id === selectedModel)
  const displayName = loading
    ? 'Memuat…'
    : current?.display_name ?? selectedModel.split('-').slice(0,2).join(' ')

  return (
    <div className="relative">
      <button onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-sm bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 hover:bg-slate-50 transition-colors shadow-sm">
        <Cpu className="w-3.5 h-3.5 text-indigo-500 flex-shrink-0" />
        <span className="text-slate-700 font-medium max-w-[110px] truncate text-xs">{displayName}</span>
        <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform flex-shrink-0 ${open?'rotate-180':''}`} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1.5 z-20 w-72 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden">
            <div className="px-3 py-2 bg-slate-50 border-b border-slate-100">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Pilih Model AI</p>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {availableModels.length === 0 && (
                <p className="px-4 py-5 text-sm text-slate-400 text-center">
                  {loading ? 'Memuat model…' : 'Tidak ada model aktif. Cek API key.'}
                </p>
              )}
              {availableModels.map(m => (
                <button key={m.model_id} onClick={() => { setModel(m.model_id); setOpen(false) }}
                  className="w-full text-left px-3 py-2.5 hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-medium text-slate-800 truncate">{m.display_name}</span>
                        {m.is_free && <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full flex-shrink-0">Gratis</span>}
                      </div>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${PROVIDER_BADGE[m.provider]||'bg-gray-100 text-gray-600'}`}>{m.provider}</span>
                        <span className="text-xs text-slate-400">{(m.context_window/1000).toFixed(0)}K ctx</span>
                        {m.tags.includes('recommended') && (
                          <span className="flex items-center gap-0.5 text-xs text-amber-600">
                            <Zap className="w-3 h-3"/>Rekomendasi
                          </span>
                        )}
                      </div>
                    </div>
                    {selectedModel === m.model_id && <Check className="w-4 h-4 text-blue-600 flex-shrink-0 mt-1" />}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
