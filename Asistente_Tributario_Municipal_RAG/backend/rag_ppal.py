import os
import re
from typing import List, Dict, Any

import numpy as np
import chromadb
from chromadb.config import Settings
import cohere
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

from storage import get_document

# ------------------------ LOGGING ------------------------
import logging
logger = logging.getLogger("RAG")
# ---------------------------------------------------------

load_dotenv()

# --------- Inicialización de Cohere y Chroma ---------

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2()  

chroma_client = chromadb.PersistentClient(path="chroma_db")

collection = chroma_client.get_or_create_collection(
    name="asistente_tributario_municipal",
    metadata={"hnsw:space": "cosine"},
)

# --------- Utilidades de texto ---------


def limpiar_texto(texto: str) -> str:
    """
    Normaliza saltos de línea y espacios.
    """
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip() 

# --------- SPLITTERS ---------

# Diferentes configuraciones para distintos tipos de documentos

# textos cortos
splitter_guias = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=80,
    separators=["\n\n", "\n", " ", ""],
)

# textos largos
splitter_codigo = RecursiveCharacterTextSplitter(
    chunk_size=3000,
    chunk_overlap=350,
    separators=["\n\n", "\n", " ", ""],
)

def infer_document_metadata(title: str) -> Dict[str, str]:
    t = title.lower()
    
    if "codigo" in t or "tributario" in t:
        return {"tipo_documento": "normativa", "tramite": "general"}

    if "guia" in t:
        return {"tipo_documento": "procedimiento", "tramite": "general"}

    if "art" in t and "25" in t:
        return {"tipo_documento": "protocolo_reclamo", "tramite": "reclamo"}

    if "autoridad" in t:
        return {"tipo_documento": "autoridad_operativa", "tramite": "general"}

    if "plan" in t:
        return {"tipo_documento": "regularizacion", "tramite": "general"}

    return {"tipo_documento": "desconocido", "tramite": "general"}


def chunk_document(content: str, title: str) -> List[str]:
    logger.info(f"[CHUNK] Iniciando chunking del documento. Longitud={len(content)} caracteres")

    limpio = limpiar_texto(content)
    meta = infer_document_metadata(title)

    if meta["tipo_documento"] == "normativa":
        chunks = splitter_codigo.split_text(limpio)
    else:
        chunks = splitter_guias.split_text(limpio)

    logger.info(f"[CHUNK] Documento dividido en {len(chunks)} chunks ({meta})")
    return chunks

# --------- Embeddings y almacenamiento en Chroma ---------

def generate_embeddings_for_document(doc_id: str, title: str, chunks: List[str]) -> List[str]:
    """
    Genera embeddings en lotes (batch) para evitar la limitación de Cohere
    que permite máximo 96 textos por request.
    Guarda embeddings y metadatos en Chroma.
    """

    logger.info(f"[EMBED] Generando embeddings para documento {doc_id} - '{title}' | {len(chunks)} chunks")
    
    MAX_BATCH = 90
    all_chunk_ids = []

    meta_doc = infer_document_metadata(title)

    for start in range(0, len(chunks), MAX_BATCH):
        batch = chunks[start:start + MAX_BATCH]

        logger.info(f"[EMBED] Procesando batch {start} - {start+len(batch)}")

        # === EMBEDDINGS ===
        response = co.embed(
            texts=batch,
            model="embed-multilingual-v3.0",
            input_type="search_document",
            embedding_types=["float"],
        )

        embeddings_np = np.array(response.embeddings.float, dtype=np.float32)

        # === IDS ===
        batch_ids = [f"{doc_id}_chunk_{start+i}" for i in range(len(batch))]
        all_chunk_ids.extend(batch_ids)

        # === METADATA ===
        metadatas = []
        for i in range(len(batch)):
            metadatas.append({
                "document_id": doc_id,
                "title": title,
                "tipo_documento": meta_doc["tipo_documento"],
                "tramite": meta_doc["tramite"],
                "chunk_index": start + i
            })

        # === Guardar en Chroma ===
        collection.add(
            ids=batch_ids,
            documents=batch,
            embeddings=embeddings_np.tolist(),
            metadatas=metadatas,
        )

        logger.info(f"[EMBED] Guardado batch con {len(batch)} chunks en Chroma")

    logger.info(f"[EMBED] Embeddings almacenados en Chroma para doc={doc_id}")
    return all_chunk_ids


