#!/usr/bin/env python3
"""
Advanced RAG Evaluation Script with Semantic Chunking
====================================================

This script implements the advanced build requirements:
1. Baseline LangGraph RAG Application using NAIVE RETRIEVAL
2. Baseline Evaluation using RAGAS METRICS
3. SEMANTIC CHUNKING STRATEGY implementation
4. LangGraph RAG Application using SEMANTIC CHUNKING with NAIVE RETRIEVAL
5. Compare and contrast results

Requirements:
- Faithfulness, Answer Relevancy, Context Precision, Context Recall, Answer Correctness
- Semantic chunking with similarity threshold
- Greedy chunking up to maximum chunk size
- Minimum chunk size of single sentence
"""

import os
import json
import time
import copy
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# LangChain imports
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# LangGraph imports
from langgraph.graph import START, StateGraph
from typing_extensions import TypedDict, List as TypedList

# Ragas imports
from ragas import evaluate, EvaluationDataset
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy, 
    ContextPrecision,
    ContextRecall,
    AnswerCorrectness
)
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator
from ragas.embeddings import LangchainEmbeddingsWrapper

# Semantic chunking imports
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import re


@dataclass
class ChunkingConfig:
    """Configuration for semantic chunking"""
    similarity_threshold: float = 0.7
    max_chunk_size: int = 1000
    min_chunk_size: int = 50
    model_name: str = "all-MiniLM-L6-v2"


class SemanticChunker:
    """
    Semantic chunking strategy that groups semantically similar sentences
    and paragraphs greedily up to a maximum chunk size.
    """
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.sentence_model = SentenceTransformer(config.model_name)
        nltk.download('punkt', quiet=True)
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk documents using semantic similarity"""
        all_chunks = []
        
        for doc in documents:
            chunks = self._chunk_document(doc)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _chunk_document(self, document: Document) -> List[Document]:
        """Chunk a single document semantically"""
        text = document.page_content
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 1:
            return [document]
        
        # Get sentence embeddings
        sentence_embeddings = self.sentence_model.encode(sentences)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence.split())
            
            # If adding this sentence would exceed max size, finalize current chunk
            if current_size + sentence_size > self.config.max_chunk_size and current_chunk:
                chunks.append(self._create_chunk(current_chunk, document.metadata))
                current_chunk = [sentence]
                current_size = sentence_size
                continue
            
            # If this is the first sentence, add it
            if not current_chunk:
                current_chunk.append(sentence)
                current_size = sentence_size
                continue
            
            # Calculate similarity with last sentence in current chunk
            if len(current_chunk) > 0:
                last_sentence_idx = len(current_chunk) - 1
                # Find the index of the last sentence in the original sentences
                last_sentence_text = current_chunk[-1]
                try:
                    last_sentence_original_idx = sentences.index(last_sentence_text)
                    similarity = cosine_similarity(
                        sentence_embeddings[i].reshape(1, -1),
                        sentence_embeddings[last_sentence_original_idx].reshape(1, -1)
                    )[0][0]
                except ValueError:
                    similarity = 0.0
            else:
                similarity = 1.0
            
            # If similarity is above threshold, add to current chunk
            if similarity >= self.config.similarity_threshold:
                current_chunk.append(sentence)
                current_size += sentence_size
            else:
                # Finalize current chunk and start new one
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, document.metadata))
                current_chunk = [sentence]
                current_size = sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, document.metadata))
        
        return chunks
    
    def _create_chunk(self, sentences: List[str], metadata: Dict[str, Any]) -> Document:
        """Create a Document from a list of sentences"""
        content = " ".join(sentences)
        return Document(page_content=content, metadata=metadata)


class RAGState(TypedDict):
    """State for RAG application"""
    question: str
    context: TypedList[Document]
    response: str


class RAGEvaluator:
    """RAG evaluation using Ragas metrics"""
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.llm = LangchainLLMWrapper(ChatOpenAI(model=llm_model))
        self.metrics = [
            Faithfulness(),
            AnswerRelevancy(),
            ContextPrecision(),
            ContextRecall(),
            AnswerCorrectness()
        ]
    
    def evaluate_rag_system(self, dataset: EvaluationDataset) -> Dict[str, float]:
        """Evaluate RAG system using Ragas metrics"""
        print("Evaluating RAG system with Ragas metrics...")
        
        result = evaluate(
            dataset=dataset,
            metrics=self.metrics,
            llm=self.llm
        )
        
        return result


class BaselineRAGSystem:
    """Baseline RAG system with naive retrieval"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        self.vector_store = None
        self.retriever = None
        self.graph = None
        self._setup_rag_prompt()
    
    def _setup_rag_prompt(self):
        """Setup RAG prompt template"""
        self.rag_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant who answers questions based on provided context. 
