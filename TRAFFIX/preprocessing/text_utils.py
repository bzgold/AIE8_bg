"""
Text processing utilities adapted from assignment 02
"""
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class TextFileLoader:
    """Enhanced text file loader for traffic data"""
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.documents = []
        self.path = path
        self.encoding = encoding

    def load(self):
        if os.path.isdir(self.path):
            self.load_directory()
        elif os.path.isfile(self.path) and self.path.endswith((".txt", ".csv", ".json")):
            self.load_file()
        else:
            raise ValueError(
                "Provided path is neither a valid directory nor a supported file type."
            )

    def load_file(self):
        if self.path.endswith(".txt"):
            with open(self.path, "r", encoding=self.encoding) as f:
                self.documents.append(f.read())
        elif self.path.endswith(".csv"):
            import pandas as pd
            df = pd.read_csv(self.path)
            self.documents.append(df.to_string())
        elif self.path.endswith(".json"):
            import json
            with open(self.path, "r", encoding=self.encoding) as f:
                data = json.load(f)
                self.documents.append(json.dumps(data, indent=2))

    def load_directory(self):
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith((".txt", ".csv", ".json")):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding=self.encoding) as f:
                        if file.endswith(".txt"):
                            self.documents.append(f.read())
                        elif file.endswith(".csv"):
                            import pandas as pd
                            df = pd.read_csv(file_path)
                            self.documents.append(df.to_string())
                        elif file.endswith(".json"):
                            import json
                            data = json.load(f)
                            self.documents.append(json.dumps(data, indent=2))

    def load_documents(self):
        self.load()
        return self.documents


class CharacterTextSplitter:
    """Enhanced text splitter for traffic data"""
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        assert (
            chunk_size > chunk_overlap
        ), "Chunk size must be greater than chunk overlap"

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i : i + self.chunk_size])
        return chunks

    def split_texts(self, texts: List[str]) -> List[str]:
        chunks = []
        for text in texts:
            chunks.extend(self.split(text))
        return chunks

    def split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences for better traffic data processing"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks


class TrafficDataPreprocessor:
    """Specialized preprocessor for traffic data"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = CharacterTextSplitter(chunk_size, chunk_overlap)
    
    def preprocess_traffic_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess traffic data for analysis"""
        processed_data = {
            "raw_data": data,
            "processed_texts": [],
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }
        }
        
        # Process different data types
        if "traffic_data" in data:
            processed_data["processed_texts"].extend(
                self._process_traffic_metrics(data["traffic_data"])
            )
        
        if "incidents" in data:
            processed_data["processed_texts"].extend(
                self._process_incidents(data["incidents"])
            )
        
        if "news_articles" in data:
            processed_data["processed_texts"].extend(
                self._process_news_articles(data["news_articles"])
            )
        
        if "weather_data" in data:
            processed_data["processed_texts"].extend(
                self._process_weather_data(data["weather_data"])
            )
        
        # Create chunks for vector storage
        processed_data["chunks"] = self.splitter.split_texts(processed_data["processed_texts"])
        
        return processed_data
    
    def _process_traffic_metrics(self, traffic_data: List[Dict[str, Any]]) -> List[str]:
        """Process traffic metrics into text format"""
        texts = []
        
        for data_point in traffic_data:
            text = f"Traffic data at {data_point.get('timestamp', 'unknown time')}: "
            text += f"Speed {data_point.get('speed', 'N/A')} mph, "
            text += f"Volume {data_point.get('volume', 'N/A')} vehicles/hour, "
            text += f"Occupancy {data_point.get('occupancy', 'N/A')}%. "
            
            if data_point.get('incident_detected'):
                text += "Incident detected. "
            
            texts.append(text)
        
        return texts
    
    def _process_incidents(self, incidents: List[Dict[str, Any]]) -> List[str]:
        """Process incident data into text format"""
        texts = []
        
        for incident in incidents:
            text = f"Traffic incident: {incident.get('description', 'Unknown incident')}. "
            text += f"Severity: {incident.get('severity', 'Unknown')}. "
            text += f"Location: {incident.get('location', 'Unknown location')}. "
            text += f"Time: {incident.get('start_time', 'Unknown')} to {incident.get('end_time', 'Unknown')}. "
            
            if incident.get('impact_assessment'):
                text += f"Impact: {incident['impact_assessment']}. "
            
            texts.append(text)
        
        return texts
    
    def _process_news_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Process news articles into text format"""
        texts = []
        
        for article in articles:
            text = f"News article: {article.get('title', 'No title')}. "
            text += f"Source: {article.get('source', 'Unknown source')}. "
            text += f"Published: {article.get('published_at', 'Unknown date')}. "
            text += f"Content: {article.get('content', 'No content')[:500]}... "
            
            texts.append(text)
        
        return texts
    
    def _process_weather_data(self, weather_data: List[Dict[str, Any]]) -> List[str]:
        """Process weather data into text format"""
        texts = []
        
        for weather in weather_data:
            text = f"Weather at {weather.get('timestamp', 'unknown time')}: "
            text += f"Condition: {weather.get('condition', 'Unknown')}. "
            text += f"Temperature: {weather.get('temperature', 'N/A')}°F. "
            text += f"Traffic impact: {weather.get('traffic_impact', 'Unknown')}. "
            
            texts.append(text)
        
        return texts
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from traffic-related text"""
        # Traffic-related keywords
        traffic_keywords = [
            "congestion", "delay", "incident", "accident", "crash", "breakdown",
            "construction", "closure", "detour", "jam", "backup", "bottleneck",
            "speed", "volume", "occupancy", "flow", "density", "reliability"
        ]
        
        # Weather-related keywords
        weather_keywords = [
            "rain", "snow", "fog", "ice", "storm", "wind", "visibility",
            "precipitation", "temperature", "weather"
        ]
        
        # Event-related keywords
        event_keywords = [
            "event", "festival", "concert", "sports", "parade", "protest",
            "construction", "maintenance", "roadwork"
        ]
        
        all_keywords = traffic_keywords + weather_keywords + event_keywords
        
        found_phrases = []
        text_lower = text.lower()
        
        for keyword in all_keywords:
            if keyword in text_lower:
                found_phrases.append(keyword)
        
        return found_phrases
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        
        # Normalize case
        text = text.strip()
        
        return text
