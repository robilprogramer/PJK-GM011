'use client'
import { Droplets, Wind, Thermometer, CloudRain, RefreshCw } from 'lucide-react'
import type { LocationStatus } from '@/types'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { formatTime } from '@/lib/utils'

interface Props {
  status: LocationStatus
  onRefresh?: () => void
  isLoading?: boolean
}

export function WeatherCard({ status, onRefresh, isLoading }: Props) {
  const { weather, earthquake, risks, overall_risk, location, updated_at } = status

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="text-base">📍</span>
          <div>
            <p className="text-sm font-semibold text-slate-800 leading-tight">{location.city}</p>
            <p className="text-xs text-slate-400">{location.province}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <RiskBadge level={overall_risk} size="sm" animate={overall_risk === 'awas'} />
          {onRefresh && (
            <button onClick={onRefresh} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Weather Stats */}
      <div className="px-4 py-3 grid grid-cols-4 gap-3">
        {[
          { icon: <Thermometer className="w-4 h-4" />, label:'Suhu', value:`${weather.temperature.toFixed(0)}°C`, color:'text-orange-500' },
          { icon: <Droplets className="w-4 h-4" />,    label:'Lembab', value:`${weather.humidity}%`, color:'text-blue-500' },
          { icon: <CloudRain className="w-4 h-4" />,   label:'Hujan', value:`${weather.rainfall_1h.toFixed(1)}mm`, color:'text-cyan-500' },
          { icon: <Wind className="w-4 h-4" />,        label:'Angin', value:`${weather.wind_speed.toFixed(1)}m/s`, color:'text-slate-500' },
        ].map(({ icon, label, value, color }) => (
          <div key={label} className="flex flex-col items-center gap-1">
            <span className={color}>{icon}</span>
            <span className="text-xs text-slate-400">{label}</span>
            <span className="text-sm font-semibold text-slate-700">{value}</span>
          </div>
        ))}
      </div>

      {/* Condition */}
      <div className="px-4 pb-2">
        <p className="text-xs text-slate-500 capitalize">
          🌤 {weather.condition}
          {earthquake.magnitude && (
            <span className="ml-2">• Gempa terakhir: M{earthquake.magnitude} di {earthquake.location}</span>
          )}
        </p>
      </div>

      {/* Risk Rows */}
      {risks.length > 0 && (
        <div className="px-4 pb-3 flex flex-wrap gap-1.5">
          {risks.map(r => (
            <div key={r.type} className="flex items-center gap-1 text-xs">
              <RiskBadge level={r.level} size="sm" />
              <span className="text-slate-500 capitalize">{r.type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-100 bg-slate-50">
        <p className="text-xs text-slate-400">Diperbarui {formatTime(updated_at)}</p>
      </div>
    </div>
  )
}
