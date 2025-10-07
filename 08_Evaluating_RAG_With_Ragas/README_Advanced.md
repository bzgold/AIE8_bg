# Advanced RAG Evaluation with Semantic Chunking

This script implements the advanced build requirements for evaluating RAG systems with semantic chunking strategies.

## 🚧 Features

### ✅ MINIMUM REQUIREMENTS IMPLEMENTED

1. **Baseline LangGraph RAG Application** using NAIVE RETRIEVAL
2. **Baseline Evaluation** using RAGAS METRICS:
   - Faithfulness
   - Answer Relevancy  
   - Context Precision
   - Context Recall
   - Answer Correctness
3. **SEMANTIC CHUNKING STRATEGY** implementation
4. **LangGraph RAG Application** using SEMANTIC CHUNKING with NAIVE RETRIEVAL
5. **Compare and contrast results** between approaches

### 🧠 Semantic Chunking Requirements

- ✅ Chunk semantically similar sentences based on designed threshold
- ✅ Greedy chunking up to maximum chunk size
- ✅ Minimum chunk size is a single sentence
- ✅ Uses sentence transformers for semantic similarity
- ✅ Configurable similarity threshold (default: 0.7)

## 📋 Prerequisites

1. **API Keys Required:**
   - OpenAI API key for LLM and embeddings
   - Set environment variable: `OPENAI_API_KEY`

2. **Data:**
   - Place PDF documents in the `data/` directory
   - The script will automatically load all PDF files

## 🚀 Installation

1. **Install additional dependencies:**
   ```bash
   pip install -r requirements_advanced.txt
   ```

2. **Or install specific packages:**
   ```bash
   pip install sentence-transformers scikit-learn nltk
   ```

## 🏃‍♂️ Usage

### Basic Usage

```bash
python advanced_rag_evaluation.py
```

### Configuration

You can modify the chunking configuration in the script:

```python
chunking_config = ChunkingConfig(
    similarity_threshold=0.7,  # Semantic similarity threshold
    max_chunk_size=1000,       # Maximum chunk size in words
    min_chunk_size=50,         # Minimum chunk size in words
    model_name="all-MiniLM-L6-v2"  # Sentence transformer model
)
```

## 📊 What the Script Does

### 1. Data Loading and Preparation
- Loads PDF documents from `data/` directory
- Generates synthetic test dataset using Ragas
- Creates 10 test questions for evaluation

### 2. Baseline RAG System (Naive Chunking)
- Uses `RecursiveCharacterTextSplitter` with fixed chunk sizes
- Implements LangGraph RAG pipeline
- Evaluates with all 5 Ragas metrics

### 3. Semantic Chunking RAG System
- Implements custom semantic chunking strategy
- Groups semantically similar sentences together
- Uses sentence transformers for similarity calculation
- Maintains same RAG pipeline structure

### 4. Comprehensive Evaluation
- Runs both systems on identical test dataset
- Compares performance across all metrics
- Provides detailed analysis and improvement percentages

## 🔧 Technical Implementation

### Semantic Chunking Algorithm

1. **Sentence Segmentation:** Uses NLTK to split text into sentences
2. **Embedding Generation:** Creates embeddings for each sentence using sentence transformers
3. **Similarity Calculation:** Computes cosine similarity between consecutive sentences
4. **Greedy Grouping:** Groups sentences above similarity threshold
5. **Size Constraints:** Respects minimum and maximum chunk size limits

### RAG Pipeline

```python
# LangGraph State
class RAGState(TypedDict):
    question: str
    context: List[Document]
    response: str

# Pipeline: Question → Retrieve → Generate → Response
```

### Evaluation Metrics

- **Faithfulness:** Measures if the answer is grounded in the retrieved context
- **Answer Relevancy:** Measures how relevant the answer is to the question
- **Context Precision:** Measures how much of the retrieved context is relevant
- **Context Recall:** Measures how much of the relevant context was retrieved
- **Answer Correctness:** Measures factual accuracy of the answer

## 📈 Output and Results

The script provides:

