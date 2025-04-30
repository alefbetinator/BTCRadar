import logging
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from .base_source import NewsSource, Article

logger = logging.getLogger(__name__)
console_logger = logging.getLogger("console")


class TradingViewAPISource(NewsSource):
    """Handler for TradingView data using unofficial API endpoints."""
    
    @property
    def name(self) -> str:
        return "TradingView API"
    
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch Bitcoin technical analysis data from TradingView API.
        
        Args:
            limit: Maximum number of articles to fetch (not used here)
            
        Returns:
            List of Article objects containing technical analysis data
        """
        articles = []
        
        try:
            console_logger.info(f"📈 Checking TradingView API for Bitcoin technical analysis...")
            logger.info(f"Fetching from {self.name}...")
            
            # Get technical analysis data
            ta_data = self._fetch_technical_analysis()
            
            if ta_data:
                # Create articles from technical data
                articles.extend(self._create_ta_articles(ta_data))
                
            # Get Bitcoin news headlines
            news_data = self._fetch_news()
            
            if news_data:
                # Create articles from news data
                articles.extend(self._create_news_articles(news_data))
            
            # Log the results
            console_logger.info(f"Found {len(articles)} items from TradingView API")
            
        except Exception as e:
            logger.error(f"Error fetching content from TradingView API: {e}")
            
        return articles[:limit]
    
    def _fetch_technical_analysis(self) -> Optional[Dict[str, Any]]:
        """Fetch technical analysis data for BTC/USD from TradingView."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                'Content-Type': 'application/json'
            }
            
            # Technical analysis endpoint
            url = "https://scanner.tradingview.com/crypto/scan"
            
            # Request for multiple indicators and timeframes
            payload = {
                "symbols": {
                    "tickers": ["COINBASE:BTCUSD"],
                    "query": {"types": []}
                },
                "columns": [
                    "Recommend.All",      # Overall recommendation
                    "Recommend.MA",       # Moving averages recommendation
                    "Recommend.Other",    # Oscillators recommendation
                    "RSI",                # Relative Strength Index
                    "RSI[1]",             # RSI previous value
                    "Stoch.K",            # Stochastic K
                    "Stoch.D",            # Stochastic D
                    "MACD.macd",          # MACD Line
                    "MACD.signal",        # MACD Signal Line
                    "ADX",                # Average Directional Index
                    "ATR",                # Average True Range
                    "Volatility.D",       # Volatility Daily
                    "Volatility.W",       # Volatility Weekly
                    "Volatility.M",       # Volatility Monthly
                    "BB.lower",           # Bollinger Bands Lower
                    "BB.upper",           # Bollinger Bands Upper
                    "AO",                 # Awesome Oscillator
                    "Pivot.M.Fibonacci.S3",  # Monthly Fibonacci S3
                    "Pivot.M.Fibonacci.S2",  # Monthly Fibonacci S2
                    "Pivot.M.Fibonacci.S1",  # Monthly Fibonacci S1
                    "Pivot.M.Fibonacci.Middle", # Monthly Fibonacci Middle
                    "Pivot.M.Fibonacci.R1",  # Monthly Fibonacci R1
                    "Pivot.M.Fibonacci.R2",  # Monthly Fibonacci R2
                    "Pivot.M.Fibonacci.R3",  # Monthly Fibonacci R3
                    "name",               # Symbol name
                    "close",              # Last price
                    "change",             # Price change percentage
                    "change_abs",         # Price change absolute
                    "volume"              # Trading volume
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    logger.info("Successfully fetched technical analysis data")
                    return data
                else:
                    logger.warning("No technical analysis data found in response")
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching technical analysis data: {e}")
            
        return None
    
    def _fetch_news(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch Bitcoin news from TradingView."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
            }
            
            # News endpoint (unofficial)
            url = "https://news-headlines.tradingview.com/v2/headlines?category=bitcoin&client=web&country=US&lang=en"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and isinstance(data, list):
                    logger.info(f"Successfully fetched {len(data)} news items")
                    return data
                else:
                    logger.warning("No news data found in response or invalid format")
            else:
                logger.error(f"News API request failed with status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching news data: {e}")
            
        return None
    
    def _create_ta_articles(self, ta_data: Dict[str, Any]) -> List[Article]:
        """Create articles from technical analysis data."""
        articles = []
        
        try:
            if "data" not in ta_data or not ta_data["data"]:
                return articles
                
            # Extract the data for BTCUSD
            btc_data = ta_data["data"][0]["d"]
            
            # Map column indices to names for better readability
            column_mapping = {
                0: "Recommend.All",
                1: "Recommend.MA",
                2: "Recommend.Other",
                3: "RSI",
                4: "RSI[1]",
                5: "Stoch.K",
                6: "Stoch.D",
                7: "MACD.macd",
                8: "MACD.signal",
                9: "ADX",
                10: "ATR",
                11: "Volatility.D",
                12: "Volatility.W",
                13: "Volatility.M",
                14: "BB.lower",
                15: "BB.upper",
                16: "AO",
                17: "Pivot.M.Fibonacci.S3",
                18: "Pivot.M.Fibonacci.S2",
                19: "Pivot.M.Fibonacci.S1",
                20: "Pivot.M.Fibonacci.Middle",
                21: "Pivot.M.Fibonacci.R1",
                22: "Pivot.M.Fibonacci.R2",
                23: "Pivot.M.Fibonacci.R3",
                24: "name",
                25: "close",
                26: "change",
                27: "change_abs",
                28: "volume"
            }
            
            # Extract values with proper names
            data_dict = {}
            for idx, value in enumerate(btc_data):
                if idx in column_mapping:
                    data_dict[column_mapping[idx]] = value
            
            # Generate the recommendation text
            recommend_all = data_dict.get("Recommend.All", 0)
            recommend_ma = data_dict.get("Recommend.MA", 0)
            recommend_other = data_dict.get("Recommend.Other", 0)
            
            # Convert recommendation values to signals
            # TradingView recommendation scale: -1 (Strong Sell) to 1 (Strong Buy)
            signal_mapping = {
                (-1.0, -0.5): "Strong Sell",
                (-0.5, -0.1): "Sell",
                (-0.1, 0.1): "Neutral",
                (0.1, 0.5): "Buy",
                (0.5, 1.0): "Strong Buy"
            }
            
            def get_signal(value):
                for (lower, upper), signal in signal_mapping.items():
                    if lower <= value <= upper:
                        return signal
                return "Neutral"  # Fallback
            
            overall_signal = get_signal(recommend_all)
            ma_signal = get_signal(recommend_ma)
            oscillators_signal = get_signal(recommend_other)
            
            # Current price
            price = data_dict.get("close", "Unknown")
            change_pct = data_dict.get("change", 0)
            
            # Create a summary article
            summary_title = f"Bitcoin Technical Analysis: {overall_signal} Signal"
            
            # Format the summary content
            summary_content = (
                f"Bitcoin (BTC/USD) Technical Analysis from TradingView:\n\n"
                f"Current Price: ${price:,.2f}\n"
                f"24h Change: {change_pct:.2f}%\n\n"
                f"Overall Signal: {overall_signal} ({recommend_all:.2f})\n"
                f"Moving Averages: {ma_signal} ({recommend_ma:.2f})\n"
                f"Oscillators: {oscillators_signal} ({recommend_other:.2f})\n\n"
                f"Technical Indicators:\n"
                f"- RSI: {data_dict.get('RSI', 'N/A'):.2f}\n"
                f"- Stochastic K/D: {data_dict.get('Stoch.K', 'N/A'):.2f}/{data_dict.get('Stoch.D', 'N/A'):.2f}\n"
                f"- MACD: {data_dict.get('MACD.macd', 'N/A'):.2f} (Signal: {data_dict.get('MACD.signal', 'N/A'):.2f})\n"
                f"- ADX: {data_dict.get('ADX', 'N/A'):.2f}\n\n"
                f"Support/Resistance Levels (Monthly Fibonacci):\n"
                f"- Resistance 3: ${data_dict.get('Pivot.M.Fibonacci.R3', 'N/A'):,.2f}\n"
                f"- Resistance 2: ${data_dict.get('Pivot.M.Fibonacci.R2', 'N/A'):,.2f}\n"
                f"- Resistance 1: ${data_dict.get('Pivot.M.Fibonacci.R1', 'N/A'):,.2f}\n"
                f"- Pivot: ${data_dict.get('Pivot.M.Fibonacci.Middle', 'N/A'):,.2f}\n"
                f"- Support 1: ${data_dict.get('Pivot.M.Fibonacci.S1', 'N/A'):,.2f}\n"
                f"- Support 2: ${data_dict.get('Pivot.M.Fibonacci.S2', 'N/A'):,.2f}\n"
                f"- Support 3: ${data_dict.get('Pivot.M.Fibonacci.S3', 'N/A'):,.2f}\n"
            )
            
            # Create the article object
            summary_article = Article(
                title=summary_title,
                url="https://www.tradingview.com/symbols/BTCUSD/",
                content=summary_content,
                published_date=datetime.now(),
                source_name=f"{self.name} Technical Analysis"
            )
            
            articles.append(summary_article)
            logger.info(f"Created technical analysis article: {summary_title}")
            
            # Create additional articles for specific signals if notable
            # For example, if RSI is in oversold or overbought territory
            rsi = data_dict.get("RSI", 50)
            if rsi > 70:
                rsi_article = Article(
                    title=f"Bitcoin RSI Overbought: {rsi:.2f}",
                    url="https://www.tradingview.com/symbols/BTCUSD/",
                    content=f"Bitcoin's RSI has reached {rsi:.2f}, which is in overbought territory. This may indicate a potential reversal or correction in the short term.",
                    published_date=datetime.now(),
                    source_name=f"{self.name} RSI Alert"
                )
                articles.append(rsi_article)
                logger.info(f"Created RSI overbought alert article")
            elif rsi < 30:
                rsi_article = Article(
                    title=f"Bitcoin RSI Oversold: {rsi:.2f}",
                    url="https://www.tradingview.com/symbols/BTCUSD/",
                    content=f"Bitcoin's RSI has reached {rsi:.2f}, which is in oversold territory. This may indicate a potential reversal or bounce in the short term.",
                    published_date=datetime.now(),
                    source_name=f"{self.name} RSI Alert"
                )
                articles.append(rsi_article)
                logger.info(f"Created RSI oversold alert article")
            
        except Exception as e:
            logger.error(f"Error creating technical analysis articles: {e}")
            
        return articles
    
    def _create_news_articles(self, news_data: List[Dict[str, Any]]) -> List[Article]:
        """Create articles from news data."""
        articles = []
        
        try:
            # Process each news item
            for item in news_data:
                # Extract fields
                title = item.get("title", "")
                
                # Skip if no title or not Bitcoin-related
                if not title or "bitcoin" not in title.lower() and "btc" not in title.lower():
                    continue
                    
                # Get the source URL
                url = item.get("url", "")
                if not url:
                    url = item.get("link", "")
                if not url:
                    # Fallback to TradingView's Bitcoin page if no URL
                    url = "https://www.tradingview.com/symbols/BTCUSD/news/"
                
                # Get the description
                content = item.get("description", "")
                if not content:
                    content = item.get("body", "")
                if not content:
                    content = title
                
                # Get the source name
                source = item.get("source", "TradingView")
                
                # Get the published date
                published_str = item.get("published", "")
                if published_str:
                    try:
                        published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        published_date = datetime.now()
                else:
                    published_date = datetime.now()
                
                # Create the article
                article = Article(
                    title=title,
                    url=url,
                    content=content,
                    published_date=published_date,
                    source_name=f"{source} via {self.name}"
                )
                
                articles.append(article)
                logger.info(f"Created news article: {title[:60]}...")
                
        except Exception as e:
            logger.error(f"Error creating news articles: {e}")
            
        return articles
    
    def extract_article_content(self, url: str) -> str:
        """
        Extract content from a TradingView article URL.
        
        Args:
            url: URL of the article
            
        Returns:
            Extracted content as a string
        """
        try:
            # For TradingView links, we've already extracted the content during fetching
            # If it's a news URL, we'd need to fetch it separately
            if "tradingview.com" in url:
                return "This content is already fully extracted. See the article details above."
                
            # For external news sources, we could implement a generic scraper here
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Use a simple extraction method for text
                # For production, you might want to use a library like newspaper3k
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove scripts, styles, etc.
                for script in soup(["script", "style", "header", "footer", "nav"]):
                    script.extract()
                
                # Get text
                text = soup.get_text(separator=' ', strip=True)
                
                # Clean up whitespace
                import re
                text = re.sub(r'\s+', ' ', text).strip()
                
                return text
            else:
                return f"Failed to fetch content: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error extracting content from URL {url}: {e}")
            return f"Failed to extract content: {str(e)}"
