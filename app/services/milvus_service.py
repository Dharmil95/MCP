import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import glob

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_unstructured import UnstructuredLoader

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MilvusDocumentService:
    """Service for managing documents in Milvus vector database"""
    
    def __init__(self):
        """Initialize the document service with Milvus and embedding model"""
        # Configure from environment
        self.milvus_uri = os.getenv("MILVUS_URI", "./milvus_data.db")
        self.collection_name = os.getenv("MILVUS_COLLECTION", "pdf_documents")
        
        # Initialize OpenAI embeddings
        self.embedding_function = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Initialize Milvus vector store
        self.vector_store = Milvus(
            embedding_function=self.embedding_function,
            collection_name=self.collection_name,
            connection_args={"uri": self.milvus_uri},
            auto_id=True,  # Let Milvus generate IDs automatically
            drop_old=False  # Preserve existing collection
        )
        
        # In-memory storage of document IDs to filenames
        # This would be replaced by a database in a production application
        self._documents = {}
    
    def process_pdf(self, file_path: str, original_filename: str) -> Dict:
        """
        Process a PDF file and store it in Milvus
        
        Args:
            file_path: Path to the temporary saved PDF file
            original_filename: Original filename of the uploaded file
            
        Returns:
            Dict with document_id and chunks information
        """
        try:
            # Generate a unique document ID
            document_id = str(uuid.uuid4())
            
            # Use UnstructuredLoader to load the PDF
            loader = UnstructuredLoader(file_path)
            docs = loader.load()
            
            # Process each document element to ensure proper metadata
            file_docs = []
            for i, doc in enumerate(docs):
                # Clean up metadata - filter out any problematic fields
                clean_metadata = {
                    "filename": original_filename,
                    "file_path": file_path,
                    "document_id": document_id,
                    "chunk_id": i,
                    "source": original_filename
                }
                
                # Copy over any basic string or numeric metadata that might be useful
                for key, value in doc.metadata.items():
                    if isinstance(value, (str, int, float, bool)) and key not in ['languages']:
                        clean_metadata[key] = value
                
                # Replace document metadata with clean metadata
                doc.metadata = clean_metadata
                file_docs.append(doc)
            
            # Split documents into chunks for better retrieval
            chunks = self.text_splitter.split_documents(file_docs)
            
            # Add document chunks to Milvus
            self.vector_store.add_documents(documents=chunks)
            
            # Store the document in our in-memory map
            self._documents[document_id] = {
                "filename": original_filename,
                "document_id": document_id,
                "chunks": len(chunks)
            }
            
            return {
                "document_id": document_id,
                "filename": original_filename,
                "chunks": len(chunks)
            }
            
        except Exception as e:
            # In a real application, we would log the error
            print(f"Error processing PDF: {str(e)}")
            raise
    
    def list_documents(self) -> List[Dict]:
        """
        List all documents stored in Milvus
        
        Returns:
            List of dictionaries with document information
        """
        return [
            {"document_id": doc_id, "filename": doc_info["filename"]}
            for doc_id, doc_info in self._documents.items()
        ]
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from Milvus
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete using filter expression based on document_id in metadata
            self.vector_store.delete(expr=f'document_id == "{document_id}"')
            
            # Remove from our tracking dictionary
            if document_id in self._documents:
                del self._documents[document_id]
                
            return True
        except Exception as e:
            # In a real application, we would log the error
            print(f"Error deleting document: {str(e)}")
            return False
    
    def search_documents(
        self, 
        query: str, 
        document_id: Optional[str] = None, 
        limit: int = 5
    ) -> List[Document]:
        """
        Search documents in Milvus
        
        Args:
            query: Search query
            document_id: Optional document ID to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of Document objects matching the query
        """
        try:
            if document_id:
                # Search within a specific document
                filter_expr = f'document_id == "{document_id}"'
                results = self.vector_store.similarity_search(
                    query, k=limit, expr=filter_expr
                )
            else:
                # Search across all documents
                results = self.vector_store.similarity_search(query, k=limit)
                
            return results
        except Exception as e:
            # In a real application, we would log the error
            print(f"Error searching documents: {str(e)}")
            raise
    
    def process_folder(self, folder_path: str) -> Dict:
        """
        Process all documents in a folder and store them in Milvus
        
        Args:
            folder_path: Path to the folder containing documents
            
        Returns:
            Dict with processing results and statistics
        """
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists() or not folder_path.is_dir():
                raise ValueError(f"Folder path does not exist or is not a directory: {folder_path}")
            
            # Find all PDF files in the folder (including subdirectories)
            pdf_files = list(folder_path.glob("**/*.pdf"))
            
            if not pdf_files:
                return {
                    "status": "success",
                    "message": "No PDF files found in folder",
                    "processed_files": [],
                    "total_files": 0,
                    "successful": 0,
                    "failed": 0
                }
            
            results = []
            successful = 0
            failed = 0
            
            for pdf_file in pdf_files:
                try:
                    # Process each PDF file
                    result = self.process_pdf(
                        file_path=str(pdf_file),
                        original_filename=pdf_file.name
                    )
                    
                    results.append({
                        "filename": pdf_file.name,
                        "file_path": str(pdf_file),
                        "document_id": result["document_id"],
                        "chunks": result["chunks"],
                        "status": "success"
                    })
                    successful += 1
                    
                except Exception as e:
                    results.append({
                        "filename": pdf_file.name,
                        "file_path": str(pdf_file),
                        "status": "error",
                        "message": str(e)
                    })
                    failed += 1
            
            return {
                "status": "completed",
                "message": f"Processed {len(pdf_files)} files from folder. Success: {successful}, Failed: {failed}",
                "folder_path": str(folder_path),
                "processed_files": results,
                "total_files": len(pdf_files),
                "successful": successful,
                "failed": failed
            }
            
        except Exception as e:
            print(f"Error processing folder: {str(e)}")
            raise

    def process_multiple_files(self, file_paths: List[str]) -> Dict:
        """
        Process multiple document files and store them in Milvus
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dict with processing results and statistics
        """
        try:
            results = []
            successful = 0
            failed = 0
            
            for file_path in file_paths:
                try:
                    file_path = Path(file_path)
                    if not file_path.exists():
                        results.append({
                            "filename": file_path.name,
                            "file_path": str(file_path),
                            "status": "error",
                            "message": "File does not exist"
                        })
                        failed += 1
                        continue
                    
                    if not file_path.suffix.lower() == '.pdf':
                        results.append({
                            "filename": file_path.name,
                            "file_path": str(file_path),
                            "status": "error",
                            "message": "Only PDF files are supported"
                        })
                        failed += 1
                        continue
                    
                    # Process the PDF file
                    result = self.process_pdf(
                        file_path=str(file_path),
                        original_filename=file_path.name
                    )
                    
                    results.append({
                        "filename": file_path.name,
                        "file_path": str(file_path),
                        "document_id": result["document_id"],
                        "chunks": result["chunks"],
                        "status": "success"
                    })
                    successful += 1
                    
                except Exception as e:
                    results.append({
                        "filename": file_path.name if 'file_path' in locals() else "unknown",
                        "file_path": str(file_path) if 'file_path' in locals() else "unknown",
                        "status": "error",
                        "message": str(e)
                    })
                    failed += 1
            
            return {
                "status": "completed",
                "message": f"Processed {len(file_paths)} files. Success: {successful}, Failed: {failed}",
                "processed_files": results,
                "total_files": len(file_paths),
                "successful": successful,
                "failed": failed
            }
            
        except Exception as e:
            print(f"Error processing multiple files: {str(e)}")
            raise
