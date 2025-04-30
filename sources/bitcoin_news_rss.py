import logging
import re
import time
from datetime import datetime
from typing import List

import requests
import feedparser
from bs4 import BeautifulSoup

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)
console_logger = logging.getLogger("console")


class BitcoinNewsRSSSource(NewsSource):
    """Handler for Bitcoin News RSS Feed."""
    
    @property
    def name(self) -> str:
        return "Bitcoin News RSS"
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch recent Bitcoin news from dedicated Bitcoin news RSS feeds.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        articles = []
        
        try:
            console_logger.info(f"📡 Checking Bitcoin News RSS feeds...")
            
            # List of Bitcoin news RSS feeds
            rss_feeds = [
                {
                    "url": "https://news.bitcoin.com/feed/",
                    "name": "Bitcoin.com News"
                },
                {
                    "url": "https://bitcoinmagazine.com/.rss/full/",
                    "name": "Bitcoin Magazine"
                },
                {
                    "url": "https://cointelegraph.com/rss/tag/bitcoin",
                    "name": "Cointelegraph Bitcoin"
                },
                {
                    "url": "https://feeds.feedburner.com/CoinDesk",
                    "name": "CoinDesk"
                }
            ]
            
            total_articles = 0
            
            # Process each RSS feed
            for feed_info in rss_feeds:
                try:
                    feed_url = feed_info["url"]
                    feed_name = feed_info["name"]
                    
                    logger.info(f"Fetching from {feed_name} RSS: {feed_url}")
                    console_logger.info(f"  - Checking {feed_name}...")
                    
                    # Parse the RSS feed
                    feed = feedparser.parse(feed_url)
                    
                    # Skip if feed couldn't be parsed or has no entries
                    if not feed or not hasattr(feed, 'entries') or not feed.entries:
                        logger.warning(f"No entries found or could not parse feed: {feed_url}")
                        continue
                    
                    logger.info(f"Found {len(feed.entries)} articles in {feed_name} RSS feed")
                    feed_articles = 0
                    
                    # Process each entry in the feed
                    for entry in feed.entries:
                        if total_articles >= limit:
                            break
                            
                        try:
                            # Get article title
                            title = entry.title if hasattr(entry, 'title') else "Unknown Title"
                            
                            # Get article link
                            link = entry.link if hasattr(entry, 'link') else ""
                            if not link:
                                continue
                                
                            # Get publication date
                            published_date = datetime.now()
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                try:
                                    published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                                except Exception:
                                    pass
                                
                            # Get content
                            content = ""
                            if hasattr(entry, 'content') and entry.content:
                                content = entry.content[0].value
                            elif hasattr(entry, 'summary') and entry.summary:
                                content = entry.summary
                            elif hasattr(entry, 'description') and entry.description:
                                content = entry.description
                                
                            # If we still don't have content, extract it from the article URL
                            if not content or len(content) < 100:
                                content = self.extract_article_content(link)
                            
                            # If we have content, clean it up
                            if content:
                                # Convert HTML to text
                                soup = BeautifulSoup(content, 'html.parser')
                                content = soup.get_text(separator=' ', strip=True)
                                
                                # Clean up the content
                                content = re.sub(r'\s+', ' ', content).strip()
                                
                            # Create Article object
                            article = Article(
                                title=title,
                                url=link,
                                content=content,
                                published_date=published_date,
                                source_name=f"{feed_name}"
                            )
                            
                            articles.append(article)
                            total_articles += 1
                            feed_articles += 1
                            
                            logger.info(f"Added article: {title}")
                            
                        except Exception as e:
                            logger.error(f"Error processing RSS entry: {e}")
                            continue
                    
                    console_logger.info(f"    Found {feed_articles} articles from {feed_name}")
                    
                except Exception as e:
                    logger.error(f"Error fetching from RSS feed {feed_info['name']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching articles from {self.name}: {e}")
            
        return articles
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract content from an article URL.
        
        Args:
            url: URL of the article
            
        Returns:
            Extracted content as a string
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts, styles, and other non-content elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try to find the main content
            article_selectors = [
                'article', 
                'main', 
                '[role="main"]',
                '.post-content',
                '.article-content',
                '.entry-content',
                '.content',
                '#content'
            ]
            
            content = ""
            
            # Try each selector until we find content
            for selector in article_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Get all paragraphs inside the content element
                    paragraphs = content_elem.find_all('p')
                    if paragraphs:
                        content = ' '.join(p.get_text(strip=True) for p in paragraphs)
                        break
            
            # If no content was found with the selectors, fall back to getting all paragraphs
            if not content:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = ' '.join(p.get_text(strip=True) for p in paragraphs)
            
            # If still no content, get the body text
            if not content:
                content = soup.body.get_text(separator=' ', strip=True)
            
            # Clean up the content
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from URL {url}: {e}")
            return ""
