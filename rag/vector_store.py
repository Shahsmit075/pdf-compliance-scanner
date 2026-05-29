# rag/vector_store.py
"""
Vector store wrapper for ChromaDB.
Used by the Knowledge Agent to index compliance findings and by the Copilot to answer questions.

Uses EphemeralClient in dev (no persistence) and PersistentClient in production.
Set CHROMA_PERSIST_DIR env var to enable persistence.
"""
import os
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).parent.parent / "storage" / "chroma_db"))
COLLECTION_NAME = "compliance_knowledge"


def _get_client():
    """Get ChromaDB client — persistent if CHROMA_PERSIST_DIR is set."""
    try:
        import chromadb

        if CHROMA_PERSIST_DIR:
            Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
            return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        else:
            return chromadb.EphemeralClient()
    except ImportError:
        raise ImportError("chromadb is required. Install with: pip install chromadb")


def get_collection():
    """Get or create the compliance knowledge collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_documents(documents: List[str], metadatas: List[dict],
                     ids: List[str], embeddings: Optional[List[List[float]]] = None):
    """
    Upsert documents into the vector store.

    Args:
        documents: List of text documents to index
        metadatas: List of metadata dicts (source_id, scan_id, entity_name, etc.)
        ids: Unique IDs for each document
        embeddings: Pre-computed embeddings (optional — ChromaDB will compute if None)
    """
    collection = get_collection()
    kwargs = {
        "documents": documents,
        "metadatas": metadatas,
        "ids": ids,
    }
    if embeddings:
        kwargs["embeddings"] = embeddings

    collection.upsert(**kwargs)
    logger.info(f"Upserted {len(documents)} documents into ChromaDB")


def query_similar(query_text: str, n_results: int = 5,
                  where: dict = None) -> dict:
    """
    Query the vector store for documents similar to query_text.

    Args:
        query_text: The search query
        n_results: Number of results to return
        where: Optional metadata filter (e.g., {"source_id": "abc123"})

    Returns:
        ChromaDB query result dict with keys: ids, documents, metadatas, distances
    """
    collection = get_collection()
    kwargs = {
        "query_texts": [query_text],
        "n_results": min(n_results, collection.count() or 1),
    }
    if where:
        kwargs["where"] = where

    return collection.query(**kwargs)


def index_scan_findings(scan_id: str, source_id: str, source_name: str,
                        scan_results: list) -> int:
    """
    Index scan findings into ChromaDB for RAG retrieval.

    Args:
        scan_id: ID of the completed scan
        source_id: Data source ID
        source_name: Human-readable source name
        scan_results: List of scan result dicts

    Returns:
        Number of documents indexed
    """
    if not scan_results:
        return 0

    documents = []
    metadatas = []
    ids = []

    for i, result in enumerate(scan_results):
        entity = result.get("entity_name", "unknown")
        check_type = result.get("check_type", "unknown")
        risk_level = result.get("risk_level", "low")
        flag_category = result.get("flag_category", "")
        recommendation = result.get("recommendation", "")
        evidence = result.get("evidence", "")

        doc_text = (
            f"Data source: {source_name}\n"
            f"Entity: {entity}\n"
            f"Risk type: {check_type} — {flag_category}\n"
            f"Risk level: {risk_level}\n"
            f"Evidence: {evidence}\n"
            f"Recommendation: {recommendation}"
        )

        documents.append(doc_text)
        metadatas.append({
            "source_id":    source_id,
            "source_name":  source_name,
            "scan_id":      scan_id,
            "entity_name":  entity,
            "check_type":   check_type,
            "risk_level":   risk_level,
            "flag_category": flag_category or "",
        })
        ids.append(f"{scan_id}_{i}_{entity[:20]}")

    try:
        upsert_documents(documents, metadatas, ids)
        return len(documents)
    except Exception as e:
        logger.error(f"Failed to index scan findings: {e}")
        return 0


def get_collection_stats() -> dict:
    """Return stats about the current collection."""
    try:
        collection = get_collection()
        return {
            "total_documents": collection.count(),
            "collection_name": COLLECTION_NAME,
            "persist_dir": CHROMA_PERSIST_DIR,
        }
    except Exception as e:
        return {"error": str(e), "total_documents": 0}
