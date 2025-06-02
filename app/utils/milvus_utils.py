from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document

from app.core.config import settings
import os
import hashlib
import uuid

class MilvusDocStore:
    def __init__(self):
        """Initialize Milvus document store with OpenAI embeddings."""
        self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        self.collection_name = settings.milvus_collection_name
        
        # Initialize connection
        self.vector_store = Milvus(
            embedding_function=self.embeddings,
            collection_name=self.collection_name,
            connection_args={"host": settings.milvus_host, "port": settings.milvus_port},
        )

    def _generate_document_id(self, filename):
        """Generate a unique ID for a document based on its filename."""
        return hashlib.md5(filename.encode()).hexdigest()

    def add_document(self, file_path, document_id=None):
        """Add a document to the Milvus vector store."""
        try:
            with open(file_path, "r") as f:
                text = f.read()
            
            # Generate a document ID if not provided
            if not document_id:
                document_id = self._generate_document_id(os.path.basename(file_path))
            
            # Split text into chunks
            texts = self.text_splitter.split_text(text)
            
            # Create documents with metadata
            documents = [
                Document(
                    page_content=t,
                    metadata={
                        "source": os.path.basename(file_path),
                        "document_id": document_id,
                        "chunk_id": f"{document_id}_{i}"
                    }
                )
                for i, t in enumerate(texts)
            ]
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            return {"document_id": document_id, "chunks": len(texts)}
        except Exception as e:
            raise Exception(f"Error adding document: {str(e)}")

    def delete_document(self, document_id):
        """Delete a document from Milvus by document_id."""
        try:
            # Delete using filter by metadata
            self.vector_store.delete({"document_id": document_id})
            return {"status": "success", "document_id": document_id}
        except Exception as e:
            raise Exception(f"Error deleting document: {str(e)}")

    def list_documents(self):
        """List all documents in the store."""
        try:
            # In a real implementation, you might want to query Milvus for this
            # This is a simple approximation using retrieval
            results = self.vector_store.similarity_search("", k=100)
            
            # Extract unique document IDs from results
            documents = {}
            for doc in results:
                doc_id = doc.metadata.get("document_id")
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id, 
                        "source": doc.metadata.get("source", "unknown")
                    }
            
            return list(documents.values())
        except Exception as e:
            raise Exception(f"Error listing documents: {str(e)}")

    def query_documents(self, query, k=4):
        """Query the document store with a natural language query."""
        try:
            # Create a retrieval chain
            llm = ChatOpenAI(api_key=settings.openai_api_key)
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": k})
            )
            
            # Run the query
            response = qa_chain.invoke(query)
            return response
        except Exception as e:
            raise Exception(f"Error querying documents: {str(e)}")
