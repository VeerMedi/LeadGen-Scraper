"""
Pain Point Analyzer using Perplexity Sonar
Analyzes company websites to identify business pain points
"""
from typing import Dict, List, Optional
from openai import OpenAI
import httpx
import re
from urllib.parse import urlparse
from .config import config


class PainPointAnalyzer:
    """Analyze company websites to find pain points using Perplexity Sonar"""
    
    def __init__(self):
        if not config.OPENROUTER_API_KEY or config._is_placeholder(config.OPENROUTER_API_KEY):
            print("⚠️  OpenRouter API key not configured - pain point analysis disabled")
            self.client = None
            return
        
        # Initialize Perplexity client via OpenRouter
        import os
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
        http_client = httpx.Client(
            timeout=60.0,
            follow_redirects=True
        )
        
        # Use OpenRouter for Perplexity Sonar
        self.client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,  # Use OpenRouter key
            base_url=config.OPENROUTER_BASE_URL,
            http_client=http_client
        )
    
    def analyze_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Analyze multiple leads and add pain points to each
        Only analyzes Apify Google Places leads (companies with websites)
        
        Args:
            leads: List of lead dictionaries with website information
            
        Returns:
            Updated leads list with pain_points added
        """
        if not self.client:
            print("⚠️  Skipping pain point analysis - Perplexity not configured")
            return leads
        
        # Filter to only Apify Google Places leads
        apify_leads = [l for l in leads if l.get('source') == 'apify_google_places']
        other_leads = [l for l in leads if l.get('source') != 'apify_google_places']
        
        if not apify_leads:
            print("⚠️  No Apify Google Places leads found - skipping pain point analysis")
            return leads
        
        print(f"\n🔍 Analyzing {len(apify_leads)} Google Places companies for pain points using Perplexity Sonar...")
        
        analyzed_apify_leads = []
        for i, lead in enumerate(apify_leads, 1):
            website = lead.get('website') or lead.get('raw_data', {}).get('website')
            company_name = lead.get('company') or lead.get('name')
            
            if website and company_name:
                print(f"   [{i}/{len(apify_leads)}] Analyzing {company_name}...")
                analysis_result = self._analyze_website(company_name, website)
                
                # Extract pain points and LinkedIn data
                pain_points = analysis_result.get('pain_points', [])
                linkedin_data = analysis_result.get('linkedin_data', {})
                
                lead['pain_points'] = pain_points
                lead['pain_points_summary'] = self._summarize_pain_points(pain_points)
                
                # Add LinkedIn data to lead
                if linkedin_data.get('company_linkedin'):
                    lead['company_linkedin'] = linkedin_data['company_linkedin']
                    print(f"      ✅ Found company LinkedIn: {linkedin_data['company_linkedin']}")
                
                if linkedin_data.get('prospect_linkedins'):
                    lead['prospect_linkedins'] = linkedin_data['prospect_linkedins']
                    print(f"      ✅ Found {len(linkedin_data['prospect_linkedins'])} prospect LinkedIn profiles")
            else:
                print(f"   [{i}/{len(apify_leads)}] Skipping {company_name or 'Unknown'} - no website")
                lead['pain_points'] = []
                lead['pain_points_summary'] = "No website available for analysis"
            
            analyzed_apify_leads.append(lead)
        
        print(f"✅ Pain point analysis completed for {len(analyzed_apify_leads)} companies\n")
        
        # Combine analyzed Apify leads with other leads (no pain points)
        for lead in other_leads:
            lead['pain_points'] = []
            lead['pain_points_summary'] = "N/A (email contact only)"
        
        return analyzed_apify_leads + other_leads
    
    def _verify_linkedin_url(self, url: str) -> bool:
        """
        Verify if a LinkedIn URL is valid
        
        Args:
            url: LinkedIn URL to verify
            
        Returns:
            True if URL format is valid, False otherwise
        """
        try:
            # Basic format check
            if not url:
                return False
                
            if not url.startswith('http'):
                url = f"https://{url}"
            
            parsed = urlparse(url)
            if 'linkedin.com' not in parsed.netloc.lower():
                return False
            
            # Check if it's a valid LinkedIn profile/company pattern
            valid_patterns = ['/in/', '/company/', '/school/', '/showcase/']
            if not any(pattern in url.lower() for pattern in valid_patterns):
                return False
            
            # Format validation: must have something after the pattern
            path = parsed.path.lower()
            for pattern in valid_patterns:
                if pattern in path:
                    slug = path.split(pattern)[1].strip('/')
                    # Must have actual slug (at least 2 chars)
                    if slug and len(slug) >= 2:
                        return True
            
            return False
                
        except Exception as e:
            print(f"      LinkedIn URL validation error: {e}")
            return False
    
    def _analyze_website(self, company_name: str, website: str) -> Dict:
        """
        Analyze a company's website to identify pain points
        
        Args:
            company_name: Name of the company
            website: Company website URL
            
        Returns:
            List of identified pain points with categories
        """
        try:
            prompt = f"""Analyze the company {company_name} (website: {website}) and provide:

