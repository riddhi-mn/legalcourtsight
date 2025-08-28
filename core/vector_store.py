import os
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import logging
import httpx
import openai   

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    """ChromaDB vector store management for legal documents"""
    
    def __init__(self, persist_directory: str, openai_api_key: str):
        self.persist_directory = persist_directory

        custom_client = httpx.Client(trust_env=False)

        self.embeddings = OpenAIEmbeddings(
            #openai_api_key=openai_api_key,
            model="text-embedding-ada-002",
            http_client=custom_client
        )
        self.vector_store: Optional[Chroma] = None
        self.collection_name = "legal_documents"
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
    
    def initialize_vector_store(self, documents: Optional[List[Document]] = None) -> bool:
        """Initialize vector store with optional documents"""
        try:
            # ChromaDB client settings
            chroma_settings = Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            )
            
            if documents and len(documents) > 0:
                logger.info(f"Creating new vector store with {len(documents)} documents")
                self.vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory,
                    collection_name=self.collection_name
                )
            else:
                logger.info("Loading existing vector store")
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            return False
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add new documents to existing vector store"""
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return False
        
        try:
            self.vector_store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return False
    
    def similarity_search(self, query: str, k: int = 5, score_threshold: float = 0.0) -> List[Document]:
        """Perform similarity search with confidence threshold"""
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        
        try:
            # Search with scores
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Filter by score threshold
            filtered_results = [
                doc for doc, score in results 
                if score >= score_threshold
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant documents for query")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    def similarity_search_with_metadata(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Enhanced similarity search with metadata and scores"""
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            enhanced_results = []
            for doc, score in results:
                enhanced_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'relevance_score': float(score),
                    'source': doc.metadata.get('source_file', 'Unknown'),
                    'legal_section': doc.metadata.get('legal_section', 'General'),
                    'chunk_id': doc.metadata.get('chunk_id', 'unknown')
                })
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in enhanced similarity search: {str(e)}")
            return []
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        if not self.vector_store:
            return {"status": "not_initialized"}
        
        try:
            # Get collection info
            collection = self.vector_store._collection
            count = collection.count()
            
            return {
                "status": "initialized",
                "document_count": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "embedding_model": "text-embedding-ada-002"
            }
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def is_initialized(self) -> bool:
        """Check if vector store is properly initialized"""
        return self.vector_store is not None
    
    def get_vector_store(self):
        """Get the vector store instance"""
        return self.vector_store
    
    def reset_vector_store(self) -> bool:
        """Reset vector store (delete all data)"""
        try:
            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)
                os.makedirs(self.persist_directory, exist_ok=True)
            
            self.vector_store = None
            logger.info("Vector store reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting vector store: {str(e)}")
            return False