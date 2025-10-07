"""
Test script for LangGraph Synthetic Data Generation
=================================================

This script demonstrates how to use the LangGraph-based synthetic data generator
with real documents from the data folder.
"""

import asyncio
import os
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langgraph_synthetic_data_generation import LangGraphSyntheticDataGenerator


async def test_with_pdf_documents():
    """Test the synthetic data generator with PDF documents."""
    
    print("🧪 Testing LangGraph Synthetic Data Generation with PDF documents...")
    
    # Load documents from the data folder
    try:
        path = "data/"
        loader = DirectoryLoader(path, glob="*.pdf", loader_cls=PyMuPDFLoader)
        docs = loader.load()
        
        print(f"📚 Loaded {len(docs)} documents")
        
        # Display document info
        for i, doc in enumerate(docs):
            print(f"  {i+1}. {doc.metadata.get('source', 'Unknown')} - {len(doc.page_content)} chars")
        
        if not docs:
            print("❌ No documents found. Please ensure PDF files are in the 'data/' folder.")
            return
        
        # Initialize the generator
        print("\n🚀 Initializing LangGraph Synthetic Data Generator...")
        generator = LangGraphSyntheticDataGenerator(
            llm_model="gpt-4o-mini",
            embedding_model="text-embedding-3-small",
            temperature=0.7
        )
        
        # Generate synthetic data
        print("\n🎯 Starting synthetic data generation...")
        result = await generator.generate_synthetic_data(docs)
        
        # Display results
        print("\n" + "="*80)
        print("🎉 SYNTHETIC DATA GENERATION COMPLETED!")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"Total Questions Generated: {result['summary']['total_questions']}")
        print(f"Evolution Types: {result['summary']['evolution_types']}")
        
        print(f"\n🔍 EVOLVED QUESTIONS BY TYPE:")
        
        # Group questions by evolution type
        by_type = {}
        for q in result['evolved_questions']:
            if q['evolution_type'] not in by_type:
                by_type[q['evolution_type']] = []
            by_type[q['evolution_type']].append(q)
        
        for evolution_type, questions in by_type.items():
            print(f"\n📝 {evolution_type.upper()} EVOLUTION ({len(questions)} questions):")
            for i, q in enumerate(questions[:3]):  # Show first 3 of each type
                print(f"  {i+1}. {q['question']}")
                if q.get('original_question'):
                    print(f"     Original: {q['original_question']}")
                print(f"     Difficulty: {q['difficulty_level']}/5")
        
        print(f"\n💡 SAMPLE ANSWERS:")
        for i, a in enumerate(result['question_answers'][:5]):
            # Find the corresponding question
            question = next((q for q in result['evolved_questions'] if q['id'] == a['question_id']), None)
            if question:
                print(f"{i+1}. Q: {question['question'][:80]}...")
                print(f"   A: {a['answer'][:150]}...")
                print(f"   Confidence: {a['confidence_score']:.2f}")
                print()
        
        print(f"\n🎯 CONTEXT SELECTION:")
        for i, c in enumerate(result['question_contexts'][:3]):
            question = next((q for q in result['evolved_questions'] if q['id'] == c['question_id']), None)
            if question:
                print(f"{i+1}. Q: {question['question'][:60]}...")
                print(f"   Contexts: {len(c['contexts'])} selected")
                if c['relevance_scores']:
                    print(f"   Avg Relevance: {sum(c['relevance_scores'])/len(c['relevance_scores']):.2f}")
                print()
        
        # Save results
        import json
        with open("langgraph_synthetic_data_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Full results saved to 'langgraph_synthetic_data_results.json'")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_with_sample_documents():
    """Test with sample documents if PDF loading fails."""
    
    print("\n🧪 Testing with sample documents...")
    
    # Create sample documents
    sample_docs = [
        Document(
            page_content="Artificial Intelligence is revolutionizing healthcare through diagnostic imaging, drug discovery, and personalized treatment plans. Machine learning algorithms can analyze medical images with accuracy comparable to human radiologists.",
            metadata={"source": "healthcare_ai.txt", "topic": "healthcare"}
        ),
        Document(
            page_content="The financial services industry has adopted AI for fraud detection, algorithmic trading, and risk assessment. Banks use machine learning to identify suspicious transactions and prevent financial crimes.",
            metadata={"source": "finance_ai.txt", "topic": "finance"}
        ),
        Document(
            page_content="Autonomous vehicles rely on AI for navigation, obstacle detection, and decision-making. Companies like Tesla, Waymo, and Cruise are developing self-driving cars that could transform transportation.",
            metadata={"source": "autonomous_vehicles.txt", "topic": "transportation"}
        )
    ]
    
    # Initialize generator
    generator = LangGraphSyntheticDataGenerator()
    
    # Generate synthetic data
    result = await generator.generate_synthetic_data(sample_docs)
    
    print("✅ Sample test completed successfully!")
    return result


async def main():
    """Main test function."""
    
    # Check for API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set your OPENAI_API_KEY environment variable")
        return
    
    print("🎯 LangGraph Synthetic Data Generation Test Suite")
    print("=" * 50)
    
    # Try with PDF documents first
    result = await test_with_pdf_documents()
    
    # If PDF test fails, try with sample documents
    if result is None:
        print("\n🔄 PDF test failed, trying with sample documents...")
        result = await test_with_sample_documents()
    
    if result:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Tests failed. Please check your setup and API keys.")


if __name__ == "__main__":
    asyncio.run(main())
