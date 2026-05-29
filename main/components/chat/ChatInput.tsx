'use client'
import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { SendHorizonal, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  onSend:    (msg: string) => void
  isLoading: boolean
  disabled?: boolean
}

const SUGGESTIONS = [
  'Apakah aman keluar rumah sekarang?',
  'Bagaimana panduan evakuasi banjir?',
  'Apa saja isi tas siaga bencana?',
  'Tanda-tanda tanah longsor akan terjadi?',
]

export function ChatInput({ onSend, isLoading, disabled }: Props) {
  const [value,    setValue]    = useState('')
  const [showSugg, setShowSugg] = useState(true)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }, [value])

  const handleSend = () => {
    if (!value.trim() || isLoading || disabled) return
    onSend(value.trim())
    setValue('')
    setShowSugg(false)
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestion = (text: string) => {
    onSend(text)
    setShowSugg(false)
  }

  return (
    <div className="space-y-2">
      {/* Quick suggestions */}
      {showSugg && !disabled && (
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTIONS.map(s => (
            <button
              key={s}
              onClick={() => handleSuggestion(s)}
              disabled={isLoading}
              className="text-xs bg-white border border-slate-200 text-slate-600 px-2.5 py-1.5 rounded-full hover:border-blue-400 hover:text-blue-600 transition-colors disabled:opacity-50 shadow-sm"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className={cn(
        'flex items-end gap-2 bg-white border rounded-2xl px-4 py-2.5 shadow-sm transition-all',
        isLoading || disabled
          ? 'border-slate-200 opacity-80'
          : 'border-slate-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent'
      )}>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          disabled={isLoading || disabled}
          placeholder={disabled ? 'Menginisialisasi sesi...' : 'Tanya tentang bencana di lokasi kamu…'}
          rows={1}
          className="flex-1 resize-none text-sm text-slate-800 placeholder-slate-400 bg-transparent focus:outline-none disabled:opacity-50"
          style={{ maxHeight: 140 }}
        />
        <button
          onClick={handleSend}
          disabled={!value.trim() || isLoading || disabled}
          className="flex-shrink-0 w-8 h-8 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-xl flex items-center justify-center transition-colors"
        >
          {isLoading
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
            : <SendHorizonal className="w-3.5 h-3.5" />
          }
        </button>
      </div>
      <p className="text-center text-xs text-slate-400">
        Enter kirim · Shift+Enter baris baru
      </p>
    </div>
  )
}
