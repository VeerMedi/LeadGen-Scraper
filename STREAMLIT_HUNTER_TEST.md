# Testing Hunter.io in Streamlit Dashboard

## ✅ Dashboard is Live!

**URL:** http://localhost:8502

## 🧪 Quick Test Steps

### Test 1: Basic Domain Search
1. Open http://localhost:8502
2. **In the sidebar:**
   - ✅ Check "Hunter.io (Email Finder)"
   - ❌ Uncheck all other platforms
   - You should see: "📧 Hunter.io: X credits available"

3. **In the main area:**
   - Enter query: **"Find emails at parajohn.com"**
   - Click "🚀 Start Scraping"

4. **Expected Results:**
   - Should find 5-10 leads
   - Each lead shows:
     - ✅ Name (e.g., "Mohammed Ashiq")
     - ✅ Email (e.g., "mohammed@parajohn.com")
     - ✅ Job Title (e.g., "Executive Director")
     - ✅ Company name
     - ✅ Quality score (0-100)
     - ✅ Sentiment (🔥 Hot, 🌤️ Warm, ❄️ Cold)
     - ✅ LinkedIn profile (if available)

### Test 2: Company Name Query
1. Enter query: **"Marketing managers at Shopify"**
2. Click "🚀 Start Scraping"
3. AI will extract "Shopify" → convert to "shopify.com"
4. Should return marketing-related contacts

### Test 3: Natural Language Query
1. Enter query: **"Developers at GitHub"**
2. AI extracts "GitHub" → "github.com"
3. Returns developer contacts

### Test 4: Multiple Platforms
1. **Check:**
   - ✅ Hunter.io
   - ✅ Another platform (e.g., Google or Apify)
2. Enter query: **"Tech leads at Stripe"**
3. Results will combine both platforms

## 📊 What You Should See

### Sidebar Display:
```
🎯 Lead Scraper

Configuration
━━━━━━━━━━━━━━━━━━

Platforms to scrape:
☐ LinkedIn
☐ Reddit  
☐ Google
☐ Apify (Instagram)
☑ Hunter.io (Email Finder)

📧 Hunter.io: 44 credits available

Filters
━━━━━━━━━━━━━━━━━━
Minimum Quality Score: 30
```

### Lead Cards Display:
```
👤 Mohammed Ashiq
💼 Executive Director
🏢 Para John

📧 mohammed@parajohn.com
🔗 LinkedIn Profile

Quality: 94
Warmth: 94
Source: hunter.io
🔥 Hot
```

## 🎯 Test Queries That Work

### Confirmed Working:
- ✅ "Find emails at stripe.com"
- ✅ "Find emails at parajohn.com"
- ✅ "Find emails at embeegroup.com"
- ✅ "Developers at GitHub"
- ✅ "Marketing at Shopify"
- ✅ "Sales team at Salesforce"
- ✅ "Engineers at Google"

### Query Patterns:
```
"Find emails at [domain.com]"
"[Job Title] at [Company]"
"[Department] team at [Company]"
"People working at [domain.com]"
```

## 🔍 Features Enabled

### Hunter.io Features:
- ✅ Domain email discovery
- ✅ AI-powered company extraction
- ✅ Email display in leads table
- ✅ Quality scoring (0-100)
- ✅ Sentiment analysis (Hot/Warm/Cold)
- ✅ LinkedIn profiles
- ✅ Job titles and departments
- ✅ CSV/JSON export with emails

### Dashboard Features:
- ✅ Real-time API credit display
- ✅ Filter by quality score
- ✅ Filter by sentiment
- ✅ Sort by name, quality, warmth
- ✅ Export leads with emails to CSV/JSON
- ✅ MongoDB storage
- ✅ Beautiful lead cards

## ⚠️ Troubleshooting

### "No leads found"
- Make sure you mentioned a company name or domain
- Try explicit domain: "Find emails at stripe.com"
- Check API credits in sidebar

### "No domains found in query"
- Use format: "[something] at [company]"
- Or use explicit domain: "Find emails at [domain.com]"

### Emails not showing
- This is now fixed! Emails should display
- If not, refresh the page (Ctrl+R)

### Credits showing as 0
- Check your Hunter.io dashboard
- Free plan has 25 requests/month
- Upgrades available for more credits

## 🎉 Success Criteria

You should be able to:
- ✅ Enter custom queries naturally
- ✅ See AI extract companies/domains
- ✅ Get 5-10 email leads per query
- ✅ See actual email addresses displayed
- ✅ Export leads with emails to CSV
- ✅ Track remaining API credits
- ✅ Filter and sort results

## 🚀 Next Steps

1. Test with the queries above
2. Try your own company targets
3. Export leads to CSV for outreach
4. Monitor your API credit usage
5. Combine with other platforms for comprehensive results

---

**Dashboard URL:** http://localhost:8502

**Your API Credits:** 44 available

**Ready to find email leads!** 🎯
