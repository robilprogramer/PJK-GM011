'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Brain, Info } from 'lucide-react'
import type { FloodPrediction } from '@/types'
import { RiskBadge } from '@/components/ui/RiskBadge'

interface Props { prediction: FloodPrediction }

const FEATURE_LABELS: Record<string, string> = {
  rainfall_1h:            'Hujan 1 Jam',
  rainfall_3h:            'Hujan 3 Jam',
  rainfall_24h:           'Hujan 24 Jam',
  humidity:               'Kelembaban',
  temperature:            'Suhu',
  wind_speed:             'Kecepatan Angin',
  month:                  'Bulan',
  elevation_m:            'Elevasi',
  distance_to_river_km:   'Jarak ke Sungai',
  soil_type_encoded:      'Jenis Tanah',
}

const CONF_COLORS: Record<string, string> = {
  high: 'text-green-600', medium: 'text-amber-600', low: 'text-red-500',
}

export function MLPredictionCard({ prediction }: Props) {
  const chartData = prediction.top_features.map(f => ({
    name: FEATURE_LABELS[f.feature] || f.feature,
    importance: +(f.importance * 100).toFixed(1),
    value: f.value,
    direction: f.direction,
  }))

  const confLabel: Record<string, string> = {
    high: 'Tinggi', medium: 'Sedang', low: 'Rendah',
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-semibold text-slate-800">Prediksi ML Model</span>
          <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
            Random Forest
          </span>
        </div>
        <RiskBadge level={prediction.risk_level} size="sm" animate={prediction.risk_level === 'awas'} />
      </div>

      <div className="px-4 py-3 space-y-3">
        {/* Risk Score bar */}
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Risk Score</span>
            <span className="font-semibold text-slate-700">{(prediction.risk_score * 100).toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${prediction.risk_score * 100}%`,
                background: prediction.risk_score > 0.7 ? '#dc2626'
                  : prediction.risk_score > 0.4 ? '#ea580c'
                  : prediction.risk_score > 0.2 ? '#d97706' : '#16a34a'
              }}
            />
          </div>
        </div>

        {/* Probabilities */}
        <div className="grid grid-cols-4 gap-1">
          {(['aman','waspada','siaga','awas'] as const).map(cls => (
            <div key={cls} className="text-center">
              <div className="text-xs font-semibold text-slate-700">
                {((prediction.probabilities[cls] || 0) * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-slate-400 capitalize">{cls}</div>
            </div>
          ))}
        </div>

        {/* SHAP Feature Importance Chart */}
        <div>
          <div className="flex items-center gap-1 mb-2">
            <Info className="w-3.5 h-3.5 text-slate-400" />
            <p className="text-xs text-slate-500 font-medium">Feature Importance (Top 5)</p>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 20, top: 0, bottom: 0 }}>
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={90} />
              <Tooltip
                formatter={(val: number) => [`${val}%`, 'Importance']}
                contentStyle={{ fontSize: 11, borderRadius: 8 }}
              />
              <Bar dataKey="importance" radius={[0,4,4,0]}>
                {chartData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={['#3b82f6','#6366f1','#8b5cf6','#a78bfa','#c4b5fd'][i] || '#6366f1'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-100 bg-slate-50 flex justify-between">
        <span className="text-xs text-slate-400">v{prediction.model_version}</span>
        <span className={`text-xs font-medium ${CONF_COLORS[prediction.confidence] || ''}`}>
          Kepercayaan: {confLabel[prediction.confidence] || prediction.confidence}
        </span>
      </div>
    </div>
  )
}
