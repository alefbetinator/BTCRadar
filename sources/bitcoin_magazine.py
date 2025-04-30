import logging
import re
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from dateutil import parser

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)


class BitcoinMagazineSource(NewsSource):
    """Handler for Bitcoin Magazine news source."""
    
    @property
    def name(self) -> str:
        return "Bitcoin Magazine"
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch recent articles from Bitcoin Magazine via RSS feed.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        articles = []
        
        try:
            # First try the RSS feed which is more reliable than scraping
            rss_url = "https://bitcoinmagazine.com/.rss/full/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            logger.info(f"Fetching articles from Bitcoin Magazine RSS: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                # Try alternative RSS URL if the first one fails
                rss_url = "https://bitcoinmagazine.com/feed"
                logger.info(f"Trying alternative RSS feed: {rss_url}")
                response = requests.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse RSS content
                soup = BeautifulSoup(response.content, 'xml')
                
                # Get all items from the feed
                items = soup.find_all('item')
                
                if not items:
                    logger.warning("No RSS items found in Bitcoin Magazine feed")
                    # Fall back to the older method if RSS fails
                    return self._fetch_articles_by_scraping(limit)
                
                logger.info(f"Found {len(items)} articles in Bitcoin Magazine RSS feed")
                
                for i, item in enumerate(items):
                    if i >= limit:
                        break
                    
                    try:
                        # Extract article details from RSS
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        description_elem = item.find('description')
                        date_elem = item.find('pubDate')
                        
                        if not title_elem or not link_elem:
                            logger.warning("Missing title or link in RSS item")
                            continue
                        
                        title = title_elem.text.strip()
                        article_url = link_elem.text.strip()
                        
                        # Extract content either from the full content or description
                        content_elem = item.find('content:encoded') or description_elem
                        
                        if content_elem:
                            content = content_elem.text.strip()
                        else:
                            # If no content in RSS, fetch the article
                            try:
                                content = self.extract_article_content(article_url)
                            except Exception as e:
                                logger.warning(f"Error extracting content from {article_url}: {e}")
                                content = "Content extraction failed. Please check the original article."
                        
                        # Parse date
                        published_date = datetime.now()  # Default
                        if date_elem:
                            try:
                                published_date = parser.parse(date_elem.text.strip())
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Could not parse date '{date_elem.text.strip()}': {e}")
                        
                        # Create article
                        article = Article(
                            title=title,
                            url=article_url,
                            content=content,
                            published_date=published_date,
                            source_name=self.name
                        )
                        
                        articles.append(article)
                        logger.info(f"Added article: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error processing RSS item: {e}")
                        continue
                
                # If we found articles via RSS, return them
                if articles:
                    return articles
                    
            else:
                logger.warning(f"Failed to access Bitcoin Magazine RSS feed: HTTP {response.status_code}")
                
            # If RSS failed or returned no articles, fall back to scraping
            if not articles:
                logger.info("Falling back to web scraping method")
                return self._fetch_articles_by_scraping(limit)
                
        except Exception as e:
            logger.error(f"Error fetching articles from {self.name} RSS: {e}")
            # Try the fallback method
            return self._fetch_articles_by_scraping(limit)
        
        # If all else fails, create a mock article
        if not articles:
            logger.warning("Failed to get any articles from Bitcoin Magazine, creating a mock article")
            mock_article = Article(
                title="Bitcoin Magazine Latest Articles",
                url="https://bitcoinmagazine.com/",
                content="This is a placeholder for Bitcoin Magazine content. Due to technical difficulties, we couldn't fetch the latest articles.",
                published_date=datetime.now(),
                source_name=self.name
            )
            articles.append(mock_article)
            
        return articles
        
    def _fetch_articles_by_scraping(self, limit: int = 10) -> List[Article]:
        """
        Fallback method to fetch articles by scraping the website directly.
        Only used if RSS feed approach fails.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        articles = []
        
        try:
            # Access the articles page
            url = "https://bitcoinmagazine.com"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Log the HTML structure for debugging
            logger.debug(f"Page title: {soup.title.text if soup.title else 'No title found'}")
            
            # Try different selectors based on possible page structures
            article_elements = []
            
            # Try various selectors that might contain articles
            for selector in [
                'article',
                '.post',
                '.article',
                '.card',
                '.post-card',
                '.article-card',
                '.post-item',
                '.article-item',
                'a[href*="/articles/"]'
            ]:
                elements = soup.select(selector)
                if elements:
                    article_elements.extend(elements)
                    logger.debug(f"Found {len(elements)} elements with selector '{selector}'")
            
            # Remove duplicates while preserving order
            seen_urls = set()
            filtered_articles = []
            for elem in article_elements:
                link = elem.select_one('a[href]') if elem.name != 'a' else elem
                if link and link.get('href'):
                    url = link['href']
                    if url not in seen_urls:
                        seen_urls.add(url)
                        filtered_articles.append(elem)
            
            logger.info(f"Found {len(filtered_articles)} unique article elements")
            
            for i, article_elem in enumerate(filtered_articles):
                if i >= limit:
                    break
                
                try:
                    # Extract article details
                    link = article_elem if article_elem.name == 'a' else article_elem.select_one('a[href]')
                    if not link or not link.get('href'):
                        continue
                        
                    article_url = link['href']
                    
                    # Make sure URL is absolute
                    if article_url.startswith('/'):
                        article_url = f"https://bitcoinmagazine.com{article_url}"
                    elif not article_url.startswith('http'):
                        article_url = f"https://bitcoinmagazine.com/{article_url}"
                    
                    # Verify this is a Bitcoin Magazine article
                    if 'bitcoinmagazine.com' not in article_url:
                        continue
                    
                    # Find the title - check various options
                    title = None
                    
                    # Option 1: Check heading elements within the article element
                    for heading in article_elem.select('h1, h2, h3, h4, h5'):
                        if heading.text.strip():
                            title = heading.text.strip()
                            break
                    
                    # Option 2: Check for title in the link text
                    if not title and link.text.strip() and len(link.text.strip()) > 5:
                        title = link.text.strip()
                    
                    # Option 3: Check for common title class names
                    if not title:
                        title_elem = article_elem.select_one('.title, .post-title, .entry-title')
                        if title_elem:
                            title = title_elem.text.strip()
                    
                    # Skip if no title found
                    if not title:
                        continue
                    
                    # Get article content
                    try:
                        content = self.extract_article_content(article_url)
                        # If content extraction failed, skip this article
                        if not content:
                            logger.warning(f"No content extracted from {article_url}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error extracting content from {article_url}: {e}")
                        continue
                    
                    # Extract date if available
                    date_elem = article_elem.select_one('time, .date, .posted-date, .post-date')
                    published_date = datetime.now()  # Default to current time
                    
                    if date_elem:
                        date_text = date_elem.text.strip()
                        try:
                            published_date = parser.parse(date_text)
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Could not parse date '{date_text}': {e}")
                    
                    # Create Article object
                    article = Article(
                        title=title,
                        url=article_url,
                        content=content,
                        published_date=published_date,
                        source_name=self.name
                    )
                    
                    articles.append(article)
                    logger.info(f"Added article (via scraping): {title}")
                    
                except Exception as e:
                    logger.error(f"Error processing Bitcoin Magazine article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching articles from {self.name} via scraping: {e}")
        
        return articles
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract the full content of a Bitcoin Magazine article.
        
        Args:
            url: URL of the article
            
        Returns:
            String containing the full article text
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find the article content container
            content_div = (
                soup.select_one('.post-content') or 
                soup.select_one('.article-content') or 
                soup.select_one('.entry-content') or
                soup.select_one('article')
            )
                
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
