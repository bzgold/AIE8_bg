"""
Data integration services for various data sources
"""
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from config import settings


class RITISService:
    """Service for integrating with RITIS API"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.ritis")
        self.base_url = settings.ritis_base_url
        self.api_key = settings.ritis_api_key
    
    async def get_traffic_data(self, location: str, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        """Get traffic data from RITIS API"""
        try:
            # This is a mock implementation - replace with actual RITIS API calls
            self.logger.info(f"Fetching RITIS data for {location}")
            
            # Simulate API call delay
            await asyncio.sleep(0.5)
            
            # Mock data - replace with actual API integration
            traffic_data = []
            base_time = datetime.now() - timedelta(hours=time_range_hours)
            
            for i in range(0, time_range_hours, 2):  # Every 2 hours
                traffic_data.append({
                    "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                    "location": location,
                    "speed": 45.0 + (i % 20) - 10,  # Varying speeds
                    "volume": 1200 + (i % 500) - 250,
                    "occupancy": 0.3 + (i % 30) / 100,
                    "congestion_level": self._determine_congestion_level(i),
                    "incident_detected": i % 7 == 0,
                    "source": "ritis"
                })
            
            return traffic_data
            
        except Exception as e:
            self.logger.error(f"RITIS data fetch failed: {e}")
            return []
    
    def _determine_congestion_level(self, hour_offset: int) -> str:
        """Determine congestion level based on time patterns"""
        if 7 <= hour_offset % 24 <= 9 or 17 <= hour_offset % 24 <= 19:
            return "high"
        elif 6 <= hour_offset % 24 <= 10 or 16 <= hour_offset % 24 <= 20:
            return "moderate"
        else:
            return "light"
    
    async def get_incident_data(self, location: str, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        """Get incident data from RITIS"""
        try:
            self.logger.info(f"Fetching RITIS incident data for {location}")
            
            # Mock incident data
            incidents = []
            base_time = datetime.now() - timedelta(hours=time_range_hours)
            
            incident_types = [
                "Vehicle breakdown",
                "Accident",
                "Road construction",
                "Weather related closure",
                "Emergency vehicle response"
            ]
            
            for i in range(2):  # 2 incidents
                incidents.append({
                    "incident_id": f"RITIS_{i:04d}",
                    "description": f"{incident_types[i % len(incident_types)]} on {location}",
                    "location": f"{location} Highway, Mile {i+10}",
                    "severity": "moderate" if i % 2 == 0 else "minor",
                    "start_time": (base_time + timedelta(hours=i*6)).isoformat(),
                    "end_time": (base_time + timedelta(hours=i*6+2)).isoformat(),
                    "impact_radius": 2.0 + i,
                    "affected_roads": [f"{location} Highway"],
                    "source": "ritis"
                })
            
            return incidents
            
        except Exception as e:
            self.logger.error(f"RITIS incident data fetch failed: {e}")
            return []


class NewsService:
    """Service for integrating with news APIs"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.news")
        self.api_key = settings.news_api_key
    
    async def get_traffic_news(self, location: str, time_range_hours: int = 24, 
                             max_articles: int = 10) -> List[Dict[str, Any]]:
        """Get traffic-related news articles"""
        try:
            self.logger.info(f"Fetching news data for {location}")
            
            # Mock news data - replace with actual news API integration
            articles = []
            base_time = datetime.now() - timedelta(hours=time_range_hours)
            
            news_sources = ["Local News", "Traffic Authority", "City Updates", "Transportation Dept"]
            news_titles = [
                f"Traffic congestion reported on {location} highway",
                f"Road construction causes delays in {location}",
                f"Accident on {location} freeway blocks traffic",
                f"Weather impacts traffic flow in {location}",
                f"New traffic management system for {location}",
                f"Rush hour delays on {location} corridor",
                f"Emergency road closure in {location}",
                f"Traffic signal malfunction affects {location}"
            ]
            
            for i in range(min(max_articles, len(news_titles))):
                articles.append({
                    "title": news_titles[i],
                    "content": self._generate_news_content(news_titles[i], location),
                    "url": f"https://example-news.com/article/{i}",
                    "published_at": (base_time + timedelta(hours=i*2)).isoformat(),
                    "source": news_sources[i % len(news_sources)],
                    "relevance_score": 0.8 + (i % 20) / 100,
                    "location_keywords": [location.lower(), "traffic", "highway", "road"],
                    "data_source": "news"
                })
            
            return articles
            
        except Exception as e:
            self.logger.error(f"News data fetch failed: {e}")
            return []
    
    def _generate_news_content(self, title: str, location: str) -> str:
        """Generate mock news content"""
        return f"""
        {title}
        
        This is a detailed news article about transportation issues affecting {location}. 
        The article discusses various factors contributing to traffic congestion and 
        provides insights into local transportation challenges.
        
        Key points covered:
        - Current traffic conditions
        - Impact on commuters
        - Planned improvements
        - Community response
        
        This content is generated for demonstration purposes and represents the type 
        of information that would be gathered from real news sources.
        """.strip()


