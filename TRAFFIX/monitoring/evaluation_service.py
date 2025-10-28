"""
Monitoring and Evaluation Service using LangSmith and RAGAS
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from langsmith import Client
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    context_relevancy
)
from ragas.testset import TestsetGenerator
from langchain_openai import ChatOpenAI

from tech_config import tech_settings


class EvaluationService:
    """Service for monitoring and evaluating Traffix performance"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.evaluation")
        
        # Initialize LangSmith client
        self.langsmith_client = Client(
            api_key=tech_settings.langsmith_api_key,
            api_url=tech_settings.langsmith_endpoint
        )
        
        # Initialize LLM for evaluation
        self.llm = ChatOpenAI(
            model=tech_settings.openai_model,
            openai_api_key=tech_settings.openai_api_key,
            temperature=0.1
        )
        
        # Initialize RAGAS testset generator
        self.testset_generator = TestsetGenerator.from_langchain(
            generator_llm=self.llm,
            critic_llm=self.llm
        )
    
    async def evaluate_analysis_quality(self, analysis_result: Dict[str, Any], 
                                      ground_truth: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evaluate the quality of analysis results using RAGAS metrics"""
        try:
            self.logger.info("Evaluating analysis quality")
            
            # Prepare evaluation data
            evaluation_data = self._prepare_evaluation_data(analysis_result, ground_truth)
            
            # Run RAGAS evaluation
            evaluation_result = await self._run_ragas_evaluation(evaluation_data)
            
            # Log evaluation results
            self._log_evaluation_results(evaluation_result)
            
            return evaluation_result
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return {"error": str(e)}
    
    async def monitor_agent_performance(self, agent_type: str, task_id: str, 
                                      input_data: Dict[str, Any], 
                                      output_data: Dict[str, Any],
                                      processing_time: float) -> Dict[str, Any]:
        """Monitor individual agent performance using LangSmith"""
        try:
            self.logger.info(f"Monitoring {agent_type} agent performance")
            
            # Create LangSmith run
            run_data = {
                "name": f"traffix_{agent_type}",
                "run_type": "agent",
                "inputs": input_data,
                "outputs": output_data,
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "execution_order": 1,
                "child_runs": [],
                "tags": ["traffix", agent_type],
                "metadata": {
                    "processing_time": processing_time,
                    "task_id": task_id,
                    "agent_type": agent_type
                }
            }
            
            # Submit to LangSmith
            run = self.langsmith_client.create_run(**run_data)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                agent_type, input_data, output_data, processing_time
            )
            
            return {
                "run_id": run.id,
                "performance_metrics": performance_metrics,
                "status": "monitored"
            }
            
        except Exception as e:
            self.logger.error(f"Agent monitoring failed: {e}")
            return {"error": str(e)}
    
    async def evaluate_workflow_performance(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate overall workflow performance"""
        try:
            self.logger.info("Evaluating workflow performance")
            
            # Extract workflow metrics
            workflow_metrics = {
                "total_processing_time": workflow_result.get("processing_time", 0),
                "workflow_status": workflow_result.get("workflow_status", "unknown"),
                "error_message": workflow_result.get("error_message"),
                "success": workflow_result.get("workflow_status") == "completed"
            }
            
            # Evaluate data quality
            data_quality = self._evaluate_data_quality(workflow_result)
            
            # Evaluate analysis quality
            analysis_quality = self._evaluate_analysis_quality(workflow_result)
            
            # Evaluate story quality
            story_quality = self._evaluate_story_quality(workflow_result)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                workflow_metrics, data_quality, analysis_quality, story_quality
            )
            
            evaluation_result = {
                "workflow_metrics": workflow_metrics,
                "data_quality": data_quality,
                "analysis_quality": analysis_quality,
                "story_quality": story_quality,
                "overall_score": overall_score,
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            # Log to LangSmith
            await self._log_workflow_evaluation(evaluation_result)
            
            return evaluation_result
            
        except Exception as e:
            self.logger.error(f"Workflow evaluation failed: {e}")
            return {"error": str(e)}
    
    async def generate_test_dataset(self, location: str, num_questions: int = 10) -> Dict[str, Any]:
        """Generate test dataset for evaluation"""
        try:
            self.logger.info(f"Generating test dataset for {location}")
            
            # Create context for test generation
            context = f"""
            Traffic analysis data for {location} including:
            - Real-time traffic data from RITIS
            - News articles about traffic incidents
            - Weather data affecting traffic
            - Social media posts about traffic conditions
            - Historical traffic patterns and trends
            """
            
            # Generate test questions
            testset = await self.testset_generator.agenerate(
                context=context,
                num_questions=num_questions
            )
            
            return {
                "testset": testset,
                "location": location,
                "num_questions": num_questions,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Test dataset generation failed: {e}")
            return {"error": str(e)}
    
    def _prepare_evaluation_data(self, analysis_result: Dict[str, Any], 
                               ground_truth: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data for RAGAS evaluation"""
        
        # Extract analysis components
        analysis = analysis_result.get("analysis_result", {})
        story = analysis_result.get("story_data", {})
        
        # Create question-answer pairs
        questions = []
        answers = []
        contexts = []
        ground_truths = []
        
        # Add analysis questions
        if analysis.get("primary_causes"):
            questions.append("What are the primary causes of traffic issues?")
            answers.append(", ".join(analysis["primary_causes"]))
            contexts.append(str(analysis.get("supporting_evidence", [])))
            ground_truths.append(ground_truth.get("primary_causes", "") if ground_truth else "")
        
        # Add story questions
        if story.get("executive_summary"):
            questions.append("What is the executive summary?")
            answers.append(story["executive_summary"])
            contexts.append(str(story.get("story_elements", [])))
            ground_truths.append(ground_truth.get("executive_summary", "") if ground_truth else "")
        
        return {
            "questions": questions,
            "answers": answers,
            "contexts": contexts,
            "ground_truths": ground_truths
        }
    
    async def _run_ragas_evaluation(self, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run RAGAS evaluation metrics"""
        try:
            # Create dataset for evaluation
            dataset = {
                "question": evaluation_data["questions"],
                "answer": evaluation_data["answers"],
                "contexts": evaluation_data["contexts"],
                "ground_truth": evaluation_data["ground_truths"]
            }
            
            # Define metrics
            metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
                context_relevancy
            ]
            
            # Run evaluation
            result = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self.llm
            )
            
            return {
                "faithfulness": result["faithfulness"],
                "answer_relevancy": result["answer_relevancy"],
                "context_precision": result["context_precision"],
                "context_recall": result["context_recall"],
                "context_relevancy": result["context_relevancy"],
                "overall_score": result["ragas_score"]
            }
            
        except Exception as e:
            self.logger.error(f"RAGAS evaluation failed: {e}")
            return {"error": str(e)}
    
    def _calculate_performance_metrics(self, agent_type: str, input_data: Dict[str, Any],
                                     output_data: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Calculate performance metrics for an agent"""
        
        metrics = {
            "processing_time": processing_time,
            "input_size": len(str(input_data)),
            "output_size": len(str(output_data)),
            "success": "error" not in output_data,
            "agent_type": agent_type
        }
        
        # Calculate efficiency metrics
        if processing_time > 0:
            metrics["throughput"] = len(str(output_data)) / processing_time
        else:
            metrics["throughput"] = 0
        
        # Calculate quality metrics based on output
        if "confidence_score" in output_data:
            metrics["confidence"] = output_data["confidence_score"]
        
        if "error_message" in output_data:
            metrics["error_rate"] = 1.0
        else:
            metrics["error_rate"] = 0.0
        
        return metrics
    
    def _evaluate_data_quality(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the quality of collected data"""
        
        collected_data = workflow_result.get("collected_data", {})
        
        quality_metrics = {
            "data_completeness": 0.0,
            "data_freshness": 0.0,
            "data_consistency": 0.0,
            "source_diversity": 0.0
        }
        
        # Calculate completeness
        data_sources = ["traffic_data", "news_articles", "incidents", "weather_data", "social_posts"]
        available_sources = sum(1 for source in data_sources if collected_data.get(source))
        quality_metrics["data_completeness"] = available_sources / len(data_sources)
        
        # Calculate freshness
        if collected_data.get("traffic_data"):
            quality_metrics["data_freshness"] = 0.8  # Assume recent data
        
        # Calculate consistency
        if collected_data.get("traffic_data") and len(collected_data["traffic_data"]) > 1:
            quality_metrics["data_consistency"] = 0.7  # Assume consistent data
        
        # Calculate source diversity
        quality_metrics["source_diversity"] = available_sources / len(data_sources)
        
        return quality_metrics
    
    def _evaluate_analysis_quality(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the quality of analysis results"""
        
        analysis_result = workflow_result.get("analysis_result", {})
        analysis = analysis_result.get("analysis_result", {})
        
        quality_metrics = {
            "confidence_score": analysis.get("confidence_score", 0.0),
            "anomaly_detection": analysis.get("anomaly_detected", False),
            "cause_identification": len(analysis.get("primary_causes", [])) > 0,
            "evidence_support": len(analysis.get("supporting_evidence", [])) > 0,
            "recommendations": len(analysis.get("recommendations", [])) > 0
        }
        
        # Calculate overall analysis quality
        quality_metrics["overall_quality"] = sum([
            quality_metrics["confidence_score"],
            1.0 if quality_metrics["cause_identification"] else 0.0,
            1.0 if quality_metrics["evidence_support"] else 0.0,
            1.0 if quality_metrics["recommendations"] else 0.0
        ]) / 4
        
        return quality_metrics
    
    def _evaluate_story_quality(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the quality of generated stories"""
        
        story_data = workflow_result.get("story_data", {})
        
        quality_metrics = {
            "has_executive_summary": bool(story_data.get("executive_summary")),
            "story_elements_count": len(story_data.get("story_elements", [])),
            "story_confidence": story_data.get("confidence_score", 0.0),
            "narrative_quality": 0.0
        }
        
        # Calculate narrative quality based on story elements
        if quality_metrics["story_elements_count"] > 0:
            quality_metrics["narrative_quality"] = min(1.0, quality_metrics["story_elements_count"] / 5)
        
        return quality_metrics
    
    def _calculate_overall_score(self, workflow_metrics: Dict[str, Any],
                               data_quality: Dict[str, Any],
                               analysis_quality: Dict[str, Any],
                               story_quality: Dict[str, Any]) -> float:
        """Calculate overall evaluation score"""
        
        # Weighted average of different quality metrics
        weights = {
            "workflow": 0.2,
            "data": 0.3,
            "analysis": 0.3,
            "story": 0.2
        }
        
        workflow_score = 1.0 if workflow_metrics["success"] else 0.0
        data_score = data_quality.get("data_completeness", 0.0)
        analysis_score = analysis_quality.get("overall_quality", 0.0)
        story_score = story_quality.get("narrative_quality", 0.0)
        
        overall_score = (
            weights["workflow"] * workflow_score +
            weights["data"] * data_score +
            weights["analysis"] * analysis_score +
            weights["story"] * story_score
        )
        
        return overall_score
    
    def _log_evaluation_results(self, evaluation_result: Dict[str, Any]):
        """Log evaluation results"""
        
        if "error" in evaluation_result:
            self.logger.error(f"Evaluation error: {evaluation_result['error']}")
        else:
            self.logger.info(f"Evaluation completed - Overall score: {evaluation_result.get('overall_score', 0):.2f}")
    
    async def _log_workflow_evaluation(self, evaluation_result: Dict[str, Any]):
        """Log workflow evaluation to LangSmith"""
        try:
            # Create evaluation run
            run_data = {
                "name": "traffix_workflow_evaluation",
                "run_type": "evaluation",
                "inputs": {"evaluation_type": "workflow_performance"},
                "outputs": evaluation_result,
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "tags": ["traffix", "evaluation", "workflow"],
                "metadata": {
                    "overall_score": evaluation_result.get("overall_score", 0),
                    "evaluation_timestamp": evaluation_result.get("evaluation_timestamp")
                }
            }
            
            self.langsmith_client.create_run(**run_data)
            
        except Exception as e:
            self.logger.error(f"Failed to log workflow evaluation: {e}")
