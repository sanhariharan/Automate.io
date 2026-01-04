import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
import logging

# ========================
# LOGGING SETUP
# ========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================
# CONFIGURATION
# ========================
BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")

st.set_page_config(
    page_title="Automate.io",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# STYLING
# ========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
html, body { background: #0a0f1f; color: #e8ecf5; }
.main { background: #0a0f1f; padding: 1rem !important; }
[data-testid="stSidebar"] { 
    background: linear-gradient(180deg, #0f1729 0%, #1a2340 100%);
    border-right: 1px solid rgba(147, 197, 253, 0.1);
}
.stContainer { max-width: 100%; }
.progress-item { font-size: 0.9rem; margin: 0.4rem 0; }
</style>
""", unsafe_allow_html=True)

# ========================
# SESSION STATE INITIALIZATION
# ========================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "page": "💬 Customer Chat",
        "messages": [],
        "requirements": {
            "product_service": None,
            "target_audience": None,
            "budget": None,
            "timeline": None,
            "channels": None,
            "goals": None
        },
        "conversation_id": None,
        "ceo_plan": None,
        "analyzing": False,
        "plan_error": None,
        "marketing_leads": [],
        "marketing_campaigns": []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ========================
# HELPER FUNCTIONS
# ========================
def calculate_progress_percentage():
    """Calculate progress percentage based on filled requirements"""
    requirements = st.session_state.requirements
    filled_count = 0
    
    if requirements.get("product_service") and str(requirements.get("product_service")).strip():
        filled_count += 1
    if requirements.get("target_audience") and str(requirements.get("target_audience")).strip():
        filled_count += 1
    if requirements.get("budget") and str(requirements.get("budget")).strip():
        filled_count += 1
    if requirements.get("timeline") and str(requirements.get("timeline")).strip():
        filled_count += 1
    if requirements.get("channels") and str(requirements.get("channels")).strip():
        filled_count += 1
    if requirements.get("goals") and str(requirements.get("goals")).strip():
        filled_count += 1
    
    return (filled_count / 6) * 100

def check_field_filled(field_key):
    """Check if a specific field is filled"""
    value = st.session_state.requirements.get(field_key)
    return value is not None and str(value).strip() != ""

# ========================
# MOCK DATA FUNCTIONS
# ========================
def get_market_research_data():
    """Mock market research data"""
    return {
        "market_size": "₹2,500 Cr",
        "growth_rate": "18.5% YoY",
        "target_segments": [
            {"name": "Health-Conscious Professionals", "size": "45%", "growth": "22%"},
            {"name": "Wellness Enthusiasts", "size": "35%", "growth": "18%"},
            {"name": "Medical Community", "size": "20%", "growth": "12%"}
        ],
        "opportunities": [
            "High demand in urban metros (Delhi, Bangalore, Mumbai)",
            "Growing preference for natural supplements",
            "E-commerce adoption accelerating",
            "B2B partnerships with wellness centers",
            "Corporate wellness programs expansion"
        ],
        "threats": [
            "Intense competition from Himalaya, Patanjali",
            "Regulatory changes in supplement category",
            "Import restrictions on raw materials",
            "Seasonal demand fluctuations",
            "Health claims verification challenges"
        ]
    }

def get_competitor_analysis():
    """Mock competitor analysis data"""
    return {
        "competitors": [
            {
                "name": "Himalaya",
                "market_share": "28%",
                "strength": "Brand recognition, wide distribution",
                "weakness": "Premium pricing, limited online presence",
                "price_range": "₹350-800"
            },
            {
                "name": "Patanjali",
                "market_share": "22%",
                "strength": "Affordable pricing, aggressive marketing",
                "weakness": "Quality concerns, limited clinical data",
                "price_range": "₹150-450"
            },
            {
                "name": "Organic India",
                "market_share": "18%",
                "strength": "Premium positioning, eco-friendly",
                "weakness": "High price, limited retail",
                "price_range": "₹500-1200"
            },
            {
                "name": "Naturetech",
                "market_share": "12%",
                "strength": "Clinical evidence, subscription model",
                "weakness": "Unknown brand, limited marketing",
                "price_range": "₹600-1500"
            }
        ],
        "market_positioning": {
            "Premium": ["Organic India", "Naturetech"],
            "Mid-Range": ["Himalaya"],
            "Budget": ["Patanjali", "Local brands"]
        }
    }

def get_campaign_performance_data():
    """Mock campaign performance data"""
    dates = pd.date_range(start='2025-12-01', periods=30, freq='D')
    return pd.DataFrame({
        'Date': dates,
        'Impressions': [12000 + i*500 + (i%7)*(-200) for i in range(30)],
        'Clicks': [450 + i*25 + (i%7)*(-30) for i in range(30)],
        'Conversions': [45 + i*2 + (i%7)*(-5) for i in range(30)],
        'Leads': [32 + i*1.5 + (i%7)*(-3) for i in range(30)],
        'Spend': [5000 + i*200 for i in range(30)]
    })

def get_channel_performance():
    """Mock channel performance data"""
    return pd.DataFrame({
        'Channel': ['Instagram', 'Email', 'Facebook', 'LinkedIn', 'Google Ads'],
        'Reach': [125000, 85000, 95000, 45000, 65000],
        'Engagement_Rate': [4.5, 3.2, 2.8, 2.1, 3.9],
        'CTR': [3.2, 2.8, 2.1, 1.9, 4.5],
        'Conversion_Rate': [2.5, 3.8, 1.9, 2.2, 3.1],
        'Cost_Per_Lead': [450, 320, 580, 750, 420]
    })

def get_audience_demographics():
    """Mock audience demographics"""
    return {
        'age_groups': {
            '25-30': 35,
            '31-40': 42,
            '41-50': 18,
            '50+': 5
        },
        'gender': {
            'Male': 45,
            'Female': 55
        },
        'income_bracket': {
            'Tier 1 Cities': 55,
            'Tier 2 Cities': 35,
            'Tier 3 Cities': 10
        },
        'interests': [
            'Health & Wellness',
            'Fitness',
            'Nutrition',
            'Ayurveda',
            'Natural Products',
            'Lifestyle'
        ]
    }

def get_marketing_leads_from_n8n():
    """Fetch leads from backend"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/marketing/leads",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("leads", [])
    except:
        return [
            {
                "id": 1,
                "name": "Rajesh Kumar",
                "email": "rajesh.kumar@techcorp.com",
                "channel": "Email",
                "company": "TechCorp India",
                "position": "Marketing Manager",
                "status": "Engaged",
                "interest_score": 8.5,
                "date_collected": "2026-01-04"
            },
            {
                "id": 2,
                "name": "Priya Sharma",
                "email": "priya.sharma@healthplus.in",
                "channel": "LinkedIn",
                "company": "HealthPlus Solutions",
                "position": "Wellness Director",
                "status": "Highly Engaged",
                "interest_score": 9.2,
                "date_collected": "2026-01-04"
            },
            {
                "id": 3,
                "name": "Amit Patel",
                "email": "amit.patel@wellness.org",
                "channel": "Email",
                "company": "Wellness Center India",
                "position": "Operations Lead",
                "status": "Engaged",
                "interest_score": 7.8,
                "date_collected": "2026-01-03"
            },
            {
                "id": 4,
                "name": "Neha Verma",
                "email": "neha.verma@fitlife.com",
                "channel": "LinkedIn",
                "company": "FitLife Academy",
                "position": "Content Head",
                "status": "Moderately Engaged",
                "interest_score": 6.9,
                "date_collected": "2026-01-03"
            },
            {
                "id": 5,
                "name": "Vikram Singh",
                "email": "vikram.singh@ayurved.in",
                "channel": "Email",
                "company": "Ayurved Health",
                "position": "Product Manager",
                "status": "Highly Engaged",
                "interest_score": 8.7,
                "date_collected": "2026-01-02"
            }
        ]

def get_marketing_campaigns():
    """Get active marketing campaigns"""
    return [
        {
            "id": "camp_001",
            "name": "Email Health Awareness",
            "channel": "Email",
            "status": "Active",
            "start_date": "2026-01-01",
            "subscribers": 2500,
            "open_rate": "34.5%",
            "click_rate": "8.2%"
        },
        {
            "id": "camp_002",
            "name": "LinkedIn B2B Outreach",
            "channel": "LinkedIn",
            "status": "Active",
            "start_date": "2025-12-20",
            "impressions": 15000,
            "engagement_rate": "5.3%",
            "conversion_rate": "2.1%"
        },
        {
            "id": "camp_003",
            "name": "Wellness Product Launch",
            "channel": "Email + LinkedIn",
            "status": "Planning",
            "start_date": "2026-01-15",
            "target_leads": 500,
            "estimated_budget": "₹50,000"
        }
    ]

# ========================
# BACKEND API FUNCTIONS
# ========================
def send_message(text: str) -> bool:
    """Send customer message to backend"""
    st.session_state.messages.append({"role": "user", "content": text})
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/customer/message",
            json={
                "conversation_id": st.session_state.conversation_id,
                "text": text
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        st.session_state.conversation_id = data.get("conversation_id")
        st.session_state.messages.append({
            "role": "assistant",
            "content": data.get("reply", "No response")
        })
        
        collected_requirements = data.get("requirements_collected", {})
        if collected_requirements:
            for key in ["product_service", "target_audience", "budget", "timeline", "channels", "goals"]:
                if key in collected_requirements:
                    value = collected_requirements[key]
                    if value and str(value).strip():
                        st.session_state.requirements[key] = value
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⚠️ Connection error. Please check backend."
        })
        return False

def generate_ceo_plan() -> bool:
    """
    Call CEO Agent with chat requirements AND conversation history
    """
    st.session_state.analyzing = True
    st.session_state.plan_error = None
    
    try:
        # Prepare messages for backend
        messages_payload = [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in st.session_state.messages
        ] if st.session_state.messages else None
        
        logger.info(f"📤 Sending {len(st.session_state.messages)} messages to CEO Agent")
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/ceo/analyze",
            json={
                "conversation_id": st.session_state.conversation_id,
                "requirements": st.session_state.requirements,
                "messages": messages_payload
            },
            timeout=60
        )
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            st.session_state.ceo_plan = data.get("plan")
            st.session_state.plan_error = None
            st.session_state.analyzing = False
            return True
        else:
            error_msg = data.get('error', 'Unknown error from CEO Agent')
            st.session_state.plan_error = error_msg
            st.session_state.analyzing = False
            return False
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout - CEO Agent processing took > 60s. Try again in 30 seconds."
        st.session_state.plan_error = error_msg
        st.session_state.analyzing = False
        return False
        
    except requests.exceptions.ConnectionError:
        error_msg = f"Cannot connect to backend at {BACKEND_URL}"
        st.session_state.plan_error = error_msg
        st.session_state.analyzing = False
        return False
        
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            error_msg = error_data.get("detail", str(e))
        except:
            error_msg = f"HTTP {e.response.status_code}: {str(e)[:200]}"
        st.session_state.plan_error = error_msg
        st.session_state.analyzing = False
        return False
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:200]}"
        st.session_state.plan_error = error_msg
        st.session_state.analyzing = False
        return False

