#!/bin/bash

# Script to run the scanner with only one specific source
# Usage: ./run_single_source.sh [SOURCE_NAME]

# Change to script directory
cd "$(dirname "$0")"

# Check if a source name was provided
if [ $# -ne 1 ]; then
  echo "Usage: $0 <SOURCE_NAME>"
  echo "Available sources: Bitcoinist, Cointelegraph, CryptoPanic, Reddit Bitcoin, Google Search, Bitcoin Magazine, Bitcoin News RSS, TradingView"
  echo "Example: $0 \"Reddit Bitcoin\""
  exit 1
fi

SOURCE_NAME="$1"

# Activate virtual environment
source venv/bin/activate

# Create a temporary Python script to run only the specified source
cat > temp_run_source.py << 'ENDPYTHON'
#!/usr/bin/env python3
import logging
import sys
from sources.source_factory import SourceFactory

# Set up basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger()

def main():
    # Get the source name from command line
    if len(sys.argv) != 2:
        print("Usage: python temp_run_source.py <SOURCE_NAME>")
        sys.exit(1)
    
    source_name = sys.argv[1]
    
    try:
        # Get the source from the factory
        print(f"\n===== RUNNING ONLY: {source_name} =====\n")
        source = SourceFactory.get_source(source_name)
        
        # Fetch articles
        print(f"Fetching articles from {source.name}...")
        articles = source.fetch_articles(limit=20)
        
        print(f"\nFetched {len(articles)} articles from {source.name}")
        
        # Display article titles
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title} - {article.url}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
ENDPYTHON

# Make the script executable
chmod +x temp_run_source.py

# Run the temporary script with the source name
python temp_run_source.py "$SOURCE_NAME"

# Clean up
rm temp_run_source.py

# Deactivate virtual environment
deactivate
