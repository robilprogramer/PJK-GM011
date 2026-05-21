'use client'
import { MapPin, RefreshCw, Trash2 } from 'lucide-react'
import { ModelSelector } from '@/components/ui/ModelSelector'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { useLocationStore, useChatStore } from '@/lib/store'

interface Props {
  onChangeLocation: () => void
}

export function AppHeader({ onChangeLocation }: Props) {
  const { location, overallRisk } = useLocationStore()
  const { clearChat, session } = useChatStore()

  return (
    <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between gap-3 sticky top-0 z-30">
      {/* Brand */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-xl">🚨</span>
        <div>
          <h1 className="text-base font-bold text-slate-800 leading-tight">SiagaAI</h1>
          <p className="text-xs text-slate-400 leading-tight hidden sm:block">Prediksi Bencana AI</p>
        </div>
      </div>

      {/* Location + Risk */}
      {location && (
        <button
          onClick={onChangeLocation}
          className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-800 min-w-0"
        >
          <MapPin className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
          <span className="truncate max-w-[120px] sm:max-w-[180px]">{location.city}</span>
          <RiskBadge level={overallRisk} size="sm" animate={overallRisk === 'awas'} />
        </button>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <ModelSelector />
        {session && (
          <button
            onClick={clearChat}
            title="Clear chat"
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  )
}
