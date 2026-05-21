'use client'
import { RISK_CONFIG, type RiskLevel } from '@/types'
import { cn } from '@/lib/utils'

interface Props {
  level: RiskLevel
  size?: 'xs' | 'sm' | 'md' | 'lg'
  showEmoji?: boolean
  animate?: boolean
  className?: string
}

export function RiskBadge({
  level,
  size = 'md',
  showEmoji = true,
  animate = false,
  className,
}: Props) {
  const cfg = RISK_CONFIG[level]
  const sizeClass = {
    xs: 'text-xs px-1.5 py-0.5 gap-0.5',
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-3 py-1 gap-1',
    lg: 'text-base px-4 py-1.5 gap-1.5',
  }[size]

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-semibold border select-none',
        sizeClass,
        animate && level === 'awas' && 'animate-pulse',
        className
      )}
      style={{
        background: cfg.bg,
        borderColor: cfg.border,
        color: cfg.color,
      }}
    >
      {showEmoji && <span aria-hidden="true">{cfg.emoji}</span>}
      <span>{cfg.label}</span>
    </span>
  )
}
