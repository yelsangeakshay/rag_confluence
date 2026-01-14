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
from jira_fetcher import JiraFetcher
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
if 'jira_vector_store' not in st.session_state:
    st.session_state.jira_vector_store = None
if 'rag_pipeline' not in st.session_state:
    st.session_state.rag_pipeline = None
if 'jira_rag_pipeline' not in st.session_state:
    st.session_state.jira_rag_pipeline = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'jira_messages' not in st.session_state:
    st.session_state.jira_messages = []
if 'documents_indexed' not in st.session_state:
    st.session_state.documents_indexed = False
if 'jira_documents_indexed' not in st.session_state:
    st.session_state.jira_documents_indexed = False
if 'current_source' not in st.session_state:
    st.session_state.current_source = 'confluence'


def initialize_system(source_type: str = 'confluence'):
    """Initialize vector store and RAG pipeline"""
    try:
        if source_type == 'jira':
            if st.session_state.jira_vector_store is None:
                st.session_state.jira_vector_store = VectorStore(collection_name=config.JIRA_COLLECTION_NAME)
            
            if st.session_state.jira_rag_pipeline is None:
                if not config.GOOGLE_API_KEY:
                    st.error("Please set GOOGLE_API_KEY in your .env file")
                    return False
                st.session_state.jira_rag_pipeline = RAGPipeline(
                    st.session_state.jira_vector_store,
                    source_type="jira"
                )
        else:  # confluence
            if st.session_state.vector_store is None:
                st.session_state.vector_store = VectorStore()
            
            if st.session_state.rag_pipeline is None:
                if not config.GOOGLE_API_KEY:
                    st.error("Please set GOOGLE_API_KEY in your .env file")
                    return False
                st.session_state.rag_pipeline = RAGPipeline(
                    st.session_state.vector_store,
                    source_type="confluence"
                )
        
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
            chunks = processor.process_pages(pages, source_type='confluence')
            
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


def index_jira_issues(project_key: str = None, jql: str = None, limit: int = 100):
    """Index issues from JIRA"""
    try:
        with st.spinner(f"Fetching issues from JIRA..."):
            # Fetch issues
            fetcher = JiraFetcher()
            issues = fetcher.fetch_issues_content(project_key=project_key, jql=jql, limit=limit)
            
            if not issues:
                st.warning(f"No issues found")
                return False
            
            st.info(f"Found {len(issues)} issues. Processing and indexing...")
            
            # Process documents
            processor = DocumentProcessor()
            chunks = processor.process_pages(issues, source_type='jira')
            
            if not chunks:
                st.warning("No chunks created from issues")
                return False
            
            # Generate embeddings
            with st.spinner("Generating embeddings..."):
                embeddings = st.session_state.jira_rag_pipeline.embeddings.embed_documents(
                    [chunk['content'] for chunk in chunks]
                )
            
            # Add to vector store
            with st.spinner("Adding to vector store..."):
                st.session_state.jira_vector_store.add_documents(chunks, embeddings)
            
            st.session_state.jira_documents_indexed = True
            st.success(f"Successfully indexed {len(chunks)} chunks from {len(issues)} issues!")
            return True
            
    except Exception as e:
        st.error(f"Error indexing issues: {e}")
        logger.error(f"Indexing error: {e}", exc_info=True)
        return False


