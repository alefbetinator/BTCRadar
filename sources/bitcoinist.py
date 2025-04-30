import re
import logging
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from dateutil import parser

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)


class BitcoinistSource(NewsSource):
    """Handler for Bitcoinist news source."""
    
    @property
    def name(self) -> str:
        return "Bitcoinist"
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch recent Bitcoin articles from Bitcoinist.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        articles = []
        
        try:
            # Access the Bitcoin category page
            url = "https://bitcoinist.com/category/bitcoin-news/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find article containers
            article_elements = soup.select('article.jeg_post')
            
            for i, article_elem in enumerate(article_elements):
                if i >= limit:
                    break
                
                try:
                    # Extract article details
                    title_elem = article_elem.select_one('.jeg_post_title a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    article_url = title_elem['href']
                    
                    # Extract date if available
                    date_elem = article_elem.select_one('.jeg_meta_date a')
                    published_date = None
                    if date_elem:
                        try:
                            date_text = date_elem.text.strip()
                            published_date = parser.parse(date_text)
                        except (ValueError, TypeError):
                            published_date = datetime.now()
                    else:
                        published_date = datetime.now()
                    
                    # Get article content
                    content = self.extract_article_content(article_url)
                    
                    # Create Article object
                    article = Article(
                        title=title,
                        url=article_url,
                        content=content,
                        published_date=published_date,
                        source_name=self.name
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching articles from {self.name}: {e}")
        
        return articles
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract the full content of a Bitcoinist article.
        
        Args:
            url: URL of the article
            
        Returns:
            String containing the full article text
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find the article content container
            content_div = soup.select_one('.content-inner')
            
            if not content_div:
                return ""
            
            # Extract paragraphs
            paragraphs = content_div.find_all('p')
            content = "\n".join([p.get_text().strip() for p in paragraphs])
            
            # Clean the content
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""
