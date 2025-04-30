import logging
import json
import os
import requests
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    logging.warning("python-dotenv not installed. Using environment variables directly.")

from sources.base_source import Article

logger = logging.getLogger(__name__)
console_logger = logging.getLogger("console")

class AIAnalyzer:
    """
    Uses AI to analyze articles and determine if they represent
    under-the-radar opportunities.
    """
    
    def __init__(self):
        """Initialize the AI analyzer."""
        logger.info("Initializing AI Analyzer...")
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.use_real_api = self.api_key is not None and os.environ.get('USE_REAL_AI', 'false').lower() == 'true'
        
        # Get GPT model from environment variable or use default
        self.gpt_model = os.environ.get('GPT_MODEL', 'gpt-3.5-turbo')
        logger.info(f"Using GPT model: {self.gpt_model}")
        
        if self.use_real_api:
            try:
                import openai
                openai.api_key = self.api_key
                self.openai = openai
                logger.info("Using OpenAI API for article analysis")
            except ImportError:
                logger.warning("OpenAI package not installed. Using mock AI analysis.")
                self.use_real_api = False
        else:
            logger.info("Using mock AI for article analysis (no OpenAI API key provided)")
    
    def analyze_article(self, article: Article) -> Dict[str, Any]:
        """
        Analyze an article using AI to determine if it's an under-the-radar opportunity.
        
        Args:
            article: The Article object to analyze
            
        Returns:
            Dict containing analysis results
        """
        # Extract key information about the article
        article_info = {
            "title": article.title,
            "url": article.url,
            "content": article.content[:2000]  # Truncate content
        }
        
        # Perform AI analysis
        if self.use_real_api:
            ai_result = self._real_ai_analysis(article_info)
        else:
            ai_result = self._mock_ai_analysis(article_info)
        
        return {
            'article': article,
            'ai_significance_score': ai_result.get('significance_score', 0.0),
            'ai_analysis': ai_result.get('analysis', 'No AI analysis available'),
            'is_under_radar': ai_result.get('is_under_radar', False),
            'confidence': ai_result.get('confidence', 0.0),
            'buy_signal': ai_result.get('buy_signal', False)
        }
    
    def _real_ai_analysis(self, article_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Real AI analysis using OpenAI API.
        
        Args:
            article_info: Dictionary with article title, URL, and content
            
        Returns:
            Dict with AI analysis results
        """
        if not self.use_real_api:
            return self._mock_ai_analysis(article_info)
        
        try:
            # Add clear indicator that AI is being called
            logger.info(f"🤖 CALLING AI API for article: {article_info['title'][:50]}...")
            console_logger.info(f"🤖 CALLING AI API: {article_info['title'][:50]}...")
            
            # Create a prompt for the AI
            prompt = f"""
            Analyze this Bitcoin news article for investment opportunities:
            
            Title: {article_info['title']}
            URL: {article_info['url']}
            
            Content: {article_info['content']}
            
            Please determine:
            1. How significant is this news? (0.0 to 1.0 scale)
            2. Is this "under the radar" information that might not be widely known? Consider the following factors:
               - Is this news not widely reported in mainstream financial media?
               - Does it involve insider knowledge, rumors, or information from exclusive sources?
               - Does it mention key Bitcoin figures like Michael Saylor, specific government officials, or major institutional players discussing unreported plans?
               - Is it early information about potential actions, partnerships, or decisions not yet finalized?
            3. Does this represent a potential buy signal?
            4. What's your confidence in this assessment? (0.0 to 1.0)
            5. Briefly explain your analysis.
            
            Format your response as JSON with these keys:
            - significance_score (float 0-1)
            - is_under_radar (boolean)
            - buy_signal (boolean)
            - confidence (float 0-1)
            - analysis (string)
            """
            
            # Debug: Print the prompt
            debug_enabled = os.environ.get('DEBUG_AI', 'false').lower() == 'true'
            if debug_enabled:
                print("\n==== GPT PROMPT ====")
                print(prompt)
                print("====================\n")
            
            # Call the OpenAI API
            response = self.openai.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            
            # Debug: Print the raw response
            if debug_enabled:
                print("\n==== GPT RESPONSE ====")
                print(response_text)
                print("=======================\n")
            
            # Try to extract JSON from the response
            try:
                # Look for JSON object in the response
                json_str = response_text
                if '{' in response_text and '}' in response_text:
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    json_str = response_text[start:end]
                
                result = json.loads(json_str)
                
                # Ensure all expected keys are present
                required_keys = ["significance_score", "is_under_radar", "buy_signal", "confidence", "analysis"]
                for key in required_keys:
                    if key not in result:
                        result[key] = 0.0 if key in ["significance_score", "confidence"] else (False if key in ["is_under_radar", "buy_signal"] else "No analysis available")
                
                return result
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {response_text}")
                # Fall back to mock analysis
                return self._mock_ai_analysis(article_info)
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            # Fall back to mock analysis
            return self._mock_ai_analysis(article_info)
    
    def _mock_ai_analysis(self, article_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Mock AI analysis for development purposes.
        In a production system, this would be replaced with a call to an AI API.
        
        Args:
            article_info: Dictionary with article title, URL, and content
            
        Returns:
            Dict with AI analysis results
        """
        title = article_info['title'].lower()
        content = article_info['content'].lower()
        
        # Special case for the Trump Bitcoin mining article
        if "trump" in title and "bitcoin mining" in title:
            return {
                'significance_score': 0.92,
                'analysis': "This article discusses potential government involvement in Bitcoin mining, which would be a major development if true. The fact that it's still in rumor phase and not widely reported in mainstream media makes this potentially under the radar. The involvement of key Bitcoin figures like Michael Saylor adds credibility.",
                'is_under_radar': True,
                'confidence': 0.85,
                'buy_signal': True
            }
        
        # Mock analysis based on keywords
        score = 0.0
        is_under_radar = False
        buy_signal = False
        
        # Check for positive indicators
        positive_indicators = [
            "exclusive", "inside", "sources tell", "not widely reported", 
            "rumor", "potential", "deal", "partnership", "government", 
            "adoption", "institutional", "regulation", "development"
        ]
        
        negative_indicators = [
            "sell-off", "crash", "ban", "restrict", "prohibit", "bubble",
            "investigation", "fraud", "scam", "ponzi", "bearish"
        ]
        
        positive_count = sum(1 for term in positive_indicators if term in content)
        negative_count = sum(1 for term in negative_indicators if term in content)
        
        # Calculate a basic score based on presence of indicators
        score = min(1.0, (positive_count * 0.1) - (negative_count * 0.15))
        confidence = 0.5 + (0.03 * (positive_count + negative_count))  # More terms = more confidence
        
        # Determine if it's under the radar
        is_under_radar = score > 0.4
        
        # Generate a simple analysis
        if score > 0.7:
            analysis = "This appears to be a significant under-the-radar development with strong positive indicators."
            buy_signal = True
        elif score > 0.4:
            analysis = "This article contains some potentially valuable information that is not widely known."
            buy_signal = score > 0.6
        else:
            analysis = "This article doesn't appear to contain significant under-the-radar information."
            buy_signal = False
        
        return {
            'significance_score': score,
            'analysis': analysis,
            'is_under_radar': is_under_radar,
            'confidence': min(1.0, confidence),
            'buy_signal': buy_signal
        }
