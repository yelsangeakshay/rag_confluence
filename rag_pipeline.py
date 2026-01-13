"""
RAG Pipeline: Retrieval-Augmented Generation with LLM
"""
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG Pipeline that combines retrieval and generation
    """
    
    def __init__(self, vector_store, api_key: str = None, model_name: str = None):
        """
        Initialize RAG Pipeline
        
        Args:
            vector_store: VectorStore instance
            api_key: Google API key for Gemini
            model_name: Model name (default: gemini-pro)
        """
        self.vector_store = vector_store
        self.api_key = api_key or config.GOOGLE_API_KEY
        self.model_name = model_name or config.GEMINI_MODEL
        
        if not self.api_key:
            raise ValueError("Google API key is required for RAG pipeline")
        
        # Initialize embeddings model
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.api_key
            )
            logger.info("Initialized embeddings model")
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            raise
        
        # Initialize LLM
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.3,
                convert_system_message_to_human=True
            )
            logger.info(f"Initialized LLM: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise
        
        # Create prompt template
        self.prompt_template = """You are a helpful assistant that answers questions based on the provided context from Confluence documentation.

Instructions:
- Answer the question using ONLY the information provided in the context
- If the context doesn't contain enough information, say so clearly
- Cite the source pages when relevant
- Be concise and accurate
- If you don't know the answer, admit it rather than making something up

Context from Confluence:
{context}

Question: {question}

Provide a helpful answer based on the context above:"""
    
    def get_context(self, query: str, top_k: int = None) -> str:
        """
        Retrieve relevant context for a query
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Formatted context string
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search vector store
            results = self.vector_store.search(query_embedding, top_k=top_k or config.TOP_K_RESULTS)
            
            # Format context
            context_parts = []
            for i, result in enumerate(results, 1):
                page_title = result['metadata'].get('page_title', 'Unknown')
                content = result['content']
                context_parts.append(f"[Source {i}: {page_title}]\n{content}\n")
            
            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    def generate_answer(self, query: str, context: str, chat_history: List = None) -> str:
        """
        Generate answer using LLM
        
        Args:
            query: User query
            context: Retrieved context
            chat_history: Previous conversation history (currently unused, reserved for future)
            
        Returns:
            Generated answer
        """
        try:
            # Format prompt
            prompt = self.prompt_template.format(context=context, question=query)
            
            # Generate response
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}"
    
    def query(self, question: str, top_k: int = None, chat_history: List = None) -> Dict:
        """
        Complete RAG query: retrieve context and generate answer
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            chat_history: Previous conversation history
            
        Returns:
            Dictionary with answer and sources
        """
        try:
            # Retrieve relevant context
            context = self.get_context(question, top_k)
            
            if not context:
                return {
                    'answer': "I couldn't find any relevant information in the knowledge base to answer your question.",
                    'sources': []
                }
            
            # Generate answer
            answer = self.generate_answer(question, context, chat_history)
            
            # Extract sources from context
            sources = self._extract_sources_from_context(context)
            
            return {
                'answer': answer,
                'sources': sources,
                'context_used': context
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                'answer': f"An error occurred: {str(e)}",
                'sources': []
            }
    
    def _extract_sources_from_context(self, context: str) -> List[Dict]:
        """
        Extract source information from context
        
        Args:
            context: Context string with source markers
            
        Returns:
            List of source dictionaries
        """
        sources = []
        lines = context.split('\n')
        
        current_source = None
        for line in lines:
            if line.startswith('[Source'):
                # Extract source info
                parts = line.strip('[]').split(': ')
                if len(parts) >= 2:
                    source_num = parts[0].replace('Source ', '')
                    source_title = parts[1]
                    current_source = {'title': source_title, 'number': source_num}
                    sources.append(current_source)
        
        # Remove duplicates based on title
        seen = set()
        unique_sources = []
        for source in sources:
            if source['title'] not in seen:
                seen.add(source['title'])
                unique_sources.append(source)
        
        return unique_sources
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query
        
        Args:
            query: Text query
            
        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(query)

