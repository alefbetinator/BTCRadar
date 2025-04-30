import platform
import logging
import webbrowser
from typing import Optional, Dict, Any
from datetime import datetime

from plyer import notification

from utils.email_notifier import EmailNotifier
import config

logger = logging.getLogger(__name__)


class Notifier:
    """Handles desktop notifications and email notifications for significant news."""
    
    def __init__(self):
        self.platform = platform.system()
        self.app_name = "BTC News Scanner"
        
        # Initialize email notifier
        self.email_notifier = EmailNotifier()
    
    def send_notification(self, title: str, message: str, url: Optional[str] = None, 
                          opportunity: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a desktop notification and optionally open the URL on click.
        Also send email notification if configured.
        
        Args:
            title: Notification title
            message: Notification message
            url: Optional URL to open when notification is clicked
            opportunity: Optional opportunity data dictionary for email notifications
            
        Returns:
            Boolean indicating success
        """
        try:
            # Store the URL globally so it can be accessed when notification is clicked
            if url:
                # In a real app, we'd use a better mechanism for this
                global _last_notification_url
                _last_notification_url = url
            
            # Send desktop notification
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=10,  # Display for 10 seconds
                ticker="BTC News Opportunity Detected",
                toast=(self.platform == "Windows")
            )
            
            logger.info(f"Sent notification: {title} - {message}")
            
            # Open URL in browser immediately for this prototype
            # In a full app, we'd use a proper callback
            if url:
                self._open_url(url)
            
            # Send email notification if configured and opportunity data is provided
            if opportunity and self.email_notifier.enabled:
                # Format the opportunity data for email
                formatted_opportunity = self._format_opportunity_for_email(opportunity)
                self.email_notifier.send_opportunity_notification(formatted_opportunity)
                logger.info(f"Email notification queued for: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            
            # Fallback: just log to console if notification fails
            print(f"\n{'='*60}")
            print(f"ALERT: {title}")
            print(f"{message}")
            if url:
                print(f"URL: {url}")
            print(f"{'='*60}\n")
            
            # Still try to open the URL if provided
            if url:
                self._open_url(url)
            
            # Try to send email even if desktop notification failed
            if opportunity and self.email_notifier.enabled:
                try:
                    formatted_opportunity = self._format_opportunity_for_email(opportunity)
                    self.email_notifier.send_opportunity_notification(formatted_opportunity)
                    logger.info(f"Email notification queued for: {title}")
                except Exception as email_err:
                    logger.error(f"Error sending email notification: {email_err}")
            
            return False
    
    def _open_url(self, url: str) -> None:
        """
        Open a URL in the default browser.
        
        Args:
            url: URL to open
        """
        try:
            webbrowser.open(url)
            logger.info(f"Opened URL in browser: {url}")
        except Exception as e:
            logger.error(f"Error opening URL: {e}")
    
    def _format_opportunity_for_email(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format opportunity data for email notifications.
        
        Args:
            opportunity: Raw opportunity data
            
        Returns:
            Formatted opportunity data for email
        """
        article_info = opportunity.get('article_info', {})
        article = article_info.get('article', {})
        sentiment_info = opportunity.get('sentiment_info', {})
        
        # Get article title and URL
        if hasattr(article, 'title'):
            title = article.title
            url = article.url
            source = getattr(article, 'source', 'Unknown Source')
        else:
            title = article.get('title', 'Unknown article')
            url = article.get('url', 'No URL available')
            source = article.get('source', 'Unknown Source')
        
        # Format the timestamp
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare significance scores
        ai_score = article_info.get('ai_significance_score', 0)
        trad_score = article_info.get('significance_score', 0)
        
        # Prepare AI analysis
        ai_analysis = article_info.get('ai_analysis', 'No AI analysis available')
        
        # Format the opportunity for email
        formatted_opportunity = {
            'article_title': title,
            'article_url': url,
            'article_source': source,
            'formatted_time': formatted_time,
            'ai_score': ai_score,
            'traditional_score': trad_score,
            'ai_analysis': ai_analysis,
            'is_under_radar': article_info.get('is_under_radar', False),
            'buy_signal': article_info.get('buy_signal', False),
            'trading_view_sentiment': sentiment_info.get('recommendation', 'Unknown')
        }
        
        return formatted_opportunity
    
    def check_pending_digest(self) -> None:
        """
        Check if any pending digest emails need to be sent.
        This should be called regularly by the scheduler.
        """
        if self.email_notifier.enabled:
            self.email_notifier.send_digest_if_needed()


# Global variable to store the last notification URL
# This is a simplified approach; in a production app,
# you'd use a proper callback mechanism
_last_notification_url = None


def on_notification_click():
    """Handle notification click event."""
    global _last_notification_url
    if _last_notification_url:
        webbrowser.open(_last_notification_url)
        _last_notification_url = None
