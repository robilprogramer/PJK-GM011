'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
import { AlertTriangle } from 'lucide-react'

import { LocationSetup }      from '@/components/location/LocationSetup'
import { WeatherCard }        from '@/components/location/WeatherCard'
import { MLPredictionCard }   from '@/components/location/MLPredictionCard'
import { ChatBubble }         from '@/components/chat/ChatBubble'
import { ChatInput }          from '@/components/chat/ChatInput'
import { SOSModal }           from '@/components/chat/SOSModal'
import { AppHeader }          from '@/components/layout/AppHeader'

import { useLocationStore, useChatStore, useSettingsStore } from '@/lib/store'
import {
  getLocationStatus, predictFloodAuto,
  createSession, sendMessage, closeSession,
} from '@/lib/api'
import type { LocationStatus, FloodPrediction, ChatMessage } from '@/types'
import { generateId } from '@/lib/utils'

export default function Home() {
  const {
    location, setOverallRisk, clear: clearLocation,
  } = useLocationStore()
  const {
    session, messages, isLoading, isSOS,
    setSession, addMessage, updateLastAssistant,
    setLoading, setIsSOS, clearChat,
  } = useChatStore()
  const { selectedModel } = useSettingsStore()

  const [locationStatus,  setLocationStatus]  = useState<LocationStatus | null>(null)
  const [mlPrediction,    setMlPrediction]    = useState<FloodPrediction | null>(null)
  const [statusLoading,   setStatusLoading]   = useState(false)
  const [changeLocation,  setChangeLocation]  = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const sessionRef     = useRef(session)
  sessionRef.current   = session

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Fetch real-time data + init chat saat lokasi berubah
  useEffect(() => {
    if (!location) return
    void fetchAll()
    void initSession()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location?.lat, location?.lng])

  // ─── Fetch cuaca + ML prediction ──────────────────────────
  const fetchAll = useCallback(async () => {
    if (!location) return
    setStatusLoading(true)
    try {
      // Paralel: location status (cuaca+risiko) + ML predict-auto (OWM→ML)
      const [statusRes, mlRes] = await Promise.allSettled([
        getLocationStatus(location),
        predictFloodAuto(location),
      ])
      if (statusRes.status === 'fulfilled') {
        setLocationStatus(statusRes.value)
        setOverallRisk(statusRes.value.overall_risk)
      }
      if (mlRes.status === 'fulfilled') {
        setMlPrediction(mlRes.value)
      }
    } finally {
      setStatusLoading(false)
    }
  }, [location, setOverallRisk])

  // ─── Init chat session ────────────────────────────────────
  const initSession = useCallback(async () => {
    if (!location) return
    try {
      if (sessionRef.current) {
        await closeSession(sessionRef.current.session_id).catch(() => {})
      }
      clearChat()
      const s = await createSession(location, selectedModel)
      setSession(s)
      addMessage({
        id:        generateId(),
        role:      'assistant',
        content:   `Halo! Saya **SiagaAI** 👋\n\nSaya sudah mendeteksi lokasi Anda di **${location.city}, ${location.province}**.\n\nTanyakan apa saja seputar kondisi bencana, panduan evakuasi, atau pertolongan pertama. Saya siap membantu! 🚀`,
        intent:    'general',
        timestamp: new Date().toISOString(),
      })
    } catch {
      // silent — user bisa coba lagi
    }
  }, [location, selectedModel, clearChat, setSession, addMessage])

  // ─── Kirim pesan ke chatbot ───────────────────────────────
  const handleSend = useCallback(async (text: string) => {
    const currentSession = sessionRef.current
    if (!currentSession || isLoading) return

    const userMsg: ChatMessage = {
      id:        generateId(),
      role:      'user',
      content:   text,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMsg)

    // Placeholder streaming
    addMessage({
      id:          generateId(),
      role:        'assistant',
      content:     '',
      isStreaming: true,
      timestamp:   new Date().toISOString(),
    })
    setLoading(true)

    try {
      const history = messages
        .filter(m => !m.isStreaming && m.content)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }))

      const res = await sendMessage({
        message:    text,
        session_id: currentSession.session_id,
        location,
        history,
        model_name: selectedModel,
      })

      updateLastAssistant(res.reply, {
        intent:              res.intent as ChatMessage['intent'],
        model_used:          res.model_used,
        requires_escalation: res.requires_escalation,
        suggested_actions:   res.suggested_actions,
      })

      if (res.requires_escalation) setIsSOS(true)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Terjadi kesalahan'
      updateLastAssistant(
        `Maaf, terjadi kesalahan: ${msg}\n\nPastikan backend berjalan di ${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}`,
        { intent: 'general' }
      )
    } finally {
      setLoading(false)
    }
  }, [
    isLoading, messages, location, selectedModel,
    addMessage, updateLastAssistant, setLoading, setIsSOS,
  ])

  // ─── Belum pilih lokasi ───────────────────────────────────
  if (!location || changeLocation) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-lg mx-auto px-4 py-8">
          {changeLocation && (
            <button
              onClick={() => setChangeLocation(false)}
              className="mb-4 text-sm text-blue-600 hover:underline flex items-center gap-1"
            >
              ← Kembali ke chat
            </button>
          )}
          <LocationSetup />
        </div>
      </div>
    )
  }

  // ─── Main App ─────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <AppHeader onChangeLocation={() => setChangeLocation(true)} />

      <div className="flex-1 flex max-w-6xl mx-auto w-full px-4 py-4 gap-4 min-h-0">

        {/* Sidebar: cuaca + ML (hanya desktop) */}
        <aside className="hidden lg:flex flex-col gap-3 w-72 xl:w-80 flex-shrink-0">
          {locationStatus && (
            <WeatherCard
              status={locationStatus}
              onRefresh={fetchAll}
              isLoading={statusLoading}
            />
          )}
          {mlPrediction && <MLPredictionCard prediction={mlPrediction} />}

          {/* Alert aktif */}
          {locationStatus && ['siaga','awas'].includes(locationStatus.overall_risk) && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 font-semibold text-red-700 mb-1 text-sm">
                <AlertTriangle className="w-4 h-4" />
                Peringatan Aktif
              </div>
              <p className="text-xs text-red-600 leading-relaxed">
                {locationStatus.summary}
              </p>
            </div>
          )}
        </aside>

        {/* Area Chat */}
        <main className="flex-1 flex flex-col min-h-0 min-w-0">
          {/* Weather card mobile */}
          {locationStatus && (
            <div className="lg:hidden mb-3">
              <WeatherCard
                status={locationStatus}
                onRefresh={fetchAll}
                isLoading={statusLoading}
              />
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-1">
            {messages.map(msg => (
              <ChatBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* SOS Button */}
          <div className="mb-2 pt-2">
            <button
              onClick={() => setIsSOS(true)}
              className="w-full py-2.5 bg-red-600 hover:bg-red-700 active:scale-[0.98] text-white font-bold rounded-xl flex items-center justify-center gap-2 transition-all text-sm shadow-sm"
            >
              <AlertTriangle className="w-4 h-4" />
              🆘 PANIC BUTTON — Laporkan Situasi Darurat
            </button>
          </div>

          {/* Input */}
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            disabled={!session}
          />
        </main>
      </div>

      {/* SOS Modal */}
      {isSOS && session && (
        <SOSModal
          sessionId={session.session_id}
          onClose={() => setIsSOS(false)}
        />
      )}
    </div>
  )
}
