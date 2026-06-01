import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { UserLocation, ChatMessage, ChatSession, RiskLevel, LLMModel } from '@/types'

// ─── Location Store ──────────────────────────────────────────
interface LocationStore {
  location: UserLocation | null
  overallRisk: RiskLevel
  isDetecting: boolean
  error: string | null
  setLocation: (loc: UserLocation) => void
  setOverallRisk: (r: RiskLevel) => void
  setDetecting: (v: boolean) => void
  setError: (e: string | null) => void
  clear: () => void
}

export const useLocationStore = create<LocationStore>((set) => ({
  location:    null,
  overallRisk: 'aman',
  isDetecting: false,
  error:       null,
  setLocation:     (loc) => set({ location: loc, error: null }),
  setOverallRisk:  (r)   => set({ overallRisk: r }),
  setDetecting:    (v)   => set({ isDetecting: v }),
  setError:        (e)   => set({ error: e }),
  clear: () => set({ location: null, overallRisk: 'aman', error: null, isDetecting: false }),
}))

// ─── Chat Store ──────────────────────────────────────────────
interface ChatStore {
  session:   ChatSession | null
  messages:  ChatMessage[]
  isLoading: boolean
  isSOS:     boolean
  setSession:          (s: ChatSession) => void
  addMessage:          (m: ChatMessage) => void
  updateLastAssistant: (content: string, extra?: Partial<ChatMessage>) => void
  setLoading:          (v: boolean) => void
  setIsSOS:            (v: boolean) => void
  clearChat:           () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  session:   null,
  messages:  [],
  isLoading: false,
  isSOS:     false,
  setSession: (s) => set({ session: s }),
  addMessage: (m) => set((st) => ({ messages: [...st.messages, m] })),
  updateLastAssistant: (content, extra = {}) =>
    set((st) => {
      const msgs = [...st.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content, isStreaming: false, ...extra }
      }
      return { messages: msgs }
    }),
  setLoading: (v) => set({ isLoading: v }),
  setIsSOS:   (v) => set({ isSOS: v }),
  clearChat:  ()  => set({ messages: [], session: null, isLoading: false, isSOS: false }),
}))

// ─── Settings Store (persisted) ──────────────────────────────
// skipHydration mencegah SSR mismatch di Next.js 14
interface SettingsStore {
  selectedModel:   string
  availableModels: LLMModel[]
  _hasHydrated:    boolean
  setModel:          (m: string) => void
  setAvailableModels:(ms: LLMModel[]) => void
  setHasHydrated:   (v: boolean) => void
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      selectedModel:   'llama-3.3-70b-versatile',
      availableModels: [],
      _hasHydrated:    false,
      setModel:           (m)  => set({ selectedModel: m }),
      setAvailableModels: (ms) => set({ availableModels: ms }),
      setHasHydrated:     (v)  => set({ _hasHydrated: v }),
    }),
    {
      name:    'siagaai-settings',
      storage: createJSONStorage(() =>
        typeof window !== 'undefined' ? localStorage : { getItem: () => null, setItem: () => {}, removeItem: () => {} }
      ),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)
