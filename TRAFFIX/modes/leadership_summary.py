"""
Leadership Summary Mode - Executive reports for transportation leadership
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from agents import DataCollectorAgent, AnalyzerAgent, StorytellerAgent, ReporterAgent
from services import DataIntegrationService
from models import ReportMode, LeadershipSummary, UserQuestion


class LeadershipSummaryProcessor:
    """Processor for leadership summaries - answers 'what happened this week?'"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.leadership_summary")
        self.data_collector = DataCollectorAgent()
        self.analyzer = AnalyzerAgent()
        self.storyteller = StorytellerAgent()
        self.reporter = ReporterAgent()
        self.data_service = DataIntegrationService()
    
    async def generate_leadership_summary(self, location: str, period: str = "week") -> Dict[str, Any]:
        """Generate executive summary for transportation leadership"""
        self.logger.info(f"Generating leadership summary for {location} - {period}")
        start_time = datetime.now()
        
        try:
            # Step 1: Collect comprehensive data for the period
            time_range_hours = self._parse_period(period)
            self.logger.info(f"Collecting data for {time_range_hours} hours...")
            
            collected_data = await self.data_service.collect_all_data(
                location=location,
                time_range_hours=time_range_hours,
                mode="deep"
            )
            
            # Step 2: Perform leadership-focused analysis
            self.logger.info("Performing leadership-focused analysis...")
            analysis_input = {
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.LEADERSHIP_SUMMARY,
                "period": period,
                "analysis_focus": "executive_summary"
            }
            analysis_task = await self.analyzer.execute_task(analysis_input)
            
            if analysis_task.status.value != "completed":
                raise Exception(f"Leadership analysis failed: {analysis_task.error_message}")
            
            # Step 3: Generate executive story
            self.logger.info("Generating executive story...")
            story_input = {
                "analysis_result": analysis_task.output_data.get("analysis_result", {}),
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.LEADERSHIP_SUMMARY,
                "user_question": f"Summarize this {period}'s mobility highlights for {location} leadership"
            }
            story_task = await self.storyteller.execute_task(story_input)
            
            if story_task.status.value != "completed":
                raise Exception(f"Story generation failed: {story_task.error_message}")
            
            # Step 4: Generate leadership report
            self.logger.info("Generating leadership report...")
            report_input = {
                "story_data": story_task.output_data,
                "location": location,
                "mode": ReportMode.LEADERSHIP_SUMMARY,
                "output_format": "html",
                "leadership_data": analysis_task.output_data
            }
            report_task = await self.reporter.execute_task(report_input)
            
            if report_task.status.value != "completed":
                raise Exception(f"Report generation failed: {report_task.error_message}")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create leadership summary
            leadership_summary = self._create_leadership_summary(
                analysis_task.output_data, collected_data, location, period
            )
            
            result = {
                "success": True,
                "location": location,
                "mode": "leadership_summary",
                "period": period,
                "processing_time_seconds": processing_time,
                "leadership_summary": leadership_summary.dict(),
                "collected_data": collected_data,
                "analysis_result": analysis_task.output_data,
                "story_data": story_task.output_data,
                "report_data": report_task.output_data,
                "executive_insights": self._generate_executive_insights(leadership_summary)
            }
            
            self.logger.info(f"Leadership summary completed for {location} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Leadership summary failed for {location}: {e}")
            return {
                "success": False,
                "location": location,
                "mode": "leadership_summary",
                "period": period,
                "error": str(e),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def _parse_period(self, period: str) -> int:
        """Parse period string to hours"""
        period = period.lower()
        
        if period == "day" or period == "today":
            return 24
        elif period == "week":
            return 168
        elif period == "month":
            return 720
        elif period == "quarter":
            return 2160
        else:
            return 168  # Default to week
    
    def _create_leadership_summary(self, analysis_data: Dict[str, Any], 
                                 collected_data: Dict[str, Any], 
                                 location: str, period: str) -> LeadershipSummary:
        """Create structured leadership summary"""
        analysis_result = analysis_data.get("analysis_result", {})
        
        # Extract key highlights
        key_highlights = self._extract_key_highlights(analysis_result, collected_data)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(collected_data, analysis_result)
        
        # Identify major incidents
        major_incidents = self._identify_major_incidents(collected_data)
        
        # Assess weather impacts
        weather_impacts = self._assess_weather_impacts(collected_data)
        
        # Generate recommendations
        recommendations = analysis_result.get("recommendations", [])
        
        # Generate outlook
        next_period_outlook = self._generate_outlook(analysis_result, period)
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(analysis_result)
        
        return LeadershipSummary(
            period=period,
            key_highlights=key_highlights,
            performance_metrics=performance_metrics,
            major_incidents=major_incidents,
            weather_impacts=weather_impacts,
            recommendations=recommendations,
            next_period_outlook=next_period_outlook,
            confidence_level=confidence_level
        )
    
    def _extract_key_highlights(self, analysis_result: Dict[str, Any], 
                              collected_data: Dict[str, Any]) -> List[str]:
        """Extract key highlights for leadership"""
        highlights = []
        
        # Traffic performance highlights
        traffic_data = collected_data.get("traffic_data", [])
        if traffic_data:
            avg_speed = sum(item.get("speed", 0) for item in traffic_data) / len(traffic_data)
            highlights.append(f"Average speed: {avg_speed:.1f} mph")
        
        # Anomaly highlights
        if analysis_result.get("anomaly_detected"):
            highlights.append("Traffic anomalies detected requiring attention")
        else:
            highlights.append("Normal traffic patterns observed")
        
        # Incident highlights
        incidents = collected_data.get("incidents", [])
        if incidents:
            highlights.append(f"{len(incidents)} traffic incidents reported")
        
        # News highlights
        news_articles = collected_data.get("news_articles", [])
        if news_articles:
            highlights.append(f"{len(news_articles)} traffic-related news items")
        
        # Weather highlights
        weather_data = collected_data.get("weather_data", [])
        if weather_data:
            conditions = [item.get("condition") for item in weather_data]
            unique_conditions = list(set(conditions))
            if len(unique_conditions) > 1:
                highlights.append(f"Weather conditions varied: {', '.join(unique_conditions)}")
        
        return highlights
    
    def _calculate_performance_metrics(self, collected_data: Dict[str, Any], 
                                     analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key performance metrics for leadership"""
        metrics = {}
        
        # Traffic metrics
        traffic_data = collected_data.get("traffic_data", [])
        if traffic_data:
            speeds = [item.get("speed", 0) for item in traffic_data]
            volumes = [item.get("volume", 0) for item in traffic_data]
            
            metrics["average_speed"] = sum(speeds) / len(speeds)
            metrics["average_volume"] = sum(volumes) / len(volumes)
            metrics["speed_variance"] = max(speeds) - min(speeds)
            metrics["data_points"] = len(traffic_data)
        
        # Reliability metrics
        incidents = collected_data.get("incidents", [])
        metrics["incident_count"] = len(incidents)
        metrics["incident_severity"] = self._calculate_incident_severity(incidents)
        
        # Analysis metrics
        metrics["confidence_score"] = analysis_result.get("confidence_score", 0)
        metrics["anomaly_detected"] = analysis_result.get("anomaly_detected", False)
        
        return metrics
    
    def _calculate_incident_severity(self, incidents: List[Dict[str, Any]]) -> str:
        """Calculate overall incident severity"""
        if not incidents:
            return "none"
        
        severities = [incident.get("severity", "minor") for incident in incidents]
        
        if "critical" in severities:
            return "critical"
        elif "major" in severities:
            return "major"
        elif "moderate" in severities:
            return "moderate"
        else:
            return "minor"
    
    def _identify_major_incidents(self, collected_data: Dict[str, Any]) -> List[str]:
        """Identify major incidents for leadership attention"""
        incidents = collected_data.get("incidents", [])
        major_incidents = []
        
        for incident in incidents:
            severity = incident.get("severity", "minor")
            description = incident.get("description", "Unknown incident")
            
            if severity in ["critical", "major"]:
                major_incidents.append(f"{severity.title()}: {description}")
        
        return major_incidents
    
    def _assess_weather_impacts(self, collected_data: Dict[str, Any]) -> List[str]:
        """Assess weather impacts on traffic"""
        weather_data = collected_data.get("weather_data", [])
        impacts = []
        
        for weather in weather_data:
            condition = weather.get("condition", "")
            impact = weather.get("traffic_impact", "low")
            
            if impact in ["high", "moderate"]:
                impacts.append(f"{condition.title()} weather caused {impact} traffic impact")
        
        return impacts
    
    def _generate_outlook(self, analysis_result: Dict[str, Any], period: str) -> str:
        """Generate outlook for next period"""
        confidence = analysis_result.get("confidence_score", 0)
        
        if confidence > 0.8:
            return f"High confidence in {period} analysis - reliable predictions for next period"
        elif confidence > 0.6:
            return f"Moderate confidence in {period} analysis - monitor trends for next period"
        else:
            return f"Low confidence in {period} analysis - additional data needed for next period outlook"
    
    def _determine_confidence_level(self, analysis_result: Dict[str, Any]) -> str:
        """Determine overall confidence level"""
        confidence = analysis_result.get("confidence_score", 0)
        
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "moderate"
        else:
            return "low"
    
    def _generate_executive_insights(self, summary: LeadershipSummary) -> List[str]:
        """Generate executive insights from leadership summary"""
        insights = []
        
        # Performance insights
        metrics = summary.performance_metrics
        if metrics.get("anomaly_detected"):
            insights.append("🚨 Traffic anomalies require immediate attention")
        else:
            insights.append("✅ Normal traffic operations maintained")
        
        # Incident insights
        if summary.major_incidents:
            insights.append(f"⚠️ {len(summary.major_incidents)} major incidents reported")
        else:
            insights.append("✅ No major incidents reported")
        
        # Weather insights
        if summary.weather_impacts:
            insights.append(f"🌤️ Weather impacts: {len(summary.weather_impacts)} events")
        
        # Confidence insights
        confidence = summary.confidence_level
        if confidence == "very_high":
            insights.append("🎯 Very high confidence in analysis")
        elif confidence == "high":
            insights.append("✅ High confidence in analysis")
        elif confidence == "moderate":
            insights.append("⚠️ Moderate confidence - consider additional monitoring")
        else:
            insights.append("❓ Low confidence - data quality issues")
        
        # Recommendation insights
        if summary.recommendations:
            insights.append(f"💡 {len(summary.recommendations)} recommendations provided")
        
        return insights
    
    async def answer_leadership_question(self, question: UserQuestion) -> Dict[str, Any]:
        """Answer leadership-focused questions"""
        self.logger.info(f"Answering leadership question: {question.specific_question}")
        
        if question.question_type == "leadership_summary":
            return await self.generate_leadership_summary(
                location=question.location,
                period=question.time_period
            )
        else:
            return {
                "success": False,
                "error": f"Leadership question type '{question.question_type}' not supported",
                "question": question.specific_question
            }
