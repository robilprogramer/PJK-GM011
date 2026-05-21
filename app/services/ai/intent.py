"""
Intent detection untuk SiagaAI chatbot.
Menentukan kategori pesan tanpa memerlukan LLM call tambahan.
"""

from app.schemas.chat import MessageIntent


# ─── Keyword Maps ─────────────────────────────────────────────────────────────

_INTENT_KEYWORDS: dict[MessageIntent, list[str]] = {
    MessageIntent.emergency: [
        "darurat", "tolong", "sos", "bahaya", "terjebak", "tenggelam",
        "tidak bisa keluar", "butuh bantuan", "selamatkan", "minta tolong",
        "korban", "celaka", "kebakaran besar", "sekarat", "butuh pertolongan",
    ],
    MessageIntent.evacuation: [
        "evakuasi", "lari", "kabur", "jalan keluar", "jalur", "pengungsian",
        "kemana harus", "tempat aman", "shelter", "titik kumpul", "mengungsi",
        "rute alternatif", "jalan lain", "keluar dari",
    ],
    MessageIntent.first_aid: [
        "pertolongan pertama", "luka", "cedera", "pingsan", "p3k",
        "patah tulang", "pendarahan", "sesak nafas", "gigitan ular",
        "luka bakar", "hipotermia", "tenggelam", "keracunan",
    ],
    MessageIntent.prediction: [
        "prediksi", "potensi", "kemungkinan", "risiko", "aman tidak",
        "bagaimana kondisi", "apakah akan", "perkiraan", "prakiraan",
        "status cuaca", "cek banjir", "cek gempa", "cuaca hari ini",
        "apakah aman", "berbahaya tidak", "level risiko",
    ],
    MessageIntent.education: [
        "cara", "tips", "bagaimana", "apa yang harus", "persiapan",
        "tas siaga", "mitigasi", "edukasi", "pelajari", "langkah",
        "prosedur", "protokol", "panduan umum", "apa itu banjir",
        "apa itu longsor", "cara menghadapi", "siap siaga",
    ],
}

_ESCALATION_TRIGGERS = [
    "darurat", "tolong", "sos", "terjebak", "tidak bisa keluar",
    "butuh bantuan segera", "korban", "tenggelam", "kebakaran",
    "nyawa", "selamatkan", "minta tolong segera", "celaka",
]


def detect_intent(message: str) -> MessageIntent:
    """
    Deteksi intent dari pesan pengguna.
    Emergency selalu punya prioritas tertinggi.
    """
    msg = message.lower()

    for intent in [
        MessageIntent.emergency,
        MessageIntent.evacuation,
        MessageIntent.first_aid,
        MessageIntent.prediction,
        MessageIntent.education,
    ]:
        if any(k in msg for k in _INTENT_KEYWORDS.get(intent, [])):
            return intent

    return MessageIntent.general


def check_escalation(message: str) -> bool:
    """Cek apakah pesan perlu dieskalasi ke SAR/BPBD."""
    return any(k in message.lower() for k in _ESCALATION_TRIGGERS)


def get_suggested_actions(intent: MessageIntent, overall_risk: str | None = None) -> list[str]:
    """Saran tindakan berdasarkan intent dan level risiko."""
    actions_map: dict[MessageIntent, list[str]] = {
        MessageIntent.emergency: [
            "Hubungi 119 (BNPB)",
            "Hubungi 112 (Darurat Nasional)",
            "Tekan tombol SOS di aplikasi ini",
            "Hubungi 118 (Ambulans) jika ada korban luka",
        ],
        MessageIntent.evacuation: [
            "Bawa dokumen penting (KTP, BPJS)",
            "Isi daya penuh ponsel",
            "Hubungi keluarga tentang lokasi evakuasi",
            "Bawa obat-obatan rutin",
        ],
        MessageIntent.first_aid: [
            "Hubungi 118 jika korban kritis",
            "Jangan pindahkan korban patah tulang",
            "Cari bantuan medis segera",
        ],
        MessageIntent.prediction: [
            "Pantau update BMKG di bmkg.go.id",
            "Aktifkan notifikasi peringatan dini",
            "Siapkan tas siaga bencana",
        ],
        MessageIntent.education: [
            "Pelajari jalur evakuasi sekitar rumah",
            "Ikuti simulasi BPBD setempat",
            "Siapkan tas siaga keluarga",
        ],
        MessageIntent.general: [
            "Pantau kondisi cuaca secara berkala",
            "Simpan nomor darurat: 119, 112, 118",
        ],
    }

    actions = list(actions_map.get(intent, []))

    if overall_risk in ("siaga", "awas") and intent != MessageIntent.emergency:
        actions.insert(0, f"Tingkatkan kewaspadaan — risiko {overall_risk.upper()} terdeteksi!")

    return actions
