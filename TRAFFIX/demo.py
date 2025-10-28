#!/usr/bin/env python3
"""
Traffix Demo Script
Demonstrates the system capabilities with sample data
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from modes import QuickModeProcessor, DeepModeProcessor, AnomalyInvestigationProcessor, LeadershipSummaryProcessor
from models import UserQuestion
from logging_config import setup_logging


async def demo_quick_mode():
    """Demonstrate Quick Mode functionality"""
    print("🚀 Quick Mode Demo")
    print("=" * 40)
    
    processor = QuickModeProcessor()
    
    # Demo locations
    locations = [
        "I-95 North",
        "I-495 Beltway", 
        "Route 50 East",
        "I-66 West"
    ]
    
    for location in locations:
        print(f"\n📍 Analyzing {location}...")
        
        try:
            result = await processor.generate_daily_summary(location)
            
            if result["success"]:
                summary = result["summary"]
                print(f"   ✅ Analysis completed in {summary['processing_time']}")
                print(f"   🎯 Confidence: {summary['confidence_score']:.2f}")
                print(f"   🚨 Anomaly detected: {summary['anomaly_detected']}")
                
                if summary["primary_causes"]:
                    print(f"   🔍 Primary causes: {', '.join(summary['primary_causes'][:2])}")
                
                if summary["key_recommendations"]:
                    print(f"   💡 Top recommendation: {summary['key_recommendations'][0]}")
            else:
                print(f"   ❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Quick Mode demo completed")


async def demo_deep_mode():
    """Demonstrate Deep Mode functionality"""
    print("\n🔬 Deep Mode Demo")
    print("=" * 40)
    
    processor = DeepModeProcessor()
    
    # Demo comprehensive analysis
    location = "I-95 North"
    print(f"\n📍 Deep analysis of {location}...")
    
    try:
        result = await processor.generate_weekly_report(location)
        
        if result["success"]:
            summary = result["comprehensive_summary"]
            print(f"   ✅ Deep analysis completed in {summary['analysis_overview']['processing_time']}")
            print(f"   🎯 Confidence: {summary['analysis_overview']['confidence_score']:.2f}")
            print(f"   📊 Analysis depth: {summary['analysis_overview']['analysis_depth']}")
            
            # Key findings
            findings = summary["key_findings"]
            if findings["primary_causes"]:
                print(f"   🔍 Primary causes: {', '.join(findings['primary_causes'][:3])}")
            
            if findings["recommendations"]:
                print(f"   💡 Recommendations: {len(findings['recommendations'])} total")
                print(f"      Top: {findings['recommendations'][0]}")
            
            # Additional insights
            insights = summary["additional_insights"]
            if insights:
                print(f"   📈 Additional insights: {len(insights)} categories")
                for category, data in insights.items():
                    print(f"      {category}: {len(data)} items")
            
            # Data quality
            quality = summary["data_quality"]
            print(f"   📋 Data quality: {quality['overall_quality']}")
            print(f"      Completeness: {quality['data_completeness']:.2f}")
            print(f"      Source diversity: {quality['source_diversity']:.2f}")
            
        else:
            print(f"   ❌ Deep analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Deep Mode demo completed")


async def demo_insights():
    """Demonstrate insights generation"""
    print("\n💡 Insights Demo")
    print("=" * 40)
    
    quick_processor = QuickModeProcessor()
    deep_processor = DeepModeProcessor()
    
    location = "I-495 Beltway"
    
    # Quick insights
    print(f"\n📍 Quick insights for {location}...")
    try:
        result = await quick_processor.generate_daily_summary(location)
        if result["success"]:
            insights = quick_processor.get_quick_insights(result["analysis_result"])
            for insight in insights:
                print(f"   {insight}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Deep insights
    print(f"\n📍 Deep insights for {location}...")
    try:
        result = await deep_processor.generate_weekly_report(location)
        if result["success"]:
            insights = deep_processor.get_deep_insights(result["analysis_results"])
            for insight in insights:
                print(f"   {insight}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Insights demo completed")


async def demo_data_collection():
    """Demonstrate data collection capabilities"""
    print("\n📊 Data Collection Demo")
    print("=" * 40)
    
    from services import DataIntegrationService
    
    service = DataIntegrationService()
    location = "Route 50 East"
    
    print(f"\n📍 Collecting data for {location}...")
    
    try:
        # Quick mode data collection
        print("   🚀 Quick mode data collection...")
        quick_data = await service.collect_all_data(location, time_range_hours=24, mode="quick")
        
        print(f"   📈 Traffic data points: {len(quick_data['traffic_data'])}")
        print(f"   📰 News articles: {len(quick_data['news_articles'])}")
        print(f"   🚨 Incidents: {len(quick_data['incidents'])}")
        print(f"   🌤️ Weather data points: {len(quick_data['weather_data'])}")
        print(f"   📱 Social posts: {len(quick_data['social_posts'])}")
        print(f"   📊 Sources used: {', '.join(quick_data['collection_metadata']['sources_used'])}")
        
        # Deep mode data collection
        print("\n   🔬 Deep mode data collection...")
        deep_data = await service.collect_all_data(location, time_range_hours=168, mode="deep")
        
        print(f"   📈 Traffic data points: {len(deep_data['traffic_data'])}")
        print(f"   📰 News articles: {len(deep_data['news_articles'])}")
        print(f"   🚨 Incidents: {len(deep_data['incidents'])}")
        print(f"   🌤️ Weather data points: {len(deep_data['weather_data'])}")
        print(f"   📱 Social posts: {len(deep_data['social_posts'])}")
        print(f"   📊 Sources used: {', '.join(deep_data['collection_metadata']['sources_used'])}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Data collection demo completed")


async def demo_anomaly_investigation():
    """Demonstrate Anomaly Investigation functionality"""
    print("\n🔍 Anomaly Investigation Demo")
    print("=" * 40)
    
    processor = AnomalyInvestigationProcessor()
    location = "I-95 North"
    
    print(f"\n📍 Investigating anomaly for {location}...")
    
    try:
        result = await processor.investigate_anomaly(
            location=location,
            time_period="today",
            baseline_period="previous_week"
        )
        
        if result["success"]:
            investigation = result["anomaly_investigation"]
            print(f"   ✅ Investigation completed in {result['processing_time_seconds']:.2f}s")
            print(f"   🎯 Anomaly type: {investigation['anomaly_type']}")
            print(f"   ⚠️ Severity: {investigation['severity']}")
            print(f"   📊 Deviation: {investigation['deviation_percentage']:.1f}%")
            
            if investigation["root_causes"]:
                print(f"   🔍 Root causes: {', '.join(investigation['root_causes'][:2])}")
            
            if investigation["recommended_actions"]:
                print(f"   💡 Actions: {investigation['recommended_actions'][0]}")
            
            # Show insights
            insights = processor.get_anomaly_insights(result)
            for insight in insights:
                print(f"   {insight}")
        else:
            print(f"   ❌ Investigation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Anomaly Investigation demo completed")


async def demo_leadership_summary():
    """Demonstrate Leadership Summary functionality"""
    print("\n👔 Leadership Summary Demo")
    print("=" * 40)
    
    processor = LeadershipSummaryProcessor()
    location = "I-495 Beltway"
    
    print(f"\n📍 Generating leadership summary for {location}...")
    
    try:
        result = await processor.generate_leadership_summary(
            location=location,
            period="week"
        )
        
        if result["success"]:
            summary = result["leadership_summary"]
            print(f"   ✅ Summary completed in {result['processing_time_seconds']:.2f}s")
            print(f"   📊 Period: {summary['period']}")
            print(f"   🎯 Confidence: {summary['confidence_level']}")
            
            if summary["key_highlights"]:
                print(f"   📈 Key highlights: {len(summary['key_highlights'])} items")
                for highlight in summary["key_highlights"][:2]:
                    print(f"      • {highlight}")
            
            if summary["major_incidents"]:
                print(f"   🚨 Major incidents: {len(summary['major_incidents'])}")
                for incident in summary["major_incidents"][:2]:
                    print(f"      • {incident}")
            
            if summary["recommendations"]:
                print(f"   💡 Recommendations: {len(summary['recommendations'])}")
                print(f"      • {summary['recommendations'][0]}")
            
            # Show executive insights
            insights = result["executive_insights"]
            for insight in insights:
                print(f"   {insight}")
        else:
            print(f"   ❌ Summary failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Leadership Summary demo completed")


async def demo_user_questions():
    """Demonstrate user question answering"""
    print("\n❓ User Questions Demo")
    print("=" * 40)
    
    anomaly_processor = AnomalyInvestigationProcessor()
    leadership_processor = LeadershipSummaryProcessor()
    
    # Example user questions
    questions = [
        UserQuestion(
            question_type="anomaly_investigation",
            location="Route 50 East",
            time_period="today",
            specific_question="Why was congestion higher than normal today?",
            context={"baseline_period": "previous_week"}
        ),
        UserQuestion(
            question_type="leadership_summary",
            location="I-66 West",
            time_period="week",
            specific_question="Can you summarize this week's mobility highlights for leadership?"
        )
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📍 Question {i}: {question.specific_question}")
        
        try:
            if question.question_type == "anomaly_investigation":
                result = await anomaly_processor.answer_user_question(question)
            else:
                result = await leadership_processor.answer_leadership_question(question)
            
            if result["success"]:
                print(f"   ✅ Question answered successfully")
                if question.question_type == "anomaly_investigation":
                    investigation = result["anomaly_investigation"]
                    print(f"   🔍 Anomaly type: {investigation['anomaly_type']}")
                    print(f"   ⚠️ Severity: {investigation['severity']}")
                else:
                    summary = result["leadership_summary"]
                    print(f"   📊 Period: {summary['period']}")
                    print(f"   🎯 Confidence: {summary['confidence_level']}")
            else:
                print(f"   ❌ Failed to answer: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ User Questions demo completed")


async def main():
    """Main demo function"""
    print("🚦 Traffix - AI Storytelling for Transportation Analytics")
    print("🎯 Demonstration Script - Enhanced for User Needs")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Setup logging
    setup_logging()
    
    try:
        # Run all demos
        await demo_data_collection()
        await demo_quick_mode()
        await demo_deep_mode()
        await demo_anomaly_investigation()
        await demo_leadership_summary()
        await demo_user_questions()
        await demo_insights()
        await demo_agent_architecture()
        
        print("\n" + "=" * 60)
        print("🎉 All demos completed successfully!")
        print("🚀 You can now start the full system with: python run.py")
        print("📚 API documentation will be available at: http://localhost:8000/docs")
        print("\n🎯 New Features Demonstrated:")
        print("   • Anomaly Investigation - Why did congestion change?")
        print("   • Leadership Summaries - Executive-ready reports")
        print("   • User Question Answering - Natural language queries")
        print("   • Enhanced Analysis - Focused on DOT/MPO needs")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.getLogger("traffix.demo").error(f"Demo failed: {e}")


async def demo_agent_architecture():
    """Demonstrate the new multi-agent architecture"""
    print("\n🤖 Multi-Agent Architecture Demo")
    print("=" * 50)
    
    try:
        from workflow import TraffixWorkflow
        
        # Initialize the workflow
        workflow = TraffixWorkflow()
        
        # Demo queries for different agent roles
        demo_queries = [
            {
                "query": "Why was congestion higher than normal on I-95 today?",
                "location": "I-95 North",
                "mode": "anomaly_investigation",
                "description": "Supervisor routes to Research → Writer → Editor → Evaluator"
            },
            {
                "query": "Summarize this week's mobility highlights for leadership",
                "location": "I-495 Beltway",
                "mode": "leadership_summary", 
                "description": "All agents collaborate for executive-ready report"
            },
            {
                "query": "Analyze traffic patterns for Route 50",
                "location": "Route 50 East",
                "mode": "deep",
                "description": "Full agent pipeline with quality assurance"
            }
        ]
        
        for i, demo in enumerate(demo_queries, 1):
            print(f"\n📋 Demo {i}: {demo['description']}")
            print(f"Query: {demo['query']}")
            print(f"Location: {demo['location']}")
            print(f"Mode: {demo['mode']}")
            
            # Run the workflow
            result = await workflow.run_workflow(
                user_query=demo['query'],
                location=demo['location'],
                mode=demo['mode']
            )
            
            if result.get("workflow_state") == "completed":
                final_output = result.get("final_output", {})
                workflow_metadata = final_output.get("workflow_metadata", {})
                
                print(f"✅ Workflow completed successfully")
                print(f"   Agents executed: {', '.join(workflow_metadata.get('agents_executed', []))}")
                print(f"   Processing time: {workflow_metadata.get('completed_at', 'Unknown')}")
                
                # Show evaluation results if available
                evaluation_results = final_output.get("evaluation_results", {})
                if evaluation_results:
                    overall_score = evaluation_results.get("overall_score", 0)
                    print(f"   Quality score: {overall_score:.2f}")
                    
                    composite_scores = evaluation_results.get("composite_scores", {})
                    if composite_scores:
                        print(f"   Faithfulness: {composite_scores.get('faithfulness_score', 0):.2f}")
                        print(f"   Relevancy: {composite_scores.get('relevancy_score', 0):.2f}")
                        print(f"   Correctness: {composite_scores.get('correctness_score', 0):.2f}")
            else:
                print(f"❌ Workflow failed: {result.get('errors', 'Unknown error')}")
        
        print(f"\n🎯 Agent Architecture Benefits:")
        print(f"   • Supervisor Agent: Intelligent query routing and work planning")
        print(f"   • Research Agent: Comprehensive data collection and analysis")
        print(f"   • Writer Agent: Compelling narrative generation")
        print(f"   • Editor Agent: Quality assurance and tone optimization")
        print(f"   • Evaluator Agent: RAGAS-style quality evaluation")
        print(f"   • LangGraph Workflow: Orchestrated multi-agent collaboration")
        
    except Exception as e:
        print(f"❌ Agent architecture demo failed: {e}")
        logging.getLogger("traffix.demo").error(f"Agent architecture demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
