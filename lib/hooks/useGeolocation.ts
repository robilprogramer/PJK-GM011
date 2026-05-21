'use client'
import { useCallback } from 'react'
import { useLocationStore } from '@/lib/store'
import { reverseGeocode, geocodeCity } from '@/lib/api'

export function useGeolocation() {
  const { setLocation, setDetecting, setError } = useLocationStore()

  const detectAuto = useCallback(async () => {
    if (!navigator.geolocation) {
      setError('Browser tidak mendukung geolocation. Coba input nama kota.')
      return
    }
    setDetecting(true)
    setError(null)
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const loc = await reverseGeocode(coords.latitude, coords.longitude)
          setLocation(loc)
        } catch {
          // Fallback: gunakan koordinat langsung
          setLocation({
            lat: coords.latitude,
            lng: coords.longitude,
            city: `${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`,
            province: '',
            display_name: `Koordinat: ${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`,
          })
        } finally {
          setDetecting(false)
        }
      },
      (err) => {
        const messages: Record<number, string> = {
          1: 'Izin lokasi ditolak. Silakan input nama kota secara manual.',
          2: 'Lokasi tidak tersedia. Coba input nama kota.',
          3: 'Timeout mendeteksi lokasi. Coba lagi atau input nama kota.',
        }
        setError(messages[err.code] || 'Gagal mendeteksi lokasi.')
        setDetecting(false)
      },
      { timeout: 10000, maximumAge: 300000, enableHighAccuracy: false }
    )
  }, [setLocation, setDetecting, setError])

  const setManual = useCallback(async (cityName: string) => {
    if (!cityName.trim()) return
    setDetecting(true)
    setError(null)
    try {
      const loc = await geocodeCity(cityName.trim())
      setLocation(loc)
    } catch (e: any) {
      setError(`Kota "${cityName}" tidak ditemukan. Coba nama lain, misal: "Jakarta" atau "Surabaya".`)
    } finally {
      setDetecting(false)
    }
  }, [setLocation, setDetecting, setError])

  return { detectAuto, setManual }
}
