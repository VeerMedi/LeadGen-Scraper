"""
Data Processing Pipeline
Handles data cleaning, deduplication, and normalization
"""
from typing import List, Dict, Set
import pandas as pd
import re
from datetime import datetime


class DataProcessor:
    """Process and clean scraped lead data"""
    
    def __init__(self):
        self.seen_emails: Set[str] = set()
        self.seen_linkedin_urls: Set[str] = set()
    
    def process_leads(self, raw_leads: List[Dict]) -> List[Dict]:
        """
        Process raw leads through cleaning and deduplication pipeline
        
        Args:
            raw_leads: List of raw lead dictionaries
            
        Returns:
            List of cleaned and deduplicated leads
        """
        # Step 1: Clean data
        cleaned_leads = [self._clean_lead(lead) for lead in raw_leads]
        
        # Step 2: Remove invalid leads
        valid_leads = [lead for lead in cleaned_leads if self._is_valid_lead(lead)]
        
        # Step 3: Deduplicate
        deduplicated_leads = self._deduplicate_leads(valid_leads)
        
        # Step 4: Normalize data
        normalized_leads = [self._normalize_lead(lead) for lead in deduplicated_leads]
        
        print(f"Data Processing: {len(raw_leads)} raw → {len(normalized_leads)} processed leads")
        
        return normalized_leads
    
    def _clean_lead(self, lead: Dict) -> Dict:
        """Clean individual lead data"""
        cleaned = lead.copy()
        
        # Clean name
        if cleaned.get('name'):
            cleaned['name'] = self._clean_name(cleaned['name'])
        
        # Clean email
        if cleaned.get('email'):
            cleaned['email'] = self._clean_email(cleaned['email'])
        
        # Clean phone
        if cleaned.get('phone'):
            cleaned['phone'] = self._clean_phone(cleaned['phone'])
        
        # Clean LinkedIn URL
        if cleaned.get('linkedin_url'):
            cleaned['linkedin_url'] = self._clean_linkedin_url(cleaned['linkedin_url'])
        
        # Clean company
        if cleaned.get('company'):
            cleaned['company'] = cleaned['company'].strip()
        
        # Clean job title
        if cleaned.get('job_title'):
            cleaned['job_title'] = cleaned['job_title'].strip()
        
        # Clean location
        if cleaned.get('location'):
            cleaned['location'] = cleaned['location'].strip()
        
        return cleaned
    
    def _is_valid_lead(self, lead: Dict) -> bool:
        """Validate lead has minimum required information"""
        # Must have at least name and one contact method
        has_name = bool(lead.get('name'))
        has_contact = bool(lead.get('email') or lead.get('phone') or lead.get('linkedin_url'))
        
        # Email validation if present
        if lead.get('email'):
            if not self._is_valid_email(lead['email']):
                return False
        
        return has_name and has_contact
    
    def _deduplicate_leads(self, leads: List[Dict]) -> List[Dict]:
        """Remove duplicate leads based on email and LinkedIn URL"""
        unique_leads = []
        duplicate_ids = []
        
        for lead in leads:
            email = lead.get('email')
            linkedin = lead.get('linkedin_url')
            
            # Check for duplicates
            is_duplicate = False
            
            if email and email in self.seen_emails:
                is_duplicate = True
            
            if linkedin and linkedin in self.seen_linkedin_urls:
                is_duplicate = True
            
            if not is_duplicate:
                # Add to unique leads
                unique_leads.append(lead)
                
                # Mark as seen
                if email:
                    self.seen_emails.add(email)
                if linkedin:
                    self.seen_linkedin_urls.add(linkedin)
            else:
                # Mark as duplicate for database
                lead['is_duplicate'] = True
                if 'id' in lead:
                    duplicate_ids.append(lead['id'])
        
        return unique_leads
    
    def _normalize_lead(self, lead: Dict) -> Dict:
        """Normalize lead data formats"""
        normalized = lead.copy()
        
        # Ensure all expected fields exist
        fields = ['name', 'email', 'phone', 'linkedin_url', 'company', 
                 'job_title', 'location', 'source', 'raw_data']
        
        for field in fields:
            if field not in normalized:
                normalized[field] = None
        
        # Add metadata
        normalized['processed_at'] = datetime.utcnow().isoformat()
        
        return normalized
    
    @staticmethod
    def _clean_name(name: str) -> str:
        """Clean and normalize name"""
        if not name:
            return None
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Title case
        name = name.title()
        
        # Remove special characters (keep letters, spaces, hyphens, apostrophes)
        name = re.sub(r"[^a-zA-Z\s\-']", '', name)
        
        return name.strip()
    
    @staticmethod
    def _clean_email(email: str) -> str:
        """Clean and normalize email"""
        if not email:
            return None
        
        # Lowercase and strip
        email = email.lower().strip()
        
        # Remove any surrounding brackets or quotes
        email = email.strip('[]()<>"\'')
        
        return email if '@' in email else None
    
    @staticmethod
    def _clean_phone(phone: str) -> str:
        """Clean and normalize phone number"""
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        return cleaned if len(cleaned) >= 10 else None
    
    @staticmethod
    def _clean_linkedin_url(url: str) -> str:
        """Clean and normalize LinkedIn URL"""
        if not url:
            return None
        
        # Ensure it's a proper LinkedIn URL
        if 'linkedin.com/in/' not in url:
            return None
        
        # Extract the profile slug
        match = re.search(r'linkedin\.com/in/([\w-]+)', url)
        if match:
            slug = match.group(1)
            return f"https://www.linkedin.com/in/{slug}"
        
        return url
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
        
        # Exclude common invalid patterns
        invalid_patterns = ['noreply', 'no-reply', 'example.com', 'test@']
        
        for pattern in invalid_patterns:
            if pattern in email.lower():
                return False
        
        return True
    
    def reset(self):
        """Reset seen leads (for new search session)"""
        self.seen_emails.clear()
        self.seen_linkedin_urls.clear()
    
    def get_duplicates_report(self) -> Dict:
        """Get report on duplicates found"""
        return {
            'unique_emails': len(self.seen_emails),
            'unique_linkedin_profiles': len(self.seen_linkedin_urls)
        }
