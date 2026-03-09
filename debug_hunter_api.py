"""
Debug script to see raw Hunter.io API response
"""
import sys
from pathlib import Path
import requests
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from backend.config import config

def debug_api_response(domain="stripe.com"):
    """See raw API response from Hunter.io"""
    
    api_key = config.HUNTER_API_KEY
    
    if not api_key or not config.is_valid_key('HUNTER_API_KEY'):
        print("❌ No valid API key found!")
        return
    
    print(f"🔍 Testing Hunter.io API with domain: {domain}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print("\n" + "=" * 60)
    
    params = {
        'domain': domain,
        'api_key': api_key,
        'limit': 3  # Just get 3 to see structure
    }
    
    try:
        response = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params=params,
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ SUCCESS! Here's the raw response:\n")
            print(json.dumps(data, indent=2))
            
            # Check email structure
            if 'data' in data and 'emails' in data['data']:
                emails = data['data']['emails']
                print(f"\n\n📧 Found {len(emails)} emails. First email structure:")
                if emails:
                    first_email = emails[0]
                    print("\nFields in email object:")
                    for key, value in first_email.items():
                        print(f"  {key}: {value}")
                    
                    # Check for email address
                    email_address = first_email.get('value') or first_email.get('email')
                    print(f"\n✉️  Email Address Field: {email_address}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    domain = input("Enter domain to test (default: stripe.com): ").strip()
    if not domain:
        domain = "stripe.com"
    
    debug_api_response(domain)
