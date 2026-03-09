"""
Personalized Outreach Script Generator
Uses Google Gemini Flash via OpenRouter to create customized scripts based on company pain points
"""
from typing import List, Dict
import requests
from backend.config import config


class OutreachScriptGenerator:
    """
    Generate personalized conversation strategies (talk tracks) for each company based on their pain points
    Uses Google Gemini Flash 2.0 via OpenRouter to create strategic sales conversation guides
    """
    
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.base_url = config.OPENROUTER_BASE_URL
        self.model = "google/gemini-2.5-flash-lite"  # Fast, cost-effective model
        
        # Load Hustle House context
        self.hustle_house_context = self._load_hustle_house_overview()
    
    def _load_hustle_house_overview(self) -> str:
        """Load Hustle House overview for context"""
        try:
            with open('HUSTLE_HOUSE_OVERVIEW.md', 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return """
            Hustle House provides:
            - Personal Branding & Social Media Management
            - Lead Generation & Cold Outreach
            - Website Creation & UI/UX Design
            - Content Marketing & SEO
            - Automation SaaS & AI Solutions
            - Custom MVP Development
            
            Software Products: FunctionalityForge, Zenith CRM, LeadStream AI, AetherChain, 
            BizDash, Trend Forecaster AI, MetaAds Automation, Content OS, AI Financial Planning,
            LMS Platform, Elysian CRM
            """
    
    def generate_scripts_for_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Generate personalized conversation strategies (talk tracks) for leads with pain points
        
        Args:
            leads: List of lead dictionaries with pain_points
            
        Returns:
            Updated leads with 'talk_track' field added
        """
        print("\n📝 Generating personalized talk tracks with Gemini Flash...")
        
        leads_with_pain_points = [
            l for l in leads 
            if l.get('pain_points') and len(l.get('pain_points', [])) > 0
        ]
        
        if not leads_with_pain_points:
            print("⚠️  No leads with pain points found")
            return leads
        
        for i, lead in enumerate(leads_with_pain_points, 1):
            company_name = lead.get('company') or lead.get('name', 'Company')
            pain_points = lead.get('pain_points', [])
            
            print(f"   [{i}/{len(leads_with_pain_points)}] Creating script for {company_name}...")
            
            talk_track = self._generate_script(
                company_name=company_name,
                pain_points=pain_points,
                industry=lead.get('raw_data', {}).get('category'),
                website=lead.get('website')
            )
            
            if talk_track:
                lead['talk_track'] = talk_track
                lead['has_talk_track'] = True
                print(f"      ✅ Talk track generated ({len(talk_track)} characters)")
            else:
                lead['talk_track'] = None
                lead['has_talk_track'] = False
                print(f"      ⚠️  Failed to generate talk track")
        
        print(f"✅ Generated talk tracks for {sum(1 for l in leads if l.get('has_talk_track'))} companies\n")
        
        return leads
    
    def _generate_script(self, company_name: str, pain_points: List[Dict], 
                        industry: str = None, website: str = None) -> str:
        """
        Generate a personalized conversation strategy (talk track) using Gemini Flash
        
        Args:
            company_name: Name of the target company
            pain_points: List of pain point dictionaries
            industry: Company industry (optional)
            website: Company website (optional)
            
        Returns:
            Personalized talk track/conversation strategy as string
        """
        try:
            # Format pain points for prompt
            pain_points_text = "\n".join([
                f"- {p.get('category')}: {p.get('issue')} (Severity: {p.get('severity')})"
                for p in pain_points[:5]  # Top 5 pain points
            ])
            
            # Create comprehensive prompt
            prompt = f"""You are an expert sales strategist at Hustle House, a premium digital transformation agency. Create a conversation guide for engaging this prospect.

COMPANY CONTEXT:
{self.hustle_house_context}

TARGET COMPANY:
Company Name: {company_name}
Industry: {industry or 'Not specified'}
Website: {website or 'Not available'}

IDENTIFIED PAIN POINTS:
{pain_points_text}

TASK:
Create a strategic conversation guide (talk track) for engaging this prospect. This is for sales calls, meetings, or in-person conversations.

Structure your response with these sections:

1. **OPENER** (2-3 sentences)
   - How to start the conversation naturally
   - Reference their business/industry to show research
   - Build rapport without being salesy

2. **PAIN POINT DISCUSSION** (3-4 key talking points)
   - For each major pain point, provide:
     * How to bring it up naturally in conversation
     * Questions to ask that uncover the depth of the problem
     * Language that shows understanding without being presumptuous
   
3. **SOLUTION POSITIONING** (2-3 specific recommendations)
   - Match 2-3 Hustle House services/products to their pain points
   - Explain the value in their language (not feature lists)
   - Focus on outcomes and transformation
   
4. **PROOF POINTS** (1-2 brief examples)
   - Relevant results or experiences to build credibility
   - Keep brief and conversational
   
5. **NEXT STEPS** (2-3 options)
   - Soft call-to-action options they can choose
   - No pressure, consultative approach
   - Offer immediate value (audit, consultation, insights)

6. **OBJECTION HANDLING** (2-3 common concerns)
   - Likely objections based on their pain points
   - How to address each one conversationally

TONE & STYLE:
- Consultative, not salesy
- Confident but humble
- Focus on their success, not our services
- Use "you" and "your business" language
- Conversational, like coaching a team member

FORMAT:
Use clear section headers (bolded with **)
Bullet points for easy scanning
Keep total under 400 words
"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://thehustlehouseofficial.com",
                "X-Title": "Hustle House Lead Scraper"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.8,  # Higher for creativity
                "max_tokens": 1000  # Increased for longer talk tracks
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                talk_track = data['choices'][0]['message']['content'].strip()
                return talk_track
            else:
                print(f"      ⚠️  API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"      ⚠️  Error generating script: {str(e)[:100]}")
            return None
    
    def generate_single_script(self, company_name: str, pain_points: List[Dict],
                              industry: str = None, website: str = None) -> str:
        """
        Generate a talk track for a single company (convenience method)
        
        Args:
            company_name: Name of the company
            pain_points: List of pain point dictionaries
            industry: Company industry
            website: Company website
            
        Returns:
            Personalized conversation strategy/talk track
        """
        return self._generate_script(company_name, pain_points, industry, website)


def add_outreach_scripts(leads: List[Dict]) -> List[Dict]:
    """
    Convenience function to add talk tracks (conversation strategies) to leads
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        Updated leads with talk tracks
    """
    generator = OutreachScriptGenerator()
    return generator.generate_scripts_for_leads(leads)
