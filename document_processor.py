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
    
    def chunk_documents(self, pages: List[Dict], source_type: str = 'confluence') -> List[Dict]:
        """
        Chunk documents into smaller pieces with metadata
        
        Args:
            pages: List of page/issue dictionaries with 'title', 'content', 'id', 'url'
            source_type: Type of source ('confluence' or 'jira')
            
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
                    if source_type == 'jira':
                        chunk_doc = {
                            'content': chunk,
                            'metadata': {
                                'issue_id': page.get('id'),
                                'issue_key': page.get('key'),
                                'page_title': page.get('title'),
                                'page_url': page.get('url'),
                                'chunk_index': i,
                                'project': page.get('project', 'unknown'),
                                'status': page.get('status', ''),
                                'issue_type': page.get('issue_type', ''),
                                'priority': page.get('priority', ''),
                                'source_type': 'jira'
                            }
                        }
                    else:  # confluence
                        chunk_doc = {
                            'content': chunk,
                            'metadata': {
                                'page_id': page.get('id'),
                                'page_title': page.get('title'),
                                'page_url': page.get('url'),
                                'chunk_index': i,
                                'space': page.get('space', 'unknown'),
                                'source_type': 'confluence'
                            }
                        }
                    all_chunks.append(chunk_doc)
            
            except Exception as e:
                logger.warning(f"Error chunking document {page.get('id')}: {e}")
                continue
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} {source_type} documents")
        return all_chunks
    
    def process_pages(self, pages: List[Dict], source_type: str = 'confluence') -> List[Dict]:
        """
        Process pages/issues: chunk them and return formatted documents
        
        Args:
            pages: List of page/issue dictionaries
            source_type: Type of source ('confluence' or 'jira')
            
        Returns:
            List of processed chunk documents
        """
        return self.chunk_documents(pages, source_type=source_type)

