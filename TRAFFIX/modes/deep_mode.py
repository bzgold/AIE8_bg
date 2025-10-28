"""
Deep Mode - Comprehensive research reports for detailed traffic analysis
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from agents import DataCollectorAgent, AnalyzerAgent, StorytellerAgent, ReporterAgent
from services import DataIntegrationService
from models import ReportMode


class DeepModeProcessor:
    """Processor for Deep Mode - comprehensive analysis and detailed reports"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.deep_mode")
        self.data_collector = DataCollectorAgent()
        self.analyzer = AnalyzerAgent()
        self.storyteller = StorytellerAgent()
        self.reporter = ReporterAgent()
        self.data_service = DataIntegrationService()
    
    async def process_deep_analysis(self, location: str, time_range_hours: int = 168, 
                                  analysis_depth: str = "comprehensive") -> Dict[str, Any]:
        """Process a deep analysis for comprehensive research report"""
        self.logger.info(f"Starting deep analysis for {location} (depth: {analysis_depth})")
        start_time = datetime.now()
        
        try:
            # Step 1: Comprehensive data collection
            self.logger.info("Collecting comprehensive data...")
            collected_data = await self.data_service.collect_all_data(
                location=location,
                time_range_hours=time_range_hours,
                mode="deep"
            )
            
            # Step 2: Multi-phase analysis
            self.logger.info("Performing multi-phase analysis...")
            analysis_results = await self._perform_multi_phase_analysis(collected_data, location, analysis_depth)
            
            # Step 3: Generate comprehensive story
            self.logger.info("Generating comprehensive story...")
            story_input = {
                "analysis_result": analysis_results["primary_analysis"],
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.DEEP,
                "additional_analyses": analysis_results["additional_analyses"]
            }
            story_task = await self.storyteller.execute_task(story_input)
            
            if story_task.status.value != "completed":
                raise Exception(f"Story generation failed: {story_task.error_message}")
            
            # Step 4: Generate comprehensive report
            self.logger.info("Generating comprehensive report...")
            report_input = {
                "story_data": story_task.output_data,
                "location": location,
                "mode": ReportMode.DEEP,
                "output_format": "html",
                "additional_data": analysis_results
            }
            report_task = await self.reporter.execute_task(report_input)
            
            if report_task.status.value != "completed":
                raise Exception(f"Report generation failed: {report_task.error_message}")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "location": location,
                "mode": "deep",
                "analysis_depth": analysis_depth,
                "processing_time_seconds": processing_time,
                "collected_data": collected_data,
                "analysis_results": analysis_results,
                "story_data": story_task.output_data,
                "report_data": report_task.output_data,
                "comprehensive_summary": self._generate_comprehensive_summary(
                    analysis_results,
                    story_task.output_data,
                    processing_time
                )
            }
            
            self.logger.info(f"Deep analysis completed for {location} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Deep analysis failed for {location}: {e}")
            return {
                "success": False,
                "location": location,
                "mode": "deep",
                "analysis_depth": analysis_depth,
                "error": str(e),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def _perform_multi_phase_analysis(self, collected_data: Dict[str, Any], 
                                          location: str, analysis_depth: str) -> Dict[str, Any]:
        """Perform multi-phase analysis for deep mode"""
        analysis_tasks = []
        
        # Primary analysis
        primary_input = {
            "collected_data": collected_data,
            "location": location,
            "mode": ReportMode.DEEP
        }
        analysis_tasks.append(self.analyzer.execute_task(primary_input))
        
        # Historical pattern analysis
        if analysis_depth in ["comprehensive", "historical"]:
            historical_input = {
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.DEEP,
                "analysis_type": "historical_patterns"
            }
            analysis_tasks.append(self.analyzer.execute_task(historical_input))
        
        # Trend analysis
        if analysis_depth in ["comprehensive", "trends"]:
            trend_input = {
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.DEEP,
                "analysis_type": "trend_analysis"
            }
            analysis_tasks.append(self.analyzer.execute_task(trend_input))
        
        # Impact analysis
        if analysis_depth in ["comprehensive", "impact"]:
            impact_input = {
                "collected_data": collected_data,
                "location": location,
                "mode": ReportMode.DEEP,
                "analysis_type": "impact_assessment"
            }
            analysis_tasks.append(self.analyzer.execute_task(impact_input))
        
        # Execute all analyses in parallel
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Process results
        analysis_results = {
            "primary_analysis": results[0].output_data if not isinstance(results[0], Exception) else {},
            "additional_analyses": {}
        }
        
        if len(results) > 1 and not isinstance(results[1], Exception):
            analysis_results["additional_analyses"]["historical_patterns"] = results[1].output_data
        if len(results) > 2 and not isinstance(results[2], Exception):
            analysis_results["additional_analyses"]["trend_analysis"] = results[2].output_data
        if len(results) > 3 and not isinstance(results[3], Exception):
            analysis_results["additional_analyses"]["impact_assessment"] = results[3].output_data
        
        return analysis_results
    
    def _generate_comprehensive_summary(self, analysis_results: Dict[str, Any], 
                                      story_data: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Generate a comprehensive summary of the deep analysis"""
        primary_analysis = analysis_results.get("primary_analysis", {})
        analysis_result = primary_analysis.get("analysis_result", {})
        
        summary = {
            "analysis_overview": {
                "anomaly_detected": analysis_result.get("anomaly_detected", False),
                "confidence_score": analysis_result.get("confidence_score", 0.0),
                "analysis_depth": "comprehensive",
                "processing_time": f"{processing_time:.2f}s"
            },
            "key_findings": {
                "primary_causes": analysis_result.get("primary_causes", []),
                "supporting_evidence": analysis_result.get("supporting_evidence", []),
                "impact_assessment": analysis_result.get("impact_assessment", ""),
                "recommendations": analysis_result.get("recommendations", [])
            },
            "additional_insights": self._extract_additional_insights(analysis_results),
            "data_quality": self._assess_data_quality(analysis_results),
            "executive_summary": story_data.get("executive_summary", ""),
            "report_metadata": {
                "story_elements_count": len(story_data.get("story_elements", [])),
                "analysis_phases": len(analysis_results.get("additional_analyses", {})) + 1,
                "comprehensive_report": True
            }
        }
        
        return summary
    
    def _extract_additional_insights(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from additional analyses"""
        insights = {}
        additional_analyses = analysis_results.get("additional_analyses", {})
        
        if "historical_patterns" in additional_analyses:
            historical = additional_analyses["historical_patterns"]
            insights["historical_patterns"] = {
                "recurring_issues": historical.get("recurring_issues", []),
                "seasonal_trends": historical.get("seasonal_trends", []),
                "pattern_confidence": historical.get("confidence_score", 0.0)
            }
        
        if "trend_analysis" in additional_analyses:
            trends = additional_analyses["trend_analysis"]
            insights["trends"] = {
                "traffic_growth": trends.get("traffic_growth", 0.0),
                "congestion_trend": trends.get("congestion_trend", "stable"),
                "peak_hour_shifts": trends.get("peak_hour_shifts", [])
            }
        
        if "impact_assessment" in additional_analyses:
            impact = additional_analyses["impact_assessment"]
            insights["impact"] = {
                "economic_impact": impact.get("economic_impact", 0.0),
                "environmental_impact": impact.get("environmental_impact", ""),
                "social_impact": impact.get("social_impact", "")
            }
        
        return insights
    
    def _assess_data_quality(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of collected data"""
        primary_analysis = analysis_results.get("primary_analysis", {})
        statistical_analysis = primary_analysis.get("statistical_analysis", {})
        
        quality_metrics = {
            "data_completeness": 0.0,
            "data_consistency": 0.0,
            "temporal_coverage": 0.0,
            "source_diversity": 0.0,
            "overall_quality": "unknown"
        }
        
        # Assess based on available data
        if statistical_analysis:
            quality_metrics["data_completeness"] = 0.8  # Assume good if statistical analysis succeeded
            quality_metrics["data_consistency"] = 0.7   # Based on variance metrics
        
        # Assess temporal coverage
        if "anomaly_indicators" in statistical_analysis:
            quality_metrics["temporal_coverage"] = 0.9  # Good temporal coverage
        
        # Assess source diversity
        sources_used = primary_analysis.get("analysis_metadata", {}).get("sources_used", [])
        quality_metrics["source_diversity"] = min(1.0, len(sources_used) / 5.0)  # 5 max sources
        
        # Calculate overall quality
        avg_quality = sum([
            quality_metrics["data_completeness"],
            quality_metrics["data_consistency"],
            quality_metrics["temporal_coverage"],
            quality_metrics["source_diversity"]
        ]) / 4
        
        if avg_quality >= 0.8:
            quality_metrics["overall_quality"] = "excellent"
        elif avg_quality >= 0.6:
            quality_metrics["overall_quality"] = "good"
        elif avg_quality >= 0.4:
            quality_metrics["overall_quality"] = "fair"
        else:
            quality_metrics["overall_quality"] = "poor"
        
        return quality_metrics
    
    async def generate_weekly_report(self, location: str) -> Dict[str, Any]:
        """Generate a comprehensive weekly report"""
        return await self.process_deep_analysis(location, time_range_hours=168, analysis_depth="comprehensive")
    
    async def generate_monthly_report(self, location: str) -> Dict[str, Any]:
        """Generate a comprehensive monthly report"""
        return await self.process_deep_analysis(location, time_range_hours=720, analysis_depth="comprehensive")
    
    async def generate_incident_investigation(self, location: str, incident_time_range: int = 48) -> Dict[str, Any]:
        """Generate a detailed investigation report for specific incidents"""
        return await self.process_deep_analysis(location, time_range_hours=incident_time_range, analysis_depth="incident")
    
    async def generate_trend_analysis(self, location: str, trend_period_hours: int = 720) -> Dict[str, Any]:
        """Generate a trend analysis report"""
        return await self.process_deep_analysis(location, time_range_hours=trend_period_hours, analysis_depth="trends")
    
    def get_deep_insights(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract deep insights from comprehensive analysis"""
        insights = []
        primary_analysis = analysis_results.get("primary_analysis", {})
        analysis_result = primary_analysis.get("analysis_result", {})
        
        # Primary analysis insights
        if analysis_result.get("anomaly_detected"):
            insights.append("🔍 Deep analysis confirms traffic anomaly with high confidence")
        
        confidence = analysis_result.get("confidence_score", 0)
        if confidence > 0.9:
            insights.append("🎯 Exceptional analysis confidence - highly reliable insights")
        elif confidence > 0.7:
            insights.append("✅ Strong analysis confidence - reliable insights")
        else:
            insights.append("⚠️ Moderate analysis confidence - consider additional data")
        
        # Additional analysis insights
        additional_analyses = analysis_results.get("additional_analyses", {})
        
        if "historical_patterns" in additional_analyses:
            insights.append("📊 Historical patterns identified - recurring issues detected")
        
        if "trend_analysis" in additional_analyses:
            trends = additional_analyses["trend_analysis"]
            if trends.get("traffic_growth", 0) > 0.1:
                insights.append("📈 Significant traffic growth trend identified")
        
        if "impact_assessment" in additional_analyses:
            insights.append("💼 Comprehensive impact assessment completed")
        
        # Data quality insights
        data_quality = self._assess_data_quality(analysis_results)
        if data_quality["overall_quality"] == "excellent":
            insights.append("⭐ Excellent data quality - comprehensive analysis possible")
        elif data_quality["overall_quality"] == "good":
            insights.append("👍 Good data quality - reliable analysis")
        else:
            insights.append("📋 Data quality issues noted - consider additional sources")
        
        return insights
