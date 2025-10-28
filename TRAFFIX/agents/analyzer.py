"""
Analyzer Agent - Analyzes collected data to identify patterns and anomalies
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from agents.base_agent import BaseAgent
from models import AnalysisResult, ReportMode
from config import settings


class AnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing collected data and identifying patterns"""
    
    def __init__(self):
        super().__init__("analyzer")
        self.llm = OpenAI(
            openai_api_key=settings.openai_api_key,
            temperature=0.1,
            max_tokens=1000
        )
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup LLM prompts for analysis"""
        self.anomaly_detection_prompt = PromptTemplate(
            input_variables=["traffic_data", "news_data", "incident_data", "location"],
            template="""
            Analyze the following traffic data to identify anomalies and patterns:
            
            Location: {location}
            
            Traffic Data Summary:
            {traffic_data}
            
            News Articles:
            {news_data}
            
            Incidents:
            {incident_data}
            
            Please identify:
            1. Any traffic anomalies or unusual patterns
            2. Primary causes of congestion
            3. Supporting evidence from news and incidents
            4. Impact assessment
            5. Recommendations for improvement
            
            Respond in JSON format with the following structure:
            {{
                "anomaly_detected": boolean,
                "confidence_score": float (0-1),
                "primary_causes": [list of causes],
                "supporting_evidence": [list of evidence],
                "impact_assessment": "string description",
                "recommendations": [list of recommendations]
            }}
            """
        )
        
        self.pattern_analysis_prompt = PromptTemplate(
            input_variables=["traffic_data", "time_period"],
            template="""
            Analyze traffic patterns for the following data over {time_period}:
            
            {traffic_data}
            
            Identify:
            1. Peak congestion times
            2. Speed variations
            3. Volume trends
            4. Recurring patterns
            
            Provide insights in a structured format.
            """
        )
    
    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze collected data and identify patterns"""
        collected_data = input_data.get("collected_data", {})
        location = input_data.get("location", "Unknown")
        mode = input_data.get("mode", ReportMode.QUICK)
        
        self.logger.info(f"Starting analysis for {location} in {mode} mode")
        
        try:
            # Perform statistical analysis
            statistical_analysis = self._perform_statistical_analysis(collected_data)
            
            # Perform LLM-based analysis
            llm_analysis = await self._perform_llm_analysis(collected_data, location)
            
            # Combine analyses
            combined_analysis = self._combine_analyses(statistical_analysis, llm_analysis)
            
            # Generate analysis result
            analysis_result = AnalysisResult(
                anomaly_detected=combined_analysis["anomaly_detected"],
                confidence_score=combined_analysis["confidence_score"],
                primary_causes=combined_analysis["primary_causes"],
                supporting_evidence=combined_analysis["supporting_evidence"],
                impact_assessment=combined_analysis["impact_assessment"],
                recommendations=combined_analysis["recommendations"]
            )
            
            return {
                "analysis_result": analysis_result.dict(),
                "statistical_analysis": statistical_analysis,
                "llm_analysis": llm_analysis,
                "analysis_metadata": {
                    "location": location,
                    "mode": mode,
                    "analyzed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise
    
    def _perform_statistical_analysis(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis on traffic data"""
        traffic_data = collected_data.get("traffic_data", [])
        
        if not traffic_data:
            return {"error": "No traffic data available"}
        
        # Extract metrics
        speeds = [item.get("speed", 0) for item in traffic_data]
        volumes = [item.get("volume", 0) for item in traffic_data]
        occupancies = [item.get("occupancy", 0) for item in traffic_data]
        
        # Calculate statistics
        analysis = {
            "speed_stats": {
                "mean": float(np.mean(speeds)),
                "std": float(np.std(speeds)),
                "min": float(np.min(speeds)),
                "max": float(np.max(speeds))
            },
            "volume_stats": {
                "mean": float(np.mean(volumes)),
                "std": float(np.std(volumes)),
                "min": float(np.min(volumes)),
                "max": float(np.max(volumes))
            },
            "occupancy_stats": {
                "mean": float(np.mean(occupancies)),
                "std": float(np.std(occupancies)),
                "min": float(np.min(occupancies)),
                "max": float(np.max(occupancies))
            },
            "anomaly_indicators": {
                "speed_variance": float(np.var(speeds)),
                "volume_variance": float(np.var(volumes)),
                "high_occupancy_periods": sum(1 for occ in occupancies if occ > 0.7)
            }
        }
        
        # Detect anomalies
        speed_threshold = analysis["speed_stats"]["mean"] - 2 * analysis["speed_stats"]["std"]
        volume_threshold = analysis["volume_stats"]["mean"] + 2 * analysis["volume_stats"]["std"]
        
        analysis["anomalies"] = {
            "low_speed_periods": sum(1 for speed in speeds if speed < speed_threshold),
            "high_volume_periods": sum(1 for volume in volumes if volume > volume_threshold),
            "congestion_events": sum(1 for item in traffic_data if item.get("incident_detected", False))
        }
        
        return analysis
    
    async def _perform_llm_analysis(self, collected_data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Perform LLM-based analysis"""
        try:
            # Prepare data for LLM
            traffic_summary = self._summarize_traffic_data(collected_data.get("traffic_data", []))
            news_summary = self._summarize_news_data(collected_data.get("news_articles", []))
            incident_summary = self._summarize_incident_data(collected_data.get("incidents", []))
            
            # Create analysis chain
            chain = LLMChain(llm=self.llm, prompt=self.anomaly_detection_prompt)
            
            # Run analysis
            result = await chain.arun(
                traffic_data=traffic_summary,
                news_data=news_summary,
                incident_data=incident_summary,
                location=location
            )
            
            # Parse JSON result
            import json
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "anomaly_detected": True,
                    "confidence_score": 0.5,
                    "primary_causes": ["Analysis incomplete"],
                    "supporting_evidence": ["LLM analysis failed to parse"],
                    "impact_assessment": "Unable to assess impact",
                    "recommendations": ["Review data quality"]
                }
                
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return {
                "anomaly_detected": False,
                "confidence_score": 0.0,
                "primary_causes": [],
                "supporting_evidence": [],
                "impact_assessment": "Analysis failed",
                "recommendations": ["Fix analysis system"]
            }
    
    def _summarize_traffic_data(self, traffic_data: List[Dict[str, Any]]) -> str:
        """Summarize traffic data for LLM analysis"""
        if not traffic_data:
            return "No traffic data available"
        
        summary = f"Traffic data points: {len(traffic_data)}\n"
        summary += f"Speed range: {min(item.get('speed', 0) for item in traffic_data):.1f} - {max(item.get('speed', 0) for item in traffic_data):.1f} mph\n"
        summary += f"Volume range: {min(item.get('volume', 0) for item in traffic_data)} - {max(item.get('volume', 0) for item in traffic_data)} vehicles\n"
        summary += f"Incidents detected: {sum(1 for item in traffic_data if item.get('incident_detected', False))}\n"
        
        return summary
    
    def _summarize_news_data(self, news_data: List[Dict[str, Any]]) -> str:
        """Summarize news data for LLM analysis"""
        if not news_data:
            return "No news data available"
        
        summary = f"News articles: {len(news_data)}\n"
        for article in news_data[:3]:  # Top 3 articles
            summary += f"- {article.get('title', 'No title')}\n"
        
        return summary
    
    def _summarize_incident_data(self, incident_data: List[Dict[str, Any]]) -> str:
        """Summarize incident data for LLM analysis"""
        if not incident_data:
            return "No incident data available"
        
        summary = f"Incidents: {len(incident_data)}\n"
        for incident in incident_data:
            summary += f"- {incident.get('description', 'No description')} ({incident.get('severity', 'Unknown severity')})\n"
        
        return summary
    
    def _combine_analyses(self, statistical: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
        """Combine statistical and LLM analyses"""
        # Use LLM analysis as base, enhance with statistical insights
        combined = llm.copy()
        
        # Enhance confidence based on statistical analysis
        if "anomalies" in statistical:
            anomaly_count = sum(statistical["anomalies"].values())
            if anomaly_count > 0:
                combined["confidence_score"] = min(1.0, combined.get("confidence_score", 0.5) + 0.2)
        
        # Add statistical insights to evidence
        if "anomalies" in statistical:
            evidence = combined.get("supporting_evidence", [])
            if statistical["anomalies"]["low_speed_periods"] > 0:
                evidence.append(f"Statistical analysis detected {statistical['anomalies']['low_speed_periods']} low-speed periods")
            if statistical["anomalies"]["high_volume_periods"] > 0:
                evidence.append(f"Statistical analysis detected {statistical['anomalies']['high_volume_periods']} high-volume periods")
            combined["supporting_evidence"] = evidence
        
        return combined
