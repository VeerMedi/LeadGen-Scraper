"""
Apify Actor Scraper
Handles scraping through various Apify actors
"""
from typing import List, Dict
from apify_client import ApifyClient
from ..config import config
import time


class ApifyScraper:
    """Use Apify actors for scraping various platforms"""
    
    def __init__(self):
        if config.is_valid_key('APIFY_API_KEY'):
            self.client = ApifyClient(config.APIFY_API_KEY)
        else:
            self.client = None
    
    def scrape(self, keywords_data: Dict, max_results: int = 10) -> List[Dict]:
        """
        Scrape using Apify actors based on query type
        
        Args:
            keywords_data: Search parameters including scrape_type and targets
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            List of leads from Apify actors
        """
        leads = []
        
        if not self.client:
            print("Apify scraping skipped: APIFY_API_KEY not configured")
            return leads
        
        try:
            scrape_type = keywords_data.get('scrape_type', 'search')  # 'search' or 'profile'
            
            if scrape_type == 'profile':
                # Profile scraping mode
                print("👤 Profile Scraping Mode Activated")
                target_platform = keywords_data.get('target_platform', 'linkedin')
                profile_urls = keywords_data.get('profile_urls', [])
                
                if target_platform == 'linkedin':
                    leads.extend(self._scrape_linkedin_profiles(profile_urls))
                elif target_platform == 'instagram':
                    leads.extend(self._scrape_instagram_profiles(profile_urls))
                elif target_platform == 'facebook':
                    leads.extend(self._scrape_facebook_profiles(profile_urls))
                else:
                    print(f"⚠️ Unknown platform: {target_platform}")
            else:
                # Search/hashtag mode (original functionality)
                print("🔍 Search/Hashtag Mode")
                
                # Google Places search (primary method)
                if keywords_data.get('query') or keywords_data.get('industry'):
                    leads.extend(self._scrape_google_places(keywords_data, max_results))
                
                # Instagram hashtag search
                if 'instagram_hashtags' in keywords_data:
                    leads.extend(self._scrape_instagram_hashtags(keywords_data))
                
                # LinkedIn search
                if 'linkedin_search' in keywords_data:
                    leads.extend(self._scrape_linkedin_search(keywords_data))
                
                # Facebook search
                if 'facebook_search' in keywords_data:
                    leads.extend(self._scrape_facebook_posts(keywords_data))
            
            # Ensure we don't exceed max_results
            if len(leads) > max_results:
                print(f"  ✂️  Truncating from {len(leads)} to {max_results} leads")
                leads = leads[:max_results]
            
            print(f"Apify: Scraped {len(leads)} leads")
            
        except Exception as e:
            print(f"Apify scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        return leads[:max_results]  # Final safety check
    
    def _scrape_google_places(self, keywords_data: Dict, max_results: int = 10) -> List[Dict]:
        """
        Scrape Google Places using Apify's compass~crawler-google-places actor
        
        Args:
            keywords_data: Dictionary containing query, industry, location, etc.
            max_results: Maximum number of places to scrape (default: 10)
            
        Returns:
            List of leads from Google Places
        """
        leads = []
        
        try:
            # Build search query
            query_parts = []
            if keywords_data.get('industry'):
                query_parts.append(keywords_data['industry'])
            if keywords_data.get('query'):
                query_parts.append(keywords_data['query'])
            if keywords_data.get('location'):
                query_parts.append(keywords_data['location'])
            
            search_query = ' '.join(query_parts) if query_parts else keywords_data.get('query', 'companies')
            
            print(f"   🗺️  Searching Google Places: '{search_query}'")
            
            # Actor ID from config
            actor_id = config.APIFY_GOOGLE_PLACES_ACTOR
            
            # Input for Google Places Crawler
            run_input = {
                "searchStringsArray": [search_query],
                "maxCrawledPlacesPerSearch": max_results,
                "language": "en",
                "exportPlaceUrls": False,
                "includeWebResults": True,
                "includeHistogram": False,
                "includeOpeningHours": False,
                "includePeopleAlsoSearch": False,
                "maxReviews": 0,
                "maxImages": 0,
                "scrapeReviewerName": False,
                "scrapeReviewerUrl": False,
                "scrapeReviewId": False,
                "scrapeReviewUrl": False,
                "scrapeReviewResponseFromOwnerText": False,
                "scrapeResponseFromOwnerDate": False,
                "oneReviewPerRow": False,
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            print(f"   🚀 Starting Google Places Crawler...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Wait for completion and get results
            print(f"   ⏳ Waiting for results...")
            dataset_items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            print(f"   ✅ Retrieved {len(dataset_items)} places from Google")
            
            # Process results
            for item in dataset_items:
                lead = self._format_google_place_lead(item)
                if lead:
                    leads.append(lead)
            
            print(f"   📊 Formatted {len(leads)} leads from Google Places")
            
        except Exception as e:
            print(f"   ⚠️  Google Places scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        return leads
    
    def _format_google_place_lead(self, place: Dict) -> Dict:
        """
        Format Google Places result into standard lead format
        
        Args:
            place: Raw place data from Google Places API
            
        Returns:
            Formatted lead dictionary
        """
        try:
            # Extract contact information
            phone = place.get('phone') or place.get('phoneNumber') or place.get('phoneUnformatted')
            website = place.get('website') or place.get('url')
            email = place.get('email')
            
            # Extract location
            location_parts = []
            if place.get('city'):
                location_parts.append(place['city'])
            if place.get('state'):
                location_parts.append(place['state'])
            if place.get('countryCode'):
                location_parts.append(place['countryCode'])
            
            location = ', '.join(location_parts) if location_parts else place.get('address', '')
            
            # Build lead
            lead = {
                'name': place.get('title') or place.get('name'),
                'company': place.get('title') or place.get('name'),
                'email': email,
                'phone': phone,
                'website': website,
                'location': location,
                'job_title': 'Business Owner',  # Default for Google Places
                'linkedin_url': None,
                'source': 'apify_google_places',
                'sentiment': self._classify_sentiment(place.get('description', '')),
                'raw_data': {
                    'google_place_id': place.get('placeId'),
                    'address': place.get('address'),
                    'category': place.get('categoryName'),
                    'rating': place.get('totalScore'),
                    'reviews_count': place.get('reviewsCount'),
                    'price_level': place.get('priceLevel'),
                    'description': place.get('description'),
                    'plus_code': place.get('plusCode'),
                    'latitude': place.get('latitude'),
                    'longitude': place.get('longitude'),
                    'hours': place.get('openingHours'),
                    'business_status': place.get('businessStatus'),
                    'verified': place.get('isAdvertisement', False)
                }
            }
            
            # Only return if we have at least name and some contact info
            if lead['name'] and (lead['email'] or lead['phone'] or lead['website']):
                return lead
            
        except Exception as e:
            print(f"   ⚠️  Error formatting Google Place lead: {e}")
        
        return None
    
    def _classify_sentiment(self, text: str) -> str:
        """Simple sentiment classification based on keywords"""
        if not text:
            return 'neutral'
        
        text_lower = text.lower()
        
        # Positive indicators
        positive_keywords = ['award', 'best', 'excellent', 'top', 'leading', 'premier', 
                           'quality', 'professional', 'certified', 'trusted']
        if any(keyword in text_lower for keyword in positive_keywords):
            return 'positive'
        
        # Negative indicators  
        negative_keywords = ['closed', 'out of business', 'bankruptcy', 'liquidation']
        if any(keyword in text_lower for keyword in negative_keywords):
            return 'negative'
        
        return 'neutral'
    
    def _scrape_linkedin_profiles(self, profile_urls: List[str]) -> List[Dict]:
        """Scrape individual LinkedIn profiles"""
        leads = []
        
        if not profile_urls:
            print("   ⚠️ No LinkedIn profile URLs provided")
            return leads
        
        try:
            print(f"   📊 Scraping {len(profile_urls)} LinkedIn profiles...")
            
            # LinkedIn Profile Scraper actor
            actor_id = "apify/linkedin-profile-scraper"
            
            run_input = {
                "startUrls": [{"url": url} for url in profile_urls],
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            print(f"   🚀 Starting LinkedIn Profile Scraper...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            print(f"   ✅ Retrieved {len(dataset_items)} LinkedIn profiles")
            
            for item in dataset_items:
                lead = {
                    'name': item.get('fullName') or item.get('name'),
                    'email': item.get('email'),
                    'phone': item.get('phone'),
                    'linkedin_url': item.get('url') or item.get('profileUrl'),
                    'company': item.get('company') or (item.get('positions', [{}])[0].get('companyName') if item.get('positions') else None),
                    'job_title': item.get('headline') or item.get('title') or (item.get('positions', [{}])[0].get('title') if item.get('positions') else None),
                    'location': item.get('location') or item.get('geoLocationName'),
                    'source': 'apify_linkedin_profile',
                    'raw_data': {
                        'connections': item.get('connectionsCount'),
                        'followers': item.get('followersCount'),
                        'summary': item.get('summary'),
                        'skills': item.get('skills', []),
                        'experience': item.get('positions', []),
                        'education': item.get('schools', [])
                    }
                }
                
                if lead['name'] or lead['linkedin_url']:
                    leads.append(lead)
                    print(f"      ✓ {lead['name']} - {lead['job_title']}")
        
        except Exception as e:
            print(f"   ❌ LinkedIn profile scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        return leads
    
    def _scrape_instagram_profiles(self, profile_urls: List[str]) -> List[Dict]:
        """Scrape individual Instagram profiles"""
        leads = []
        
        if not profile_urls:
            print("   ⚠️ No Instagram profile URLs provided")
            return leads
        
        try:
            print(f"   📸 Scraping {len(profile_urls)} Instagram profiles...")
            
            # Instagram Profile Scraper actor
            actor_id = "shu8hvrXbJbY3Eb9W"
            
            run_input = {
                "directUrls": profile_urls,
                "resultsType": "profiles",
                "resultsLimit": 100,
                "addParentData": True
            }
            
            print(f"   🚀 Starting Instagram Profile Scraper...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            print(f"   ✅ Retrieved {len(dataset_items)} Instagram profiles")
            
            for item in dataset_items:
                lead = {
                    'name': item.get('fullName') or item.get('ownerFullName'),
                    'email': None,
                    'phone': None,
                    'linkedin_url': None,
                    'company': None,
                    'job_title': None,
                    'location': None,
                    'source': 'apify_instagram_profile',
                    'raw_data': {
                        'username': item.get('username') or item.get('ownerUsername'),
                        'bio': item.get('biography'),
                        'followers': item.get('followersCount'),
                        'following': item.get('followsCount'),
                        'posts': item.get('postsCount'),
                        'url': item.get('url'),
                        'is_verified': item.get('verified'),
                        'is_business': item.get('businessCategoryName') is not None,
                        'category': item.get('businessCategoryName'),
                        'external_url': item.get('externalUrl')
                    }
                }
                
                if lead['name']:
                    leads.append(lead)
                    print(f"      ✓ {lead['name']} (@{lead['raw_data']['username']})")
        
        except Exception as e:
            print(f"   ❌ Instagram profile scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        return leads
    
    def _scrape_facebook_profiles(self, profile_urls: List[str]) -> List[Dict]:
        """Scrape individual Facebook profiles"""
        leads = []
        
        if not profile_urls:
            print("   ⚠️ No Facebook profile URLs provided")
            return leads
        
        try:
            print(f"   📘 Scraping {len(profile_urls)} Facebook profiles...")
            
            # Facebook Pages Scraper actor
            actor_id = "apify/facebook-pages-scraper"
            
            run_input = {
                "startUrls": [{"url": url} for url in profile_urls],
                "maxPosts": 10,
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            print(f"   🚀 Starting Facebook Pages Scraper...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            print(f"   ✅ Retrieved {len(dataset_items)} Facebook profiles")
            
            for item in dataset_items:
                lead = {
                    'name': item.get('name') or item.get('pageName'),
                    'email': item.get('email'),
                    'phone': item.get('phone'),
                    'linkedin_url': None,
                    'company': item.get('name'),
                    'job_title': None,
                    'location': item.get('location'),
                    'source': 'apify_facebook_profile',
                    'raw_data': {
                        'page_id': item.get('pageId'),
                        'category': item.get('category'),
                        'likes': item.get('likes'),
                        'followers': item.get('followers'),
                        'about': item.get('about'),
                        'website': item.get('website'),
                        'url': item.get('url')
                    }
                }
                
                if lead['name']:
                    leads.append(lead)
                    print(f"      ✓ {lead['name']}")
        
        except Exception as e:
            print(f"   ❌ Facebook profile scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        return leads
    
    def _scrape_facebook_posts(self, keywords_data: Dict) -> List[Dict]:
        """Scrape Facebook posts based on search keywords"""
        leads = []
        
        try:
            print(f"   📘 Scraping Facebook posts...")
            
            search_terms = keywords_data.get('search_terms', [])
            if not search_terms:
                return leads
            
            actor_id = "apify/facebook-posts-scraper"
            
            run_input = {
                "searchQuery": ' '.join(search_terms[:3]),
                "maxPosts": 20,
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            print(f"   🚀 Starting Facebook Posts Scraper...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            print(f"   ✅ Retrieved {len(dataset_items)} Facebook posts")
            
            for item in dataset_items:
                lead = {
                    'name': item.get('authorName'),
                    'email': None,
                    'phone': None,
                    'linkedin_url': None,
                    'company': None,
                    'job_title': None,
                    'location': None,
                    'source': 'apify_facebook_post',
                    'raw_data': {
                        'post_text': item.get('text'),
                        'post_url': item.get('url'),
                        'likes': item.get('likes'),
                        'comments': item.get('comments'),
                        'shares': item.get('shares'),
                        'timestamp': item.get('timestamp')
                    }
                }
                
                if lead['name']:
                    leads.append(lead)
        
        except Exception as e:
            print(f"   ❌ Facebook posts scraping error: {e}")
        
        return leads
    
    def _scrape_linkedin_search(self, keywords_data: Dict) -> List[Dict]:
        """Search LinkedIn using Sales Navigator"""
        leads = []
        
        try:
            print(f"   💼 Searching LinkedIn...")
            
            search_terms = keywords_data.get('search_terms', [])
            location = keywords_data.get('location')
            
            actor_id = "apify/linkedin-search-scraper"
            
            search_query = ' '.join(search_terms[:3])
            run_input = {
                "searchQuery": search_query,
                "location": location,
                "maxResults": 50,
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            print(f"   🚀 Starting LinkedIn Search...")
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            print(f"   ✅ Retrieved {len(dataset_items)} LinkedIn results")
            
            for item in dataset_items:
                lead = {
                    'name': item.get('name') or item.get('fullName'),
                    'email': item.get('email'),
                    'phone': item.get('phone'),
                    'linkedin_url': item.get('url'),
                    'company': item.get('company'),
                    'job_title': item.get('title') or item.get('headline'),
                    'location': item.get('location'),
                    'source': 'apify_linkedin_search',
                    'raw_data': item
                }
                
                if lead['name'] or lead['linkedin_url']:
                    leads.append(lead)
        
        except Exception as e:
            print(f"   ❌ LinkedIn search error: {e}")
        
        return leads
    
    def _scrape_instagram_hashtags(self, keywords_data: Dict) -> List[Dict]:
        """Scrape Instagram using LLM-generated hashtag search"""
        leads = []
        
        try:
            print("   Running Instagram Scraper actor...")
            print(f"   📋 Keywords data received: {keywords_data.get('search_intent', 'N/A')}")
            
            # Instagram Scraper Actor ID
            actor_id = "shu8hvrXbJbY3Eb9W"
            
            # Use LLM-generated Instagram hashtags
            llm_hashtags = keywords_data.get('instagram_hashtags', [])
            
            if llm_hashtags:
                # Use LLM-generated hashtags
                hashtags = [f"#{tag.strip().lstrip('#')}" for tag in llm_hashtags[:5]]
                print(f"   ✅ Using LLM-generated hashtags: {', '.join(hashtags)}")
            else:
                # Fallback: extract from primary keywords
                primary_keywords = keywords_data.get('primary_keywords', [])
                search_terms = keywords_data.get('search_terms', [])
                
                hashtags = []
                for keyword in (primary_keywords + search_terms)[:5]:
                    hashtag = keyword.strip().lower().replace(' ', '').replace('-', '')
                    if hashtag:
                        hashtags.append(f"#{hashtag}")
                
                print(f"   ⚠️ Fallback hashtags: {', '.join(hashtags) if hashtags else 'None'}")
            
            # Final fallback if no hashtags generated
            if not hashtags:
                hashtags = ["#business", "#entrepreneur", "#startup"]
                print(f"   ⚠️ Using default hashtags: {', '.join(hashtags)}")
            
            # Prepare input - use hashtag search
            run_input = {
                "hashtags": hashtags,
                "resultsType": "posts",
                "resultsLimit": 20,
                "searchType": "hashtag",
                "searchLimit": 5,
                "addParentData": True
            }
            
            # Run the actor
            print(f"   🚀 Starting actor {actor_id}...")
            print(f"   📦 Input: {run_input}")
            
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            print(f"   ✅ Actor run completed!")
            print(f"   📊 Run details: Status={run.get('status')}, ID={run.get('id')}")
            print(f"   📁 Dataset ID: {run.get('defaultDatasetId')}")
            
            # Fetch results from dataset
            print(f"   📥 Fetching results from dataset...")
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            print(f"   ✅ Retrieved {len(dataset_items)} items from Instagram")
            
            if not dataset_items:
                print(f"   ⚠️ WARNING: No items returned from Instagram actor!")
                print(f"   💡 This could mean:")
                print(f"      - Hashtags have no recent posts")
                print(f"      - Instagram rate limiting")
                print(f"      - Actor configuration issue")
            
            # Process results - extract potential leads from posts
            for item in dataset_items:
                # Debug: Print the item structure
                print(f"   🔍 DEBUG: Instagram item keys: {list(item.keys())[:10]}")
                
                # Try different field variations
                username = (item.get('ownerUsername') or 
                           item.get('owner_username') or 
                           item.get('username'))
                
                full_name = (item.get('ownerFullName') or 
                            item.get('owner_full_name') or 
                            item.get('fullName') or 
                            username)
                
                # Extract data from Instagram post
                lead = {
                    'name': full_name,
                    'email': None,  # Instagram doesn't provide emails
                    'phone': None,
                    'linkedin_url': None,
                    'company': None,
                    'job_title': 'Instagram Influencer',
                    'location': item.get('locationName') or item.get('location'),
                    'instagram_handle': username,
                    'followers': item.get('ownerFollowersCount') or item.get('followers'),
                    'source': 'apify_instagram',
                    'sentiment': 'positive',
                    'raw_data': {
                        'username': username,
                        'caption': item.get('caption'),
                        'likes': item.get('likesCount') or item.get('likes'),
                        'comments': item.get('commentsCount') or item.get('comments'),
                        'url': item.get('url') or item.get('shortCode'),
                        'timestamp': item.get('timestamp') or item.get('created_time'),
                        'hashtags': item.get('hashtags', [])
                    }
                }
                
                # Accept leads even without full name (use username as fallback)
                if username:
                    leads.append(lead)
                    print(f"   ✓ Found lead: {full_name or username} (@{username}) - {item.get('ownerFollowersCount', 0)} followers")
        
        except Exception as e:
            print(f"❌ Instagram scraping error: {e}")
            import traceback
            traceback.print_exc()
        
        return leads
    
    def _scrape_linkedin_sales_nav(self, keywords_data: Dict) -> List[Dict]:
        """Scrape LinkedIn Sales Navigator"""
        leads = []
        
        try:
            # Build Sales Navigator search URL
            search_url = self._build_sales_nav_url(keywords_data)
            
            # Actor ID for LinkedIn Sales Navigator
            actor_id = "curious_coder/linkedin-sales-navigator-scraper"
            
            run_input = {
                "searchUrls": [search_url],
                "maxResults": 50,
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            # Process results
            for item in dataset_items:
                lead = {
                    'name': item.get('name') or item.get('fullName'),
                    'email': item.get('email'),
                    'phone': item.get('phone'),
                    'linkedin_url': item.get('profileUrl') or item.get('url'),
                    'company': item.get('company') or item.get('currentCompany'),
                    'job_title': item.get('title') or item.get('headline'),
                    'location': item.get('location'),
                    'source': 'apify_linkedin',
                    'raw_data': item
                }
                
                if lead['name'] or lead['linkedin_url']:
                    leads.append(lead)
        
        except Exception as e:
            print(f"Apify LinkedIn scraping error: {e}")
        
        return leads
    
    def _scrape_google_maps(self, keywords_data: Dict) -> List[Dict]:
        """Scrape Google Maps for local business leads"""
        leads = []
        
        try:
            # Build search query
            query = ' '.join(keywords_data.get('primary_keywords', []))
            location = keywords_data.get('location', '')
            
            # Actor ID for Google Maps scraper
            actor_id = "nwua9Gu5YrADL7ZDj"  # Popular Google Maps scraper
            
            run_input = {
                "searchStringsArray": [f"{query} {location}"],
                "maxCrawledPlacesPerSearch": 20,
                "language": "en",
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            # Process results
            for item in dataset_items:
                lead = {
                    'name': item.get('title') or item.get('name'),
                    'email': item.get('email'),
                    'phone': item.get('phone') or item.get('phoneNumber'),
                    'linkedin_url': None,
                    'company': item.get('title'),
                    'job_title': None,
                    'location': item.get('address') or location,
                    'source': 'apify_google_maps',
                    'raw_data': {
                        'website': item.get('website'),
                        'rating': item.get('rating'),
                        'reviews': item.get('reviewsCount'),
                        'category': item.get('categoryName')
                    }
                }
                
                if lead['name'] and (lead['email'] or lead['phone']):
                    leads.append(lead)
        
        except Exception as e:
            print(f"Apify Google Maps scraping error: {e}")
        
        return leads
    
    def _scrape_twitter(self, keywords_data: Dict) -> List[Dict]:
        """Scrape Twitter/X for leads"""
        leads = []
        
        try:
            query = ' '.join(keywords_data.get('primary_keywords', []))
            
            # Actor ID for Twitter scraper
            actor_id = "heLL6fUofdPgRXZie"  # Twitter scraper
            
            run_input = {
                "searchTerms": [query],
                "maxItems": 50,
                "proxyConfiguration": {
                    "useApifyProxy": True
                }
            }
            
            # Run the actor
            run = self.client.actor(actor_id).call(run_input=run_input)
            
            # Fetch results
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            # Process results (extract leads from tweets/profiles)
            for item in dataset_items:
                # Extract from user profile
                user = item.get('user', {})
                
                lead = {
                    'name': user.get('name'),
                    'email': None,  # Rarely available
                    'phone': None,
                    'linkedin_url': None,
                    'company': None,
                    'job_title': None,
                    'location': user.get('location'),
                    'source': 'apify_twitter',
                    'raw_data': {
                        'twitter_handle': user.get('screen_name'),
                        'twitter_url': f"https://twitter.com/{user.get('screen_name')}",
                        'bio': user.get('description'),
                        'followers': user.get('followers_count')
                    }
                }
                
                if lead['name']:
                    leads.append(lead)
        
        except Exception as e:
            print(f"Apify Twitter scraping error: {e}")
        
        return leads
    
    def _build_sales_nav_url(self, keywords_data: Dict) -> str:
        """Build LinkedIn Sales Navigator search URL"""
        base_url = "https://www.linkedin.com/sales/search/people"
        
        # Build query parameters
        keywords = ' '.join(keywords_data.get('primary_keywords', []))
        
        # Simplified URL (actual implementation would need proper encoding)
        url = f"{base_url}?keywords={keywords}"
        
        if keywords_data.get('location'):
            url += f"&geoUrn={keywords_data['location']}"
        
        return url
