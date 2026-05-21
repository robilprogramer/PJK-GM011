'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
import { AlertTriangle } from 'lucide-react'

import { LocationSetup } from '@/components/location/LocationSetup'
import { WeatherCard } from '@/components/location/WeatherCard'
import { MLPredictionCard } from '@/components/location/MLPredictionCard'
import { ChatBubble } from '@/components/chat/ChatBubble'
import { ChatInput } from '@/components/chat/ChatInput'
import { SOSModal } from '@/components/chat/SOSModal'
import { AppHeader } from '@/components/layout/AppHeader'

import { useLocationStore, useChatStore, useSettingsStore } from '@/lib/store'
import {
  getLocationStatus, predictFloodAuto,
  createSession, sendMessage, closeSession,
} from '@/lib/api'
import type { LocationStatus, FloodPrediction, ChatMessage } from '@/types'
import { generateId } from '@/lib/utils'

export default function Home() {
  const { location, setOverallRisk, clear: clearLocation } = useLocationStore()
  const {
    session, messages, isLoading, isSOS,
    setSession, addMessage, updateLastAssistant, setLoading, setIsSOS, clearChat,
  } = useChatStore()
  const { selectedModel } = useSettingsStore()

  const [locationStatus, setLocationStatus] = useState<LocationStatus | null>(null)
  const [mlPrediction, setMlPrediction] = useState<FloodPrediction | null>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [changeLocation, setChangeLocation] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Fetch status when location changes
  useEffect(() => {
    if (!location) return
    fetchLocationData()
    initSession()
  }, [location])

  const fetchLocationData = async () => {
    if (!location) return
    setStatusLoading(true)
    try {
      const [status, ml] = await Promise.allSettled([
        getLocationStatus(location),
        predictFloodAuto(location),
      ])
      if (status.status === 'fulfilled') {
        setLocationStatus(status.value)
        setOverallRisk(status.value.overall_risk)
      }
      if (ml.status === 'fulfilled') setMlPrediction(ml.value)
    } catch { /* silent */ }
    finally { setStatusLoading(false) }
  }

  const initSession = async () => {
    if (!location) return
    try {
      // Close old session
      if (session) await closeSession(session.session_id).catch(() => {})
      clearChat()
      const s = await createSession(location, selectedModel)
      setSession(s)

      // Welcome message
      const welcomeRisk = locationStatus?.overall_risk || 'aman'
      const welcomeContent = `Halo! Saya **SiagaAI** 👋\n\nSaya sudah mendeteksi lokasi Anda di **${location.city}, ${location.province}**.\n\nSilakan tanyakan apa saja seputar kondisi bencana, panduan evakuasi, atau pertolongan pertama. Saya siap membantu! 🚀`
      addMessage({
        id: generateId(), role: 'assistant',
        content: welcomeContent, intent: 'general',
        timestamp: new Date().toISOString(),
      })
    } catch { /* silent */ }
  }

  const handleSend = useCallback(async (text: string) => {
    if (!session || isLoading) return

    const userMsg: ChatMessage = {
      id: generateId(), role: 'user',
      content: text, timestamp: new Date().toISOString(),
    }
    addMessage(userMsg)

    // Streaming placeholder
    const assistantId = generateId()
    addMessage({
      id: assistantId, role: 'assistant',
      content: '', isStreaming: true,
      timestamp: new Date().toISOString(),
    })
    setLoading(true)

    try {
      const history = messages
        .filter(m => !m.isStreaming)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }))

      const res = await sendMessage({
        message: text,
        session_id: session.session_id,
        location,
        history,
        model_name: selectedModel,
      })

      updateLastAssistant(res.reply, {
        intent: res.intent as any,
        model_used: res.model_used,
        requires_escalation: res.requires_escalation,
        suggested_actions: res.suggested_actions,
      })

      if (res.requires_escalation) setIsSOS(true)
    } catch (e: any) {
      updateLastAssistant(
        'Maaf, terjadi kesalahan. Pastikan backend berjalan dan coba lagi.',
        { intent: 'general' }
      )
    } finally {
      setLoading(false)
    }
  }, [session, isLoading, messages, location, selectedModel])

  // ── Not yet set location ──────────────────────────────────
  if (!location || changeLocation) {
    return (
      <div className="min-h-screen">
        <div className="max-w-lg mx-auto px-4 py-8">
          {changeLocation && (
            <button
              onClick={() => setChangeLocation(false)}
              className="mb-4 text-sm text-blue-600 hover:underline"
            >
              ← Kembali ke chat
            </button>
          )}
          <LocationSetup />
        </div>
      </div>
    )
  }

  // ── Main App ──────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col">
      <AppHeader onChangeLocation={() => setChangeLocation(true)} />

      <div className="flex-1 flex max-w-6xl mx-auto w-full px-4 py-4 gap-4">
        {/* LEFT: Sidebar cards */}
        <aside className="hidden lg:flex flex-col gap-4 w-80 flex-shrink-0">
          {locationStatus && (
            <WeatherCard
              status={locationStatus}
              onRefresh={fetchLocationData}
              isLoading={statusLoading}
            />
          )}
          {mlPrediction && <MLPredictionCard prediction={mlPrediction} />}

          {/* Risk alert banner */}
          {locationStatus && ['siaga','awas'].includes(locationStatus.overall_risk) && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-red-700 font-semibold mb-1">
                <AlertTriangle className="w-4 h-4" />
                Peringatan Aktif
              </div>
              <p className="text-sm text-red-600">{locationStatus.summary}</p>
            </div>
          )}
        </aside>

        {/* RIGHT: Chat */}
        <main className="flex-1 flex flex-col min-h-0">
          {/* Mobile weather strip */}
          {locationStatus && (
            <div className="lg:hidden mb-3">
              <WeatherCard status={locationStatus} onRefresh={fetchLocationData} isLoading={statusLoading} />
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
          <div className="mb-3">
            <button
              onClick={() => setIsSOS(true)}
              className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl flex items-center justify-center gap-2 transition-colors shadow-sm text-sm"
            >
              <AlertTriangle className="w-4 h-4" />
              🆘 PANIC BUTTON — Laporkan Situasi Darurat
            </button>
          </div>

          {/* Chat Input */}
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
