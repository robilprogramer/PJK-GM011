"""
Risk Analyzer — SiagaAI
Menganalisis data cuaca dan gempa untuk menentukan level risiko bencana.
"""

from app.core.config import settings
from app.schemas.location import DisasterRisk, WeatherData, EarthquakeData

AMAN = "aman"
WASPADA = "waspada"
SIAGA = "siaga"
AWAS = "awas"
LEVEL_ORDER = [AMAN, WASPADA, SIAGA, AWAS]


def _max_level(*levels: str) -> str:
    return max(levels, key=lambda l: LEVEL_ORDER.index(l))


class RiskAnalyzer:
    """Analisis risiko 4 jenis bencana: banjir, longsor, gempa, angin kencang."""

    def analyze(
        self,
        weather: WeatherData,
        earthquake: EarthquakeData,
    ) -> tuple[list[DisasterRisk], str]:
        risks = [
            self._flood(weather),
            self._landslide(weather),
            self._earthquake(earthquake),
            self._wind(weather),
        ]
        overall = _max_level(*[r.level for r in risks])
        return risks, overall

    def _flood(self, w: WeatherData) -> DisasterRisk:
        rain = w.rainfall_1h
        if rain >= settings.RAIN_AWAS_MM or (rain >= settings.RAIN_SIAGA_MM and w.humidity > 90):
            return DisasterRisk(
                type="banjir", level=AWAS,
                description=f"Hujan sangat lebat ({rain:.1f} mm/jam). Risiko banjir sangat tinggi.",
                recommended_action="Segera pindah ke tempat lebih tinggi. Hindari bantaran sungai dan gorong-gorong.",
            )
        if rain >= settings.RAIN_SIAGA_MM:
            return DisasterRisk(
                type="banjir", level=SIAGA,
                description=f"Hujan lebat ({rain:.1f} mm/jam). Waspada genangan dan luapan sungai.",
                recommended_action="Pantau ketinggian air. Siapkan barang penting untuk evakuasi cepat.",
            )
        if rain >= settings.RAIN_WASPADA_MM:
            return DisasterRisk(
                type="banjir", level=WASPADA,
                description=f"Hujan sedang ({rain:.1f} mm/jam). Potensi genangan di daerah rendah.",
                recommended_action="Pastikan saluran air lancar. Hindari daerah rawan genangan.",
            )
        return DisasterRisk(
            type="banjir", level=AMAN,
            description=f"Tidak ada hujan signifikan ({rain:.1f} mm/jam).",
            recommended_action="Kondisi normal. Tetap pantau perkembangan cuaca.",
        )

    def _landslide(self, w: WeatherData) -> DisasterRisk:
        rain, hum = w.rainfall_1h, w.humidity
        if rain >= settings.RAIN_SIAGA_MM and hum > 85:
            return DisasterRisk(
                type="longsor", level=AWAS,
                description=f"Hujan lebat + kelembaban sangat tinggi ({hum}%). Risiko longsor sangat tinggi.",
                recommended_action="Jauhi lereng bukit dan tebing. Evakuasi jika ada retakan tanah atau suara gemuruh.",
            )
        if rain >= settings.RAIN_WASPADA_MM and hum > 80:
            return DisasterRisk(
                type="longsor", level=SIAGA,
                description=f"Hujan + kelembaban tinggi ({hum}%). Potensi longsor di area perbukitan.",
                recommended_action="Waspada retakan tanah, suara gemuruh, aliran lumpur.",
            )
        if rain > 0 and hum > 75:
            return DisasterRisk(
                type="longsor", level=WASPADA,
                description="Kondisi lembab. Pantau area perbukitan sekitar.",
                recommended_action="Perhatikan kondisi lereng. Laporkan ke BPBD jika ada tanda pergerakan tanah.",
            )
        return DisasterRisk(
            type="longsor", level=AMAN,
            description="Risiko longsor rendah.",
            recommended_action="Kondisi normal. Tetap waspada di area perbukitan.",
        )

    def _earthquake(self, eq: EarthquakeData) -> DisasterRisk:
        try:
            mag = float(eq.magnitude) if eq.magnitude else 0.0
        except (ValueError, TypeError):
            mag = 0.0

        if mag >= settings.EQ_AWAS_MAG:
            return DisasterRisk(
                type="gempa", level=AWAS,
                description=f"Gempa M{mag:.1f}! Potensi kerusakan besar dan tsunami.",
                recommended_action="Berlindung di bawah meja. Jauhi jendela. Setelah gempa, evakuasi ke dataran tinggi.",
            )
        if mag >= settings.EQ_SIAGA_MAG:
            return DisasterRisk(
                type="gempa", level=SIAGA,
                description=f"Gempa M{mag:.1f} terjadi di {eq.location or 'wilayah terdekat'}.",
                recommended_action="Periksa kerusakan bangunan. Waspada gempa susulan.",
            )
        if mag >= settings.EQ_WASPADA_MAG:
            return DisasterRisk(
                type="gempa", level=WASPADA,
                description=f"Aktivitas gempa M{mag:.1f} terdeteksi.",
                recommended_action="Kenali jalur evakuasi. Siapkan tas darurat.",
            )
        return DisasterRisk(
            type="gempa", level=AMAN,
            description="Tidak ada aktivitas gempa signifikan.",
            recommended_action="Pastikan bangunan memenuhi standar tahan gempa.",
        )

    def _wind(self, w: WeatherData) -> DisasterRisk:
        wind = w.wind_speed
        if wind >= 17.2:
            return DisasterRisk(
                type="angin_kencang", level=AWAS,
                description=f"Angin sangat kencang ({wind:.1f} m/s). Bahaya pohon dan bangunan tumbang.",
                recommended_action="Tetap di dalam ruangan. Jauhi pohon besar dan papan reklame.",
            )
        if wind >= 10.8:
            return DisasterRisk(
                type="angin_kencang", level=SIAGA,
                description=f"Angin kencang ({wind:.1f} m/s). Waspada ranting patah dan atap terbang.",
                recommended_action="Amankan benda ringan di luar rumah.",
            )
        if wind >= 5.5:
            return DisasterRisk(
                type="angin_kencang", level=WASPADA,
                description=f"Angin sedang ({wind:.1f} m/s).",
                recommended_action="Pantau perkembangan cuaca.",
            )
        return DisasterRisk(
            type="angin_kencang", level=AMAN,
            description=f"Kecepatan angin normal ({wind:.1f} m/s).",
            recommended_action="Tidak ada tindakan khusus.",
        )
