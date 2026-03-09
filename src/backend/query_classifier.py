"""
Query Classifier
Uses LLM to automatically determine if query is for profile scraping or search/hashtag mode
"""
import requests
from backend.config import config


class QueryClassifier:
    """Classify user queries to determine appropriate scraping mode"""
    
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.base_url = config.OPENROUTER_BASE_URL
        self.model = "google/gemini-2.5-flash-lite"
    
    def classify_query(self, query: str) -> dict:
        """
        Classify query and extract relevant information
        
        Args:
            query: User's input query
            
        Returns:
            dict with:
                - mode: 'profile' or 'search'
                - platform: detected platform (for profile mode)
                - urls: list of URLs (for profile mode)
                - search_query: cleaned search query (for search mode)
                - confidence: classification confidence (0-1)
        """
        
        prompt = f"""You are a query classifier for a lead scraping system. Analyze the user's query and determine:

1. **MODE**: Is this a profile scraping request or a search/hashtag request?
   - Profile: User provides URLs or wants to scrape specific profiles (LinkedIn, Instagram, Facebook, etc.)
   - Search: User wants to find leads via keywords, hashtags, industries, job titles, locations, etc.

2. **Extract relevant information**:
   - If PROFILE mode: Extract all URLs and detect platform (linkedin/instagram/facebook)
   - If SEARCH mode: Clean and optimize the search query

USER QUERY: "{query}"

Respond ONLY with valid JSON in this exact format:
{{
    "mode": "profile" or "search",
    "platform": "linkedin" or "instagram" or "facebook" or null,
    "urls": ["url1", "url2"] or [],
    "search_query": "cleaned query" or null,
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}

Examples:
- "https://linkedin.com/in/johndoe" → {{"mode": "profile", "platform": "linkedin", "urls": ["https://linkedin.com/in/johndoe"], "confidence": 1.0}}
- "Python developers in NYC" → {{"mode": "search", "search_query": "Python developers in NYC", "confidence": 1.0}}
- "Scrape this profile: linkedin.com/in/jane" → {{"mode": "profile", "platform": "linkedin", "urls": ["linkedin.com/in/jane"], "confidence": 0.95}}
"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Extract JSON from response
                import json
                import re
                
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    classification = json.loads(json_match.group())
                    
                    # Validate and set defaults
                    classification.setdefault('mode', 'search')
                    classification.setdefault('platform', None)
                    classification.setdefault('urls', [])
                    classification.setdefault('search_query', query)
                    classification.setdefault('confidence', 0.5)
                    classification.setdefault('reasoning', '')
                    
                    return classification
            
            # Fallback: Simple heuristic
            return self._fallback_classification(query)
            
        except Exception as e:
            print(f"Classification error: {e}")
            return self._fallback_classification(query)
    
    def _fallback_classification(self, query: str) -> dict:
        """Fallback heuristic-based classification"""
        query_lower = query.lower()
        
        # Check for URLs
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, query)
        
        # Check for domain mentions without protocol
        if 'linkedin.com' in query_lower or '/in/' in query_lower:
            urls.extend([line.strip() for line in query.split('\n') if 'linkedin' in line.lower()])
            platform = 'linkedin'
        elif 'instagram.com' in query_lower or '@' in query:
            urls.extend([line.strip() for line in query.split('\n') if 'instagram' in line.lower()])
            platform = 'instagram'
        elif 'facebook.com' in query_lower:
            urls.extend([line.strip() for line in query.split('\n') if 'facebook' in line.lower()])
            platform = 'facebook'
        else:
            platform = None
        
        # Determine mode
        if urls or 'profile' in query_lower or 'scrape' in query_lower and platform:
            return {
                'mode': 'profile',
                'platform': platform,
                'urls': urls,
                'search_query': None,
                'confidence': 0.7,
                'reasoning': 'Detected URLs or profile scraping keywords'
            }
        else:
            return {
                'mode': 'search',
                'platform': None,
                'urls': [],
                'search_query': query,
                'confidence': 0.8,
                'reasoning': 'No URLs detected, treating as search query'
            }


def classify_query(query: str) -> dict:
    """Convenience function to classify a query"""
    classifier = QueryClassifier()
    return classifier.classify_query(query)
