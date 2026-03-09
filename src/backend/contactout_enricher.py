"""
ContactOut Scraper
Enriches company leads with decision-maker contact information
"""
from typing import List, Dict, Optional
import requests
from backend.config import config


class ContactOutScraper:
    """
    Scrape contact information using ContactOut API
    Focuses on finding decision-makers (CEO, VP, Director) for companies with pain points
    """
    
    def __init__(self):
        self.api_key = config.CONTACTOUT_API_KEY
        # Working ContactOut API endpoint (found through testing)
        self.base_url = "https://api.contactout.com/v1"
        self.search_endpoint = "people/search"
        
        if not self.api_key or config._is_placeholder(self.api_key):
            print("⚠️  ContactOut API key not configured or invalid")
            print("    See CONTACTOUT_API_KEY_GUIDE.md for instructions")
            self.api_key = None
    
    def enrich_companies(self, leads: List[Dict]) -> List[Dict]:
        """
        Enrich company leads with decision-maker contact information
        Only processes companies with pain points (Google Places leads)
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            Updated leads with contact information added
        """
        if not self.api_key:
            print("⚠️  Skipping ContactOut enrichment - API key not configured")
            return leads
        
        # Filter companies with pain points
        companies_with_pain_points = [
            l for l in leads 
            if l.get('source') == 'apify_google_places' and l.get('pain_points')
        ]
        
        if not companies_with_pain_points:
            print("⚠️  No companies with pain points found - skipping ContactOut enrichment")
            return leads
        
        print(f"\n📞 Finding decision-maker contacts for {len(companies_with_pain_points)} companies...")
        
        enriched_companies = []
        successful_enrichments = 0
        
        for i, lead in enumerate(companies_with_pain_points, 1):
            company_name = lead.get('company') or lead.get('name')
            print(f"   [{i}/{len(companies_with_pain_points)}] Finding contacts at {company_name}...")
            
            contacts = self._find_decision_makers(company_name, lead.get('website'))
            
            if contacts:
                lead['decision_makers'] = contacts
                lead['contact_count'] = len(contacts)
                successful_enrichments += 1
                print(f"      ✅ Found {len(contacts)} decision-maker contacts")
            else:
                lead['decision_makers'] = []
                lead['contact_count'] = 0
                print(f"      ⚠️  No contacts found")
            
            enriched_companies.append(lead)
        
        # Combine enriched companies with other leads
        other_leads = [l for l in leads if l not in companies_with_pain_points]
        
        print(f"✅ ContactOut enrichment completed: {successful_enrichments}/{len(enriched_companies)} companies had contacts found\n")
        
        return enriched_companies + other_leads
    
    def _find_decision_makers(self, company_name: str, website: Optional[str] = None) -> List[Dict]:
        """
        Find decision-makers (C-level, VP, Directors) at a company using ContactOut API
        
        Endpoint: POST https://api.contactout.com/v1/people/search
        Auth: Bearer token in Authorization header
        
        Args:
            company_name: Name of the company
            website: Company website URL
            
        Returns:
            List of contact dictionaries with phone numbers
        """
        if not self.api_key:
            return []
        
        try:
            # Extract domain from website
            domain = None
            if website:
                domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            
            # ContactOut API endpoint
            url = f"{self.base_url}/{self.search_endpoint}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Search payload - targeting decision-makers
            payload = {
                "company_name": company_name,
                "titles": [
                    "CEO", "Chief Executive Officer",
                    "CTO", "Chief Technology Officer",
                    "COO", "Chief Operating Officer", 
                    "CFO", "Chief Financial Officer",
                    "President", "Co-Founder", "Founder",
                    "VP", "Vice President",
                    "Director", "Managing Director",
                    "Head of"
                ],
                "limit": 5
            }
            
            # Add domain if available
            if domain:
                payload["company_domain"] = domain
            
            # Make API request
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                contacts = self._parse_contactout_response(data, company_name)
                if contacts:
                    print(f"      ✅ Found {len(contacts)} decision-maker(s)")
                return contacts
            
            elif response.status_code == 401:
                print(f"      ❌ ContactOut API authentication failed")
                print(f"         Your API key may be invalid or doesn't have API access")
                print(f"         See CONTACTOUT_API_KEY_GUIDE.md for help")
                return []
            
            elif response.status_code == 404:
                # Company not in database
                return []
            
            elif response.status_code == 429:
                print(f"      ⚠️  Rate limit exceeded")
                return []
            
            else:
                print(f"      ⚠️  ContactOut API error: {response.status_code}")
                return []
        
        except requests.exceptions.Timeout:
            print(f"      ⚠️  Request timeout")
            return []
        except Exception as e:
            print(f"      ⚠️  Error: {str(e)[:100]}")
            return []
    
    def _parse_contactout_response(self, data: Dict, company_name: str) -> List[Dict]:
        """Parse ContactOut API response into standard contact format"""
        contacts = []
        
        # Try different response formats
        results = (
            data.get('results') or 
            data.get('data') or 
            data.get('people') or 
            data.get('contacts') or
            [data] if 'name' in data else []
        )
        
        for person in results[:5]:  # Limit to 5 contacts
            # Extract phone numbers
            phones = person.get('phone_numbers') or person.get('phones') or []
            phone = phones[0].get('number') if phones and isinstance(phones, list) else (phones if isinstance(phones, str) else None)
            
            # Extract emails
            emails = person.get('emails') or person.get('email') or []
            email = emails[0].get('email') if emails and isinstance(emails, list) else (emails if isinstance(emails, str) else None)
            
            contact = {
                'name': person.get('name') or person.get('full_name') or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                'title': person.get('title') or person.get('job_title') or person.get('position'),
                'phone': phone,
                'email': email,
                'linkedin': person.get('linkedin_url') or person.get('linkedin'),
                'confidence': person.get('confidence') or person.get('accuracy') or 0,
                'company': company_name
            }
            
            # Only add if we have at least name and (phone or email)
            if contact['name'] and (contact['phone'] or contact['email']):
                contacts.append(contact)
        
        return contacts
        
        # Original code kept for reference if API becomes available:
        """
        try:
            search_url = f"{self.base_url}/search/person"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "company_name": company_name,
                "titles": ["CEO", "Chief Executive Officer", "President", "VP", "Vice President", 
                          "Director", "Head of", "CTO", "COO", "CFO"],
                "per_page": 5
            }
            
            if website:
                payload["company_domain"] = website.replace('https://', '').replace('http://', '').split('/')[0]
            
            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                contacts = []
                
                for person in data.get('results', [])[:5]:
                    contact = {
                        'name': person.get('name'),
                        'title': person.get('title'),
                        'phone': person.get('phone_numbers', [{}])[0].get('number') if person.get('phone_numbers') else None,
                        'email': person.get('emails', [{}])[0].get('email') if person.get('emails') else None,
                        'linkedin': person.get('linkedin_url'),
                        'confidence': person.get('confidence_score', 0)
                    }
                    
                    if contact['phone'] or contact['email']:
                        contacts.append(contact)
                
                return contacts
            
            return []
                
        except Exception as e:
            return []
        """
    
    def get_contact_for_company(self, company_name: str, website: Optional[str] = None) -> List[Dict]:
        """
        Get decision-maker contacts for a single company
        
        Args:
            company_name: Name of the company
            website: Company website URL
            
        Returns:
            List of contact dictionaries
        """
        return self._find_decision_makers(company_name, website)


def enrich_with_contacts(leads: List[Dict]) -> List[Dict]:
    """
    Convenience function to enrich leads with ContactOut data
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        Updated leads with contact information
    """
    scraper = ContactOutScraper()
    return scraper.enrich_companies(leads)
