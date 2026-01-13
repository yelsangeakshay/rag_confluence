"""
Configuration settings for the RAG application
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Confluence Configuration
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")

# Google Gemini API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"  # Options: "gemini-1.5-flash" (faster), "gemini-1.5-pro" (more capable)

# Vector Store Configuration
VECTOR_STORE_PATH = "./chroma_db"
COLLECTION_NAME = "confluence_docs"

# RAG Configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
TOP_K_RESULTS = 4  # Number of relevant chunks to retrieve

# Streamlit Configuration
APP_TITLE = "Confluence RAG QA Bot"
PAGE_ICON = "🤖"

