"""
Keyword Extraction Module using LLM
Processes user queries to extract optimized search keywords
"""
from typing import List, Dict
from openai import OpenAI
import httpx
import json
import re
from .config import config


class KeywordExtractor:
    """Extract and optimize keywords from user queries using LLM"""
    
    def __init__(self):
        # Initialize OpenAI client for OpenRouter (Nvidia model)
        # Create httpx client with no proxy to avoid proxy errors
        import os
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
        http_client = httpx.Client(
            timeout=30.0,
            follow_redirects=True
        )
        
        self.client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
            http_client=http_client
        )
    
    def extract_keywords(self, query: str) -> Dict[str, any]:
        """
        Extract keywords, intent, and search parameters from user query
        
        Args:
            query: Raw user search query
            
        Returns:
            Dictionary containing keywords, platforms, filters, etc.
        """
        system_prompt = """You are an expert at analyzing lead generation queries and extracting 
        structured search parameters. Extract:
        1. Primary keywords (main search terms)
        2. Location (if mentioned)
        3. Industry/domain
        4. Job titles/roles
        5. Company size (if mentioned)
        6. Experience level
        7. Platforms to search (LinkedIn, Reddit, Google, etc.)
        
        Return a JSON structure with these fields."""
        
        user_prompt = f"""
        Analyze this lead search query and extract structured parameters:
        
        Query: "{query}"
        
        Return JSON with:
        {{
            "primary_keywords": ["list of main keywords"],
            "location": "location or null",
            "industry": "industry or null",
            "job_titles": ["list of job titles"],
            "company_size": "size or null",
            "experience_level": "level or null",
            "platforms": ["suggested platforms to search"],
            "search_intent": "brief description of what user wants",
            "instagram_hashtags": ["list of 3-5 relevant hashtags without # symbol for Instagram search"],
            "search_terms": ["broader search terms for general platforms"],
            "companies": ["list of company names mentioned"],
            "domains": ["list of company domains like stripe.com, github.com"]
        }}
        
        IMPORTANT: Extract company names and domains if mentioned in the query.
        For queries like "Find emails at stripe.com" or "Developers at Google", extract the company/domain.
        
        Examples:
        Query: "Find emails at stripe.com"
        Output: {{
            "primary_keywords": ["emails", "stripe"],
            "companies": ["Stripe"],
            "domains": ["stripe.com"],
            "job_titles": [],
            "search_intent": "Find email addresses at Stripe"
        }}
        
        Query: "Marketing managers at Shopify"
        Output: {{
            "primary_keywords": ["marketing", "manager", "shopify"],
            "companies": ["Shopify"],
            "domains": ["shopify.com"],
            "job_titles": ["marketing manager"],
            "search_intent": "Find marketing managers working at Shopify"
        }}
        
        Query: "Python developers in San Francisco"
        Output: {{
            "primary_keywords": ["Python", "developer", "San Francisco"],
            "companies": [],
            "domains": [],
            "job_titles": ["Python developer"],
            "instagram_hashtags": ["python", "pythondeveloper", "sanfranciscotech", "softwaredeveloper", "coding"],
            "search_terms": ["python developer", "software engineer", "programmer"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.LLM_TEMPERATURE
            )
            
            content = response.choices[0].message.content
            
            # Try to extract JSON from response (in case model adds explanation)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            keywords_data = json.loads(content)
            
            return keywords_data
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback to basic keyword extraction
            return self._fallback_extraction(query)
    
    def _fallback_extraction(self, query: str) -> Dict[str, any]:
        """Simple fallback keyword extraction if LLM fails"""
        words = query.split()
        return {
            "primary_keywords": words,
            "location": None,
            "industry": None,
            "job_titles": [],
            "company_size": None,
            "experience_level": None,
            "platforms": ["linkedin", "google", "reddit"],
            "search_intent": query
        }
    
    def generate_search_queries(self, keywords_data: Dict[str, any]) -> Dict[str, List[str]]:
        """
        Generate platform-specific search queries from extracted keywords
        
        Args:
            keywords_data: Extracted keywords and parameters
            
        Returns:
            Dictionary with platform-specific search queries
        """
        queries = {}
        
        # LinkedIn queries
        linkedin_queries = []
        for title in keywords_data.get('job_titles', []):
            base_query = f"{title}"
            if keywords_data.get('location'):
                base_query += f" {keywords_data['location']}"
            linkedin_queries.append(base_query)
        
        if not linkedin_queries:
            linkedin_queries = [' '.join(keywords_data.get('primary_keywords', []))]
        
        queries['linkedin'] = linkedin_queries
        
        # Reddit queries
        reddit_queries = []
        for keyword in keywords_data.get('primary_keywords', []):
            reddit_queries.append(keyword)
        queries['reddit'] = reddit_queries
        
        # Google queries
        google_queries = []
        base_terms = ' '.join(keywords_data.get('primary_keywords', []))
        google_queries.append(f"{base_terms} contact email")
        google_queries.append(f"{base_terms} LinkedIn")
        queries['google'] = google_queries
        
        return queries


# Convenience function
def extract_keywords(query: str) -> Dict[str, any]:
    """Extract keywords from user query"""
    extractor = KeywordExtractor()
    return extractor.extract_keywords(query)
