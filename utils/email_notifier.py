"""
Email notification service for Bitcoin News Scanner.
Sends email notifications about new investment opportunities.
"""

import os
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Handles email notifications for new investment opportunities.
    """
    
    def __init__(self, email_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the email notifier.
        
        Args:
            email_config: Optional configuration for email.
                          If not provided, will load from environment variables.
        """
        self.enabled = False
        
        # Load config
        if email_config is None:
            self.enabled = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
            self.sender_email = os.environ.get('EMAIL_SENDER', '')
            self.sender_password = os.environ.get('EMAIL_PASSWORD', '')
            recipients = os.environ.get('EMAIL_RECIPIENTS', '')
            self.recipient_list = [r.strip() for r in recipients.split(',') if r.strip()]
            self.frequency = os.environ.get('EMAIL_FREQUENCY', 'instant').lower()
            self.smtp_server = os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
            self.smtp_port = int(os.environ.get('EMAIL_SMTP_PORT', '587'))
        else:
            self.enabled = email_config.get('enabled', False)
            self.sender_email = email_config.get('sender_email', '')
            self.sender_password = email_config.get('sender_password', '')
            self.recipient_list = email_config.get('recipients', [])
            self.frequency = email_config.get('frequency', 'instant').lower()
            self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
            self.smtp_port = int(email_config.get('smtp_port', 587))
        
        # Check if email is properly configured
        if self.enabled:
            if not self.sender_email or not self.sender_password or not self.recipient_list:
                logger.warning("Email notification is enabled but not properly configured.")
                self.enabled = False
            else:
                logger.info(f"Email notifications enabled. Frequency: {self.frequency}. Recipients: {len(self.recipient_list)}")
        
        # Last notification time for rate limiting
        self.last_notification_time = None
        
        # Store pending opportunities for digest emails
        self.pending_opportunities = []
    
    def send_opportunity_notification(self, opportunity: Dict[str, Any]) -> bool:
        """
        Send an email notification about a new investment opportunity.
        
        Args:
            opportunity: The opportunity data to include in the notification
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        # For instant notifications, send immediately
        if self.frequency == 'instant':
            return self._send_single_opportunity_email(opportunity)
        
        # For digest notifications, store the opportunity for later
        self.pending_opportunities.append(opportunity)
        return True
    
    def send_digest_if_needed(self) -> bool:
        """
        Send a digest email if it's time to do so.
        
        Returns:
            True if digest was sent, False otherwise
        """
        if not self.enabled or not self.pending_opportunities:
            return False
        
        now = datetime.now()
        
        # Check if it's time to send based on frequency
        should_send = False
        
        if self.frequency == 'hourly':
            # Send hourly digest if last notification was in a different hour or not sent yet
            if (not self.last_notification_time or 
                self.last_notification_time.hour != now.hour or
                self.last_notification_time.day != now.day or
                self.last_notification_time.month != now.month):
                should_send = True
        
        elif self.frequency == 'daily':
            # Send daily digest if last notification was on a different day or not sent yet
            if (not self.last_notification_time or 
                self.last_notification_time.day != now.day or
                self.last_notification_time.month != now.month):
                should_send = True
        
        if should_send:
            result = self._send_digest_email(self.pending_opportunities)
            if result:
                self.pending_opportunities = []
                self.last_notification_time = now
            return result
        
        return False
    
    def _send_single_opportunity_email(self, opportunity: Dict[str, Any]) -> bool:
        """
        Send an email about a single opportunity.
        
        Args:
            opportunity: The opportunity data
            
        Returns:
            True if successful, False otherwise
        """
        subject = f"Bitcoin Opportunity: {opportunity.get('article_title', '')}"
        
        # Create opportunity details in HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                .opportunity {{ background-color: #f1f8ff; padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
                .title {{ color: #0366d6; font-size: 18px; margin-bottom: 10px; }}
                .info {{ margin-bottom: 5px; }}
                .source {{ color: #586069; font-style: italic; }}
                .analysis {{ background-color: #f6f8fa; padding: 10px; border-radius: 5px; margin-top: 10px; }}
                .footer {{ margin-top: 30px; color: #586069; font-size: 12px; }}
                a {{ color: #0366d6; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Bitcoin News Scanner: New Investment Opportunity</h2>
                </div>
                <div class="opportunity">
                    <div class="title">
                        <a href="{opportunity.get('article_url', '')}">{opportunity.get('article_title', '')}</a>
                    </div>
                    <div class="info">
                        <strong>Source:</strong> <span class="source">{opportunity.get('article_source', 'Unknown Source')}</span>
                    </div>
                    <div class="info">
                        <strong>Date Found:</strong> {opportunity.get('formatted_time', 'Unknown')}
                    </div>
                    <div class="info">
                        <strong>Opportunity Score:</strong> {opportunity.get('ai_score', 0)}
                    </div>
                    <div class="analysis">
                        <strong>AI Analysis:</strong><br>
                        {opportunity.get('ai_analysis', 'No analysis available').replace("\\n", "<br>")}
                    </div>
                </div>
                <div class="footer">
                    <p>This email was sent by the Bitcoin News Scanner. You received this because a new potential investment opportunity was detected.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version as fallback
        text = f"""Bitcoin News Scanner: New Investment Opportunity
        
