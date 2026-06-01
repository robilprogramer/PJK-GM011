import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Admin Dashboard — SiagaAI',
  description: 'System monitoring & management panel for SiagaAI',
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
