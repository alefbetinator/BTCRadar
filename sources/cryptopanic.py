import logging
import os
from datetime import datetime
from typing import List, Dict, Any

import requests
from dateutil import parser

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)

class CryptoPanicSource(NewsSource):
    """Handler for CryptoPanic news aggregator API."""
    
    # CryptoPanic API endpoint
    API_URL = "https://cryptopanic.com/api/v1/posts/"
    
    @property
    def name(self) -> str:
        return "CryptoPanic"
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch recent Bitcoin articles from CryptoPanic API.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        articles = []
        
        try:
            # Get API key from environment variable
            api_key = os.environ.get('CRYPTOPANIC_API_KEY')
            
            if not api_key:
                logger.warning("CRYPTOPANIC_API_KEY not found in environment variables")
                return articles
            
            # Set up query parameters
            params = {
                'auth_token': api_key,
                'currencies': 'BTC',  # Filter for Bitcoin news
                'public': 'true',     # Only public news
                'kind': 'news',       # Filter for news (not signals)
                'limit': limit        # Number of results to return
            }
            
            # Make API request
            response = requests.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Process each news item
            for item in data.get('results', []):
                try:
                    # Extract the news item details
                    title = item.get('title', '')
                    url = item.get('url', '')
                    
                    # Parse the published date
                    date_str = item.get('published_at', '')
                    published_date = parser.parse(date_str) if date_str else datetime.now()
                    
                    # Extract the source information
                    source_info = item.get('source', {})
                    original_source = source_info.get('title', 'Unknown Source')
                    
                    # Get article content
                    content = self.extract_article_content(url)
                    
                    # Extract any additional metadata
                    metadata = item.get('metadata', {})
                    description = metadata.get('description', '')
                    
                    # If we couldn't get content, use the description as minimal content
                    if not content and description:
                        content = description
                    
                    # Create Article object with CryptoPanic as the aggregator source
                    article = Article(
                        title=title,
                        url=url,
                        content=content,
                        published_date=published_date,
                        source_name=f"{self.name} (via {original_source})"
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error processing CryptoPanic article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching articles from {self.name}: {e}")
        
        return articles
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract content from the linked article.
        
        Args:
            url: URL of the article
            
        Returns:
            String containing the article text
        """
        try:
            # Basic content extraction - could be improved with a dedicated scraper for each source
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Use BeautifulSoup to parse the HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try to find the main content
            # This is a simple approach - for production, would need more sophisticated scraping
            content_elements = soup.find_all(['p', 'article', 'div.content', 'div.article-content'])
            content = "\n".join([elem.get_text().strip() for elem in content_elements[:10]])
            
            # Clean the content
            import re
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""
