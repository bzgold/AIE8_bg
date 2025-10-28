"""
Advanced retrieval strategies from assignment 09
"""
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import re
from datetime import datetime

from langchain.retrievers import BM25Retriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.ensemble import EnsembleRetriever
from langchain.retrievers.parent_document import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

from services.vector_service import VectorService


class AdvancedRetrievalSystem:
    """Advanced retrieval system with multiple strategies from assignment 09"""
    
    def __init__(self, vector_service: VectorService = None):
        self.vector_service = vector_service or VectorService()
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Initialize retrievers
        self.bm25_retriever = None
        self.vector_retriever = None
        self.ensemble_retriever = None
        self.multi_query_retriever = None
        self.compression_retriever = None
        
        # Documents storage
        self.documents = []
        self.chunked_documents = []
    
    def setup_retrievers(self, documents: List[Document]):
        """Setup all retrieval strategies"""
        
        self.documents = documents
        
        # 1. BM25 Retriever
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 5
        
        # 2. Vector Retriever (using our vector service)
        self._setup_vector_retriever(documents)
        
        # 3. Multi-Query Retriever
        self._setup_multi_query_retriever()
        
        # 4. Ensemble Retriever
        self._setup_ensemble_retriever()
        
        # 5. Contextual Compression Retriever
        self._setup_compression_retriever()
    
    def _setup_vector_retriever(self, documents: List[Document]):
        """Setup vector-based retrieval"""
        # This would integrate with our existing vector service
        self.vector_retriever = self.vector_service
    
    def _setup_multi_query_retriever(self):
        """Setup multi-query retrieval"""
        if self.vector_retriever and self.llm:
            self.multi_query_retriever = MultiQueryRetriever.from_llm(
                retriever=self.vector_retriever,
                llm=self.llm
            )
    
    def _setup_ensemble_retriever(self):
        """Setup ensemble retrieval combining BM25 and vector"""
        if self.bm25_retriever and self.vector_retriever:
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.bm25_retriever, self.vector_retriever],
                weights=[0.5, 0.5]
            )
    
    def _setup_compression_retriever(self):
        """Setup contextual compression retriever"""
        if self.vector_retriever:
            # This would use a compressor like CohereRerank
            self.compression_retriever = self.vector_retriever  # Simplified for now
    
    def retrieve_documents(
        self,
        query: str,
        strategy: str = "ensemble",
        k: int = 5
    ) -> List[Document]:
        """Retrieve documents using specified strategy"""
        
        if strategy == "bm25":
            return self.bm25_retriever.get_relevant_documents(query) if self.bm25_retriever else []
        
        elif strategy == "vector":
            return self._vector_search(query, k)
        
        elif strategy == "multi_query":
            return self.multi_query_retriever.get_relevant_documents(query) if self.multi_query_retriever else []
        
        elif strategy == "ensemble":
            return self.ensemble_retriever.get_relevant_documents(query) if self.ensemble_retriever else []
        
        elif strategy == "compression":
            return self.compression_retriever.get_relevant_documents(query) if self.compression_retriever else []
        
        else:
            raise ValueError(f"Unknown retrieval strategy: {strategy}")
    
    def _vector_search(self, query: str, k: int) -> List[Document]:
        """Perform vector search using our vector service"""
        try:
            # Get query embedding
            query_embedding = self.vector_service.get_embedding(query)
            
            # Search in vector database
            results = self.vector_service.search_similar(
                query_embedding=query_embedding,
                top_k=k
            )
            
            # Convert to Document objects
            documents = []
            for result in results:
                doc = Document(
                    page_content=result.get("content", ""),
                    metadata=result.get("metadata", {})
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    def semantic_chunking(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        """Perform semantic chunking of text"""
        
        # Use recursive character text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_text(text)
        
        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "chunk_id": i,
                    "chunk_size": len(chunk),
                    "created_at": datetime.now().isoformat()
                }
            )
            documents.append(doc)
        
        self.chunked_documents = documents
        return documents
    
    def parent_document_retrieval(self, parent_documents: List[Document]) -> ParentDocumentRetriever:
        """Setup parent document retrieval"""
        
        # Create child splitter
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
        
        # Create parent document retriever
        retriever = ParentDocumentRetriever(
            parent_splitter=RecursiveCharacterTextSplitter(chunk_size=2000),
            child_splitter=child_splitter,
            docstore=self._create_docstore(parent_documents),
            child_vectorstore=self.vector_service,
            search_kwargs={"k": 5}
        )
        
        return retriever
    
    def _create_docstore(self, documents: List[Document]) -> Dict[str, Document]:
        """Create a simple docstore for parent documents"""
        docstore = {}
        for i, doc in enumerate(documents):
            docstore[str(i)] = doc
        return docstore
    
    def evaluate_retrieval_strategies(
        self,
        queries: List[str],
        ground_truth: List[List[str]]
    ) -> Dict[str, Dict[str, float]]:
        """Evaluate different retrieval strategies"""
        
        strategies = ["bm25", "vector", "ensemble", "multi_query"]
        results = {}
        
        for strategy in strategies:
            strategy_results = {
                "precision": [],
                "recall": [],
                "f1": []
            }
            
            for i, query in enumerate(queries):
                # Retrieve documents
                retrieved_docs = self.retrieve_documents(query, strategy, k=5)
                retrieved_texts = [doc.page_content for doc in retrieved_docs]
                
                # Calculate metrics
                precision = self._calculate_precision(retrieved_texts, ground_truth[i])
                recall = self._calculate_recall(retrieved_texts, ground_truth[i])
                f1 = self._calculate_f1(precision, recall)
                
                strategy_results["precision"].append(precision)
                strategy_results["recall"].append(recall)
                strategy_results["f1"].append(f1)
            
            # Calculate averages
            results[strategy] = {
                "avg_precision": np.mean(strategy_results["precision"]),
                "avg_recall": np.mean(strategy_results["recall"]),
                "avg_f1": np.mean(strategy_results["f1"])
            }
        
        return results
    
    def _calculate_precision(self, retrieved: List[str], relevant: List[str]) -> float:
        """Calculate precision for retrieval results"""
        if not retrieved:
            return 0.0
        
        relevant_set = set(relevant)
        retrieved_set = set(retrieved)
        
        intersection = len(relevant_set.intersection(retrieved_set))
        return intersection / len(retrieved_set)
    
    def _calculate_recall(self, retrieved: List[str], relevant: List[str]) -> float:
        """Calculate recall for retrieval results"""
        if not relevant:
            return 0.0
        
        relevant_set = set(relevant)
        retrieved_set = set(retrieved)
        
        intersection = len(relevant_set.intersection(retrieved_set))
        return intersection / len(relevant_set)
    
    def _calculate_f1(self, precision: float, recall: float) -> float:
        """Calculate F1 score"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def get_retrieval_insights(self, query: str, strategy: str = "ensemble") -> Dict[str, Any]:
        """Get insights about retrieval performance"""
        
        retrieved_docs = self.retrieve_documents(query, strategy)
        
        insights = {
            "query": query,
            "strategy": strategy,
            "num_documents": len(retrieved_docs),
            "avg_document_length": np.mean([len(doc.page_content) for doc in retrieved_docs]) if retrieved_docs else 0,
            "document_types": self._classify_document_types(retrieved_docs),
            "key_topics": self._extract_key_topics(retrieved_docs),
            "retrieval_confidence": self._calculate_retrieval_confidence(retrieved_docs)
        }
        
        return insights
    
    def _classify_document_types(self, documents: List[Document]) -> Dict[str, int]:
        """Classify document types in retrieval results"""
        types = []
        
        for doc in documents:
            content = doc.page_content.lower()
            if any(word in content for word in ["incident", "accident", "crash"]):
                types.append("incident")
            elif any(word in content for word in ["construction", "maintenance"]):
                types.append("construction")
            elif any(word in content for word in ["weather", "rain", "snow"]):
                types.append("weather")
            else:
                types.append("general")
        
        return Counter(types)
    
    def _extract_key_topics(self, documents: List[Document]) -> List[str]:
        """Extract key topics from retrieved documents"""
        all_text = " ".join([doc.page_content for doc in documents])
        
        # Simple keyword extraction
        traffic_keywords = [
            "congestion", "delay", "incident", "accident", "crash", "breakdown",
            "construction", "closure", "detour", "jam", "backup", "bottleneck",
            "speed", "volume", "occupancy", "flow", "density", "reliability"
        ]
        
        found_topics = []
        for keyword in traffic_keywords:
            if keyword in all_text.lower():
                found_topics.append(keyword)
        
        return found_topics[:10]  # Return top 10 topics
    
    def _calculate_retrieval_confidence(self, documents: List[Document]) -> float:
        """Calculate confidence score for retrieval results"""
        if not documents:
            return 0.0
        
        # Simple confidence based on document count and average length
        doc_count_score = min(len(documents) / 5, 1.0)  # Normalize to 0-1
        avg_length = np.mean([len(doc.page_content) for doc in documents])
        length_score = min(avg_length / 500, 1.0)  # Normalize to 0-1
        
        return (doc_count_score + length_score) / 2
