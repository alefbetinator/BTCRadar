"""
NOTE: This source is currently not working as CoinDesk's website structure 
appears to use client-side rendering which makes it difficult to scrape directly.
The selectors used in this implementation may need to be updated in the future
if you wish to integrate CoinDesk as a news source.

This file is kept for reference and potential future use.
"""

import re
import logging
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from dateutil import parser

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)


class CoinDeskSource(NewsSource):
    """Handler for CoinDesk news source."""
    
    @property
    def name(self) -> str:
        return "CoinDesk"
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch recent Bitcoin articles from CoinDesk.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        articles = []
        
        try:
            # Access the Bitcoin tag page
            url = "https://www.coindesk.com/tag/bitcoin/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find article containers - CoinDesk uses div cards for articles
            article_elements = soup.select('.article-cardstyles__AcTitle-sc-q1x8lc-1')
            
            for i, article_elem in enumerate(article_elements):
                if i >= limit:
                    break
                
                try:
                    # Extract article details
                    parent_card = article_elem.find_parent('article')
                    if not parent_card:
                        continue
                    
                    # Get title and URL
                    title_elem = parent_card.select_one('h6 a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    article_url = "https://www.coindesk.com" + title_elem['href'] if title_elem['href'].startswith('/') else title_elem['href']
                    
                    # Extract date if available
                    date_elem = parent_card.select_one('time')
                    published_date = None
                    if date_elem and date_elem.has_attr('datetime'):
                        try:
                            date_text = date_elem['datetime']
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
                    logger.error(f"Error processing CoinDesk article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching articles from {self.name}: {e}")
        
        return articles
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract the full content of a CoinDesk article.
        
        Args:
            url: URL of the article
            
        Returns:
            String containing the full article text
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find the article content container
            content_div = soup.select_one('.at-content-wrapper')
            
            if not content_div:
                # Try alternative content selector
                content_div = soup.select_one('.contentstyle__StyledWrapper-sc-1m8jtgy-0')
                
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
