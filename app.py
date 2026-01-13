"""
Streamlit application for Confluence RAG QA Bot
"""
import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from confluence_fetcher import ConfluenceFetcher
from document_processor import DocumentProcessor
from vector_store import VectorStore
from rag_pipeline import RAGPipeline
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide"
)

# Initialize session state
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'rag_pipeline' not in st.session_state:
    st.session_state.rag_pipeline = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'documents_indexed' not in st.session_state:
    st.session_state.documents_indexed = False


def initialize_system():
    """Initialize vector store and RAG pipeline"""
    try:
        if st.session_state.vector_store is None:
            st.session_state.vector_store = VectorStore()
        
        if st.session_state.rag_pipeline is None:
            if not config.GOOGLE_API_KEY:
                st.error("Please set GOOGLE_API_KEY in your .env file")
                return False
            st.session_state.rag_pipeline = RAGPipeline(st.session_state.vector_store)
        
        return True
    except Exception as e:
        st.error(f"Error initializing system: {e}")
        return False


def index_confluence_pages(space_key: str, limit: int = 100):
    """Index pages from Confluence"""
    try:
        with st.spinner(f"Fetching pages from Confluence space '{space_key}'..."):
            # Fetch pages
            fetcher = ConfluenceFetcher()
            pages = fetcher.fetch_pages_content(space_key, limit=limit)
            
            if not pages:
                st.warning(f"No pages found in space '{space_key}'")
                return False
            
            st.info(f"Found {len(pages)} pages. Processing and indexing...")
            
            # Process documents
            processor = DocumentProcessor()
            chunks = processor.process_pages(pages)
            
            if not chunks:
                st.warning("No chunks created from pages")
                return False
            
            # Generate embeddings
            with st.spinner("Generating embeddings..."):
                embeddings = st.session_state.rag_pipeline.embeddings.embed_documents(
                    [chunk['content'] for chunk in chunks]
                )
            
            # Add to vector store
            with st.spinner("Adding to vector store..."):
                st.session_state.vector_store.add_documents(chunks, embeddings)
            
            st.session_state.documents_indexed = True
            st.success(f"Successfully indexed {len(chunks)} chunks from {len(pages)} pages!")
            return True
            
    except Exception as e:
        st.error(f"Error indexing pages: {e}")
        logger.error(f"Indexing error: {e}", exc_info=True)
        return False


def main():
    st.title("🤖 Confluence RAG QA Bot")
    st.markdown("Ask questions about your Confluence documentation!")
    
    # Initialize system
    if not initialize_system():
        st.stop()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check if documents are indexed
        doc_count = st.session_state.vector_store.get_collection_count()
        st.metric("Indexed Documents", doc_count)
        
        st.divider()
        
        st.header("📥 Index Confluence Pages")
        st.markdown("Enter a Confluence space key to index pages")
        
        space_key = st.text_input(
            "Space Key",
            placeholder="e.g., DEV, DOCS, or your-space-key",
            help="The key of the Confluence space to index"
        )
        
        limit = st.number_input(
            "Max Pages",
            min_value=1,
            max_value=500,
            value=50,
            help="Maximum number of pages to fetch"
        )
        
        if st.button("🚀 Index Pages", type="primary"):
            if not space_key:
                st.warning("Please enter a space key")
            elif not config.CONFLUENCE_URL or not config.CONFLUENCE_USERNAME or not config.CONFLUENCE_API_TOKEN:
                st.error("Please configure Confluence credentials in .env file")
            else:
                index_confluence_pages(space_key, limit)
        
        if st.button("🗑️ Clear Index", help="Delete all indexed documents"):
            try:
                st.session_state.vector_store.delete_collection()
                st.session_state.vector_store = VectorStore()
                st.session_state.documents_indexed = False
                st.session_state.messages = []
                st.success("Index cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing index: {e}")
        
        st.divider()
        st.markdown("### ℹ️ Instructions")
        st.markdown("""
        1. Configure your `.env` file with:
           - CONFLUENCE_URL
           - CONFLUENCE_USERNAME
           - CONFLUENCE_API_TOKEN
           - GOOGLE_API_KEY
        
        2. Enter a space key and click "Index Pages"
        
        3. Ask questions about the indexed content!
        """)
    
    # Main chat interface
    if doc_count == 0:
        st.info("👈 Please index some Confluence pages from the sidebar to get started!")
    else:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show sources if available
                if message["role"] == "assistant" and "sources" in message and message["sources"]:
                    with st.expander("📚 Sources"):
                        for source in message["sources"]:
                            st.markdown(f"- **{source['title']}**")
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your Confluence docs..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        result = st.session_state.rag_pipeline.query(prompt)
                        
                        answer = result['answer']
                        sources = result.get('sources', [])
                        
                        st.markdown(answer)
                        
                        # Display sources
                        if sources:
                            with st.expander("📚 Sources"):
                                for source in sources:
                                    st.markdown(f"- **{source['title']}**")
                        
                        # Add to chat history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })
                        
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })


if __name__ == "__main__":
    main()

