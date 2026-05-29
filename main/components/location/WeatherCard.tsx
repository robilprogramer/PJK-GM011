'use client'
import { Droplets, Wind, Thermometer, CloudRain, RefreshCw, MapPin } from 'lucide-react'
import type { LocationStatus } from '@/types'
import { RiskBadge }   from '@/components/ui/RiskBadge'
import { formatTime }  from '@/lib/utils'

interface Props {
  status:     LocationStatus
  onRefresh?: () => void
  isLoading?: boolean
}

export function WeatherCard({ status, onRefresh, isLoading }: Props) {
  const { weather, earthquake, risks, overall_risk, location, updated_at } = status

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2.5 flex items-center justify-between border-b border-slate-100">
        <div className="flex items-center gap-2 min-w-0">
          <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-800 truncate leading-tight">
              {location.city}
            </p>
            <p className="text-xs text-slate-400 leading-tight">{location.province}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          <RiskBadge level={overall_risk} size="sm" animate={overall_risk === 'awas'} />
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
              title="Refresh data"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="px-4 py-2.5 grid grid-cols-4 gap-2">
        {[
          { icon: Thermometer, label: 'Suhu',  value: `${weather.temperature.toFixed(0)}°C`, color: 'text-orange-500' },
          { icon: Droplets,    label: 'Lembab', value: `${weather.humidity}%`,                color: 'text-blue-500' },
          { icon: CloudRain,   label: 'Hujan',  value: `${weather.rainfall_1h.toFixed(1)}mm`, color: 'text-cyan-500' },
          { icon: Wind,        label: 'Angin',  value: `${weather.wind_speed.toFixed(1)}m/s`, color: 'text-slate-400' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="flex flex-col items-center gap-0.5">
            <Icon className={`w-4 h-4 ${color}`} />
            <span className="text-xs text-slate-400">{label}</span>
            <span className="text-xs font-semibold text-slate-700">{value}</span>
          </div>
        ))}
      </div>

      {/* Condition */}
      <div className="px-4 pb-2">
        <p className="text-xs text-slate-500 capitalize leading-relaxed">
          🌤 {weather.condition}
          {earthquake.magnitude && (
            <span className="ml-1.5 text-slate-400">
              · Gempa M{earthquake.magnitude} ({earthquake.location})
            </span>
          )}
        </p>
      </div>

      {/* Risk tags */}
      {risks.length > 0 && (
        <div className="px-4 pb-2.5 flex flex-wrap gap-1.5">
          {risks.map(r => (
            <div key={r.type} className="flex items-center gap-1 text-xs">
              <RiskBadge level={r.level} size="xs" showEmoji={false} />
              <span className="text-slate-400 capitalize">{r.type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-1.5 bg-slate-50 border-t border-slate-100">
        <p className="text-xs text-slate-400">Update {formatTime(updated_at)}</p>
      </div>
    </div>
  )
}
