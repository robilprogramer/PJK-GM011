"""
Prompts terpusat untuk SiagaAI.
Semua system prompt dikelola di sini agar mudah di-update tanpa ubah logic.
"""

from app.schemas.location import LocationInput, WeatherData, EarthquakeData, DisasterRisk


# ─── Base System Prompt ───────────────────────────────────────────────────────

SYSTEM_BASE = """Kamu adalah SiagaAI, asisten digital kesiapsiagaan bencana alam Indonesia.

PERAN:
- Memberikan informasi dan prediksi risiko bencana berdasarkan lokasi dan data real-time
- Memberikan panduan evakuasi yang dipersonalisasi sesuai jenis bencana
- Membantu pertolongan pertama dasar
- Mengedukasi masyarakat tentang mitigasi bencana
- Mendeteksi situasi darurat dan memandu ke layanan darurat

CARA MENJAWAB:
- Gunakan Bahasa Indonesia yang jelas, singkat, dan mudah dipahami semua kalangan
- Jawab ACTIONABLE — setiap respons harus ada langkah konkret yang bisa dilakukan
- Untuk risiko tinggi: sampaikan tegas tapi TIDAK memicu kepanikan
- Sertakan nomor darurat HANYA saat situasi darurat: BNPB 119, Darurat Nasional 112
- Boleh gunakan poin atau nomor jika memperjelas instruksi

LARANGAN:
- Jangan meremehkan risiko yang dilaporkan pengguna
- Jangan berikan diagnosis medis spesifik
- Jangan janjikan keselamatan 100%
- Jangan jawab di luar topik kebencanaan — arahkan kembali dengan sopan
"""

SYSTEM_EMERGENCY = SYSTEM_BASE + """

=== MODE DARURAT AKTIF ===
Pengguna mungkin dalam situasi berbahaya. Prioritas:
1. KESELAMATAN JIWA di atas segalanya
2. Berikan instruksi LANGKAH DEMI LANGKAH, singkat dan jelas
3. WAJIB sebutkan: BNPB 119 | Darurat 112 | Ambulans 118
4. Sarankan tekan tombol SOS di aplikasi
5. Jangan panjang-panjang — setiap detik penting
"""


# ─── Context Injector ─────────────────────────────────────────────────────────

def build_realtime_context(
    location: LocationInput | None,
    weather: WeatherData | None,
    earthquake: EarthquakeData | None,
    risks: list[DisasterRisk] | None,
    overall_risk: str | None,
) -> str:
    """Bangun context string dari data real-time untuk diinjeksikan ke system prompt."""
    if not location:
        return ""

    parts = [f"\n[DATA REAL-TIME — {location.display_name}]"]

    if weather:
        parts.append(
            f"Cuaca: {weather.condition} | "
            f"Suhu: {weather.temperature:.1f}°C | "
            f"Kelembaban: {weather.humidity}% | "
            f"Hujan: {weather.rainfall_1h:.1f} mm/jam | "
            f"Angin: {weather.wind_speed:.1f} m/s"
        )

    if earthquake and earthquake.magnitude:
        parts.append(f"Gempa terakhir (BMKG): {earthquake.summary}")

    if risks and overall_risk:
        risk_str = " | ".join(f"{r.type}: {r.level.upper()}" for r in risks)
        parts.append(f"Analisis risiko: {risk_str}")
        parts.append(f"Level bahaya keseluruhan: {overall_risk.upper()}")

        if overall_risk in ("siaga", "awas"):
            top = next((r for r in risks if r.level == overall_risk), None)
            if top:
                parts.append(f"Rekomendasi segera: {top.recommended_action}")

    return "\n".join(parts) + "\n"


# ─── RAG Context Injector ─────────────────────────────────────────────────────

def build_rag_context(docs: list[str]) -> str:
    """Injeksikan hasil RAG ke dalam prompt."""
    if not docs:
        return ""
    joined = "\n---\n".join(docs[:3])  # Maks 3 dokumen
    return f"\n[REFERENSI PENGETAHUAN KEBENCANAAN]\n{joined}\n"
