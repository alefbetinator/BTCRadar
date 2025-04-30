from analyzers.ai_analyzer import AIAnalyzer
from sources.base_source import Article
from datetime import datetime

# Create a test article
test_article = Article(
    title='Is Trump Planning Bitcoin Mining? Rumors Fly',
    url='https://bitcoinist.com/is-trump-planning-bitcoin-mining-rumors-fly/',
    content="""In recent news, there are rumors that former president Donald Trump might be planning to enter the Bitcoin mining space. 
    According to unnamed sources close to the Trump family, there have been discussions about creating a Bitcoin mining operation 
    using energy from Trump-owned properties. Michael Saylor, a prominent Bitcoin advocate, has reportedly been consulted on this venture. 
    This would represent a significant shift in Trump's stance on cryptocurrency, as he has previously expressed skepticism about Bitcoin. 
    If true, this could significantly impact the Bitcoin mining landscape in the United States, potentially bringing major investment and attention to the sector. 
    However, these claims remain unverified, with no official statement from the Trump organization. 
    Industry experts suggest that such a move would align with Trump's business focus and could potentially influence regulatory attitudes toward Bitcoin in the future.""",
    published_date=datetime.now(),
    source_name='Bitcoinist'
)

# Create AI analyzer and analyze
analyzer = AIAnalyzer()
result = analyzer.analyze_article(test_article)

# Print result
print(f'AI analysis result:')
print(f'Significance score: {result.get("ai_significance_score")}')
print(f'Under radar: {result.get("is_under_radar")}')
print(f'Buy signal: {result.get("buy_signal")}')
print(f'Confidence: {result.get("confidence")}')
print(f'Analysis: {result.get("ai_analysis")}')
