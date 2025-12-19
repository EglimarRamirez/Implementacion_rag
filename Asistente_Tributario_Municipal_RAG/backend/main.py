from fastapi import FastAPI, HTTPException
from fastapi import UploadFile, File

from uuid import uuid4
import pdfplumber

from models import (StatusResponse,
    GenerateEmbeddingsRequest, GenerateEmbeddingsResponse,
    SearchRequest, SearchResponse, SearchResultItem,
    AskRequest, AskResponse,
)
from storage import save_document, get_document, DOCUMENTS
from rag_ppal import chunk_document, generate_embeddings_for_document, search_similar_chunks, rag_answer

# ------------------------ LOGGING ------------------------
from logging_config import configure_logging
import logging

configure_logging()
logger = logging.getLogger("API")
# ---------------------------------------------------------

app = FastAPI(title="Asistente Tributario Municipal API", version="1.0.0")

@app.get("/status", response_model=StatusResponse)
def status():
    logger.info("[STATUS] Health check OK")
    return StatusResponse(
        service="asistente_tributario_rag",
        status="ok",
        documents_loaded=len(DOCUMENTS)
    )

@app.post("/upload-file")
async def upload_file(title: str, file: UploadFile = File(...)):
    logger.info(f"[UPLOAD-FILE] Recibiendo archivo: {file.filename}")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    # ---- Extraer texto ----
    try:

        pdf_text = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pdf_text += page_text + "\n"

        if not pdf_text.strip():
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")

    except Exception:
        logger.error("[UPLOAD-FILE] Error leyendo PDF", exc_info=True)
        raise HTTPException(status_code=500, detail="Error procesando el PDF")

    # ---- Guardar documento crudo ----
    doc_id = str(uuid4())

    save_document(doc_id, title, pdf_text)

    DOCUMENTS[doc_id]["chunks"] = None
    DOCUMENTS[doc_id]["embedding_ids"] = None

    logger.info(f"[UPLOAD-FILE] Documento guardado crudo con id={doc_id}")

    return {
        "message": "PDF cargado correctamente. Listo para procesar embeddings luego.",
        "document_id": doc_id,
        "title": title,
        "text_length": len(pdf_text)
    }

@app.post("/generate-embeddings", response_model=GenerateEmbeddingsResponse)
def generate_embeddings(payload: GenerateEmbeddingsRequest):
    logger.info(f"[EMBEDDINGS] Solicitud para generar embeddings. document_id={payload.document_id}")

    if payload.document_id:
        doc = get_document(payload.document_id)
        if not doc:
            logger.warning(f"[EMBEDDINGS] Documento no encontrado: {payload.document_id}")
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        logger.info(f"[EMBEDDINGS] Generando embeddings para documento {doc['id']} - '{doc['title']}'")
        
        chunks = chunk_document(doc["content"], doc["title"])
        ids = generate_embeddings_for_document(doc["id"], doc["title"], chunks)
        doc["chunks"] = chunks
        doc["embedding_ids"] = ids

        logger.info(f"[EMBEDDINGS] Embeddings generados correctamente para {doc['id']}")

        return GenerateEmbeddingsResponse(
            message=f"Embeddings generated successfully for document {doc['id']}",
            document_id=doc["id"],
        )

    # Si viene sin document_id, procesar todos
    for doc in DOCUMENTS.values():
        if doc.get("embedding_ids"):
            continue

        logger.info(f"[EMBEDDINGS] Procesando documento {doc['id']} - '{doc['title']}'")

        chunks = chunk_document(doc["content"], doc["title"])
        ids = generate_embeddings_for_document(doc["id"], doc["title"], chunks)
        doc["chunks"] = chunks
        doc["embedding_ids"] = ids

        logger.info(f"[EMBEDDINGS] Embeddings generados para documento {doc['id']}")

    logger.info("[EMBEDDINGS] Embeddings generados para todos los documentos sin procesar.")

    return GenerateEmbeddingsResponse(
        message="Embeddings generated successfully for all documents"
    )

logger.info(f"[DEBUG] DOCUMENTS keys: {list(DOCUMENTS.keys())}")

@app.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest):
    logger.info(f"[SEARCH] Consulta recibida: '{payload.query}'")

    try:
        results_raw = search_similar_chunks(payload.query, n_results=3)
    except Exception:
        logger.error("[SEARCH] Error al procesar la búsqueda.", exc_info=True)
        raise HTTPException(status_code=500, detail="El servicio externo no pudo procesar la solicitud en este momento.")

    items = [
        SearchResultItem(
            document_id=r["document_id"],
            title=r["title"],
            content_snippet=r["content_snippet"],
            similarity_score=r["similarity_score"],
        )
        for r in results_raw
    ]

    logger.info(f"[SEARCH] {len(items)} resultados devueltos para la consulta.")

    return SearchResponse(results=items)


@app.post("/query", response_model=AskResponse)
def query(payload: AskRequest):
    logger.info(f"[QUERY] Pregunta recibida: '{payload.question}'")

    try:
        rag_result = rag_answer(payload.question)
    except Exception:
        logger.error("[QUERY] Error interno al generar respuesta.", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="El servicio externo no pudo procesar la solicitud en este momento."
        )

    logger.info(
        f"[QUERY] Respuesta generada | grounded={rag_result['grounded']} | similitud={rag_result['similarity_score']:.3f}"
    )

    return AskResponse(
    question=payload.question,
    answer=rag_result["answer"],
    context_used=rag_result["context_used"],
    similarity_score=rag_result["similarity_score"],
    grounded=rag_result["grounded"],
    source_document=rag_result.get("source_document"),
    chunk_id=rag_result.get("chunk_id"),
)



if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)