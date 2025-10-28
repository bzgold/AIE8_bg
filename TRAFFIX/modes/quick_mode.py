"""
Quick Mode - Fast daily summaries for traffic analysis
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents import DataCollectorAgent, AnalyzerAgent, StorytellerAgent, ReporterAgent
from services import DataIntegrationService
from models import ReportMode


class QuickModeProcessor:
    """Processor for Quick Mode - optimized for speed and daily summaries"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.quick_mode")
        self.data_collector = DataCollectorAgent()
        self.analyzer = AnalyzerAgent()
        self.storyteller = StorytellerAgent()
        self.reporter = ReporterAgent()
        self.data_service = DataIntegrationService()
    
    async def process_quick_analysis(self, location: str, time_range_hours: int = 24) -> Dict[str, Any]:
        """Process a quick analysis for daily summary"""
        self.logger.info(f"Starting quick analysis for {location}")
        start_time = datetime.now()
        
        try:
            # Step 1: Collect data (optimized for speed)
            self.logger.info("Collecting data...")
            collected_data = await self.data_service.collect_all_data(
                location=location,
                time_range_hours=time_range_hours,
                mode="quick"
            )
            
            # Step 2: Quick analysis
            self.logger.info("Performing quick analysis...")
            analysis_input = {
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.QUICK
            }
            analysis_task = await self.analyzer.execute_task(analysis_input)
            
            if analysis_task.status.value != "completed":
                raise Exception(f"Analysis failed: {analysis_task.error_message}")
            
            # Step 3: Generate quick story
            self.logger.info("Generating quick story...")
            story_input = {
                "analysis_result": analysis_task.output_data.get("analysis_result", {}),
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.QUICK
            }
            story_task = await self.storyteller.execute_task(story_input)
            
            if story_task.status.value != "completed":
                raise Exception(f"Story generation failed: {story_task.error_message}")
            
            # Step 4: Generate quick report
            self.logger.info("Generating quick report...")
            report_input = {
                "story_data": story_task.output_data,
                "location": location,
                "mode": ReportMode.QUICK,
                "output_format": "html"
            }
            report_task = await self.reporter.execute_task(report_input)
            
            if report_task.status.value != "completed":
                raise Exception(f"Report generation failed: {report_task.error_message}")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "location": location,
                "mode": "quick",
                "processing_time_seconds": processing_time,
                "collected_data": collected_data,
                "analysis_result": analysis_task.output_data,
                "story_data": story_task.output_data,
                "report_data": report_task.output_data,
                "summary": self._generate_quick_summary(
                    analysis_task.output_data,
                    story_task.output_data,
                    processing_time
                )
            }
            
            self.logger.info(f"Quick analysis completed for {location} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Quick analysis failed for {location}: {e}")
            return {
                "success": False,
                "location": location,
                "mode": "quick",
                "error": str(e),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def _generate_quick_summary(self, analysis_data: Dict[str, Any], 
                              story_data: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Generate a quick summary of the analysis"""
        analysis_result = analysis_data.get("analysis_result", {})
        
        summary = {
            "anomaly_detected": analysis_result.get("anomaly_detected", False),
            "confidence_score": analysis_result.get("confidence_score", 0.0),
            "primary_causes": analysis_result.get("primary_causes", []),
            "key_recommendations": analysis_result.get("recommendations", [])[:3],  # Top 3
            "executive_summary": story_data.get("executive_summary", ""),
            "processing_time": f"{processing_time:.2f}s",
            "data_sources_used": len(analysis_data.get("analysis_metadata", {}).get("sources_used", [])),
            "story_elements_count": len(story_data.get("story_elements", [])),
            "report_generated": True
        }
        
        return summary
    
    async def generate_daily_summary(self, location: str) -> Dict[str, Any]:
        """Generate a daily summary for a specific location"""
        return await self.process_quick_analysis(location, time_range_hours=24)
    
    async def generate_shift_summary(self, location: str, shift_hours: int = 8) -> Dict[str, Any]:
        """Generate a shift summary for a specific location"""
        return await self.process_quick_analysis(location, time_range_hours=shift_hours)
    
    async def generate_incident_summary(self, location: str, incident_time_range: int = 4) -> Dict[str, Any]:
        """Generate a summary focused on recent incidents"""
        return await self.process_quick_analysis(location, time_range_hours=incident_time_range)
    
    def get_quick_insights(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract quick insights from analysis data"""
        insights = []
        analysis_result = analysis_data.get("analysis_result", {})
        
        if analysis_result.get("anomaly_detected"):
            insights.append("🚨 Traffic anomaly detected - requires attention")
        
        confidence = analysis_result.get("confidence_score", 0)
        if confidence > 0.8:
            insights.append("✅ High confidence analysis - reliable insights")
        elif confidence > 0.5:
            insights.append("⚠️ Moderate confidence analysis - review recommended")
        else:
            insights.append("❌ Low confidence analysis - data quality issues")
        
        causes = analysis_result.get("primary_causes", [])
        if causes:
            insights.append(f"🔍 Primary causes identified: {', '.join(causes[:2])}")
        
        recommendations = analysis_result.get("recommendations", [])
        if recommendations:
            insights.append(f"💡 Key recommendation: {recommendations[0]}")
        
        return insights