1. LINKEDIN PROFILES - Search and find:
   - Company LinkedIn page: linkedin.com/company/[company-slug]
   - Key executives with LinkedIn profiles (CEO, Founder, CTO, VP, etc.)
   
   IMPORTANT: Search LinkedIn directly for "{company_name}" to find their actual company page.
   For executives, search "{company_name} CEO LinkedIn" or similar.
   
2. BUSINESS PAIN POINTS from their website/online presence:
   - Operational challenges (efficiency, scalability, automation)
   - Technology gaps (outdated systems, missing tools)
   - Market challenges (competition, customer acquisition)
   - Resource constraints (budget, staffing)
   - Customer experience issues

Return ONLY valid JSON (no markdown, no extra text):
{{
    "company_linkedin": "https://linkedin.com/company/exact-slug",
    "prospect_linkedins": [
        {{
            "name": "Full Name",
            "title": "Job Title",
            "linkedin_url": "https://linkedin.com/in/profile-slug"
        }}
    ],
    "pain_points": [
        {{
            "category": "Operational|Technology|Market|Resources|Customer Experience",
            "issue": "Brief description",
            "severity": "High|Medium|Low",
            "evidence": "What indicates this problem"
        }}
    ],
    "opportunities": ["Potential solutions"]
}}

CRITICAL: Search LinkedIn and the web to find REAL LinkedIn URLs. Do not guess or fabricate URLs. If you cannot find a LinkedIn profile, leave the field empty or null."""

            response = self.client.chat.completions.create(
                model=config.PERPLEXITY_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business analyst expert at identifying pain points from company websites and online presence. You also excel at finding LinkedIn profiles for companies and their key decision-makers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            import json
            json_match = re.search(r'\{[\s\S]*\}', content)

            if json_match:
                data = json.loads(json_match.group())
                pain_points = data.get('pain_points', [])
                opportunities = data.get('opportunities', [])
                
                # Extract LinkedIn profiles
                company_linkedin = data.get('company_linkedin', '')
                prospect_linkedins = data.get('prospect_linkedins', [])
                
                print(f"      🔍 Raw LinkedIn data extracted:")
                print(f"         Company: {company_linkedin}")
                print(f"         Prospects: {len(prospect_linkedins)} found")

                # Add opportunities to pain points
                for opp in opportunities[:3]:  # Limit to 3 opportunities
                    pain_points.append({
                        'category': 'Opportunity',
                        'issue': opp,
                        'severity': 'Medium',
                        'evidence': 'Identified growth opportunity'
                    })

                # Validate any URLs found in evidence fields to guard against hallucinated links
                validated_pain_points = []
                linkedin_data = {
                    'company_linkedin': None,
                    'prospect_linkedins': []
                }
                
                # Verify company LinkedIn URL
                if company_linkedin:
                    print(f"      🔗 Validating company LinkedIn: {company_linkedin}")
                    if self._verify_linkedin_url(company_linkedin):
                        linkedin_data['company_linkedin'] = company_linkedin
                        print(f"         ✅ Valid!")
                    else:
                        print(f"         ❌ Invalid format")
                
                # Verify prospect LinkedIn URLs
                for i, prospect in enumerate(prospect_linkedins):
                    linkedin_url = prospect.get('linkedin_url', '')
                    if linkedin_url:
                        print(f"      🔗 Validating prospect {i+1} LinkedIn: {linkedin_url}")
                        if self._verify_linkedin_url(linkedin_url):
                            linkedin_data['prospect_linkedins'].append(prospect)
                            print(f"         ✅ Valid!")
                        else:
                            print(f"         ❌ Invalid format")
                
                for p in pain_points:
                    evidence = p.get('evidence', '') or ''
                    urls = re.findall(r'https?://[^\s\)\]\']+', evidence)
                    verified_urls = []
                    unverified_urls = []

                    for u in urls:
                        try:
                            # Quick sanity: parse and ensure scheme+netloc
                            parts = urlparse(u)
                            if not parts.scheme or not parts.netloc:
                                raise ValueError('invalid url')

                            # Use httpx to verify the URL responds
                            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                                head = client.head(u)
                                status = head.status_code
                                if status == 405 or status == 400:
                                    # Some servers don't allow HEAD; try GET
                                    get = client.get(u)
                                    status = get.status_code
                                    content_len = len(get.content or b'')
                                else:
                                    content_len = 0

                                if 200 <= status < 400 and (content_len == 0 or content_len > 50):
                                    verified_urls.append(u)
                                else:
                                    unverified_urls.append(u)
                        except Exception:
                            unverified_urls.append(u)

                    # Attach verification results
                    if verified_urls:
                        p['evidence_urls_verified'] = verified_urls
                    if unverified_urls:
                        p['evidence_urls_unverified'] = unverified_urls
                        # annotate evidence to avoid showing unverified links as facts
                        if evidence and not verified_urls:
                            p['evidence'] = f"{evidence} (NOTE: evidence links could not be verified)"

                    validated_pain_points.append(p)

                return {
                    'pain_points': validated_pain_points,
                    'linkedin_data': linkedin_data
                }

            return {
                'pain_points': [],
                'linkedin_data': {'company_linkedin': None, 'prospect_linkedins': []}
            }
            
        except Exception as e:
            print(f"      ⚠️  Error analyzing {company_name}: {e}")
            return [{
                'category': 'Error',
                'issue': f'Analysis failed: {str(e)[:100]}',
                'severity': 'Unknown',
                'evidence': 'Unable to complete analysis'
            }]
    
    def _summarize_pain_points(self, pain_points: List[Dict]) -> str:
        """
        Create a brief summary of pain points
        
        Args:
            pain_points: List of pain point dictionaries
            
        Returns:
            String summary of top pain points
        """
        if not pain_points:
            return "No pain points identified"
        
        # Group by severity
        high_severity = [p for p in pain_points if p.get('severity') == 'High']
        medium_severity = [p for p in pain_points if p.get('severity') == 'Medium']
        
        summary_parts = []
        
        if high_severity:
            summary_parts.append(f"{len(high_severity)} high-priority issues")
        if medium_severity:
            summary_parts.append(f"{len(medium_severity)} medium-priority issues")
        
        if not summary_parts:
            summary_parts.append(f"{len(pain_points)} issues identified")
        
        # Add top issue
        top_issue = pain_points[0].get('issue', '')
        if top_issue:
            summary_parts.append(f"Top: {top_issue[:50]}...")
        
        return " | ".join(summary_parts)
    
    def analyze_single_lead(self, lead: Dict) -> Dict:
        """
        Analyze a single lead for pain points
        
        Args:
            lead: Lead dictionary with website information
            
        Returns:
            Updated lead with pain_points added
        """
        results = self.analyze_leads([lead])
        return results[0] if results else lead


def analyze_pain_points(leads: List[Dict]) -> List[Dict]:
    """
    Convenience function to analyze pain points for a list of leads
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        Updated leads with pain points
    """
    analyzer = PainPointAnalyzer()
    return analyzer.analyze_leads(leads)
