"""
Streamlit User Interface for Traffix
"""
import streamlit as st
import asyncio
import logging
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from orchestration.langgraph_workflow import TraffixWorkflow
from models import UserQuestion
from tech_config import tech_settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("traffix.streamlit")

# Page configuration
st.set_page_config(
    page_title="Traffix - AI Storytelling for Transportation Analytics",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .mode-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize workflow
@st.cache_resource
def get_workflow():
    return TraffixWorkflow()

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🚦 Traffix</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: #7f8c8d;">AI Storytelling for Transportation Analytics</h2>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # Location input
        location = st.text_input(
            "Location",
            value="I-95 North",
            help="Enter the traffic corridor or location to analyze"
        )
        
        # Mode selection
        mode = st.selectbox(
            "Analysis Mode",
            options=["quick", "deep", "anomaly_investigation", "leadership_summary", "pattern_analysis"],
            format_func=lambda x: {
                "quick": "🚀 Quick Mode - Daily Summaries",
                "deep": "🔬 Deep Mode - Comprehensive Analysis",
                "anomaly_investigation": "🔍 Anomaly Investigation",
                "leadership_summary": "👔 Leadership Summary",
                "pattern_analysis": "📊 Pattern Analysis"
            }[x]
        )
        
        # Time period
        time_period = st.selectbox(
            "Time Period",
            options=["24h", "48h", "1w", "2w", "1m"],
            format_func=lambda x: {
                "24h": "24 Hours",
                "48h": "48 Hours", 
                "1w": "1 Week",
                "2w": "2 Weeks",
                "1m": "1 Month"
            }[x]
        )
        
        # User question
        user_question = st.text_area(
            "Specific Question (Optional)",
            placeholder="e.g., Why was congestion higher than normal today?",
            help="Ask a specific question about the traffic patterns"
        )
        
        # Analysis button
        analyze_button = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
        
        # Export options
        st.header("Export Options")
        export_html = st.checkbox("Export as HTML", value=True)
        export_pdf = st.checkbox("Export as PDF", value=False)
        export_json = st.checkbox("Export as JSON", value=False)
        
        # Email options
        st.header("Email Options")
        email_enabled = st.checkbox("Email Report")
        if email_enabled:
            email_recipients = st.text_input(
                "Recipients (comma-separated)",
                placeholder="analyst@dot.gov, manager@dot.gov"
            )
    
    # Main content area
    if analyze_button:
        run_analysis(location, mode, time_period, user_question, {
            "export_html": export_html,
            "export_pdf": export_pdf,
            "export_json": export_json,
            "email_enabled": email_enabled,
            "email_recipients": email_recipients if email_enabled else None
        })
    
    # Display mode information
    display_mode_info(mode)
    
    # Display example questions
    display_example_questions()

def run_analysis(location: str, mode: str, time_period: str, 
                user_question: str, export_options: dict):
    """Run the analysis workflow"""
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize workflow
        workflow = get_workflow()
        
        # Update progress
        progress_bar.progress(10)
        status_text.text("Initializing analysis...")
        
        # Run analysis
        status_text.text("Running analysis workflow...")
        progress_bar.progress(30)
        
        # Run async workflow
        result = asyncio.run(workflow.run_analysis(
            location=location,
            mode=mode,
            time_period=time_period,
            user_question=user_question
        ))
        
        progress_bar.progress(80)
        status_text.text("Generating results...")
        
        # Check if analysis was successful
        if result["workflow_status"] == "completed":
            progress_bar.progress(100)
            status_text.text("Analysis completed successfully!")
            
            # Display results
            display_results(result, location, mode)
            
            # Handle exports
            handle_exports(result, export_options)
            
        else:
            progress_bar.progress(100)
            st.error(f"Analysis failed: {result.get('error_message', 'Unknown error')}")
            
    except Exception as e:
        progress_bar.progress(100)
        st.error(f"Analysis failed: {str(e)}")
        logger.error(f"Analysis failed: {e}")

def display_results(result: dict, location: str, mode: str):
    """Display analysis results"""
    
    st.success(f"✅ Analysis completed for {location} in {result['processing_time']:.2f} seconds")
    
    # Tabs for different result views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "📈 Analysis", "📝 Story", "📄 Report"])
    
    with tab1:
        display_summary(result, mode)
    
    with tab2:
        display_analysis_details(result)
    
    with tab3:
        display_story(result)
    
    with tab4:
        display_report(result)

def display_summary(result: dict, mode: str):
    """Display analysis summary"""
    
    st.header("Analysis Summary")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Processing Time", f"{result['processing_time']:.2f}s")
    
    with col2:
        st.metric("Mode", mode.title())
    
    with col3:
        st.metric("Status", result['workflow_status'].title())
    
    with col4:
        if 'analysis_result' in result and result['analysis_result']:
            confidence = result['analysis_result'].get('analysis_result', {}).get('confidence_score', 0)
            st.metric("Confidence", f"{confidence:.2f}")
    
    # Analysis insights
    if 'analysis_result' in result and result['analysis_result']:
        analysis = result['analysis_result'].get('analysis_result', {})
        
        if analysis.get('anomaly_detected'):
            st.warning("🚨 Traffic anomaly detected")
        else:
            st.success("✅ Normal traffic patterns")
        
        # Primary causes
        if analysis.get('primary_causes'):
            st.subheader("Primary Causes")
            for cause in analysis['primary_causes']:
                st.write(f"• {cause}")
        
        # Recommendations
        if analysis.get('recommendations'):
            st.subheader("Recommendations")
            for rec in analysis['recommendations']:
                st.write(f"• {rec}")

def display_analysis_details(result: dict):
    """Display detailed analysis"""
    
    st.header("Detailed Analysis")
    
    # Traffic data visualization
    if 'collected_data' in result and result['collected_data']:
        traffic_data = result['collected_data'].get('traffic_data', [])
        
        if traffic_data:
            # Create DataFrame
            df = pd.DataFrame(traffic_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Speed over time
            fig_speed = px.line(df, x='timestamp', y='speed', 
                              title='Speed Over Time', 
                              labels={'speed': 'Speed (mph)', 'timestamp': 'Time'})
            st.plotly_chart(fig_speed, use_container_width=True)
            
            # Volume over time
            fig_volume = px.line(df, x='timestamp', y='volume',
                               title='Volume Over Time',
                               labels={'volume': 'Volume (vehicles)', 'timestamp': 'Time'})
            st.plotly_chart(fig_volume, use_container_width=True)
            
            # Congestion levels
            congestion_counts = df['congestion_level'].value_counts()
            fig_congestion = px.pie(values=congestion_counts.values, 
                                  names=congestion_counts.index,
                                  title='Congestion Level Distribution')
            st.plotly_chart(fig_congestion, use_container_width=True)

def display_story(result: dict):
    """Display generated story"""
    
    st.header("Generated Story")
    
    if 'story_data' in result and result['story_data']:
        story_data = result['story_data']
        
        # Executive summary
        if story_data.get('executive_summary'):
            st.subheader("Executive Summary")
            st.write(story_data['executive_summary'])
        
        # Story elements
        if story_data.get('story_elements'):
            st.subheader("Story Elements")
            for element in story_data['story_elements']:
                with st.expander(f"{element['element_type'].title()}"):
                    st.write(element['content'])
                    
                    if element.get('supporting_data'):
                        st.write("**Supporting Data:**")
                        for data in element['supporting_data']:
                            st.write(f"• {data.get('type', 'Unknown')}: {data.get('value', 'N/A')}")

def display_report(result: dict):
    """Display generated report"""
    
    st.header("Generated Report")
    
    if 'report_data' in result and result['report_data']:
        report_data = result['report_data']
        
        # Report metadata
        if 'report' in report_data:
            report = report_data['report']
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Report ID:** {report.get('report_id', 'N/A')}")
                st.write(f"**Mode:** {report.get('mode', 'N/A')}")
            with col2:
                st.write(f"**Generated:** {report.get('generated_at', 'N/A')}")
                st.write(f"**Confidence:** {report.get('confidence_score', 0):.2f}")
        
        # Report content
        if 'report_content' in report_data:
            st.subheader("Report Content")
            st.markdown(report_data['report_content'], unsafe_allow_html=True)

def display_mode_info(mode: str):
    """Display information about the selected mode"""
    
    mode_info = {
        "quick": {
            "title": "🚀 Quick Mode",
            "description": "Fast daily summaries optimized for speed",
            "processing_time": "30-60 seconds",
            "use_cases": ["Daily summaries", "Shift reports", "Incident summaries"]
        },
        "deep": {
            "title": "🔬 Deep Mode", 
            "description": "Comprehensive research reports with detailed analysis",
            "processing_time": "2-5 minutes",
            "use_cases": ["Weekly reports", "Monthly analysis", "Incident investigations"]
        },
        "anomaly_investigation": {
            "title": "🔍 Anomaly Investigation",
            "description": "Investigates why congestion patterns changed",
            "processing_time": "1-3 minutes",
            "use_cases": ["Why was congestion higher/lower?", "Root cause analysis"]
        },
        "leadership_summary": {
            "title": "👔 Leadership Summary",
            "description": "Executive summaries for transportation leadership",
            "processing_time": "2-4 minutes",
            "use_cases": ["Weekly highlights", "Executive reports"]
        },
        "pattern_analysis": {
            "title": "📊 Pattern Analysis",
            "description": "Identifies recurring congestion patterns and mitigation strategies",
            "processing_time": "3-5 minutes",
            "use_cases": ["Recurring pattern identification", "Mitigation strategies"]
        }
    }
    
    info = mode_info.get(mode, {})
    if info:
        with st.expander(f"ℹ️ About {info['title']}", expanded=False):
            st.write(f"**Description:** {info['description']}")
            st.write(f"**Processing Time:** {info['processing_time']}")
            st.write("**Use Cases:**")
            for use_case in info['use_cases']:
                st.write(f"• {use_case}")

def display_example_questions():
    """Display example questions"""
    
    with st.expander("💡 Example Questions", expanded=False):
        st.write("**Anomaly Investigation:**")
        st.write("• Why was congestion higher than normal today?")
        st.write("• What caused the traffic spike this morning?")
        st.write("• Why did travel times increase yesterday?")
        
        st.write("**Leadership Summary:**")
        st.write("• Can you summarize this week's mobility highlights?")
        st.write("• What are the key traffic issues this month?")
        st.write("• How did weather impact traffic this week?")
        
        st.write("**Pattern Analysis:**")
        st.write("• What recurring congestion patterns should we address?")
        st.write("• What mitigation strategies would be most effective?")
        st.write("• When do accidents most commonly occur?")

def handle_exports(result: dict, export_options: dict):
    """Handle report exports"""
    
    if any(export_options.values()):
        st.header("Export Options")
        
        if export_options.get('export_html'):
            if st.button("📄 Download HTML Report"):
                st.success("HTML report download initiated")
        
        if export_options.get('export_pdf'):
            if st.button("📋 Download PDF Report"):
                st.success("PDF report download initiated")
        
        if export_options.get('export_json'):
            if st.button("📊 Download JSON Data"):
                st.success("JSON data download initiated")
        
        if export_options.get('email_enabled') and export_options.get('email_recipients'):
            if st.button("📧 Email Report"):
                st.success(f"Report emailed to: {export_options['email_recipients']}")

if __name__ == "__main__":
    main()
