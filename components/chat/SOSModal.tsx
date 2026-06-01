'use client'
import { useState } from 'react'
import { X, AlertTriangle, Phone, Loader2, CheckCircle } from 'lucide-react'
import { useLocationStore } from '@/lib/store'
import { escalateEmergency } from '@/lib/api'

interface Props { sessionId: string; onClose: () => void }

const NUMS = [
  { name:'BNPB',    number:'119', color:'bg-red-50 border-red-200 text-red-700' },
  { name:'Darurat', number:'112', color:'bg-red-50 border-red-200 text-red-700' },
  { name:'Ambulans',number:'118', color:'bg-orange-50 border-orange-200 text-orange-700' },
  { name:'SAR',     number:'115', color:'bg-blue-50 border-blue-200 text-blue-700' },
]

export function SOSModal({ sessionId, onClose }: Props) {
  const { location } = useLocationStore()
  const [situation,     setSituation]     = useState('')
  const [contactName,   setContactName]   = useState('')
  const [contactPhone,  setContactPhone]  = useState('')
  const [loading,       setLoading]       = useState(false)
  const [doneId,        setDoneId]        = useState<string|null>(null)
  const [error,         setError]         = useState<string|null>(null)

  const handleSubmit = async () => {
    if (!situation.trim() || !location) return
    setLoading(true); setError(null)
    try {
      const r = await escalateEmergency({
        session_id: sessionId, location, situation: situation.trim(),
        contact_name: contactName || undefined,
        contact_phone: contactPhone || undefined,
      })
      setDoneId(r.escalation_id)
    } catch {
      setError('Gagal mengirim laporan. Hubungi 112 langsung!')
    } finally { setLoading(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-red-600 px-5 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white font-bold">
            <AlertTriangle className="w-5 h-5" />
            LAPORAN DARURAT SOS
          </div>
          <button onClick={onClose} className="text-red-200 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {doneId ? (
          <div className="p-6 text-center">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <h3 className="font-bold text-slate-800 text-lg mb-1">Laporan Terkirim!</h3>
            <p className="text-slate-500 text-sm mb-4">ID: <span className="font-mono font-semibold">{doneId}</span></p>
            <div className="grid grid-cols-2 gap-2 mb-5">
              {NUMS.map(n => (
                <a key={n.number} href={`tel:${n.number}`}
                  className={`flex items-center gap-2 p-3 border rounded-xl ${n.color}`}>
                  <Phone className="w-4 h-4" />
                  <div><p className="text-sm font-bold">{n.number}</p><p className="text-xs">{n.name}</p></div>
                </a>
              ))}
            </div>
            <button onClick={onClose} className="w-full py-3 bg-slate-800 text-white rounded-xl font-semibold">Tutup</button>
          </div>
        ) : (
          <div className="p-5 space-y-3">
            <div className="grid grid-cols-4 gap-2">
              {NUMS.map(n => (
                <a key={n.number} href={`tel:${n.number}`}
                  className={`flex flex-col items-center p-2 border rounded-xl ${n.color}`}>
                  <Phone className="w-3.5 h-3.5 mb-0.5" />
                  <span className="text-sm font-bold">{n.number}</span>
                  <span className="text-xs">{n.name}</span>
                </a>
              ))}
            </div>
            {location && (
              <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-600">
                📍 {location.display_name}
              </div>
            )}
            <textarea
              value={situation} onChange={e => setSituation(e.target.value)} rows={3}
              placeholder="Jelaskan situasi darurat secara singkat…"
              className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
            />
            <div className="grid grid-cols-2 gap-2">
              <input type="text" value={contactName} onChange={e => setContactName(e.target.value)}
                placeholder="Nama (opsional)"
                className="border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
              <input type="tel" value={contactPhone} onChange={e => setContactPhone(e.target.value)}
                placeholder="No. HP (opsional)"
                className="border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>
            {error && <p className="p-2.5 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">{error}</p>}
            <button onClick={handleSubmit} disabled={!situation.trim() || loading}
              className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-bold rounded-xl flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <AlertTriangle className="w-5 h-5" />}
              {loading ? 'Mengirim…' : 'Kirim Laporan Darurat'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
