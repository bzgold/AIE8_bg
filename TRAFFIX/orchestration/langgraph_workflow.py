"""
LangGraph orchestration for Traffix multi-agent system
"""
import logging
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from agents import DataCollectorAgent, AnalyzerAgent, StorytellerAgent, ReporterAgent
from agents.pattern_analyzer import PatternAnalyzerAgent
from services.vector_service import VectorService
from models import ReportMode
from tech_config import tech_settings


class TraffixState(TypedDict):
    """State for Traffix workflow"""
    # Input
    location: str
    mode: str
    time_period: str
    user_question: Optional[str]
    
    # Data
    collected_data: Dict[str, Any]
    vector_context: Dict[str, Any]
    
    # Analysis
    analysis_result: Dict[str, Any]
    pattern_analysis: Optional[Dict[str, Any]]
    
    # Output
    story_data: Dict[str, Any]
    report_data: Dict[str, Any]
    
    # Metadata
    workflow_status: str
    error_message: Optional[str]
    processing_time: float


class TraffixWorkflow:
    """LangGraph workflow for Traffix system"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.workflow")
        self.llm = ChatOpenAI(
            model=tech_settings.openai_model,
            openai_api_key=tech_settings.openai_api_key,
            temperature=0.1
        )
        
        # Initialize agents
        self.data_collector = DataCollectorAgent()
        self.analyzer = AnalyzerAgent()
        self.storyteller = StorytellerAgent()
        self.reporter = ReporterAgent()
        self.pattern_analyzer = PatternAnalyzerAgent()
        self.vector_service = VectorService()
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(TraffixState)
        
        # Add nodes
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("store_vectors", self._store_vectors_node)
        workflow.add_node("analyze_data", self._analyze_data_node)
        workflow.add_node("analyze_patterns", self._analyze_patterns_node)
        workflow.add_node("generate_story", self._generate_story_node)
        workflow.add_node("generate_report", self._generate_report_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Add edges
        workflow.set_entry_point("collect_data")
        
        workflow.add_edge("collect_data", "store_vectors")
        workflow.add_edge("store_vectors", "analyze_data")
        
        # Conditional edge for pattern analysis
        workflow.add_conditional_edges(
            "analyze_data",
            self._should_analyze_patterns,
            {
                "analyze_patterns": "analyze_patterns",
                "generate_story": "generate_story"
            }
        )
        
        workflow.add_edge("analyze_patterns", "generate_story")
        workflow.add_edge("generate_story", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Error handling
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    async def _collect_data_node(self, state: TraffixState) -> TraffixState:
        """Collect data from various sources"""
        try:
            self.logger.info(f"Collecting data for {state['location']}")
            
            # Determine time range based on mode
            time_range_hours = self._get_time_range_hours(state["mode"], state.get("time_period", "24h"))
            
            # Collect data
            collected_data = await self.data_collector.execute_task({
                "location": state["location"],
                "time_range_hours": time_range_hours,
                "mode": state["mode"]
            })
            
            if collected_data.status.value != "completed":
                state["workflow_status"] = "error"
                state["error_message"] = f"Data collection failed: {collected_data.error_message}"
                return state
            
            state["collected_data"] = collected_data.output_data
            state["workflow_status"] = "data_collected"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Data collection node failed: {e}")
            state["workflow_status"] = "error"
            state["error_message"] = str(e)
            return state
    
    async def _store_vectors_node(self, state: TraffixState) -> TraffixState:
        """Store collected data in vector database"""
        try:
            self.logger.info("Storing data in vector database")
            
            collected_data = state["collected_data"]
            location = state["location"]
            
            # Store different data types
            await self.vector_service.add_traffic_data(
                collected_data.get("traffic_data", []), location
            )
            await self.vector_service.add_news_data(
                collected_data.get("news_articles", []), location
            )
            await self.vector_service.add_incident_data(
                collected_data.get("incidents", []), location
            )
            
            # Get vector context for analysis
            query = f"Traffic analysis for {location} {state.get('user_question', '')}"
            vector_context = await self.vector_service.get_context_for_analysis(
                query=query,
                location=location,
                analysis_type=state["mode"]
            )
            
            state["vector_context"] = vector_context
            state["workflow_status"] = "vectors_stored"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Vector storage node failed: {e}")
            state["workflow_status"] = "error"
            state["error_message"] = str(e)
            return state
    
    async def _analyze_data_node(self, state: TraffixState) -> TraffixState:
        """Analyze collected data"""
        try:
            self.logger.info("Analyzing data")
            
            # Prepare analysis input with vector context
            analysis_input = {
                "collected_data": state["collected_data"],
                "vector_context": state["vector_context"],
                "location": state["location"],
                "mode": state["mode"]
            }
            
            # Perform analysis
            analysis_task = await self.analyzer.execute_task(analysis_input)
            
            if analysis_task.status.value != "completed":
                state["workflow_status"] = "error"
                state["error_message"] = f"Analysis failed: {analysis_task.error_message}"
                return state
            
            state["analysis_result"] = analysis_task.output_data
            state["workflow_status"] = "data_analyzed"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Analysis node failed: {e}")
            state["workflow_status"] = "error"
            state["error_message"] = str(e)
            return state
    
    async def _analyze_patterns_node(self, state: TraffixState) -> TraffixState:
        """Analyze patterns for deep analysis modes"""
        try:
            self.logger.info("Analyzing patterns")
            
            pattern_input = {
                "collected_data": state["collected_data"],
                "location": state["location"],
                "analysis_period": state.get("time_period", "week")
            }
            
            pattern_task = await self.pattern_analyzer.execute_task(pattern_input)
            
            if pattern_task.status.value != "completed":
                self.logger.warning(f"Pattern analysis failed: {pattern_task.error_message}")
                state["pattern_analysis"] = {}
            else:
                state["pattern_analysis"] = pattern_task.output_data
            
            state["workflow_status"] = "patterns_analyzed"
            return state
            
        except Exception as e:
            self.logger.error(f"Pattern analysis node failed: {e}")
            state["pattern_analysis"] = {}
            state["workflow_status"] = "patterns_analyzed"
            return state
    
    async def _generate_story_node(self, state: TraffixState) -> TraffixState:
        """Generate story from analysis"""
        try:
            self.logger.info("Generating story")
            
            story_input = {
                "analysis_result": state["analysis_result"],
                "collected_data": state["collected_data"],
                "vector_context": state["vector_context"],
                "pattern_analysis": state.get("pattern_analysis"),
                "location": state["location"],
                "mode": state["mode"],
                "user_question": state.get("user_question")
            }
            
            story_task = await self.storyteller.execute_task(story_input)
            
            if story_task.status.value != "completed":
                state["workflow_status"] = "error"
                state["error_message"] = f"Story generation failed: {story_task.error_message}"
                return state
            
            state["story_data"] = story_task.output_data
            state["workflow_status"] = "story_generated"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Story generation node failed: {e}")
            state["workflow_status"] = "error"
            state["error_message"] = str(e)
            return state
    
    async def _generate_report_node(self, state: TraffixState) -> TraffixState:
        """Generate final report"""
        try:
            self.logger.info("Generating report")
            
            report_input = {
                "story_data": state["story_data"],
                "location": state["location"],
                "mode": state["mode"],
                "output_format": "html"
            }
            
            report_task = await self.reporter.execute_task(report_input)
            
            if report_task.status.value != "completed":
                state["workflow_status"] = "error"
                state["error_message"] = f"Report generation failed: {report_task.error_message}"
                return state
            
            state["report_data"] = report_task.output_data
            state["workflow_status"] = "completed"
            
            return state
            
        except Exception as e:
            self.logger.error(f"Report generation node failed: {e}")
            state["workflow_status"] = "error"
            state["error_message"] = str(e)
            return state
    
    async def _error_handler_node(self, state: TraffixState) -> TraffixState:
        """Handle errors in the workflow"""
        self.logger.error(f"Workflow error: {state.get('error_message', 'Unknown error')}")
        state["workflow_status"] = "error"
        return state
    
    def _should_analyze_patterns(self, state: TraffixState) -> str:
        """Determine if pattern analysis should be performed"""
        mode = state["mode"]
        if mode in ["deep", "pattern_analysis", "leadership_summary"]:
            return "analyze_patterns"
        return "generate_story"
    
    def _get_time_range_hours(self, mode: str, time_period: str) -> int:
        """Get time range in hours based on mode and period"""
        if time_period.endswith("h"):
            return int(time_period[:-1])
        elif time_period.endswith("d"):
            return int(time_period[:-1]) * 24
        elif time_period.endswith("w"):
            return int(time_period[:-1]) * 168
        elif time_period.endswith("m"):
            return int(time_period[:-1]) * 720
        
        # Default based on mode
        mode_defaults = {
            "quick": 24,
            "deep": 168,
            "anomaly_investigation": 24,
            "leadership_summary": 168,
            "pattern_analysis": 168
        }
        
        return mode_defaults.get(mode, 24)
    
    async def run_analysis(self, location: str, mode: str, 
                          time_period: str = "24h", 
                          user_question: str = None) -> Dict[str, Any]:
        """Run the complete analysis workflow"""
        start_time = datetime.now()
        
        # Initialize state
        initial_state = TraffixState(
            location=location,
            mode=mode,
            time_period=time_period,
            user_question=user_question,
            collected_data={},
            vector_context={},
            analysis_result={},
            pattern_analysis=None,
            story_data={},
            report_data={},
            workflow_status="started",
            error_message=None,
            processing_time=0.0
        )
        
        try:
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            final_state["processing_time"] = processing_time
            
            self.logger.info(f"Workflow completed in {processing_time:.2f}s")
            return final_state
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "workflow_status": "error",
                "error_message": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
