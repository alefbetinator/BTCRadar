#!/usr/bin/env python3
"""
Bitcoin News Scanner

This script scans Bitcoin news sources for investment opportunities.

Usage:
    python main.py                  # Run continuously with scheduler
    python main.py --once           # Run once and exit
    python main.py --force-rescan   # Force rescan of already seen articles
    python main.py --show-recent    # Show opportunities detected in the last 24 hours

Note: All detailed logs are saved to bitcoin_scanner.log file
    while only essential information (opportunities found and AI calls)
    is displayed in the console.
"""

import argparse
import logging
import os
import sys
import time
from typing import Dict, List, Any
import datetime

import schedule
from bs4 import BeautifulSoup

import config
from analyzers.content_analyzer import ContentAnalyzer
from analyzers.sentiment_checker import SentimentChecker
from analyzers.ai_analyzer import AIAnalyzer
from sources.source_factory import SourceFactory
from utils.db_manager import DatabaseManager
from utils.notifier import Notifier

# Configure logging
# File handler for detailed logs
file_handler = logging.FileHandler("bitcoin_scanner.log")
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
file_handler.setFormatter(file_format)

# Console handler for minimal output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(message)s')
console_handler.setFormatter(console_format)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

# Create a special logger for console-only messages
# This will be used to show only what matters: opportunities and AI calls
console_logger = logging.getLogger("console")
for handler in console_logger.handlers:
    console_logger.removeHandler(handler)
console_logger.addHandler(console_handler)
console_logger.propagate = False  # Don't send to root logger

logger = logging.getLogger(__name__)


