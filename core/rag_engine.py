import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain.prompts import PromptTemplate
import re
import logging

from .vector_store import VectorStoreManager
from .document_processor import DocumentProcessor

#load_dotenv()
#openai_api_key = os.getenv('OPENAI_API_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """Advanced RAG engine for legal document consultation"""
    
    def __init__(self, openai_api_key: str, vector_store_manager: VectorStoreManager, model_name: str = "gpt-3.5-turbo"):
        #load_dotenv()
    #openai_api_key = os.getenv('OPENAI_API_KEY')

        self.openai_api_key = openai_api_key
        self.vector_store_manager = vector_store_manager
        
        # Initialize OpenAI chat model
        self.llm = ChatOpenAI(
            #openai_api_key=self.openai_api_key,
            model=model_name,
            temperature=0.1  # It will auto-detect OPENAI_API_KEY from env
        )

        # Conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Legal-specific prompt template
        self.legal_prompt = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""You are a professional legal AI assistant specializing in BNS (Bharatiya Nyaya Sanhita) legal documents. 
            
Provide accurate, well-structured legal information based ONLY on the provided context.

Context from legal documents:
{context}

Previous conversation:
{chat_history}

Question: {question}

Instructions:
1. Provide clear, professional legal information
2. Cite specific sections and sources when available
3. Use proper legal terminology
4. If information is not in the context, clearly state this limitation
5. Structure your response with clear headings when appropriate
6. Include relevant BNS section numbers when applicable

IMPORTANT: This is for informational purposes only and does not constitute legal advice. Users should consult qualified legal professionals for specific legal matters.

Answer:"""
        )
        
        self.qa_chain = None
        self._initialize_qa_chain()
    
    def _initialize_qa_chain(self):
        """Initialize the conversational retrieval chain"""
        if not self.vector_store_manager.is_initialized():
            logger.warning("Vector store not initialized, QA chain unavailable")
            return
        
        try:
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vector_store_manager.get_vector_store().as_retriever( search_kwargs={"k": 5} ),
                memory=self.memory,
                return_source_documents=True,
                #verbose=True
            )
            logger.info("QA chain initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing QA chain: {str(e)}")
    
    def process_query(self, query: str, session_id: str) -> Dict[str, Any]:
        """Process legal query and return comprehensive response"""
        if not self.qa_chain:
            return self._create_error_response("System not initialized", query)
        
        try:
            # Classify query type
            query_type = self._classify_query(query)
            
            # Get relevant documents first for confidence calculation
            relevant_docs = self.vector_store_manager.similarity_search_with_metadata(query, k=5)
            
            # Process with conversational chain
            result = self.qa_chain({
                "question": query,
                "chat_history": []  # Could be enhanced with session-specific history
            })
            
            # Calculate confidence score
            confidence = self._calculate_confidence(query, relevant_docs, result.get("answer", ""))
            
            # Extract BNS citations
            citations = self._extract_bns_citations(result.get("answer", ""))
            
            # Format response
            response = {
                "success": True,
                "answer": result.get("answer", ""),
                "confidence": confidence,
                "query_type": query_type,
                "retrieved_docs_count": len(relevant_docs),
                "sources": self._format_sources(result.get("source_documents", [])),
                "bns_citations": citations,
                "session_id": session_id,
                "timestamp": self._get_timestamp(),
                "model": "gpt-3.5-turbo",
                "relevant_excerpts": [
                    {
                        "content": doc["content"][:300] + "...",
                        "source": doc["source"],
                        "relevance_score": doc["relevance_score"],
                        "legal_section": doc["legal_section"]
                    }
                    for doc in relevant_docs[:3]  # Top 3 most relevant
                ]
            }
            
            logger.info(f"Successfully processed query of type: {query_type}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return self._create_error_response(str(e), query)
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of legal query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["what is", "define", "definition", "meaning"]):
            return "definition"
        elif any(word in query_lower for word in ["how to", "procedure", "process", "steps"]):
            return "procedure"
        elif any(word in query_lower for word in ["penalty", "punishment", "fine", "imprisonment"]):
            return "penalty"
        elif any(word in query_lower for word in ["section", "article", "provision"]):
            return "citation"
        elif any(word in query_lower for word in ["compare", "difference", "versus", "vs"]):
            return "comparison"
        else:
            return "general"
    
    def _calculate_confidence(self, query: str, relevant_docs: List[Dict], answer: str) -> float:
        """Calculate confidence score based on relevance and answer quality"""
        if not relevant_docs:
            return 0.1
        
        # Base confidence from document relevance
        avg_relevance = sum(doc["relevance_score"] for doc in relevant_docs) / len(relevant_docs)
        
        # Answer quality factors
        answer_length_factor = min(len(answer) / 500, 1.0)  # Longer answers tend to be more comprehensive
        citation_factor = 1.2 if self._extract_bns_citations(answer) else 1.0
        
        # Combine factors
        confidence = min(avg_relevance * answer_length_factor * citation_factor, 1.0)
        
        return round(confidence, 2)
    
    def _extract_bns_citations(self, text: str) -> List[str]:
        """Extract BNS section citations from text"""
        citations = []
        
        # Common citation patterns
        patterns = [
            r'Section\s+(\d+)',
            r'Sec\.\s+(\d+)',
            r'BNS\s+(\d+)',
            r'§\s*(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend([f"Section {match}" for match in matches])
        
        return list(set(citations))  # Remove duplicates
    
    def _format_sources(self, source_documents: List[Document]) -> List[Dict[str, Any]]:
        """Format source documents for response"""
        sources = []
        
        for doc in source_documents:
            sources.append({
                "source_file": doc.metadata.get("source_file", "Unknown"),
                "legal_section": doc.metadata.get("legal_section", "General"),
                "chunk_id": doc.metadata.get("chunk_id", "unknown"),
                "content_preview": doc.page_content[:200] + "..."
            })
        
        return sources
    
    def _create_error_response(self, error_message: str, query: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": error_message,
            "answer": "I apologize, but I'm unable to process your query at this time. Please try again later.",
            "confidence": 0.0,
            "query_type": "error",
            "retrieved_docs_count": 0,
            "sources": [],
            "bns_citations": [],
            "timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "rag_engine": "initialized" if self.qa_chain else "not_initialized",
            "vector_store": self.vector_store_manager.get_vector_store_stats(),
            "llm_model": "gpt-3.5-turbo",
            "memory_initialized": self.memory is not None,
            "timestamp": self._get_timestamp()
        }