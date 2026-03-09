"""
LinkedIn Scraper using Apify LinkedIn actors
"""
from typing import List, Dict
from apify_client import ApifyClient
from ..config import config
import time


class LinkedInScraper:
    """Scrape LinkedIn profiles using Apify"""
    
    def __init__(self):
        if config.is_valid_key('APIFY_API_KEY'):
            self.client = ApifyClient(config.APIFY_API_KEY)
        else:
            self.client = None
        # Using popular LinkedIn scraper actors
        self.sales_navigator_actor = "curious_coder/linkedin-sales-navigator-scraper"
        self.profile_scraper_actor = "apify/linkedin-profile-scraper"
    
    def scrape(self, keywords_data: Dict) -> List[Dict]:
        """
        Scrape LinkedIn for leads
        
        Args:
            keywords_data: Search parameters
            
        Returns:
            List of LinkedIn leads
        """
        leads = []
        
        if not self.client:
            print("LinkedIn scraping skipped: APIFY_API_KEY not configured")
            return leads
        
        try:
            # Build search URLs based on keywords
            search_urls = self._build_search_urls(keywords_data)
            
            # Run LinkedIn Sales Navigator scraper
            leads.extend(self._scrape_sales_navigator(search_urls))
            
        except Exception as e:
            print(f"LinkedIn scraping error: {e}")
        
        return leads
    
    def _build_search_urls(self, keywords_data: Dict) -> List[str]:
        """Build LinkedIn search URLs from keywords"""
        urls = []
        
        # Get job titles
        job_titles = keywords_data.get('job_titles', [])
        location = keywords_data.get('location', '')
        
        if not job_titles:
            job_titles = keywords_data.get('primary_keywords', [''])
        
        # Build LinkedIn search URLs
        base_url = "https://www.linkedin.com/search/results/people/"
        
        for title in job_titles:
            params = []
            if title:
                params.append(f"keywords={title.replace(' ', '%20')}")
            if location:
                params.append(f"location={location.replace(' ', '%20')}")
            
            url = base_url + "?" + "&".join(params) if params else base_url
            urls.append(url)
        
        return urls[:3]  # Limit to 3 searches to avoid rate limits
    
    def _scrape_sales_navigator(self, search_urls: List[str]) -> List[Dict]:
        """Scrape using LinkedIn Sales Navigator actor"""
        leads = []
        
        try:
            # Prepare input for Apify actor
            run_input = {
                "searchUrls": search_urls,
                "maxResults": 50,  # Limit results per search
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            # Run the actor
            run = self.client.actor(self.sales_navigator_actor).call(run_input=run_input)
            
            # Fetch results
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            # Process results
            for item in dataset_items:
                lead = self._process_linkedin_item(item)
                if lead:
                    leads.append(lead)
            
            print(f"LinkedIn: Scraped {len(leads)} leads")
            
        except Exception as e:
            print(f"LinkedIn Sales Navigator scraping error: {e}")
            # Try alternative method with direct profile scraper
            leads.extend(self._scrape_profiles_fallback(search_urls))
        
        return leads
    
    def _scrape_profiles_fallback(self, search_urls: List[str]) -> List[Dict]:
        """Fallback method using profile scraper"""
        leads = []
        
        try:
            # Extract profile URLs from search results (simplified)
            # In production, you'd need to get profile URLs first
            
            run_input = {
                "urls": search_urls[:10],  # Limit to 10 profiles
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            run = self.client.actor(self.profile_scraper_actor).call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            for item in dataset_items:
                lead = self._process_linkedin_item(item)
                if lead:
                    leads.append(lead)
                    
        except Exception as e:
            print(f"LinkedIn profile scraping fallback error: {e}")
        
        return leads
    
    def _process_linkedin_item(self, item: Dict) -> Dict:
        """Process LinkedIn scraped item into lead format"""
        try:
            lead = {
                'name': item.get('name') or item.get('fullName'),
                'email': item.get('email'),  # Often not available
                'phone': item.get('phone'),
                'linkedin_url': item.get('url') or item.get('profileUrl'),
                'company': item.get('company') or item.get('currentCompany'),
                'job_title': item.get('title') or item.get('headline'),
                'location': item.get('location'),
                'source': 'linkedin',
                'raw_data': item
            }
            
            # Only return if we have at least name and LinkedIn URL
            if lead['name'] and lead['linkedin_url']:
                return lead
            
        except Exception as e:
            print(f"Error processing LinkedIn item: {e}")
        
        return None