def search_similar_chunks(query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    Busca los n chunks más similares para la consulta.
    Devuelve además los metadatos necesarios para grounding inteligente.
    """
    logger.info(f"[SEARCH] Buscando contexto para consulta: '{query}'")

    # ---- Embed de la query ----
    embed_resp = co.embed(
        texts=[query],
        model="embed-multilingual-v3.0",
        input_type="search_query",
        embedding_types=["float"],
    )

    query_emb = np.array(embed_resp.embeddings.float[0], dtype=np.float32)

    # ---- Búsqueda en Chroma ----
    result = collection.query(
        query_embeddings=[query_emb.tolist()],
        n_results=n_results,
    )

    docs = result["documents"][0]
    ids = result["ids"][0]
    distances = result["distances"][0]
    metadatas = result["metadatas"][0]

    items: List[Dict[str, Any]] = []

    # ---- Construcción de resultados ----
    for i in range(len(docs)):
        similarity = 1 - distances[i]

        items.append(
            {
                "chunk_id": ids[i],
                "document_id": metadatas[i].get("document_id"),
                "title": metadatas[i].get("title"),
                "tipo_documento": metadatas[i].get("tipo_documento"),
                "tramite": metadatas[i].get("tramite"),
                "chunk_index": metadatas[i].get("chunk_index"),
                "content_snippet": docs[i][:200],
                "similarity_score": float(similarity),
                "full_chunk": docs[i],
            }
        )

    logger.info(
        f"[SEARCH] Resultados encontrados: {len(items)} | "
        f"Mejor similitud={max(i['similarity_score'] for i in items):.3f}"
    )

    return items

# --------- RAG completo: usado por /ask ---------

SYSTEM_PROMPT = f"""
Eres un Asistente de Orientación Tributaria Municipal especializado en resolver dudas sobre:

- Reclamo por Falta de Imputación de Pago
- Reclamo por Pago Duplicado
- Consulta / Emisión / Pago de Cedulones
- Plan de Pago de Deudas Tributarias

Tu función es orientar al ciudadano de forma clara, precisa y responsable.

REGLAS OBLIGATORIAS:
1) SOLO puedes responder usando la información del CONTEXTO proporcionado.
2) Si algo NO está en los documentos, NO lo inventes.
3) Si falta información, indícalo claramente y orienta qué datos son necesarios.
4) La respuesta SIEMPRE debe ser en español.
5) NO usar emojis.
6) No incorporar normativa externa ni interpretar más allá de lo que dicen los documentos.
7) Si el usuario pregunta algo fuera del alcance, responde:
   "La base de conocimiento disponible no contiene información suficiente para responder con certeza este caso."
8) Si el usuario consulta si existe devolución de dinero y los documentos indican que la solución es la generación de crédito a favor, debes responder claramente que la resolución prevista es crédito imputable, y que no se menciona devolución directa. 
No respondas “no hay información” si existe un mecanismo documentado que responde de manera indirecta la duda.

PROHIBICIÓN ESTRICTA DE CONTENIDO NORMATIVO:
Está TERMINANTEMENTE PROHIBIDO mencionar:
- “artículo”
- “ordenanza”
- “ley”
- “decreto”
- numeración legal
- citas normativas
- frases como “según normativa vigente”, “según artículo…”

Si los documentos mencionan normativa o artículos, NO los cites. 
Solo expresa los requisitos y pasos operativos.

REGLA ESPECIAL PARA DOCUMENTO SOBRE NOTAS (Artículo 25):
Si la respuesta requiere que el ciudadano presente una nota, 
DEBES extraer literalmente lo que el documento indica sobre:
- Qué nota debe presentar
- Qué debe contener la nota
- Qué documentación debe acompañar

Debes responder en lenguaje operativo y ciudadano:
"Debe presentar una nota que contenga…"
Nunca decir “citar artículo”, “de acuerdo al artículo”, etc.

PRECISIÓN Y FOCO:
- Responde únicamente lo que el usuario pregunta.
- No agregues información adicional que el usuario no solicitó.
- No incluyas recomendaciones extra ni explicaciones innecesarias.
- Usa únicamente información del contexto.
- Si la respuesta es un concepto, define sin extenderte.

ESTILO DE RESPUESTA:
- Claro
- Administrativo pero accesible
- Operativo
- Concreto
- Máximo 3 a 6 oraciones
- Sin introducciones ni cierres

SI EL USUARIO SOLICITA DEFINICIÓN:
- Da una definición breve y directa.
- No agregues pasos operativos a menos que él los pida.

