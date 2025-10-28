"""
Integrated Pipeline Script
Combines preprocessing → research → writing → editing → evaluation
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import our modules
from preprocessing import TextFileLoader, CharacterTextSplitter, TrafficDataPreprocessor
from preprocessing.vector_database import EnhancedVectorDatabase
from preprocessing.document_loaders import EnhancedTextFileLoader, PDFLoader, TrafficDocumentProcessor
from evaluation import RagasEvaluator
from research import DeepResearchAgent
from retrieval import AdvancedRetrievalSystem
from synthetic_data import SyntheticDataGenerator
from agents import SupervisorAgent, ResearchAgent, WriterAgent, EditorAgent, EvaluatorAgent
from workflow import TraffixWorkflow
from services.data_services import DataIntegrationService
from services.vector_service import VectorService


class IntegratedTraffixPipeline:
    """Integrated pipeline combining all modules"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.pipeline")
        self.setup_logging()
        
        # Initialize components
        self.data_service = DataIntegrationService()
        self.vector_service = VectorService()
        self.preprocessor = TrafficDataPreprocessor()
        self.vector_db = EnhancedVectorDatabase(self.vector_service)
        self.ragas_evaluator = RagasEvaluator()
        self.deep_research = DeepResearchAgent()
        self.workflow = TraffixWorkflow()
        
        # Initialize new components from other assignments
        self.document_processor = TrafficDocumentProcessor()
        self.advanced_retrieval = AdvancedRetrievalSystem(self.vector_service)
        self.synthetic_generator = SyntheticDataGenerator()
        
        # Initialize agents
        self.supervisor = SupervisorAgent()
        self.research_agent = ResearchAgent()
        self.writer_agent = WriterAgent()
        self.editor_agent = EditorAgent()
        self.evaluator_agent = EvaluatorAgent()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def run_complete_pipeline(
        self,
        user_query: str,
        location: str,
        mode: str = "deep",
        export_formats: List[str] = None
    ) -> Dict[str, Any]:
        """Run the complete integrated pipeline"""
        
        self.logger.info(f"Starting integrated pipeline for {location}")
        start_time = datetime.now()
        
        try:
            # Step 1: Preprocessing
            self.logger.info("Step 1: Data Preprocessing")
            preprocessed_data = await self._preprocess_data(location)
            
            # Step 2: Research
            self.logger.info("Step 2: Research Phase")
            research_results = await self._conduct_research(user_query, location, preprocessed_data)
            
            # Step 3: Writing
            self.logger.info("Step 3: Writing Phase")
            written_content = await self._generate_content(research_results, mode)
            
            # Step 4: Editing
            self.logger.info("Step 4: Editing Phase")
            edited_content = await self._edit_content(written_content, research_results)
            
            # Step 5: Evaluation
            self.logger.info("Step 5: Evaluation Phase")
            evaluation_results = await self._evaluate_content(edited_content, research_results)
            
            # Step 6: Export
            self.logger.info("Step 6: Export Phase")
            export_results = await self._export_content(edited_content, export_formats or ["html"])
            
            # Calculate total time
            total_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "user_query": user_query,
                "location": location,
                "mode": mode,
                "preprocessed_data": preprocessed_data,
                "research_results": research_results,
                "written_content": written_content,
                "edited_content": edited_content,
                "evaluation_results": evaluation_results,
                "export_results": export_results,
                "pipeline_metadata": {
                    "total_processing_time": total_time,
                    "completed_at": datetime.now().isoformat(),
                    "steps_completed": 6
                }
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_metadata": {
                    "failed_at": datetime.now().isoformat(),
                    "error_step": "unknown"
                }
            }
    
    async def _preprocess_data(self, location: str) -> Dict[str, Any]:
        """Preprocess traffic data"""
        
        # Collect raw data
        raw_data = await self.data_service.collect_all_data(
            location=location,
            time_range_hours=168,  # 1 week
            mode="deep"
        )
        
        # Preprocess the data
        preprocessed = self.preprocessor.preprocess_traffic_data(raw_data)
        
        # Build vector database
        await self.vector_db.abuild_from_traffic_data(raw_data)
        
        return {
            "raw_data": raw_data,
            "preprocessed": preprocessed,
            "vector_db_stats": self.vector_db.get_statistics()
        }
    
    async def _conduct_research(
        self,
        user_query: str,
        location: str,
        preprocessed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        # Use the workflow for research
        workflow_result = await self.workflow.run_workflow(
            user_query=user_query,
            location=location,
            mode="deep"
        )
        
        # Also conduct deep research
        deep_research_result = await self.deep_research.conduct_deep_research(
            research_question=user_query,
            location=location,
            time_range_hours=168
        )
        
        return {
            "workflow_result": workflow_result,
            "deep_research": deep_research_result,
            "preprocessed_data": preprocessed_data
        }
    
    async def _generate_content(
        self,
        research_results: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        
        # Extract research data
        workflow_result = research_results.get("workflow_result", {})
        final_output = workflow_result.get("final_output", {})
        
        # Generate content using writer agent
        writer_input = {
            "research_data": final_output.get("research_data", {}),
            "location": final_output.get("location", "Unknown"),
            "query_type": "deep_research",
            "narrative_style": "professional",
            "audience": "analysts"
        }
        
        writer_task = await self.writer_agent.execute_task(writer_input)
        
        if writer_task.status != "completed":
            raise Exception(f"Writing failed: {writer_task.error_message}")
        
        return writer_task.output_data
    
    async def _edit_content(
        self,
        written_content: Dict[str, Any],
        research_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        # Prepare content for editing
        content_to_edit = written_content.get("detailed_narrative", "")
        research_data = research_results.get("workflow_result", {}).get("final_output", {}).get("research_data", {})
        
        editor_input = {
            "content": content_to_edit,
            "source_data": research_data,
            "location": research_data.get("location", "Unknown"),
            "audience": "analysts",
            "purpose": "analysis",
            "context": "traffic analysis"
        }
        
        editor_task = await self.editor_agent.execute_task(editor_input)
        
        if editor_task.status != "completed":
            raise Exception(f"Editing failed: {editor_task.error_message}")
        
        return editor_task.output_data
    
    async def _evaluate_content(
        self,
        edited_content: Dict[str, Any],
        research_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        # Prepare content for evaluation
        content_to_evaluate = edited_content.get("corrected_content", "")
        research_data = research_results.get("workflow_result", {}).get("final_output", {}).get("research_data", {})
        
        evaluator_input = {
            "response": content_to_evaluate,
            "context": research_data,
            "question": research_results.get("workflow_result", {}).get("user_query", ""),
            "ground_truth": {
                "expected_findings": research_data.get("research_insights", {}).get("key_findings", []),
                "expected_causes": research_data.get("cause_analysis", {}).get("primary_causes", []),
                "expected_recommendations": research_data.get("research_insights", {}).get("recommendations", [])
            }
        }
        
        evaluator_task = await self.evaluator_agent.execute_task(evaluator_input)
        
        if evaluator_task.status != "completed":
            raise Exception(f"Evaluation failed: {evaluator_task.error_message}")
        
        return evaluator_task.output_data
    
    async def _export_content(
        self,
        edited_content: Dict[str, Any],
        export_formats: List[str]
    ) -> Dict[str, Any]:
        
        export_results = {}
        
        for format_type in export_formats:
            try:
                if format_type == "html":
                    content = edited_content.get("corrected_content", "")
                    export_results[format_type] = {
                        "success": True,
                        "content": f"<html><body><h1>Traffic Analysis Report</h1><p>{content}</p></body></html>",
                        "file_path": f"traffic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    }
                elif format_type == "pdf":
                    # Placeholder for PDF generation
                    export_results[format_type] = {
                        "success": True,
                        "message": "PDF export not yet implemented",
                        "file_path": f"traffic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    }
                elif format_type == "email":
                    # Placeholder for email export
                    export_results[format_type] = {
                        "success": True,
                        "message": "Email export not yet implemented",
                        "recipients": []
                    }
                else:
                    export_results[format_type] = {
                        "success": False,
                        "error": f"Unsupported format: {format_type}"
                    }
                    
            except Exception as e:
                export_results[format_type] = {
                    "success": False,
                    "error": str(e)
                }
        
        return export_results
    
    async def run_quick_analysis(
        self,
        user_query: str,
        location: str
    ) -> Dict[str, Any]:
        """Run quick analysis using the workflow"""
        
        return await self.workflow.run_workflow(
            user_query=user_query,
            location=location,
            mode="quick"
        )
    
    async def run_anomaly_investigation(
        self,
        user_query: str,
        location: str
    ) -> Dict[str, Any]:
        """Run anomaly investigation"""
        
        return await self.workflow.run_workflow(
            user_query=user_query,
            location=location,
            mode="anomaly_investigation"
        )
    
    def save_pipeline_state(self, results: Dict[str, Any], filepath: str):
        """Save pipeline state to file"""
        import json
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Pipeline state saved to {filepath}")


async def main():
    """Main function to demonstrate the integrated pipeline"""
    
    # Initialize pipeline
    pipeline = IntegratedTraffixPipeline()
    
    # Example queries
    queries = [
        {
            "query": "Why was congestion higher than normal on I-95 today?",
            "location": "I-95 North",
            "mode": "anomaly_investigation"
        },
        {
            "query": "Analyze traffic patterns for Route 50",
            "location": "Route 50 East", 
            "mode": "deep"
        },
        {
            "query": "Summarize this week's mobility highlights for leadership",
            "location": "I-495 Beltway",
            "mode": "leadership_summary"
        }
    ]
    
    # Run pipeline for each query
    for i, query_data in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Running Pipeline {i}: {query_data['query']}")
        print(f"{'='*60}")
        
        try:
            result = await pipeline.run_complete_pipeline(
                user_query=query_data["query"],
                location=query_data["location"],
                mode=query_data["mode"],
                export_formats=["html", "pdf", "email"]
            )
            
            if result["success"]:
                print(f"✅ Pipeline {i} completed successfully")
                print(f"Processing time: {result['pipeline_metadata']['total_processing_time']:.2f} seconds")
                
                # Save results
                pipeline.save_pipeline_state(
                    result, 
                    f"pipeline_results_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
            else:
                print(f"❌ Pipeline {i} failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Pipeline {i} failed with exception: {e}")


if __name__ == "__main__":
    asyncio.run(main())
