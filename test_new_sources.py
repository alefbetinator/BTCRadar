import os
import logging
import sys
from dotenv import load_dotenv

from sources.source_factory import SourceFactory
from sources.cryptopanic import CryptoPanicSource
from sources.reddit_bitcoin import RedditBitcoinSource
from sources.google_search import GoogleSearchSource
from sources.bitcoin_magazine import BitcoinMagazineSource
from analyzers.ai_analyzer import AIAnalyzer
from analyzers.content_analyzer import ContentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_cryptopanic():
    """Test fetching articles from CryptoPanic."""
    source = CryptoPanicSource()
    logger.info(f"Testing {source.name} source...")
    
    # Load environment variables for API keys
    load_dotenv()
    
    # Check if API key is available
    api_key = os.environ.get('CRYPTOPANIC_API_KEY')
    if not api_key:
        logger.error("CRYPTOPANIC_API_KEY not found in environment variables!")
        logger.info("Please add your CryptoPanic API key to .env file as CRYPTOPANIC_API_KEY=your_key_here")
        return
    
    # Fetch articles
    articles = source.fetch_articles(limit=5)
    
    # Display results
    logger.info(f"Found {len(articles)} articles from {source.name}")
    
    for i, article in enumerate(articles):
        logger.info(f"\nArticle {i+1}:")
        logger.info(f"Title: {article.title}")
        logger.info(f"URL: {article.url}")
        logger.info(f"Source: {article.source_name}")
        logger.info(f"Date: {article.published_date}")
        
        # Show a snippet of content
        content_preview = article.content[:150] + "..." if article.content else "No content"
        logger.info(f"Content preview: {content_preview}")

def test_reddit():
    """Test Reddit Bitcoin source"""
    source = RedditBitcoinSource()
    logger.info(f"\nTesting {source.name} source...")
    
    # Fetch articles
    articles = source.fetch_articles(limit=5)
    
    # Display results
    logger.info(f"Found {len(articles)} posts from {source.name}")
    
    for i, article in enumerate(articles):
        logger.info(f"\nPost {i+1}:")
        logger.info(f"Title: {article.title}")
        logger.info(f"URL: {article.url}")
        logger.info(f"Author: {article.source_name}")
        logger.info(f"Date: {article.published_date}")
        
        # Show a snippet of content
        content_preview = article.content[:150] + "..." if article.content else "No content"
        logger.info(f"Content preview: {content_preview}")

def test_google_search():
    """Test fetching articles from Google Search."""
    source = GoogleSearchSource()
    logger.info(f"Testing {source.name} source...")
    
    # Fetch articles
    articles = source.fetch_articles(limit=5)
    
    # Display results
    logger.info(f"Found {len(articles)} articles from {source.name}")
    
    for i, article in enumerate(articles):
        logger.info(f"\nArticle {i+1}:")
        logger.info(f"Title: {article.title}")
        logger.info(f"URL: {article.url}")
        logger.info(f"Source: {article.source_name}")
        logger.info(f"Date: {article.published_date}")
        
        # Show a snippet of content
        content_preview = article.content[:150] + "..." if article.content else "No content"
        logger.info(f"Content preview: {content_preview}")

def test_bitcoin_magazine():
    """Test fetching articles from Bitcoin Magazine."""
    source = BitcoinMagazineSource()
    logger.info(f"Testing {source.name} source...")
    
    # Fetch articles
    articles = source.fetch_articles(limit=5)
    
    # Display results
    logger.info(f"Found {len(articles)} articles from {source.name}")
    
    for i, article in enumerate(articles):
        logger.info(f"\nArticle {i+1}:")
        logger.info(f"Title: {article.title}")
        logger.info(f"URL: {article.url}")
        logger.info(f"Source: {article.source_name}")
        logger.info(f"Date: {article.published_date}")
        
        # Show a snippet of content
        content_preview = article.content[:150] + "..." if article.content else "No content"
        logger.info(f"Content preview: {content_preview}")

def test_integration():
    """Test integration with the main scanner by simulating article processing"""
    logger.info("\nTesting integration with main scanner...")
    
    # Initialize the analyzers
    ai_analyzer = AIAnalyzer()
    content_analyzer = ContentAnalyzer()
    
    # Get sources to test
    sources = [
        SourceFactory.get_source("CryptoPanic"),
        SourceFactory.get_source("Reddit Bitcoin"),
        SourceFactory.get_source("Google Search"),
        SourceFactory.get_source("Bitcoin Magazine")
    ]
    
    # Track source status
    results = {}
    
    # Test each source
    for source in sources:
        source_name = source.name
        logger.info(f"\nTesting integration with {source_name}...")
        
        try:
            # Fetch a limited number of articles
            articles = source.fetch_articles(limit=2)
            
            if not articles:
                logger.warning(f"No articles found from {source_name}")
                results[source_name] = "No articles found"
                continue
            
            # Check if we can process an article through the analyzers
            sample_article = articles[0]
            logger.info(f"Checking article: {sample_article.title}")
            
            # Check if article is Bitcoin-related using content analyzer
            try:
                is_bitcoin = content_analyzer.is_bitcoin_related(sample_article)
                logger.info(f"Content analysis result - Is Bitcoin related: {is_bitcoin}")
                
                # Get AI analysis if it's Bitcoin related
                if is_bitcoin:
                    analysis = ai_analyzer.analyze_article(sample_article)
                    score = analysis.get('ai_significance_score', 0)
                    logger.info(f"AI opportunity score: {score}")
                    logger.info(f"AI analysis: {analysis.get('ai_analysis', 'No analysis')[:100]}...")
                
                results[source_name] = "Working properly"
            except Exception as e:
                logger.error(f"Error during analysis: {e}")
                results[source_name] = f"Error during analysis: {str(e)}"
        
        except Exception as e:
            logger.error(f"Error testing {source_name}: {e}")
            results[source_name] = f"Error: {str(e)}"
    
    # Display final results
    logger.info("\nIntegration Test Results:")
    for source_name, status in results.items():
        logger.info(f"{source_name}: {status}")
    
    return all(status == "Working properly" for status in results.values())

if __name__ == "__main__":
    logger.info("Testing new news sources...")
    
    # Test CryptoPanic
    test_cryptopanic()
    
    # Test Reddit Bitcoin
    test_reddit()
    
    # Test Google Search
    test_google_search()
    
    # Test Bitcoin Magazine
    test_bitcoin_magazine()
    
    # Test integration
    test_integration()
    
    logger.info("\nTest completed!")
