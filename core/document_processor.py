import os
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Advanced document processing for legal documents"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Legal-aware text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence endings
                ", ",    # Clause separators
                " ",     # Word boundaries
                ""
            ]
        )
    
    def load_documents(self, documents_path: str) -> List[Document]:
        """Load and process all PDF documents from directory"""
        documents = []
        
        if not os.path.exists(documents_path):
            logger.warning(f"Documents path does not exist: {documents_path}")
            return documents
        
        pdf_files = [f for f in os.listdir(documents_path) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {documents_path}")
            return documents
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            file_path = os.path.join(documents_path, pdf_file)
            try:
                loader = PyPDFLoader(file_path)
                file_documents = loader.load()
                
                # Add metadata
                for doc in file_documents:
                    doc.metadata.update({
                        'source_file': pdf_file,
                        'file_path': file_path,
                        'document_type': 'legal_document',
                        'processed_at': str(os.path.getmtime(file_path))
                    })
                
                documents.extend(file_documents)
                logger.info(f"Loaded {len(file_documents)} pages from {pdf_file}")
                
            except Exception as e:
                logger.error(f"Error loading {pdf_file}: {str(e)}")
        
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks with legal-aware segmentation"""
        if not documents:
            logger.warning("No documents to chunk")
            return []
        
        chunks = []
        
        for doc in documents:
            try:
                # Split document into chunks
                doc_chunks = self.text_splitter.split_documents([doc])
                
                # Enhance chunks with legal-specific metadata
                for i, chunk in enumerate(doc_chunks):
                    chunk.metadata.update({
                        'chunk_id': f"{doc.metadata.get('source_file', 'unknown')}_{i}",
                        'chunk_index': i,
                        'total_chunks': len(doc_chunks),
                        'chunk_size': len(chunk.page_content),
                        'legal_section': self._extract_legal_section(chunk.page_content)
                    })
                
                chunks.extend(doc_chunks)
                
            except Exception as e:
                logger.error(f"Error chunking document: {str(e)}")
        
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def _extract_legal_section(self, text: str) -> str:
        """Extract legal section number from text"""
        import re
        
        # Common legal section patterns
        patterns = [
            r'Section\s+(\d+)',
            r'Sec\.\s+(\d+)',
            r'§\s*(\d+)',
            r'Article\s+(\d+)',
            r'Chapter\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "General"
    
    def get_processing_stats(self, chunks: List[Document]) -> Dict[str, Any]:
        """Get document processing statistics"""
        if not chunks:
            return {"total_chunks": 0, "total_documents": 0}
        
        source_files = set()
        total_chars = 0
        legal_sections = {}
        
        for chunk in chunks:
            source_files.add(chunk.metadata.get('source_file', 'unknown'))
            total_chars += len(chunk.page_content)
            
            legal_section = chunk.metadata.get('legal_section', 'General')
            legal_sections[legal_section] = legal_sections.get(legal_section, 0) + 1
        
        return {
            "total_chunks": len(chunks),
            "total_documents": len(source_files),
            "total_characters": total_chars,
            "average_chunk_size": total_chars // len(chunks) if chunks else 0,
            "legal_sections": legal_sections,
            "source_files": list(source_files)
        }