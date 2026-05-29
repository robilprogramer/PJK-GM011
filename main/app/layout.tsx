import type { Metadata } from 'next'
import './globals.css'
export const metadata: Metadata = {
  title: 'SiagaAI — Prediksi Bencana Alam Indonesia',
  description: 'AI Chatbot prediksi bencana berbasis lokasi real-time. Data BMKG + Custom ML + Llama 3.3',
}
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="id"><body className="min-h-screen bg-slate-50 text-gray-900 antialiased">{children}</body></html>
}
