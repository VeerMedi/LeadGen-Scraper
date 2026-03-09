"""
Google/Web Scraper for finding leads
"""
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from ..config import config
import re
import time


class GoogleScraper:
    """Scrape Google search results for leads"""
    
    def __init__(self):
        self.api_key = config.GOOGLE_API_KEY if config.is_valid_key('GOOGLE_API_KEY') else None
        self.cse_id = config.GOOGLE_CSE_ID if config.is_valid_key('GOOGLE_CSE_ID') else None
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def scrape(self, keywords_data: Dict) -> List[Dict]:
        """
        Scrape Google for leads
        
        Args:
            keywords_data: Search parameters
            
        Returns:
            List of leads from Google search
        """
        leads = []
        
        try:
            # Build search queries
            queries = self._build_queries(keywords_data)
            
            for query in queries:
                try:
                    results = self._search_google(query)
                    leads.extend(self._extract_leads_from_results(results))
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"Error searching Google for '{query}': {e}")
            
            print(f"Google: Scraped {len(leads)} leads")
            
        except Exception as e:
            print(f"Google scraping error: {e}")
        
        return leads
    
    def _build_queries(self, keywords_data: Dict) -> List[str]:
        """Build Google search queries"""
        queries = []
        
        primary_keywords = ' '.join(keywords_data.get('primary_keywords', []))
        job_titles = keywords_data.get('job_titles', [])
        location = keywords_data.get('location', '')
        
        # Query 1: General professional search with email
        queries.append(f"{primary_keywords} email contact {location}")
        
        # Query 2: LinkedIn profiles
        queries.append(f'site:linkedin.com/in {primary_keywords} {location}')
        
        # Query 3: Company websites with contact info
        for title in job_titles[:2]:  # Limit to 2 titles
            queries.append(f"{title} {primary_keywords} contact email")
        
        return queries[:5]  # Limit to 5 queries
    
    def _search_google(self, query: str) -> List[Dict]:
        """Perform Google Custom Search API request"""
        results = []
        
        try:
            if self.api_key and self.cse_id:
                # Use Google Custom Search API
                params = {
                    'key': self.api_key,
                    'cx': self.cse_id,
                    'q': query,
                    'num': 10
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('items', [])
            else:
                # Fallback: Direct web scraping (less reliable)
                results = self._scrape_google_direct(query)
        
        except Exception as e:
            print(f"Error in Google search: {e}")
        
        return results
    
    def _scrape_google_direct(self, query: str) -> List[Dict]:
        """Direct Google scraping (fallback, not recommended for production)"""
        results = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                for result in soup.find_all('div', class_='g')[:10]:
                    try:
                        title_elem = result.find('h3')
                        link_elem = result.find('a')
                        snippet_elem = result.find('div', class_='VwiC3b')
                        
                        if title_elem and link_elem:
                            results.append({
                                'title': title_elem.get_text(),
                                'link': link_elem.get('href'),
                                'snippet': snippet_elem.get_text() if snippet_elem else ''
                            })
                    except:
                        continue
        
        except Exception as e:
            print(f"Error in direct Google scraping: {e}")
        
        return results
    
    def _extract_leads_from_results(self, results: List[Dict]) -> List[Dict]:
        """Extract lead information from search results"""
        leads = []
        
        for result in results:
            try:
                # Get the page content
                url = result.get('link')
                if not url:
                    continue
                
                # Extract information from snippet first
                snippet = result.get('snippet', '')
                title = result.get('title', '')
                
                email = self._extract_email(snippet + ' ' + title)
                linkedin_url = url if 'linkedin.com/in' in url else None
                
                # Try to get more info from the page
                if email or linkedin_url:
                    page_data = self._scrape_page(url)
                    
                    lead = {
                        'name': page_data.get('name') or self._extract_name_from_linkedin_url(linkedin_url),
                        'email': email or page_data.get('email'),
                        'phone': page_data.get('phone'),
                        'linkedin_url': linkedin_url or page_data.get('linkedin_url'),
                        'company': page_data.get('company'),
                        'job_title': page_data.get('job_title'),
                        'location': page_data.get('location'),
                        'source': 'google',
                        'raw_data': {
                            'search_result_title': title,
                            'url': url,
                            'snippet': snippet
                        }
                    }
                    
                    # Only add if we have at least email or LinkedIn
                    if lead['email'] or lead['linkedin_url']:
                        leads.append(lead)
            
            except Exception as e:
                print(f"Error extracting lead from result: {e}")
        
        return leads
    
    def _scrape_page(self, url: str) -> Dict:
        """Scrape a page for contact information"""
        page_data = {}
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # Extract email
                page_data['email'] = self._extract_email(text)
                
                # Extract phone
                page_data['phone'] = self._extract_phone(text)
                
                # Extract LinkedIn URL
                linkedin_links = soup.find_all('a', href=re.compile(r'linkedin\.com/in/'))
                if linkedin_links:
                    page_data['linkedin_url'] = linkedin_links[0].get('href')
        
        except Exception as e:
            print(f"Error scraping page {url}: {e}")
        
        return page_data
    
    @staticmethod
    def _extract_email(text: str) -> str:
        """Extract email from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        # Filter out common non-personal emails
        valid_emails = [e for e in matches if not any(x in e.lower() for x in ['noreply', 'example', 'test', 'info@'])]
        return valid_emails[0] if valid_emails else None
    
    @staticmethod
    def _extract_phone(text: str) -> str:
        """Extract phone number from text"""
        phone_pattern = r'[\+]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
        matches = re.findall(phone_pattern, text)
        return matches[0] if matches else None
    
    @staticmethod
    def _extract_name_from_linkedin_url(url: str) -> str:
        """Extract name from LinkedIn URL"""
        if not url:
            return None
        
        try:
            # Extract username from LinkedIn URL
            match = re.search(r'linkedin\.com/in/([\w-]+)', url)
            if match:
                username = match.group(1)
                # Convert username to name (basic)
                name = username.replace('-', ' ').title()
                return name
        except:
            pass
        
        return None
