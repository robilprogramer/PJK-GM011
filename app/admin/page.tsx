'use client'
import { useState, useEffect, useCallback } from 'react'
import {
  Brain, Activity, Database, MessageSquare, AlertTriangle,
  RefreshCw, CheckCircle, XCircle, Zap, Shield, BarChart3,
  Users, Clock, ArrowLeft, Search, Trash2
} from 'lucide-react'
import Link from 'next/link'
import { getHealth, getMLModelInfo, getActiveModels } from '@/lib/api'
import api from '@/lib/api'
import type { MLModelInfo, LLMModel } from '@/types'
import { cn, formatDate } from '@/lib/utils'

// ─── API helpers admin ────────────────────────────────────────
const getKBStats    = async () => (await api.get('/api/knowledge/stats')).data.data
const reloadKB      = async () => (await api.post('/api/knowledge/reload')).data
const searchKB      = async (q: string) => (await api.post('/api/knowledge/search', { query: q, n_results: 3 })).data.data
const getEarthquakes= async () => (await api.get('/api/location/earthquakes?limit=5')).data.data

// ─── Types ────────────────────────────────────────────────────
interface HealthStatus {
  status: string
  version: string
  environment: string
  timestamp: string
  services: Record<string, unknown>
}
interface KBStats {
  total_documents: number
  collection_name: string
  [k: string]: unknown
}
interface EqData {
  summary: string
  magnitude?: string
  location?: string
  date?: string
}

// ─── Stat Card ────────────────────────────────────────────────
function StatCard({
  icon, title, value, sub, color, loading
}: {
  icon: React.ReactNode; title: string; value: string | number
  sub?: string; color: string; loading?: boolean
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className={cn('w-9 h-9 rounded-xl flex items-center justify-center', color)}>
          {icon}
        </div>
        {loading && <RefreshCw className="w-3.5 h-3.5 text-slate-300 animate-spin" />}
      </div>
      <p className="text-2xl font-bold text-slate-800 leading-none mb-1">
        {loading ? '–' : value}
      </p>
      <p className="text-xs font-medium text-slate-600">{title}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  )
}