class BitcoinNewsScanner:
    """Main application class that coordinates the scanning and analysis process."""
    
    def __init__(self):
        """Initialize the Bitcoin news scanner."""
        logger.info("Initializing Bitcoin News Scanner...")
        
        # Initialize components
        self.content_analyzer = ContentAnalyzer()
        self.sentiment_checker = SentimentChecker()
        self.ai_analyzer = AIAnalyzer()
        self.notifier = Notifier()
        self.db_manager = DatabaseManager(config.DB_FILE)
        
        # Track the currently active sources
        self.active_sources = config.ACTIVE_SOURCES
        logger.info(f"Active sources: {', '.join(self.active_sources)}")
        
        # For console output
        self.console_logger = logging.getLogger("console")
    
    def scan_for_opportunities(self, once=False, force_rescan=False) -> List[Dict[str, Any]]:
        """
        Scan for Bitcoin news opportunities and identify significant articles.
        
        Args:
            once: If True, scan once and exit
            force_rescan: If True, ignore already processed articles
            
        Returns:
            List of opportunity dictionaries
        """
        logger.info("Starting scan for Bitcoin news opportunities...")
        
        # Store force_rescan flag for later use
        self._force_rescan = force_rescan
        
        # Get current TV data
        sentiment_info = self.sentiment_checker.get_current_sentiment()
        logger.info(f"Current TradingView sentiment: {sentiment_info.get('recommendation', 'Unknown')}")
        
        simplified_output = os.environ.get('SIMPLIFIED_OUTPUT', 'false').lower() == 'true'
        
        # Initialize empty lists for results
        opportunities = []
        significant_articles = []
        all_opportunity_urls = []  # Track all URLs for summary
        
        for source_name in self.active_sources:
            try:
                # Get source instance
                source = SourceFactory.get_source(source_name)
                logger.info(f"Fetching articles from {source_name}...")
                
                # Add clear console output showing which source is being checked
                source_emoji = "📰"
                if source_name == "Reddit Bitcoin":
                    source_emoji = "🔴"
                elif source_name == "CryptoPanic":
                    source_emoji = "📊"
                elif source_name == "Bitcoin Magazine":
                    source_emoji = "🔶"
                elif source_name == "Google Search":
                    source_emoji = "🔍"
                elif source_name == "Bitcoin News RSS":
                    source_emoji = "📡"
                elif source_name == "TradingView":
                    source_emoji = "📈"
                
                self.console_logger.info(f"\n{source_emoji} Checking {source_name}...")
                
                # Fetch articles from this source
                articles = source.fetch_articles(limit=config.ARTICLE_LIMIT_PER_SOURCE)
                logger.info(f"Fetched {len(articles)} articles from {source_name}")
                
                if len(articles) > 0:
                    self.console_logger.info(f"Found {len(articles)} articles from {source_name}")
                else:
                    self.console_logger.info(f"No articles found from {source_name}")
                
                # Process each article
                for article in articles:
                    # Only force process for NEW TradingView articles
                    # This ensures AI analysis while allowing duplicate detection
                    force_process = False
                    
                    # Skip if already processed (unless forced)
                    if not self._force_rescan and not force_process and self.db_manager.has_seen_article(article.url):
                        continue
                    
                    # Mark as processed
                    self.db_manager.mark_article_as_seen(article.url)
                    
                    # Analyze article for significance and opportunities
                    analysis_result = self._process_article(article, sentiment_info)
                    
                    if analysis_result['is_opportunity']:
                        opportunities.append(analysis_result['opportunity_data'])
                        
                        if simplified_output:
                            logger.info(f"OPPORTUNITY: {article.url}")
                        
                        # Add to URL list for summary
                        article_url = article.url
                        all_opportunity_urls.append(article_url)
                        
                        # Console output for opportunity
                        self.console_logger.info(f"🔔 OPPORTUNITY FOUND: {article.title}")
                        self.console_logger.info(f"🔗 URL: {article_url}")
                    
                    if analysis_result['is_significant'] or analysis_result['is_under_radar']:
                        if not simplified_output:
                            logger.info(f"Found significant article: {article.title}")
                        significant_articles.append(analysis_result)
                
                # Save database after processing all articles from this source
                self.db_manager._save_database()
                        
            except Exception as e:
                logger.error(f"Error processing source {source_name}: {e}")
        
        # Process notifications
        if opportunities:
            self._notify_opportunities(opportunities, sentiment_info)
        
        # Log results
        if not simplified_output:
            # Get all opportunities including previously found ones
            recent_opportunities = self.db_manager.get_recent_opportunities(24)
            all_opportunities = recent_opportunities if not opportunities else opportunities
            
            if all_opportunities:
                if opportunities:
                    logger.info(f"Scan completed. Found {len(opportunities)} new opportunities:")
                else:
                    logger.info(f"Scan completed. No new opportunities found. {len(all_opportunities)} previous opportunities in database:")
                
                for i, opp in enumerate(all_opportunities, 1):
                    # Handle both formats: direct opportunity objects and stored DB opportunities
                    if 'article_info' in opp:
                        # This is a newly detected opportunity with full structure
                        article_info = opp.get('article_info', {})
                        article = article_info.get('article', {})
                        
                        if hasattr(article, 'title'):
                            title = article.title
                            url = article.url
                        else:
                            title = article.get('title', 'Unknown article')
                            url = article.get('url', 'No URL available')
                        
                        is_under_radar = article_info.get('is_under_radar', False)
                        buy_signal = article_info.get('buy_signal', False)
                        ai_analysis = article_info.get('ai_analysis', 'No AI analysis available')
                        
                        # List factors that contributed to this being marked as an opportunity
                        factors = []
                        if article_info.get('insider_keywords_found'):
                            factors.append(f"Insider keywords: {', '.join(article_info['insider_keywords_found'][:3])}")
                        if article_info.get('bullish_keywords_found'):
                            factors.append("Bullish signals detected")
                        if is_under_radar:
                            factors.append("Under the radar")
                        if buy_signal:
                            factors.append("AI buy signal")
                    else:
                        # This is a stored opportunity from the database
                        title = opp.get('article_title', 'Unknown article')
                        url = opp.get('article_url', 'No URL available')
                        is_under_radar = opp.get('is_under_radar', False)
                        buy_signal = opp.get('buy_signal', False)
                        ai_analysis = opp.get('ai_analysis', 'No AI analysis available')
                        
                        # List factors
                        factors = []
                        sig_factors = opp.get('significance_factors', {})
                        if 'insider_keywords' in sig_factors and sig_factors['insider_keywords']:
                            factors.append(f"Insider keywords: {', '.join(sig_factors['insider_keywords'][:3])}")
                        if 'bullish_keywords' in sig_factors and sig_factors['bullish_keywords']:
                            factors.append("Bullish signals detected")
                        if is_under_radar:
                            factors.append("Under the radar")
                        if buy_signal:
                            factors.append("AI buy signal")
                    
                    # Display the opportunity information
                    logger.info(f"{i}. {title}")
                    logger.info(f"   URL: {url}")
                    
                    if factors:
                        logger.info(f"   Factors: {' | '.join(factors)}")
                    
                    # Include AI analysis
                    logger.info(f"   AI Analysis: {ai_analysis}")
                    
                    # Show under the radar and buy signal status
                    logger.info(f"   Under radar: {is_under_radar}, Buy signal: {buy_signal}")
                    
                    logger.info("   --------------------------------------------------------------------------------")
            else:
                logger.info("Scan completed. No opportunities found.")
        
        # Console summary
        if opportunities:
            self.console_logger.info(f"\n===== SCAN SUMMARY: {len(opportunities)} new opportunities found =====")
            # Show the new opportunities
            for i, opp in enumerate(opportunities, 1):
                article_info = opp.get('article_info', {})
                article = article_info.get('article', {})
                
                if hasattr(article, 'title'):
                    title = article.title
                    url = article.url
                else:
                    title = article.get('title', 'Unknown article')
                    url = article.get('url', 'No URL available')
                
                self.console_logger.info(f"{i}. {title}")
                self.console_logger.info(f"   URL: {url}")
        
        # Always show the recent opportunities (whether or not new ones were found)
        previous_opps = self.db_manager.get_recent_opportunities(24)
        # Sort by timestamp, newest first
        previous_opps.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        if previous_opps and (not opportunities or len(previous_opps) > len(opportunities)):
            self.console_logger.info(f"\n===== RECENT OPPORTUNITIES (last 24 hours) =====")
            # Show all recent opportunities
            for i, opp in enumerate(previous_opps, 1):
                title = opp.get('article_title', 'Unknown article')
                url = opp.get('article_url', 'No URL available')
                
                # Format timestamp
                timestamp = opp.get('timestamp', '')
                found_time = ''
                if timestamp:
                    try:
                        found_time = datetime.datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                # Check if this opportunity was already shown in the new opportunities list
                already_shown = False
                for new_opp in opportunities:
                    article_info = new_opp.get('article_info', {})
                    article = article_info.get('article', {})
                    if hasattr(article, 'title') and article.title == title and article.url == url:
                        already_shown = True
                        break
                
                # Only show if not already shown in the new opportunities list
                if not already_shown:
                    if found_time:
                        self.console_logger.info(f"{i}. [{found_time}] {title}")
                    else:
                        self.console_logger.info(f"{i}. {title}")
                    self.console_logger.info(f"   URL: {url}")
        
        # Save the database after the complete scan
        self.db_manager._save_database()
        
        # Exit if in once mode
        if once:
            logger.info("Single scan mode - exiting.")
            if not simplified_output:
                sys.exit(0)
        
        return opportunities
    
    def _process_article(self, article, sentiment_info):
        # Analyze article content with the regular analyzer
        analysis_result = self.content_analyzer.analyze_article(article)
        
        # First check if the article is Bitcoin-related
        is_bitcoin_related = self.content_analyzer.is_bitcoin_related(article)
        
        # Always consider TradingView articles as Bitcoin-related
        if 'TradingView' in article.source_name:
            is_bitcoin_related = True
            if not analysis_result.get('is_bitcoin_related', False):
                self.console_logger.info(f"🔄 Marking TradingView article as Bitcoin-related: '{article.title}'")
                analysis_result['is_bitcoin_related'] = True
                
            # Add extra debugging for TradingView articles
            self.console_logger.info(f"📊 DEBUG: TradingView article: '{article.title}' | Source: {article.source_name}")
            self.console_logger.info(f"📊 Content preview: '{article.content[:100].strip()}...'")
        
        if is_bitcoin_related:
            # Only use AI analyzer for Bitcoin-related articles
            ai_result = self.ai_analyzer.analyze_article(article)
            
            # Add AI analysis to the results
            analysis_result['ai_significance_score'] = ai_result.get('ai_significance_score', 0.0)
            analysis_result['ai_analysis'] = ai_result.get('ai_analysis', '')
            analysis_result['is_under_radar'] = ai_result.get('is_under_radar', False)
            analysis_result['buy_signal'] = ai_result.get('buy_signal', False)
        else:
            # Skip AI analysis for non-Bitcoin articles
            self.console_logger.info(f"⛔ SKIPPING AI ANALYSIS: '{article.title}' (not Bitcoin-related)")
            analysis_result['ai_significance_score'] = 0.0
            analysis_result['ai_analysis'] = 'Not Bitcoin-related, AI analysis skipped'
            analysis_result['is_under_radar'] = False
            analysis_result['buy_signal'] = False
        
        # Identify if this is an opportunity
        is_opportunity = self._identify_opportunity(analysis_result, sentiment_info)
        
        # If it's an opportunity, record it and structure it properly for display
        if is_opportunity:
            # Record the opportunity in the database
            # Only record if it's not in the force_rescan mode (to avoid duplicates)
            if not self._force_rescan:
                self.db_manager.record_opportunity(analysis_result, sentiment_info)
            
            # Create a well-structured opportunity object
            opportunity = {
                'article_info': {
                    'article': article,
                    'is_significant': analysis_result['is_significant'],
                    'significance_score': analysis_result['significance_score'],
                    'ai_significance_score': analysis_result['ai_significance_score'],
                    'ai_analysis': analysis_result['ai_analysis'],
                    'is_under_radar': analysis_result['is_under_radar'],
                    'buy_signal': analysis_result['buy_signal'],
                    'insider_keywords_found': analysis_result.get('significance_factors', {}).get('insider_keywords', []),
                    'bullish_keywords_found': analysis_result.get('significance_factors', {}).get('bullish_keywords', [])
                },
                'sentiment_info': sentiment_info
            }
            analysis_result['opportunity_data'] = opportunity
            
        analysis_result['is_opportunity'] = is_opportunity
        return analysis_result
    
    def _identify_opportunity(self, article_info, sentiment_info):
        is_opportunity = False
        
        # Modified logic: only consider AI-based signals or require BOTH traditional AND AI signals
        
        # Check AI-based opportunity criteria first
        if config.USE_AI_ANALYSIS:
            # If AI detected this as under the radar with a buy signal
            if article_info.get('is_under_radar', False) and article_info.get('buy_signal', False):
                is_opportunity = True
        
        # Only check traditional criteria if AI didn't already flag this and if traditional analysis is enabled
        if not is_opportunity and article_info.get('is_significant', False) and config.USE_TRADITIONAL_ANALYSIS:
            # We also want a sell signal unless that requirement is disabled
            if not config.REQUIRE_SELL_SIGNAL or sentiment_info.get('is_sell', False):
                is_opportunity = True
        
        return is_opportunity
    
    def _notify_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        sentiment_info: Dict[str, Any] = None
    ) -> None:
        """
        Send notifications for detected opportunities.
        
        Args:
            opportunities: List of opportunities to notify about
            sentiment_info: Current market sentiment information
        """
        for opportunity in opportunities:
            article_info = opportunity.get('article_info', {})
            article = article_info.get('article', {})
            
            # Extract title from either a dict or Article object
            if hasattr(article, 'title'):
                title = article.title
                url = article.url
            else:
                title = article.get('title', 'Unknown article')
                url = article.get('url', 'No URL available')
            
            # Build a list of factors that make this an opportunity
            factors = []
            
            if article_info.get('insider_keywords_found'):
                factors.append(f"Insider keywords: {', '.join(article_info['insider_keywords_found'][:3])}")
            if article_info.get('bullish_keywords_found'):
                factors.append("Bullish signals detected")
            if article_info.get('is_under_radar'):
                factors.append("Under the radar")
            if article_info.get('buy_signal'):
                factors.append("AI buy signal")
            
            factors_text = " | ".join(factors)
            if sentiment_info:
                sentiment_text = f"TradingView: {sentiment_info.get('recommendation', 'Unknown')}"
            else:
                sentiment_text = "TradingView: Unknown"
            
            message = f"{factors_text}\n{sentiment_text}"
            
            # Send notifications including the opportunity data for email
            self.notifier.send_notification(title, message, url, opportunity=opportunity)
            
            logger.info(f"Opportunity: {title}")
            logger.info(f"Factors: {factors_text}")
            
            # If there's AI analysis, include it
            if article_info.get('ai_analysis'):
                logger.info(f"AI Analysis: {article_info.get('ai_analysis')}")
            
            # Log URL for easy access
            if hasattr(article, 'url'):
                url = article.url
            else:
                url = article.get('url', 'Unknown URL')
            logger.info(f"URL: {url}")
            logger.info("-" * 80)


