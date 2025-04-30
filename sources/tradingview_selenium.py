import logging
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)
console_logger = logging.getLogger("console")


class TradingViewSource(NewsSource):
    """Handler for TradingView BTC/USD page using Selenium."""
    
    @property
    def name(self) -> str:
        return "TradingView"
    
    def __init__(self):
        """Initialize the TradingView source."""
        self.driver = None
        
    def _initialize_driver(self):
        """Initialize the Selenium WebDriver."""
        if self.driver is not None:
            return
            
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36")
            
            # Initialize the WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Initialized Selenium WebDriver for TradingView")
            
        except Exception as e:
            logger.error(f"Error initializing WebDriver: {e}")
            self.driver = None
            
    def _close_driver(self):
        """Close the Selenium WebDriver."""
        if self.driver is not None:
            try:
                self.driver.quit()
                logger.info("Closed Selenium WebDriver")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """Fetch BTC news articles from TradingView using Selenium."""
        articles = []
        
        try:
            logger.info("Fetching from TradingView using Selenium...")
            
            # Initialize a Chrome WebDriver instance with headless mode
            self._initialize_driver()
            
            if not self.driver:
                logger.error("Failed to initialize Selenium WebDriver")
                return []
            
            # First, extract key facts from the main BTC/USD page
            logger.info("Checking TradingView BTC/USD page (with Selenium)...")
            self._extract_from_main_page(articles, limit)
            
            # Then, extract news from the dedicated news page
            logger.info("Checking TradingView BTC/USD news page...")
            self._extract_from_news_page(articles, limit)
            
            # Close the WebDriver
            self._close_driver()
            
            logger.info(f"Found {len(articles)} items from TradingView BTC/USD page")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching articles from TradingView with Selenium: {e}")
            if self.driver:
                self._close_driver()
            return articles

    def _extract_from_main_page(self, articles: List[Article], limit: int):
        """Extract content from the main BTC/USD page."""
        try:
            # Navigate to the BTC/USD page
            self.driver.get("https://www.tradingview.com/symbols/BTCUSD/")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait longer for JavaScript to render content
            time.sleep(10)
            
            logger.info("Page loaded, attempting to extract content...")
            
            # Take a screenshot for debugging
            try:
                screenshot_path = "tradingview_screenshot.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot to {screenshot_path}")
            except Exception as e:
                logger.error(f"Error saving screenshot: {e}")
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Save the HTML for debugging
            try:
                with open("tradingview_page.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                logger.info("Saved page HTML for debugging")
            except Exception as e:
                logger.error(f"Error saving HTML: {e}")
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract key facts - this is the new high-value section
            self._extract_key_facts(soup, articles, limit)
            
            # Extract news items
            self._extract_news_feed(soup, articles, limit)
            
            # Extract market updates
            self._extract_market_updates(soup, articles, limit)
            
        except Exception as e:
            logger.error(f"Error extracting from main page: {e}")
    
    def _extract_from_news_page(self, articles: List[Article], limit: int):
        """Extract news articles from the dedicated BTC/USD news page."""
        try:
            # Navigate to the BTC/USD news page
            self.driver.get("https://www.tradingview.com/symbols/BTCUSD/news/?exchange=BITSTAMP")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait longer for JavaScript to render content
            time.sleep(10)
            
            logger.info("News page loaded, attempting to extract content...")
            
            # Take a screenshot for debugging
            try:
                screenshot_path = "tradingview_news_screenshot.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Saved news page screenshot to {screenshot_path}")
            except Exception as e:
                logger.error(f"Error saving news screenshot: {e}")
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Save the HTML for debugging
            try:
                with open("tradingview_news_page.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                logger.info("Saved news page HTML for debugging")
            except Exception as e:
                logger.error(f"Error saving news HTML: {e}")
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Process news articles
            self._process_news_articles(soup, articles, limit)
            
        except Exception as e:
            logger.error(f"Error extracting from news page: {e}")
    
    def _process_news_articles(self, soup: BeautifulSoup, articles: List[Article], limit: int):
        """Process and extract news articles from the news page."""
        try:
            # Try various strategies to find news articles
            
            # Strategy 1: Look for article elements
            news_items = soup.select('article, [class*="article"], [class*="news-item"], [class*="newsItem"]')
            
            # Strategy 2: Look for containers with title and description
            if not news_items:
                news_items = soup.select('div:has(h2, h3):has(p), div:has(a[href*="/news/"])')
            
            # Strategy 3: Try JavaScript to find news elements
            if not news_items and self.driver:
                try:
                    # Use JavaScript to find possible news elements
                    news_elements = self.driver.execute_script("""
                        return Array.from(document.querySelectorAll('*')).filter(el => 
                            (el.textContent.includes('news') || 
                             el.textContent.includes('article') ||
                             el.textContent.includes('bitcoin') ||
                             el.textContent.includes('btc')) &&
                            (el.querySelector('a, h2, h3') || 
                             el.classList.contains('article') || 
                             el.classList.contains('news'))
                        );
                    """)
                    
                    if news_elements:
                        # Convert the JavaScript elements to HTML and parse with BeautifulSoup
                        js_html = self.driver.execute_script("""
                            return arguments[0].map(el => el.outerHTML).join('');
                        """, news_elements)
                        
                        if js_html:
                            js_soup = BeautifulSoup(js_html, 'html.parser')
                            news_items.extend(js_soup.find_all())
                            
                except Exception as e:
                    logger.error(f"Error finding news elements with JavaScript: {e}")
            
            if not news_items:
                logger.warning("No news articles found on TradingView BTC/USD news page")
                return
            
            logger.info(f"Found {len(news_items)} potential news items to process")
            
            for item in news_items:
                if len(articles) >= limit:
                    return
                
                try:
                    # Extract title
                    title_elem = item.select_one('h1, h2, h3, h4, a, [class*="title"]')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue
                    
                    # Extract URL
                    url = None
                    if title_elem.name == 'a' and title_elem.get('href'):
                        url = title_elem['href']
                    else:
                        url_elem = item.select_one('a')
                        if url_elem and url_elem.get('href'):
                            url = url_elem['href']
                    
                    # Fix relative URLs
                    if url and url.startswith('/'):
                        url = f"https://www.tradingview.com{url}"
                    elif not url:
                        url = "https://www.tradingview.com/symbols/BTCUSD/news/?exchange=BITSTAMP"
                    
                    # DON'T add timestamps to URLs - we want duplicate detection to work
                    # Make the URL unique to prevent duplicate detection
                    # if url:
                    #     url = f"{url}?timestamp={datetime.now().timestamp()}"
                    # else:
                    #     url = f"https://www.tradingview.com/symbols/BTCUSD/news/?timestamp={datetime.now().timestamp()}"
                    
                    # Extract content/description
                    content_elem = item.select_one('p, [class*="content"], [class*="description"], [class*="summary"]')
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    # If no specific content element found, use the whole item text excluding the title
                    if not content:
                        full_text = item.get_text(strip=True)
                        content = full_text.replace(title, '').strip()
                    
                    # If still no content, use title as content
                    if not content:
                        content = title
                    
                    # Extract date if available
                    date_elem = item.select_one('[class*="date"], [class*="time"], time')
                    published_date = None
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        try:
                            # Try to parse the date text
                            # This is a simplified approach, might need adjustments based on actual format
                            if 'ago' in date_text.lower():
                                # Handle relative times like "2 hours ago"
                                published_date = datetime.now()
                            else:
                                # Try common date formats
                                for fmt in ['%b %d, %Y', '%Y-%m-%d', '%d %b %Y', '%B %d, %Y']:
                                    try:
                                        published_date = datetime.strptime(date_text, fmt)
                                        break
                                    except ValueError:
                                        continue
                        except Exception:
                            # Default to current date if parsing fails
                            published_date = datetime.now()
                    
                    if not published_date:
                        published_date = datetime.now()
                    
                    # Create Article object
                    article = Article(
                        title=title,
                        url=url,
                        content=content,
                        published_date=published_date,
                        source_name=f"{self.name} News"
                    )
                    
                    # Check if it's Bitcoin-related
                    is_bitcoin_related = any(term in (title + ' ' + content).lower() 
                                           for term in ['bitcoin', 'btc', 'crypto', 'blockchain'])
                    
                    # Since we're on the BTCUSD news page, we can assume most articles are Bitcoin-related
                    # But still double-check to filter out unrelated content
                    if is_bitcoin_related or 'btcusd' in url.lower():
                        articles.append(article)
                        logger.info(f"Added news article: {title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Error processing news item: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error processing news articles: {e}")
    
    def _extract_key_facts(self, soup: BeautifulSoup, articles: List[Article], limit: int):
        """Extract 'Key facts today' carousel items from the page."""
        try:
            # Try a broader approach to find any content areas
            logger.info("Searching for key facts with various selector strategies...")
            
            # Strategy 1: Look for headings containing "Key facts"
            headings = soup.find_all(['h1', 'h2', 'h3'], string=lambda text: text and ('key facts' in text.lower() or 'today' in text.lower()))
            if headings:
                logger.info(f"Found {len(headings)} headings related to key facts")
                for heading in headings:
                    # Try to get the parent container
                    container = heading.parent
                    if container:
                        logger.info(f"Found potential facts container: {container.name} with classes {container.get('class', '')}")
            
            # Strategy 2: Look for elements with 'carousel' in class name or id
            carousel_elements = soup.select('[class*="carousel"], [class*="slider"], [id*="carousel"], [id*="slider"]')
            if carousel_elements:
                logger.info(f"Found {len(carousel_elements)} potential carousel elements")
            
            # Strategy 3: Look for any div containing both headings and paragraphs
            content_sections = soup.select('div:has(h2):has(p)')
            if content_sections:
                logger.info(f"Found {len(content_sections)} content sections with headings and paragraphs")
            
            # Combine all potential containers
            all_containers = []
            if headings:
                all_containers.extend([h.parent for h in headings if h.parent])
            all_containers.extend(carousel_elements)
            all_containers.extend(content_sections)
            
            # If no containers found, try one last approach - any div with multiple paragraphs
            if not all_containers:
                paragraph_groups = soup.select('div:has(p + p)')
                all_containers.extend(paragraph_groups)
                logger.info(f"Found {len(paragraph_groups)} paragraph groups")
            
            if not all_containers:
                logger.warning("No key facts carousel found on TradingView BTC/USD page")
                return
                
            logger.info(f"Found {len(all_containers)} potential fact containers to process")
            
            # Process each container
            for container in all_containers:
                # Try multiple strategies to extract fact items
                fact_items = []
                
                # 1. Look for direct children that are divs
                children_divs = container.find_all('div', recursive=False)
                if children_divs:
                    fact_items.extend(children_divs)
                
                # 2. Look for paragraphs
                paragraphs = container.find_all('p')
                if paragraphs:
                    fact_items.extend(paragraphs)
                
                # 3. Look for specific article-like elements
                articles_elements = container.select('article, .item, [class*="item"], [class*="card"]')
                if articles_elements:
                    fact_items.extend(articles_elements)
                
                if not fact_items:
                    continue
                    
                logger.info(f"Found {len(fact_items)} potential fact items to process")
                
                # Process each fact item
                for item in fact_items:
                    if len(articles) >= limit:
                        return
                        
                    try:
                        # Get the item's text content
                        item_text = item.get_text(strip=True)
                        
                        # Skip if empty
                        if not item_text:
                            continue
                        
                        # Try to extract a title and content
                        title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
                        title = title_elem.get_text(strip=True) if title_elem else "Key Insight"
                        
                        # Content could be in a paragraph or the rest of the text
                        if title_elem and title_elem.get_text(strip=True) in item_text:
                            content = item_text.replace(title_elem.get_text(strip=True), '').strip()
                        else:
                            content = item_text
                        
                        # If no separate content, use the whole text
                        if not content:
                            content = item_text
                            
                        # Skip if too short to be meaningful
                        if len(content) < 20:
                            continue
                            
                        # Create Article object
                        article = Article(
                            title=f"TradingView Key Fact: {title[:50]}",
                            url="https://www.tradingview.com/symbols/BTCUSD/key-fact",
                            content=content,
                            published_date=datetime.now(),
                            source_name=f"{self.name} Key Facts"
                        )
                        
                        # Check if the content is Bitcoin-related or add anyway if specifically from key facts
                        bitcoin_related = any(term in content.lower() or term in title.lower() 
                                             for term in ['bitcoin', 'btc', 'crypto', 'blockchain'])
                        
                        if bitcoin_related:
                            articles.append(article)
                            logger.info(f"Added key fact: {content[:60]}...")
                        
                    except Exception as e:
                        logger.error(f"Error processing key fact item: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error extracting key facts: {e}")
    
    def _extract_news_feed(self, soup: BeautifulSoup, articles: List[Article], limit: int):
        """Extract news feed items from the page."""
        try:
            # Try various selectors that might contain news
            news_containers = soup.select('div.newsFeed, div.news-feed, div.feed, div.newsFeedWithTimeFrame')
            
            if not news_containers:
                logger.warning("No news feed containers found on TradingView BTC/USD page")
                return
                
            # Process each news container
            for container in news_containers:
                # Look for news items
                news_items = container.select('div.newsFeedItem, div.card-news, article.card, div.newsFeedWithTimeFrame__item')
                
                if not news_items:
                    continue
                    
                logger.info(f"Found {len(news_items)} news items in feed container")
                
                # Process each news item
                for item in news_items:
                    if len(articles) >= limit:
                        return
                        
                    try:
                        # Extract title
                        title_elem = item.select_one('a.title, a.newsFeedItemHeading, h3 a')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        
                        # Extract URL
                        item_url = title_elem.get('href', '')
                        if not item_url.startswith('http'):
                            item_url = f"https://www.tradingview.com{item_url}"
                        
                        # DON'T add timestamps to URLs - we want duplicate detection to work
                        # Make the URL unique to prevent duplicate detection
                        # if item_url:
                        #     item_url = f"{item_url}?timestamp={datetime.now().timestamp()}"
                        
                        # Extract preview text
                        preview_elem = item.select_one('div.desc, div.description, p.newsFeedItemHeading__description')
                        preview = preview_elem.get_text(strip=True) if preview_elem else ""
                        
                        # Create Article object
                        article = Article(
                            title=title,
                            url=item_url,
                            content=preview,  # Use preview as initial content, could fetch full content later
                            published_date=datetime.now(),  # Use current time as fallback
                            source_name=f"{self.name} News"
                        )
                        
                        articles.append(article)
                        logger.info(f"Added news item: {title[:60]}...")
                        
                    except Exception as e:
                        logger.error(f"Error processing news item: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error extracting news feed: {e}")
    
    def _extract_market_updates(self, soup: BeautifulSoup, articles: List[Article], limit: int):
        """Extract market updates and important signals."""
        try:
            # Extract technical indicators
            indicator_container = soup.select_one('div.technicalIndicators, div.technicalAnalysis')
            
            if indicator_container:
                # Extract summary text
                summary_elem = indicator_container.select_one('div.summary, span.recommendation')
                
                if summary_elem:
                    recommendation = summary_elem.get_text(strip=True)
                    
                    # Create Article for technical summary
                    summary_article = Article(
                        title=f"BTC/USD Technical Analysis: {recommendation}",
                        url="https://www.tradingview.com/symbols/BTCUSD/",
                        content=f"TradingView's technical indicators for Bitcoin (BTC/USD) are currently showing: {recommendation}.",
                        published_date=datetime.now(),
                        source_name=f"{self.name} Technical Analysis"
                    )
                    
                    articles.append(summary_article)
                    logger.info(f"Added technical analysis summary: {recommendation}")
        
        except Exception as e:
            logger.error(f"Error extracting market updates: {e}")
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract content from a TradingView article URL.
        
        Args:
            url: URL of the article
            
        Returns:
            Extracted content as a string
        """
        try:
            # Initialize the WebDriver if not already initialized
            self._initialize_driver()
            
            if self.driver is None:
                logger.error("WebDriver initialization failed. Cannot extract article content.")
                return "Failed to initialize WebDriver for content extraction."
                
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give time for JavaScript to render content
            time.sleep(5)
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try to find the article content
            content_elem = soup.select_one('div.tv-news-item__body, article.content, div.content')
            
            if content_elem:
                content = content_elem.get_text(separator=' ', strip=True)
            else:
                # If no specific content element found, get all paragraphs
                paragraphs = soup.select('p')
                content = ' '.join(p.get_text(strip=True) for p in paragraphs)
            
            # Clean up the content
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from URL {url}: {e}")
            return f"Failed to extract content: {str(e)}"
            
        finally:
            # Close the driver after use to free resources
            self._close_driver()