"""

def rag_answer(question: str) -> Dict[str, Any]:
    """
    Pipeline RAG completo con grounding robusto:
    - Detecta intención de "nota"
    - Si aplica → restringe búsqueda SOLO a Art 25
    - Sino → retrieval normal
    - Evalúa grounding
    - Genera respuesta segura
    """
    logger.info(f"[RAG] Pregunta recibida: '{question}'")

    # -------- DETECCIÓN DE INTENCIÓN DE NOTA --------
    requires_note = any(w in question.lower() for w in [
        "nota",
        "presentar nota",
        "nota formal",
        "nota de reclamo",
        "nota para reclamo",
        "escribir nota",
        "carta",
        "como hago la nota"
    ])

    # -------- MODO ESPECIAL ART 25 / NOTAS --------
    if requires_note:
        logger.info("[RAG] INTENCIÓN DETECTADA: MODO NOTA ACTIVADO")

        # Embedding del query con Cohere (MISMA dimensión que Chroma)
        emb = co.embed(
            texts=[question],
            model="embed-multilingual-v3.0",
            input_type="search_query",
            embedding_types=["float"],
        )

        query_emb = np.array(emb.embeddings.float, dtype=np.float32).tolist()

        chroma_results = collection.query(
            query_embeddings=query_emb,
            n_results=5,
            where={
                "tipo_documento": "protocolo_reclamo"     # <-- Art 25
            }
        )

        results = []
        for i in range(len(chroma_results["ids"][0])):
            results.append({
                "full_chunk": chroma_results["documents"][0][i],
                "similarity_score": 1 - chroma_results["distances"][0][i],
                "tramite": chroma_results["metadatas"][0][i].get("tramite"),
                "tipo_documento": chroma_results["metadatas"][0][i].get("tipo_documento"),
                "title": chroma_results["metadatas"][0][i].get("title"),
                "chunk_id": chroma_results["ids"][0][i]
            })

        logger.info("[RAG] CONTEXTO RESTRINGIDO EXCLUSIVAMENTE A ART 25")

    # -------- FLUJO NORMAL --------
    else:
        results = search_similar_chunks(question, n_results=5)

    # ---- DEBUG ----
    logger.info("[RAG] Contexto recuperado para responder:")
    for i, r in enumerate(results):
        try:
            logger.info(
                f"CHUNK {i} | score={r['similarity_score']:.3f} | "
                f"doc_id={r.get('document_id','?')} | tipo={r.get('tipo_documento','?')}"
            )
            logger.info(r["full_chunk"][:400] + "...\n")
        except Exception as e:
            logger.warning(f"[RAG] No se pudo loguear chunk {i}: {e}")

    if not results:
        logger.warning("[RAG] No se encontraron resultados. Respuesta sin grounding.")
        return {
            "answer": "No cuento con información suficiente para responder a esta consulta.",
            "context_used": "",
            "similarity_score": 0.0,
            "grounded": False,
        }

    # -------- SIMILITUD ---------- 
    scores = [r["similarity_score"] for r in results]
    best_score = max(scores)
    avg_score = sum(scores) / len(scores)

    context_text = "\n\n".join(r["full_chunk"] for r in results)

    # -------- CONSISTENCIA DE METADATOS --------
    tramites = [r["tramite"] for r in results if r.get("tramite")]
    tipo_docs = [r["tipo_documento"] for r in results if r.get("tipo_documento")]

    tramite_consistente = len(set(tramites)) == 1 if tramites else False
    tipo_consistente = len(set(tipo_docs)) == 1 if tipo_docs else False

    confianza = (
        best_score >= 0.45 and
        avg_score >= 0.35 and
        (tramite_consistente or tipo_consistente)
    )

    logger.info(
        f"[GROUND] best={best_score:.3f} | avg={avg_score:.3f} | "
        f"tramite_consistente={tramite_consistente} | tipo_consistente={tipo_consistente}"
    )

    # -------- Grounding insuficiente --------
    if not confianza:
        logger.warning("[RAG] Grounding insuficiente. Se responde seguro sin inventar.")
        return {
            "answer": "No cuento con información suficiente para responder a esta consulta.",
            "context_used": context_text[:400],
            "similarity_score": float(best_score),
            "grounded": False,
        }

    # -------- LLM --------
    user_prompt = f"""
Contexto de las historias:
\"\"\"{context_text}\"\"\"\n
Pregunta:
{question}
"""

    logger.info("[RAG] Enviando prompt al modelo Cohere.")

    chat_resp = co.chat(
        model="command-r-plus-08-2024",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=400,
    )

    answer_text = chat_resp.message.content[0].text.strip()

    logger.info("[RAG] Respuesta generada con grounding=True")

    best_chunk = max(results, key=lambda r: r["similarity_score"])

    return {
        "answer": answer_text,
        "context_used": context_text[:400],
        "similarity_score": float(best_score),
        "grounded": True,
        "source_document": best_chunk.get("title"),
        "chunk_id": best_chunk.get("chunk_id")
    }

