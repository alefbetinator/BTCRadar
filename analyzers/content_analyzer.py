import re
import logging
from typing import List, Dict, Any, Tuple

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from sources.base_source import Article

logger = logging.getLogger(__name__)

# Download required NLTK data (run this once)
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {e}")


class ContentAnalyzer:
    """Analyzes article content to identify potential significance."""
    
    # Keywords that might indicate insider information or rumors
    INSIDER_KEYWORDS = [
        'rumor', 'insider', 'source', 'leak', 'exclusive', 'plan',
        'developing', 'exclusive', 'reportedly', 'anonymous', 'confidential',
        'reveal', 'behind the scenes', 'according to sources'
    ]
    
    # Keywords related to bullish BTC developments
    BULLISH_KEYWORDS = [
        'adoption', 'institutional', 'mainstream', 'regulation', 'positive',
        'bullish', 'favorable', 'opportunity', 'support', 'backing',
        'endorsement', 'embrace', 'proposal', 'potential', 'innovation',
        'breakthrough', 'development', 'upgrade', 'approval'
    ]
    
    # Bitcoin-related keywords to check relevance
    BITCOIN_KEYWORDS = [
        'bitcoin', 'btc', 'crypto', 'cryptocurrency', 'cryptocurrencies', 
        'blockchain', 'digital currency', 'satoshi', 'nakamoto', 'halvening',
        'halving', 'mining', 'miner', 'hash rate', 'hashrate', 'difficulty adjustment',
        'digital gold', 'cold storage', 'wallet', 'ledger', 'trezor', 'exchange',
        'bitfinex', 'coinbase', 'binance', 'kraken', 'gemini', 'bybit',
        'lightning network', 'layer 2', 'segwit', 'taproot', 'ckpool'
    ]
    
    # Patterns for finding multiple sources in an article
    MULTIPLE_SOURCE_PATTERNS = [
        r'according to (\w+) sources',
        r'sources (?:from|at|within) (\w+)',
        r'(\w+) reported',
        r'report(?:s|ed) (?:from|by) (\w+)',
        r'citing (?:a|multiple) (?:source|sources)',
        r'sources (familiar|close) with'
    ]
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
    
    def analyze_article(self, article: Article) -> Dict[str, Any]:
        """
        Analyze article content to determine if it's potentially significant.
        
        Args:
            article: The Article object to analyze
            
        Returns:
            Dict containing analysis results
        """
        significance_score, factors = self._calculate_significance(article)
        
        return {
            'article': article,
            'significance_score': significance_score,
            'significance_factors': factors,
            'is_significant': significance_score >= 0.6,  # Threshold can be adjusted
            'multiple_sources_found': factors.get('has_multiple_sources', False),
            'insider_keywords_found': factors.get('insider_keywords', []),
            'bullish_keywords_found': factors.get('bullish_keywords', [])
        }
    
    def _calculate_significance(self, article: Article) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate a significance score for the article.
        
        Args:
            article: The Article object
            
        Returns:
            Tuple of (score, explanation_factors)
        """
        factors = {}
        score_components = []
        
        # Check for multiple sources mentioned
        sources_found = self._find_multiple_sources(article.content)
        factors['has_multiple_sources'] = len(sources_found) >= 2
        factors['sources_mentioned'] = sources_found
        
        if factors['has_multiple_sources']:
            score_components.append(0.4)  # Multiple sources is a strong signal
        
        # Check for insider keywords
        insider_keywords = self._find_matching_keywords(article.content, self.INSIDER_KEYWORDS)
        factors['insider_keywords'] = insider_keywords
        
        if insider_keywords:
            # Score increases with more unique insider keywords
            insider_score = min(0.3, 0.1 * len(set(insider_keywords)))
            score_components.append(insider_score)
        
        # Check for bullish keywords
        bullish_keywords = self._find_matching_keywords(article.content, self.BULLISH_KEYWORDS)
        factors['bullish_keywords'] = bullish_keywords
        
        if bullish_keywords:
            # Score increases with more unique bullish keywords
            bullish_score = min(0.3, 0.05 * len(set(bullish_keywords)))
            score_components.append(bullish_score)
        
        # Check for proximity of insider and bullish keywords
        if insider_keywords and bullish_keywords:
            score_components.append(0.2)  # Bonus for having both types of keywords
        
        # Calculate final score
        final_score = sum(score_components)
        
        # Cap the score at 1.0
        return min(1.0, final_score), factors
    
    def _find_multiple_sources(self, content: str) -> List[str]:
        """
        Find mentions of multiple sources in the content.
        
        Args:
            content: Article content
            
        Returns:
            List of source mentions found
        """
        sources = []
        
        # Check for specific patterns that indicate multiple sources
        for pattern in self.MULTIPLE_SOURCE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                sources.extend(matches)
                
        return sources
    
    def _find_matching_keywords(self, content: str, keyword_list: List[str]) -> List[str]:
        """
        Find keywords from the provided list in the content.
        
        Args:
            content: Article content
            keyword_list: List of keywords to check for
            
        Returns:
            List of found keywords
        """
        found_keywords = []
        content_lower = content.lower()
        
        for keyword in keyword_list:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)
                
        return found_keywords
    
    def is_bitcoin_related(self, article: Article) -> bool:
        """
        Check if an article is related to Bitcoin.
        
        Args:
            article: The Article object to check
            
        Returns:
            Boolean indicating if the article is Bitcoin-related
        """
        combined_text = (article.title + " " + article.content).lower()
        
        # Check for direct mention of Bitcoin keywords
        for keyword in self.BITCOIN_KEYWORDS:
            if keyword.lower() in combined_text:
                return True
                
        # Article is not Bitcoin-related
        return False
