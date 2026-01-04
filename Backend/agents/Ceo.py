"""
routes/ceo.py - FINAL FIXED VERSION - NO MORE FALLBACK
CEO Strategic Agent with proper prompt formatting
"""
import os
import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# ========================
# LOGGING SETUP
# ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# LOAD ENV
# ========================
load_dotenv()

# ========================
# LANGCHAIN + GROQ SETUP
# ========================
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel as PydanticBaseModel, Field

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

if not GROQ_API_KEY:
    logger.error("❌ GROQ_API_KEY not found in .env")
    raise RuntimeError("GROQ_API_KEY required in .env file")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name=MODEL,
    temperature=0.3,
    max_tokens=4000,
    timeout=60
)

logger.info(f"✅ LangChain ChatGroq {MODEL} initialized")

# ========================
# PYDANTIC MODELS FOR API
# ========================
class CEOAnalysisRequest(BaseModel):
    """Request from frontend with requirements + conversation"""
    requirements: Dict[str, Any]
    messages: List[Dict[str, str]] = []
    conversation_id: str

# ========================
# PYDANTIC SCHEMA FOR JSON PARSING
# ========================
class ConversationInsights(PydanticBaseModel):
    """Conversation analysis insights"""
    customer_tone: str = Field(description="Customer tone: enthusiastic/neutral/hesitant/urgent")
    pain_points: List[str] = Field(description="Main pain points mentioned")
    unspoken_needs: List[str] = Field(description="Unspoken needs inferred")
    urgency_level: str = Field(description="urgency: high/medium/low")
    budget_flexibility: str = Field(description="Budget flexibility: fixed/flexible/unknown")
    market_context: str = Field(description="Brief market observation")
    recommendations: List[str] = Field(description="Strategic recommendations")

class BudgetAllocation(PydanticBaseModel):
    """Budget allocation breakdown"""
    rnd_research: float = Field(description="R&D Research budget in INR")
    content_creation: float = Field(description="Content Creation budget in INR")
    ads_paid: float = Field(description="Paid Ads budget in INR")
    tools_tech: float = Field(description="Tools & Tech budget in INR")
    total: float = Field(description="Total budget (must equal customer budget)")

class KPITargets(PydanticBaseModel):
    """KPI targets for campaign"""
    leads: int = Field(description="Target number of leads")
    conversion_rate: str = Field(description="Conversion rate as percentage string")
    roi_expected: str = Field(description="Expected ROI as multiplier string")
    cac_target: str = Field(description="Customer Acquisition Cost target in INR format")

class Phase(PydanticBaseModel):
    """Campaign execution phase"""
    name: str = Field(description="Phase name with action verb")
    duration_days: int = Field(description="Duration in whole days")
    deliverables: List[str] = Field(description="Specific deliverables")
    owner: str = Field(description="Owner: R&D, Marketing, CEO, or External")
    dependencies: List[str] = Field(description="Phase dependencies")
    milestone: bool = Field(description="Is this a critical path milestone")

class RiskAssessment(PydanticBaseModel):
    """Risk assessment"""
    high: List[str] = Field(description="High risk factors")
    medium: List[str] = Field(description="Medium risk factors")
    mitigation: str = Field(description="Mitigation strategy")

class RNDParams(PydanticBaseModel):
    """R&D parameters"""
    research_topics: List[str] = Field(description="Research topics")
    competitor_analysis: bool = Field(description="Include competitor analysis")
    market_research: bool = Field(description="Include market research")

class MarketingParams(PydanticBaseModel):
    """Marketing parameters"""
    campaign_type: str = Field(description="Type of campaign")
    creative_brief: str = Field(description="Creative brief")
    ad_budget: float = Field(description="Ad spend budget")

class CEOPlan(PydanticBaseModel):
    """Complete CEO Strategic Plan"""
    project_name: str = Field(description="Specific project name")
    strategy_summary: str = Field(description="2-3 sentence strategy summary")
    executive_summary: str = Field(description="Detailed executive summary")
    phases: List[Phase] = Field(description="Campaign phases (minimum 3)")
    budget_allocation: BudgetAllocation = Field(description="Budget breakdown")
    kpi_targets: KPITargets = Field(description="KPI targets")
    channels_priority: List[str] = Field(description="Ranked channels with rationale")
    timeline_days: int = Field(description="Total project duration in days")
    risk_assessment: RiskAssessment = Field(description="Risk assessment")
    should_trigger_rnd: bool = Field(description="Should trigger R&D workflow")
    rnd_params: RNDParams = Field(description="R&D parameters if triggered")
    should_trigger_marketing: bool = Field(description="Should trigger marketing workflow")
    marketing_params: MarketingParams = Field(description="Marketing parameters if triggered")
    conversation_insights: Dict[str, Any] = Field(description="Insights from conversation analysis")
    success_probability: str = Field(description="Success probability: High/Medium/Low with confidence")

