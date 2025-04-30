#!/usr/bin/env python
import sys
import logging
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import argparse

from sources.base_source import Article
from analyzers.ai_analyzer import AIAnalyzer
from analyzers.content_analyzer import ContentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def fetch_article_content(url):
    """Fetch and parse content from a URL."""
    logger.info(f"Fetching content from: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to get the title from the page
        title = soup.title.string if soup.title else "Unknown Title"
        
        # Extract the text content
        # Remove scripts, styles, and other non-content elements
        for script in soup(["script", "style", "aside", "nav", "footer", "header"]):
            script.extract()
        
        # Get the text content
        content = soup.get_text(separator=' ', strip=True)
        
        # Create an Article object
        article = Article(
            title=title,
            url=url,
            content=content,
            source_name="Manual URL Test",
            published_date=None
        )
        
        return article
    
    except Exception as e:
        logger.error(f"Error fetching URL: {e}")
        raise

def analyze_single_url(url):
    """Analyze a single URL for under-the-radar opportunities."""
    # Load environment variables
    load_dotenv()
    
    # Check OpenAI API key
    api_key = os.environ.get('OPENAI_API_KEY')
    use_real_ai = os.environ.get('USE_REAL_AI', 'false').lower() == 'true'
    
    if use_real_ai and not api_key:
        logger.error("OpenAI API key is required for real AI analysis. Set OPENAI_API_KEY in your .env file.")
        return
    
    try:
        # Fetch the article content
        article = fetch_article_content(url)
        
        logger.info(f"Successfully fetched article: {article.title}")
        
        # Initialize analyzers
        ai_analyzer = AIAnalyzer()
        content_analyzer = ContentAnalyzer()
        
        # Check if the article is Bitcoin-related
        is_bitcoin = content_analyzer.is_bitcoin_related(article)
        logger.info(f"Is Bitcoin related: {is_bitcoin}")
        
        if not is_bitcoin:
            logger.warning("This article does not appear to be Bitcoin-related. Analysis may not be accurate.")
        
        # Perform AI analysis
        analysis_result = ai_analyzer.analyze_article(article)
        
        # Display the results
        print("\n===== ANALYSIS RESULTS =====")
        print(f"Title: {article.title}")
        print(f"URL: {url}")
        print(f"GPT Model: {ai_analyzer.gpt_model}")
        print(f"Under the radar: {analysis_result['is_under_radar']}")
        print(f"Buy signal: {analysis_result['buy_signal']}")
        print(f"Significance score: {analysis_result['ai_significance_score']:.2f}")
        print(f"Confidence: {analysis_result['confidence']:.2f}")
        print("\nAnalysis:")
        print(analysis_result['ai_analysis'])
        print("============================\n")
        
        # Determine if it would be considered an opportunity
        is_opportunity = analysis_result['is_under_radar'] and analysis_result['buy_signal']
        if is_opportunity:
            print("✅ This article WOULD be considered an investment opportunity by the scanner.")
        else:
            print("❌ This article would NOT be considered an investment opportunity by the scanner.")
            if not analysis_result['is_under_radar']:
                print("   - Not considered 'under the radar'")
            if not analysis_result['buy_signal']:
                print("   - Not considered a 'buy signal'")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing URL: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test a single URL against the Bitcoin News Scanner AI analysis')
    parser.add_argument('url', help='URL to analyze')
    args = parser.parse_args()
    
    analyze_single_url(args.url)
