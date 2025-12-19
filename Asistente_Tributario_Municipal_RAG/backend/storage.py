from typing import Dict, List, Optional

# ------------------------ LOGGING ------------------------
import logging
logger = logging.getLogger("STORAGE")
# ---------------------------------------------------------

# Diccionario global donde guardamos los documentos subidos.
# Clave: document_id (str)
# Valor: dict con title, content, chunks, embedding_ids

DOCUMENTS: Dict[str, dict] = {}

def save_document(doc_id: str, title: str, content: str):
    DOCUMENTS[doc_id] = {
        "id": doc_id,
        "title": title,
        "content": content,
        "chunks": None,  # se llena después de generar embeddings
        "embedding_ids": None,  # IDs de los chunks en el vector store
    }
    logger.info(f"[STORAGE] Documento guardado: id={doc_id}, titulo='{title[:40]}'")


def get_document(doc_id: str) -> Optional[dict]:
    doc = DOCUMENTS.get(doc_id)
    if doc:
        logger.info(f"[STORAGE] Documento recuperado: id={doc_id}")
    else:
        logger.warning(f"[STORAGE] Documento no encontrado: id={doc_id}")
    return doc


def list_documents() -> List[dict]:
    logger.info(f"[STORAGE] Listando {len(DOCUMENTS)} documentos almacenados.")
    return list(DOCUMENTS.values())

def debug_documents():
    return DOCUMENTS