if __name__ == "__main__":
    import argparse
    import datetime
    
    parser = argparse.ArgumentParser(description="Bitcoin News Scanner")
    parser.add_argument(
        "--once", 
        action="store_true", 
        help="Run one scan and exit (don't start scheduler)"
    )
    parser.add_argument(
        "--force-rescan", 
        action="store_true", 
        help="Force rescan of already seen articles"
    )
    parser.add_argument(
        "--show-recent",
        action="store_true",
        help="Show opportunities detected in the last 24 hours"
    )
    args = parser.parse_args()
    
    scanner = BitcoinNewsScanner()
    
    if args.show_recent:
        recent_opportunities = scanner.db_manager.get_recent_opportunities(hours=24)
        
        if not recent_opportunities:
            print("\n===== No opportunities detected in the last 24 hours =====\n")
        else:
            # Group opportunities by article URL to avoid duplicates
            # Keep only the most recent entry for each article
            unique_opportunities = {}
            for opportunity in recent_opportunities:
                article_url = opportunity['article_url']
                if article_url not in unique_opportunities:
                    unique_opportunities[article_url] = opportunity
                else:
                    # If we have a newer entry for this article, replace it
                    existing_timestamp = datetime.datetime.fromisoformat(unique_opportunities[article_url]['timestamp'])
                    new_timestamp = datetime.datetime.fromisoformat(opportunity['timestamp'])
                    if new_timestamp > existing_timestamp:
                        unique_opportunities[article_url] = opportunity
            
            # Convert back to a list and sort prioritizing:
            # 1. Articles with AI buy signals first
            # 2. Then by timestamp (newest first)
            sorted_opportunities = sorted(
                unique_opportunities.values(),
                key=lambda x: (
                    not x.get('buy_signal', False),  # Sort buy signals first
                    -datetime.datetime.fromisoformat(x['timestamp']).timestamp()  # Then by timestamp (newest first)
                )
            )
            
            print(f"\n===== {len(sorted_opportunities)} unique opportunities detected in the last 24 hours =====\n")
            
            for i, opportunity in enumerate(sorted_opportunities, 1):
                timestamp = opportunity.get('timestamp', '')
                if timestamp:
                    try:
                        timestamp_obj = datetime.datetime.fromisoformat(timestamp)
                        formatted_time = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        formatted_time = timestamp
                else:
                    formatted_time = "Unknown time"
                
                print(f"#{i}: {opportunity['article_title']} ({formatted_time})")
                print(f"URL: {opportunity['article_url']}")
                
                # Print significance factors
                factors = []
                try:
                    if 'significance_factors' in opportunity:
                        sig_factors = opportunity['significance_factors']
                        if 'insider_keywords' in sig_factors and sig_factors['insider_keywords']:
                            factors.append(f"Insider keywords: {', '.join(sig_factors['insider_keywords'][:3])}")
                        if 'bullish_keywords' in sig_factors and sig_factors['bullish_keywords']:
                            factors.append("Bullish signals detected")
                except Exception:
                    pass
                
                # Add AI analysis if available
                if opportunity.get('is_under_radar', False):
                    factors.append("Under the radar")
                
                if opportunity.get('buy_signal', False):
                    factors.append("AI buy signal")
                
                if factors:
                    print(f"Factors: {' | '.join(factors)}")
                
                # Print sentiment
                print(f"Market sentiment: {opportunity.get('market_sentiment', 'Unknown')}")
                
                # Print AI analysis if available
                if opportunity.get('ai_analysis'):
                    print(f"AI analysis: {opportunity.get('ai_analysis')}")
                
                print("-" * 80)
            
            print()
    
    if args.once:
        scanner.scan_for_opportunities(once=True, force_rescan=args.force_rescan)
    else:
        if args.force_rescan:
            scanner._force_rescan = True
            schedule.every(config.SCAN_INTERVAL).minutes.do(
                lambda: scanner.scan_for_opportunities(force_rescan=True)
            )
        else:
            schedule.every(config.SCAN_INTERVAL).minutes.do(scanner.scan_for_opportunities)
        
        # Run initial scan immediately
        scanner.scan_for_opportunities(force_rescan=args.force_rescan)
        
        # Run the scheduler
        print(f"Bitcoin News Scanner is running. Checking every {config.SCAN_INTERVAL} minutes.")
        print("Press Ctrl+C to exit.")
        
        try:
            last_scan_time = time.time()
            last_digest_check_time = time.time()
            
            while True:
                current_time = time.time()
                
                # Check if it's time for a new scan
                elapsed_time = current_time - last_scan_time
                next_scan_in = (config.SCAN_INTERVAL * 60) - elapsed_time
                
                if next_scan_in <= 0:
                    # Time for a new scan
                    schedule.run_pending()
                    last_scan_time = time.time()  # Reset the timer after executing the scan
                
                # Check for pending digest emails every minute
                digest_elapsed_time = current_time - last_digest_check_time
                if digest_elapsed_time >= 60:  # Check every minute
                    scanner.notifier.check_pending_digest()
                    last_digest_check_time = time.time()
                
                # Update countdown every second
                print(f"\rNext scan in: {int(next_scan_in)} seconds", end="", flush=True)
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down Bitcoin News Scanner...")
