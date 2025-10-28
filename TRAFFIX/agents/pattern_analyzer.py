"""
Pattern Analyzer Agent - Identifies recurring congestion patterns and causes
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import statistics

from agents.base_agent import BaseAgent
from models import ReportMode


class PatternAnalyzerAgent(BaseAgent):
    """Agent responsible for identifying recurring congestion patterns and causes"""
    
    def __init__(self):
        super().__init__("pattern_analyzer")
    
    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in traffic data"""
        collected_data = input_data.get("collected_data", {})
        location = input_data.get("location", "Unknown")
        analysis_period = input_data.get("analysis_period", "week")
        
        self.logger.info(f"Analyzing patterns for {location} over {analysis_period}")
        
        try:
            # Analyze temporal patterns
            temporal_patterns = self._analyze_temporal_patterns(collected_data)
            
            # Analyze recurring causes
            recurring_causes = self._analyze_recurring_causes(collected_data)
            
            # Analyze incident patterns
            incident_patterns = self._analyze_incident_patterns(collected_data)
            
            # Analyze weather impact patterns
            weather_patterns = self._analyze_weather_patterns(collected_data)
            
            # Generate mitigation strategies
            mitigation_strategies = self._generate_mitigation_strategies(
                temporal_patterns, recurring_causes, incident_patterns, weather_patterns
            )
            
            # Calculate pattern confidence
            pattern_confidence = self._calculate_pattern_confidence(
                temporal_patterns, recurring_causes, incident_patterns, weather_patterns
            )
            
            return {
                "temporal_patterns": temporal_patterns,
                "recurring_causes": recurring_causes,
                "incident_patterns": incident_patterns,
                "weather_patterns": weather_patterns,
                "mitigation_strategies": mitigation_strategies,
                "pattern_confidence": pattern_confidence,
                "analysis_metadata": {
                    "location": location,
                    "analysis_period": analysis_period,
                    "analyzed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {e}")
            raise
    
    def _analyze_temporal_patterns(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temporal patterns in traffic data"""
        traffic_data = collected_data.get("traffic_data", [])
        
        if not traffic_data:
            return {"error": "No traffic data available"}
        
        # Group by hour of day
        hourly_patterns = defaultdict(list)
        for item in traffic_data:
            try:
                timestamp = datetime.fromisoformat(item.get("timestamp", ""))
                hour = timestamp.hour
                hourly_patterns[hour].append({
                    "speed": item.get("speed", 0),
                    "volume": item.get("volume", 0),
                    "occupancy": item.get("occupancy", 0)
                })
            except:
                continue
        
        # Calculate hourly averages
        hourly_averages = {}
        for hour, data_points in hourly_patterns.items():
            if data_points:
                hourly_averages[hour] = {
                    "avg_speed": statistics.mean([dp["speed"] for dp in data_points]),
                    "avg_volume": statistics.mean([dp["volume"] for dp in data_points]),
                    "avg_occupancy": statistics.mean([dp["occupancy"] for dp in data_points]),
                    "data_points": len(data_points)
                }
        
        # Identify peak hours
        peak_hours = self._identify_peak_hours(hourly_averages)
        
        # Identify recurring congestion times
        congestion_times = self._identify_congestion_times(hourly_averages)
        
        return {
            "hourly_averages": hourly_averages,
            "peak_hours": peak_hours,
            "congestion_times": congestion_times,
            "pattern_strength": self._calculate_pattern_strength(hourly_averages)
        }
    
    def _analyze_recurring_causes(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze recurring causes of congestion"""
        incidents = collected_data.get("incidents", [])
        news_articles = collected_data.get("news_articles", [])
        
        # Analyze incident patterns
        incident_causes = []
        for incident in incidents:
            description = incident.get("description", "").lower()
            if "accident" in description or "crash" in description:
                incident_causes.append("accidents")
            elif "construction" in description:
                incident_causes.append("construction")
            elif "breakdown" in description or "disabled" in description:
                incident_causes.append("vehicle_breakdown")
            elif "weather" in description or "rain" in description or "snow" in description:
                incident_causes.append("weather")
            else:
                incident_causes.append("other")
        
        # Analyze news patterns
        news_themes = []
        for article in news_articles:
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            
            if "construction" in title or "construction" in content:
                news_themes.append("construction")
            elif "accident" in title or "crash" in title:
                news_themes.append("accidents")
            elif "weather" in title or "rain" in title or "snow" in title:
                news_themes.append("weather")
            elif "event" in title or "festival" in title or "game" in title:
                news_themes.append("events")
            else:
                news_themes.append("other")
        
        # Count recurring causes
        incident_counter = Counter(incident_causes)
        news_counter = Counter(news_themes)
        
        # Identify most common causes
        top_incident_causes = incident_counter.most_common(5)
        top_news_themes = news_counter.most_common(5)
        
        return {
            "incident_causes": dict(incident_counter),
            "news_themes": dict(news_counter),
            "top_incident_causes": top_incident_causes,
            "top_news_themes": top_news_themes,
            "recurring_causes": self._identify_recurring_causes(top_incident_causes, top_news_themes)
        }
    
    def _analyze_incident_patterns(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in traffic incidents"""
        incidents = collected_data.get("incidents", [])
        
        if not incidents:
            return {"error": "No incident data available"}
        
        # Group incidents by time
        hourly_incidents = defaultdict(int)
        daily_incidents = defaultdict(int)
        
        for incident in incidents:
            try:
                start_time = datetime.fromisoformat(incident.get("start_time", ""))
                hour = start_time.hour
                day = start_time.weekday()  # 0 = Monday, 6 = Sunday
                
                hourly_incidents[hour] += 1
                daily_incidents[day] += 1
            except:
                continue
        
        # Calculate incident frequency
        total_incidents = len(incidents)
        avg_incidents_per_hour = total_incidents / 24 if total_incidents > 0 else 0
        avg_incidents_per_day = total_incidents / 7 if total_incidents > 0 else 0
        
        # Identify high-incident periods
        high_incident_hours = [hour for hour, count in hourly_incidents.items() 
                              if count > avg_incidents_per_hour * 1.5]
        high_incident_days = [day for day, count in daily_incidents.items() 
                             if count > avg_incidents_per_day * 1.5]
        
        return {
            "total_incidents": total_incidents,
            "hourly_distribution": dict(hourly_incidents),
            "daily_distribution": dict(daily_incidents),
            "high_incident_hours": high_incident_hours,
            "high_incident_days": high_incident_days,
            "avg_incidents_per_hour": avg_incidents_per_hour,
            "avg_incidents_per_day": avg_incidents_per_day
        }
    
    def _analyze_weather_patterns(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze weather impact patterns"""
        weather_data = collected_data.get("weather_data", [])
        traffic_data = collected_data.get("traffic_data", [])
        
        if not weather_data or not traffic_data:
            return {"error": "Insufficient weather or traffic data"}
        
        # Correlate weather with traffic performance
        weather_impact = defaultdict(list)
        
        for weather in weather_data:
            try:
                weather_time = datetime.fromisoformat(weather.get("timestamp", ""))
                condition = weather.get("condition", "")
                impact = weather.get("traffic_impact", "low")
                
                # Find corresponding traffic data
                for traffic in traffic_data:
                    try:
                        traffic_time = datetime.fromisoformat(traffic.get("timestamp", ""))
                        # Check if times are within 1 hour
                        if abs((weather_time - traffic_time).total_seconds()) < 3600:
                            weather_impact[condition].append({
                                "speed": traffic.get("speed", 0),
                                "volume": traffic.get("volume", 0),
                                "occupancy": traffic.get("occupancy", 0),
                                "impact_level": impact
                            })
                    except:
                        continue
            except:
                continue
        
        # Calculate weather impact metrics
        weather_metrics = {}
        for condition, data_points in weather_impact.items():
            if data_points:
                avg_speed = statistics.mean([dp["speed"] for dp in data_points])
                avg_volume = statistics.mean([dp["volume"] for dp in data_points])
                avg_occupancy = statistics.mean([dp["occupancy"] for dp in data_points])
                
                weather_metrics[condition] = {
                    "avg_speed": avg_speed,
                    "avg_volume": avg_volume,
                    "avg_occupancy": avg_occupancy,
                    "data_points": len(data_points),
                    "impact_level": data_points[0]["impact_level"] if data_points else "unknown"
                }
        
        return {
            "weather_metrics": weather_metrics,
            "high_impact_conditions": [cond for cond, metrics in weather_metrics.items() 
                                     if metrics["impact_level"] in ["high", "moderate"]],
            "weather_traffic_correlation": self._calculate_weather_correlation(weather_metrics)
        }
    
    def _generate_mitigation_strategies(self, temporal_patterns: Dict[str, Any], 
                                      recurring_causes: Dict[str, Any],
                                      incident_patterns: Dict[str, Any],
                                      weather_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mitigation strategies based on identified patterns"""
        strategies = []
        
        # Temporal pattern strategies
        if temporal_patterns.get("congestion_times"):
            strategies.append({
                "type": "temporal_management",
                "priority": "high",
                "description": "Implement dynamic traffic management during peak congestion times",
                "target_times": temporal_patterns["congestion_times"],
                "actions": [
                    "Adjust signal timing during peak hours",
                    "Implement variable speed limits",
                    "Deploy additional traffic management personnel"
                ]
            })
        
        # Recurring cause strategies
        if recurring_causes.get("recurring_causes"):
            for cause in recurring_causes["recurring_causes"]:
                if cause == "accidents":
                    strategies.append({
                        "type": "safety_improvements",
                        "priority": "high",
                        "description": "Address recurring accident patterns",
                        "actions": [
                            "Improve road signage and markings",
                            "Install additional safety barriers",
                            "Implement speed reduction measures",
                            "Increase police presence during high-risk periods"
                        ]
                    })
                elif cause == "construction":
                    strategies.append({
                        "type": "construction_management",
                        "priority": "medium",
                        "description": "Optimize construction scheduling and management",
                        "actions": [
                            "Schedule construction during off-peak hours",
                            "Improve construction zone signage",
                            "Implement alternative routing",
                            "Coordinate with multiple construction projects"
                        ]
                    })
        
        # Incident pattern strategies
        if incident_patterns.get("high_incident_hours"):
            strategies.append({
                "type": "incident_response",
                "priority": "high",
                "description": "Enhance incident response during high-risk periods",
                "target_hours": incident_patterns["high_incident_hours"],
                "actions": [
                    "Pre-position emergency response vehicles",
                    "Implement rapid incident clearance protocols",
                    "Improve incident detection systems",
                    "Enhance communication with motorists"
                ]
            })
        
        # Weather pattern strategies
        if weather_patterns.get("high_impact_conditions"):
            strategies.append({
                "type": "weather_management",
                "priority": "medium",
                "description": "Improve traffic management during adverse weather",
                "target_conditions": weather_patterns["high_impact_conditions"],
                "actions": [
                    "Implement weather-responsive traffic management",
                    "Improve weather monitoring and alerting",
                    "Adjust speed limits during adverse conditions",
                    "Enhance road maintenance and drainage"
                ]
            })
        
        return strategies
    
    def _identify_peak_hours(self, hourly_averages: Dict[int, Dict[str, Any]]) -> List[int]:
        """Identify peak traffic hours"""
        if not hourly_averages:
            return []
        
        # Calculate average speed across all hours
        all_speeds = [data["avg_speed"] for data in hourly_averages.values()]
        overall_avg_speed = statistics.mean(all_speeds) if all_speeds else 0
        
        # Identify hours with significantly lower speeds (peak congestion)
        peak_hours = []
        for hour, data in hourly_averages.items():
            if data["avg_speed"] < overall_avg_speed * 0.8:  # 20% below average
                peak_hours.append(hour)
        
        return sorted(peak_hours)
    
    def _identify_congestion_times(self, hourly_averages: Dict[int, Dict[str, Any]]) -> List[int]:
        """Identify recurring congestion times"""
        if not hourly_averages:
            return []
        
        # Find hours with high occupancy and low speed
        congestion_hours = []
        for hour, data in hourly_averages.items():
            if data["avg_occupancy"] > 0.7 and data["avg_speed"] < 30:  # High occupancy, low speed
                congestion_hours.append(hour)
        
        return sorted(congestion_hours)
    
    def _calculate_pattern_strength(self, hourly_averages: Dict[int, Dict[str, Any]]) -> float:
        """Calculate the strength of temporal patterns"""
        if not hourly_averages:
            return 0.0
        
        # Calculate coefficient of variation for speed
        speeds = [data["avg_speed"] for data in hourly_averages.values()]
        if len(speeds) < 2:
            return 0.0
        
        mean_speed = statistics.mean(speeds)
        std_speed = statistics.stdev(speeds)
        
        if mean_speed == 0:
            return 0.0
        
        # Higher coefficient of variation indicates stronger patterns
        cv = std_speed / mean_speed
        return min(1.0, cv)  # Cap at 1.0
    
    def _identify_recurring_causes(self, incident_causes: List[tuple], 
                                 news_themes: List[tuple]) -> List[str]:
        """Identify recurring causes from incident and news data"""
        recurring = []
        
        # Look for causes that appear in both incidents and news
        incident_cause_names = [cause for cause, _ in incident_causes]
        news_theme_names = [theme for theme, _ in news_themes]
        
        for cause in incident_cause_names:
            if cause in news_theme_names and cause != "other":
                recurring.append(cause)
        
        return recurring
    
    def _calculate_weather_correlation(self, weather_metrics: Dict[str, Dict[str, Any]]) -> float:
        """Calculate correlation between weather and traffic performance"""
        if len(weather_metrics) < 2:
            return 0.0
        
        # Simple correlation based on speed variation across weather conditions
        speeds = [metrics["avg_speed"] for metrics in weather_metrics.values()]
        if len(speeds) < 2:
            return 0.0
        
        mean_speed = statistics.mean(speeds)
        std_speed = statistics.stdev(speeds)
        
        if mean_speed == 0:
            return 0.0
        
        # Higher variation indicates stronger weather correlation
        return min(1.0, std_speed / mean_speed)
    
    def _calculate_pattern_confidence(self, temporal_patterns: Dict[str, Any],
                                    recurring_causes: Dict[str, Any],
                                    incident_patterns: Dict[str, Any],
                                    weather_patterns: Dict[str, Any]) -> float:
        """Calculate overall confidence in pattern analysis"""
        confidence_factors = []
        
        # Temporal pattern confidence
        if temporal_patterns.get("pattern_strength"):
            confidence_factors.append(temporal_patterns["pattern_strength"])
        
        # Recurring cause confidence
        if recurring_causes.get("recurring_causes"):
            confidence_factors.append(min(1.0, len(recurring_causes["recurring_causes"]) / 3))
        
        # Incident pattern confidence
        if incident_patterns.get("total_incidents", 0) > 0:
            confidence_factors.append(min(1.0, incident_patterns["total_incidents"] / 10))
        
        # Weather pattern confidence
        if weather_patterns.get("weather_traffic_correlation"):
            confidence_factors.append(weather_patterns["weather_traffic_correlation"])
        
        if not confidence_factors:
            return 0.0
        
        return statistics.mean(confidence_factors)