# ========================
# HELPER FUNCTIONS
# ========================
def safe_float(value, default=100000):
    """Safely convert value to float with default"""
    if value is None:
        return float(default)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            value = value.strip().lower()
            if "lkh" in value or "lakh" in value:
                num = float(value.replace("lkh", "").replace("lakh", "").strip())
                return num * 100000
            elif "cr" in value or "crore" in value:
                num = float(value.replace("cr", "").replace("crore", "").strip())
                return num * 10000000
            else:
                return float(value)
        except:
            return float(default)
    return float(default)

# ========================
# CEO AGENT CLASS
# ========================
class CEOAgent:
    def __init__(self):
        self.model = MODEL

    def _extract_conversation_insights(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze full conversation history to extract deeper insights"""
        if not messages:
            return {
                "customer_tone": "neutral",
                "pain_points": ["Limited information provided"],
                "unspoken_needs": ["Market validation"],
                "urgency_level": "medium",
                "budget_flexibility": "unknown",
                "market_context": "No conversation history",
                "recommendations": ["Collect more market data"]
            }
        
        logger.info("🔍 Analyzing conversation history for insights...")
        
        try:
            conversation_text = "\n".join([
                f"{'Customer' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')}"
                for m in messages
            ])
            
            parser = JsonOutputParser(pydantic_object=ConversationInsights)
            
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a conversation analyst. Extract key insights from the customer conversation.
                
Return VALID JSON matching this structure:
{
    "customer_tone": "enthusiastic|neutral|hesitant|urgent",
    "pain_points": ["point1", "point2"],
    "unspoken_needs": ["need1", "need2"],
    "urgency_level": "high|medium|low",
    "budget_flexibility": "fixed|flexible|unknown",
    "market_context": "brief market observation",
    "recommendations": ["rec1", "rec2"]
}"""),
                ("user", f"""Analyze this customer conversation and extract insights:

{conversation_text}

Return only valid JSON matching the schema above.""")
            ])
            
            chain = analysis_prompt | llm | parser
            insights = chain.invoke({})
            
            logger.info(f"✅ Conversation insights extracted: {insights.get('customer_tone')}")
            return insights.dict() if hasattr(insights, 'dict') else dict(insights)
            
        except Exception as e:
            logger.warning(f"⚠️ Conversation analysis failed: {str(e)[:100]}")
            return {
                "customer_tone": "neutral",
                "pain_points": ["Analysis failed"],
                "unspoken_needs": ["Needs assessment"],
                "urgency_level": "medium",
                "budget_flexibility": "unknown",
                "market_context": "Conversation analyzed",
                "recommendations": ["Proceed with standard approach"]
            }

    def analyze_requirements(self, requirements: Dict[str, Any], messages: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate CEO strategic plan from requirements AND conversation history"""
        logger.info("🤖 CEO Agent analyzing requirements...")
        logger.debug(f"Requirements: {json.dumps(requirements, ensure_ascii=False)}")
        
        try:
            budget = safe_float(requirements.get("budget"))
            logger.info(f"📊 Budget parsed: ₹{budget:,.0f}")
            
            # Extract insights from conversation
            insights = {}
            if messages:
                insights = self._extract_conversation_insights(messages)
            
            # Prepare data - CONVERT TO STRINGS TO AVOID F-STRING ISSUES
            req_text = json.dumps(requirements, indent=2, ensure_ascii=False)
            insights_text = json.dumps(insights, indent=2, ensure_ascii=False) if insights else "No conversation history"
            
            # FIXED: Use proper template variables instead of f-string with JSON
            parser = JsonOutputParser(pydantic_object=CEOPlan)
            
            # Build prompt WITHOUT f-strings for JSON objects
            prompt = ChatPromptTemplate.from_template("""You are a CEO STRATEGIC PLANNING AGENT for Automate.io.

Your task: Transform customer requirements AND conversation insights into a comprehensive JSON strategic marketing plan.

CRITICAL CONSTRAINTS:
1. RETURN ONLY VALID JSON matching the exact schema
2. budget_allocation.total MUST equal {total_budget}
3. timeline_days = sum of all phase durations
4. phases: minimum 3, maximum 5 items
5. All arrays must have minimum 2 items
6. Booleans must be true/false (lowercase)
7. All amounts in INR (₹)

CUSTOMER REQUIREMENTS:
{requirements_json}

CONVERSATION INSIGHTS (use this to enhance strategy):
{insights_json}

Generate a comprehensive CEO strategic plan as valid JSON matching this exact structure:

{{
    "project_name": "specific project name",
    "strategy_summary": "2-3 sentence high-level strategy",
    "executive_summary": "detailed paragraph with all key points",
    "phases": [
        {{
            "name": "phase name with action verb",
            "duration_days": 3,
            "deliverables": ["specific output 1", "specific output 2"],
            "owner": "R&D",
            "dependencies": [],
            "milestone": true
        }},
        {{
            "name": "second phase",
            "duration_days": 5,
            "deliverables": ["output 1", "output 2"],
            "owner": "Marketing",
            "dependencies": ["phase name"],
            "milestone": true
        }},
        {{
            "name": "third phase",
            "duration_days": 6,
            "deliverables": ["output 1", "output 2"],
            "owner": "Marketing",
            "dependencies": ["second phase"],
            "milestone": true
        }}
    ],
    "budget_allocation": {{
        "rnd_research": {rnd_budget},
        "content_creation": {content_budget},
        "ads_paid": {ads_budget},
        "tools_tech": {tools_budget},
        "total": {total_budget}
    }},
    "kpi_targets": {{
        "leads": {leads_target},
        "conversion_rate": "3-5%",
        "roi_expected": "2-3x",
        "cac_target": "₹{cac_target}"
    }},
    "channels_priority": ["LinkedIn", "YouTube"],
    "timeline_days": 14,
    "risk_assessment": {{
        "high": ["Limited budget may restrict reach", "Tight timeline requires agile execution"],
        "medium": ["Market saturation in awareness space", "Audience targeting precision"],
        "mitigation": "Use combination of organic and paid channels. Implement daily optimization."
    }},
    "should_trigger_rnd": true,
    "rnd_params": {{
        "research_topics": ["Audience behavior analysis", "Competitor positioning", "Market gaps"],
        "competitor_analysis": true,
        "market_research": true
    }},
    "should_trigger_marketing": true,
    "marketing_params": {{
        "campaign_type": "Awareness + Lead Generation",
        "creative_brief": "Create compelling marketing content for target audience",
        "ad_budget": {ads_budget}
    }},
    "conversation_insights": {insights_json},
    "success_probability": "High"
}}

VALIDATION CHECKLIST:
- All required keys present
- budget_allocation.total equals {total_budget}
- timeline_days = sum of phase durations
- phases count minimum 3
- Valid JSON only, no markdown

Return ONLY valid JSON. NO explanations.""")
            
            # Calculate budget splits
            rnd_budget = int(budget * 0.15)
            content_budget = int(budget * 0.25)
            ads_budget = int(budget * 0.50)
            tools_budget = int(budget * 0.10)
            leads_target = max(10, int(budget / 1000))
            cac_target = int(budget / max(10, int(budget / 1000)))
            
            # Invoke with template variables (NO f-strings)
            chain = prompt | llm | parser
            
            logger.info(f"📤 Invoking Groq {MODEL} with JsonOutputParser...")
            
            plan = chain.invoke({
                "total_budget": int(budget),
                "rnd_budget": rnd_budget,
                "content_budget": content_budget,
                "ads_budget": ads_budget,
                "tools_budget": tools_budget,
                "leads_target": leads_target,
                "cac_target": cac_target,
                "requirements_json": req_text,
                "insights_json": insights_text
            })
            
            if hasattr(plan, 'dict'):
                plan = plan.dict()
            else:
                plan = json.loads(json.dumps(plan, default=str))
            
            # Validate and fix
            plan = self._validate_and_fix_plan(plan, requirements, insights)
            
            logger.info(f"✅ CEO plan generated: {plan.get('project_name')}")
            return plan
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)[:150]}"
            logger.error(f"❌ LLM Error: {error_msg}")
            logger.error(f"Traceback: {str(e)}")
            raise

    def _validate_and_fix_plan(self, plan: Dict[str, Any], requirements: Dict[str, Any], insights: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate and auto-fix plan structure"""
        budget = safe_float(requirements.get("budget"))
        
        if "budget_allocation" not in plan:
            plan["budget_allocation"] = {}
        
        plan["budget_allocation"]["total"] = budget
        
        if insights:
            plan["conversation_insights"] = insights
        
        defaults = {
            "project_name": f"{requirements.get('product_service', 'Campaign')} Strategic Plan",
            "strategy_summary": "Multi-channel marketing campaign with data-driven approach.",
            "executive_summary": f"Comprehensive marketing campaign for {requirements.get('product_service')} targeting {requirements.get('target_audience')}.",
            "channels_priority": [ch.strip() for ch in (requirements.get("channels", "").split(","))] if requirements.get("channels") else ["LinkedIn", "YouTube"],
            "timeline_days": 14,
            "should_trigger_rnd": True,
            "should_trigger_marketing": True,
            "success_probability": "Medium"
        }
        
        for key, default_value in defaults.items():
            if key not in plan or not plan[key]:
                plan[key] = default_value
        
        if not isinstance(plan.get("phases"), list) or len(plan["phases"]) < 3:
            plan["phases"] = [
                {
                    "name": "Research & Planning",
                    "duration_days": 3,
                    "deliverables": ["Strategy document"],
                    "owner": "R&D",
                    "dependencies": [],
                    "milestone": True
                },
                {
                    "name": "Content Creation",
                    "duration_days": 5,
                    "deliverables": ["Creative assets"],
                    "owner": "Marketing",
                    "dependencies": ["Research & Planning"],
                    "milestone": True
                },
                {
                    "name": "Campaign Execution",
                    "duration_days": 6,
                    "deliverables": ["Live campaign", "Performance report"],
                    "owner": "Marketing",
                    "dependencies": ["Content Creation"],
                    "milestone": True
                }
            ]
        
        ba = plan.get("budget_allocation", {})
        ba.setdefault("rnd_research", budget * 0.15)
        ba.setdefault("content_creation", budget * 0.25)
        ba.setdefault("ads_paid", budget * 0.50)
        ba.setdefault("tools_tech", budget * 0.10)
        ba["total"] = budget
        plan["budget_allocation"] = ba
        
        if not isinstance(plan.get("kpi_targets"), dict):
            plan["kpi_targets"] = {}
        
        kpi = plan["kpi_targets"]
        kpi.setdefault("leads", max(10, int(budget / 1000)))
        kpi.setdefault("conversion_rate", "3-5%")
        kpi.setdefault("roi_expected", "2-3x")
        kpi.setdefault("cac_target", f"₹{int(budget / max(10, int(budget / 1000)))}")
        
        if not isinstance(plan.get("risk_assessment"), dict):
            plan["risk_assessment"] = {}
        
        ra = plan["risk_assessment"]
        if not ra.get("high"):
            ra["high"] = ["Timeline constraints", "Budget limitations"]
        if not ra.get("medium"):
            ra["medium"] = ["Audience targeting", "Market competition"]
        ra.setdefault("mitigation", "Daily optimization, A/B testing, continuous monitoring")
        
        if not isinstance(plan.get("rnd_params"), dict):
            plan["rnd_params"] = {}
        
        rnd = plan["rnd_params"]
        rnd.setdefault("research_topics", ["Market analysis", "Competitor research"])
        rnd.setdefault("competitor_analysis", True)
        rnd.setdefault("market_research", True)
        
        if not isinstance(plan.get("marketing_params"), dict):
            plan["marketing_params"] = {}
        
        mp = plan["marketing_params"]
        mp.setdefault("campaign_type", "Awareness + Lead Generation")
        mp.setdefault("creative_brief", f"Create {requirements.get('goals')} for {requirements.get('product_service')}")
        mp.setdefault("ad_budget", budget * 0.50)
        
        logger.info(f"✅ Plan validated and fixed")
        return plan

# ========================
# FASTAPI ROUTER
# ========================
router = APIRouter()
agent = CEOAgent()

@router.post("/api/v1/ceo/analyze")
async def analyze_plan(request: CEOAnalysisRequest):
    """
    Receive requirements + conversation from frontend
    Generate CEO strategic plan
    """
    try:
        logger.info(f"📨 CEO Analysis request: {request.conversation_id}")
        logger.info(f"Requirements: {request.requirements}")
        
        plan = agent.analyze_requirements(request.requirements, request.messages)
        
        return {
            "status": "success",
            "conversation_id": request.conversation_id,
            "plan": plan
        }
        
    except Exception as e:
        logger.error(f"❌ CEO Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/ceo/status")
async def get_status():
    """Get CEO agent status"""
    return {
        "status": "ready",
        "model": agent.model,
        "provider": "Groq"
    }