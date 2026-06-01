'use client'
import { useEffect, useState } from 'react'
import { Brain, Info } from 'lucide-react'
import type { FloodPrediction } from '@/types'
import { RiskBadge } from '@/components/ui/RiskBadge'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts'

interface Props { prediction: FloodPrediction }

const FEATURE_LABELS: Record<string, string> = {
  rainfall_1h:           'Hujan 1 Jam',
  rainfall_3h:           'Hujan 3 Jam',
  rainfall_24h:          'Hujan 24 Jam',
  humidity:              'Kelembaban',
  temperature:           'Suhu',
  wind_speed:            'Angin',
  month:                 'Bulan',
  elevation_m:           'Elevasi',
  distance_to_river_km:  'Jarak Sungai',
  soil_type_encoded:     'Jenis Tanah',
  rain_intensity:        'Intensitas Hujan',
  rain_persistence:      'Persistensi Hujan',
  saturation_index:      'Saturasi',
  drainage_score:        'Drainase',
  heat_humidity:         'Panas-Lembab',
  city_risk:             'Risiko Kota',
}

const CONF_COLORS: Record<string, string> = {
  high:   'text-green-600',
  medium: 'text-amber-600',
  low:    'text-red-500',
}
const CONF_LABELS: Record<string, string> = {
  high: 'Tinggi', medium: 'Sedang', low: 'Rendah',
}

const BAR_COLORS = ['#3b82f6','#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#7c3aed','#4f46e5']

export function MLPredictionCard({ prediction }: Props) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  const chartData = prediction.top_features.slice(0, 5).map((f, i) => ({
    name:       FEATURE_LABELS[f.feature] || f.feature,
    importance: parseFloat((f.importance * 100).toFixed(1)),
    color:      BAR_COLORS[i] ?? '#6366f1',
  }))

  const riskColor = {
    aman:    '#16a34a',
    waspada: '#d97706',
    siaga:   '#ea580c',
    awas:    '#dc2626',
  }[prediction.risk_level] ?? '#6b7280'

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-semibold text-slate-800">Prediksi ML</span>
          <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full border border-indigo-100">
            Random Forest
          </span>
        </div>
        <RiskBadge level={prediction.risk_level} size="sm" animate={prediction.risk_level === 'awas'} />
      </div>

      <div className="px-4 py-3 space-y-3">
        {/* Risk Score Bar */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-500">Risk Score</span>
            <span className="font-semibold text-slate-700">
              {(prediction.risk_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${prediction.risk_score * 100}%`, background: riskColor }}
            />
          </div>
        </div>

        {/* Probability per kelas */}
        <div className="grid grid-cols-4 gap-1 text-center">
          {(['aman','waspada','siaga','awas'] as const).map(cls => (
            <div key={cls} className="bg-slate-50 rounded-lg py-1.5">
              <div className="text-xs font-bold text-slate-700">
                {((prediction.probabilities[cls] ?? 0) * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-slate-400 capitalize leading-tight">{cls}</div>
            </div>
          ))}
        </div>

        {/* Feature Importance Chart */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <Info className="w-3.5 h-3.5 text-slate-400" />
            <p className="text-xs text-slate-500 font-medium">
              Feature Importance (Top 5)
            </p>
          </div>
          <div style={{ height: 118 }}>
            {isClient && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ left: 0, right: 16, top: 0, bottom: 0 }}
                >
                  <XAxis
                    type="number"
                    tick={{ fontSize: 10, fill: '#94a3b8' }}
                    tickFormatter={(v: number) => `${v}%`}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 10, fill: '#64748b' }}
                    width={86}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(val) => [`${val}%`, 'Importance']}
                    contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e2e8f0' }}
                  />
                  <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 flex justify-between items-center">
        <span className="text-xs text-slate-400">
          v{prediction.model_version} · {prediction.inference_ms}ms
        </span>
        <span className={`text-xs font-medium ${CONF_COLORS[prediction.confidence] ?? ''}`}>
          Kepercayaan: {CONF_LABELS[prediction.confidence] ?? prediction.confidence}
        </span>
      </div>
    </div>
  )
}