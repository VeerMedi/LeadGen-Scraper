"""
Scraping modules orchestrator
"""
from typing import List, Dict
import asyncio
from .linkedin_scraper import LinkedInScraper
from .reddit_scraper import RedditScraper
from .google_scraper import GoogleScraper
from .apify_scraper import ApifyScraper
from .hunter_scraper import HunterScraper


class ScraperOrchestrator:
    """Orchestrate multiple scrapers working in parallel"""
    
    def __init__(self):
        self.linkedin = LinkedInScraper()
        self.reddit = RedditScraper()
        self.google = GoogleScraper()
        self.apify = ApifyScraper()
        self.hunter = HunterScraper()
    
    async def scrape_all_platforms_async(self, keywords_data: Dict) -> List[Dict]:
        """
        Scrape all platforms asynchronously
        
        Args:
            keywords_data: Extracted keywords and search parameters
            
        Returns:
            Combined list of leads from all platforms
        """
        tasks = []
        
        # LinkedIn scraping
        if 'linkedin' in keywords_data.get('platforms', []):
            tasks.append(self._scrape_linkedin(keywords_data))
        
        # Reddit scraping
        if 'reddit' in keywords_data.get('platforms', []):
            tasks.append(self._scrape_reddit(keywords_data))
        
        # Google scraping
        if 'google' in keywords_data.get('platforms', []):
            tasks.append(self._scrape_google(keywords_data))
        
        # Apify scraping (Instagram)
        if 'apify' in keywords_data.get('platforms', []):
            print("🎬 Apify platform selected - will scrape Instagram")
            tasks.append(self._scrape_apify(keywords_data))
        else:
            print("⏭️  Apify platform not selected - skipping")
        
        # Hunter.io scraping (Email discovery)
        if 'hunter' in keywords_data.get('platforms', []):
            print("📧 Hunter.io platform selected - will find emails")
            tasks.append(self._scrape_hunter(keywords_data))
        else:
            print("⏭️  Hunter.io platform not selected - skipping")
        
        # Execute all scrapers in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_leads = []
        for result in results:
            if isinstance(result, list):
                all_leads.extend(result)
            elif isinstance(result, Exception):
                print(f"Scraping error: {result}")
        
        return all_leads
    
    async def _scrape_linkedin(self, keywords_data: Dict) -> List[Dict]:
        """Scrape LinkedIn"""
        try:
            return await asyncio.to_thread(
                self.linkedin.scrape, 
                keywords_data
            )
        except Exception as e:
            print(f"LinkedIn scraping failed: {e}")
            return []
    
    async def _scrape_reddit(self, keywords_data: Dict) -> List[Dict]:
        """Scrape Reddit"""
        try:
            return await asyncio.to_thread(
                self.reddit.scrape,
                keywords_data
            )
        except Exception as e:
            print(f"Reddit scraping failed: {e}")
            return []
    
    async def _scrape_google(self, keywords_data: Dict) -> List[Dict]:
        """Scrape Google"""
        try:
            return await asyncio.to_thread(
                self.google.scrape,
                keywords_data
            )
        except Exception as e:
            print(f"Google scraping failed: {e}")
            return []
    
    async def _scrape_apify(self, keywords_data: Dict) -> List[Dict]:
        """Scrape using Apify actors"""
        try:
            max_results = keywords_data.get('max_results', 10)
            return await asyncio.to_thread(
                self.apify.scrape,
                keywords_data,
                max_results
            )
        except Exception as e:
            print(f"Apify scraping failed: {e}")
            return []
    
    async def _scrape_hunter(self, keywords_data: Dict) -> List[Dict]:
        """Scrape using Hunter.io"""
        try:
            max_results = keywords_data.get('max_results', 10)
            return await asyncio.to_thread(
                self.hunter.scrape,
                keywords_data,
                True,  # auto_discover
                max_results
            )
        except Exception as e:
            print(f"Hunter.io scraping failed: {e}")
            return []


def scrape_leads(keywords_data: Dict, max_results: int = 10) -> List[Dict]:
    """
    Convenience function to scrape leads from all platforms
    
    Args:
        keywords_data: Extracted keywords and parameters
        max_results: Maximum number of results per platform (default: 10)
        
    Returns:
        List of leads from all platforms
    """
    orchestrator = ScraperOrchestrator()
    keywords_data['max_results'] = max_results  # Pass to orchestrator
    
    # Run async scraping (Windows-compatible)
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop in thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        leads = loop.run_until_complete(
            orchestrator.scrape_all_platforms_async(keywords_data)
        )
    finally:
        # Don't close the loop if we didn't create it
        pass
    
    return leads