You must only use the provided context, and cannot use your own knowledge.

### Question
{question}

### Context
{context}
""")
    
    def load_and_chunk_documents(self, data_path: str) -> List[Document]:
        """Load and chunk documents using naive chunking"""
        print(f"Loading documents from {data_path}...")
        
        loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyMuPDFLoader)
        docs = loader.load()
        
        print(f"Loaded {len(docs)} documents")
        
        # Naive chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        split_documents = text_splitter.split_documents(docs)
        
        print(f"Created {len(split_documents)} chunks with naive chunking")
        return split_documents
    
    def setup_vector_store(self, documents: List[Document]):
        """Setup vector store with documents"""
        print("Setting up vector store...")
        
        client = QdrantClient(":memory:")
        client.create_collection(
            collection_name="rag_data",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        
        self.vector_store = QdrantVectorStore(
            client=client,
            collection_name="rag_data",
            embedding=self.embeddings,
        )
        
        self.vector_store.add_documents(documents)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        print("Vector store setup complete")
    
    def retrieve(self, state: RAGState) -> RAGState:
        """Retrieve relevant documents"""
        retrieved_docs = self.retriever.invoke(state["question"])
        return {"context": retrieved_docs}
    
    def generate(self, state: RAGState) -> RAGState:
        """Generate response using retrieved context"""
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        messages = self.rag_prompt.format_messages(
            question=state["question"], 
            context=docs_content
        )
        response = self.llm.invoke(messages)
        return {"response": response.content}
    
    def build_graph(self):
        """Build LangGraph RAG graph"""
        print("Building LangGraph RAG graph...")
        
        graph_builder = StateGraph(RAGState)
        graph_builder.add_sequence([self.retrieve, self.generate])
        graph_builder.add_edge(START, "retrieve")
        self.graph = graph_builder.compile()
        print("Graph built successfully")
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system"""
        return self.graph.invoke({"question": question})


class SemanticRAGSystem(BaselineRAGSystem):
    """RAG system with semantic chunking"""
    
    def __init__(self, chunking_config: ChunkingConfig, chunk_size: int = 500, chunk_overlap: int = 50):
        super().__init__(chunk_size, chunk_overlap)
        self.chunking_config = chunking_config
        self.semantic_chunker = SemanticChunker(chunking_config)
    
    def load_and_chunk_documents(self, data_path: str) -> List[Document]:
        """Load and chunk documents using semantic chunking"""
        print(f"Loading documents from {data_path}...")
        
        loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyMuPDFLoader)
        docs = loader.load()
        
        print(f"Loaded {len(docs)} documents")
        
        # Semantic chunking
        split_documents = self.semantic_chunker.chunk_documents(docs)
        
        print(f"Created {len(split_documents)} chunks with semantic chunking")
        return split_documents


