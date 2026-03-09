# MongoDB Atlas Setup Guide

## 🚀 Setting Up MongoDB Atlas for Your Lead Scraper

### Step 1: Create a MongoDB Atlas Account

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up for a free account
3. Create a new organization (or use existing)
4. Create a new project (e.g., "Lead Scraper")

---

### Step 2: Create a Free Cluster

1. Click **"Build a Database"** or **"Create"**
2. Choose **FREE** tier (M0 Sandbox)
3. Select your preferred cloud provider:
   - AWS, Google Cloud, or Azure
   - Choose a region close to you
4. Cluster name: Use default or rename (e.g., "LeadScraperCluster")
5. Click **"Create Cluster"**
6. Wait 3-5 minutes for cluster creation

---

### Step 3: Set Up Database Access

1. In the left sidebar, go to **"Database Access"**
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Username: `leadscraper` (or your choice)
5. Password: **Auto-generate** or create a strong password
6. **COPY AND SAVE THE PASSWORD** - you'll need it!
7. Database User Privileges: Select **"Read and write to any database"**
8. Click **"Add User"**

---

### Step 4: Set Up Network Access

1. In the left sidebar, go to **"Network Access"**
2. Click **"Add IP Address"**
3. For testing, you can:
   - Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - Or add your current IP address
4. Click **"Confirm"**

⚠️ **For production:** Only whitelist specific IP addresses!

---

### Step 5: Get Your Connection String

1. Go back to **"Database"** in the sidebar
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Driver: **Python**
5. Version: **3.12 or later**
6. Copy the connection string that looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

---

### Step 6: Configure Your Application

1. Open your `.env` file in the project root
2. Replace the MongoDB settings:

```env
# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://leadscraper:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=lead_scraper
```

**Important:** Replace `YOUR_PASSWORD` with the actual password you created!

---

### Step 7: Test Connection

Run the test script to verify MongoDB connection:

```bash
python test_scrapers.py
```

Or test directly:

```python
from pymongo import MongoClient

# Your connection string
uri = "mongodb+srv://leadscraper:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"

# Test connection
client = MongoClient(uri)
db = client['lead_scraper']
print("✅ Connected to MongoDB Atlas!")
client.close()
```

---

## 📊 Database Schema

MongoDB will automatically create these collections:

### `leads` Collection
```javascript
{
  "_id": ObjectId("..."),
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "company": "Tech Corp",
  "job_title": "Software Engineer",
  "location": "San Francisco, CA",
  "source_platform": "linkedin",
  "raw_data": {},
  "quality_score": 0.85,
  "warmth_score": 0.75,
  "sentiment": "hot",
  "is_duplicate": false,
  "query_id": "507f1f77bcf86cd799439011",
  "created_at": ISODate("2024-11-15T10:30:00Z"),
  "updated_at": ISODate("2024-11-15T10:30:00Z")
}
```

### `search_queries` Collection
```javascript
{
  "_id": ObjectId("..."),
  "raw_query": "Software Engineer in San Francisco",
  "extracted_keywords": {
    "primary_keywords": ["software", "engineer"],
    "location": "San Francisco",
    "platforms": ["linkedin", "reddit"]
  },
  "platforms_searched": ["linkedin", "reddit", "google"],
  "total_leads_found": 25,
  "total_leads_filtered": 18,
  "created_at": ISODate("2024-11-15T10:25:00Z")
}
```

---

## 🔍 Viewing Your Data

### Option 1: MongoDB Atlas UI
1. Go to your cluster in MongoDB Atlas
2. Click **"Browse Collections"**
3. Select `lead_scraper` database
4. View `leads` and `search_queries` collections

### Option 2: MongoDB Compass (Desktop App)
1. Download from https://www.mongodb.com/products/compass
2. Use your connection string to connect
3. Browse collections visually

### Option 3: VS Code Extension
1. Install "MongoDB for VS Code" extension
2. Connect using your connection string
3. Browse and query data from VS Code

---

## 🎯 Common Issues & Solutions

### Issue 1: "MongoServerSelectionError"
**Cause:** Can't connect to MongoDB
**Solutions:**
- Check your internet connection
- Verify connection string is correct
- Ensure IP address is whitelisted in Network Access
- Check username/password are correct

### Issue 2: "Authentication failed"
**Cause:** Wrong username or password
**Solutions:**
- Verify password in .env file
- Password must be URL-encoded if it contains special characters
- Recreate database user if needed

### Issue 3: "Database not found"
**Cause:** Database doesn't exist yet
**Solution:** 
- MongoDB creates databases automatically on first write
- Just run the app and it will create `lead_scraper` database

---

## 🔐 Security Best Practices

1. **Never commit .env file** - Already in .gitignore
2. **Use strong passwords** - Generate random passwords
3. **Limit IP access** - Only allow needed IPs in production
4. **Rotate credentials** - Change passwords regularly
5. **Use environment variables** - Never hardcode credentials

---

## 💰 Free Tier Limits

MongoDB Atlas Free Tier (M0):
- ✅ 512 MB storage
- ✅ Shared RAM
- ✅ Shared vCPU
- ✅ No credit card required
- ✅ Perfect for development and small projects

**For your lead scraper:**
- Can store ~50,000 - 100,000 leads
- More than enough for testing and initial use

---

## 📈 Scaling Up (When Needed)

If you need more:
1. Upgrade to M10 cluster ($0.08/hour = ~$57/month)
2. Get 10GB storage + dedicated resources
3. Automatic backups included

---

## ✅ Quick Setup Checklist

- [ ] Create MongoDB Atlas account
- [ ] Create free cluster
- [ ] Add database user
- [ ] Whitelist IP address (0.0.0.0/0 for testing)
- [ ] Copy connection string
- [ ] Update .env file with connection string
- [ ] Update .env with database name (lead_scraper)
- [ ] Test connection with `python test_scrapers.py`
- [ ] Run app with `streamlit run app.py`
- [ ] Verify data is being saved

---

## 🆘 Need Help?

- MongoDB Docs: https://docs.mongodb.com/
- Atlas Docs: https://docs.atlas.mongodb.com/
- Community: https://www.mongodb.com/community/forums/

---

## 🎉 You're Done!

Your lead scraper is now using MongoDB Atlas as the database backend. Start scraping leads and they'll be automatically stored in your cloud database!
