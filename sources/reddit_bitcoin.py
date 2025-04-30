import logging
import os
import re
from datetime import datetime
from typing import List, Optional

import requests
from dateutil import parser

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)


class RedditBitcoinSource(NewsSource):
    """Handler for Reddit r/Bitcoin subreddit."""
    
    # Reddit API endpoints
    HOT_API_URL = "https://www.reddit.com/r/Bitcoin/hot.json"
    NEW_API_URL = "https://www.reddit.com/r/Bitcoin/new.json"
    RISING_API_URL = "https://www.reddit.com/r/Bitcoin/rising.json"
    COMMENT_URL_TEMPLATE = "https://www.reddit.com/r/Bitcoin/comments/{post_id}/.json"
    
    # Minimum text length to consider post valid
    MIN_TEXT_LENGTH = 100
    
    # VIP keywords that should bypass filtering - posts with these terms are always considered valuable
    VIP_KEYWORDS = [
        'jack dorsey', 'dorsey', 'square', 'block', 'michael saylor', 'saylor', 'microstrategy',
        'blackrock', 'larry fink', 'spot etf', 'elon musk', 'tesla', 'argentina', 'el salvador',
        'major investment', 'institutional', 'sec approval', 'fed', 'federal reserve'
    ]
    
    @property
    def name(self) -> str:
        return "Reddit Bitcoin"
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch recent Bitcoin posts from Reddit from multiple sort types (hot, rising, new).
        
        Args:
            limit: Maximum number of posts to fetch
            
        Returns:
            List of Article objects
        """
        articles = []
        post_ids_seen = set()  # Track unique posts across different sort types
        
        # Define the sort types to check (hot, rising, new)
        sort_types = [
            (self.HOT_API_URL, "hot"),
            (self.RISING_API_URL, "rising"),
            (self.NEW_API_URL, "new")
        ]
        
        # Set up headers to avoid rate limiting
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Calculate how many posts to fetch per sort type
        posts_per_sort = max(5, limit // 3) 
        
        try:
            # Iterate through each sort type (hot, rising, new)
            for api_url, sort_type in sort_types:
                if len(articles) >= limit:
                    break
                    
                logger.info(f"Checking r/Bitcoin {sort_type} posts...")
                
                try:
                    # Fetch posts of this sort type
                    params = {'limit': posts_per_sort * 3}  # Get 3x to allow for filtering
                    response = requests.get(api_url, headers=headers, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Process each post from this sort type
                    for post in data.get('data', {}).get('children', []):
                        if len(articles) >= limit:
                            break
                        
                        try:
                            # Get post data
                            post_data = post.get('data', {})
                            post_id = post_data.get('id', '')
                            
                            # Skip if already seen this post in another sort
                            if post_id in post_ids_seen:
                                continue
                                
                            # Track that we've seen this post
                            post_ids_seen.add(post_id)
                            
                            # Skip stickied posts (usually rules or announcements)
                            if post_data.get('stickied', False):
                                continue
                            
                            # Extract post details
                            title = post_data.get('title', '')
                            url = f"https://www.reddit.com/r/Bitcoin/comments/{post_id}/"
                            selftext = post_data.get('selftext', '')
                            
                            # Check if post contains VIP keywords - these posts should never be filtered out
                            contains_vip_keyword = any(keyword.lower() in title.lower() for keyword in self.VIP_KEYWORDS)
                            
                            # Skip media posts without text unless they have VIP keywords or sufficient selftext
                            if self._is_media_post(post_data) and not selftext and not contains_vip_keyword:
                                logger.debug(f"Skipping media post without text: {title}")
                                continue
                            elif contains_vip_keyword and self._is_media_post(post_data):
                                logger.info(f"Found VIP keyword post (keeping despite being media): {title}")
                            
                            # Initialize content variables
                            content = ""
                            source_description = ""
                            
                            # Handle external link posts vs self posts
                            post_url = post_data.get('url')
                            if post_url and post_url.startswith('http') and 'reddit.com' not in post_url:
                                # External link post - try to extract content from the link
                                source_description = f"External link: {post_url}"
                                external_content = self.extract_article_content(post_url)
                                
                                if external_content:
                                    # Combine selftext with external content if available
                                    if selftext:
                                        content = f"[Reddit Post]\n{selftext}\n\n[External Content]\n{external_content}"
                                    else:
                                        content = external_content
                            else:
                                # Self post - use the post's own text
                                source_description = "Self post"
                                content = selftext
                            
                            # If content is low quality, try to enhance with comments
                            if self._is_low_quality_content(content):
                                comments = self._fetch_top_comments(post_id)
                                if comments:
                                    if content:
                                        content += f"\n\n[Top Comments]\n{comments}"
                                    else:
                                        content = f"[Top Comments]\n{comments}"
                                    source_description += " with comments"
                            
                            # Final quality check
                            if self._is_low_quality_content(content):
                                logger.debug(f"Skipping low quality content post: {title}")
                                continue
                            
                            # Parse post date and author
                            created_utc = post_data.get('created_utc', 0)
                            published_date = datetime.fromtimestamp(created_utc) if created_utc else datetime.now()
                            author = post_data.get('author', 'anonymous')
                            
                            # Create and add the article
                            article = Article(
                                title=title,
                                url=url,
                                content=content,
                                published_date=published_date,
                                source_name=f"{self.name} (by u/{author})"
                            )
                            
                            articles.append(article)
                            logger.debug(f"Added {sort_type} post: {title}")
                            
                        except Exception as e:
                            logger.error(f"Error processing Reddit post: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error fetching {sort_type} posts from Reddit: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in Reddit source: {e}")
        
        logger.info(f"Found {len(articles)} articles from Reddit across multiple sort types")
        return articles
    
    def _is_media_post(self, post_data: dict) -> bool:
        """
        Check if a post is primarily media (image/video).
        
        Args:
            post_data: Post data from Reddit API
            
        Returns:
            Boolean indicating if it's a media post
        """
        # Check various media indicators
        return (
            post_data.get('is_video', False) or
            post_data.get('is_gallery', False) or
            post_data.get('is_reddit_media_domain', False) or
            post_data.get('post_hint', '') == 'image' or
            '.jpg' in post_data.get('url', '') or
            '.png' in post_data.get('url', '') or
            '.gif' in post_data.get('url', '') or
            'imgur.com' in post_data.get('url', '') or
            'i.redd.it' in post_data.get('url', '')
        )
    
    def _is_low_quality_content(self, content: str) -> bool:
        """
        Check if content is too short or appears to be binary/image data.
        
        Args:
            content: The content string to check
            
        Returns:
            Boolean indicating if content is low quality
        """
        if not content:
            return True
            
        # Check if content is too short
        if len(content.strip()) < self.MIN_TEXT_LENGTH:
            return True
            
        # Check for binary data markers
        binary_indicators = [
            'ÿØÿÛ',  # JPEG SOI marker
            '‰PNG',   # PNG signature
            'GIF89a', # GIF signature
            '\x89PNG', # PNG signature (binary)
            'PK\x03\x04', # ZIP signature
            '\xFF\xD8\xFF', # JPEG SOI marker (binary)
        ]
        
        for indicator in binary_indicators:
            if indicator in content[:20]:
                return True
                
        # Check if content is mostly non-text characters
        text_chars = sum(c.isalpha() or c.isspace() or c.isdigit() or c in '.,;:!?-()[]{}\'\"' for c in content[:200])
        if text_chars / max(1, len(content[:200])) < 0.7:  # Less than 70% text characters
            return True
            
        return False
    
    def _fetch_top_comments(self, post_id: str, limit: int = 5) -> Optional[str]:
        """
        Fetch top comments for a Reddit post.
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to fetch
            
        Returns:
            String containing concatenated comments or None
        """
        try:
            url = self.COMMENT_URL_TEMPLATE.format(post_id=post_id)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 2 or 'data' not in data[1]:
                return None
                
            comments_data = data[1]['data']['children']
            
            comments = []
            for i, comment_wrapper in enumerate(comments_data):
                if i >= limit:
                    break
                    
                if comment_wrapper.get('kind') != 't1':  # t1 is a comment
                    continue
                    
                comment = comment_wrapper.get('data', {})
                body = comment.get('body', '')
                author = comment.get('author', 'anonymous')
                
                if body and author != 'AutoModerator':  # Skip AutoModerator comments
                    comments.append(f"u/{author}: {body}")
            
            if not comments:
                return None
                
            return "\n\n".join(comments)
            
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            return None
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract content from an external URL linked from Reddit.
        
        Args:
            url: URL of the article
            
        Returns:
            String containing the article text
        """
        try:
            # Basic content extraction - could be improved with a dedicated scraper for each domain
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Check content type to make sure it's not an image or binary file
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type and 'application/json' not in content_type:
                return ""
            
            # Use BeautifulSoup to parse the HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Try common article container selectors
            article_selectors = [
                'article', '.article', '.post', '.content', 
                '.article-content', '.entry-content', '.post-content',
                'main', '#main', '#content', '.main-content'
            ]
            
            content = ""
            
            # Try to find the main content using selectors
            for selector in article_selectors:
                content_container = soup.select_one(selector)
                if content_container:
                    paragraphs = content_container.find_all('p')
                    if paragraphs:
                        content = " ".join([p.get_text().strip() for p in paragraphs])
                        break
            
            # If no content found with selectors, get all paragraphs
            if not content:
                paragraphs = soup.find_all('p')
                # Filter out very short paragraphs (likely UI elements)
                paragraphs = [p for p in paragraphs if len(p.get_text().strip()) > 20]
                if paragraphs:
                    content = " ".join([p.get_text().strip() for p in paragraphs[:15]])  # Limit to first 15 paragraphs
            
            # Clean the content
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""
