'use client'
import { useState } from 'react'
import { X, AlertTriangle, Phone, Loader2, CheckCircle } from 'lucide-react'
import { useLocationStore } from '@/lib/store'
import { escalateEmergency } from '@/lib/api'

interface Props {
  sessionId: string
  onClose: () => void
}

const EMERGENCY_NUMBERS = [
  { name: 'BNPB', number: '119', desc: 'Badan Nasional Penanggulangan Bencana' },
  { name: 'Darurat', number: '112', desc: 'Layanan Darurat Nasional' },
  { name: 'Ambulans', number: '118', desc: 'Emergency Medical Service' },
  { name: 'SAR', number: '115', desc: 'SAR Nasional (BASARNAS)' },
]

export function SOSModal({ sessionId, onClose }: Props) {
  const { location } = useLocationStore()
  const [situation, setSituation] = useState('')
  const [contactName, setContactName] = useState('')
  const [contactPhone, setContactPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!situation.trim() || !location) return
    setLoading(true)
    setError(null)
    try {
      const result = await escalateEmergency({
        session_id: sessionId,
        location,
        situation: situation.trim(),
        contact_name: contactName || undefined,
        contact_phone: contactPhone || undefined,
      })
      setDone(result.escalation_id)
    } catch {
      setError('Gagal mengirim laporan. Coba lagi atau hubungi 112 langsung.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-red-600 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-bold text-lg">LAPORAN DARURAT SOS</span>
          </div>
          <button onClick={onClose} className="text-red-200 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {done ? (
          /* Success state */
          <div className="p-6 text-center">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <h3 className="font-bold text-slate-800 text-lg mb-1">Laporan Terkirim!</h3>
            <p className="text-slate-500 text-sm mb-1">ID Laporan: <span className="font-mono font-semibold">{done}</span></p>
            <p className="text-slate-500 text-sm mb-5">Segera hubungi juga nomor darurat berikut:</p>
            <div className="grid grid-cols-2 gap-2 mb-5">
              {EMERGENCY_NUMBERS.map(n => (
                <a key={n.number} href={`tel:${n.number}`}
                  className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl hover:bg-red-100 transition-colors">
                  <Phone className="w-4 h-4 text-red-600" />
                  <div className="text-left">
                    <p className="text-sm font-bold text-red-700">{n.number}</p>
                    <p className="text-xs text-red-500">{n.name}</p>
                  </div>
                </a>
              ))}
            </div>
            <button onClick={onClose}
              className="w-full py-3 bg-slate-800 text-white rounded-xl font-semibold hover:bg-slate-700 transition-colors">
              Tutup
            </button>
          </div>
        ) : (
          /* Form state */
          <div className="p-5 space-y-4">
            {/* Emergency numbers quick access */}
            <div className="grid grid-cols-4 gap-2">
              {EMERGENCY_NUMBERS.map(n => (
                <a key={n.number} href={`tel:${n.number}`}
                  className="flex flex-col items-center p-2 bg-red-50 border border-red-200 rounded-xl hover:bg-red-100 transition-colors">
                  <Phone className="w-4 h-4 text-red-600 mb-0.5" />
                  <span className="text-sm font-bold text-red-700">{n.number}</span>
                  <span className="text-xs text-red-500">{n.name}</span>
                </a>
              ))}
            </div>

            {location && (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-600">
                📍 Lokasi: <span className="font-semibold">{location.display_name}</span>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Deskripsi Situasi <span className="text-red-500">*</span>
              </label>
              <textarea
                value={situation}
                onChange={e => setSituation(e.target.value)}
                rows={3}
                placeholder="Contoh: Banjir setinggi 1 meter, 4 orang terjebak termasuk 1 balita..."
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Nama (opsional)</label>
                <input type="text" value={contactName} onChange={e => setContactName(e.target.value)}
                  placeholder="Nama Anda"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">No. HP (opsional)</label>
                <input type="tel" value={contactPhone} onChange={e => setContactPhone(e.target.value)}
                  placeholder="08xxxxxxxxxx"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500" />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">{error}</div>
            )}

            <button
              onClick={handleSubmit}
              disabled={!situation.trim() || loading}
              className="w-full py-3.5 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-bold rounded-xl flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <AlertTriangle className="w-5 h-5" />}
              {loading ? 'Mengirim laporan...' : 'Kirim Laporan Darurat'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
