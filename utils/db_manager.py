import json
import os
import logging
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Simple database manager to track articles and analysis."""
    
    def __init__(self, db_file: str = "article_database.json"):
        """
        Initialize the database manager.
        
        Args:
            db_file: Path to the database file
        """
        # Ensure the path is absolute
        if not os.path.isabs(db_file):
            # Get the directory of this script
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_file = os.path.join(current_dir, db_file)
        
        self.db_file = db_file
        self.article_urls: Set[str] = set()
        self.opportunities: List[Dict[str, Any]] = []
        
        # Load existing data
        self._load_database()
    
    def _load_database(self) -> None:
        """Load the database from disk."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    
                self.article_urls = set(data.get('article_urls', []))
                self.opportunities = data.get('opportunities', [])
                
                logger.info(f"Loaded database with {len(self.article_urls)} known articles and "
                           f"{len(self.opportunities)} recorded opportunities")
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                # Start with empty data
                self.article_urls = set()
                self.opportunities = []
    
    def _save_database(self) -> None:
        """Save the database to disk."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            
            with open(self.db_file, 'w') as f:
                data = {
                    'article_urls': list(self.article_urls),
                    'opportunities': self.opportunities
                }
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved database with {len(self.article_urls)} articles and "
                       f"{len(self.opportunities)} opportunities")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def has_seen_article(self, url: str) -> bool:
        """
        Check if an article URL has been seen before.
        
        Args:
            url: Article URL to check
            
        Returns:
            Boolean indicating if the article has been seen
        """
        return url in self.article_urls
    
    def mark_article_as_seen(self, url: str) -> None:
        """
        Mark an article as seen.
        
        Args:
            url: Article URL to mark
        """
        self.article_urls.add(url)
        # Don't save after every article, let the caller save at the end of a batch
    
    def record_opportunity(self, article_info: Dict[str, Any], sentiment_info: Dict[str, Any]) -> None:
        """
        Record a detected opportunity.
        
        Args:
            article_info: Information about the article
            sentiment_info: Information about the market sentiment
        """
        # Create a simplified record
        opportunity = {
            'timestamp': datetime.now().isoformat(),
            'article_title': article_info['article'].title,
            'article_url': article_info['article'].url,
            'article_source': article_info['article'].source_name if hasattr(article_info['article'], 'source_name') else 'Unknown',
            'significance_score': article_info['significance_score'],
            'significance_factors': article_info['significance_factors'],
            'market_sentiment': sentiment_info['recommendation'],
            'is_sell_signal': sentiment_info['is_sell']
        }
        
        # Add AI analysis if available
        if 'ai_significance_score' in article_info:
            opportunity['ai_significance_score'] = article_info['ai_significance_score']
            opportunity['ai_analysis'] = article_info.get('ai_analysis', 'No AI analysis available')
            opportunity['is_under_radar'] = article_info.get('is_under_radar', False)
            opportunity['buy_signal'] = article_info.get('buy_signal', False)
        
        self.opportunities.append(opportunity)
        self._save_database()
    
    def clean_old_data(self, days: int = 30) -> None:
        """
        Remove data older than specified days.
        
        Args:
            days: Number of days to keep data for
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter opportunities by date
        try:
            filtered_opportunities = []
            for opp in self.opportunities:
                timestamp = datetime.fromisoformat(opp['timestamp'])
                if timestamp >= cutoff_date:
                    filtered_opportunities.append(opp)
            
            removed_count = len(self.opportunities) - len(filtered_opportunities)
            self.opportunities = filtered_opportunities
            
            if removed_count > 0:
                logger.info(f"Removed {removed_count} opportunities older than {days} days")
                self._save_database()
        except Exception as e:
            logger.error(f"Error cleaning old data: {e}")
    
    def get_recent_opportunities(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get opportunities detected within the specified number of hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent opportunities
        """
        recent_opportunities = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for opportunity in self.opportunities:
            try:
                timestamp = datetime.fromisoformat(opportunity['timestamp'])
                if timestamp >= cutoff_time:
                    recent_opportunities.append(opportunity)
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing opportunity timestamp: {e}")
                continue
        
        return recent_opportunities
