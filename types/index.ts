// ═══════════════════════════════════════════════════════════
//  SiagaAI — Global Type Definitions
// ═══════════════════════════════════════════════════════════

export type RiskLevel = 'aman' | 'waspada' | 'siaga' | 'awas'

export const RISK_CONFIG: Record<RiskLevel, {
  label: string; color: string; bg: string; border: string;
  emoji: string; textColor: string;
}> = {
  aman:    { label: 'Aman',    color: '#16a34a', bg: '#f0fdf4', border: '#86efac', emoji: '✅', textColor: 'text-green-700' },
  waspada: { label: 'Waspada', color: '#d97706', bg: '#fffbeb', border: '#fcd34d', emoji: '⚠️', textColor: 'text-amber-700' },
  siaga:   { label: 'Siaga',   color: '#ea580c', bg: '#fff7ed', border: '#fdba74', emoji: '🔶', textColor: 'text-orange-700' },
  awas:    { label: 'Awas!',   color: '#dc2626', bg: '#fef2f2', border: '#fca5a5', emoji: '🚨', textColor: 'text-red-700' },
}

// ─── Location ──────────────────────────────────────────────
export interface UserLocation {
  lat: number; lng: number
  city: string; province: string; display_name: string
}

export interface WeatherData {
  temperature: number; humidity: number
  condition: string; icon?: string
  wind_speed: number; rainfall_1h: number; city_name: string
}

export interface EarthquakeData {
  magnitude?: string; depth?: string; location?: string
  date?: string; time?: string; felt?: string
  summary: string
}

export interface DisasterRisk {
  type: string; level: RiskLevel
  description: string; recommended_action: string
}

export interface LocationStatus {
  location: UserLocation; weather: WeatherData
  earthquake: EarthquakeData; risks: DisasterRisk[]
  overall_risk: RiskLevel; summary: string; updated_at: string
}

// ─── ML ────────────────────────────────────────────────────
export interface FeatureImportance {
  feature: string; importance: number
  value: number; direction: string
}

export interface FloodPrediction {
  risk_level: RiskLevel; risk_score: number
  probabilities: Record<string, number>
  top_features: FeatureImportance[]
  model_version: string; confidence: string; message: string
}

export interface MLModelInfo {
  model_type: string; model_version: string
  trained_at: string; accuracy: number; f1_score: number
  classes: string[]; feature_names: string[]
  total_training_samples: number; is_loaded: boolean
}

// ─── Chat ──────────────────────────────────────────────────
export type MessageRole = 'user' | 'assistant'

export type MessageIntent =
  | 'prediction' | 'evacuation' | 'first_aid'
  | 'emergency'  | 'education'  | 'general'

export const INTENT_CONFIG: Record<MessageIntent, {
  label: string; emoji: string; color: string
}> = {
  prediction: { label: 'Prediksi', emoji: '📊', color: 'bg-blue-100 text-blue-700' },
  evacuation: { label: 'Evakuasi', emoji: '🚶', color: 'bg-orange-100 text-orange-700' },
  first_aid:  { label: 'P3K',      emoji: '🩺', color: 'bg-red-100 text-red-700' },
  emergency:  { label: 'DARURAT',  emoji: '🆘', color: 'bg-red-200 text-red-800 font-bold' },
  education:  { label: 'Edukasi',  emoji: '📚', color: 'bg-purple-100 text-purple-700' },
  general:    { label: 'Umum',     emoji: '💬', color: 'bg-gray-100 text-gray-700' },
}

export interface ChatMessage {
  id: string; role: MessageRole; content: string
  intent?: MessageIntent; model_used?: string
  requires_escalation?: boolean
  suggested_actions?: string[]
  timestamp: string; isStreaming?: boolean
}

export interface ChatSession {
  session_id: string; city?: string; province?: string
  model_name?: string; created_at: string; message_count?: number
}

// ─── LLM Models ────────────────────────────────────────────
export interface LLMModel {
  model_id: string; display_name: string; provider: string
  context_window: number; is_free: boolean; is_active: boolean
  description: string; tags: string[]
}

// ─── API Responses ─────────────────────────────────────────
export interface ApiResponse<T> {
  success: boolean; data: T; message?: string
}
