"""
Module for vector store operations using ChromaDB
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages vector store operations using ChromaDB
    """
    
    def __init__(self, collection_name: str = None, persist_directory: str = None):
        """
        Initialize ChromaDB client and collection
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name or config.COLLECTION_NAME
        self.persist_directory = persist_directory or config.VECTOR_STORE_PATH
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )
            logger.info(f"Connected to collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Add documents to the vector store
        
        Args:
            chunks: List of chunk dictionaries with 'content' and 'metadata'
            embeddings: List of embedding vectors
        """
        try:
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                # Create unique ID - handle both Confluence and JIRA
                metadata = chunk['metadata']
                source_id = metadata.get('page_id') or metadata.get('issue_id') or metadata.get('issue_key', f"doc_{i}")
                chunk_id = f"{source_id}_chunk_{metadata.get('chunk_index', i)}"
                ids.append(chunk_id)
                documents.append(chunk['content'])
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(self, query_embedding: List[float], top_k: int = None) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        top_k = top_k or config.TOP_K_RESULTS
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def delete_collection(self):
        """
        Delete the collection (useful for re-indexing)
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Error deleting collection: {e}")
    
    def get_collection_count(self) -> int:
        """
        Get the number of documents in the collection
        
        Returns:
            Number of documents
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0

