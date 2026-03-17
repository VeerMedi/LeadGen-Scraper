# 🎯 LeadGen Scraper

An AI-powered lead generation and scraping system built with Python and Streamlit. It automatically discovers, qualifies, and scores potential leads from multiple platforms using LLM-based intelligence.

---

## 📌 Overview

LeadGen Scraper lets you find qualified leads by entering plain-language queries or profile URLs. The system automatically classifies your intent (search mode vs. profile scraping mode), routes requests to the appropriate platforms, filters results with an AI quality score, and saves everything to MongoDB Atlas.

**Built by [Hustle House](https://hustlehouse.app) for B2B lead generation workflows.**

---

## ✨ Features

- **🤖 Smart Query Classification** — AI automatically detects whether you want a broad keyword search or to scrape specific profile URLs.
- **🔍 Multi-Platform Scraping** — LinkedIn, Reddit, Google, Apify (Google Places), Hunter.io.
- **👤 Profile Scraping Mode** — Directly scrape LinkedIn, Instagram, and Facebook profiles by URL.
- **📊 AI Lead Scoring** — Every lead is scored 0–100 and classified as 🔥 Hot, 🌤 Warm, or ❄️ Cold using an LLM.
- **📧 Email Discovery** — Hunter.io integration for email lookup and verification.
- **🏢 Business Search** — Apify Google Places integration for finding companies by location and industry.
- **💾 Persistent Storage** — All results saved to MongoDB Atlas for future reference.
- **📥 CSV Export** — Download scraped leads as a CSV file directly from the UI.
- **⚙️ Configurable Filters** — Set minimum quality score, max results per platform, and choose which platforms to use.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| Language | Python 3.10+ |
| Database | [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) |
| LLM / AI | [OpenRouter](https://openrouter.ai) (Nvidia Nemotron by default) |
| Scraping | [Apify](https://apify.com), PRAW (Reddit), BeautifulSoup, Requests |
| Email Lookup | [Hunter.io](https://hunter.io) |
| Contact Enrichment | ContactOut (optional) |
| Environment | python-dotenv |

---

## 📂 Project Structure

```
LeadGen-Scraper/
├── app.py                      # Streamlit application entry point
├── requirements.txt            # Python dependencies
├── src/
│   └── backend/
│       ├── config.py           # Centralized configuration & env vars
│       ├── keyword_extractor.py
│       ├── query_classifier.py # LLM-based query intent detection
│       ├── scrapers/
│       │   ├── apify_scraper.py    # Google Places via Apify
│       │   ├── google_scraper.py
│       │   ├── hunter_scraper.py   # Email discovery
│       │   ├── linkedin_scraper.py
│       │   └── reddit_scraper.py
│       ├── data_processor.py
│       ├── llm_filter.py       # AI lead scoring & sentiment
│       ├── database_mongodb.py # MongoDB Atlas integration
│       ├── contact_enrichment.py
│       ├── contactout_enricher.py
│       ├── pain_point_analyzer.py
│       └── script_generator.py
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- A [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster (free tier works)
- An [OpenRouter](https://openrouter.ai) API key (required)
- Optional API keys: Apify, Hunter.io, ContactOut, Perplexity, Reddit, Google

### 1. Clone the repository

```bash
git clone https://github.com/VeerMedi/LeadGen-Scraper.git
cd LeadGen-Scraper
```

### 2. Create a virtual environment & install dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Required
OPENROUTER_API_KEY=your_openrouter_key_here
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/leadscraper?retryWrites=true&w=majority

# Optional — enable platforms as needed
APIFY_API_KEY=your_apify_key_here
HUNTER_API_KEY=your_hunter_key_here
CONTACTOUT_API_KEY=your_contactout_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here

# Reddit (for Reddit scraping)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=LeadScraper/1.0

# Google Custom Search (for Google scraping)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# LinkedIn credentials (for LinkedIn scraping)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# LLM customisation (optional)
LLM_MODEL=nvidia/nemotron-nano-9b-v2:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 4. Run the application

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**.

---

## 💡 Usage

### Search Mode

Enter a natural-language query in the text box and select the platforms you want to scrape from the sidebar. The AI will extract keywords and run searches across your chosen platforms.

**Example queries:**
- `Python developers in San Francisco`
- `Marketing agencies in New York`
- `Find emails at stripe.com`
- `SaaS companies offering HR tools`

### Profile Scraping Mode

Paste one or more profile URLs (LinkedIn, Instagram, or Facebook) directly into the query box. The AI will detect the URLs and switch to profile mode automatically.

**Example inputs:**
- `https://www.linkedin.com/in/username`
- `https://www.instagram.com/companyname`

### Lead Results

Each lead is displayed with:
- Name, company, and contact details
- Quality score (0–100)
- Sentiment classification (Hot / Warm / Cold)
- Source platform

Use the **Download as CSV** button to export results.

---

## 📖 Additional Guides

| Guide | Description |
|---|---|
| [MONGODB_SETUP.md](MONGODB_SETUP.md) | Step-by-step MongoDB Atlas cluster setup |
| [HOSTINGER_VPS_DEPLOYMENT.md](HOSTINGER_VPS_DEPLOYMENT.md) | Full VPS deployment with Nginx + Supervisor |
| [HUNTER_USAGE_GUIDE.md](HUNTER_USAGE_GUIDE.md) | How to use Hunter.io for email discovery |
| [CONTACTOUT_API_KEY_GUIDE.md](CONTACTOUT_API_KEY_GUIDE.md) | Obtaining and using a ContactOut API key |
| [PROFILE_SCRAPING_GUIDE.md](PROFILE_SCRAPING_GUIDE.md) | Profile scraping mode walkthrough |
| [HUSTLE_HOUSE_OVERVIEW.md](HUSTLE_HOUSE_OVERVIEW.md) | Overview of Hustle House services and products |

---

## 🔒 Security Notes

- Never commit your `.env` file — it is already listed in `.gitignore`.
- For production deployments, restrict MongoDB Atlas network access to your server's IP only.
- Rotate API keys regularly and use environment-specific keys for staging vs. production.

---

## 👤 Author

**Krishna Jaiswal** — [Hustle House](https://hustlehouse.app)  
For inquiries or support: [contact@hustlehouse.com](mailto:contact@hustlehouse.com)
