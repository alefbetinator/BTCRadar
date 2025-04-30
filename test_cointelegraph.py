from sources.source_factory import SourceFactory
from sources.cointelegraph import CointelegraphSource

print('Available sources:', SourceFactory.get_available_source_names())

src = CointelegraphSource()
print(f'Testing {src.name} source...')
articles = src.fetch_articles(limit=3)
print(f'Found {len(articles)} articles:')

for article in articles:
    print(f'- {article.title} ({article.url})')
    print(f'  Published: {article.published_date}')
    print(f'  Content snippet: {article.content[:150]}...' if article.content else '  No content extracted')
    print()
