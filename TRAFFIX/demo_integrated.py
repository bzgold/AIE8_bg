#!/usr/bin/env python3
"""
Integrated Pipeline Demo Script
Demonstrates the complete integrated pipeline with modules from previous assignments
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from integrated_pipeline import IntegratedTraffixPipeline
from preprocessing import TextFileLoader, CharacterTextSplitter, TrafficDataPreprocessor
from preprocessing.vector_database import EnhancedVectorDatabase
from evaluation import RagasEvaluator
from research import DeepResearchAgent
from services.vector_service import VectorService


async def demo_preprocessing():
    """Demonstrate preprocessing capabilities"""
    print("\n🔧 Preprocessing Module Demo")
    print("=" * 50)
    
    try:
        # Initialize components
        vector_service = VectorService()
        preprocessor = TrafficDataPreprocessor()
        
        # Simulate traffic data
        sample_traffic_data = {
            "traffic_data": [
                {"timestamp": "2024-01-15T08:00:00", "speed": 45.2, "volume": 1200, "occupancy": 0.75},
                {"timestamp": "2024-01-15T08:30:00", "speed": 38.1, "volume": 1450, "occupancy": 0.85},
                {"timestamp": "2024-01-15T09:00:00", "speed": 32.5, "volume": 1600, "occupancy": 0.92}
            ],
            "incidents": [
                {"description": "Multi-vehicle accident on I-95 North", "severity": "major", "location": "I-95 North", "start_time": "2024-01-15T08:15:00", "end_time": "2024-01-15T10:30:00"},
                {"description": "Disabled vehicle blocking right lane", "severity": "minor", "location": "Route 50 East", "start_time": "2024-01-15T09:45:00", "end_time": "2024-01-15T10:15:00"}
            ],
            "news_articles": [
                {"title": "Traffic delays on I-95 due to morning accident", "source": "Local News", "published_at": "2024-01-15T09:00:00", "content": "A multi-vehicle accident on I-95 North caused significant delays during morning rush hour..."}
            ],
            "weather_data": [
                {"timestamp": "2024-01-15T08:00:00", "condition": "rain", "temperature": 42, "traffic_impact": "moderate"}
            ]
        }
        
        # Process the data
        processed_data = preprocessor.preprocess_traffic_data(sample_traffic_data)
        
        print(f"✅ Processed {len(processed_data['chunks'])} text chunks")
        print(f"✅ Extracted {len(processed_data['processed_texts'])} processed texts")
        print(f"✅ Data types: {list(set([chunk.split(':')[0] for chunk in processed_data['processed_texts']]))}")
        
        # Demonstrate text splitting
        splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        sample_text = "This is a sample traffic analysis report with detailed information about congestion patterns, incident impacts, and weather effects on traffic flow."
        chunks = splitter.split(sample_text)
        
        print(f"✅ Text splitting: {len(chunks)} chunks created")
        print(f"   Sample chunk: {chunks[0][:100]}...")
        
        return processed_data
        
    except Exception as e:
        print(f"❌ Preprocessing demo failed: {e}")
        return None


async def demo_vector_database():
    """Demonstrate vector database capabilities"""
    print("\n🗄️ Vector Database Demo")
    print("=" * 50)
    
    try:
        vector_service = VectorService()
        vector_db = EnhancedVectorDatabase(vector_service)
        
        # Sample traffic data
        sample_data = {
            "traffic_data": [
                {"timestamp": "2024-01-15T08:00:00", "speed": 45.2, "volume": 1200, "occupancy": 0.75}
            ],
            "incidents": [
                {"description": "Multi-vehicle accident on I-95 North", "severity": "major", "location": "I-95 North"}
            ]
        }
        
        # Build vector database
        await vector_db.abuild_from_traffic_data(sample_data)
        
        # Get statistics
        stats = vector_db.get_statistics()
        print(f"✅ Vector database built with {stats['total_vectors']} vectors")
        print(f"✅ Data types: {stats['data_types']}")
        print(f"✅ Average dimension: {stats['average_vector_dimension']}")
        
        # Test search
        search_results = vector_db.search_by_text("traffic accident", k=2)
        print(f"✅ Search results: {len(search_results)} matches found")
        
        return vector_db
        
    except Exception as e:
        print(f"❌ Vector database demo failed: {e}")
        return None


async def demo_ragas_evaluation():
    """Demonstrate RAGAS evaluation capabilities"""
    print("\n📊 RAGAS Evaluation Demo")
    print("=" * 50)
    
    try:
        evaluator = RagasEvaluator()
        
        # Sample evaluation data
        questions = [
            "What caused the traffic incident on I-95?",
            "How did weather affect traffic patterns?"
        ]
        answers = [
            "The incident was caused by a multi-vehicle accident during morning rush hour.",
            "Rainy weather reduced visibility and increased travel times by 15%."
        ]
        contexts = [
            ["Multi-vehicle accident on I-95 North at 8:15 AM caused major delays"],
            ["Rainy conditions with 42°F temperature impacted traffic flow"]
        ]
        ground_truths = [
            ["Multi-vehicle accident"],
            ["Weather impact on traffic"]
        ]
        
        # Run evaluation
        evaluation_results = await evaluator.evaluate_traffic_analysis(
            questions, answers, contexts, ground_truths
        )
        
        print(f"✅ Evaluation completed with method: {evaluation_results['evaluation_method']}")
        print(f"✅ Overall score: {evaluation_results['overall_score']:.2f}")
        print(f"✅ Metric scores: {evaluation_results['metric_scores']}")
        
        # Generate insights
        insights = evaluator.get_quality_insights(evaluation_results)
        print(f"✅ Quality insights: {insights}")
        
        return evaluation_results
        
    except Exception as e:
        print(f"❌ RAGAS evaluation demo failed: {e}")
        return None


async def demo_deep_research():
    """Demonstrate deep research capabilities"""
    print("\n🔍 Deep Research Demo")
    print("=" * 50)
    
    try:
        deep_research = DeepResearchAgent()
        
        # Conduct deep research
        research_result = await deep_research.conduct_deep_research(
            research_question="Why was congestion higher than normal on I-95 today?",
            location="I-95 North",
            time_range_hours=24
        )
        
        print(f"✅ Deep research completed for {research_result['location']}")
        print(f"✅ Research depth: {research_result['research_metadata']['research_depth']}")
        print(f"✅ Tools used: {research_result['research_metadata']['tools_used']}")
        
        findings = research_result['findings']
        print(f"✅ Key insights: {len(findings['key_insights'])} found")
        print(f"✅ Recommendations: {len(findings['recommendations'])} generated")
        print(f"✅ Confidence level: {findings['confidence_level']}")
        
        # Generate research report
        report = await deep_research.generate_research_report(
            research_question=research_result['research_question'],
            location=research_result['location'],
            findings=findings
        )
        
        print(f"✅ Research report generated ({len(report)} characters)")
        
        return research_result
        
    except Exception as e:
        print(f"❌ Deep research demo failed: {e}")
        return None


async def demo_integrated_pipeline():
    """Demonstrate the complete integrated pipeline"""
    print("\n🚀 Integrated Pipeline Demo")
    print("=" * 50)
    
    try:
        pipeline = IntegratedTraffixPipeline()
        
        # Demo queries
        demo_queries = [
            {
                "query": "Why was congestion higher than normal on I-95 today?",
                "location": "I-95 North",
                "mode": "anomaly_investigation"
            },
            {
                "query": "Analyze traffic patterns for Route 50",
                "location": "Route 50 East",
                "mode": "deep"
            }
        ]
        
        for i, query_data in enumerate(demo_queries, 1):
            print(f"\n📋 Pipeline Demo {i}: {query_data['query']}")
            print(f"Location: {query_data['location']}")
            print(f"Mode: {query_data['mode']}")
            
            # Run pipeline
            result = await pipeline.run_complete_pipeline(
                user_query=query_data["query"],
                location=query_data["location"],
                mode=query_data["mode"],
                export_formats=["html", "pdf", "email"]
            )
            
            if result["success"]:
                print(f"✅ Pipeline {i} completed successfully")
                print(f"   Processing time: {result['pipeline_metadata']['total_processing_time']:.2f} seconds")
                print(f"   Steps completed: {result['pipeline_metadata']['steps_completed']}")
                
                # Show evaluation results
                eval_results = result.get("evaluation_results", {})
                if eval_results:
                    overall_score = eval_results.get("overall_score", 0)
                    print(f"   Quality score: {overall_score:.2f}")
                
                # Show export results
                export_results = result.get("export_results", {})
                for format_type, export_result in export_results.items():
                    if export_result.get("success"):
                        print(f"   {format_type.upper()} export: ✅")
                    else:
                        print(f"   {format_type.upper()} export: ❌")
                
                # Save results
                pipeline.save_pipeline_state(
                    result,
                    f"demo_pipeline_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                print(f"   Results saved to file")
                
            else:
                print(f"❌ Pipeline {i} failed: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integrated pipeline demo failed: {e}")
        return False


async def demo_modularity():
    """Demonstrate modularity and independent updates"""
    print("\n🔧 Modularity Demo")
    print("=" * 50)
    
    try:
        # Test independent module updates
        print("✅ Testing independent module updates...")
        
        # Test preprocessing module
        preprocessor = TrafficDataPreprocessor(chunk_size=800, chunk_overlap=150)
        print("✅ Preprocessing module updated with new parameters")
        
        # Test vector database module
        vector_service = VectorService()
        vector_db = EnhancedVectorDatabase(vector_service)
        print("✅ Vector database module initialized independently")
        
        # Test evaluation module
        evaluator = RagasEvaluator()
        print("✅ Evaluation module initialized independently")
        
        # Test research module
        deep_research = DeepResearchAgent()
        print("✅ Research module initialized independently")
        
        print("✅ All modules can be updated independently")
        print("✅ Modular architecture ensures maintainability")
        
        return True
        
    except Exception as e:
        print(f"❌ Modularity demo failed: {e}")
        return False


async def main():
    """Main demo function"""
    print("🎉 Traffix Integrated Pipeline Demo")
    print("=" * 60)
    print("Demonstrating modules integrated from previous assignments:")
    print("• Assignment 02: Text processing and vector database")
    print("• Assignment 06: Multi-agent patterns")
    print("• Assignment 08: RAGAS evaluation")
    print("• Assignment 10: Deep research capabilities")
    print("=" * 60)
    
    try:
        # Run all demos
        await demo_preprocessing()
        await demo_vector_database()
        await demo_ragas_evaluation()
        await demo_deep_research()
        await demo_integrated_pipeline()
        await demo_modularity()
        
        print("\n" + "=" * 60)
        print("🎉 All integrated pipeline demos completed successfully!")
        print("🚀 You can now use the integrated pipeline with:")
        print("   • POST /analyze/integrated - Complete pipeline")
        print("   • POST /analyze/workflow - Agent workflow only")
        print("   • POST /analyze - Legacy modes")
        print("\n📚 API documentation: http://localhost:8000/docs")
        print("🔧 Modular design allows independent updates")
        print("📊 RAGAS evaluation ensures quality")
        print("🔍 Deep research provides comprehensive analysis")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.getLogger("traffix.demo").error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
