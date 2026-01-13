# Step-by-Step Setup and Explanation Guide

## Overview

This guide explains how the Confluence RAG QA Bot works and how to set it up step by step.

## Architecture Overview

The application follows a RAG (Retrieval-Augmented Generation) pattern:

```
User Query → Embed Query → Vector Search → Retrieve Context → LLM Generation → Answer
```

## Step-by-Step Explanation

### Step 1: Data Ingestion (`confluence_fetcher.py`)

**What it does:**
- Connects to Confluence using the Confluence REST API
- Fetches pages from a specified Confluence space
- Extracts clean text from HTML content

**Key Components:**
- Uses `atlassian-python-api` library for Confluence API interaction
- Uses BeautifulSoup to extract text from Confluence's HTML format
- Supports fetching all pages from a space or searching with CQL

**Why this step:**
Confluence stores content in HTML format. We need to extract plain text for processing.

---

### Step 2: Document Processing (`document_processor.py`)

**What it does:**
- Splits large documents into smaller chunks
- Preserves metadata (page ID, title, URL) with each chunk

**Key Components:**
- Uses LangChain's `RecursiveCharacterTextSplitter`
- Configurable chunk size (default: 1000 characters) and overlap (default: 200 characters)

**Why this step:**
- LLMs have token limits, so we can't send entire documents
- Smaller chunks improve retrieval accuracy
- Overlap ensures context isn't lost at chunk boundaries

**Example:**
A 5000-character page becomes ~5 chunks of 1000 characters each with 200-character overlaps.

---

### Step 3: Embedding Generation (Part of `rag_pipeline.py`)

**What it does:**
- Converts text chunks into vector embeddings (numerical representations)
- Uses Google's embedding model (`models/embedding-001`)

**Key Components:**
- `GoogleGenerativeAIEmbeddings` from LangChain
- Each chunk is converted to a 768-dimensional vector

**Why this step:**
- Enables semantic search (finding meaning, not just keywords)
- Vector similarity allows finding related content even with different wording

**Example:**
"The user clicked the button" and "The button was clicked by the user" will have similar embeddings.

---

### Step 4: Vector Storage (`vector_store.py`)

**What it does:**
- Stores embeddings in ChromaDB (a vector database)
- Enables fast similarity search

**Key Components:**
- ChromaDB with persistent storage (local file system)
- Uses cosine similarity for matching

**Why this step:**
- Vector databases are optimized for similarity search
- Allows retrieving relevant chunks in milliseconds
- Persists data so we don't need to re-index every time

---

### Step 5: Query Processing (`rag_pipeline.py`)

**What it does:**
- Takes user query
- Converts query to embedding
- Searches vector store for similar chunks
- Retrieves top-k most relevant chunks (default: 4)

**Key Components:**
- Same embedding model for consistency
- ChromaDB's query method with cosine similarity

**Why this step:**
- Finds the most relevant context for the user's question
- Retrieves only necessary information (not entire documents)

---

### Step 6: Answer Generation (`rag_pipeline.py`)

**What it does:**
- Takes retrieved context and user query
- Sends to LLM (Google Gemini) with a prompt
- LLM generates answer based on context

**Key Components:**
- `ChatGoogleGenerativeAI` from LangChain
- Prompt engineering to instruct LLM to use only provided context
- Includes source citation

**Why this step:**
- LLM synthesizes information from multiple chunks
- Provides natural language answers
- Can cite sources for transparency

---

### Step 7: User Interface (`app.py`)

**What it does:**
- Streamlit web interface
- Allows indexing Confluence spaces
- Chat interface for asking questions

**Key Features:**
- Sidebar for configuration and indexing
- Chat history
- Source citations
- Real-time feedback

---

## Setup Instructions

### Prerequisites

1. **Python 3.8+** installed
2. **Confluence Access**: 
   - URL of your Confluence instance
   - Username (email)
   - API token (see below)
3. **Google API Key**: For Gemini and embeddings (see below)

### Getting API Keys

#### Confluence API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "RAG Bot")
4. Copy the token (you'll only see it once!)
5. Use your email as username and the token as password

#### Google API Key (for Gemini)

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

**Note:** Gemini has a free tier with generous limits for testing/development.

### Installation Steps

1. **Clone/Navigate to project directory**
   ```bash
   cd rag_confluence
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Or create manually with:
   CONFLUENCE_URL=https://your-instance.atlassian.net/wiki
   CONFLUENCE_USERNAME=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token
   GOOGLE_API_KEY=your-google-api-key
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Open browser**
   - The app will automatically open at http://localhost:8501
   - Or open manually if needed

### First-Time Usage

1. **Index a Confluence Space:**
   - In the sidebar, enter a space key (e.g., "DEV", "DOCS")
   - Click "Index Pages"
   - Wait for indexing to complete

2. **Ask Questions:**
   - Type your question in the chat input
   - The bot will retrieve relevant context and generate an answer
   - Check sources for references

### Testing with Public/Open Source Confluence

For development purposes, you have several options:

1. **Use Your Own Confluence**: Most straightforward option
2. **Public Confluence Instances**: Some organizations have public spaces
3. **Atlassian Cloud Trial**: Create a free trial instance
4. **Mock Data**: Modify the fetcher to use sample data

**Example Public Confluence:**
- Atlassian's own documentation spaces (if accessible)
- Some open-source projects host documentation on Confluence

## LLM Selection

### Development/Testing: Gemini Pro

**Why Gemini?**
- Free tier with generous limits
- High-quality embeddings
- Good performance for RAG
- Same model you'll use in production (consistency)

**Alternative Options for Testing:**
- **Ollama** (local, free): Requires local setup, slower
- **OpenAI GPT** (paid): Good quality, but costs money
- **Hugging Face** (free): Requires more setup

Since you'll use Gemini in production, using it for testing ensures consistency.

### Production: Gemini Pro

As specified, Gemini will be used in production. The code is already configured for Gemini.

## Customization

### Adjusting Chunk Size

Edit `config.py`:
```python
CHUNK_SIZE = 1000  # Increase for longer context, decrease for more granular chunks
CHUNK_OVERLAP = 200  # Increase to preserve more context at boundaries
```

### Changing Retrieval Count

```python
TOP_K_RESULTS = 4  # Number of chunks to retrieve (increase for more context)
```

### Using Different LLM Models

The code uses Gemini, but you can modify `rag_pipeline.py` to use other LangChain-compatible LLMs.

## Troubleshooting

### "Connection Error" when indexing
- Verify Confluence URL, username, and API token
- Check if your Confluence instance is accessible
- Ensure API token hasn't expired

### "No pages found"
- Verify the space key is correct
- Check if you have access to that space
- Try with a different space

### "API Key Error"
- Verify Google API key is correct
- Check if API key has proper permissions
- Ensure billing is enabled (even for free tier)

### Slow indexing
- Reduce the page limit
- Index smaller spaces first
- Check network connection

## Production Considerations

1. **Scalability**: Consider managed vector databases (Pinecone, Weaviate)
2. **Security**: Use secrets management (AWS Secrets Manager, Azure Key Vault)
3. **Monitoring**: Add logging and monitoring
4. **Rate Limiting**: Implement rate limiting for API calls
5. **Caching**: Cache frequently asked questions
6. **Error Handling**: More robust error handling and retries
7. **Deployment**: Containerize with Docker, deploy to cloud

## Next Steps

- Index more Confluence spaces
- Fine-tune chunk sizes for your content
- Adjust prompts for better answers
- Add conversation history
- Implement feedback mechanism

