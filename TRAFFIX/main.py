"""
Main orchestration system for Traffix
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from agents import SupervisorAgent, ResearchAgent, WriterAgent, EditorAgent, EvaluatorAgent
from workflow import TraffixWorkflow
from modes import QuickModeProcessor, DeepModeProcessor
from modes.anomaly_investigation import AnomalyInvestigationProcessor
from modes.leadership_summary import LeadershipSummaryProcessor
from agents.pattern_analyzer import PatternAnalyzerAgent
from models import ReportMode, UserQuestion
from config import settings
from integrated_pipeline import IntegratedTraffixPipeline


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("traffix.main")

# Initialize FastAPI app
app = FastAPI(
    title="Traffix - AI Storytelling for Transportation Analytics",
    description="AI-powered storytelling assistant that integrates structured traffic data (RITIS) and unstructured sources (news articles, incident summaries) to reduce analysts' manual investigation and provide quick or deep narrative reports.",
    version="1.0.0"
)

# Initialize integrated pipeline
integrated_pipeline = IntegratedTraffixPipeline()

# Initialize workflow and agents
traffix_workflow = TraffixWorkflow()
supervisor_agent = SupervisorAgent()
research_agent = ResearchAgent()
writer_agent = WriterAgent()
editor_agent = EditorAgent()
evaluator_agent = EvaluatorAgent()

# Initialize processors (legacy support)
quick_processor = QuickModeProcessor()
deep_processor = DeepModeProcessor()
anomaly_processor = AnomalyInvestigationProcessor()
leadership_processor = LeadershipSummaryProcessor()
pattern_analyzer = PatternAnalyzerAgent()

# Request/Response models
class AnalysisRequest(BaseModel):
    location: str
    mode: str = "quick"  # "quick", "deep", "anomaly_investigation", "leadership_summary"
    time_range_hours: int = 24
    analysis_depth: Optional[str] = None  # For deep mode
    output_format: str = "html"  # "html", "json", "markdown", "pdf"
    time_period: Optional[str] = None  # For anomaly investigation and leadership summary
    baseline_period: Optional[str] = None  # For anomaly investigation
    export_options: Optional[Dict[str, Any]] = None  # Email and multi-format export options

class AnalysisResponse(BaseModel):
    success: bool
    location: str
    mode: str
    processing_time_seconds: float
    report_path: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    active_analyses: int
    system_health: str
    uptime_seconds: float

# Global state
startup_time = datetime.now()
active_analyses = 0

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    logger.info("Starting Traffix system...")
    logger.info(f"Configuration loaded: {settings.log_level} log level")
    logger.info("Traffix system started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Traffix system...")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with system information"""
    uptime = (datetime.now() - startup_time).total_seconds()
    return f"""
    <html>
        <head>
            <title>Traffix - AI Storytelling for Transportation Analytics</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 20px; }}
                .status {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .endpoints {{ margin: 20px 0; }}
                .endpoint {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚦 Traffix</h1>
                    <h2>AI Storytelling for Transportation Analytics</h2>
                </div>
                
                <div class="status">
                    <h3>System Status</h3>
                    <p><strong>Status:</strong> Running</p>
                    <p><strong>Uptime:</strong> {uptime:.1f} seconds</p>
                    <p><strong>Active Analyses:</strong> {active_analyses}</p>
                </div>
                
                <div class="endpoints">
                    <h3>Available Endpoints</h3>
                    <div class="endpoint">
                        <strong>POST /analyze</strong> - Run traffic analysis
                    </div>
                    <div class="endpoint">
                        <strong>GET /status</strong> - System status
                    </div>
                    <div class="endpoint">
                        <strong>GET /health</strong> - Health check
                    </div>
                    <div class="endpoint">
                        <strong>GET /docs</strong> - API documentation
                    </div>
                </div>
                
                <div style="margin-top: 30px; color: #666;">
                    <p>Traffix helps traffic analysts understand congestion patterns by integrating 
                    structured traffic data (RITIS) with unstructured sources (news, incidents).</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds()
    }

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    uptime = (datetime.now() - startup_time).total_seconds()
    return StatusResponse(
        status="running",
        active_analyses=active_analyses,
        system_health="healthy",
        uptime_seconds=uptime
    )

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_traffic(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Run traffic analysis in specified mode"""
    global active_analyses
    
    try:
        active_analyses += 1
        logger.info(f"Starting {request.mode} analysis for {request.location}")
        
        start_time = datetime.now()
        
        if request.mode == "quick":
            result = await quick_processor.process_quick_analysis(
                location=request.location,
                time_range_hours=request.time_range_hours
            )
        elif request.mode == "deep":
            analysis_depth = request.analysis_depth or "comprehensive"
            result = await deep_processor.process_deep_analysis(
                location=request.location,
                time_range_hours=request.time_range_hours,
                analysis_depth=analysis_depth
            )
        elif request.mode == "anomaly_investigation":
            time_period = request.time_period or "today"
            result = await anomaly_processor.investigate_anomaly(
                location=request.location,
                time_period=time_period,
                baseline_period=request.baseline_period
            )
        elif request.mode == "leadership_summary":
            period = request.time_period or "week"
            result = await leadership_processor.generate_leadership_summary(
                location=request.location,
                period=period
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid mode. Use 'quick', 'deep', 'anomaly_investigation', or 'leadership_summary'")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        active_analyses -= 1
        
        if result["success"]:
            return AnalysisResponse(
                success=True,
                location=request.location,
                mode=request.mode,
                processing_time_seconds=processing_time,
                report_path=result.get("report_data", {}).get("report_path"),
                summary=result.get("summary") or result.get("comprehensive_summary")
            )
        else:
            return AnalysisResponse(
                success=False,
                location=request.location,
                mode=request.mode,
                processing_time_seconds=processing_time,
                error=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        active_analyses -= 1
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/quick")
async def quick_analysis(request: AnalysisRequest):
    """Convenience endpoint for quick analysis"""
    request.mode = "quick"
    return await analyze_traffic(request, BackgroundTasks())

@app.post("/analyze/deep")
async def deep_analysis(request: AnalysisRequest):
    """Convenience endpoint for deep analysis"""
    request.mode = "deep"
    return await analyze_traffic(request, BackgroundTasks())

@app.post("/analyze/anomaly")
async def anomaly_investigation(request: AnalysisRequest):
    """Convenience endpoint for anomaly investigation"""
    request.mode = "anomaly_investigation"
    return await analyze_traffic(request, BackgroundTasks())

@app.post("/analyze/leadership")
async def leadership_summary(request: AnalysisRequest):
    """Convenience endpoint for leadership summary"""
    request.mode = "leadership_summary"
    return await analyze_traffic(request, BackgroundTasks())

@app.post("/analyze/workflow")
async def analyze_with_workflow(request: AnalysisRequest):
    """New analysis endpoint using the agent workflow architecture"""
    try:
        logger.info(f"Processing {request.mode} analysis with workflow for {request.location}")
        
        # Use the new workflow for all analysis types
        user_query = f"Analyze traffic patterns for {request.location}"
        if request.mode == "anomaly_investigation":
            user_query = f"Why was congestion higher or lower than normal in {request.location}?"
        elif request.mode == "leadership_summary":
            user_query = f"Summarize this week's mobility highlights for {request.location} in a report suitable for leadership"
        elif request.mode == "deep":
            user_query = f"Provide a detailed analysis of traffic patterns in {request.location}"
        
        # Run the workflow
        workflow_result = await traffix_workflow.run_workflow(
            user_query=user_query,
            location=request.location,
            mode=request.mode
        )
        
        if workflow_result.get("workflow_state") == "error":
            raise Exception(f"Workflow failed: {workflow_result.get('errors', 'Unknown error')}")
        
        # Extract final output
        final_output = workflow_result.get("final_output", {})
        
        return {
            "success": True,
            "location": request.location,
            "mode": request.mode,
            "result": final_output,
            "workflow_metadata": final_output.get("workflow_metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Workflow analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/integrated")
async def analyze_with_integrated_pipeline(request: AnalysisRequest):
    """Integrated pipeline endpoint with preprocessing → research → writing → editing → evaluation"""
    try:
        logger.info(f"Processing {request.mode} analysis with integrated pipeline for {request.location}")
        
        # Prepare user query
        user_query = f"Analyze traffic patterns for {request.location}"
        if request.mode == "anomaly_investigation":
            user_query = f"Why was congestion higher or lower than normal in {request.location}?"
        elif request.mode == "leadership_summary":
            user_query = f"Summarize this week's mobility highlights for {request.location} in a report suitable for leadership"
        elif request.mode == "deep":
            user_query = f"Provide a detailed analysis of traffic patterns in {request.location}"
        
        # Run the integrated pipeline
        pipeline_result = await integrated_pipeline.run_complete_pipeline(
            user_query=user_query,
            location=request.location,
            mode=request.mode,
            export_formats=["html", "pdf", "email"]
        )
        
        if not pipeline_result["success"]:
            raise Exception(f"Pipeline failed: {pipeline_result.get('error', 'Unknown error')}")
        
        return {
            "success": True,
            "location": request.location,
            "mode": request.mode,
            "result": pipeline_result,
            "pipeline_metadata": pipeline_result.get("pipeline_metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Integrated pipeline analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get a specific report by ID"""
    # This would typically look up the report in a database
    # For now, we'll return a placeholder
    return {
        "report_id": report_id,
        "status": "not_found",
        "message": "Report lookup not implemented yet"
    }

@app.get("/insights/{location}")
async def get_location_insights(location: str, mode: str = "quick"):
    """Get quick insights for a location"""
    try:
        if mode == "quick":
            result = await quick_processor.generate_daily_summary(location)
            insights = quick_processor.get_quick_insights(result.get("analysis_result", {}))
        else:
            result = await deep_processor.generate_weekly_report(location)
            insights = deep_processor.get_deep_insights(result.get("analysis_results", {}))
        
        return {
            "location": location,
            "mode": mode,
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get insights for {location}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(question: UserQuestion):
    """Answer specific user questions about traffic patterns"""
    try:
        logger.info(f"Processing user question: {question.specific_question}")
        
        if question.question_type == "anomaly_investigation":
            result = await anomaly_processor.answer_user_question(question)
        elif question.question_type == "leadership_summary":
            result = await leadership_processor.answer_leadership_question(question)
        else:
            # Default to quick analysis for other question types
            result = await quick_processor.process_quick_analysis(
                location=question.location,
                time_range_hours=24
            )
        
        return {
            "question": question.specific_question,
            "question_type": question.question_type,
            "location": question.location,
            "answer": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/patterns")
async def analyze_patterns(location: str, analysis_period: str = "week"):
    """Analyze recurring congestion patterns and generate mitigation strategies"""
    try:
        logger.info(f"Analyzing patterns for {location} over {analysis_period}")
        
        # Collect data for pattern analysis
        from services import DataIntegrationService
        data_service = DataIntegrationService()
        
        time_range_hours = 168 if analysis_period == "week" else 720 if analysis_period == "month" else 24
        collected_data = await data_service.collect_all_data(
            location=location,
            time_range_hours=time_range_hours,
            mode="deep"
        )
        
        # Analyze patterns
        pattern_input = {
            "collected_data": collected_data,
            "location": location,
            "analysis_period": analysis_period
        }
        
        pattern_task = await pattern_analyzer.execute_task(pattern_input)
        
        if pattern_task.status.value != "completed":
            raise Exception(f"Pattern analysis failed: {pattern_task.error_message}")
        
        return {
            "success": True,
            "location": location,
            "analysis_period": analysis_period,
            "pattern_analysis": pattern_task.output_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/modes")
async def get_available_modes():
    """Get information about available analysis modes and agent architecture"""
    return {
        "agent_architecture": {
            "description": "Multi-agent system with specialized roles",
            "agents": [
                {
                    "name": "Supervisor Agent",
                    "role": "Orchestrator",
                    "description": "Routes queries between research and writing teams, creates work plans"
                },
                {
                    "name": "Research Agent", 
                    "role": "Analyst",
                    "description": "Queries RITIS + Tavily, extracts key incidents, identifies causes"
                },
                {
                    "name": "Writer Agent",
                    "role": "Storyteller", 
                    "description": "Synthesizes data into narratives (concise summaries or detailed reports)"
                },
                {
                    "name": "Editor Agent",
                    "role": "Copy & Context Checker",
                    "description": "Ensures factual accuracy, readability, empathetic tone"
                },
                {
                    "name": "Evaluator Agent",
                    "role": "QA",
                    "description": "Uses RAGAS-style heuristics to improve pipeline quality"
                }
            ]
        },
        "modes": [
            {
                "name": "quick",
                "description": "Fast daily summaries optimized for speed",
                "typical_processing_time": "30-60 seconds",
                "data_sources": ["ritis", "news", "incidents"],
                "use_cases": ["Daily summaries", "Shift reports", "Incident summaries"],
                "agents_used": ["Supervisor", "Research", "Writer", "Evaluator"]
            },
            {
                "name": "deep",
                "description": "Comprehensive research reports with detailed analysis",
                "typical_processing_time": "2-5 minutes",
                "data_sources": ["ritis", "news", "incidents", "weather", "social"],
                "use_cases": ["Weekly reports", "Monthly analysis", "Incident investigations", "Trend analysis"],
                "agents_used": ["Supervisor", "Research", "Writer", "Editor", "Evaluator"]
            },
            {
                "name": "anomaly_investigation",
                "description": "Investigates why congestion patterns changed",
                "typical_processing_time": "1-3 minutes",
                "data_sources": ["ritis", "news", "incidents", "weather", "social"],
                "use_cases": ["Why was congestion higher/lower?", "What caused the anomaly?", "Root cause analysis"],
                "agents_used": ["Supervisor", "Research", "Writer", "Editor", "Evaluator"]
            },
            {
                "name": "leadership_summary",
                "description": "Executive summaries for transportation leadership",
                "typical_processing_time": "2-4 minutes",
                "data_sources": ["ritis", "news", "incidents", "weather", "social"],
                "use_cases": ["Weekly highlights", "Executive reports", "Leadership briefings"],
                "agents_used": ["Supervisor", "Research", "Writer", "Editor", "Evaluator"]
            },
            {
                "name": "pattern_analysis",
                "description": "Identifies recurring congestion patterns and mitigation strategies",
                "typical_processing_time": "3-5 minutes",
                "data_sources": ["ritis", "news", "incidents", "weather", "social"],
                "use_cases": ["Recurring pattern identification", "Mitigation strategy development", "Long-term planning"],
                "agents_used": ["Supervisor", "Research", "Writer", "Editor", "Evaluator"]
            }
        ],
        "user_questions": [
            "Why was congestion higher or lower than normal today?",
            "What major incidents occurred in my region this week?",
            "Did weather or other events affect travel time reliability today?",
            "Can you summarize this week's mobility highlights in a report suitable for leadership?",
            "What recurring congestion patterns should we address?",
            "What mitigation strategies would be most effective for our corridor?"
        ],
        "export_formats": ["html", "json", "markdown", "pdf"],
        "export_options": {
            "email": "Send reports via email",
            "multi_format": "Export in multiple formats simultaneously"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
