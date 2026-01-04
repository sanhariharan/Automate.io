"""
main.py - FIXED
Automate.io API Gateway - Production Ready
Customer Intake → CEO Planning → Agent Orchestration
"""
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Agent imports
from Backend.agents import customer as customer_agent
from Backend.agents import Ceo as ceo_agent_module

app = FastAPI(
    title="Automate.io API Gateway",
    description="Multi-agent marketing intelligence platform",
    version="2.0.0"
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Instantiate CEO Agent
CEO_AGENT = ceo_agent_module.CEOAgent()
logger.info(f"✅ CEO Agent initialized: {CEO_AGENT.model}")

# Project data directory
os.makedirs("data/projects", exist_ok=True)
os.makedirs("data/jobs", exist_ok=True)

# -------------------------
# Request Models
# -------------------------
class CustomerMessage(BaseModel):
    conversation_id: Optional[str] = None
    text: str

class CEORequest(BaseModel):
    conversation_id: Optional[str] = None
    requirements: Dict[str, Any]

class AgentTriggerRequest(BaseModel):
    project_id: str
    params: Dict[str, Any]

# -------------------------
# Customer Intake Endpoints
# -------------------------
@app.post("/api/v1/customer/message")
async def post_customer_message(msg: CustomerMessage):
    """Customer chat intake - collects requirements"""
    try:
        result = customer_agent.process_customer_message(msg.text, msg.conversation_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer agent error: {str(e)}")

@app.get("/api/v1/customer/{conversation_id}")
async def get_customer_conversation(conversation_id: str):
    """Get full conversation history"""
    try:
        return customer_agent.get_conversation(conversation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/customer/ready/{conversation_id}")
async def customer_ready_for_ceo(conversation_id: str):
    """Check if ready for CEO analysis"""
    try:
        return customer_agent.is_ready_for_ceo(conversation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/customer/export/{conversation_id}")
async def export_customer_for_ceo(conversation_id: str):
    """Export structured requirements for CEO"""
    try:
        requirements = customer_agent.export_for_ceo(conversation_id)
        return {"conversation_id": conversation_id, "requirements": requirements}
    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# CEO Strategic Planning
# -------------------------
@app.post("/api/v1/ceo/analyze")
async def ceo_analyze(req: CEORequest):
    """
    CEO Analysis: Generate strategic plan from requirements
    
    Generates:
    - Project roadmap (3-5 phases)
    - Budget allocation (R&D/Content/Ads)
    - KPI targets
    - Agent trigger decisions
    """
    try:
        conversation_id = req.conversation_id or f"proj_{int(datetime.now().timestamp())}"
        requirements = req.requirements
        
        logger.info(f"🤖 CEO Analysis starting: {requirements.get('product_service', 'Unknown')}")
        
        # Generate CEO plan
        plan = CEO_AGENT.analyze_requirements(requirements)
        
        if not plan:
            raise Exception("CEO Agent returned empty plan")
        
        # Persist project
        project_id = conversation_id
        project_path = f"data/projects/{project_id}.json"
        project_data = {
            "project_id": project_id,
            "conversation_id": conversation_id,
            "requirements": requirements,
            "ceo_plan": plan,
            "status": "planning_complete",
            "created_at": datetime.now().isoformat(),
            "agents_triggered": [],
            "model": CEO_AGENT.model
        }
        
        with open(project_path, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ CEO Plan saved: {project_id}")
        
        return {
            "status": "success",
            "project_id": project_id,
            "conversation_id": conversation_id,
            "plan": plan,
            "rnd_trigger": plan.get("should_trigger_rnd", False),
            "marketing_trigger": plan.get("should_trigger_marketing", False),
            "success_probability": plan.get("success_probability", "Medium")
        }
        
    except Exception as e:
        logger.error(f"❌ CEO Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CEO Analysis failed: {str(e)}")

@app.get("/api/v1/ceo/{project_id}")
async def get_ceo_plan(project_id: str):
    """Get saved CEO plan"""
    try:
        project_path = f"data/projects/{project_id}.json"
        with open(project_path, "r") as f:
            project_data = json.load(f)
        return project_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ceo/status")
async def ceo_status():
    """Get CEO Agent status - FIXED: Returns correct attributes"""
    try:
        return {
            "status": "online",
            "model": CEO_AGENT.model,  # FIXED: Was model_name
            "last_error": CEO_AGENT.last_error,  # FIXED: Direct access
            "plan_cached": CEO_AGENT.last_plan is not None
        }
    except Exception as e:
        logger.error(f"❌ CEO Status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# Agent Orchestration
# -------------------------
@app.post("/api/v1/rnd/trigger")
async def trigger_rnd_agent(trigger: AgentTriggerRequest):
    """Trigger R&D Research Agent"""
    try:
        project_id = trigger.project_id
        rnd_params = trigger.params
        
        # Create R&D job
        job_id = f"rnd_{int(datetime.now().timestamp())}"
        job_data = {
            "job_id": job_id,
            "project_id": project_id,
            "agent": "rnd",
            "params": rnd_params,
            "status": "queued",
            "created_at": datetime.now().isoformat()
        }
        
        job_path = f"data/jobs/{job_id}.json"
        with open(job_path, "w") as f:
            json.dump(job_data, f, indent=2)
        
        # Update project status
        project_path = f"data/projects/{project_id}.json"
        if os.path.exists(project_path):
            with open(project_path, "r+") as f:
                project = json.load(f)
                project["agents_triggered"].append({
                    "agent": "rnd",
                    "job_id": job_id,
                    "status": "queued",
                    "timestamp": datetime.now().isoformat()
                })
                f.seek(0)
                json.dump(project, f, indent=2)
        
        logger.info(f"🔬 R&D Agent triggered: {job_id}")
        return {
            "status": "success",
            "job_id": job_id,
            "agent": "rnd",
            "queue_status": "queued",
            "next_check": f"/api/v1/jobs/{job_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"R&D trigger failed: {str(e)}")

@app.post("/api/v1/marketing/trigger")
async def trigger_marketing_agent(trigger: AgentTriggerRequest):
    """Trigger Marketing Execution Agent"""
    try:
        project_id = trigger.project_id
        marketing_params = trigger.params
        
        # Create Marketing job
        job_id = f"mkt_{int(datetime.now().timestamp())}"
        job_data = {
            "job_id": job_id,
            "project_id": project_id,
            "agent": "marketing",
            "params": marketing_params,
            "status": "queued",
            "created_at": datetime.now().isoformat()
        }
        
        job_path = f"data/jobs/{job_id}.json"
        with open(job_path, "w") as f:
            json.dump(job_data, f, indent=2)
        
        # Update project
        project_path = f"data/projects/{project_id}.json"
        if os.path.exists(project_path):
            with open(project_path, "r+") as f:
                project = json.load(f)
                project["agents_triggered"].append({
                    "agent": "marketing",
                    "job_id": job_id,
                    "status": "queued",
                    "timestamp": datetime.now().isoformat()
                })
                f.seek(0)
                json.dump(project, f, indent=2)
        
        logger.info(f"📢 Marketing Agent triggered: {job_id}")
        return {
            "status": "success",
            "job_id": job_id,
            "agent": "marketing",
            "queue_status": "queued",
            "next_check": f"/api/v1/jobs/{job_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Marketing trigger failed: {str(e)}")

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get agent job status"""
    try:
        job_path = f"data/jobs/{job_id}.json"
        with open(job_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")

# -------------------------
# Health & Status
# -------------------------
@app.get("/")
async def root():
    """Root endpoint - list all services"""
    return {
        "status": "🚀 Automate.io API v2.0 - LIVE",
        "services": {
            "customer": [
                "POST /api/v1/customer/message",
                "GET  /api/v1/customer/{id}",
                "GET  /api/v1/customer/ready/{id}",
                "POST /api/v1/customer/export/{id}"
            ],
            "ceo": [
                "POST /api/v1/ceo/analyze",
                "GET  /api/v1/ceo/{project_id}",
                "GET  /api/v1/ceo/status"
            ],
            "agents": [
                "POST /api/v1/rnd/trigger",
                "POST /api/v1/marketing/trigger",
                "GET  /api/v1/jobs/{job_id}"
            ]
        },
        "ceo_agent": {
            "model": CEO_AGENT.model,
            "initialized": True,
            "plan_cached": CEO_AGENT.last_plan is not None
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ceo_agent": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)