// ─── Service Badge ────────────────────────────────────────────
function ServiceBadge({ name, status }: { name: string; status: unknown }) {
  const ok = status === 'ok' || status === 'loaded'
  const warn = typeof status === 'string' && status.startsWith('no_')
  return (
    <div className={cn(
      'flex items-center justify-between px-3 py-2 rounded-xl border text-sm',
      ok   ? 'bg-green-50 border-green-200' :
      warn ? 'bg-amber-50 border-amber-200' :
             'bg-red-50   border-red-200'
    )}>
      <span className="font-medium text-slate-700">{name}</span>
      <div className="flex items-center gap-1.5">
        {ok
          ? <CheckCircle className="w-4 h-4 text-green-500" />
          : warn
          ? <AlertTriangle className="w-4 h-4 text-amber-500" />
          : <XCircle className="w-4 h-4 text-red-500" />
        }
        <span className={cn('text-xs font-medium',
          ok ? 'text-green-600' : warn ? 'text-amber-600' : 'text-red-600'
        )}>
          {ok ? 'Online' : warn ? 'No Key' : 'Offline'}
        </span>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const [health,     setHealth]     = useState<HealthStatus | null>(null)
  const [mlInfo,     setMlInfo]     = useState<MLModelInfo | null>(null)
  const [models,     setModels]     = useState<LLMModel[]>([])
  const [kbStats,    setKbStats]    = useState<KBStats | null>(null)
  const [earthquakes,setEarthquakes]= useState<EqData[]>([])
  const [loading,    setLoading]    = useState(true)
  const [kbQuery,    setKbQuery]    = useState('')
  const [kbResults,  setKbResults]  = useState<string[]>([])
  const [kbSearching,setKbSearching]= useState(false)
  const [reloading,  setReloading]  = useState(false)
  const [toast,      setToast]      = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const [h, ml, m, kb, eq] = await Promise.allSettled([
        getHealth(),
        getMLModelInfo(),
        getActiveModels(),
        getKBStats(),
        getEarthquakes(),
      ])
      if (h.status  === 'fulfilled') setHealth(h.value)
      if (ml.status === 'fulfilled') setMlInfo(ml.value)
      if (m.status  === 'fulfilled') setModels(m.value.models)
      if (kb.status === 'fulfilled') setKbStats(kb.value)
      if (eq.status === 'fulfilled') setEarthquakes(eq.value as EqData[])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void loadAll() }, [loadAll])

  const handleReloadKB = async () => {
    setReloading(true)
    try {
      await reloadKB()
      const kb = await getKBStats()
      setKbStats(kb)
      showToast('Knowledge base berhasil di-reload!')
    } catch {
      showToast('Gagal reload knowledge base')
    } finally {
      setReloading(false)
    }
  }

  const handleSearchKB = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!kbQuery.trim()) return
    setKbSearching(true)
    try {
      const res = await searchKB(kbQuery)
      setKbResults(res.results ?? [])
    } catch {
      setKbResults([])
    } finally {
      setKbSearching(false)
    }
  }

  const services = health?.services
    ? Object.entries(health.services).filter(([k]) => k !== 'llm_models')
    : []

  const llmInfo = health?.services?.llm_models as Record<string, unknown> | undefined

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-slate-800 text-white px-4 py-2.5 rounded-xl shadow-lg text-sm animate-fade-in">
          {toast}
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/"
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Kembali ke App
            </Link>
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <span className="text-lg">🛡️</span>
              <div>
                <h1 className="text-sm font-bold text-slate-800 leading-tight">Admin Dashboard</h1>
                <p className="text-xs text-slate-400 leading-tight">SiagaAI System Monitor</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {health && (
              <span className={cn(
                'inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium border',
                health.status === 'healthy'
                  ? 'bg-green-50 text-green-700 border-green-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              )}>
                <span className={cn('w-1.5 h-1.5 rounded-full',
                  health.status === 'healthy' ? 'bg-green-500' : 'bg-amber-500'
                )} />
                {health.status === 'healthy' ? 'System Healthy' : 'Degraded'}
              </span>
            )}
            <button onClick={loadAll} disabled={loading}
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
              <RefreshCw className={cn('w-3.5 h-3.5', loading && 'animate-spin')} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">

        {/* ── Stat Cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={<Brain className="w-5 h-5 text-white" />}
            title="ML Accuracy" color="bg-indigo-500"
            value={mlInfo ? `${(mlInfo.accuracy * 100).toFixed(1)}%` : '–'}
            sub={mlInfo ? `F1: ${mlInfo.f1_score_weighted}` : 'Model not loaded'}
            loading={loading}
          />
          <StatCard
            icon={<Database className="w-5 h-5 text-white" />}
            title="Knowledge Base" color="bg-teal-500"
            value={kbStats ? kbStats.total_documents : '–'}
            sub="Dokumen RAG"
            loading={loading}
          />
          <StatCard
            icon={<Zap className="w-5 h-5 text-white" />}
            title="LLM Models Aktif" color="bg-amber-500"
            value={models.length}
            sub={`Default: ${llmInfo?.default as string ?? '–'}`}
            loading={loading}
          />
          <StatCard
            icon={<Activity className="w-5 h-5 text-white" />}
            title="Environment" color="bg-slate-600"
            value={health?.environment ?? '–'}
            sub={`v${health?.version ?? '–'}`}
            loading={loading}
          />
        </div>

        {/* ── Row 2: Services + ML Model ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Service Status */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-slate-800 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-500" />
                Service Status
              </h2>
              <span className="text-xs text-slate-400">
                {health?.timestamp ? formatDate(health.timestamp) : '–'}
              </span>
            </div>
            <div className="space-y-2">
              {loading
                ? [1,2,3,4].map(i => (
                    <div key={i} className="h-9 bg-slate-100 rounded-xl animate-pulse" />
                  ))
                : services.map(([name, status]) => (
                    <ServiceBadge key={name} name={name} status={status} />
                  ))
              }
              {!loading && services.length === 0 && (
                <p className="text-sm text-slate-400 text-center py-4">
                  Backend tidak tersambung
                </p>
              )}
            </div>
          </div>

          {/* ML Model Info */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2 mb-4">
              <Brain className="w-4 h-4 text-indigo-500" />
              Custom ML Model
            </h2>
            {loading ? (
              <div className="space-y-2">
                {[1,2,3,4].map(i => <div key={i} className="h-8 bg-slate-100 rounded-lg animate-pulse" />)}
              </div>
            ) : mlInfo ? (
              <div className="space-y-2">
                {[
                  ['Tipe','RandomForestClassifier'],
                  ['Versi', mlInfo.model_version],
                  ['Accuracy', `${(mlInfo.accuracy * 100).toFixed(1)}%`],
                  ['F1-Score (weighted)', mlInfo.f1_score_weighted?.toString() ?? '–'],
                  ['F1-Score (macro)', mlInfo.f1_score_macro?.toString() ?? '–'],
                  ['ROC-AUC', mlInfo.roc_auc?.toString() ?? '–'],
                  ['Total Training Samples', mlInfo.total_training_samples?.toLocaleString() ?? '–'],
                  ['Jumlah Features', `${mlInfo.n_features} fitur`],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
                    <span className="text-xs text-slate-500">{k}</span>
                    <span className="text-xs font-semibold text-slate-700">{v}</span>
                  </div>
                ))}
                {/* Top features */}
                {mlInfo.top5_features && mlInfo.top5_features.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-slate-100">
                    <p className="text-xs font-medium text-slate-500 mb-2">Top 5 Features:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {mlInfo.top5_features.map((f: string) => (
                        <span key={f} className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full border border-indigo-100">
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-400 text-center py-4">Model belum loaded</p>
            )}
          </div>
        </div>

        {/* ── Row 3: LLM Models + Earthquakes ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* LLM Models */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-amber-500" />
              LLM Models Aktif
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full ml-auto">
                {models.length} model
              </span>
            </h2>
            <div className="space-y-2">
              {loading
                ? [1,2,3].map(i => <div key={i} className="h-14 bg-slate-100 rounded-xl animate-pulse" />)
                : models.length === 0
                ? <p className="text-sm text-slate-400 text-center py-4">Tidak ada model aktif</p>
                : models.map(m => (
                    <div key={m.model_id}
                      className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div>
                        <p className="text-sm font-medium text-slate-800">{m.display_name}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-slate-400">{m.provider}</span>
                          <span className="text-xs text-slate-300">·</span>
                          <span className="text-xs text-slate-400">
                            {(m.context_window/1000).toFixed(0)}K ctx
                          </span>
                        </div>
                      </div>
                      <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium',
                        m.is_free
                          ? 'bg-green-100 text-green-700'
                          : 'bg-slate-100 text-slate-600'
                      )}>
                        {m.is_free ? 'Gratis' : 'Berbayar'}
                      </span>
                    </div>
                  ))
              }
            </div>
          </div>

          {/* Gempa Terkini */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2 mb-4">
              <Shield className="w-4 h-4 text-red-500" />
              Gempa Terkini — BMKG
            </h2>
            <div className="space-y-2">
              {loading
                ? [1,2,3].map(i => <div key={i} className="h-12 bg-slate-100 rounded-xl animate-pulse" />)
                : earthquakes.length === 0
                ? <p className="text-sm text-slate-400 text-center py-4">Tidak ada data gempa</p>
                : earthquakes.slice(0, 5).map((eq, i) => (
                    <div key={i}
                      className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div className={cn(
                        'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold',
                        parseFloat(eq.magnitude ?? '0') >= 5
                          ? 'bg-red-100 text-red-700'
                          : parseFloat(eq.magnitude ?? '0') >= 3
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-slate-100 text-slate-600'
                      )}>
                        M{eq.magnitude ?? '?'}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-slate-700 truncate">
                          {eq.location ?? eq.summary}
                        </p>
                        {eq.date && (
                          <p className="text-xs text-slate-400">{eq.date}</p>
                        )}
                      </div>
                    </div>
                  ))
              }
            </div>
          </div>
        </div>

        {/* ── Knowledge Base Management ── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2">
              <Database className="w-4 h-4 text-teal-500" />
              Knowledge Base Management
            </h2>
            <div className="flex items-center gap-2">
              {kbStats && (
                <span className="text-xs text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                  {kbStats.total_documents} dokumen di ChromaDB
                </span>
              )}
              <button
                onClick={handleReloadKB}
                disabled={reloading}
                className="flex items-center gap-1.5 text-sm px-3 py-1.5 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-300 text-white rounded-xl transition-colors"
              >
                <RefreshCw className={cn('w-3.5 h-3.5', reloading && 'animate-spin')} />
                {reloading ? 'Reloading…' : 'Reload KB'}
              </button>
            </div>
          </div>

          {/* Search KB */}
          <form onSubmit={handleSearchKB} className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={kbQuery}
                onChange={e => setKbQuery(e.target.value)}
                placeholder="Test semantic search di knowledge base…"
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <button type="submit" disabled={kbSearching || !kbQuery.trim()}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-xl text-sm transition-colors">
              {kbSearching ? 'Searching…' : 'Search'}
            </button>
            {kbResults.length > 0 && (
              <button type="button" onClick={() => { setKbResults([]); setKbQuery('') }}
                className="p-2.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl">
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </form>

          {/* Search Results */}
          {kbResults.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-slate-500">
                {kbResults.length} dokumen ditemukan:
              </p>
              {kbResults.map((doc, i) => (
                <div key={i} className="p-3 bg-teal-50 border border-teal-100 rounded-xl">
                  <p className="text-xs text-slate-700 leading-relaxed line-clamp-3">
                    {typeof doc === 'string' ? doc : JSON.stringify(doc).slice(0, 200) + '…'}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* KB Info grid */}
          {kbStats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-2">
              {[
                ['Total Dokumen', kbStats.total_documents],
                ['Koleksi', kbStats.collection_name ?? 'siagaai_knowledge'],
                ['Vector DB', 'ChromaDB'],
                ['Embedding', 'all-MiniLM-L6-v2'],
              ].map(([k, v]) => (
                <div key={k as string} className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                  <p className="text-xs text-slate-400 mb-1">{k as string}</p>
                  <p className="text-sm font-semibold text-slate-700 truncate">{String(v)}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Per-Class ML Metrics ── */}
        {mlInfo?.per_class_metrics && Object.keys(mlInfo.per_class_metrics).length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2 mb-4">
              <BarChart3 className="w-4 h-4 text-indigo-500" />
              Performa ML Per Kelas — Test Set
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    {['Kelas','Precision','Recall','F1-Score','Support'].map(h => (
                      <th key={h} className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(mlInfo.per_class_metrics).map(([cls, m]: [string, unknown], i) => {
                    const metrics = m as Record<string, number>
                    const colors: Record<string,string> = {
                      aman:'text-green-700 bg-green-50 border-green-200',
                      waspada:'text-amber-700 bg-amber-50 border-amber-200',
                      siaga:'text-orange-700 bg-orange-50 border-orange-200',
                      awas:'text-red-700 bg-red-50 border-red-200',
                    }
                    return (
                      <tr key={cls} className={cn('border-b border-slate-50', i%2===0?'bg-white':'bg-slate-50/50')}>
                        <td className="py-2.5 px-3">
                          <span className={cn('inline-flex px-2 py-0.5 rounded-full text-xs font-semibold border', colors[cls] ?? 'bg-gray-100 text-gray-700')}>
                            {cls}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-700 font-medium">{metrics.precision?.toFixed(4) ?? '–'}</td>
                        <td className="py-2.5 px-3 text-slate-700 font-medium">{metrics.recall?.toFixed(4) ?? '–'}</td>
                        <td className="py-2.5 px-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full bg-indigo-500 rounded-full"
                                style={{ width: `${(metrics.f1 ?? 0) * 100}%` }} />
                            </div>
                            <span className="text-slate-700 font-medium text-xs w-12">{metrics.f1?.toFixed(4) ?? '–'}</span>
                          </div>
                        </td>
                        <td className="py-2.5 px-3 text-slate-500">{metrics.support?.toLocaleString() ?? '–'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center py-4">
          <p className="text-xs text-slate-400">
            SiagaAI Admin Dashboard · PJK-GM011 · DCamp 2025 × IBM Skillsbuild
          </p>
        </div>
      </main>
    </div>
  )
}
