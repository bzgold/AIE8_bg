"""
Enhanced vector database adapted from assignment 02
"""
import numpy as np
from collections import defaultdict
from typing import List, Tuple, Callable, Dict, Any, Optional
import asyncio
import json
from datetime import datetime

from services.vector_service import VectorService


def cosine_similarity(vector_a: np.array, vector_b: np.array) -> float:
    """Computes the cosine similarity between two vectors."""
    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def euclidean_distance(vector_a: np.array, vector_b: np.array) -> float:
    """Computes the euclidean distance between two vectors."""
    return np.linalg.norm(vector_a - vector_b)


class EnhancedVectorDatabase:
    """Enhanced vector database for traffic data with metadata support"""
    
    def __init__(self, vector_service: VectorService = None):
        self.vectors = defaultdict(np.array)
        self.metadata = defaultdict(dict)
        self.vector_service = vector_service or VectorService()
        self.index = {}  # For fast lookups

    def insert(self, key: str, vector: np.array, metadata: Dict[str, Any] = None) -> None:
        """Insert a vector with optional metadata"""
        self.vectors[key] = vector
        self.metadata[key] = metadata or {}
        self.metadata[key]['inserted_at'] = datetime.now().isoformat()

    def search(
        self,
        query_vector: np.array,
        k: int,
        distance_measure: Callable = cosine_similarity,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors with optional metadata filtering"""
        scores = []
        
        for key, vector in self.vectors.items():
            # Apply metadata filtering if specified
            if filter_metadata:
                if not self._matches_filter(self.metadata[key], filter_metadata):
                    continue
            
            distance = distance_measure(query_vector, vector)
            scores.append((key, distance, self.metadata[key]))
        
        # Sort by similarity (higher is better for cosine similarity)
        reverse = distance_measure == cosine_similarity
        return sorted(scores, key=lambda x: x[1], reverse=reverse)[:k]

    def search_by_text(
        self,
        query_text: str,
        k: int,
        distance_measure: Callable = cosine_similarity,
        return_as_text: bool = False,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search by text query"""
        query_vector = self.vector_service.get_embedding(query_text)
        results = self.search(query_vector, k, distance_measure, filter_metadata)
        
        if return_as_text:
            return [(result[0], result[1], result[2]) for result in results]
        return results

    def retrieve_from_key(self, key: str) -> Tuple[np.array, Dict[str, Any]]:
        """Retrieve vector and metadata by key"""
        vector = self.vectors.get(key, None)
        metadata = self.metadata.get(key, {})
        return vector, metadata

    async def abuild_from_traffic_data(self, traffic_data: Dict[str, Any]) -> "EnhancedVectorDatabase":
        """Build vector database from traffic data"""
        # Extract text chunks from traffic data
        from .text_utils import TrafficDataPreprocessor
        
        preprocessor = TrafficDataPreprocessor()
        processed_data = preprocessor.preprocess_traffic_data(traffic_data)
        
        # Create embeddings for each chunk
        chunks = processed_data["chunks"]
        embeddings = await self.vector_service.get_embeddings_async(chunks)
        
        # Insert vectors with metadata
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            key = f"chunk_{i}"
            metadata = {
                "chunk_index": i,
                "chunk_size": len(chunk),
                "data_type": self._classify_chunk_type(chunk),
                "processed_at": datetime.now().isoformat()
            }
            self.insert(key, np.array(embedding), metadata)
        
        return self

    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_metadata.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True

    def _classify_chunk_type(self, chunk: str) -> str:
        """Classify chunk type based on content"""
        chunk_lower = chunk.lower()
        
        if any(word in chunk_lower for word in ["incident", "accident", "crash"]):
            return "incident"
        elif any(word in chunk_lower for word in ["speed", "volume", "occupancy"]):
            return "traffic_metrics"
        elif any(word in chunk_lower for word in ["news", "article", "published"]):
            return "news"
        elif any(word in chunk_lower for word in ["weather", "rain", "snow", "temperature"]):
            return "weather"
        else:
            return "general"

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "total_vectors": len(self.vectors),
            "data_types": self._get_data_type_counts(),
            "average_vector_dimension": self._get_average_dimension(),
            "last_updated": max(
                [meta.get('inserted_at', '') for meta in self.metadata.values()],
                default='Never'
            )
        }

    def _get_data_type_counts(self) -> Dict[str, int]:
        """Get count of each data type"""
        counts = defaultdict(int)
        for metadata in self.metadata.values():
            data_type = metadata.get('data_type', 'unknown')
            counts[data_type] += 1
        return dict(counts)

    def _get_average_dimension(self) -> int:
        """Get average vector dimension"""
        if not self.vectors:
            return 0
        
        dimensions = [len(vector) for vector in self.vectors.values()]
        return int(np.mean(dimensions))

    def save_to_file(self, filepath: str) -> None:
        """Save database to file"""
        data = {
            "vectors": {k: v.tolist() for k, v in self.vectors.items()},
            "metadata": dict(self.metadata),
            "statistics": self.get_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: str) -> None:
        """Load database from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.vectors = {k: np.array(v) for k, v in data["vectors"].items()}
        self.metadata = data["metadata"]
