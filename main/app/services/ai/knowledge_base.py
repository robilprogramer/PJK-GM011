"""
Knowledge Base Service — RAG untuk SiagaAI.
Menyimpan dan mencari dokumen pengetahuan kebencanaan menggunakan ChromaDB.
"""

import json
import os
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class KnowledgeBaseService:
    """
    RAG service menggunakan ChromaDB sebagai vector store.
    Menyimpan knowledge base kebencanaan dan melakukan semantic search.
    """

    def __init__(self):
        self._client: chromadb.ClientAPI | None = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            ef = embedding_functions.DefaultEmbeddingFunction()
            self._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                embedding_function=ef,
                metadata={"description": "SiagaAI disaster knowledge base"},
            )
        return self._collection

    async def search(self, query: str, n_results: int = 3) -> list[str]:
        """
        Cari dokumen yang relevan dengan query.
        Returns list of document texts.
        """
        try:
            coll = self._get_collection()
            count = coll.count()
            if count == 0:
                logger.warning("Knowledge base kosong — skip RAG")
                return []

            results = coll.query(
                query_texts=[query],
                n_results=min(n_results, count),
                include=["documents", "metadatas"],
            )

            docs = results.get("documents", [[]])[0]
            return docs

        except Exception as e:
            logger.warning("Knowledge base search failed", error=str(e))
            return []

    def load_from_json(self, json_path: str) -> int:
        """
        Load knowledge base dari file JSON ke ChromaDB.
        Returns jumlah dokumen yang berhasil di-load.
        """
        if not os.path.exists(json_path):
            logger.error("Dataset file tidak ditemukan", path=json_path)
            return 0

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = data.get("knowledge_base", [])
        if not entries:
            return 0

        coll = self._get_collection()

        ids, docs, metas = [], [], []
        for entry in entries:
            ids.append(entry["id"])
            docs.append(entry["content"])
            metas.append({
                "category": entry.get("category", "general"),
                "disaster_type": entry.get("disaster_type", "general"),
                "title": entry.get("title", ""),
                "source": entry.get("source", "SiagaAI"),
                "tags": ",".join(entry.get("tags", [])),
            })

        # Upsert (tambah atau update jika sudah ada)
        coll.upsert(ids=ids, documents=docs, metadatas=metas)
        logger.info("Knowledge base loaded", count=len(ids), path=json_path)
        return len(ids)

    def get_stats(self) -> dict:
        """Info jumlah dokumen di knowledge base."""
        try:
            coll = self._get_collection()
            return {
                "total_documents": coll.count(),
                "collection_name": settings.CHROMA_COLLECTION,
                "db_path": settings.CHROMA_DB_PATH,
            }
        except Exception as e:
            return {"error": str(e)}

    def reset(self) -> bool:
        """Hapus semua data di collection (untuk testing)."""
        try:
            client = self._get_client()
            client.delete_collection(settings.CHROMA_COLLECTION)
            self._collection = None
            logger.warning("Knowledge base di-reset")
            return True
        except Exception as e:
            logger.error("Reset knowledge base failed", error=str(e))
            return False


# Singleton
knowledge_base = KnowledgeBaseService()
