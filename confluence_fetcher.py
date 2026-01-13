"""
Module for fetching content from Confluence using the Confluence API
"""
from atlassian import Confluence
from typing import List, Dict
import config
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """
    Fetches pages and content from Confluence
    """
    
    def __init__(self, url: str = None, username: str = None, api_token: str = None):
        """
        Initialize Confluence client
        
        Args:
            url: Confluence base URL
            username: Confluence username/email
            api_token: Confluence API token
        """
        self.url = url or config.CONFLUENCE_URL
        self.username = username or config.CONFLUENCE_USERNAME
        self.api_token = api_token or config.CONFLUENCE_API_TOKEN
        
        if not all([self.url, self.username, self.api_token]):
            raise ValueError("Confluence URL, username, and API token are required")
        
        try:
            self.confluence = Confluence(
                url=self.url,
                username=self.username,
                password=self.api_token,
                cloud=True  # Set to False if using server/DC
            )
            logger.info(f"Connected to Confluence at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Confluence: {e}")
            raise
    
    def get_all_pages_from_space(self, space_key: str, limit: int = 100) -> List[Dict]:
        """
        Fetch all pages from a specific Confluence space
        
        Args:
            space_key: The key of the Confluence space
            limit: Maximum number of pages to fetch
            
        Returns:
            List of page dictionaries with id, title, and content
        """
        try:
            pages = self.confluence.get_all_pages_from_space(
                space=space_key,
                limit=limit,
                content_type='page',
                expand='body.storage,version'
            )
            
            logger.info(f"Found {len(pages)} pages in space {space_key}")
            return pages
        except Exception as e:
            logger.error(f"Error fetching pages from space {space_key}: {e}")
            return []
    
    def get_page_content(self, page_id: str) -> Dict:
        """
        Get full content of a specific page
        
        Args:
            page_id: The ID of the page
            
        Returns:
            Dictionary with page metadata and content
        """
        try:
            page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand='body.storage,version,ancestors'
            )
            return page
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {e}")
            return {}
    
    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract clean text from Confluence HTML content
        
        Args:
            html_content: HTML content from Confluence
            
        Returns:
            Clean text content
        """
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def fetch_pages_content(self, space_key: str, limit: int = 100) -> List[Dict]:
        """
        Fetch and process all pages from a space with clean text content
        
        Args:
            space_key: The key of the Confluence space
            limit: Maximum number of pages to fetch
            
        Returns:
            List of dictionaries with page metadata and cleaned text content
        """
        pages = self.get_all_pages_from_space(space_key, limit)
        
        processed_pages = []
        for page in pages:
            try:
                # Extract text from HTML
                html_content = page.get('body', {}).get('storage', {}).get('value', '')
                text_content = self.extract_text_from_html(html_content)
                
                if text_content:  # Only include pages with content
                    processed_pages.append({
                        'id': page.get('id'),
                        'title': page.get('title'),
                        'content': text_content,
                        'url': f"{self.url}/pages/viewpage.action?pageId={page.get('id')}",
                        'space': space_key
                    })
            except Exception as e:
                logger.warning(f"Error processing page {page.get('id')}: {e}")
                continue
        
        logger.info(f"Processed {len(processed_pages)} pages with content")
        return processed_pages
    
    def search_pages(self, cql: str, limit: int = 100) -> List[Dict]:
        """
        Search pages using Confluence Query Language (CQL)
        
        Args:
            cql: CQL query string (e.g., "space=DEV and type=page")
            limit: Maximum number of results
            
        Returns:
            List of page dictionaries
        """
        try:
            results = self.confluence.cql(cql, limit=limit)
            pages = results.get('results', [])
            
            processed_pages = []
            for page in pages:
                page_id = page.get('content', {}).get('id')
                if page_id:
                    full_page = self.get_page_content(page_id)
                    html_content = full_page.get('body', {}).get('storage', {}).get('value', '')
                    text_content = self.extract_text_from_html(html_content)
                    
                    if text_content:
                        processed_pages.append({
                            'id': page_id,
                            'title': full_page.get('title'),
                            'content': text_content,
                            'url': f"{self.url}/pages/viewpage.action?pageId={page_id}",
                        })
            
            return processed_pages
        except Exception as e:
            logger.error(f"Error searching pages: {e}")
            return []

