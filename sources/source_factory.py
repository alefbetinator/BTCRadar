from typing import Dict, Type, List

from .base_source import NewsSource
from .bitcoinist import BitcoinistSource
from .cointelegraph import CointelegraphSource
from .cryptopanic import CryptoPanicSource
from .reddit_bitcoin import RedditBitcoinSource
from .google_search import GoogleSearchSource
from .bitcoin_magazine import BitcoinMagazineSource
from .bitcoin_news_rss import BitcoinNewsRSSSource
from .tradingview_selenium import TradingViewSource


class SourceFactory:
    """Factory for creating and managing news sources."""
    
    _sources: Dict[str, Type[NewsSource]] = {}
    
    @classmethod
    def register(cls, source_class: Type[NewsSource]) -> None:
        """
        Register a new news source class.
        
        Args:
            source_class: The class to register
        """
        source = source_class()
        cls._sources[source.name.lower()] = source_class
    
    @classmethod
    def get_source(cls, name: str) -> NewsSource:
        """
        Get an instance of a news source by name.
        
        Args:
            name: Name of the news source (case insensitive)
            
        Returns:
            Instance of the requested NewsSource
            
        Raises:
            ValueError: If source with given name is not found
        """
        source_class = cls._sources.get(name.lower())
        if not source_class:
            raise ValueError(f"Source not found: {name}")
        return source_class()
    
    @classmethod
    def get_all_sources(cls) -> List[NewsSource]:
        """
        Get instances of all registered news sources.
        
        Returns:
            List of NewsSource instances
        """
        return [source_class() for source_class in cls._sources.values()]
    
    @classmethod
    def get_available_source_names(cls) -> List[str]:
        """
        Get names of all available sources.
        
        Returns:
            List of source names
        """
        return [source().name for source in cls._sources.values()]


# Register available sources
SourceFactory.register(BitcoinistSource)
SourceFactory.register(CointelegraphSource)  # Added Cointelegraph as a news source
SourceFactory.register(CryptoPanicSource)    # Added CryptoPanic aggregator
SourceFactory.register(RedditBitcoinSource)  # Added Reddit Bitcoin forum
SourceFactory.register(GoogleSearchSource)
SourceFactory.register(BitcoinMagazineSource)
SourceFactory.register(BitcoinNewsRSSSource) # Added Bitcoin News RSS feeds
SourceFactory.register(TradingViewSource)    # Added TradingView Key Facts extraction

# In the future, add more sources here:
# SourceFactory.register(CoinDeskSource)
# etc.
