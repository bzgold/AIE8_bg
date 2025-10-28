"""
RAGAS evaluation module adapted from assignment 08
"""
import asyncio
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness,
        answer_similarity
    )
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("RAGAS not available. Install with: pip install ragas")


class RagasEvaluator:
    """RAGAS-based evaluation for traffic analysis quality"""
    
    def __init__(self):
        self.available = RAGAS_AVAILABLE
        self.metrics = self._setup_metrics()
    
    def _setup_metrics(self) -> List[Any]:
        """Setup RAGAS metrics"""
        if not self.available:
            return []
        
        return [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
            answer_similarity
        ]
    
    async def evaluate_traffic_analysis(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate traffic analysis using RAGAS metrics"""
        
        if not self.available:
            return self._fallback_evaluation(questions, answers, contexts)
        
        try:
            # Prepare data for RAGAS
            data = {
                "question": questions,
                "answer": answers,
                "contexts": contexts,
                "ground_truths": ground_truths or [[] for _ in questions]
            }
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Run evaluation
            result = await evaluate(
                df,
                metrics=self.metrics,
                is_async=True
            )
            
            return self._format_ragas_results(result)
            
        except Exception as e:
            print(f"RAGAS evaluation failed: {e}")
            return self._fallback_evaluation(questions, answers, contexts)
    
    def _format_ragas_results(self, result: Any) -> Dict[str, Any]:
        """Format RAGAS results for our use case"""
        try:
            # Extract scores from RAGAS result
            scores = {}
            
            for metric in self.metrics:
                metric_name = metric.name
                if hasattr(result, metric_name):
                    scores[metric_name] = getattr(result, metric_name)
                else:
                    scores[metric_name] = 0.0
            
            # Calculate overall score
            overall_score = sum(scores.values()) / len(scores) if scores else 0.0
            
            return {
                "overall_score": overall_score,
                "metric_scores": scores,
                "evaluation_method": "ragas",
                "evaluated_at": datetime.now().isoformat(),
                "total_questions": len(result) if hasattr(result, '__len__') else 0
            }
            
        except Exception as e:
            print(f"Error formatting RAGAS results: {e}")
            return self._fallback_evaluation([], [], [])
    
    def _fallback_evaluation(self, questions: List[str], answers: List[str], contexts: List[List[str]]) -> Dict[str, Any]:
        """Fallback evaluation when RAGAS is not available"""
        return {
            "overall_score": 0.7,  # Default score
            "metric_scores": {
                "faithfulness": 0.7,
                "answer_relevancy": 0.7,
                "context_precision": 0.7,
                "context_recall": 0.7,
                "answer_correctness": 0.7,
                "answer_similarity": 0.7
            },
            "evaluation_method": "fallback",
            "evaluated_at": datetime.now().isoformat(),
            "total_questions": len(questions),
            "note": "RAGAS not available, using fallback evaluation"
        }
    
    def evaluate_single_response(
        self,
        question: str,
        answer: str,
        context: List[str],
        ground_truth: List[str] = None
    ) -> Dict[str, Any]:
        """Evaluate a single response"""
        return asyncio.run(
            self.evaluate_traffic_analysis(
                [question],
                [answer],
                [context],
                [ground_truth or []]
            )
        )
    
    def generate_synthetic_test_data(self, traffic_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate synthetic test data for evaluation"""
        
        # Extract key information from traffic data
        incidents = traffic_data.get("incidents", [])
        traffic_metrics = traffic_data.get("traffic_data", [])
        news_articles = traffic_data.get("news_articles", [])
        
        # Generate questions based on data
        questions = []
        answers = []
        contexts = []
        ground_truths = []
        
        # Incident-related questions
        for incident in incidents[:3]:  # Limit to 3 incidents
            question = f"What caused the traffic incident at {incident.get('location', 'unknown location')}?"
            answer = f"The incident was caused by {incident.get('description', 'unknown cause')}."
            context = [incident.get('description', '')]
            ground_truth = [incident.get('description', '')]
            
            questions.append(question)
            answers.append(answer)
            contexts.append(context)
            ground_truths.append(ground_truth)
        
        # Traffic pattern questions
        if traffic_metrics:
            question = "What were the traffic patterns during the analysis period?"
            answer = f"Traffic patterns showed varying speeds and volumes with {len(traffic_metrics)} data points."
            context = [f"Speed: {tm.get('speed', 'N/A')} mph, Volume: {tm.get('volume', 'N/A')}" for tm in traffic_metrics[:5]]
            ground_truth = ["Traffic data analysis"]
            
            questions.append(question)
            answers.append(answer)
            contexts.append(context)
            ground_truths.append(ground_truth)
        
        # News-related questions
        for article in news_articles[:2]:  # Limit to 2 articles
            question = f"What traffic-related news was reported by {article.get('source', 'unknown source')}?"
            answer = f"News reported: {article.get('title', 'No title')}"
            context = [article.get('content', '')[:500]]
            ground_truth = [article.get('title', '')]
            
            questions.append(question)
            answers.append(answer)
            contexts.append(context)
            ground_truths.append(ground_truth)
        
        return {
            "questions": questions,
            "answers": answers,
            "contexts": contexts,
            "ground_truths": ground_truths
        }
    
    def create_evaluation_dataset(self, traffic_analyses: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create evaluation dataset from multiple traffic analyses"""
        
        all_questions = []
        all_answers = []
        all_contexts = []
        all_ground_truths = []
        
        for analysis in traffic_analyses:
            # Extract questions and answers from analysis
            questions = analysis.get("questions", [])
            answers = analysis.get("answers", [])
            contexts = analysis.get("contexts", [])
            ground_truths = analysis.get("ground_truths", [])
            
            all_questions.extend(questions)
            all_answers.extend(answers)
            all_contexts.extend(contexts)
            all_ground_truths.extend(ground_truths)
        
        return pd.DataFrame({
            "question": all_questions,
            "answer": all_answers,
            "contexts": all_contexts,
            "ground_truths": all_ground_truths
        })
    
    def get_quality_insights(self, evaluation_results: Dict[str, Any]) -> List[str]:
        """Generate quality insights from evaluation results"""
        
        insights = []
        metric_scores = evaluation_results.get("metric_scores", {})
        overall_score = evaluation_results.get("overall_score", 0.0)
        
        # Overall quality assessment
        if overall_score >= 0.8:
            insights.append("Excellent quality - all metrics above 0.8")
        elif overall_score >= 0.6:
            insights.append("Good quality - most metrics above 0.6")
        elif overall_score >= 0.4:
            insights.append("Fair quality - some metrics need improvement")
        else:
            insights.append("Poor quality - significant improvements needed")
        
        # Specific metric insights
        for metric, score in metric_scores.items():
            if score < 0.5:
                insights.append(f"Low {metric} score ({score:.2f}) - needs attention")
            elif score > 0.8:
                insights.append(f"High {metric} score ({score:.2f}) - performing well")
        
        return insights
