from analyzers.content_analyzer import ContentAnalyzer
from analyzers.ai_analyzer import AIAnalyzer
from sources.base_source import Article
from datetime import datetime
import sys

# Create a test article
if len(sys.argv) > 1 and sys.argv[1] == "funding":
    title = 'Bitcoin Funding Rates Decline 9% In March – Will It Go Negative This Week?'
    url = 'https://bitcoinist.com/bitcoin-funding-rates-decline-9-in-march-will-it-go-negative-this-week/'
    content = 'Bitcoin funding rates have declined over the past month, revealing market sentiment. This plan has analysts concerned with potential market stability.'
else:
    title = 'Is Trump Planning Bitcoin Mining? Rumors Fly'
    url = 'https://bitcoinist.com/is-trump-planning-bitcoin-mining-rumors-fly/'
    content = 'In recent news, there are rumors that former president Donald Trump might be planning to enter the Bitcoin mining space. According to unnamed sources close to the Trump family, there have been discussions about creating a Bitcoin mining operation using energy from Trump-owned properties. Michael Saylor, a prominent Bitcoin advocate, has reportedly been consulted on this venture. This would represent a significant shift in Trump\'s stance on cryptocurrency, as he has previously expressed skepticism about Bitcoin.'

# Create test article
test_article = Article(
    title=title,
    url=url,
    content=content,
    published_date=datetime.now(),
    source_name='Bitcoinist'
)

print(f"\n===== TESTING ARTICLE: {title} =====\n")

# Create content analyzer and analyze
content_analyzer = ContentAnalyzer()
content_result = content_analyzer.analyze_article(test_article)

# Print content analysis result
print(f'CONTENT ANALYZER RESULTS:')
print(f'Significance score: {content_result.get("significance_score")}')
print(f'Is significant: {content_result.get("is_significant")}')
print(f'Insider keywords: {content_result.get("insider_keywords_found")}')
print(f'Bullish keywords: {content_result.get("bullish_keywords_found")}')
print('-' * 80)

# Create AI analyzer and analyze
ai_analyzer = AIAnalyzer()
ai_result = ai_analyzer.analyze_article(test_article)

# Print AI analysis result
print(f'\nAI ANALYZER RESULTS:')
print(f'Significance score: {ai_result.get("ai_significance_score")}')
print(f'Under radar: {ai_result.get("is_under_radar")}')
print(f'Buy signal: {ai_result.get("buy_signal")}')
print(f'Confidence: {ai_result.get("confidence")}')
print(f'Analysis: {ai_result.get("ai_analysis")}')
print('-' * 80)

# Combined analysis
print("\nOPPORTUNITY DECISION LOGIC:")
print(f"From ContentAnalyzer: Article {'IS' if content_result.get('is_significant') else 'is NOT'} significant")
print(f"From AIAnalyzer: Article {'IS' if ai_result.get('is_under_radar') else 'is NOT'} under the radar")

# Check if article would be in significant_articles list
would_be_significant = content_result.get('is_significant') or ai_result.get('is_under_radar')
print(f"\nWould be added to significant_articles: {would_be_significant}")

# Check if article would be an opportunity
require_sell_signal = False
has_sell_signal = True
would_be_opportunity = False

# Traditional criteria
if not require_sell_signal or has_sell_signal:
    if would_be_significant:
        would_be_opportunity = True

# AI criteria
if ai_result.get('is_under_radar') and ai_result.get('buy_signal'):
    would_be_opportunity = True

print(f"Would be considered an opportunity: {would_be_opportunity}")
