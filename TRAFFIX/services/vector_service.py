"""
Vector Database Service using Qdrant for RAG pipelines
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from tech_config import tech_settings


class VectorService:
    """Service for vector database operations using Qdrant"""
    
    def __init__(self):
        self.logger = logging.getLogger("traffix.vector_service")
        self.client = QdrantClient(
            url=tech_settings.qdrant_url,
            api_key=tech_settings.qdrant_api_key
        )
        self.embeddings = OpenAIEmbeddings(
            model=tech_settings.embedding_model,
            openai_api_key=tech_settings.openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=tech_settings.chunk_size,
            chunk_overlap=tech_settings.chunk_overlap
        )
        self.collection_name = tech_settings.qdrant_collection_name
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists in Qdrant"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=tech_settings.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
            else:
                self.logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            self.logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    async def add_traffic_data(self, traffic_data: List[Dict[str, Any]], 
                             location: str, data_type: str = "traffic") -> bool:
        """Add traffic data to vector database"""
        try:
            points = []
            
            for item in traffic_data:
                # Create text representation of traffic data
                text = self._create_traffic_text(item, location)
                
                # Split text into chunks
                chunks = self.text_splitter.split_text(text)
                
                for i, chunk in enumerate(chunks):
                    # Generate embedding
                    embedding = await self._get_embedding(chunk)
                    
                    # Create point
                    point_id = str(uuid.uuid4())
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk,
                            "location": location,
                            "data_type": data_type,
                            "timestamp": item.get("timestamp", datetime.now().isoformat()),
                            "original_data": item,
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    points.append(point)
            
            # Insert points into Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            self.logger.info(f"Added {len(points)} traffic data points to vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add traffic data: {e}")
            return False
    
    async def add_news_data(self, news_data: List[Dict[str, Any]], 
                          location: str) -> bool:
        """Add news data to vector database"""
        try:
            points = []
            
            for article in news_data:
                # Create text representation
                text = f"Title: {article.get('title', '')}\nContent: {article.get('content', '')}"
                
                # Split into chunks
                chunks = self.text_splitter.split_text(text)
                
                for i, chunk in enumerate(chunks):
                    embedding = await self._get_embedding(chunk)
                    
                    point_id = str(uuid.uuid4())
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk,
                            "location": location,
                            "data_type": "news",
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "published_at": article.get("published_at", ""),
                            "source": article.get("source", ""),
                            "relevance_score": article.get("relevance_score", 0.0),
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            self.logger.info(f"Added {len(points)} news data points to vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add news data: {e}")
            return False
    
    async def add_incident_data(self, incident_data: List[Dict[str, Any]], 
                              location: str) -> bool:
        """Add incident data to vector database"""
        try:
            points = []
            
            for incident in incident_data:
                text = f"Incident: {incident.get('description', '')}\nLocation: {incident.get('location', '')}\nSeverity: {incident.get('severity', '')}"
                
                chunks = self.text_splitter.split_text(text)
                
                for i, chunk in enumerate(chunks):
                    embedding = await self._get_embedding(chunk)
                    
                    point_id = str(uuid.uuid4())
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk,
                            "location": location,
                            "data_type": "incident",
                            "incident_id": incident.get("incident_id", ""),
                            "severity": incident.get("severity", ""),
                            "start_time": incident.get("start_time", ""),
                            "end_time": incident.get("end_time", ""),
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            self.logger.info(f"Added {len(points)} incident data points to vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add incident data: {e}")
            return False
    
    async def search_similar_content(self, query: str, location: str, 
                                   data_types: List[str] = None, 
                                   limit: int = None) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self._get_embedding(query)
            
            # Build filter
            filter_conditions = [
                FieldCondition(key="location", match=MatchValue(value=location))
            ]
            
            if data_types:
                filter_conditions.append(
                    FieldCondition(key="data_type", match=MatchValue(value=data_types[0]))
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit or tech_settings.top_k_results,
                score_threshold=tech_settings.similarity_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "data_type": result.payload.get("data_type", ""),
                    "location": result.payload.get("location", ""),
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["text", "data_type", "location"]}
                })
            
            self.logger.info(f"Found {len(results)} similar content items")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    async def get_context_for_analysis(self, query: str, location: str, 
                                     analysis_type: str = "general") -> Dict[str, List[Dict[str, Any]]]:
        """Get relevant context for analysis based on query and location"""
        try:
            # Determine data types based on analysis type
            data_type_mapping = {
                "anomaly_investigation": ["traffic", "incident", "news"],
                "leadership_summary": ["traffic", "news", "incident"],
                "pattern_analysis": ["traffic", "incident"],
                "general": ["traffic", "news", "incident"]
            }
            
            data_types = data_type_mapping.get(analysis_type, ["traffic", "news", "incident"])
            
            # Search for each data type
            context = {}
            for data_type in data_types:
                results = await self.search_similar_content(
                    query=query,
                    location=location,
                    data_types=[data_type],
                    limit=3
                )
                context[data_type] = results
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get context: {e}")
            return {}
    
    def _create_traffic_text(self, item: Dict[str, Any], location: str) -> str:
        """Create text representation of traffic data"""
        return f"""
        Location: {location}
        Timestamp: {item.get('timestamp', '')}
        Speed: {item.get('speed', 0)} mph
        Volume: {item.get('volume', 0)} vehicles
        Occupancy: {item.get('occupancy', 0):.2f}
        Congestion Level: {item.get('congestion_level', 'unknown')}
        Incident Detected: {item.get('incident_detected', False)}
        """.strip()
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to get embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * tech_settings.embedding_dimension
    
    async def clear_location_data(self, location: str) -> bool:
        """Clear all data for a specific location"""
        try:
            # Delete points with location filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="location", match=MatchValue(value=location))]
                )
            )
            
            self.logger.info(f"Cleared all data for location: {location}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear location data: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": collection_info.config.params.vectors.size,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {}
