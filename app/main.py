import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi_mcp import FastApiMCP

from app.api.routes import router as api_router

# Create FastAPI app
app = FastAPI(title="MCP Backend API")

# Include API routes
app.include_router(api_router, prefix="/api")

# Create an MCP server based on this app with proper configuration
mcp = FastApiMCP(
    app,
    include_operations = ["list_documents", "search_documents", "upload_documents", "upload_folder", "delete_document", "delete_document_mcp"],
)

# Mount the MCP server with explicit prefix
mcp.mount()

# Set up CORS - needed for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a simple root endpoint that provides API information
@app.get("/")
async def root():
    return {
        "name": "MCP Backend API",
        "version": "1.0.0",
        "description": "Backend API for MCP-based chat application",
        "endpoints": [
            {"path": "/api/chat", "description": "Chat endpoint for supervisor workflow"},
            {"path": "/api/chat/status", "description": "Check status of chat system"},
            {"path": "/api/documents", "description": "Document management endpoints"}
        ]
    }

if __name__ == "__main__":    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
