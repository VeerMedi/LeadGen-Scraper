"""
Hunter.io Email Finder and Verification Scraper
Provides email discovery, verification, and domain search capabilities
"""
from typing import List, Dict, Optional
import requests
from ..config import config
import time


class HunterScraper:
    """Use Hunter.io API for email discovery and verification"""
    
    BASE_URL = "https://api.hunter.io/v2"
    
    def __init__(self):
        self.api_key = config.HUNTER_API_KEY if hasattr(config, 'HUNTER_API_KEY') else None
        
    def scrape(self, keywords_data: Dict, auto_discover: bool = False, max_results: int = 10) -> List[Dict]:
        """
        Main scraping method that routes to appropriate Hunter.io endpoints
        
        Args:
            keywords_data: Search parameters including query, domains, and names
            auto_discover: Whether to use LLM to discover companies (default: False)
            max_results: Maximum number of companies to search (default: 10)
            
        Returns:
            List of leads with email information
        """
        leads = []
        
        if not self.api_key or not config.is_valid_key('HUNTER_API_KEY'):
            print("⚠️  Hunter.io scraping skipped: HUNTER_API_KEY not configured")
            return leads
        
        print("🎯 Starting Hunter.io scraping...")
        
        try:
            scrape_type = keywords_data.get('scrape_type', 'auto')
            print(f"  🔧 Scrape type: {scrape_type}")
            
            # Domain search - find all emails from a domain (only if domains are explicitly provided)
            if scrape_type == 'domain_search' and 'domains' in keywords_data and keywords_data['domains']:
                domains = keywords_data.get('domains', [])
                for domain in domains:
                    domain_leads = self._domain_search(domain, keywords_data)
                    leads.extend(domain_leads)
                    time.sleep(1)  # Rate limiting
            
            # Email finder - find email for specific person at company
            elif scrape_type == 'email_finder' and 'contacts' in keywords_data:
                contacts = keywords_data.get('contacts', [])
                for contact in contacts:
                    found_lead = self._find_email(
                        domain=contact.get('domain'),
                        first_name=contact.get('first_name'),
                        last_name=contact.get('last_name'),
                        full_name=contact.get('full_name')
                    )
                    if found_lead:
                        leads.append(found_lead)
                    time.sleep(1)  # Rate limiting
            
            # Email verification
            elif scrape_type == 'email_verify' and 'emails' in keywords_data:
                emails = keywords_data.get('emails', [])
                for email in emails:
                    verified_lead = self._verify_email(email)
                    if verified_lead:
                        leads.append(verified_lead)
                    time.sleep(0.5)  # Rate limiting
            
            # Company search with query
            else:
                query = keywords_data.get('query', '')
                print(f"  📝 Processing query: {query}")
                
                # Try to extract domains from multiple sources (priority order)
                domains = []
                
                # 1. HIGHEST PRIORITY: LLM-extracted domains from keywords_data
                if 'domains' in keywords_data and keywords_data['domains']:
                    llm_domains = keywords_data.get('domains', [])
                    domains.extend(llm_domains)
                    print(f"  🤖 LLM extracted {len(llm_domains)} domain(s): {', '.join(llm_domains)}")
                
                # 2. LLM-extracted company names (convert to domains)
                if 'companies' in keywords_data and keywords_data['companies']:
                    companies = keywords_data.get('companies', [])
                    print(f"  🏢 LLM extracted {len(companies)} companies")
                    for company in companies:
                        domain = self._company_to_domain(company)
                        if domain:
                            domains.append(domain)
                
                # 3. Extract from query text directly (if LLM missed anything)
                if not domains:
                    query_domains = self._extract_domains_from_query(query)
                    domains.extend(query_domains)
                    if query_domains:
                        print(f"  🔍 Direct extraction found: {', '.join(query_domains)}")
                
                # 4. FALLBACK: Try common company name recognition
                if not domains:
                    guessed = self._guess_domains_from_query(query)
                    domains.extend(guessed)
                    if guessed:
                        print(f"  💡 Guessed domains: {', '.join(guessed)}")
                
                # 5. NEW: Auto-discover companies if no domains found
                if not domains:
                    print(f"  🔎 No companies found - searching for companies matching your query...")
                    discovered_companies = self._discover_companies_for_query(query, keywords_data)
                    if discovered_companies:
                        print(f"  ✨ Discovered {len(discovered_companies)} companies!")
                        domains.extend(discovered_companies)
                    else:
                        print(f"  ℹ️  Could not find companies for this query")
                
                # Remove duplicates while preserving order
                seen = set()
                domains = [d for d in domains if d not in seen and not seen.add(d)]
                
                if domains:
                    print(f"  🎯 Searching {len(domains)} domain(s): {', '.join(domains[:3])}{'...' if len(domains) > 3 else ''}")
                    for domain in domains[:max_results]:  # Limit domains to preserve API credits
                        if len(leads) >= max_results:  # Stop if we've reached the limit
                            print(f"  ⚠️  Reached max_results limit ({max_results}), stopping domain search")
                            break
                        domain_leads = self._domain_search(domain, keywords_data)
                        leads.extend(domain_leads)
                        time.sleep(1)  # Rate limiting
                else:
                    print("ℹ️  No companies/domains found in your query.")
                    print("     💡 Try queries like:")
                    print("        • 'Find emails at stripe.com'")
                    print("        • 'Developers at GitHub'")
                    print("        • 'Marketing team at Shopify'")
                    print("        • 'Sales people at Salesforce'")
            
            # Ensure we don't exceed max_results
            if len(leads) > max_results:
                print(f"  ✂️  Truncating from {len(leads)} to {max_results} leads")
                leads = leads[:max_results]
            
            print(f"✅ Hunter.io found {len(leads)} leads")
            
        except Exception as e:
            print(f"❌ Hunter.io scraping error: {e}")
        
        return leads[:max_results]  # Final safety check
    
    def _domain_search(self, domain: str, keywords_data: Dict) -> List[Dict]:
        """
        Search for all emails from a specific domain
        
        Args:
            domain: Company domain (e.g., 'stripe.com')
            keywords_data: Additional search parameters
            
        Returns:
            List of leads from the domain
        """
        leads = []
        
        try:
            params = {
                'domain': domain,
                'api_key': self.api_key,
                'limit': 10  # Fixed limit of 10 emails per domain
            }
            
            # Add optional filters
            if 'department' in keywords_data:
                params['department'] = keywords_data['department']
            if 'seniority' in keywords_data:
                params['seniority'] = keywords_data['seniority']
            
            response = requests.get(
                f"{self.BASE_URL}/domain-search",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'emails' in data['data']:
                    emails = data['data']['emails']
                    
                    for email_data in emails:
                        # Debug: Check if email is in the data
                        if not email_data.get('value'):
                            print(f"  ⚠️  Warning: No email value in response for {email_data.get('first_name')} {email_data.get('last_name')}")
                        
                        lead = self._format_lead(email_data, domain)
                        leads.append(lead)
                    
                    print(f"  📧 Found {len(emails)} emails from {domain}")
                else:
                    print(f"  ℹ️  No emails found for {domain}")
            else:
                print(f"  ⚠️  Hunter.io API error for {domain}: {response.status_code}")
                if response.status_code == 401:
                    print(f"      Invalid API key")
                elif response.status_code == 429:
                    print(f"      Rate limit exceeded")
                
        except Exception as e:
            print(f"  ❌ Error searching domain {domain}: {e}")
        
        return leads
    
    def _find_email(self, domain: str, first_name: Optional[str] = None, 
                    last_name: Optional[str] = None, full_name: Optional[str] = None) -> Optional[Dict]:
        """
        Find email address for a specific person at a company
        
        Args:
            domain: Company domain
            first_name: Person's first name
            last_name: Person's last name
            full_name: Full name (will be split if first/last not provided)
            
        Returns:
            Lead dict with email information or None
        """
        try:
            # Parse full name if needed
            if full_name and (not first_name or not last_name):
                parts = full_name.strip().split()
                first_name = parts[0] if len(parts) > 0 else ''
                last_name = parts[-1] if len(parts) > 1 else ''
            
            if not domain or not first_name or not last_name:
                return None
            
            params = {
                'domain': domain,
                'first_name': first_name,
                'last_name': last_name,
                'api_key': self.api_key
            }
            
            response = requests.get(
                f"{self.BASE_URL}/email-finder",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and data['data'].get('email'):
                    lead = self._format_lead(data['data'], domain)
                    print(f"  ✅ Found email for {first_name} {last_name} at {domain}")
                    return lead
                else:
                    print(f"  ℹ️  No email found for {first_name} {last_name} at {domain}")
            else:
                print(f"  ⚠️  Hunter.io API error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error finding email: {e}")
        
        return None
    
    def _verify_email(self, email: str) -> Optional[Dict]:
        """
        Verify if an email address is valid and deliverable
        
        Args:
            email: Email address to verify
            
        Returns:
            Lead dict with verification information
        """
        try:
            params = {
                'email': email,
                'api_key': self.api_key
            }
            
            response = requests.get(
                f"{self.BASE_URL}/email-verifier",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    verification = data['data']
                    
                    lead = {
                        'name': f"{verification.get('first_name', '')} {verification.get('last_name', '')}".strip(),
                        'email': email,
                        'source': 'hunter.io',
                        'verification_status': verification.get('status'),
                        'verification_result': verification.get('result'),
                        'score': verification.get('score', 0),
                        'is_valid': verification.get('result') == 'deliverable',
                        'company': verification.get('organization', ''),
                        'position': verification.get('position', ''),
                    }
                    
                    print(f"  ✅ Verified {email}: {verification.get('result')}")
                    return lead
            else:
                print(f"  ⚠️  Hunter.io verification error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error verifying email: {e}")
        
        return None
    
    def _format_lead(self, email_data: Dict, domain: str) -> Dict:
        """
        Format Hunter.io email data into standard lead format
        
        Args:
            email_data: Raw email data from Hunter.io API
            domain: Company domain
            
        Returns:
            Formatted lead dictionary
        """
        # Calculate quality score based on Hunter.io confidence
        confidence = email_data.get('confidence', 0)
        quality_score = min(100, confidence)  # Hunter gives 0-100 score
        
        # Determine sentiment based on position/seniority
        position = (email_data.get('position') or '').lower()
        seniority = (email_data.get('seniority') or '').lower()
        
        if any(title in position for title in ['ceo', 'founder', 'president', 'director', 'vp', 'head']):
            sentiment = 'hot'
        elif any(title in position for title in ['manager', 'lead', 'senior', 'principal']):
            sentiment = 'warm'
        else:
            sentiment = 'cold'
        
        # Hunter.io returns email in 'value' field, not 'email'
        email_address = email_data.get('value') or email_data.get('email', '')
        
        lead = {
            'name': f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
            'email': email_address,
            'job_title': email_data.get('position', 'N/A'),  # Streamlit uses 'job_title'
            'position': email_data.get('position', 'N/A'),  # Keep for backward compatibility
            'company': email_data.get('organization', domain),
            'source': 'hunter.io',
            'platform': 'Email Discovery',
            'linkedin_url': email_data.get('linkedin', ''),  # Streamlit uses 'linkedin_url'
            'url': email_data.get('linkedin', ''),  # Keep for backward compatibility
            'phone': email_data.get('phone_number', ''),
            'location': '',  # Hunter.io doesn't provide location
            'department': email_data.get('department', ''),
            'seniority': seniority,
            'twitter': email_data.get('twitter', ''),
            'quality_score': quality_score,
            'warmth_score': quality_score,  # Use confidence as warmth score
            'sentiment': sentiment,
            'verification_status': email_data.get('verification', {}).get('status', 'unknown'),
            'verification_date': email_data.get('verification', {}).get('date', ''),
            'confidence': confidence,
            'type': email_data.get('type', 'personal'),
        }
        
        return lead
    
    def _extract_domains_from_query(self, query: str) -> List[str]:
        """
        Extract company domains from a search query
        
        Args:
            query: Search query text
            
        Returns:
            List of potential domains
        """
        domains = []
        import re
        
        # Look for explicit domain mentions (e.g., stripe.com, github.io)
        domain_pattern = r'\b([a-z0-9-]+\.[a-z]{2,})\b'
        found_domains = re.findall(domain_pattern, query.lower())
        domains.extend(found_domains)
        
        # Look for patterns like "at CompanyName" or "from CompanyName"
        company_keywords = ['at', 'from', 'for', 'with']
        words = query.lower().split()
        
        for i, word in enumerate(words):
            if word in company_keywords and i + 1 < len(words):
                potential_company = words[i + 1].strip('.,!?')
                if potential_company and len(potential_company) > 2 and '.' not in potential_company:
                    domains.append(f"{potential_company}.com")
        
        return domains
    
    def _guess_domains_from_query(self, query: str) -> List[str]:
        """
        Make educated guesses about domains from query keywords
        
        Args:
            query: Search query text
            
        Returns:
            List of potential domains
        """
        domains = []
        query_lower = query.lower()
        
        # Common tech company mapping
        common_companies = {
            'google': 'google.com',
            'facebook': 'facebook.com',
            'meta': 'meta.com',
            'amazon': 'amazon.com',
            'microsoft': 'microsoft.com',
            'apple': 'apple.com',
            'netflix': 'netflix.com',
            'tesla': 'tesla.com',
            'twitter': 'twitter.com',
            'x': 'x.com',
            'linkedin': 'linkedin.com',
            'github': 'github.com',
            'stripe': 'stripe.com',
            'shopify': 'shopify.com',
            'airbnb': 'airbnb.com',
            'uber': 'uber.com',
            'lyft': 'lyft.com',
            'spotify': 'spotify.com',
            'slack': 'slack.com',
            'zoom': 'zoom.us',
            'dropbox': 'dropbox.com',
            'salesforce': 'salesforce.com',
            'oracle': 'oracle.com',
            'ibm': 'ibm.com',
            'adobe': 'adobe.com',
            'intel': 'intel.com',
            'nvidia': 'nvidia.com',
        }
        
        for company, domain in common_companies.items():
            if company in query_lower:
                domains.append(domain)
        
        return domains
    
    def _company_to_domain(self, company_name: str) -> Optional[str]:
        """
        Convert company name to domain
        
        Args:
            company_name: Company name
            
        Returns:
            Domain string or None
        """
        if not company_name:
            return None
        
        # Clean company name
        company_clean = company_name.lower().strip()
        
        # Remove common suffixes
        suffixes = [' inc', ' inc.', ' llc', ' ltd', ' ltd.', ' corp', ' corp.', 
                   ' corporation', ' company', ' co.', ' co']
        for suffix in suffixes:
            if company_clean.endswith(suffix):
                company_clean = company_clean[:-len(suffix)].strip()
        
        # Remove special characters and spaces
        import re
        company_clean = re.sub(r'[^a-z0-9]', '', company_clean)
        
        if len(company_clean) > 2:
            return f"{company_clean}.com"
        
        return None
    
    def _discover_companies_for_query(self, query: str, keywords_data: Dict) -> List[str]:
        """
        Use LLM to discover relevant companies and their domains for a query
        
        Args:
            query: User's search query
            keywords_data: Extracted keywords and context
            
        Returns:
            List of discovered company domains
        """
        try:
            from openai import OpenAI
            import httpx
            import os
            
            # Remove proxy settings
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                os.environ.pop(key, None)
            
            http_client = httpx.Client(timeout=30.0, follow_redirects=True)
            
            client = OpenAI(
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL,
                http_client=http_client
            )
            
            # Extract context
            industry = keywords_data.get('industry', '')
            location = keywords_data.get('location', '')
            job_titles = keywords_data.get('job_titles', [])
            
            prompt = f"""Given this lead search query, list 5-10 mid-sized companies (100-200 employees) that match the criteria.
For each company, provide their primary domain name.

Query: "{query}"
Industry: {industry or 'Any'}
Location: {location or 'Any'}
Job Titles: {', '.join(job_titles) if job_titles else 'Any'}

Target: Mid-tier companies with approximately 100-200 employees (NOT Fortune 500 or major brands)

Return ONLY a JSON array of domains (no explanations):
["company1.com", "company2.com", "company3.ae"]

Examples:
- Query "property brokers in UAE" → ["allsopp.com", "provident.ae", "better-homes.ae", "harbor-re.com"]
- Query "fashion companies needing trend analysis" → ["revolve.com", "everlane.com", "rothy.com", "allbirds.com"]
- Query "tech startups in Dubai" → ["fetchr.com", "kitopi.com", "noon-academy.com"]

Focus on growing, mid-market companies (100-200 employees), NOT Nike/Adidas/Zara scale brands.
Return ONLY the JSON array, nothing else."""

            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON array
            import re
            import json
            json_match = re.search(r'\[[\s\S]*?\]', content)
            
            if json_match:
                domains = json.loads(json_match.group())
                # Clean and validate domains
                valid_domains = []
                for domain in domains[:10]:  # Limit to 10
                    domain = domain.strip().lower()
                    if '.' in domain and len(domain) > 4:
                        valid_domains.append(domain)
                
                return valid_domains
            
        except Exception as e:
            print(f"  ⚠️  Company discovery error: {e}")
        
        return []
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get Hunter.io account information and remaining API calls
        
        Returns:
            Account information dictionary
        """
        try:
            params = {'api_key': self.api_key}
            
            response = requests.get(
                f"{self.BASE_URL}/account",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    account = data['data']
                    return {
                        'email': account.get('email'),
                        'plan_name': account.get('plan_name'),
                        'requests_available': account.get('requests', {}).get('available', 0),
                        'requests_used': account.get('requests', {}).get('used', 0),
                    }
        except Exception as e:
            print(f"Error getting account info: {e}")
        
        return None
