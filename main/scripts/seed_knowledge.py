#!/usr/bin/env python3
"""
Seed Knowledge Base — SiagaAI
==============================
Load dataset disaster_knowledge.json ke ChromaDB.

Cara pakai:
    cd backend
    python scripts/seed_knowledge.py

    # Reset dulu lalu load ulang:
    python scripts/seed_knowledge.py --reset
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai.knowledge_base import knowledge_base
from app.core.config import settings


def main():
    parser = argparse.ArgumentParser(description="Seed SiagaAI Knowledge Base")
    parser.add_argument("--reset", action="store_true", help="Hapus data lama sebelum load")
    parser.add_argument(
        "--dataset",
        default="app/data/disaster_knowledge.json",
        help="Path ke file dataset JSON",
    )
    args = parser.parse_args()

    print("=" * 55)
    print("  SiagaAI Knowledge Base Seeder")
    print("=" * 55)
    print(f"  Dataset : {args.dataset}")
    print(f"  ChromaDB: {settings.CHROMA_DB_PATH}")
    print(f"  Koleksi : {settings.CHROMA_COLLECTION}")
    print("=" * 55)

    # Cek file dataset ada
    if not os.path.exists(args.dataset):
        print(f"\n[ERROR] Dataset tidak ditemukan: {args.dataset}")
        print("  Pastikan kamu menjalankan script ini dari direktori 'backend/'")
        sys.exit(1)

    # Reset jika diminta
    if args.reset:
        print("\n[RESET] Menghapus data lama...")
        ok = knowledge_base.reset()
        if ok:
            print("  Data lama berhasil dihapus.")
        else:
            print("  Tidak ada data lama atau gagal reset.")

    # Tampilkan stats sebelum
    stats_before = knowledge_base.get_stats()
    print(f"\n[SEBELUM] Total dokumen: {stats_before.get('total_documents', 0)}")

    # Load dataset
    print(f"\n[LOAD] Memuat dataset dari {args.dataset}...")
    count = knowledge_base.load_from_json(args.dataset)

    # Tampilkan stats sesudah
    stats_after = knowledge_base.get_stats()
    print(f"\n[SELESAI] Dokumen berhasil dimuat: {count}")
    print(f"[TOTAL]  Total dokumen di KB   : {stats_after.get('total_documents', 0)}")

    # Test search
    print("\n[TEST SEARCH] Mencoba semantic search...")
    import asyncio

    async def test():
        results = await knowledge_base.search("cara evakuasi saat banjir", n_results=2)
        print(f"  Query: 'cara evakuasi saat banjir'")
        print(f"  Ditemukan {len(results)} dokumen relevan:")
        for i, doc in enumerate(results, 1):
            preview = doc[:120].replace("\n", " ")
            print(f"  [{i}] {preview}...")

    asyncio.run(test())

    print("\n[OK] Knowledge base siap digunakan!")
    print("     Jalankan server: uvicorn main:app --reload")
    print("=" * 55)


if __name__ == "__main__":
    main()
