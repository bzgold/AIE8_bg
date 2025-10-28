"""
Data Collector Agent - Collects data from various sources
"""
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from agents.base_agent import BaseAgent
from models import TrafficData, NewsArticle, IncidentReport, DataSource, ReportMode
from config import settings


class DataCollectorAgent(BaseAgent):
    """Agent responsible for collecting data from various sources"""
    
    def __init__(self):
        super().__init__("data_collector")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data from specified sources"""
        mode = input_data.get("mode", ReportMode.QUICK)
        location = input_data.get("location", "")
        time_range = input_data.get("time_range", 24)  # hours
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Collect data from all sources in parallel
            tasks = []
            
            if input_data.get("collect_traffic", True):
                tasks.append(self._collect_traffic_data(location, time_range))
            
            if input_data.get("collect_news", True):
                tasks.append(self._collect_news_data(location, time_range, mode))
            
            if input_data.get("collect_incidents", True):
                tasks.append(self._collect_incident_data(location, time_range))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            collected_data = {
                "traffic_data": [],
                "news_articles": [],
                "incidents": [],
                "collection_metadata": {
                    "mode": mode,
                    "location": location,
                    "time_range_hours": time_range,
                    "collected_at": datetime.now().isoformat()
                }
            }
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Data collection task {i} failed: {result}")
                    continue
                
                if i == 0:  # Traffic data
                    collected_data["traffic_data"] = result
                elif i == 1:  # News data
                    collected_data["news_articles"] = result
                elif i == 2:  # Incident data
                    collected_data["incidents"] = result
            
            return collected_data
            
        finally:
            if self.session:
                await self.session.close()
                self.session = None
    
    async def _collect_traffic_data(self, location: str, time_range: int) -> List[Dict[str, Any]]:
        """Collect traffic data from RITIS API"""
        try:
            # Simulate RITIS API call (replace with actual implementation)
            self.logger.info(f"Collecting traffic data for {location}")
            
            # Mock data for demonstration
            traffic_data = []
            base_time = datetime.now() - timedelta(hours=time_range)
            
            for i in range(0, time_range, 2):  # Every 2 hours
                traffic_data.append({
                    "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                    "location": location,
                    "speed": 45.0 + (i % 20),  # Varying speeds
                    "volume": 1200 + (i % 500),
                    "occupancy": 0.3 + (i % 30) / 100,
                    "congestion_level": "moderate" if i % 3 == 0 else "light",
                    "incident_detected": i % 7 == 0
                })
            
            return traffic_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect traffic data: {e}")
            return []
    
    async def _collect_news_data(self, location: str, time_range: int, mode: ReportMode) -> List[Dict[str, Any]]:
        """Collect news articles related to traffic and transportation"""
        try:
            self.logger.info(f"Collecting news data for {location}")
            
            # Determine max articles based on mode
            max_articles = 5 if mode == ReportMode.QUICK else 20
            
            # Mock news data (replace with actual news API integration)
            news_articles = []
            base_time = datetime.now() - timedelta(hours=time_range)
            
            sample_titles = [
                f"Traffic congestion reported on {location} highway",
                f"Road construction causes delays in {location}",
                f"Accident on {location} freeway blocks traffic",
                f"Weather impacts traffic flow in {location}",
                f"New traffic management system for {location}"
            ]
            
            for i in range(min(max_articles, len(sample_titles))):
                news_articles.append({
                    "title": sample_titles[i],
                    "content": f"Sample news content about traffic in {location}. This is a detailed article about transportation issues affecting the area.",
                    "url": f"https://example-news.com/article/{i}",
                    "published_at": (base_time + timedelta(hours=i*2)).isoformat(),
                    "source": "Local News",
                    "relevance_score": 0.8 + (i % 20) / 100,
                    "location_keywords": [location.lower()]
                })
            
            return news_articles
            
        except Exception as e:
            self.logger.error(f"Failed to collect news data: {e}")
            return []
    
    async def _collect_incident_data(self, location: str, time_range: int) -> List[Dict[str, Any]]:
        """Collect traffic incident data"""
        try:
            self.logger.info(f"Collecting incident data for {location}")
            
            # Mock incident data (replace with actual incident API integration)
            incidents = []
            base_time = datetime.now() - timedelta(hours=time_range)
            
            sample_incidents = [
                {
                    "incident_id": f"INC_{i:04d}",
                    "description": f"Vehicle breakdown on {location} highway",
                    "location": f"{location} Highway, Mile {i+10}",
                    "severity": "minor" if i % 2 == 0 else "moderate",
                    "start_time": (base_time + timedelta(hours=i*3)).isoformat(),
                    "end_time": (base_time + timedelta(hours=i*3+1)).isoformat(),
                    "impact_radius": 2.0 + i,
                    "affected_roads": [f"{location} Highway", f"Side Street {i}"]
                }
                for i in range(3)  # 3 incidents
            ]
            
            return sample_incidents
            
        except Exception as e:
            self.logger.error(f"Failed to collect incident data: {e}")
            return []
