from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile
import shutil
import time
from pathlib import Path
from pydantic import BaseModel

from app.services.milvus_service import MilvusDocumentService
from app.models.models import (
    DocumentListResponse, 
    DocumentResponse, 
    SearchResponse, 
    SearchResult,
    StatusResponse
)

# Request models for JSON endpoints
class FolderUploadRequest(BaseModel):
    folder_path: str

router = APIRouter()

# Create a single instance of the service
milvus_service = MilvusDocumentService()

@router.post("/documents/upload", response_model=StatusResponse, operation_id="upload_documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload PDF documents to be stored in Milvus.
    
    The documents will be processed, split into chunks, and indexed for semantic search.
    """
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    for file in files:
        # Check file type
        if not file.filename.endswith('.pdf'):
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "Only PDF files are supported"
            })
            continue
        
        # Save file temporarily
        temp_file = None
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = Path("app/uploads")
            upload_dir.mkdir(exist_ok=True)
            
            # Save the file with a unique name to prevent overwriting
            file_location = f"app/uploads/{int(time.time())}_{file.filename}"
            with open(file_location, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            # Process the PDF
            result = milvus_service.process_pdf(
                file_path=file_location,
                original_filename=file.filename
            )
            
            results.append({
                "filename": file.filename,
                "document_id": result["document_id"],
                "chunks": result["chunks"],
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
        finally:
            # Close the file
            file.file.close()
    
    successful = len([r for r in results if r.get("status") == "success"])
    failed = len(results) - successful
    
    return {
        "status": "completed",
        "message": f"Processed {len(results)} files. Success: {successful}, Failed: {failed}",
        "details": results
    }

@router.post("/documents/upload-folder", response_model=StatusResponse, operation_id="upload_folder")
async def upload_folder(request: FolderUploadRequest):
    """
    Upload all PDF documents from a folder to be stored in Milvus.
    
    Recursively processes all PDF files in the specified folder and its subdirectories.
    The documents will be processed, split into chunks, and indexed for semantic search.
    """
    
    folder_path = request.folder_path
    
    if not folder_path:
        raise HTTPException(status_code=400, detail="Folder path is required")
    
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail=f"Folder path does not exist: {folder_path}")
    
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
    
    try:
        # Process all PDF files in the folder
        result = milvus_service.process_folder(folder_path)
        
        return {
            "status": result["status"],
            "message": result["message"],
            "details": {
                "folder_path": folder_path,
                "total_files": result["total_files"],
                "successful": result["successful"],
                "failed": result["failed"],
                "processed_files": result["processed_files"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing folder: {str(e)}"
        )

@router.get("/documents", response_model=DocumentListResponse, operation_id="list_documents")
async def list_documents():
    """
    List all documents stored in Milvus.
    
    Returns a list of all uploaded documents with their IDs and filenames.
    """
    documents = milvus_service.list_documents()
    return {"documents": documents}

@router.delete("/documents/{document_id}", response_model=StatusResponse, operation_id="delete_document")
async def delete_document(document_id: str):
    """
    Delete a document from Milvus.
    
    Returns a status message indicating success or failure.
    """
    success = milvus_service.delete_document(document_id)
    
    if success:
        return {
            "status": "success",
            "message": f"Document {document_id} deleted successfully"
        }
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"Failed to delete document {document_id}"
        )

@router.post("/documents/delete", response_model=StatusResponse, operation_id="delete_document_mcp")
async def delete_document_mcp(request: dict):
    """
    Delete a document from Milvus using a POST request.
    This allows the MCP client to use call_tool instead of requiring a direct DELETE request.
    
    Returns a status message indicating success or failure.
    """
    document_id = request.get("document_id")
    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")
        
    success = milvus_service.delete_document(document_id)
    
    if success:
        return {
            "status": "success",
            "message": f"Document {document_id} deleted successfully"
        }
    else:
        raise HTTPException(
            status_code=404, 
            detail=f"Failed to delete document {document_id}"
        )

@router.get("/documents/search", response_model=SearchResponse, operation_id="search_documents")
async def search_documents(
    query: str, 
    document_id: Optional[str] = None,
    limit: int = Query(5, ge=1, le=50)
):
    """
    Search documents in Milvus using vector similarity.
    
    Performs semantic search on the document chunks using the query.
    Optionally filters by document_id and limits the number of results.
    """
    try:
        results = milvus_service.search_documents(
            query=query,
            document_id=document_id,
            limit=limit
        )
        
        # Convert the results to SearchResult objects
        search_results = [
            SearchResult(
                content=doc.page_content,
                metadata=doc.metadata
            )
            for doc in results
        ]
        
        return {
            "query": query,
            "results": search_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during search: {str(e)}"
        )
