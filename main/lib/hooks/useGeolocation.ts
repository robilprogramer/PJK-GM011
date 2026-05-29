'use client'
import { useCallback } from 'react'
import { useLocationStore } from '@/lib/store'
import { reverseGeocode, geocodeCity } from '@/lib/api'

export function useGeolocation() {
  const { setLocation, setDetecting, setError } = useLocationStore()

  const detectAuto = useCallback(async () => {
    if (!navigator.geolocation) { setError('Browser tidak mendukung geolocation'); return }
    setDetecting(true); setError(null)
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const loc = await reverseGeocode(coords.latitude, coords.longitude)
          setLocation(loc)
        } catch {
          setLocation({ lat: coords.latitude, lng: coords.longitude,
            city: `${coords.latitude.toFixed(4)},${coords.longitude.toFixed(4)}`,
            province: '', display_name: `Koordinat: ${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}` })
        } finally { setDetecting(false) }
      },
      (err) => {
        const msgs: Record<number,string> = {
          1:'Izin lokasi ditolak. Input nama kota manual.',
          2:'Posisi tidak tersedia. Coba input kota.',
          3:'Timeout. Coba lagi atau input kota.',
        }
        setError(msgs[err.code] || 'Gagal mendeteksi lokasi.')
        setDetecting(false)
      },
      { timeout: 10000, maximumAge: 300000, enableHighAccuracy: false }
    )
  }, [setLocation, setDetecting, setError])

  const setManual = useCallback(async (cityName: string) => {
    if (!cityName.trim()) return
    setDetecting(true); setError(null)
    try {
      const loc = await geocodeCity(cityName.trim())
      setLocation(loc)
    } catch {
      setError(`Kota "${cityName}" tidak ditemukan. Coba nama lain.`)
    } finally { setDetecting(false) }
  }, [setLocation, setDetecting, setError])

  return { detectAuto, setManual }
}
