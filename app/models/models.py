from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class DocumentResponse(BaseModel):
    document_id: str
    filename: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]


class StatusResponse(BaseModel):
    status: str
    message: str
