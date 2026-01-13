"""
Module for processing and chunking documents
"""
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes documents by chunking them into smaller pieces
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_documents(self, pages: List[Dict]) -> List[Dict]:
        """
        Chunk documents into smaller pieces with metadata
        
        Args:
            pages: List of page dictionaries with 'title', 'content', 'id', 'url'
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        all_chunks = []
        
        for page in pages:
            try:
                # Split the content into chunks
                text_chunks = self.text_splitter.split_text(page['content'])
                
                # Create chunk documents with metadata
                for i, chunk in enumerate(text_chunks):
                    chunk_doc = {
                        'content': chunk,
                        'metadata': {
                            'page_id': page.get('id'),
                            'page_title': page.get('title'),
                            'page_url': page.get('url'),
                            'chunk_index': i,
                            'space': page.get('space', 'unknown')
                        }
                    }
                    all_chunks.append(chunk_doc)
            
            except Exception as e:
                logger.warning(f"Error chunking page {page.get('id')}: {e}")
                continue
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
        return all_chunks
    
    def process_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Process pages: chunk them and return formatted documents
        
        Args:
            pages: List of page dictionaries
            
        Returns:
            List of processed chunk documents
        """
        return self.chunk_documents(pages)

