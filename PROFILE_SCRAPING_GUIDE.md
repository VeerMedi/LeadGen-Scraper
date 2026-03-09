# Profile Scraping Guide

## Overview
The Lead Scraper System now supports **two distinct scraping modes**:

1. **🔍 Search/Hashtag Mode** - Find leads by keywords and hashtags (original functionality)
2. **👤 Profile Scraping Mode** - Scrape specific profile URLs directly (NEW)

## Profile Scraping Mode

### Supported Platforms
- **LinkedIn** - Individual profile scraping
- **Instagram** - Individual profile scraping  
- **Facebook** - Page/profile scraping

### How to Use

1. **Select Profile Scraping Mode**
   - Open the app at `http://localhost:8501`
   - Choose "👤 Profile Scraping Mode" from the radio buttons

2. **Choose Platform**
   - Select LinkedIn, Instagram, or Facebook from the dropdown

3. **Enter Profile URLs**
   - Paste profile URLs (one per line) in the text area
   - Examples:
     ```
     https://www.linkedin.com/in/johndoe/
     https://www.linkedin.com/in/janedoe/
     https://www.instagram.com/username/
     https://www.facebook.com/pagename/
     ```

4. **Start Scraping**
   - Click "🚀 Scrape Profiles"
   - The system will:
     - Validate all URLs
     - Use Apify actors to scrape each profile
     - Extract detailed information
     - Score lead quality (0-100)
     - Save to MongoDB

### What Gets Scraped

#### LinkedIn Profiles
- Full name
- Email (if available)
- Phone number (if available)
- Company/headline
- Connections count
- Followers count
- Skills
- Experience history
- Education

#### Instagram Profiles
- Username
- Full name
- Bio/description
- Followers count
- Following count
- Post count
- Verified status
- Business category (if business account)
- Contact info (if available)

#### Facebook Pages/Profiles
- Page name
- Email (if available)
- Phone (if available)
- Location/address
- Likes count
- Followers count
- About/description
- Website
- Category

## Technical Details

### Apify Actors Used

**LinkedIn Profile Scraper**
- Actor: `apify/linkedin-profile-scraper`
- Input: List of profile URLs
- Max profiles: 10 per run (can be adjusted)

**Instagram Profile Scraper**  
- Actor: `shu8hvrXbJbY3Eb9W`
- Input: List of profile URLs
- Results type: "profiles"
- Max profiles: 10 per run

**Facebook Pages Scraper**
- Actor: `apify/facebook-pages-scraper`
- Input: List of page URLs
- Max pages: 10 per run

### Code Architecture

**Backend Flow:**
```
app.py (UI)
    ↓
keywords_data with scrape_type='profile'
    ↓
scrapers/__init__.py (orchestrator)
    ↓
apify_scraper.py
    ↓
Apify actors → raw data
    ↓
data_processor.py (cleaning)
    ↓
llm_filter.py (scoring 0-100)
    ↓
database.py (MongoDB)
```

**Key Files Modified:**
- `app.py` - Added profile mode UI and validation
- `src/backend/scrapers/apify_scraper.py` - Added profile scraping methods
- Profile mode uses same LLM scoring and duplicate detection as search mode

## Search/Hashtag Mode (Original)

Still fully functional! This mode:
- Extracts keywords using LLM
- Searches across multiple platforms (LinkedIn, Reddit, Google, Instagram)
- Finds leads via hashtags, search queries, and content matching
- Best for broad lead generation

## Quality Scoring

Both modes use the same **0-100 quality scoring system**:
- **🔥 Hot (80-100)** - Highly relevant, immediate potential
- **🌤️ Warm (50-79)** - Good fit, worth nurturing
- **❄️ Cold (0-49)** - Lower priority, background research

Minimum quality threshold can be set in the sidebar (default: 30)

## Best Practices

### Profile Scraping
- ✅ Scrape profiles you've identified through other means (conferences, referrals, etc.)
- ✅ Use for targeted, high-value prospect lists
- ✅ Ideal for account-based marketing (ABM)
- ✅ Verify URLs are publicly accessible
- ⚠️ Start with small batches (5-10 profiles) to test

### Search/Hashtag Mode
- ✅ Use for broad market research
- ✅ Find leads matching specific criteria
- ✅ Discover trending topics and influencers
- ✅ Monitor multiple platforms simultaneously

## Rate Limits & Costs

**Apify Usage:**
- Profile scraping consumes Apify compute units
- LinkedIn: ~0.1-0.2 compute units per profile
- Instagram: ~0.05-0.1 compute units per profile
- Facebook: ~0.1-0.2 compute units per page

**Free tier:** 5 USD (~500 compute units) per month
**Monitor usage:** https://console.apify.com/account/usage

## Troubleshooting

**No data returned:**
- Verify profile URLs are public (not private accounts)
- Check Apify API key is valid
- Ensure sufficient compute units remain

**Quality scores low:**
- Profile scraping extracts raw data - scores depend on profile completeness
- Adjust minimum quality threshold in sidebar

**Scraping fails:**
- Check console logs for specific actor errors
- Some profiles may be blocked or restricted
- Try reducing batch size

## Future Enhancements

Planned features:
- [ ] Bulk CSV upload of profile URLs
- [ ] Twitter/X profile scraping
- [ ] GitHub profile scraping
- [ ] Automated enrichment (find email/phone from profile data)
- [ ] Profile monitoring (detect changes over time)

## Support

For issues or questions:
1. Check console logs in terminal
2. Review `FIXES_APPLIED.md` for known issues
3. Verify `.env` configuration
4. Test with single profile first