1. **Real-time Progress:** Console output showing each step
2. **Detailed Comparison:** Side-by-side metric comparison
3. **Performance Analysis:** Improvement percentages for each metric
4. **Chunk Statistics:** Comparison of chunk counts between approaches
5. **JSON Results:** Saved results in `rag_evaluation_results.json`

### Sample Output

```
🚧 Advanced RAG Evaluation with Semantic Chunking 🚧
============================================================

1. BASELINE RAG SYSTEM (Naive Chunking)
============================================================
Loading documents from data/...
Loaded 1 documents
Created 45 chunks with naive chunking
Setting up vector store...
Vector store setup complete
Building LangGraph RAG graph...
Graph built successfully

2. SEMANTIC CHUNKING RAG SYSTEM
============================================================
Loading documents from data/...
Loaded 1 documents
Created 38 chunks with semantic chunking
Setting up vector store...
Vector store setup complete
Building LangGraph RAG graph...
Graph built successfully

3. COMPARISON AND ANALYSIS
============================================================

Detailed Comparison:
                Metric  Baseline (Naive Chunking)  Semantic Chunking  Improvement  Improvement %
0         faithfulness                        0.85               0.92         0.07           8.24
1      answer_relevancy                       0.78               0.84         0.06           7.69
2    context_precision                        0.72               0.79         0.07           9.72
3       context_recall                        0.68               0.75         0.07          10.29
4  answer_correctness                         0.81               0.88         0.07           8.64

4. ANALYSIS SUMMARY
============================================================

Chunk Count Comparison:
Baseline (Naive): 45 chunks
Semantic Chunking: 38 chunks
Difference: -7 chunks

Performance Analysis:
faithfulness:
  Baseline: 0.850
  Semantic: 0.920
  Improvement: +0.070 (+8.2%)

answer_relevancy:
  Baseline: 0.780
  Semantic: 0.840
  Improvement: +0.060 (+7.7%)

context_precision:
  Baseline: 0.720
  Semantic: 0.790
  Improvement: +0.070 (+9.7%)

context_recall:
  Baseline: 0.680
  Semantic: 0.750
  Improvement: +0.070 (+10.3%)

answer_correctness:
  Baseline: 0.810
  Semantic: 0.880
  Improvement: +0.070 (+8.6%)

Results saved to 'rag_evaluation_results.json'
🎉 Advanced RAG Evaluation Complete! 🎉
```

## 🎯 Key Benefits of Semantic Chunking

1. **Better Context Preservation:** Related sentences stay together
2. **Improved Retrieval Quality:** More coherent chunks for retrieval
3. **Enhanced Answer Quality:** Better context leads to better answers
4. **Reduced Chunk Count:** Fewer, more meaningful chunks
5. **Semantic Coherence:** Chunks maintain semantic meaning

## 🔍 Troubleshooting

### Common Issues

1. **Missing API Key:**
   ```
   Error: OpenAI API key not found
   Solution: Set OPENAI_API_KEY environment variable
   ```

2. **Missing Dependencies:**
   ```
   ModuleNotFoundError: No module named 'sentence_transformers'
   Solution: pip install -r requirements_advanced.txt
   ```

3. **NLTK Data Missing:**
   ```
   LookupError: Resource punkt not found
   Solution: The script automatically downloads NLTK data
   ```

### Performance Tips

1. **Adjust Similarity Threshold:** Lower values (0.5-0.6) create more chunks, higher values (0.8-0.9) create fewer chunks
2. **Modify Chunk Sizes:** Adjust `max_chunk_size` based on your content
3. **Model Selection:** Use faster models like `all-MiniLM-L6-v2` for speed, or larger models for accuracy

## 📚 Further Reading

- [Ragas Documentation](https://docs.ragas.io/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Sentence Transformers](https://www.sbert.net/)
- [Semantic Chunking Strategies](https://docs.llamaindex.ai/en/stable/module_guides/processing/node_parsers/semantic_chunker/)

## 🤝 Contributing

Feel free to extend this script with:
- Different chunking strategies
- Additional evaluation metrics
- Different embedding models
- Advanced retrieval techniques

