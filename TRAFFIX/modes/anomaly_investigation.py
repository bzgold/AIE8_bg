"""
Anomaly Investigation Mode - Focused on uncovering causes behind congestion changes
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from agents import DataCollectorAgent, AnalyzerAgent, StorytellerAgent, ReporterAgent
from services import DataIntegrationService
from models import ReportMode, AnomalyInvestigation, UserQuestion


class AnomalyInvestigationProcessor:
    """Processor for anomaly investigation - answers 'why did congestion change?'"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.anomaly_investigation")
        self.data_collector = DataCollectorAgent()
        self.analyzer = AnalyzerAgent()
        self.storyteller = StorytellerAgent()
        self.reporter = ReporterAgent()
        self.data_service = DataIntegrationService()
    
    async def investigate_anomaly(self, location: str, time_period: str, 
                                baseline_period: str = None) -> Dict[str, Any]:
        """Investigate why congestion patterns changed in a specific location and time"""
        self.logger.info(f"Investigating anomaly for {location} during {time_period}")
        start_time = datetime.now()
        
        try:
            # Step 1: Collect data for both anomaly and baseline periods
            self.logger.info("Collecting data for anomaly and baseline periods...")
            
            anomaly_data = await self.data_service.collect_all_data(
                location=location,
                time_range_hours=self._parse_time_period(time_period),
                mode="deep"
            )
            
            # Collect baseline data for comparison
            baseline_hours = self._parse_time_period(baseline_period) if baseline_period else 168  # Default 1 week
            baseline_data = await self.data_service.collect_all_data(
                location=location,
                time_range_hours=baseline_hours,
                mode="deep"
            )
            
            # Step 2: Perform anomaly detection and cause analysis
            self.logger.info("Performing anomaly detection and cause analysis...")
            analysis_input = {
                "collected_data": anomaly_data,
                "baseline_data": baseline_data,
                "location": location,
                "mode": ReportMode.ANOMALY_INVESTIGATION,
                "time_period": time_period,
                "baseline_period": baseline_period or "previous_week"
            }
            analysis_task = await self.analyzer.execute_task(analysis_input)
            
            if analysis_task.status.value != "completed":
                raise Exception(f"Anomaly analysis failed: {analysis_task.error_message}")
            
            # Step 3: Generate focused story explaining the anomaly
            self.logger.info("Generating anomaly explanation story...")
            story_input = {
                "analysis_result": analysis_task.output_data.get("analysis_result", {}),
                "collected_data": anomaly_data,
                "baseline_data": baseline_data,
                "location": location,
                "mode": ReportMode.ANOMALY_INVESTIGATION,
                "user_question": f"Why was congestion different than normal in {location} during {time_period}?"
            }
            story_task = await self.storyteller.execute_task(story_input)
            
            if story_task.status.value != "completed":
                raise Exception(f"Story generation failed: {story_task.error_message}")
            
            # Step 4: Generate anomaly investigation report
            self.logger.info("Generating anomaly investigation report...")
            report_input = {
                "story_data": story_task.output_data,
                "location": location,
                "mode": ReportMode.ANOMALY_INVESTIGATION,
                "output_format": "html",
                "anomaly_data": analysis_task.output_data
            }
            report_task = await self.reporter.execute_task(report_input)
            
            if report_task.status.value != "completed":
                raise Exception(f"Report generation failed: {report_task.error_message}")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create anomaly investigation result
            anomaly_investigation = self._create_anomaly_investigation(
                analysis_task.output_data, location, time_period, baseline_period
            )
            
            result = {
                "success": True,
                "location": location,
                "mode": "anomaly_investigation",
                "time_period": time_period,
                "baseline_period": baseline_period,
                "processing_time_seconds": processing_time,
                "anomaly_investigation": anomaly_investigation.dict(),
                "collected_data": anomaly_data,
                "baseline_data": baseline_data,
                "analysis_result": analysis_task.output_data,
                "story_data": story_task.output_data,
                "report_data": report_task.output_data,
                "investigation_summary": self._generate_investigation_summary(anomaly_investigation)
            }
            
            self.logger.info(f"Anomaly investigation completed for {location} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Anomaly investigation failed for {location}: {e}")
            return {
                "success": False,
                "location": location,
                "mode": "anomaly_investigation",
                "time_period": time_period,
                "error": str(e),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def _parse_time_period(self, time_period: str) -> int:
        """Parse time period string to hours"""
        time_period = time_period.lower()
        
        if "today" in time_period:
            return 24
        elif "yesterday" in time_period:
            return 24
        elif "week" in time_period:
            return 168
        elif "month" in time_period:
            return 720
        elif "hour" in time_period:
            # Extract number of hours
            import re
            match = re.search(r'(\d+)\s*hour', time_period)
            if match:
                return int(match.group(1))
            return 24
        else:
            return 24  # Default to 24 hours
    
    def _create_anomaly_investigation(self, analysis_data: Dict[str, Any], 
                                    location: str, time_period: str, 
                                    baseline_period: str) -> AnomalyInvestigation:
        """Create structured anomaly investigation result"""
        analysis_result = analysis_data.get("analysis_result", {})
        statistical_analysis = analysis_data.get("statistical_analysis", {})
        
        # Determine anomaly type and severity
        anomaly_type = self._determine_anomaly_type(statistical_analysis)
        severity = self._determine_severity(analysis_result.get("confidence_score", 0))
        
        # Calculate deviation percentage
        deviation_percentage = self._calculate_deviation_percentage(statistical_analysis)
        
        # Extract root causes and contributing factors
        root_causes = analysis_result.get("primary_causes", [])
        contributing_factors = analysis_result.get("supporting_evidence", [])
        
        # Impact metrics
        impact_metrics = {
            "confidence_score": analysis_result.get("confidence_score", 0),
            "anomaly_detected": analysis_result.get("anomaly_detected", False),
            "impact_assessment": analysis_result.get("impact_assessment", ""),
            "data_quality": statistical_analysis.get("data_completeness", 0)
        }
        
        # Recommended actions
        recommended_actions = analysis_result.get("recommendations", [])
        
        return AnomalyInvestigation(
            anomaly_type=anomaly_type,
            severity=severity,
            baseline_period=baseline_period or "previous_week",
            anomaly_period=time_period,
            deviation_percentage=deviation_percentage,
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            impact_metrics=impact_metrics,
            recommended_actions=recommended_actions
        )
    
    def _determine_anomaly_type(self, statistical_analysis: Dict[str, Any]) -> str:
        """Determine the type of anomaly based on statistical analysis"""
        if not statistical_analysis:
            return "unknown"
        
        anomalies = statistical_analysis.get("anomalies", {})
        
        if anomalies.get("low_speed_periods", 0) > 0:
            return "congestion_spike"
        elif anomalies.get("high_volume_periods", 0) > 0:
            return "volume_increase"
        elif anomalies.get("congestion_events", 0) > 0:
            return "reliability_decrease"
        else:
            return "speed_drop"
    
    def _determine_severity(self, confidence_score: float) -> str:
        """Determine anomaly severity based on confidence score"""
        if confidence_score >= 0.9:
            return "critical"
        elif confidence_score >= 0.7:
            return "high"
        elif confidence_score >= 0.5:
            return "moderate"
        else:
            return "low"
    
    def _calculate_deviation_percentage(self, statistical_analysis: Dict[str, Any]) -> float:
        """Calculate percentage deviation from baseline"""
        if not statistical_analysis:
            return 0.0
        
        speed_stats = statistical_analysis.get("speed_stats", {})
        if not speed_stats:
            return 0.0
        
        # Calculate deviation based on speed variance
        variance = speed_stats.get("std", 0)
        mean_speed = speed_stats.get("mean", 0)
        
        if mean_speed > 0:
            return (variance / mean_speed) * 100
        
        return 0.0
    
    def _generate_investigation_summary(self, investigation: AnomalyInvestigation) -> Dict[str, Any]:
        """Generate a summary of the anomaly investigation"""
        return {
            "anomaly_detected": investigation.anomaly_type != "unknown",
            "severity": investigation.severity,
            "deviation": f"{investigation.deviation_percentage:.1f}%",
            "primary_cause": investigation.root_causes[0] if investigation.root_causes else "Unknown",
            "key_finding": investigation.contributing_factors[0] if investigation.contributing_factors else "No specific factors identified",
            "action_required": investigation.severity in ["high", "critical"],
            "confidence": investigation.impact_metrics.get("confidence_score", 0)
        }
    
    async def answer_user_question(self, question: UserQuestion) -> Dict[str, Any]:
        """Answer a specific user question about traffic patterns"""
        self.logger.info(f"Answering user question: {question.specific_question}")
        
        if question.question_type == "anomaly_investigation":
            return await self.investigate_anomaly(
                location=question.location,
                time_period=question.time_period,
                baseline_period=question.context.get("baseline_period") if question.context else None
            )
        else:
            # Handle other question types
            return await self._handle_other_question_types(question)
    
    async def _handle_other_question_types(self, question: UserQuestion) -> Dict[str, Any]:
        """Handle other types of user questions"""
        # This would be expanded to handle incident summaries, weather impacts, etc.
        return {
            "success": False,
            "error": f"Question type '{question.question_type}' not yet implemented",
            "question": question.specific_question
        }
    
    def get_anomaly_insights(self, investigation_data: Dict[str, Any]) -> List[str]:
        """Extract key insights from anomaly investigation"""
        insights = []
        
        if not investigation_data.get("success"):
            insights.append("❌ Investigation failed - unable to determine causes")
            return insights
        
        investigation = investigation_data.get("anomaly_investigation", {})
        
        if investigation.get("anomaly_type") != "unknown":
            insights.append(f"🔍 {investigation['anomaly_type'].replace('_', ' ').title()} detected")
        
        severity = investigation.get("severity", "unknown")
        if severity == "critical":
            insights.append("🚨 Critical anomaly - immediate attention required")
        elif severity == "high":
            insights.append("⚠️ High severity anomaly - investigation recommended")
        
        deviation = investigation.get("deviation_percentage", 0)
        if deviation > 20:
            insights.append(f"📊 Significant deviation: {deviation:.1f}% from baseline")
        elif deviation > 10:
            insights.append(f"📈 Moderate deviation: {deviation:.1f}% from baseline")
        
        root_causes = investigation.get("root_causes", [])
        if root_causes:
            insights.append(f"🎯 Primary cause: {root_causes[0]}")
        
        confidence = investigation.get("impact_metrics", {}).get("confidence_score", 0)
        if confidence > 0.8:
            insights.append("✅ High confidence analysis - reliable findings")
        elif confidence > 0.6:
            insights.append("⚠️ Moderate confidence - consider additional data")
        else:
            insights.append("❓ Low confidence - data quality issues")
        
        return insights