class WeatherService:
    """Service for integrating with weather APIs"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.weather")
    
    async def get_weather_data(self, location: str, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        """Get weather data that might affect traffic"""
        try:
            self.logger.info(f"Fetching weather data for {location}")
            
            # Mock weather data
            weather_data = []
            base_time = datetime.now() - timedelta(hours=time_range_hours)
            
            weather_conditions = ["clear", "rain", "fog", "snow", "cloudy"]
            
            for i in range(0, time_range_hours, 6):  # Every 6 hours
                condition = weather_conditions[i % len(weather_conditions)]
                weather_data.append({
                    "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                    "location": location,
                    "condition": condition,
                    "temperature": 20 + (i % 15) - 7,  # 13-35°C
                    "precipitation": 0.1 if condition in ["rain", "snow"] else 0.0,
                    "visibility": 10.0 if condition == "clear" else 5.0 if condition == "fog" else 8.0,
                    "wind_speed": 5 + (i % 10),
                    "traffic_impact": self._assess_traffic_impact(condition),
                    "source": "weather"
                })
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Weather data fetch failed: {e}")
            return []
    
    def _assess_traffic_impact(self, condition: str) -> str:
        """Assess traffic impact of weather condition"""
        if condition in ["rain", "snow", "fog"]:
            return "high"
        elif condition == "cloudy":
            return "moderate"
        else:
            return "low"


class SocialMediaService:
    """Service for integrating with social media APIs"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.social")
    
    async def get_traffic_posts(self, location: str, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        """Get traffic-related social media posts"""
        try:
            self.logger.info(f"Fetching social media data for {location}")
            
            # Mock social media data
            posts = []
            base_time = datetime.now() - timedelta(hours=time_range_hours)
            
            platforms = ["Twitter", "Facebook", "Reddit", "Instagram"]
            post_types = ["complaint", "update", "warning", "question", "observation"]
            
            for i in range(5):  # 5 posts
                posts.append({
                    "post_id": f"social_{i:04d}",
                    "content": f"Traffic is terrible on {location} right now! #traffic #{location.lower()}",
                    "platform": platforms[i % len(platforms)],
                    "author": f"user_{i}",
                    "posted_at": (base_time + timedelta(hours=i*4)).isoformat(),
                    "post_type": post_types[i % len(post_types)],
                    "sentiment": "negative" if i % 2 == 0 else "neutral",
                    "location_keywords": [location.lower()],
                    "engagement": 10 + (i % 50),
                    "source": "social"
                })
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Social media data fetch failed: {e}")
            return []


class DataIntegrationService:
    """Main service for coordinating data collection from all sources"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.data_integration")
        self.ritis = RITISService()
        self.news = NewsService()
        self.weather = WeatherService()
        self.social = SocialMediaService()
    
    async def collect_all_data(self, location: str, time_range_hours: int = 24, 
                             mode: str = "quick") -> Dict[str, Any]:
        """Collect data from all available sources"""
        self.logger.info(f"Starting data collection for {location} in {mode} mode")
        
        # Determine max sources based on mode
        max_news_articles = 5 if mode == "quick" else 20
        max_social_posts = 3 if mode == "quick" else 10
        
        try:
            # Collect data from all sources in parallel
            tasks = [
                self.ritis.get_traffic_data(location, time_range_hours),
                self.ritis.get_incident_data(location, time_range_hours),
                self.news.get_traffic_news(location, time_range_hours, max_news_articles),
                self.weather.get_weather_data(location, time_range_hours),
                self.social.get_traffic_posts(location, time_range_hours)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            collected_data = {
                "traffic_data": results[0] if not isinstance(results[0], Exception) else [],
                "incidents": results[1] if not isinstance(results[1], Exception) else [],
                "news_articles": results[2] if not isinstance(results[2], Exception) else [],
                "weather_data": results[3] if not isinstance(results[3], Exception) else [],
                "social_posts": results[4] if not isinstance(results[4], Exception) else [],
                "collection_metadata": {
                    "location": location,
                    "time_range_hours": time_range_hours,
                    "mode": mode,
                    "collected_at": datetime.now().isoformat(),
                    "sources_used": self._get_successful_sources(results)
                }
            }
            
            self.logger.info(f"Data collection completed for {location}")
            return collected_data
            
        except Exception as e:
            self.logger.error(f"Data collection failed: {e}")
            return {
                "traffic_data": [],
                "incidents": [],
                "news_articles": [],
                "weather_data": [],
                "social_posts": [],
                "collection_metadata": {
                    "location": location,
                    "time_range_hours": time_range_hours,
                    "mode": mode,
                    "collected_at": datetime.now().isoformat(),
                    "error": str(e)
                }
            }
    
    def _get_successful_sources(self, results: List[Any]) -> List[str]:
        """Get list of sources that successfully returned data"""
        sources = []
        source_names = ["ritis_traffic", "ritis_incidents", "news", "weather", "social"]
        
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                sources.append(source_names[i])
        
        return sources
