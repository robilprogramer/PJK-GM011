'use client'
import ReactMarkdown from 'react-markdown'
import { Bot, User, AlertTriangle } from 'lucide-react'
import type { ChatMessage } from '@/types'
import { INTENT_CONFIG }   from '@/types'
import { formatTime, cn }  from '@/lib/utils'

interface Props { message: ChatMessage }

export function ChatBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const intent = message.intent ? INTENT_CONFIG[message.intent] : null

  return (
    <div className={cn('flex gap-2.5 animate-slide-up', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 w-7 h-7 rounded-xl flex items-center justify-center text-white text-xs shadow-sm',
        isUser ? 'bg-blue-600' : 'bg-slate-700'
      )}>
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      <div className={cn('flex flex-col gap-1 max-w-[82%]', isUser && 'items-end')}>
        {/* Intent badge */}
        {intent && !isUser && (
          <span className={cn(
            'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium',
            intent.color
          )}>
            <span>{intent.emoji}</span>
            {intent.label}
          </span>
        )}

        {/* Bubble */}
        <div className={cn(
          'rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed break-words',
          isUser
            ? 'bg-blue-600 text-white rounded-tr-sm'
            : message.requires_escalation
              ? 'bg-red-50 border border-red-200 text-slate-800 rounded-tl-sm'
              : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm'
        )}>
          {message.requires_escalation && !isUser && (
            <div className="flex items-center gap-1.5 text-red-600 font-bold mb-2 text-xs">
              <AlertTriangle className="w-3.5 h-3.5" />
              SITUASI DARURAT TERDETEKSI
            </div>
          )}

          {message.isStreaming ? (
            <div className="flex items-center gap-1 py-0.5">
              {[0, 1, 2].map(i => (
                <div key={i}
                  className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot"
                />
              ))}
            </div>
          ) : (
            <div className={cn('prose-chat', isUser && '[&_*]:text-white')}>
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Suggested actions */}
        {!isUser && message.suggested_actions && message.suggested_actions.length > 0 && !message.isStreaming && (
          <div className="flex flex-wrap gap-1.5 mt-0.5">
            {message.suggested_actions.slice(0, 3).map((action, i) => (
              <span
                key={i}
                className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full border border-slate-200"
              >
                {action}
              </span>
            ))}
          </div>
        )}

        {/* Meta */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">{formatTime(message.timestamp)}</span>
          {message.model_used && !isUser && (
            <span className="text-xs text-slate-300 bg-slate-100 px-1.5 py-0.5 rounded-full">
              {message.model_used.split('-').slice(0, 2).join(' ')}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