class RAGComparison:
    """Compare different RAG approaches"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.evaluator = RAGEvaluator()
        self.test_dataset = None
    
    def generate_test_dataset(self, documents: List[Document], test_size: int = 10):
        """Generate synthetic test dataset using Ragas"""
        print("Generating synthetic test dataset...")
        
        generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
        generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
        
        generator = TestsetGenerator(
            llm=generator_llm, 
            embedding_model=generator_embeddings
        )
        
        self.test_dataset = generator.generate_with_langchain_docs(
            documents, 
            testset_size=test_size
        )
        
        print(f"Generated {len(self.test_dataset)} test samples")
        return self.test_dataset
    
    def evaluate_system(self, rag_system: BaselineRAGSystem, system_name: str) -> Dict[str, float]:
        """Evaluate a RAG system"""
        print(f"\nEvaluating {system_name}...")
        
        # Run queries through the system
        for test_row in self.test_dataset:
            response = rag_system.query(test_row.eval_sample.user_input)
            test_row.eval_sample.response = response["response"]
            test_row.eval_sample.retrieved_contexts = [
                context.page_content for context in response["context"]
            ]
        
        # Convert to evaluation dataset
        evaluation_dataset = EvaluationDataset.from_pandas(self.test_dataset.to_pandas())
        
        # Evaluate
        results = self.evaluator.evaluate_rag_system(evaluation_dataset)
        
        print(f"{system_name} evaluation complete")
        return results
    
    def compare_systems(self, baseline_results: Dict[str, float], 
                       semantic_results: Dict[str, float]) -> pd.DataFrame:
        """Compare results between systems"""
        comparison_data = {
            'Metric': list(baseline_results.keys()),
            'Baseline (Naive Chunking)': list(baseline_results.values()),
            'Semantic Chunking': list(semantic_results.values())
        }
        
        df = pd.DataFrame(comparison_data)
        
        # Calculate improvement
        df['Improvement'] = df['Semantic Chunking'] - df['Baseline (Naive Chunking)']
        df['Improvement %'] = (df['Improvement'] / df['Baseline (Naive Chunking)'] * 100).round(2)
        
        return df


def main():
    """Main execution function"""
    print("🚧 Advanced RAG Evaluation with Semantic Chunking 🚧")
    print("=" * 60)
    
    # Configuration
    data_path = "data/"
    chunking_config = ChunkingConfig(
        similarity_threshold=0.7,
        max_chunk_size=1000,
        min_chunk_size=50
    )
    
    # Initialize comparison system
    comparison = RAGComparison(data_path)
    
    # Load documents for test dataset generation
    loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyMuPDFLoader)
    docs = loader.load()
    
    # Generate test dataset
    test_dataset = comparison.generate_test_dataset(docs, test_size=10)
    
    print("\n" + "="*60)
    print("1. BASELINE RAG SYSTEM (Naive Chunking)")
    print("="*60)
    
    # Baseline RAG system
    baseline_rag = BaselineRAGSystem(chunk_size=500, chunk_overlap=50)
    baseline_docs = baseline_rag.load_and_chunk_documents(data_path)
    baseline_rag.setup_vector_store(baseline_docs)
    baseline_rag.build_graph()
    
    # Test baseline system
    test_question = "What are the different kinds of loans?"
    baseline_response = baseline_rag.query(test_question)
    print(f"Test question: {test_question}")
    print(f"Baseline response: {baseline_response['response'][:200]}...")
    
    # Evaluate baseline
    baseline_results = comparison.evaluate_system(baseline_rag, "Baseline RAG")
    
    print("\n" + "="*60)
    print("2. SEMANTIC CHUNKING RAG SYSTEM")
    print("="*60)
    
    # Semantic RAG system
    semantic_rag = SemanticRAGSystem(chunking_config, chunk_size=500, chunk_overlap=50)
    semantic_docs = semantic_rag.load_and_chunk_documents(data_path)
    semantic_rag.setup_vector_store(semantic_docs)
    semantic_rag.build_graph()
    
    # Test semantic system
    semantic_response = semantic_rag.query(test_question)
    print(f"Test question: {test_question}")
    print(f"Semantic response: {semantic_response['response'][:200]}...")
    
    # Evaluate semantic system
    semantic_results = comparison.evaluate_system(semantic_rag, "Semantic RAG")
    
    print("\n" + "="*60)
    print("3. COMPARISON AND ANALYSIS")
    print("="*60)
    
    # Compare results
    comparison_df = comparison.compare_systems(baseline_results, semantic_results)
    
    print("\nDetailed Comparison:")
    print(comparison_df.to_string(index=False))
    
    print("\n" + "="*60)
    print("4. ANALYSIS SUMMARY")
    print("="*60)
    
    # Analysis
    print(f"\nChunk Count Comparison:")
    print(f"Baseline (Naive): {len(baseline_docs)} chunks")
    print(f"Semantic Chunking: {len(semantic_docs)} chunks")
    print(f"Difference: {len(semantic_docs) - len(baseline_docs)} chunks")
    
    print(f"\nPerformance Analysis:")
    for metric in baseline_results.keys():
        baseline_score = baseline_results[metric]
        semantic_score = semantic_results[metric]
        improvement = semantic_score - baseline_score
        improvement_pct = (improvement / baseline_score * 100) if baseline_score > 0 else 0
        
        print(f"{metric}:")
        print(f"  Baseline: {baseline_score:.3f}")
        print(f"  Semantic: {semantic_score:.3f}")
        print(f"  Improvement: {improvement:+.3f} ({improvement_pct:+.1f}%)")
        print()
    
    # Save results
    results = {
        'baseline_results': baseline_results,
        'semantic_results': semantic_results,
        'comparison_df': comparison_df.to_dict(),
        'chunk_counts': {
            'baseline': len(baseline_docs),
            'semantic': len(semantic_docs)
        }
    }
    
    with open('rag_evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to 'rag_evaluation_results.json'")
    print("\n🎉 Advanced RAG Evaluation Complete! 🎉")


if __name__ == "__main__":
    main()