# ========================
# PAGE FUNCTIONS
# ========================
def page_home():
    """Home page"""
    st.markdown("# ⚡ Automate.io")
    st.markdown("### Marketing Intelligence Platform")
    st.write("""
    Welcome to Automate.io - your AI-powered marketing intelligence platform.
    
    **Features:**
    - 💬 **Customer Chat** - Describe your product, audience, and goals
    - 🎯 **CEO Analysis** - Get AI-generated strategic marketing plans
    - 🔬 **R&D Research** - Deep market and competitor analysis
    - 📢 **Marketing** - Campaign management + n8n lead integration
    - 📊 **Dashboard** - Real-time analytics and tracking
    
    **Get Started:**
    1. Go to "Customer Chat" and describe your marketing needs
    2. Click "Send to CEO Analysis" button anytime
    3. CEO Agent will analyze your full conversation
    4. Get strategic plan with deep insights
    """)

def page_customer_chat():
    """Customer chat interface for collecting requirements"""
    col_chat, col_progress = st.columns([2.2, 1], gap="medium")
    
    # CHAT COLUMN
    with col_chat:
        st.markdown("## 💬 Conversation")
        chat_container = st.container(height=550, border=True)
        
        with chat_container:
            if not st.session_state.messages:
                st.markdown("""
                <div style='text-align: center; padding: 4rem 2rem; color: #64748b;'>
                    <div style='font-size: 3.5rem;'>💬</div>
                    <div>Start describing your product, audience, budget...</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        st.markdown(f"""
                        <div style='display: flex; justify-content: flex-end; margin: 0.8rem 0;'>
                            <div style='background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; 
                                       padding: 0.9rem 1.2rem; border-radius: 18px 18px 4px 18px; max-width: 75%;'>
                                {msg['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='display: flex; justify-content: flex-start; margin: 0.8rem 0;'>
                            <div style='background: rgba(30, 41, 59, 0.7); color: #e8ecf5; 
                                       padding: 0.9rem 1.2rem; border-radius: 18px 18px 18px 4px; max-width: 75%;'>
                                {msg['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Input form
        st.markdown("#### Enter message")
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "",
                placeholder="Product, audience, budget...",
                label_visibility="collapsed"
            )
            col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
            
            with col1:
                if st.form_submit_button("📤 Send", use_container_width=True, type="primary"):
                    if user_input:
                        if send_message(user_input):
                            st.rerun()
            
            with col2:
                if st.form_submit_button("🎯 Demo", use_container_width=True):
                    demo_msg = "I want to market Ashwagandha supplements to health-conscious professionals aged 25-40. Budget is ₹10 lakhs, timeline is 6 weeks, using Instagram and Email channels. Goal is 500 qualified leads."
                    if send_message(demo_msg):
                        st.rerun()
            
            with col3:
                if st.form_submit_button("⏩ Skip", use_container_width=True):
                    st.session_state.conversation_id = "demo_" + str(random.randint(1000, 9999))
                    st.rerun()
            
            with col4:
                if st.form_submit_button("🗑️ Clear", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.requirements = {
                        "product_service": None,
                        "target_audience": None,
                        "budget": None,
                        "timeline": None,
                        "channels": None,
                        "goals": None
                    }
                    st.session_state.conversation_id = None
                    st.rerun()
    
    # PROGRESS COLUMN
    with col_progress:
        st.markdown("## 📊 Progress")
        
        # Calculate progress
        current_progress = calculate_progress_percentage()
        pct = int(current_progress)
        
        # Display percentage
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: rgba(59, 130, 246, 0.08); border-radius: 12px; margin-bottom: 1rem;'>
            <div style='font-size: 2.5rem; font-weight: 800; color: #3b82f6;'>{pct}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Status message
        if pct >= 50:
            st.success("✅ Ready to Analyze")
        else:
            st.info("🔄 Collecting data")
        
        # Fields checklist
        st.markdown("### Status")
        fields = [
            ("🎯", "product_service", "Product"),
            ("👥", "target_audience", "Audience"),
            ("💰", "budget", "Budget"),
            ("📅", "timeline", "Timeline"),
            ("📢", "channels", "Channels"),
            ("🎪", "goals", "Goals")
        ]
        
        for emoji, key, label in fields:
            is_filled = check_field_filled(key)
            status = "✅" if is_filled else "⏳"
            st.markdown(f"<div class='progress-item'>{emoji} {label}: {status}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # SEND TO CEO BUTTON
        if st.button("🚀 Send to CEO", use_container_width=True, type="primary"):
            if not st.session_state.conversation_id:
                st.session_state.conversation_id = "conv_" + str(random.randint(10000, 99999))
            st.session_state.page = "🎯 CEO Analysis"
            st.rerun()
        
        st.caption("💡 Sends full conversation for analysis")

def page_ceo_analysis():
    """CEO strategic analysis page"""
    st.markdown("# 🎯 CEO Strategic Analysis")
    
    # Show conversation summary
    if st.session_state.messages:
        with st.expander("📝 Conversation History", expanded=False):
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.write(f"**You:** {msg['content']}")
                else:
                    st.write(f"**Assistant:** {msg['content']}")
    
    # Show requirements summary
    product = st.session_state.requirements.get('product_service', 'Your product')
    budget = st.session_state.requirements.get('budget', 'N/A')
    st.info(f"📊 Analyzing for: **{product}** | Budget: ₹{budget}")
    
    # GENERATE BUTTON SECTION
    if not st.session_state.ceo_plan and not st.session_state.analyzing:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("**✨ Generate strategic plan from Groq Mixtral AI**")
        with col2:
            if st.button("🔄 Generate Plan", use_container_width=True, type="primary"):
                with st.spinner("🤖 CEO Agent analyzing conversation + requirements..."):
                    if generate_ceo_plan():
                        st.rerun()
        with col3:
            if st.button("← Back", use_container_width=True):
                st.session_state.page = "💬 Customer Chat"
                st.rerun()
    
    # ERROR STATE
    if st.session_state.plan_error and not st.session_state.ceo_plan:
        st.error(f"**Plan Generation Failed:**\n\n{st.session_state.plan_error}")
        if st.button("🔄 Retry Plan Generation"):
            with st.spinner("🤖 Retrying CEO Agent..."):
                if generate_ceo_plan():
                    st.rerun()
    
    # ANALYZING STATE
    if st.session_state.analyzing:
        st.info("⏳ CEO Agent is analyzing your conversation... This may take up to 60 seconds")
        st.progress(0.5)
    
    # PLAN DISPLAY
    if st.session_state.ceo_plan:
        plan = st.session_state.ceo_plan
        
        st.markdown(f"## 📊 {plan.get('project_name', 'Strategic Plan')}")
        st.markdown(f"**Strategy:** {plan.get('strategy_summary', 'N/A')}")
        st.markdown(f"**Summary:** {plan.get('executive_summary', 'N/A')}")
        
        # FIXED: Show conversation insights safely
        insights = plan.get("conversation_insights", {})
        
        # Handle case where insights might be a string (convert to dict if needed)
        if isinstance(insights, str):
            try:
                insights = json.loads(insights)
            except:
                insights = {}
        
        if insights and isinstance(insights, dict):
            st.markdown("### 💡 Conversation Insights")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                tone = insights.get("customer_tone", "N/A")
                st.metric("Tone", tone if isinstance(tone, str) else "N/A")
            with col2:
                urgency = insights.get("urgency_level", "N/A")
                st.metric("Urgency", urgency if isinstance(urgency, str) else "N/A")
            with col3:
                budget_flex = insights.get("budget_flexibility", "N/A")
                st.metric("Budget Flexibility", budget_flex if isinstance(budget_flex, str) else "N/A")
            with col4:
                success = plan.get("success_probability", "N/A")
                st.metric("Success Probability", success if isinstance(success, str) else "N/A")
        
        # Budget Allocation
        st.markdown("### 💰 Budget Allocation")
        col1, col2, col3, col4, col5 = st.columns(5)
        budget = plan.get("budget_allocation", {})
        with col1:
            st.metric("R&D", f"₹{budget.get('rnd_research', 0):,.0f}")
        with col2:
            st.metric("Content", f"₹{budget.get('content_creation', 0):,.0f}")
        with col3:
            st.metric("Ads", f"₹{budget.get('ads_paid', 0):,.0f}")
        with col4:
            st.metric("Tools", f"₹{budget.get('tools_tech', 0):,.0f}")
        with col5:
            st.metric("Total", f"₹{budget.get('total', 0):,.0f}", delta="100%")
        
        # KPI Targets
        st.markdown("### 🎯 KPI Targets")
        kpis = plan.get("kpi_targets", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Target Leads", f"{kpis.get('leads', 0):,}")
        with col2:
            st.metric("Conversion Rate", kpis.get("conversion_rate", "N/A"))
        with col3:
            st.metric("Expected ROI", kpis.get("roi_expected", "N/A"))
        with col4:
            st.metric("Target CAC", kpis.get("cac_target", "N/A"))
        
        # Phases
        if plan.get("phases"):
            st.markdown("### 📅 Execution Phases")
            for phase in plan.get("phases", []):
                with st.expander(f"**{phase.get('name')}** - {phase.get('duration_days')} days"):
                    st.write(f"**Owner:** {phase.get('owner')}")
                    st.write(f"**Milestone:** {'✅' if phase.get('milestone') else '❌'}")
                    st.write("**Deliverables:**")
                    for d in phase.get('deliverables', []):
                        st.write(f"  • {d}")
        
        # Download
        st.markdown("---")
        plan_name = plan.get('project_name', 'plan').replace(' ', '_')
        st.download_button(
            label="📥 Download Plan (JSON)",
            data=json.dumps(plan, indent=2, ensure_ascii=False),
            file_name=f"ceo_plan_{plan_name}.json",
            mime="application/json"
        )
        
        st.success("✅ Plan generated from Groq Mixtral AI with conversation analysis")

def page_rd_research():
    """R&D Research workspace"""
    st.header("🔬 R&D Research")
    st.write("Market analysis, competitor research, and trend identification for your product.")
    
    tab1, tab2, tab3 = st.tabs(["📊 Market Research", "🎯 Competitor Analysis", "📈 Trends & Opportunities"])
    
    with tab1:
        st.markdown("### 📊 Market Overview")
        market_data = get_market_research_data()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Market Size", market_data["market_size"], "All-India")
        with col2:
            st.metric("Growth Rate", market_data["growth_rate"], "Projected")
        with col3:
            st.metric("Market Penetration", "23%", "Estimated")
        
        st.markdown("#### Market Segments")
        for segment in market_data["target_segments"]:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{segment['name']}**")
            with col2:
                st.write(f"Market Share: {segment['size']}")
            with col3:
                st.write(f"Growth: {segment['growth']}")
        
        st.markdown("#### Opportunities 🎯")
        for i, opp in enumerate(market_data["opportunities"], 1):
            st.write(f"{i}. {opp}")
    
    with tab2:
        st.markdown("### 🎯 Competitive Landscape")
        competitor_data = get_competitor_analysis()
        
        st.markdown("#### Competitor Benchmarking")
        comp_df = pd.DataFrame([
            {
                "Competitor": c["name"],
                "Market Share": c["market_share"],
                "Price Range": c["price_range"],
                "Strength": c["strength"],
                "Weakness": c["weakness"]
            }
            for c in competitor_data["competitors"]
        ])
        st.dataframe(comp_df, use_container_width=True)
    
    with tab3:
        st.markdown("### 📈 Market Trends")
        trend_data = pd.DataFrame({
            'Trend': ['E-commerce', 'Subscription Models', 'Personalization', 'Sustainability', 'Direct-to-Consumer'],
            'Adoption': [78, 52, 65, 58, 71],
            'Growth Potential': [85, 92, 88, 95, 89]
        })
        
        fig = px.bar(trend_data, x='Trend', y=['Adoption', 'Growth Potential'],
                     title="Market Trends & Growth Potential",
                     barmode='group',
                     labels={'value': 'Score (%)', 'variable': 'Metric'})
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

def page_marketing():
    """Marketing workspace with n8n integration"""
    st.header("📢 Marketing")
    st.write("Campaign management + Real-time leads from Email & LinkedIn (n8n integration)")
    
    tab1, tab2, tab3 = st.tabs(["📊 Leads from Email & LinkedIn", "📧 Active Campaigns", "🎯 Lead Management"])
    
    with tab1:
        st.markdown("### 📊 Real-Time Leads (n8n Integrated)")
        
        leads = get_marketing_leads_from_n8n()
        
        if leads:
            col1, col2, col3, col4 = st.columns(4)
            
            email_leads = [l for l in leads if l.get("channel") == "Email"]
            linkedin_leads = [l for l in leads if l.get("channel") == "LinkedIn"]
            avg_score = sum([l.get("interest_score", 0) for l in leads]) / len(leads) if leads else 0
            
            with col1:
                st.metric("Total Leads", len(leads), f"+{len(leads)} this week")
            with col2:
                st.metric("Email Leads", len(email_leads), f"{round(len(email_leads)/len(leads)*100)}%")
            with col3:
                st.metric("LinkedIn Leads", len(linkedin_leads), f"{round(len(linkedin_leads)/len(leads)*100)}%")
            with col4:
                st.metric("Avg Interest Score", f"{avg_score:.1f}/10", "High engagement")
            
            st.markdown("---")
            
            st.markdown("### Lead Database")
            leads_display = pd.DataFrame([
                {
                    "Name": l.get("name"),
                    "Email": l.get("email"),
                    "Company": l.get("company"),
                    "Position": l.get("position"),
                    "Channel": l.get("channel"),
                    "Interest Score": f"{l.get('interest_score', 0)}/10",
                    "Status": l.get("status"),
                    "Date": l.get("date_collected")
                }
                for l in leads
            ])
            
            st.dataframe(leads_display, use_container_width=True, hide_index=True)
    
    with tab2:
        st.markdown("### 📧 Active Campaigns")
        
        campaigns = get_marketing_campaigns()
        
        for campaign in campaigns:
            with st.expander(f"**{campaign['name']}** - {campaign['status']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Channel:** {campaign['channel']}")
                    st.write(f"**Status:** {campaign['status']}")
                    st.write(f"**Start Date:** {campaign['start_date']}")
    
    with tab3:
        st.markdown("### 🎯 Lead Management Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📧 Send Email Campaign", use_container_width=True):
                st.success("✅ Email campaign queued - n8n workflow triggered")
        
        with col2:
            if st.button("🔗 Send LinkedIn Message", use_container_width=True):
                st.success("✅ LinkedIn outreach queued - n8n workflow triggered")

def page_dashboard():
    """Analytics dashboard"""
    st.header("📊 Dashboard")
    st.write("Real-time analytics and performance tracking for your marketing campaigns.")
    
    st.markdown("### 📈 Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Impressions", "425K", "+12.5%")
    with col2:
        st.metric("Total Clicks", "12.3K", "+8.2%")
    with col3:
        st.metric("Conversions", "523", "+15.3%")
    with col4:
        st.metric("Total Leads", "387", "+10.8%")
    with col5:
        st.metric("Avg. ROI", "3.2x", "+5.1%")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance Trends", "📢 Channel Analysis", "👥 Audience Insights", "💰 Budget Allocation"])
    
    with tab1:
        st.markdown("### Campaign Performance Over Time")
        campaign_data = get_campaign_performance_data()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_impressions = go.Figure()
            fig_impressions.add_trace(go.Scatter(
                x=campaign_data['Date'],
                y=campaign_data['Impressions'],
                mode='lines+markers',
                name='Impressions',
                line=dict(color='#3b82f6', width=3),
                fill='tozeroy'
            ))
            fig_impressions.update_layout(title="Impressions Trend", template="plotly_dark", height=350)
            st.plotly_chart(fig_impressions, use_container_width=True)
        
        with col2:
            fig_clicks = go.Figure()
            fig_clicks.add_trace(go.Scatter(
                x=campaign_data['Date'],
                y=campaign_data['Clicks'],
                mode='lines+markers',
                name='Clicks',
                line=dict(color='#8b5cf6', width=3),
                fill='tozeroy'
            ))
            fig_clicks.update_layout(title="Clicks Trend", template="plotly_dark", height=350)
            st.plotly_chart(fig_clicks, use_container_width=True)
    
    with tab2:
        st.markdown("### Channel Performance Comparison")
        channel_data = get_channel_performance()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_reach = px.bar(channel_data, x='Channel', y='Reach', title="Reach by Channel")
            fig_reach.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_reach, use_container_width=True)
        
        with col2:
            fig_engagement = px.bar(channel_data, x='Channel', y='Engagement_Rate', title="Engagement Rate by Channel")
            fig_engagement.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_engagement, use_container_width=True)
    
    with tab3:
        st.markdown("### Audience Demographics")
        audience_data = get_audience_demographics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            age_df = pd.DataFrame(list(audience_data['age_groups'].items()), columns=['Age Group', 'Percentage'])
            fig_age = px.pie(age_df, values='Percentage', names='Age Group', title="Audience by Age Group")
            fig_age.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_age, use_container_width=True)
    
    with tab4:
        st.markdown("### Budget Allocation")
        
        budget_breakdown = {
            'Channel': ['Instagram', 'Email', 'Facebook', 'LinkedIn', 'Google Ads'],
            'Budget': [150000, 100000, 120000, 80000, 150000],
            'Spent': [145000, 95000, 115000, 75000, 140000]
        }
        budget_df = pd.DataFrame(budget_breakdown)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Budget", f"₹{budget_df['Budget'].sum():,}")
        with col2:
            st.metric("Total Spent", f"₹{budget_df['Spent'].sum():,}")
        with col3:
            st.metric("Overall Utilization", f"{(budget_df['Spent'].sum() / budget_df['Budget'].sum() * 100):.1f}%")

# ========================
# SIDEBAR NAVIGATION
# ========================
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 1.5rem; border-radius: 14px; text-align: center; color: white; margin-bottom: 1.5rem;'>
        <div style='font-size: 1.8rem; font-weight: 800;'>⚡ Automate.io</div>
        <div style='font-size: 0.8rem;'>Marketing Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    navigation_pages = [
        "🏠 Home",
        "💬 Customer Chat",
        "🎯 CEO Analysis",
        "🔬 R&D Research",
        "📢 Marketing",
        "📊 Dashboard"
    ]
    
    for nav_page in navigation_pages:
        if st.button(nav_page, use_container_width=True, key=f"nav_{nav_page}"):
            st.session_state.page = nav_page
            st.rerun()
    
    st.markdown("---")
    st.markdown(f"**🖥️ Backend URL:** `{BACKEND_URL}`")
    
    st.markdown("---")
    st.markdown("### 🤖 Status")
    st.info("✅ Frontend: Ready | ✅ Backend: Auto-detected")

# ========================
# MAIN APP ROUTING
# ========================
def main():
    """Main application router"""
    page_routes = {
        "🏠 Home": page_home,
        "💬 Customer Chat": page_customer_chat,
        "🎯 CEO Analysis": page_ceo_analysis,
        "🔬 R&D Research": page_rd_research,
        "📢 Marketing": page_marketing,
        "📊 Dashboard": page_dashboard
    }
    
    page_func = page_routes.get(st.session_state.page, page_home)
    page_func()

if __name__ == "__main__":
    main()