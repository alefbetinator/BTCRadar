#!/usr/bin/env python3
"""
Test a single URL with the AI analyzer to see if it's considered "under the radar".
Usage: python test_single_url.py <url>
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)

logger = logging.getLogger(__name__)

# Make sure we can import from the project
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from analyzers.ai_analyzer import AIAnalyzer
from sources.base_source import Article
import requests
from bs4 import BeautifulSoup

def extract_reddit_content(url: str) -> Dict[str, Any]:
    """Extract content from a Reddit post URL."""
    try:
        # Convert URL to JSON API URL if it's a Reddit post
        if 'reddit.com/r/' in url and not url.endswith('.json'):
            url = f"{url}.json"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract post data
        post_data = data[0]['data']['children'][0]['data']
        
        title = post_data.get('title', '')
        selftext = post_data.get('selftext', '')
        content = selftext if selftext else post_data.get('url', '')
        
        # Get top comments if selftext is empty
        if not selftext and len(data) > 1:
            comments = []
            for comment in data[1]['data']['children'][:5]:  # Get top 5 comments
                if 'body' in comment.get('data', {}):
                    comments.append(comment['data']['body'])
            
            if comments:
                content = '\n\n'.join(comments)
        
        return {
            'title': title,
            'content': content,
            'permalink': post_data.get('permalink', ''),
            'score': post_data.get('score', 0),
            'upvote_ratio': post_data.get('upvote_ratio', 0),
            'author': post_data.get('author', ''),
            'created_utc': post_data.get('created_utc', 0)
        }
        
    except Exception as e:
        logger.error(f"Error extracting Reddit content: {e}")
        return {'title': '', 'content': ''}

def extract_generic_content(url: str) -> Dict[str, Any]:
    """Extract content from a generic URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.title.text.strip() if soup.title else ''
        
        # Extract content - focus on article and paragraph tags
        content_elements = soup.find_all(['article', 'p', 'div.content', 'div.article-content'])
        content = "\n".join([elem.get_text().strip() for elem in content_elements[:20]])
        
        return {
            'title': title,
            'content': content
        }
        
    except Exception as e:
        logger.error(f"Error extracting generic content: {e}")
        return {'title': '', 'content': ''}

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python test_single_url.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    logger.info(f"Testing URL: {url}")
    
    # Extract content based on the URL type
    if 'reddit.com' in url:
        data = extract_reddit_content(url)
        title = data['title']
        content = data['content']
    else:
        data = extract_generic_content(url)
        title = data['title']
        content = data['content']
    
    if not title or not content:
        logger.error("Failed to extract content from the URL")
        sys.exit(1)
    
    logger.info(f"Extracted title: {title}")
    logger.info(f"Content length: {len(content)} characters")
    
    # Create an Article object
    article = Article(
        title=title,
        url=url,
        content=content,
        published_date=datetime.now(),
        source_name="URL Test"
    )
    
    # Initialize AI analyzer
    ai_analyzer = AIAnalyzer()
    
    # Analyze the article
    result = ai_analyzer.analyze_article(article)
    
    # Display results
    print("\n===== AI ANALYSIS RESULTS =====")
    print(f"Title: {title}")
    print(f"URL: {url}")
    print(f"AI Significance Score: {result.get('ai_significance_score', 0.0)}")
    print(f"Is Under The Radar: {result.get('is_under_radar', False)}")
    print(f"Buy Signal: {result.get('buy_signal', False)}")
    print(f"AI Analysis: {result.get('ai_analysis', '')}")
    print("===============================")

if __name__ == "__main__":
    main()
