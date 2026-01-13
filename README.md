# Confluence RAG QA Bot

A Retrieval-Augmented Generation (RAG) application that answers user queries using content from Confluence pages. Built with Streamlit, LangChain, and ChromaDB.

## Features

- **Confluence Integration**: Fetches and indexes content from Confluence pages
- **RAG Pipeline**: Uses vector embeddings and semantic search for relevant document retrieval
- **Streamlit UI**: Interactive web interface for querying the knowledge base
- **LLM Integration**: Uses Google Gemini for generating answers (configurable for other LLMs)

## Project Structure

```
rag_confluence/
├── app.py                 # Streamlit application
├── config.py              # Configuration settings
├── confluence_fetcher.py  # Confluence API integration
├── document_processor.py  # Document chunking and processing
├── vector_store.py        # Vector database operations
├── rag_pipeline.py        # RAG pipeline with LLM
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
CONFLUENCE_URL=https://your-confluence-instance.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
GOOGLE_API_KEY=your-google-api-key
```

**Getting Confluence API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Use your email as username and the token as password

**Getting Google API Key (for Gemini):**
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key

### 3. Run the Application

```bash
streamlit run app.py
```

## Development Testing

For development purposes, you can use:
- **Public Confluence instances** (if available)
- **Your own Confluence space** for testing
- **Sample data**: The code can work with any Confluence URL you have access to

## Production Deployment

For production, ensure:
- Secure storage of API keys (use environment variables or secrets management)
- Proper error handling and logging
- Rate limiting for API calls
- Scalable vector database (consider Pinecone, Weaviate, or managed ChromaDB)

## How It Works

1. **Data Ingestion**: Fetches pages from Confluence using the Confluence API
2. **Document Processing**: Chunks documents into smaller pieces for better retrieval
3. **Embedding Generation**: Creates vector embeddings for each chunk
4. **Vector Storage**: Stores embeddings in ChromaDB for fast similarity search
5. **Query Processing**: 
   - Converts user query to embedding
   - Retrieves relevant document chunks
   - Passes context to LLM for answer generation
6. **Response Generation**: LLM generates answer based on retrieved context

## Configuration

Edit `config.py` to customize:
- Chunk size and overlap
- Number of documents to retrieve
- LLM model parameters
- Embedding model settings