def main():
    st.title("🤖 Confluence & JIRA RAG QA Bot")
    st.markdown("Ask questions about your Confluence documentation and JIRA issues!")
    
    # Source selection tabs
    source_tab = st.tabs(["📚 Confluence", "🎫 JIRA"])
    
    # Initialize both systems
    if not initialize_system('confluence'):
        st.stop()
    if not initialize_system('jira'):
        st.stop()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Source selector
        selected_source = st.radio(
            "Select Source",
            ["Confluence", "JIRA"],
            index=0 if st.session_state.current_source == 'confluence' else 1,
            help="Choose which source to query"
        )
        st.session_state.current_source = 'confluence' if selected_source == 'Confluence' else 'jira'
        
        st.divider()
        
        # Confluence section
        if st.session_state.current_source == 'confluence':
            doc_count = st.session_state.vector_store.get_collection_count()
            st.metric("Indexed Documents", doc_count)
            
            st.divider()
            
            st.header("📥 Index Confluence Pages")
            st.markdown("Enter a Confluence space key to index pages")
            
            space_key = st.text_input(
                "Space Key",
                placeholder="e.g., DEV, DOCS, or your-space-key",
                help="The key of the Confluence space to index",
                key="confluence_space_key"
            )
            
            limit = st.number_input(
                "Max Pages",
                min_value=1,
                max_value=500,
                value=50,
                help="Maximum number of pages to fetch",
                key="confluence_limit"
            )
            
            if st.button("🚀 Index Pages", type="primary", key="index_confluence"):
                if not space_key:
                    st.warning("Please enter a space key")
                elif not config.CONFLUENCE_URL or not config.CONFLUENCE_USERNAME or not config.CONFLUENCE_API_TOKEN:
                    st.error("Please configure Confluence credentials in .env file")
                else:
                    index_confluence_pages(space_key, limit)
            
            if st.button("🗑️ Clear Index", help="Delete all indexed Confluence documents", key="clear_confluence"):
                try:
                    st.session_state.vector_store.delete_collection()
                    st.session_state.vector_store = VectorStore()
                    st.session_state.documents_indexed = False
                    st.session_state.messages = []
                    st.success("Confluence index cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing index: {e}")
        
        # JIRA section
        else:
            jira_doc_count = st.session_state.jira_vector_store.get_collection_count()
            st.metric("Indexed Issues", jira_doc_count)
            
            st.divider()
            
            st.header("📥 Index JIRA Issues")
            st.markdown("Enter a project key or JQL query to index issues")
            
            index_method = st.radio(
                "Index Method",
                ["Project Key", "JQL Query"],
                key="jira_index_method"
            )
            
            if index_method == "Project Key":
                project_key = st.text_input(
                    "Project Key",
                    placeholder="e.g., PROJ, DEV, or your-project-key",
                    help="The key of the JIRA project to index",
                    key="jira_project_key"
                )
                jql = None
            else:
                jql = st.text_area(
                    "JQL Query",
                    placeholder='e.g., project = PROJ AND status = Open',
                    help="JIRA Query Language query to filter issues",
                    key="jira_jql"
                )
                project_key = None
            
            limit = st.number_input(
                "Max Issues",
                min_value=1,
                max_value=500,
                value=50,
                help="Maximum number of issues to fetch",
                key="jira_limit"
            )
            
            if st.button("🚀 Index Issues", type="primary", key="index_jira"):
                if index_method == "Project Key" and not project_key:
                    st.warning("Please enter a project key")
                elif index_method == "JQL Query" and not jql:
                    st.warning("Please enter a JQL query")
                elif not config.JIRA_URL or not config.JIRA_USERNAME or not config.JIRA_API_TOKEN:
                    st.error("Please configure JIRA credentials in .env file")
                else:
                    index_jira_issues(project_key=project_key, jql=jql, limit=limit)
            
            if st.button("🗑️ Clear Index", help="Delete all indexed JIRA issues", key="clear_jira"):
                try:
                    st.session_state.jira_vector_store.delete_collection()
                    st.session_state.jira_vector_store = VectorStore(collection_name=config.JIRA_COLLECTION_NAME)
                    st.session_state.jira_documents_indexed = False
                    st.session_state.jira_messages = []
                    st.success("JIRA index cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing index: {e}")
        
        st.divider()
        st.markdown("### ℹ️ Instructions")
        if st.session_state.current_source == 'confluence':
            st.markdown("""
            1. Configure your `.env` file with:
               - CONFLUENCE_URL
               - CONFLUENCE_USERNAME
               - CONFLUENCE_API_TOKEN
               - GOOGLE_API_KEY
            
            2. Enter a space key and click "Index Pages"
            
            3. Ask questions about the indexed content!
            """)
        else:
            st.markdown("""
            1. Configure your `.env` file with:
               - JIRA_URL
               - JIRA_USERNAME
               - JIRA_API_TOKEN
               - GOOGLE_API_KEY
            
            2. Enter a project key or JQL query and click "Index Issues"
            
            3. Ask questions about the indexed issues!
            """)
    
    # Main chat interface
    if st.session_state.current_source == 'confluence':
        doc_count = st.session_state.vector_store.get_collection_count()
        messages = st.session_state.messages
        rag_pipeline = st.session_state.rag_pipeline
        placeholder_text = "Ask a question about your Confluence docs..."
        
        if doc_count == 0:
            st.info("👈 Please index some Confluence pages from the sidebar to get started!")
        else:
            # Display chat history
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # Show sources if available
                    if message["role"] == "assistant" and "sources" in message and message["sources"]:
                        with st.expander("📚 Sources"):
                            for source in message["sources"]:
                                st.markdown(f"- **{source['title']}**")
            
            # Chat input
            if prompt := st.chat_input(placeholder_text):
                # Add user message
                messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            result = rag_pipeline.query(prompt)
                            
                            answer = result['answer']
                            sources = result.get('sources', [])
                            
                            st.markdown(answer)
                            
                            # Display sources
                            if sources:
                                with st.expander("📚 Sources"):
                                    for source in sources:
                                        st.markdown(f"- **{source['title']}**")
                            
                            # Add to chat history
                            messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": sources
                            })
                            
                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.error(error_msg)
                            messages.append({
                                "role": "assistant",
                                "content": error_msg
                            })
    else:  # JIRA
        jira_doc_count = st.session_state.jira_vector_store.get_collection_count()
        messages = st.session_state.jira_messages
        rag_pipeline = st.session_state.jira_rag_pipeline
        placeholder_text = "Ask a question about your JIRA issues..."
        
        if jira_doc_count == 0:
            st.info("👈 Please index some JIRA issues from the sidebar to get started!")
        else:
            # Display chat history
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # Show sources if available
                    if message["role"] == "assistant" and "sources" in message and message["sources"]:
                        with st.expander("📚 Sources"):
                            for source in message["sources"]:
                                st.markdown(f"- **{source['title']}**")
            
            # Chat input
            if prompt := st.chat_input(placeholder_text):
                # Add user message
                messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            result = rag_pipeline.query(prompt)
                            
                            answer = result['answer']
                            sources = result.get('sources', [])
                            
                            st.markdown(answer)
                            
                            # Display sources
                            if sources:
                                with st.expander("📚 Sources"):
                                    for source in sources:
                                        st.markdown(f"- **{source['title']}**")
                            
                            # Add to chat history
                            messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": sources
                            })
                            
                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.error(error_msg)
                            messages.append({
                                "role": "assistant",
                                "content": error_msg
                            })


if __name__ == "__main__":
    main()

