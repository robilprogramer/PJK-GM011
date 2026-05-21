'use client'
import { useState, useRef, useEffect } from 'react'
import { SendHorizonal, Loader2 } from 'lucide-react'

interface Props {
  onSend: (msg: string) => void
  isLoading: boolean
  disabled?: boolean
}

const SUGGESTIONS = [
  'Apakah aman keluar rumah sekarang?',
  'Bagaimana panduan evakuasi banjir?',
  'Apa isi tas siaga bencana?',
  'Tanda-tanda tanah longsor?',
]

export function ChatInput({ onSend, isLoading, disabled }: Props) {
  const [value, setValue] = useState('')
  const [showSugg, setShowSugg] = useState(true)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 140) + 'px'
    }
  }, [value])

  const handleSend = () => {
    if (!value.trim() || isLoading || disabled) return
    onSend(value.trim())
    setValue('')
    setShowSugg(false)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="space-y-2">
      {/* Quick suggestions */}
      {showSugg && (
        <div className="flex flex-wrap gap-1.5 px-1">
          {SUGGESTIONS.map(s => (
            <button
              key={s}
              onClick={() => { onSend(s); setShowSugg(false) }}
              disabled={isLoading || disabled}
              className="text-xs bg-white border border-slate-200 text-slate-600 px-2.5 py-1.5 rounded-full hover:border-blue-400 hover:text-blue-600 transition-colors disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input box */}
      <div className="flex items-end gap-2 bg-white border border-slate-200 rounded-2xl px-4 py-2.5 shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition-all">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          disabled={isLoading || disabled}
          placeholder="Tanya tentang bencana di lokasi kamu..."
          rows={1}
          className="flex-1 resize-none text-sm text-slate-800 placeholder-slate-400 bg-transparent focus:outline-none disabled:opacity-50"
          style={{ maxHeight: 140 }}
        />
        <button
          onClick={handleSend}
          disabled={!value.trim() || isLoading || disabled}
          className="flex-shrink-0 w-9 h-9 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-xl flex items-center justify-center transition-colors"
        >
          {isLoading
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <SendHorizonal className="w-4 h-4" />}
        </button>
      </div>
      <p className="text-xs text-slate-400 text-center">
        Enter untuk kirim • Shift+Enter untuk baris baru
      </p>
    </div>
  )
}
