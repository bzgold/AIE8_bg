"""
Synthetic data generation from assignment 07
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

try:
    from ragas.testset import TestsetGenerator
    from ragas.testset.evolutions import SimpleEvolution, NodeCountEvolution
    from ragas.testset.generator import TestsetGenerator
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("RAGAS not available. Install with: pip install ragas")

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class SyntheticDataGenerator:
    """Synthetic data generator for traffic analysis evaluation"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.ragas_available = RAGAS_AVAILABLE
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup prompts for synthetic data generation"""
        
        self.question_generation_prompt = PromptTemplate(
            input_variables=["context"],
            template="""
            Based on the following traffic analysis context, generate 5 diverse questions that a traffic analyst might ask:
            
            Context: {context}
            
            Generate questions that cover:
            1. Incident analysis and causes
            2. Traffic pattern identification
            3. Weather impact assessment
            4. Congestion analysis
            5. Recommendations and solutions
            
            Format as a JSON list of questions.
            """
        )
        
        self.answer_generation_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""
            Answer the following traffic analysis question based on the provided context:
            
            Question: {question}
            Context: {context}
            
            Provide a comprehensive answer that includes:
            - Specific data points and metrics
            - Analysis of causes and contributing factors
            - Evidence-based conclusions
            - Actionable recommendations
            
            Answer:
            """
        )
        
        self.context_generation_prompt = PromptTemplate(
            input_variables=["topic"],
            template="""
            Generate a realistic traffic analysis context about: {topic}
            
            Include:
            - Traffic metrics (speed, volume, occupancy)
            - Incident details and impacts
            - Weather conditions
            - Time periods and locations
            - Specific data points and measurements
            
            Make it realistic and detailed for traffic analysis purposes.
            """
        )
    
    async def generate_traffic_testset(
        self,
        num_questions: int = 10,
        topics: List[str] = None
    ) -> Dict[str, Any]:
        """Generate synthetic test dataset for traffic analysis"""
        
        if topics is None:
            topics = [
                "I-95 congestion analysis",
                "Weather impact on traffic",
                "Construction zone delays",
                "Incident response effectiveness",
                "Peak hour traffic patterns"
            ]
        
        # Generate contexts
        contexts = []
        for topic in topics:
            context = await self._generate_context(topic)
            contexts.append(context)
        
        # Generate questions and answers
        questions = []
        answers = []
        ground_truths = []
        
        for context in contexts:
            # Generate questions for this context
            context_questions = await self._generate_questions(context)
            questions.extend(context_questions)
            
            # Generate answers for each question
            for question in context_questions:
                answer = await self._generate_answer(question, context)
                answers.append(answer)
                
                # Extract ground truth from context
                ground_truth = self._extract_ground_truth(question, context)
                ground_truths.append(ground_truth)
        
        # Limit to requested number
        questions = questions[:num_questions]
        answers = answers[:num_questions]
        ground_truths = ground_truths[:num_questions]
        
        return {
            "questions": questions,
            "answers": answers,
            "contexts": contexts,
            "ground_truths": ground_truths,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "num_questions": len(questions),
                "num_contexts": len(contexts),
                "topics": topics
            }
        }
    
    async def _generate_context(self, topic: str) -> str:
        """Generate a realistic traffic analysis context"""
        
        chain = LLMChain(llm=self.llm, prompt=self.context_generation_prompt)
        context = await chain.arun(topic=topic)
        return context
    
    async def _generate_questions(self, context: str) -> List[str]:
        """Generate questions for a given context"""
        
        chain = LLMChain(llm=self.llm, prompt=self.question_generation_prompt)
        response = await chain.arun(context=context)
        
        # Parse JSON response
        try:
            import json
            questions = json.loads(response)
            return questions[:3]  # Limit to 3 questions per context
        except:
            # Fallback: extract questions from text
            lines = response.split('\n')
            questions = [line.strip() for line in lines if line.strip() and '?' in line]
            return questions[:3]
    
    async def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer for a question"""
        
        chain = LLMChain(llm=self.llm, prompt=self.answer_generation_prompt)
        answer = await chain.arun(question=question, context=context)
        return answer
    
    def _extract_ground_truth(self, question: str, context: str) -> List[str]:
        """Extract ground truth information from context"""
        
        # Simple extraction based on keywords
        ground_truth = []
        
        # Extract numbers and metrics
        import re
        numbers = re.findall(r'\d+\.?\d*', context)
        ground_truth.extend(numbers[:5])  # Limit to 5 numbers
        
        # Extract key terms
        key_terms = [
            "congestion", "delay", "incident", "accident", "crash", "breakdown",
            "construction", "closure", "detour", "jam", "backup", "bottleneck",
            "speed", "volume", "occupancy", "flow", "density", "reliability"
        ]
        
        for term in key_terms:
            if term in context.lower():
                ground_truth.append(term)
        
        return ground_truth[:10]  # Limit to 10 items
    
    def generate_ragas_testset(self, documents: List[str]) -> Optional[Dict[str, Any]]:
        """Generate testset using RAGAS if available"""
        
        if not self.ragas_available:
            print("RAGAS not available for testset generation")
            return None
        
        try:
            # Create testset generator
            generator = TestsetGenerator.from_default(
                generator_llm=self.llm,
                critic_llm=self.llm,
                embeddings=self.llm
            )
            
            # Generate testset
            testset = generator.generate(
                documents=documents,
                num_questions=10,
                distributions={
                    "simple": 0.3,
                    "reasoning": 0.4,
                    "multi_context": 0.3
                }
            )
            
            return {
                "testset": testset,
                "generated_at": datetime.now().isoformat(),
                "method": "ragas"
            }
            
        except Exception as e:
            print(f"RAGAS testset generation failed: {e}")
            return None
    
    def create_evaluation_dataset(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[List[str]]
    ) -> pd.DataFrame:
        """Create evaluation dataset from generated data"""
        
        # Ensure all lists have the same length
        min_length = min(len(questions), len(answers), len(contexts), len(ground_truths))
        
        data = {
            "question": questions[:min_length],
            "answer": answers[:min_length],
            "contexts": contexts[:min_length],
            "ground_truths": ground_truths[:min_length]
        }
        
        return pd.DataFrame(data)
    
    def generate_traffic_scenarios(self, num_scenarios: int = 5) -> List[Dict[str, Any]]:
        """Generate realistic traffic scenarios for testing"""
        
        scenarios = [
            {
                "name": "Morning Rush Hour Congestion",
                "description": "Heavy congestion on I-95 North during morning rush hour",
                "time": "07:00-09:00",
                "location": "I-95 North",
                "factors": ["high_volume", "weather", "incidents"],
                "metrics": {
                    "avg_speed": 25.3,
                    "volume": 1800,
                    "occupancy": 0.85
                }
            },
            {
                "name": "Weather-Related Delays",
                "description": "Rainy weather causing reduced speeds and increased delays",
                "time": "14:00-16:00",
                "location": "Route 50 East",
                "factors": ["weather", "visibility", "safety"],
                "metrics": {
                    "avg_speed": 35.2,
                    "volume": 1200,
                    "occupancy": 0.70
                }
            },
            {
                "name": "Construction Zone Impact",
                "description": "Road construction causing lane closures and delays",
                "time": "10:00-15:00",
                "location": "I-495 Beltway",
                "factors": ["construction", "lane_closures", "detours"],
                "metrics": {
                    "avg_speed": 30.1,
                    "volume": 1500,
                    "occupancy": 0.80
                }
            },
            {
                "name": "Incident Response",
                "description": "Multi-vehicle accident causing major delays",
                "time": "16:30-19:00",
                "location": "I-66 West",
                "factors": ["incident", "emergency_response", "lane_closures"],
                "metrics": {
                    "avg_speed": 20.5,
                    "volume": 800,
                    "occupancy": 0.95
                }
            },
            {
                "name": "Holiday Traffic Patterns",
                "description": "Unusual traffic patterns during holiday weekend",
                "time": "All day",
                "location": "Multiple corridors",
                "factors": ["holiday", "tourism", "events"],
                "metrics": {
                    "avg_speed": 40.8,
                    "volume": 2200,
                    "occupancy": 0.75
                }
            }
        ]
        
        return scenarios[:num_scenarios]
    
    def validate_synthetic_data(self, testset: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality of generated synthetic data"""
        
        validation_results = {
            "total_questions": len(testset.get("questions", [])),
            "total_answers": len(testset.get("answers", [])),
            "total_contexts": len(testset.get("contexts", [])),
            "quality_metrics": {}
        }
        
        # Check question quality
        questions = testset.get("questions", [])
        if questions:
            avg_question_length = sum(len(q) for q in questions) / len(questions)
            validation_results["quality_metrics"]["avg_question_length"] = avg_question_length
            
            # Check for question marks
            questions_with_marks = sum(1 for q in questions if "?" in q)
            validation_results["quality_metrics"]["question_mark_ratio"] = questions_with_marks / len(questions)
        
        # Check answer quality
        answers = testset.get("answers", [])
        if answers:
            avg_answer_length = sum(len(a) for a in answers) / len(answers)
            validation_results["quality_metrics"]["avg_answer_length"] = avg_answer_length
            
            # Check for data points
            answers_with_numbers = sum(1 for a in answers if any(c.isdigit() for c in a))
            validation_results["quality_metrics"]["answers_with_data_ratio"] = answers_with_numbers / len(answers)
        
        # Check context quality
        contexts = testset.get("contexts", [])
        if contexts:
            avg_context_length = sum(len(c) for c in contexts) / len(contexts)
            validation_results["quality_metrics"]["avg_context_length"] = avg_context_length
        
        return validation_results
