from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# /status
class StatusResponse(BaseModel):
    service: str
    status: str
    documents_loaded: int

# /generate-embeddings
class GenerateEmbeddingsRequest(BaseModel): 
    # si viene vacío, generar para todos   
    document_id: Optional[str] = Field(
        default=None,
        description="ID del documento a procesar; si se omite, se pueden procesar todos"
    ) 

class GenerateEmbeddingsResponse(BaseModel):
    message: str
    document_id: Optional[str] = None

# /search
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Texto de búsqueda")

class SearchResultItem(BaseModel):
    document_id: str
    title: str
    content_snippet: str
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[SearchResultItem]

# /query
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Pregunta del usuario")

class AskResponse(BaseModel):
    question: str
    answer: str
    context_used: str
    similarity_score: float
    grounded: bool
    source_document: Optional[str] = None
    chunk_id: Optional[str] = None
