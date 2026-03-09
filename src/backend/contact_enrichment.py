"""
Contact Enrichment Module
Finds and enriches contact information for leads
"""
from typing import Dict, Optional, List
import requests
from .config import config
import time


class ContactEnricher:
    """Enrich lead data with email and additional contact information"""
    
    def __init__(self):
        self.hunter_api_key = config.CONTACTOUT_API_KEY  # Can be reused for Hunter.io
        self.session = requests.Session()
    
    def enrich_lead(self, lead: Dict) -> Dict:
        """
        Enrich a single lead with contact information
        
        Args:
            lead: Lead dictionary
            
        Returns:
            Enriched lead dictionary
        """
        enriched = lead.copy()
        
        # If email is missing, try to find it
        if not enriched.get('email'):
            # Try different methods
            email = None
            
            # Method 1: LinkedIn URL to email
            if enriched.get('linkedin_url'):
                email = self.find_email_from_linkedin(enriched['linkedin_url'])
            
            # Method 2: Name + Company to email
            if not email and enriched.get('name') and enriched.get('company'):
                email = self.find_email_from_name_company(
                    enriched['name'], 
                    enriched['company']
                )
            
            # Method 3: Company domain + name to email
            if not email and enriched.get('company'):
                email = self.guess_email_from_company(
                    enriched.get('name', ''),
                    enriched['company']
                )
            
            if email:
                enriched['email'] = email
                enriched['email_source'] = 'enrichment'
        
        # Verify email if present
        if enriched.get('email'):
            enriched['email_verified'] = self.verify_email(enriched['email'])
        
        return enriched
    
    def find_email_from_linkedin(self, linkedin_url: str) -> Optional[str]:
        """
        Find email from LinkedIn URL using ContactOut/Hunter API
        
        Note: You'll need to integrate a real email finder API:
        - ContactOut: https://contactout.com/
        - Hunter.io: https://hunter.io/
        - RocketReach: https://rocketreach.co/
        - Apollo.io: https://apollo.io/
        """
        # Placeholder - implement with your chosen service
        return None
    
    def find_email_from_name_company(self, name: str, company: str) -> Optional[str]:
        """Find email using Hunter.io Email Finder"""
        if not self.hunter_api_key:
            return None
        
        try:
            # Hunter.io Email Finder API
            url = "https://api.hunter.io/v2/email-finder"
            params = {
                'domain': self._extract_domain(company),
                'full_name': name,
                'api_key': self.hunter_api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('email'):
                    return data['data']['email']
        
        except Exception as e:
            print(f"Error finding email: {e}")
        
        return None
    
    def guess_email_from_company(self, name: str, company: str) -> Optional[str]:
        """
        Guess email patterns from company domain
        Common patterns: firstname.lastname@, firstname@, flastname@, etc.
        """
        if not name or not company:
            return None
        
        domain = self._extract_domain(company)
        if not domain:
            return None
        
        # Split name
        parts = name.lower().strip().split()
        if len(parts) < 2:
            return None
        
        first_name = parts[0]
        last_name = parts[-1]
        
        # Common email patterns (in order of likelihood)
        patterns = [
            f"{first_name}.{last_name}@{domain}",
            f"{first_name}@{domain}",
            f"{first_name[0]}{last_name}@{domain}",
            f"{first_name}{last_name[0]}@{domain}",
            f"{first_name}_{last_name}@{domain}",
            f"{last_name}.{first_name}@{domain}",
        ]
        
        # Try to find company email pattern using Hunter.io
        pattern = self._get_company_email_pattern(domain)
        if pattern:
            # Use the known pattern
            email = pattern.replace('{first}', first_name).replace('{last}', last_name)
            email = email.replace('{f}', first_name[0]).replace('{l}', last_name[0])
            return email
        
        # Return most common pattern as best guess
        return patterns[0]
    
    def _get_company_email_pattern(self, domain: str) -> Optional[str]:
        """Get company email pattern from Hunter.io"""
        if not self.hunter_api_key:
            return None
        
        try:
            # Hunter.io Domain Search API
            url = "https://api.hunter.io/v2/domain-search"
            params = {
                'domain': domain,
                'limit': 1,
                'api_key': self.hunter_api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pattern = data.get('data', {}).get('pattern')
                return pattern
        
        except Exception as e:
            print(f"Error getting email pattern: {e}")
        
        return None
    
    def verify_email(self, email: str) -> bool:
        """
        Verify if email is valid and deliverable
        
        Note: Integrate with email verification service:
        - Hunter.io Email Verifier
        - ZeroBounce
        - NeverBounce
        """
        # Basic format validation
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
        
        # TODO: Integrate real email verification API
        # For now, just return True for valid format
        return True
    
    def _extract_domain(self, company: str) -> Optional[str]:
        """
        Extract domain from company name
        Examples: 
            "Google" -> "google.com"
            "Microsoft Corp" -> "microsoft.com"
        """
        if not company:
            return None
        
        # Clean company name
        company = company.lower().strip()
        
        # Remove common suffixes
        suffixes = [' inc', ' llc', ' ltd', ' corp', ' corporation', 
                   ' co', ' company', ' group', ' limited']
        for suffix in suffixes:
            company = company.replace(suffix, '')
        
        # Remove special characters
        company = ''.join(c for c in company if c.isalnum())
        
        # Add .com (most common)
        return f"{company}.com"
    
    def enrich_batch(self, leads: List[Dict], delay: float = 1.0) -> List[Dict]:
        """
        Enrich multiple leads with rate limiting
        
        Args:
            leads: List of leads
            delay: Delay between API calls in seconds
            
        Returns:
            List of enriched leads
        """
        enriched_leads = []
        
        for i, lead in enumerate(leads):
            try:
                enriched = self.enrich_lead(lead)
                enriched_leads.append(enriched)
                
                # Rate limiting
                if i < len(leads) - 1:
                    time.sleep(delay)
            
            except Exception as e:
                print(f"Error enriching lead {i}: {e}")
                enriched_leads.append(lead)  # Add original if enrichment fails
        
        return enriched_leads


# Convenience function
def enrich_leads(leads: List[Dict]) -> List[Dict]:
    """Enrich a list of leads with contact information"""
    enricher = ContactEnricher()
    return enricher.enrich_batch(leads)


# Example usage and API integration instructions
"""
SETUP INSTRUCTIONS:

1. Hunter.io (Recommended for email finding)
   - Sign up: https://hunter.io/
   - Get API key from dashboard
   - Add to .env: HUNTER_API_KEY=your_key
   - Free tier: 25 requests/month
   - Paid: $49/month for 1000 requests

2. ContactOut (LinkedIn email finder)
   - Sign up: https://contactout.com/
   - Get API key
   - Add to .env: CONTACTOUT_API_KEY=your_key
   - Pricing: Contact for enterprise

3. RocketReach (Comprehensive data)
   - Sign up: https://rocketreach.co/
   - Get API key
   - Add to .env: ROCKETREACH_API_KEY=your_key
   - Free tier: 5 lookups/month
   - Paid: Starting at $39/month

4. Apollo.io (B2B contact database)
   - Sign up: https://www.apollo.io/
   - Get API key
   - Add to .env: APOLLO_API_KEY=your_key
   - Free tier: 50 credits/month
   - Paid: Starting at $49/month

INTEGRATION STEPS:

1. Choose one or more services above
2. Get API keys
3. Add to .env file
4. Update config.py with new key names
5. Implement the specific API calls in this file
6. Test with test_enrichment.py script

RECOMMENDED: Start with Hunter.io (best balance of cost/features)
"""
