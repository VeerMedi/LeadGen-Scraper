"""
Reddit Scraper using PRAW (Python Reddit API Wrapper)
"""
from typing import List, Dict
import praw
from ..config import config
import re


class RedditScraper:
    """Scrape Reddit for potential leads"""
    
    def __init__(self):
        """Initialize Reddit API client"""
        if config.is_valid_key('REDDIT_CLIENT_ID') and config.is_valid_key('REDDIT_CLIENT_SECRET'):
            try:
                self.reddit = praw.Reddit(
                    client_id=config.REDDIT_CLIENT_ID,
                    client_secret=config.REDDIT_CLIENT_SECRET,
                    user_agent=config.REDDIT_USER_AGENT
                )
            except Exception as e:
                print(f"Reddit API initialization error: {e}")
                self.reddit = None
        else:
            self.reddit = None
    
    def scrape(self, keywords_data: Dict) -> List[Dict]:
        """
        Scrape Reddit for leads
        
        Args:
            keywords_data: Search parameters
            
        Returns:
            List of Reddit leads
        """
        leads = []
        
        if not self.reddit:
            print("Reddit scraping skipped: Reddit API credentials not configured")
            return leads
        
        try:
            # Get relevant subreddits
            subreddits = self._identify_subreddits(keywords_data)
            
            # Search each subreddit
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    leads.extend(self._search_subreddit(subreddit, keywords_data))
                except Exception as e:
                    print(f"Error scraping r/{subreddit_name}: {e}")
            
            # Also do general Reddit search
            leads.extend(self._general_search(keywords_data))
            
            print(f"Reddit: Scraped {len(leads)} leads")
            
        except Exception as e:
            print(f"Reddit scraping error: {e}")
        
        return leads
    
    def _identify_subreddits(self, keywords_data: Dict) -> List[str]:
        """Identify relevant subreddits based on keywords"""
        # Default professional/hiring subreddits
        default_subreddits = [
            'forhire',
            'freelance',
            'jobbit',
            'hiring',
            'digitalnomad'
        ]
        
        # Add industry-specific subreddits
        industry = keywords_data.get('industry', '').lower()
        if 'tech' in industry or 'software' in industry or 'developer' in industry:
            default_subreddits.extend(['programming', 'cscareerquestions', 'webdev'])
        elif 'marketing' in industry:
            default_subreddits.extend(['marketing', 'socialmedia'])
        elif 'design' in industry:
            default_subreddits.extend(['design', 'graphic_design'])
        
        return default_subreddits[:5]  # Limit to 5 subreddits
    
    def _search_subreddit(self, subreddit, keywords_data: Dict) -> List[Dict]:
        """Search within a specific subreddit"""
        leads = []
        
        try:
            # Build search query
            search_terms = ' '.join(keywords_data.get('primary_keywords', []))
            
            # Search posts
            for submission in subreddit.search(search_terms, limit=20, time_filter='month'):
                # Extract lead from post
                lead = self._extract_lead_from_submission(submission)
                if lead:
                    leads.append(lead)
                
                # Also check comments for leads
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list()[:10]:  # Top 10 comments
                    lead = self._extract_lead_from_comment(comment)
                    if lead:
                        leads.append(lead)
        
        except Exception as e:
            print(f"Error searching subreddit: {e}")
        
        return leads
    
    def _general_search(self, keywords_data: Dict) -> List[Dict]:
        """Perform general Reddit search"""
        leads = []
        
        try:
            search_terms = ' '.join(keywords_data.get('primary_keywords', []))
            
            for submission in self.reddit.subreddit('all').search(search_terms, limit=20):
                lead = self._extract_lead_from_submission(submission)
                if lead:
                    leads.append(lead)
        
        except Exception as e:
            print(f"Error in general Reddit search: {e}")
        
        return leads
    
    def _extract_lead_from_submission(self, submission) -> Dict:
        """Extract lead information from Reddit submission"""
        try:
            # Extract contact information from post
            text = f"{submission.title} {submission.selftext}"
            
            email = self._extract_email(text)
            
            if email or submission.author:
                return {
                    'name': str(submission.author) if submission.author else None,
                    'email': email,
                    'phone': None,
                    'linkedin_url': self._extract_linkedin(text),
                    'company': None,
                    'job_title': None,
                    'location': None,
                    'source': 'reddit',
                    'raw_data': {
                        'post_title': submission.title,
                        'post_url': f"https://reddit.com{submission.permalink}",
                        'subreddit': str(submission.subreddit),
                        'score': submission.score,
                        'created_utc': submission.created_utc
                    }
                }
        
        except Exception as e:
            print(f"Error extracting lead from submission: {e}")
        
        return None
    
    def _extract_lead_from_comment(self, comment) -> Dict:
        """Extract lead information from Reddit comment"""
        try:
            text = comment.body
            email = self._extract_email(text)
            
            if email or (comment.author and '@' in text):
                return {
                    'name': str(comment.author) if comment.author else None,
                    'email': email,
                    'phone': None,
                    'linkedin_url': self._extract_linkedin(text),
                    'company': None,
                    'job_title': None,
                    'location': None,
                    'source': 'reddit',
                    'raw_data': {
                        'comment_text': text[:200],  # First 200 chars
                        'comment_url': f"https://reddit.com{comment.permalink}",
                        'score': comment.score
                    }
                }
        
        except Exception as e:
            print(f"Error extracting lead from comment: {e}")
        
        return None
    
    @staticmethod
    def _extract_email(text: str) -> str:
        """Extract email from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    @staticmethod
    def _extract_linkedin(text: str) -> str:
        """Extract LinkedIn URL from text"""
        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[\w-]+'
        matches = re.findall(linkedin_pattern, text)
        return matches[0] if matches else None
