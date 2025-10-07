# LangGraph Synthetic Data Generation with Evol Instruct

This implementation provides a sophisticated alternative to RAGAS Knowledge Graph-based synthetic data generation using LangGraph with the Evol Instruct method.

## 🚀 Features

### Evolution Types
- **Simple Evolution**: Basic question generation and evolution
- **Multi-Context Evolution**: Questions requiring multiple document contexts
- **Reasoning Evolution**: Complex questions requiring logical reasoning

### Output Structure
- **Evolved Questions**: List of questions with IDs and evolution types
- **Question Answers**: Comprehensive answers with confidence scores
- **Question Contexts**: Relevant contexts with relevance scores

### LangGraph Workflow
- **Stateful Processing**: Maintains context throughout the generation process
- **Asynchronous Execution**: Efficient parallel processing
- **Modular Design**: Easy to extend and customize

## 📋 Requirements

Install the required dependencies:

```bash
pip install -r requirements_sdg.txt
```

## 🔧 Setup

1. **Set Environment Variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

2. **Prepare Documents**: Place your PDF files in the `data/` folder

## 🎯 Usage

### Basic Usage

```python
import asyncio
from langchain_core.documents import Document
from langgraph_synthetic_data_generation import LangGraphSyntheticDataGenerator

# Initialize the generator
generator = LangGraphSyntheticDataGenerator(
    llm_model="gpt-4o-mini",
    embedding_model="text-embedding-3-small",
    temperature=0.7
)

# Your documents
documents = [
    Document(page_content="Your document content...", metadata={"source": "doc1.txt"}),
    # ... more documents
]

# Generate synthetic data
result = await generator.generate_synthetic_data(documents)

# Access results
evolved_questions = result['evolved_questions']
question_answers = result['question_answers']
question_contexts = result['question_contexts']
```

### Running the Test Script

```bash
python test_sdg.py
```

## 📊 Output Structure

### Evolved Questions
```json
{
  "id": "unique-question-id",
  "question": "evolved question text",
  "evolution_type": "simple|multi_context|reasoning",
  "original_question": "original question (if applicable)",
  "difficulty_level": 1-5,
  "evolution_prompt": "explanation of evolution"
}
```

### Question Answers
```json
{
  "question_id": "corresponding-question-id",
  "answer": "comprehensive answer",
  "confidence_score": 0.0-1.0,
  "source_citations": ["source1", "source2"]
}
```

### Question Contexts
```json
{
  "question_id": "corresponding-question-id",
  "contexts": ["relevant context 1", "relevant context 2"],
  "relevance_scores": [0.9, 0.8],
  "source_documents": ["doc1.txt", "doc2.txt"]
}
```

## 🔄 Workflow Process

The LangGraph workflow follows these steps:

1. **Initialize**: Set up the generation process and create initial questions
2. **Simple Evolution**: Evolve basic questions using simple transformation
3. **Multi-Context Evolution**: Create questions requiring multiple contexts
4. **Reasoning Evolution**: Generate questions requiring logical reasoning
5. **Generate Answers**: Create comprehensive answers for all questions
6. **Select Contexts**: Identify relevant contexts for each question
7. **Finalize**: Compile and format the final results

## 🎨 Customization

### Custom Evolution Prompts

You can customize the evolution prompts by modifying the prompt templates in the `_setup_prompts()` method:

```python
# Custom simple evolution prompt
self.simple_evolution_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="Your custom evolution instructions..."),
    HumanMessage(content="Original Question: {original_question}\nContext: {context}")
])
```

### Adding New Evolution Types

To add new evolution types:

1. Add the new type to the `EvolutionType` enum
2. Create a new prompt template
3. Add a new node to the LangGraph workflow
4. Update the workflow edges

### Custom Context Selection

Modify the `_get_relevant_context()` method to implement custom context selection logic:

```python
async def _get_relevant_context(self, question: str, documents: List[Document]) -> str:
    # Your custom context selection logic
    # e.g., embedding-based similarity, keyword matching, etc.
    pass
```

## 🔍 Comparison with RAGAS Knowledge Graph

| Aspect | RAGAS Knowledge Graph | LangGraph Evol Instruct |
|--------|----------------------|-------------------------|
| **Approach** | Graph-based clustering | Sequential evolution |
| **Flexibility** | Fixed transformations | Customizable prompts |
| **Scalability** | Limited by graph size | Scales with documents |
| **Control** | Limited control | Full control over process |
| **Complexity** | High (graph management) | Medium (workflow design) |
| **Customization** | Limited | Highly customizable |

## 🚨 Troubleshooting

### Common Issues

1. **API Key Not Set**:
   ```
   ❌ Please set your OPENAI_API_KEY environment variable
   ```
   Solution: Set the environment variable or pass it directly to the LLM

2. **No Documents Found**:
   ```
   ❌ No documents found. Please ensure PDF files are in the 'data/' folder.
   ```
   Solution: Check that PDF files exist in the `data/` folder

3. **Memory Issues**:
   - Reduce the number of documents
   - Use smaller chunk sizes
   - Process documents in batches

### Performance Optimization

1. **Use Smaller Models**: Use `gpt-3.5-turbo` instead of `gpt-4o-mini` for faster generation
2. **Batch Processing**: Process documents in smaller batches
3. **Caching**: Implement caching for repeated operations

## 📈 Advanced Features

### Embedding-Based Context Selection

```python
async def _get_relevant_context_embedding(self, question: str, documents: List[Document]) -> str:
    """Enhanced context selection using embeddings."""
    question_embedding = await self.embeddings.aembed_query(question)
    
    similarities = []
    for doc in documents:
        doc_embedding = await self.embeddings.aembed_query(doc.page_content)
        similarity = cosine_similarity([question_embedding], [doc_embedding])[0][0]
        similarities.append((similarity, doc))
    
    # Return the most similar document
    best_match = max(similarities, key=lambda x: x[0])
    return best_match[1].page_content
```

### Custom Difficulty Scoring

```python
def calculate_difficulty_score(self, question: str, context: str) -> int:
    """Calculate question difficulty based on various factors."""
    factors = {
        'length': len(question.split()),
        'complexity': len([w for w in question.split() if len(w) > 8]),
        'reasoning_indicators': len([w for w in question.lower().split() 
                                   if w in ['why', 'how', 'analyze', 'compare', 'evaluate']])
    }
    
    # Calculate weighted score
    score = (factors['length'] * 0.3 + 
             factors['complexity'] * 0.4 + 
             factors['reasoning_indicators'] * 0.3)
    
    return min(5, max(1, int(score / 10)))
```

## 🤝 Contributing

To contribute to this implementation:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

## 📄 License

This implementation is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

- Inspired by RAGAS synthetic data generation
- Built with LangGraph for workflow management
- Uses Evol Instruct method for question evolution

