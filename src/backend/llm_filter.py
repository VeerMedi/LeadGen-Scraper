"""
LLM-based Lead Filtering and Quality Assessment
Uses AI to evaluate lead quality, warmth, and sentiment
"""
from typing import List, Dict
from openai import OpenAI
import httpx
import json
import re
from .config import config


class LLMFilter:
    """Filter and score leads using LLM"""
    
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
    
    def filter_and_score_leads(self, leads: List[Dict], batch_size: int = 10, min_quality_threshold: int = 30) -> List[Dict]:
        """
        Filter and score leads using LLM with duplicate detection
        
        Args:
            leads: List of processed leads
            batch_size: Number of leads to process at once
            min_quality_threshold: Minimum quality score (0-100) to keep leads
            
        Returns:
            List of filtered, deduplicated leads with quality scores (0-100)
        """
        print(f"\n{'='*60}")
        print(f"🤖 LLM FILTER: Starting analysis of {len(leads)} leads")
        print(f"{'='*60}")
        
        scored_leads = []
        
        # Process in batches
        total_batches = (len(leads) + batch_size - 1) // batch_size
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            batch_num = i//batch_size + 1
            
            print(f"\n📊 Processing batch {batch_num}/{total_batches} ({len(batch)} leads)...")
            
            try:
                batch_results = self._score_batch(batch)
                scored_leads.extend(batch_results)
                print(f"✅ Batch {batch_num} scored successfully")
            except Exception as e:
                print(f"❌ Error scoring batch {batch_num}: {e}")
                # Add leads with default scores
                for lead in batch:
                    lead['quality_score'] = 50
                    lead['warmth_score'] = 50
                    lead['sentiment'] = 'neutral'
                    scored_leads.append(lead)
        
        print(f"\n🔍 Running duplicate detection on {len(scored_leads)} leads...")
        # Detect duplicates using LLM
        scored_leads = self._detect_duplicates_llm(scored_leads)
        
        # Filter out duplicates and low-quality leads
        filtered_leads = [
            lead for lead in scored_leads 
            if not lead.get('is_duplicate', False) 
            and lead.get('quality_score', 0) >= min_quality_threshold
        ]
        
        # Sort by quality score
        filtered_leads.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        print(f"LLM Filter: {len(leads)} leads → {len(filtered_leads)} after filtering (removed {len(leads) - len(filtered_leads)} duplicates/low-quality)")
        
        return filtered_leads
    
    def _score_batch(self, leads: List[Dict]) -> List[Dict]:
        """Score a batch of leads"""
        # Prepare lead summaries for LLM
        lead_summaries = []
        for idx, lead in enumerate(leads):
            summary = self._create_lead_summary(lead, idx)
            lead_summaries.append(summary)
        
        # Create prompt
        system_prompt = """You are an expert lead qualification analyst. Evaluate each lead based on:
        
        1. **Quality Score (0-100)**: Overall lead quality
           - Data completeness (has email, phone, LinkedIn, etc.) - 40 points
           - Professional relevance (job title, company) - 30 points
           - Information accuracy and detail - 30 points
        
        2. **Warmth Score (0-100)**: How "warm" or ready the lead is
           - Contact accessibility (email/phone available) - 40 points
           - Recent activity or engagement signals - 30 points
           - Professional positioning and approachability - 30 points
        
        3. **Sentiment**: Overall impression
           - 'hot' (80-100): High quality, warm, ready to contact
           - 'warm' (50-79): Good quality, moderate warmth
           - 'cold' (0-49): Low quality or hard to reach
        
        Return a JSON array with scores for each lead."""
        
        user_prompt = f"""Evaluate these leads and provide scores:

{chr(10).join(lead_summaries)}

Return JSON array:
[
  {{
    "lead_index": 0,
    "quality_score": 85,
    "warmth_score": 70,
    "sentiment": "warm",
    "reasoning": "Brief explanation"
  }},
  ...
]"""
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            # Parse response - extract JSON if wrapped in text
            content = response.choices[0].message.content
            json_match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
                result = json.loads(content)
                scores = result if isinstance(result, list) else result.get('scores', result.get('leads', []))
            else:
                # Try parsing the whole content
                result = json.loads(content)
                scores = result.get('scores', result.get('leads', []))
            
            # Apply scores to leads
            print(f"   📋 LLM returned scores for {len(scores)} leads")
            for score_data in scores:
                idx = score_data.get('lead_index', 0)
                if 0 <= idx < len(leads):
                    quality = score_data.get('quality_score', 50)
                    warmth = score_data.get('warmth_score', 50)
                    sentiment = score_data.get('sentiment', 'neutral')
                    
                    leads[idx]['quality_score'] = quality
                    leads[idx]['warmth_score'] = warmth
                    leads[idx]['sentiment'] = sentiment
                    leads[idx]['llm_reasoning'] = score_data.get('reasoning', '')
                    
                    print(f"   Lead {idx}: Quality={quality}, Warmth={warmth}, Sentiment={sentiment}")
            
        except Exception as e:
            print(f"❌ Error in LLM scoring: {e}")
            print(f"   Falling back to rule-based scoring...")
            # Fallback to rule-based scoring
            for lead in leads:
                scores = self._fallback_scoring(lead)
                lead.update(scores)
        
        return leads
    
    def _create_lead_summary(self, lead: Dict, index: int) -> str:
        """Create a concise summary of a lead for LLM evaluation"""
        summary = f"\nLead {index}:"
        
        if lead.get('name'):
            summary += f"\n  Name: {lead['name']}"
        
        if lead.get('job_title'):
            summary += f"\n  Title: {lead['job_title']}"
        
        if lead.get('company'):
            summary += f"\n  Company: {lead['company']}"
        
        if lead.get('email'):
            summary += f"\n  Email: ✓"
        
        if lead.get('phone'):
            summary += f"\n  Phone: ✓"
        
        if lead.get('linkedin_url'):
            summary += f"\n  LinkedIn: ✓"
        
        if lead.get('location'):
            summary += f"\n  Location: {lead['location']}"
        
        summary += f"\n  Source: {lead.get('source', 'unknown')}"
        
        return summary
    
    def _fallback_scoring(self, lead: Dict) -> Dict:
        """Rule-based fallback scoring if LLM fails (0-100 scale)"""
        quality_score = 0
        warmth_score = 0
        
        # Quality score based on data completeness (out of 100)
        if lead.get('name'):
            quality_score += 20
        if lead.get('email'):
            quality_score += 30
        if lead.get('phone'):
            quality_score += 20
        if lead.get('linkedin_url'):
            quality_score += 15
        if lead.get('company'):
            quality_score += 10
        if lead.get('job_title'):
            quality_score += 5
        
        # Warmth score based on contact accessibility (out of 100)
        if lead.get('email'):
            warmth_score += 40
        if lead.get('phone'):
            warmth_score += 30
        if lead.get('linkedin_url'):
            warmth_score += 20
        
        # Platform-based warmth adjustment
        source = lead.get('source', '').lower()
        if 'linkedin' in source:
            warmth_score += 10
        elif 'reddit' in source:
            warmth_score += 5
        
        # Determine sentiment
        avg_score = (quality_score + warmth_score) / 2
        if avg_score >= 80:
            sentiment = 'hot'
        elif avg_score >= 50:
            sentiment = 'warm'
        else:
            sentiment = 'cold'
        
        return {
            'quality_score': min(quality_score, 100),
            'warmth_score': min(warmth_score, 100),
            'sentiment': sentiment
        }
    
    def analyze_lead_sentiment_detailed(self, lead: Dict) -> Dict:
        """
        Perform detailed sentiment analysis on a single lead
        
        Args:
            lead: Lead dictionary
            
        Returns:
            Detailed sentiment analysis
        """
        system_prompt = """Analyze this lead in detail. Provide:
        1. Contact readiness (how easy to reach)
        2. Professional fit (relevance to typical B2B sales)
        3. Engagement potential (likelihood of response)
        4. Red flags (any concerns)
        5. Recommended next steps"""
        
        user_prompt = f"""Analyze this lead:

Name: {lead.get('name', 'N/A')}
Title: {lead.get('job_title', 'N/A')}
Company: {lead.get('company', 'N/A')}
Email: {'Available' if lead.get('email') else 'Not available'}
Phone: {'Available' if lead.get('phone') else 'Not available'}
LinkedIn: {'Available' if lead.get('linkedin_url') else 'Not available'}
Location: {lead.get('location', 'N/A')}
Source: {lead.get('source', 'N/A')}

Provide detailed JSON analysis."""
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            # Parse response - extract JSON if wrapped in text
            content = response.choices[0].message.content
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            analysis = json.loads(content)
            return analysis
            
        except Exception as e:
            print(f"Error in detailed sentiment analysis: {e}")
            return {
                'error': str(e),
                'contact_readiness': 'Unknown',
                'professional_fit': 'Unknown',
                'engagement_potential': 'Unknown'
            }
    
    def _detect_duplicates_llm(self, leads: List[Dict]) -> List[Dict]:
        """Use LLM to detect duplicate leads based on similarity"""
        if len(leads) <= 1:
            return leads
        
        try:
            # Create lead summaries for comparison
            lead_summaries = []
            for idx, lead in enumerate(leads):
                summary = f"{idx}: {lead.get('name', 'N/A')} | {lead.get('email', 'N/A')} | {lead.get('company', 'N/A')} | {lead.get('linkedin_url', 'N/A')}"
                lead_summaries.append(summary)
            
            system_prompt = """You are a duplicate detection expert. Identify duplicate leads based on:
            1. Same email address (definite duplicate)
            2. Same LinkedIn URL (definite duplicate)
            3. Same name AND company (likely duplicate)
            4. Similar names with same contact info (likely duplicate)
            
            Return JSON array of duplicate lead indices. If leads are NOT duplicates, return empty array."""
            
            user_prompt = f"""Identify duplicates among these leads:

{chr(10).join(lead_summaries)}

Return JSON: {{"duplicates": [list of duplicate lead indices to remove]}}
Example: {{"duplicates": [2, 5, 7]}}"""
            
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            result = json.loads(content)
            duplicate_indices = result.get('duplicates', [])
            
            # Mark duplicates
            for idx in duplicate_indices:
                if 0 <= idx < len(leads):
                    leads[idx]['is_duplicate'] = True
            
            print(f"LLM Duplicate Detection: Found {len(duplicate_indices)} duplicates")
            
        except Exception as e:
            print(f"Error in LLM duplicate detection: {e}")
            # Fallback to basic duplicate detection
            seen_emails = set()
            seen_linkedin = set()
            
            for lead in leads:
                email = lead.get('email')
                linkedin = lead.get('linkedin_url')
                
                if email and email in seen_emails:
                    lead['is_duplicate'] = True
                elif linkedin and linkedin in seen_linkedin:
                    lead['is_duplicate'] = True
                else:
                    if email:
                        seen_emails.add(email)
                    if linkedin:
                        seen_linkedin.add(linkedin)
        
        return leads
    
    def get_quality_distribution(self, leads: List[Dict]) -> Dict:
        """Get distribution of lead quality"""
        hot = sum(1 for lead in leads if lead.get('sentiment') == 'hot')
        warm = sum(1 for lead in leads if lead.get('sentiment') == 'warm')
        cold = sum(1 for lead in leads if lead.get('sentiment') == 'cold')
        
        return {
            'hot': hot,
            'warm': warm,
            'cold': cold,
            'total': len(leads)
        }


# Convenience function
def filter_leads_with_llm(leads: List[Dict]) -> List[Dict]:
    """Filter and score leads using LLM"""
    llm_filter = LLMFilter()
    return llm_filter.filter_and_score_leads(leads)