Article: {opportunity.get('article_title', '')}
URL: {opportunity.get('article_url', '')}
Source: {opportunity.get('article_source', 'Unknown Source')}
Date Found: {opportunity.get('formatted_time', 'Unknown')}
Opportunity Score: {opportunity.get('ai_score', 0)}

AI Analysis:
{opportunity.get('ai_analysis', 'No analysis available')}

This email was sent by the Bitcoin News Scanner.
"""
        
        return self._send_email(subject, text, html)
    
    def _send_digest_email(self, opportunities: List[Dict[str, Any]]) -> bool:
        """
        Send a digest email containing multiple opportunities.
        
        Args:
            opportunities: List of opportunity data
            
        Returns:
            True if successful, False otherwise
        """
        if not opportunities:
            return False
        
        subject = f"Bitcoin News Scanner: {len(opportunities)} New Opportunities"
        
        # Create HTML content with all opportunities
        opportunities_html = ""
        opportunities_text = ""
        
        for i, opp in enumerate(opportunities, 1):
            opportunities_html += f"""
            <div class="opportunity">
                <div class="number">{i}</div>
                <div class="title">
                    <a href="{opp.get('article_url', '')}">{opp.get('article_title', '')}</a>
                </div>
                <div class="info">
                    <strong>Source:</strong> <span class="source">{opp.get('article_source', 'Unknown Source')}</span>
                </div>
                <div class="info">
                    <strong>Date Found:</strong> {opp.get('formatted_time', 'Unknown')}
                </div>
                <div class="info">
                    <strong>Opportunity Score:</strong> {opp.get('ai_score', 0)}
                </div>
                <div class="analysis">
                    <strong>AI Analysis:</strong><br>
                    {opp.get('ai_analysis', 'No analysis available').replace("\\n", "<br>")}
                </div>
            </div>
            """
            
            opportunities_text += f"""
Opportunity #{i}:
Article: {opp.get('article_title', '')}
URL: {opp.get('article_url', '')}
Source: {opp.get('article_source', 'Unknown Source')}
Date Found: {opp.get('formatted_time', 'Unknown')}
Opportunity Score: {opp.get('ai_score', 0)}

AI Analysis:
{opp.get('ai_analysis', 'No analysis available')}

-------------------
"""
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                .opportunity {{ background-color: #f1f8ff; padding: 15px; border-radius: 5px; margin-bottom: 15px; position: relative; }}
                .number {{ position: absolute; top: 10px; right: 10px; background-color: #0366d6; color: white; width: 24px; height: 24px; border-radius: 12px; text-align: center; line-height: 24px; }}
                .title {{ color: #0366d6; font-size: 18px; margin-bottom: 10px; }}
                .info {{ margin-bottom: 5px; }}
                .source {{ color: #586069; font-style: italic; }}
                .analysis {{ background-color: #f6f8fa; padding: 10px; border-radius: 5px; margin-top: 10px; }}
                .footer {{ margin-top: 30px; color: #586069; font-size: 12px; }}
                a {{ color: #0366d6; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Bitcoin News Scanner: Digest of New Opportunities</h2>
                    <p>We found {len(opportunities)} potential investment opportunities</p>
                </div>
                {opportunities_html}
                <div class="footer">
                    <p>This digest was sent by the Bitcoin News Scanner. You received this because new potential investment opportunities were detected.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text = f"""Bitcoin News Scanner: Digest of New Opportunities
        
We found {len(opportunities)} potential investment opportunities:

{opportunities_text}

This digest was sent by the Bitcoin News Scanner.
"""
        
        return self._send_email(subject, text, html)
    
    def _send_email(self, subject: str, text_content: str, html_content: str) -> bool:
        """
        Send an email with both text and HTML content.
        
        Args:
            subject: Email subject
            text_content: Plain text content
            html_content: HTML content
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Create multipart message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            
            # Set recipients
            message["To"] = self.recipient_list[0]  # Primary recipient
            all_recipients = self.recipient_list.copy()  # For sending
            
            # Add plain text and HTML parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            # Attach parts - text first, then HTML
            message.attach(part1)
            message.attach(part2)
            
            # Create secure connection with server and send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, all_recipients, message.as_string())
            
            logger.info(f"Email notification sent to {len(all_recipients)} recipients")
            self.last_notification_time = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
