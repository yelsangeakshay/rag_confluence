"""
Module for fetching content from JIRA using the JIRA API
"""
from atlassian import Jira
from typing import List, Dict
import config
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JiraFetcher:
    """
    Fetches issues and content from JIRA
    """
    
    def __init__(self, url: str = None, username: str = None, api_token: str = None):
        """
        Initialize JIRA client
        
        Args:
            url: JIRA base URL
            username: JIRA username/email
            api_token: JIRA API token
        """
        self.url = url or config.JIRA_URL
        self.username = username or config.JIRA_USERNAME
        self.api_token = api_token or config.JIRA_API_TOKEN
        
        if not all([self.url, self.username, self.api_token]):
            raise ValueError("JIRA URL, username, and API token are required")
        
        try:
            self.jira = Jira(
                url=self.url,
                username=self.username,
                password=self.api_token,
                cloud=True  # Set to False if using server/DC
            )
            logger.info(f"Connected to JIRA at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to JIRA: {e}")
            raise
    
    def get_issues_from_project(self, project_key: str, limit: int = 100, jql: str = None) -> List[Dict]:
        """
        Fetch issues from a specific JIRA project
        
        Args:
            project_key: The key of the JIRA project (e.g., 'PROJ')
            limit: Maximum number of issues to fetch
            jql: Optional JQL query to filter issues
            
        Returns:
            List of issue dictionaries with id, key, summary, description, etc.
        """
        try:
            # Build JQL query
            if jql:
                query = jql
            else:
                query = f"project = {project_key} ORDER BY updated DESC"
            
            # Fetch issues
            issues = []
            start_at = 0
            max_results = min(limit, 100)  # JIRA API limit per request
            
            while len(issues) < limit:
                response = self.jira.jql(
                    query,
                    start=start_at,
                    limit=max_results,
                    fields=['summary', 'description', 'status', 'assignee', 'reporter', 'created', 'updated', 'priority', 'issueType', 'comments']
                )
                
                fetched_issues = response.get('issues', [])
                if not fetched_issues:
                    break
                
                issues.extend(fetched_issues)
                
                if len(fetched_issues) < max_results or len(issues) >= limit:
                    break
                
                start_at += max_results
            
            # Limit to requested number
            issues = issues[:limit]
            
            logger.info(f"Found {len(issues)} issues from project {project_key}")
            return issues
        except Exception as e:
            logger.error(f"Error fetching issues from project {project_key}: {e}")
            return []
    
    def get_issue_content(self, issue_key: str) -> Dict:
        """
        Get full content of a specific issue
        
        Args:
            issue_key: The key of the issue (e.g., 'PROJ-123')
            
        Returns:
            Dictionary with issue metadata and content
        """
        try:
            issue = self.jira.issue(issue_key, expand='renderedFields')
            return issue
        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {e}")
            return {}
    
    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract clean text from JIRA HTML content (description, comments, etc.)
        
        Args:
            html_content: HTML content from JIRA
            
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
    
    def format_issue_content(self, issue: Dict) -> str:
        """
        Format issue content into a readable text string
        
        Args:
            issue: Issue dictionary from JIRA API
            
        Returns:
            Formatted text content
        """
        content_parts = []
        
        # Summary
        summary = issue.get('fields', {}).get('summary', '')
        if summary:
            content_parts.append(f"Summary: {summary}")
        
        # Description
        description = issue.get('fields', {}).get('description', '')
        if description:
            if isinstance(description, dict):
                # ADF (Atlassian Document Format) or HTML
                if 'content' in description:
                    # ADF format - extract text from content array
                    desc_text = self._extract_text_from_adf(description)
                else:
                    desc_text = self.extract_text_from_html(str(description))
            else:
                desc_text = self.extract_text_from_html(str(description))
            
            if desc_text:
                content_parts.append(f"\nDescription:\n{desc_text}")
        
        # Status, Priority, Type
        status = issue.get('fields', {}).get('status', {}).get('name', '')
        priority = issue.get('fields', {}).get('priority', {}).get('name', '')
        issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', '')
        
        if status or priority or issue_type:
            content_parts.append(f"\nIssue Details:")
            if issue_type:
                content_parts.append(f"Type: {issue_type}")
            if status:
                content_parts.append(f"Status: {status}")
            if priority:
                content_parts.append(f"Priority: {priority}")
        
        # Comments
        comments = issue.get('fields', {}).get('comment', {}).get('comments', [])
        if comments:
            content_parts.append(f"\nComments ({len(comments)}):")
            for comment in comments:
                comment_body = comment.get('body', '')
                if comment_body:
                    if isinstance(comment_body, dict):
                        comment_text = self._extract_text_from_adf(comment_body)
                    else:
                        comment_text = self.extract_text_from_html(str(comment_body))
                    
                    if comment_text:
                        author = comment.get('author', {}).get('displayName', 'Unknown')
                        created = comment.get('created', '')
                        content_parts.append(f"\n- {author} ({created}): {comment_text}")
        
        return "\n".join(content_parts)
    
    def _extract_text_from_adf(self, adf_content: Dict) -> str:
        """
        Extract text from Atlassian Document Format (ADF)
        
        Args:
            adf_content: ADF content dictionary
            
        Returns:
            Plain text content
        """
        text_parts = []
        
        def extract_from_node(node):
            if isinstance(node, dict):
                node_type = node.get('type', '')
                
                if node_type == 'text':
                    return node.get('text', '')
                elif 'content' in node:
                    # Recursively extract from content
                    content_text = []
                    for child in node.get('content', []):
                        child_text = extract_from_node(child)
                        if child_text:
                            content_text.append(child_text)
                    return ' '.join(content_text)
            
            return ''
        
        if isinstance(adf_content, dict) and 'content' in adf_content:
            for node in adf_content.get('content', []):
                text = extract_from_node(node)
                if text:
                    text_parts.append(text)
        else:
            text = extract_from_node(adf_content)
            if text:
                text_parts.append(text)
        
        return ' '.join(text_parts)
    
    def fetch_issues_content(self, project_key: str = None, jql: str = None, limit: int = 100) -> List[Dict]:
        """
        Fetch and process issues with clean text content
        
        Args:
            project_key: The key of the JIRA project (required if jql not provided)
            jql: JQL query string (e.g., "project = PROJ AND status = Open")
            limit: Maximum number of issues to fetch
            
        Returns:
            List of dictionaries with issue metadata and cleaned text content
        """
        if not jql and not project_key:
            raise ValueError("Either project_key or jql must be provided")
        
        issues = self.get_issues_from_project(project_key or '', limit=limit, jql=jql)
        
        processed_issues = []
        for issue in issues:
            try:
                # Format issue content
                text_content = self.format_issue_content(issue)
                
                if text_content:  # Only include issues with content
                    fields = issue.get('fields', {})
                    processed_issues.append({
                        'id': issue.get('id'),
                        'key': issue.get('key'),
                        'title': f"{issue.get('key')}: {fields.get('summary', 'No Summary')}",
                        'content': text_content,
                        'url': f"{self.url}/browse/{issue.get('key')}",
                        'project': project_key or fields.get('project', {}).get('key', 'unknown'),
                        'status': fields.get('status', {}).get('name', ''),
                        'issue_type': fields.get('issuetype', {}).get('name', ''),
                        'priority': fields.get('priority', {}).get('name', ''),
                        'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                        'reporter': fields.get('reporter', {}).get('displayName', 'Unknown') if fields.get('reporter') else 'Unknown',
                        'created': fields.get('created', ''),
                        'updated': fields.get('updated', '')
                    })
            except Exception as e:
                logger.warning(f"Error processing issue {issue.get('key')}: {e}")
                continue
        
        logger.info(f"Processed {len(processed_issues)} issues with content")
        return processed_issues
    
    def search_issues(self, jql: str, limit: int = 100) -> List[Dict]:
        """
        Search issues using JQL (JIRA Query Language)
        
        Args:
            jql: JQL query string (e.g., "project = PROJ AND status = Open")
            limit: Maximum number of results
            
        Returns:
            List of issue dictionaries
        """
        try:
            return self.fetch_issues_content(jql=jql, limit=limit)
        except Exception as e:
            logger.error(f"Error searching issues: {e}")
            return []

