#!/usr/bin/env python3
"""
Test script to validate the Bitcoin-related article detection.
"""
import sys
import logging
from datetime import datetime
from sources.base_source import Article
from analyzers.content_analyzer import ContentAnalyzer

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_bitcoin_detection():
    """Test if the Bitcoin detection logic correctly identifies articles."""
    analyzer = ContentAnalyzer()
    current_time = datetime.now()
    
    # Test cases - should be identified as Bitcoin-related
    bitcoin_articles = [
        Article(title="Bitcoin Price Analysis: BTC May Surge to $100K", 
                url="https://example.com/bitcoin-analysis", 
                content="Bitcoin price is expected to increase due to the halving.",
                published_date=current_time,
                source_name="Test Source"),
        Article(title="El Salvador Adds More BTC to Treasury", 
                url="https://example.com/el-salvador-btc", 
                content="The country purchased another 100 coins.",
                published_date=current_time,
                source_name="Test Source"),
        Article(title="New Crypto Regulations Impact Market", 
                url="https://example.com/crypto-regulations", 
                content="The regulations affect multiple cryptocurrencies including Bitcoin.",
                published_date=current_time,
                source_name="Test Source"),
    ]
    
    # Test cases - should NOT be identified as Bitcoin-related
    non_bitcoin_articles = [
        Article(title="Stock Market Analysis: S&P 500 Recovery", 
                url="https://example.com/stock-analysis", 
                content="The stock market is showing signs of recovery after recent dips.",
                published_date=current_time,
                source_name="Test Source"),
        Article(title="Tech Company Launches New AI Product", 
                url="https://example.com/tech-ai-launch", 
                content="The artificial intelligence solution is aimed at enterprise customers.",
                published_date=current_time,
                source_name="Test Source"),
        Article(title="Gold Price Surges Amid Economic Uncertainty", 
                url="https://example.com/gold-price", 
                content="Precious metal trading at all-time highs as investors seek safe havens.",
                published_date=current_time,
                source_name="Test Source"),
    ]
    
    # Test Bitcoin articles
    logger.info("Testing Bitcoin-related articles:")
    for article in bitcoin_articles:
        result = analyzer.is_bitcoin_related(article)
        logger.info(f"Article: '{article.title}' - Bitcoin-related: {result}")
        if not result:
            logger.error(f"ERROR: Failed to identify a Bitcoin article: {article.title}")
    
    logger.info("\nTesting non-Bitcoin articles:")
    for article in non_bitcoin_articles:
        result = analyzer.is_bitcoin_related(article)
        logger.info(f"Article: '{article.title}' - Bitcoin-related: {result}")
        if result:
            logger.error(f"ERROR: Incorrectly identified as Bitcoin article: {article.title}")

if __name__ == "__main__":
    try:
        test_bitcoin_detection()
        logger.info("\nTests completed successfully!")
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        sys.exit(1)
