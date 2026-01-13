# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file:

```env
CONFLUENCE_URL=https://your-instance.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
GOOGLE_API_KEY=your-google-api-key
```

**Get API Keys:**
- **Confluence API Token**: https://id.atlassian.com/manage-profile/security/api-tokens
- **Google API Key**: https://makersuite.google.com/app/apikey

### 3. Run the Application

```bash
streamlit run app.py
```

### 4. Index Your Confluence Space

1. Open the app (usually at http://localhost:8501)
2. In the sidebar, enter a Confluence space key
3. Click "Index Pages"
4. Wait for indexing to complete

### 5. Ask Questions!

Type your question in the chat interface and get answers from your Confluence documentation.

## 📝 For Development/Testing

### Option 1: Use Your Own Confluence (Recommended)
- Create a free Atlassian Cloud account if you don't have one
- Use your own Confluence space for testing

### Option 2: Use a Trial Instance
- Sign up for Atlassian Cloud trial (free for 7 days)
- Create a test space with sample documentation

### Option 3: Mock Data (Advanced)
- Modify `confluence_fetcher.py` to return sample data
- Useful for testing the RAG pipeline without Confluence access

## 🧪 Testing the Setup

1. **Verify API Keys**: The app will show errors if keys are invalid
2. **Test Indexing**: Try indexing a small space first (5-10 pages)
3. **Test Queries**: Ask simple questions to verify retrieval works

## ❓ Common Issues

**"No pages found"**
- Check space key spelling
- Verify you have access to that space

**"API Key Error"**
- Verify keys in `.env` file
- Check for extra spaces or quotes

**"Connection Error"**
- Verify Confluence URL format (should end with `/wiki`)
- Check if instance is accessible from your network

## 📚 Next Steps

- Read `SETUP_GUIDE.md` for detailed explanations
- Customize `config.py` for your needs
- Explore the code to understand the architecture

