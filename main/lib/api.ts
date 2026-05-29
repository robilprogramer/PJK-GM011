import axios from 'axios'
import type {
  ApiResponse, UserLocation, LocationStatus,
  ChatSession, LLMModel, FloodPrediction, MLModelInfo,
} from '@/types'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err?.response?.data?.error || err?.message || 'Network error'
    return Promise.reject(new Error(msg))
  }
)

// ─── Location ────────────────────────────────────────────────
export const getLocationStatus = async (loc: UserLocation): Promise<LocationStatus> => {
  const { data } = await api.post<ApiResponse<LocationStatus>>('/api/location/status', {
    lat: loc.lat, lng: loc.lng,
    city: loc.city, province: loc.province,
    display_name: loc.display_name,
  })
  return data.data
}

export const geocodeCity = async (city: string): Promise<UserLocation> => {
  const { data } = await api.get<ApiResponse<UserLocation>>('/api/location/geocode', {
    params: { city },
  })
  return data.data
}

export const reverseGeocode = async (lat: number, lng: number): Promise<UserLocation> => {
  const { data } = await api.get<ApiResponse<UserLocation>>('/api/location/reverse', {
    params: { lat, lng },
  })
  return data.data
}

export const getEarthquakes = async (limit = 5) => {
  const { data } = await api.get<ApiResponse<unknown[]>>('/api/location/earthquakes', {
    params: { limit },
  })
  return data.data
}

// ─── Chat ─────────────────────────────────────────────────────
export const createSession = async (
  location?: UserLocation | null,
  modelName?: string
): Promise<ChatSession> => {
  const payload: Record<string, unknown> = { model_name: modelName }
  if (location) {
    payload.location = {
      lat: location.lat, lng: location.lng,
      city: location.city, province: location.province,
      display_name: location.display_name,
    }
  }
  const { data } = await api.post<ApiResponse<ChatSession>>('/api/chat/sessions', payload)
  return data.data
}

export const sendMessage = async (payload: {
  message:    string
  session_id: string
  location?:  UserLocation | null
  history:    { role: string; content: string }[]
  model_name?: string
}) => {
  const body: Record<string, unknown> = {
    message:    payload.message,
    session_id: payload.session_id,
    history:    payload.history,
    model_name: payload.model_name,
  }
  if (payload.location) {
    body.location = {
      lat:          payload.location.lat,
      lng:          payload.location.lng,
      city:         payload.location.city,
      province:     payload.location.province,
      display_name: payload.location.display_name,
    }
  }
  const { data } = await api.post<ApiResponse<{
    reply: string; intent: string; session_id: string
    model_used: string; requires_escalation: boolean
    suggested_actions: string[]; message_id: string
  }>>('/api/chat/send', body)
  return data.data
}

export const getChatHistory = async (sessionId: string) => {
  const { data } = await api.get<ApiResponse<{
    session_id: string; messages: unknown[]; total: number
  }>>(`/api/chat/sessions/${sessionId}/history`)
  return data.data
}

export const closeSession = async (sessionId: string) => {
  await api.delete(`/api/chat/sessions/${sessionId}`)
}

// ─── LLM Models ───────────────────────────────────────────────
export const getActiveModels = async (): Promise<{
  models: LLMModel[]; default_model: string; total: number; total_active: number
}> => {
  const { data } = await api.get<ApiResponse<{
    models: LLMModel[]; default_model: string; total: number; total_active: number
  }>>('/api/models/active')
  return data.data
}

// ─── ML Model — predict-auto ──────────────────────────────────
// Sinkron: backend fetch OWM dulu → ML predictor
// Frontend cukup kirim koordinat + nama kota
export const predictFloodAuto = async (loc: UserLocation): Promise<FloodPrediction> => {
  const { data } = await api.post<ApiResponse<FloodPrediction>>('/api/ml/predict-auto', {
    lat:          loc.lat,
    lng:          loc.lng,
    city:         loc.city,
    province:     loc.province,
    display_name: loc.display_name,
  })
  return data.data
}

export const getMLModelInfo = async (): Promise<MLModelInfo> => {
  const { data } = await api.get<ApiResponse<MLModelInfo>>('/api/ml/model-info')
  return data.data
}

// ─── Escalation ───────────────────────────────────────────────
export const escalateEmergency = async (payload: {
  session_id:   string
  location:     UserLocation
  situation:    string
  contact_name?:  string
  contact_phone?: string
}): Promise<{
  escalation_id: string; message: string
  emergency_numbers: Record<string, string>
}> => {
  const { data } = await api.post<ApiResponse<{
    escalation_id: string; message: string
    emergency_numbers: Record<string, string>
  }>>('/api/escalate', {
    session_id:    payload.session_id,
    situation:     payload.situation,
    contact_name:  payload.contact_name,
    contact_phone: payload.contact_phone,
    location: {
      lat:          payload.location.lat,
      lng:          payload.location.lng,
      city:         payload.location.city,
      province:     payload.location.province,
      display_name: payload.location.display_name,
    },
  })
  return data.data
}

export const getHealth = async () => {
  const { data } = await api.get('/api/health')
  return data
}

export default api
