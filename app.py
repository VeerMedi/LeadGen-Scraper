import streamlit as st
import sys
import os
from pathlib import Path

# Disable proxy settings for OpenAI/OpenRouter
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from backend.keyword_extractor import extract_keywords
from backend.scrapers import scrape_leads
from backend.data_processor import DataProcessor
from backend.llm_filter import filter_leads_with_llm
from backend.database_mongodb import MongoDBManager
from backend.config import config
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Lead Scraper System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .lead-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
    }
    .hot { background-color: #ffebee; border-left: 4px solid #f44336; }
    .warm { background-color: #fff3e0; border-left: 4px solid #ff9800; }
    .cold { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
    .metric-card {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'leads' not in st.session_state:
    st.session_state.leads = []
if 'query_id' not in st.session_state:
    st.session_state.query_id = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Sidebar
with st.sidebar:
    st.title("🎯 Lead Scraper")
    st.markdown("---")
    
    st.subheader("Configuration")
    
    # Platform selection
    st.write("**Platforms to scrape:**")
    use_linkedin = st.checkbox("LinkedIn", value=False)
    use_reddit = st.checkbox("Reddit", value=False)
    use_google = st.checkbox("Google", value=False)
    use_apify = st.checkbox("Apify (Google Places)", value=True, help="Google Places business search - find companies by location and industry")
    use_hunter = st.checkbox("Hunter.io (Email Finder)", value=True, help="Email discovery and verification")
    
    # Results limit
    st.markdown("---")
    max_results = st.slider("Maximum results per platform", 5, 50, 10, 5, help="Limit results to reduce API costs")
    
    st.markdown("---")
    # Hunter.io quota display
    if use_hunter and config.is_valid_key('HUNTER_API_KEY'):
        try:
            from backend.scrapers.hunter_scraper import HunterScraper
            hunter = HunterScraper()
            account_info = hunter.get_account_info()
            if account_info:
                requests_available = account_info.get('requests_available', 0)
                st.info(f"📧 Hunter.io: {requests_available} credits available")
        except:
            pass
    
    # Filters
    st.subheader("Filters")
    min_quality = st.slider("Minimum Quality Score", 0, 100, 30, 5, help="Scores range from 0-100")
    
    # Stats
    if st.session_state.leads:
        st.markdown("---")
        st.subheader("Current Results")
        st.metric("Total Leads", len(st.session_state.leads))
        
        hot = sum(1 for l in st.session_state.leads if l.get('sentiment') == 'hot')
        warm = sum(1 for l in st.session_state.leads if l.get('sentiment') == 'warm')
        cold = sum(1 for l in st.session_state.leads if l.get('sentiment') == 'cold')
        
        st.write(f"🔥 Hot: {hot}")
        st.write(f"🌤️ Warm: {warm}")
        st.write(f"❄️ Cold: {cold}")

# Main content
st.title("🎯 Lead Scraper System")
st.markdown("Find and qualify leads from multiple platforms using AI")

# Unified query input
st.markdown("### 🤖 Smart Query Input")
st.info("💡 Enter anything: search queries, keywords, hashtags, or profile URLs. AI will automatically detect what you want!")

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_area(
        "Enter your query",
        placeholder="Examples:\n• Python developers in San Francisco\n• Marketing agencies in NYC\n• https://linkedin.com/in/username\n• instagram.com/companyname",
        height=120,
        key="unified_query"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    st.write("")  # Spacing
    start_button = st.button("🚀 Start Scraping", type="primary", use_container_width=True)

# Processing pipeline
if start_button:
    if not query or not query.strip():
        st.error("Please enter a query or URL")
        st.stop()
    
    # Classify query using LLM
    with st.spinner("🤖 Analyzing your query..."):
        from backend.query_classifier import classify_query
        classification = classify_query(query.strip())
    
    # Display classification result
    mode_emoji = "👤" if classification['mode'] == 'profile' else "🔍"
    confidence_pct = int(classification['confidence'] * 100)
    
    st.success(f"{mode_emoji} Detected: **{classification['mode'].upper()} MODE** (Confidence: {confidence_pct}%)")
    if classification.get('reasoning'):
        st.caption(f"💭 {classification['reasoning']}")
    
    # Set mode variables
    is_profile_mode = classification['mode'] == 'profile'
    
    if is_profile_mode:
        profile_urls = classification['urls']
        profile_platform = classification['platform']
        
        if not profile_urls:
            st.error("No valid URLs detected in your query")
            st.stop()
        
        st.info(f"📋 Found {len(profile_urls)} profile(s) on {profile_platform or 'unknown platform'}")
    else:
        if not any([use_linkedin, use_reddit, use_google, use_apify, use_hunter]):
            st.error("Please select at least one platform to scrape")
            st.stop()
        
        # Use cleaned query from classification
        query = classification['search_query']
    
    st.session_state.processing = True
    
    try:
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            st.error(f"Configuration Error: {e}")
            st.info("Please set up your .env file with required API keys. See .env.example for reference.")
            st.stop()
        
        # Initialize components
        db = MongoDBManager()
        processor = DataProcessor()
        
        if is_profile_mode:
            # Profile scraping mode
            st.info(f"📊 Scraping {len(profile_urls)} {profile_platform} profile(s)...")
            
            # Create keywords_data for profile scraping
            keywords_data = {
                'scrape_type': 'profile',
                'profile_urls': profile_urls,
                'target_platform': profile_platform.lower(),
                'platforms': ['apify']  # Profile scraping uses Apify
            }
            
            # Save to database
            query_text = f"Profile scraping: {profile_platform} ({len(profile_urls)} profiles)"
            query_id = db.save_query(query_text, keywords_data)
            st.session_state.query_id = query_id
            
            # Step 2: Scrape profiles
            with st.spinner(f"🌐 Scraping {len(profile_urls)} {profile_platform} profiles... This may take a few minutes."):
                progress_bar = st.progress(0)
                
                raw_leads = asyncio.run(scrape_leads(keywords_data))
                
                progress_bar.progress(100)
                
        else:
            # Search/hashtag mode (existing logic)
            # Step 1: Extract keywords
            with st.spinner("🔍 Analyzing query and extracting keywords..."):
                keywords_data = extract_keywords(query)
                
                # Override platforms based on user selection
                selected_platforms = []
                if use_linkedin:
                    selected_platforms.append('linkedin')
                if use_reddit:
                    selected_platforms.append('reddit')
                if use_google:
                    selected_platforms.append('google')
                if use_apify:
                    selected_platforms.append('apify')
                if use_hunter:
                    selected_platforms.append('hunter')
                
                keywords_data['platforms'] = selected_platforms
                keywords_data['scrape_type'] = 'search'  # Explicitly set search mode
                print(f"🎯 Selected platforms: {selected_platforms}")
            
            st.success("✅ Keywords extracted!")
            with st.expander("View Extracted Keywords"):
                st.json(keywords_data)
            
            # Save query to database
            query_id = db.save_query(query, keywords_data)
            st.session_state.query_id = query_id
            
            # Step 2: Scrape leads
            with st.spinner("🌐 Scraping leads from selected platforms... This may take a few minutes."):
                progress_bar = st.progress(0)
                progress_bar.progress(0.2)
                
                raw_leads = scrape_leads(keywords_data, max_results=max_results)
                progress_bar.progress(0.6)
        
        if not raw_leads:
            st.warning("⚠️ No leads found. Try adjusting your search query or enabling more platforms.")
            st.stop()
        
        st.success(f"✅ Scraped {len(raw_leads)} raw leads!")
        
        # Step 3: Process and clean data
        with st.spinner("🧹 Cleaning and deduplicating data..."):
            processed_leads = processor.process_leads(raw_leads)
            progress_bar.progress(0.8)
        
        st.success(f"✅ Processed {len(processed_leads)} unique leads!")
        
        # Step 4: LLM filtering and scoring
        with st.spinner("🤖 Analyzing lead quality with AI... This may take a moment."):
            st.info(f"📤 Sending {len(processed_leads)} leads to LLM for quality analysis...")
            filtered_leads = filter_leads_with_llm(processed_leads)
            st.info(f"📥 LLM returned {len(filtered_leads)} leads after filtering")
            progress_bar.progress(0.85)
        
        # Apply minimum quality filter
        before_quality_filter = len(filtered_leads)
        filtered_leads = [l for l in filtered_leads if l.get('quality_score', 0) >= min_quality]
        st.info(f"🎯 After quality filter (>={min_quality}): {len(filtered_leads)} leads (removed {before_quality_filter - len(filtered_leads)} low-quality)")
        
        # Step 4.5: Analyze pain points with Perplexity Sonar (only for Google Places companies)
        google_places_leads = [l for l in filtered_leads if l.get('source') == 'apify_google_places']
        if google_places_leads:
            with st.spinner(f"🔍 Analyzing {len(google_places_leads)} Google Places companies for pain points... This may take a few minutes."):
                from backend.pain_point_analyzer import analyze_pain_points
                st.info(f"🌐 Researching Google Places company websites for pain points...")
                filtered_leads = analyze_pain_points(filtered_leads)
                st.success(f"✅ Pain point analysis completed for {len(google_places_leads)} companies!")
                progress_bar.progress(0.92)
        else:
            st.info("ℹ️ No Google Places companies found - skipping pain point analysis")
        
        # Step 4.6: ContactOut enrichment
        companies_with_pain_points = [l for l in filtered_leads if l.get('pain_points') and len(l.get('pain_points', [])) > 0]
        if companies_with_pain_points:
            with st.spinner(f"📞 Searching for decision-maker contacts..."):
                from backend.contactout_enricher import enrich_with_contacts
                filtered_leads = enrich_with_contacts(filtered_leads)
                
                # Check if any contacts were found
                found_contacts = sum(1 for l in filtered_leads if l.get('contact_count', 0) > 0)
                if found_contacts > 0:
                    st.success(f"✅ Found decision-maker contacts for {found_contacts} companies!")
                else:
                    st.warning("⚠️ No decision-maker contacts found. Your ContactOut API key may be invalid.")
                    st.info("💡 **Fix:** See `CONTACTOUT_API_KEY_GUIDE.md` for instructions, or use Apollo.io (50 free credits/month)")
                
                progress_bar.progress(0.94)
        
        # Step 4.7: Generate Personalized Talk Tracks
        companies_with_pain_points = [l for l in filtered_leads if l.get('pain_points') and len(l.get('pain_points', [])) > 0]
        if companies_with_pain_points:
            with st.spinner(f"🎯 Generating conversation strategies (talk tracks) with AI for {len(companies_with_pain_points)} companies..."):
                from backend.script_generator import add_outreach_scripts
                filtered_leads = add_outreach_scripts(filtered_leads)
                
                # Count successful talk tracks
                talk_tracks_generated = sum(1 for l in filtered_leads if l.get('has_talk_track'))
                if talk_tracks_generated > 0:
                    st.success(f"✅ Generated {talk_tracks_generated} personalized talk tracks!")
                else:
                    st.warning("⚠️ Failed to generate talk tracks")
                
                progress_bar.progress(0.97)
        
        # Step 5: Save to database
        with st.spinner("💾 Saving results to database..."):
            saved_count = db.save_leads(filtered_leads, query_id)
            progress_bar.progress(1.0)
        
        st.session_state.leads = filtered_leads
        
        st.success(f"🎉 Complete! Found {len(filtered_leads)} high-quality leads!")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)
    finally:
        st.session_state.processing = False

# Display results
if st.session_state.leads:
    st.markdown("---")
    st.subheader("📊 Lead Results")
    
    # Metrics - Row 1
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Leads", len(st.session_state.leads))
    
    with col2:
        avg_quality = sum(l.get('quality_score', 0) for l in st.session_state.leads) / len(st.session_state.leads)
        st.metric("Avg Quality", f"{avg_quality:.2f}")
    
    with col3:
        avg_warmth = sum(l.get('warmth_score', 0) for l in st.session_state.leads) / len(st.session_state.leads)
        st.metric("Avg Warmth", f"{avg_warmth:.2f}")
    
    with col4:
        hot_count = sum(1 for l in st.session_state.leads if l.get('sentiment') == 'hot')
        st.metric("Hot Leads", hot_count)
    
    with col5:
        # LinkedIn profiles found
        linkedin_count = sum(1 for l in st.session_state.leads if l.get('company_linkedin') or l.get('prospect_linkedins'))
        if linkedin_count > 0:
            st.metric("LinkedIn", f"{linkedin_count} 🔗")
        else:
            st.metric("LinkedIn", "0")
    
    with col6:
        # Talk tracks generated count
        talk_tracks_count = sum(1 for l in st.session_state.leads if l.get('has_talk_track'))
        if talk_tracks_count > 0:
            st.metric("Talk Tracks", f"{talk_tracks_count} 🎯")
        else:
            st.metric("Talk Tracks", "0")
    
    # Filters
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sentiment_filter = st.selectbox("Filter by Sentiment", ["All", "Hot", "Warm", "Cold"])
    
    with col2:
        source_filter = st.selectbox("Filter by Source", 
            ["All"] + list(set(l.get('source', 'Unknown') for l in st.session_state.leads))
        )
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Quality Score", "Warmth Score", "Name"])
    
    # Apply filters
    filtered_display = st.session_state.leads.copy()
    
    if sentiment_filter != "All":
        filtered_display = [l for l in filtered_display if l.get('sentiment', '').lower() == sentiment_filter.lower()]
    
    if source_filter != "All":
        filtered_display = [l for l in filtered_display if l.get('source') == source_filter]
    
    # Sort
    if sort_by == "Quality Score":
        filtered_display.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
    elif sort_by == "Warmth Score":
        filtered_display.sort(key=lambda x: x.get('warmth_score', 0), reverse=True)
    else:
        filtered_display.sort(key=lambda x: x.get('name', ''))
    
    # Display leads
    st.markdown(f"### Showing {len(filtered_display)} leads")
    
    for lead in filtered_display:
        sentiment = lead.get('sentiment', 'cold').lower()
        
        with st.container():
            st.markdown(f'<div class="lead-card {sentiment}">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**👤 {lead.get('name', 'N/A')}**")
                if lead.get('job_title'):
                    st.write(f"💼 {lead['job_title']}")
                if lead.get('company'):
                    st.write(f"🏢 {lead['company']}")
            
            with col2:
                if lead.get('email'):
                    st.write(f"📧 {lead['email']}")
                if lead.get('phone'):
                    st.write(f"📱 {lead['phone']}")
                if lead.get('linkedin_url'):
                    st.write(f"[🔗 LinkedIn Profile]({lead['linkedin_url']})")
                if lead.get('location'):
                    st.write(f"📍 {lead['location']}")
            
            with col3:
                st.write(f"**Quality:** {lead.get('quality_score', 0):.2f}")
                st.write(f"**Warmth:** {lead.get('warmth_score', 0):.2f}")
                st.write(f"**Source:** {lead.get('source', 'N/A')}")
                
                # Sentiment badge
                sentiment_emoji = {'hot': '🔥', 'warm': '🌤️', 'cold': '❄️'}.get(sentiment, '❓')
                st.write(f"{sentiment_emoji} {sentiment.title()}")
            
            # Pain Points Section (only for Google Places companies)
            if lead.get('source') == 'apify_google_places' and lead.get('pain_points'):
                st.markdown("---")
                
                pain_points = lead['pain_points']
                if pain_points and len(pain_points) > 0:
                    # Count by severity
                    high_count = sum(1 for p in pain_points if p.get('severity') == 'High')
                    medium_count = sum(1 for p in pain_points if p.get('severity') == 'Medium')
                    low_count = sum(1 for p in pain_points if p.get('severity') == 'Low')
                    
                    # Concise summary with counts
                    summary_parts = []
                    if high_count:
                        summary_parts.append(f"🔴 {high_count} High")
                    if medium_count:
                        summary_parts.append(f"🟡 {medium_count} Medium")
                    if low_count:
                        summary_parts.append(f"🟢 {low_count} Low")
                    
                    st.markdown(f"**🎯 Company Pain Points:** {' | '.join(summary_parts) if summary_parts else f'{len(pain_points)} identified'}")
                    
                    # Show top 3 high-priority issues
                    high_priority = [p for p in pain_points if p.get('severity') == 'High'][:3]
                    if high_priority:
                        for pp in high_priority:
                            st.caption(f"🔴 {pp.get('category', 'General')}: {pp.get('issue', 'N/A')[:80]}...")
                    
                    # Full details in compact expander
                    with st.expander(f"📋 View All {len(pain_points)} Pain Points"):
                        for i, pp in enumerate(pain_points, 1):
                            severity_icon = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 'Unknown': '⚪'}.get(pp.get('severity', 'Unknown'), '⚪')
                            st.markdown(f"**{i}. {severity_icon} [{pp.get('category', 'General')}]** {pp.get('issue', 'N/A')}")
                            # Show evidence text (if any)
                            if pp.get('evidence'):
                                st.caption(pp.get('evidence'))

                            # Show verified evidence links (safe to display)
                            for v in pp.get('evidence_urls_verified', []):
                                try:
                                    st.markdown(f"- Verified evidence: [{v}]({v})")
                                except Exception:
                                    st.write(f"- Verified evidence: {v}")

                            # Show unverified links as warnings (don't render as clickable links)
                            for u in pp.get('evidence_urls_unverified', []):
                                st.markdown(f"- ❗ Unverified evidence (could not reach): `{u}`")
            
            # LinkedIn Profiles Section (merged from multiple sources)
            has_linkedin_data = (lead.get('linkedin_url') or lead.get('company_linkedin') or 
                                lead.get('prospect_linkedins'))
            
            if has_linkedin_data:
                st.markdown("---")
                st.markdown("**🔗 LinkedIn Profiles:**")
                
                # Original prospect LinkedIn (from scraping)
                if lead.get('linkedin_url'):
                    contact_name = lead.get('name', 'Contact')
                    st.markdown(f"👤 **{contact_name}:** [View Profile]({lead['linkedin_url']})")
                
                # Company LinkedIn (from Perplexity)
                if lead.get('company_linkedin'):
                    st.markdown(f"🏢 **Company Page:** [{lead['company_linkedin']}]({lead['company_linkedin']})")
                
                # Additional prospects (from Perplexity)
                if lead.get('prospect_linkedins') and len(lead['prospect_linkedins']) > 0:
                    st.markdown(f"**👥 Key Decision Makers ({len(lead['prospect_linkedins'])}):**")
                    for i, prospect in enumerate(lead['prospect_linkedins'], 1):
                        name = prospect.get('name', 'N/A')
                        title = prospect.get('title', 'N/A')
                        linkedin_url = prospect.get('linkedin_url', '')
                        if linkedin_url:
                            st.markdown(f"   {i}. **{name}** - {title} - [View Profile]({linkedin_url})")
                        else:
                            st.markdown(f"   {i}. **{name}** - {title}")
            
            # Contact Information Section
            if lead.get('phone') or lead.get('email') or lead.get('website'):
                st.markdown("---")
                st.markdown("**📞 Company Contact Information:**")
                
                if lead.get('phone'):
                    st.markdown(f"📱 **Phone:** {lead['phone']}")
                if lead.get('email'):
                    st.markdown(f"📧 **Email:** {lead['email']}")
                if lead.get('website'):
                    st.markdown(f"🌐 **Website:** [{lead['website']}]({lead['website']})")
            
            # Decision Makers Section (ContactOut data - currently unavailable)
            if lead.get('decision_makers') and len(lead['decision_makers']) > 0:
                st.markdown("---")
                st.markdown(f"**👔 Decision-Maker Contacts ({lead.get('contact_count', 0)}):**")
                
                for i, contact in enumerate(lead['decision_makers'][:3], 1):  # Show top 3
                    st.markdown(f"**{i}. {contact.get('name', 'N/A')}** - {contact.get('title', 'N/A')}")
                    if contact.get('phone'):
                        st.caption(f"📱 {contact['phone']}")
                    if contact.get('email'):
                        st.caption(f"📧 {contact['email']}")
                    if contact.get('linkedin'):
                        st.caption(f"[🔗 LinkedIn]({contact['linkedin']})")
                
                # Full list in expander if more than 3
                if len(lead['decision_makers']) > 3:
                    with st.expander(f"View All {len(lead['decision_makers'])} Contacts"):
                        for i, contact in enumerate(lead['decision_makers'][3:], 4):
                            st.markdown(f"**{i}. {contact.get('name', 'N/A')}** - {contact.get('title', 'N/A')}")
                            if contact.get('phone'):
                                st.caption(f"📱 {contact['phone']}")
                            if contact.get('email'):
                                st.caption(f"📧 {contact['email']}")
            
            # Personalized Talk Track Section
            if lead.get('has_talk_track') and lead.get('talk_track'):
                st.markdown("---")
                st.markdown("**🎯 Conversation Strategy (Talk Track):**")
                
                # Display talk track in a nice box
                st.markdown("""
                <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                """, unsafe_allow_html=True)
                
                st.markdown(lead['talk_track'])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Copy button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("📋 Copy", key=f"copy_{lead.get('name', '')}_{i}"):
                        st.success("✅ Copied to clipboard!")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Export options
    st.markdown("---")
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export to CSV
        df = pd.DataFrame(filtered_display)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="leads.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export to JSON
        import json
        json_data = json.dumps(filtered_display, indent=2)
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name="leads.json",
            mime="application/json"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built by the Hustle House Team</p>
    <p>Run with: <code>streamlit run app.py</code></p>
</div>
""", unsafe_allow_html=True)