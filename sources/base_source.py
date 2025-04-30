from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Article:
    """Data class representing a news article."""
    title: str
    url: str
    content: str
    published_date: datetime
    source_name: str
    keywords: List[str] = None
    summary: Optional[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class NewsSource(ABC):
    """Abstract base class for all news sources."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the news source."""
        pass
    
    @abstractmethod
    def fetch_articles(self, limit: int = 10) -> List[Article]:
        """
        Fetch articles from the news source.
        
        Args:
            limit: Maximum number of articles to fetch
            
        Returns:
            List of Article objects
        """
        pass
    
    @abstractmethod
    def extract_article_content(self, url: str) -> str:
        """
        Extract the full content of an article from its URL.
        
        Args:
            url: URL of the article
            
        Returns:
            String containing the full article text
        """
        pass
