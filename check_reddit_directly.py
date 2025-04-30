#!/usr/bin/env python3
"""
Simple script to directly check Reddit for specific posts.
"""

import requests
import json

# URL for Reddit's r/Bitcoin hot posts
url = "https://www.reddit.com/r/Bitcoin/hot.json"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    # Make the request
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    # Parse the JSON response
    data = response.json()
    
    # Extract posts
    posts = data['data']['children']
    
    # Print the first 10 posts (or fewer if there aren't 10)
    print("\n===== Top r/Bitcoin Posts =====\n")
    for i, post in enumerate(posts[:10], 1):
        post_data = post['data']
        title = post_data['title']
        author = post_data['author']
        url = post_data['url']
        permalink = f"https://www.reddit.com{post_data['permalink']}"
        
        print(f"{i}. Title: {title}")
        print(f"   Author: {author}")
        print(f"   URL: {url}")
        print(f"   Reddit Link: {permalink}")
        print(f"   Stickied: {post_data.get('stickied', False)}")
        print()
        
        # Check specifically for Jack Dorsey, Square, or Block
        keywords = ['dorsey', 'jack', 'square', 'block']
        if any(keyword.lower() in title.lower() for keyword in keywords):
            print(f"*** FOUND DORSEY/SQUARE/BLOCK POST: {title} ***")
            print()
    
except Exception as e:
    print(f"Error: {e}")
