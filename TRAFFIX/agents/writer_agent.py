"""
Writer Agent (Storyteller) - Synthesizes data into narratives (concise summaries or detailed reports)
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from agents.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from models import ReportMode


class WriterAgent(BaseAgent):
    """Writer Agent responsible for creating compelling narratives from research data"""
    
    def __init__(self):
        super().__init__("writer")
        self.logger = logging.getLogger("traffix.writer")
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup LLM prompts for different narrative types"""
        
        # Executive Summary Prompt
        self.executive_summary_prompt = PromptTemplate(
            input_variables=["research_data", "location", "query_type", "audience"],
            template="""
            Create an executive summary for transportation leadership based on the following research data:
            
            Location: {location}
            Query Type: {query_type}
            Target Audience: {audience}
            
            Research Data:
            {research_data}
            
            Requirements:
            - 2-3 paragraphs maximum
            - Focus on key findings and actionable insights
            - Use clear, professional language
            - Include specific metrics and data points
            - Highlight any urgent issues requiring attention
            - Provide clear recommendations
            
            Format the summary for executive consumption with bullet points for key points.
            """
        )
        
        # Detailed Narrative Prompt
        self.detailed_narrative_prompt = PromptTemplate(
            input_variables=["research_data", "location", "query_type", "narrative_style"],
            template="""
            Create a detailed narrative report based on the research data:
            
            Location: {location}
            Query Type: {query_type}
            Narrative Style: {narrative_style}
            
            Research Data:
            {research_data}
            
            Structure the narrative with:
            1. Introduction - Set the context and scope
            2. Key Findings - Present the main discoveries
            3. Analysis - Explain what the data means
            4. Evidence - Support findings with specific data
            5. Implications - Discuss the significance
            6. Recommendations - Provide actionable next steps
            7. Conclusion - Summarize key takeaways
            
            Use engaging, professional language that tells a compelling story about the traffic situation.
            Include specific examples and data points to support your narrative.
            """
        )
        
        # Incident Story Prompt
        self.incident_story_prompt = PromptTemplate(
            input_variables=["incidents", "causes", "location", "timeframe"],
            template="""
            Create a narrative about traffic incidents and their impact:
            
            Location: {location}
            Timeframe: {timeframe}
            
            Incidents:
            {incidents}
            
            Causes:
            {causes}
            
            Write a compelling story that:
            - Explains what happened and when
            - Describes the impact on traffic flow
            - Identifies the root causes
            - Explains the response and resolution
            - Provides lessons learned
            - Suggests prevention strategies
            
            Use a journalistic style that is informative yet engaging.
            """
        )
        
        # Pattern Analysis Prompt
        self.pattern_analysis_prompt = PromptTemplate(
            input_variables=["patterns", "trends", "location", "timeframe"],
            template="""
            Create a narrative about traffic patterns and trends:
            
            Location: {location}
            Timeframe: {timeframe}
            
            Patterns:
            {patterns}
            
            Trends:
            {trends}
            
            Write an analytical narrative that:
            - Explains the patterns discovered
            - Discusses trends and their implications
            - Identifies recurring issues
            - Suggests long-term solutions
            - Provides data-driven insights
            
            Use an analytical but accessible tone.
            """
        )
    
    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute writing tasks"""
        research_data = input_data.get("research_data", {})
        location = input_data.get("location", "Unknown")
        query_type = input_data.get("query_type", "daily_summary")
        narrative_style = input_data.get("narrative_style", "professional")
        audience = input_data.get("audience", "analysts")
        
        self.logger.info(f"Writer agent creating narrative for {location} - {query_type}")
        
        try:
            # Step 1: Create executive summary
            executive_summary = await self._create_executive_summary(
                research_data, location, query_type, audience
            )
            
            # Step 2: Create detailed narrative
            detailed_narrative = await self._create_detailed_narrative(
                research_data, location, query_type, narrative_style
            )
            
            # Step 3: Create specialized narratives based on query type
            specialized_narratives = await self._create_specialized_narratives(
                research_data, location, query_type
            )
            
            # Step 4: Generate story elements
            story_elements = await self._generate_story_elements(
                research_data, location, query_type
            )
            
            # Step 5: Create narrative metadata
            narrative_metadata = self._create_narrative_metadata(
                research_data, location, query_type
            )
            
            return {
                "executive_summary": executive_summary,
                "detailed_narrative": detailed_narrative,
                "specialized_narratives": specialized_narratives,
                "story_elements": story_elements,
                "narrative_metadata": narrative_metadata,
                "writer_metadata": {
                    "location": location,
                    "query_type": query_type,
                    "narrative_style": narrative_style,
                    "audience": audience,
                    "generated_at": datetime.now().isoformat(),
                    "narrative_quality": self._assess_narrative_quality(executive_summary, detailed_narrative)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Writing task failed: {e}")
            raise
    
    async def _create_executive_summary(self, research_data: Dict[str, Any], 
                                      location: str, query_type: str, 
                                      audience: str) -> str:
        """Create executive summary for leadership"""
        
        try:
            # Prepare research data for prompt
            formatted_data = self._format_research_data_for_prompt(research_data)
            
            # Create chain
            chain = LLMChain(llm=self.llm, prompt=self.executive_summary_prompt)
            
            # Generate summary
            summary = await chain.arun(
                research_data=formatted_data,
                location=location,
                query_type=query_type,
                audience=audience
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Executive summary creation failed: {e}")
            return f"Executive summary for {location} traffic analysis - {query_type} mode analysis completed."
    
    async def _create_detailed_narrative(self, research_data: Dict[str, Any], 
                                       location: str, query_type: str, 
                                       narrative_style: str) -> str:
        """Create detailed narrative report"""
        
        try:
            # Prepare research data for prompt
            formatted_data = self._format_research_data_for_prompt(research_data)
            
            # Create chain
            chain = LLMChain(llm=self.llm, prompt=self.detailed_narrative_prompt)
            
            # Generate narrative
            narrative = await chain.arun(
                research_data=formatted_data,
                location=location,
                query_type=query_type,
                narrative_style=narrative_style
            )
            
            return narrative
            
        except Exception as e:
            self.logger.error(f"Detailed narrative creation failed: {e}")
            return f"Detailed narrative for {location} traffic analysis - comprehensive report generated."
    
    async def _create_specialized_narratives(self, research_data: Dict[str, Any], 
                                           location: str, query_type: str) -> Dict[str, str]:
        """Create specialized narratives based on query type"""
        
        specialized_narratives = {}
        
        try:
            # Incident narrative
            if query_type in ["incident_analysis", "anomaly_investigation"]:
                incidents = research_data.get("key_incidents", [])
                causes = research_data.get("cause_analysis", {})
                
                if incidents:
                    chain = LLMChain(llm=self.llm, prompt=self.incident_story_prompt)
                    incident_narrative = await chain.arun(
                        incidents=self._format_incidents_for_prompt(incidents),
                        causes=self._format_causes_for_prompt(causes),
                        location=location,
                        timeframe="recent"
                    )
                    specialized_narratives["incident_narrative"] = incident_narrative
            
            # Pattern analysis narrative
            if query_type == "pattern_analysis":
                patterns = research_data.get("pattern_analysis", {})
                trends = research_data.get("research_insights", {})
                
                if patterns:
                    chain = LLMChain(llm=self.llm, prompt=self.pattern_analysis_prompt)
                    pattern_narrative = await chain.arun(
                        patterns=self._format_patterns_for_prompt(patterns),
                        trends=self._format_trends_for_prompt(trends),
                        location=location,
                        timeframe="analysis_period"
                    )
                    specialized_narratives["pattern_narrative"] = pattern_narrative
            
        except Exception as e:
            self.logger.error(f"Specialized narrative creation failed: {e}")
        
        return specialized_narratives
    
    async def _generate_story_elements(self, research_data: Dict[str, Any], 
                                     location: str, query_type: str) -> List[Dict[str, Any]]:
        """Generate individual story elements"""
        
        story_elements = []
        
        # Introduction element
        introduction = self._create_introduction_element(research_data, location, query_type)
        story_elements.append(introduction)
        
        # Key findings element
        key_findings = self._create_key_findings_element(research_data, location)
        story_elements.append(key_findings)
        
        # Analysis element
        analysis = self._create_analysis_element(research_data, location)
        story_elements.append(analysis)
        
        # Evidence element
        evidence = self._create_evidence_element(research_data, location)
        story_elements.append(evidence)
        
        # Recommendations element
        recommendations = self._create_recommendations_element(research_data, location)
        story_elements.append(recommendations)
        
        return story_elements
    
    def _create_introduction_element(self, research_data: Dict[str, Any], 
                                   location: str, query_type: str) -> Dict[str, Any]:
        """Create introduction story element"""
        
        data_quality = research_data.get("research_metadata", {}).get("data_quality_score", 0.5)
        incident_count = len(research_data.get("key_incidents", []))
        
        content = f"""
        Traffic analysis for {location} reveals significant patterns requiring attention. 
        Based on comprehensive data collection from multiple sources, this analysis 
        identifies {incident_count} key incidents and provides insights into traffic 
        patterns and their underlying causes. The analysis demonstrates 
        {'high' if data_quality > 0.7 else 'moderate'} data quality with reliable findings.
        """
        
        return {
            "element_type": "introduction",
            "content": content.strip(),
            "supporting_data": [
                {"type": "location", "value": location},
                {"type": "incident_count", "value": str(incident_count)},
                {"type": "data_quality", "value": f"{data_quality:.2f}"}
            ],
            "confidence": data_quality
        }
    
    def _create_key_findings_element(self, research_data: Dict[str, Any], 
                                   location: str) -> Dict[str, Any]:
        """Create key findings story element"""
        
        cause_analysis = research_data.get("cause_analysis", {})
        primary_causes = cause_analysis.get("primary_causes", [])
        contributing_factors = cause_analysis.get("contributing_factors", [])
        
        content = f"""
        Key findings for {location} traffic analysis:
        """
        
        if primary_causes:
            content += f"\n• Primary causes identified: {', '.join(primary_causes[:3])}"
        
        if contributing_factors:
            content += f"\n• Contributing factors: {', '.join(contributing_factors[:3])}"
        
        supporting_data = []
        for cause in primary_causes[:3]:
            supporting_data.append({"type": "primary_cause", "value": cause})
        
        return {
            "element_type": "key_findings",
            "content": content.strip(),
            "supporting_data": supporting_data,
            "confidence": cause_analysis.get("cause_confidence", 0.5)
        }
    
    def _create_analysis_element(self, research_data: Dict[str, Any], 
                               location: str) -> Dict[str, Any]:
        """Create analysis story element"""
        
        pattern_analysis = research_data.get("pattern_analysis", {})
        patterns_detected = pattern_analysis.get("patterns_detected", False)
        
        content = f"""
        Analysis of {location} traffic data reveals {'significant patterns' if patterns_detected else 'standard traffic patterns'}. 
        The data indicates various factors influencing traffic flow, with both immediate 
        and underlying causes contributing to observed patterns.
        """
        
        if patterns_detected:
            content += " Recurring patterns suggest systematic issues requiring attention."
        
        supporting_data = [
            {"type": "pattern_analysis", "value": "patterns_detected" if patterns_detected else "no_patterns"},
            {"type": "analysis_type", "value": "comprehensive"}
        ]
        
        return {
            "element_type": "analysis",
            "content": content.strip(),
            "supporting_data": supporting_data,
            "confidence": 0.8 if patterns_detected else 0.6
        }
    
    def _create_evidence_element(self, research_data: Dict[str, Any], 
                               location: str) -> Dict[str, Any]:
        """Create evidence story element"""
        
        key_incidents = research_data.get("key_incidents", [])
        evidence_support = research_data.get("cause_analysis", {}).get("evidence_support", [])
        
        content = f"""
        Evidence supporting this analysis includes {len(key_incidents)} documented incidents 
        and {len(evidence_support)} supporting data points. The evidence demonstrates 
        clear correlations between identified causes and observed traffic impacts.
        """
        
        supporting_data = [
            {"type": "incident_count", "value": str(len(key_incidents))},
            {"type": "evidence_count", "value": str(len(evidence_support))},
            {"type": "data_sources", "value": "multiple"}
        ]
        
        return {
            "element_type": "evidence",
            "content": content.strip(),
            "supporting_data": supporting_data,
            "confidence": 0.7
        }
    
    def _create_recommendations_element(self, research_data: Dict[str, Any], 
                                      location: str) -> Dict[str, Any]:
        """Create recommendations story element"""
        
        recommendations = research_data.get("research_insights", {}).get("recommendations", [])
        
        content = f"""
        Based on this analysis, the following recommendations are proposed for {location}:
        """
        
        for i, rec in enumerate(recommendations[:3], 1):
            content += f"\n{i}. {rec}"
        
        supporting_data = []
        for rec in recommendations[:3]:
            supporting_data.append({"type": "recommendation", "value": rec})
        
        return {
            "element_type": "recommendations",
            "content": content.strip(),
            "supporting_data": supporting_data,
            "confidence": 0.8
        }
    
    def _format_research_data_for_prompt(self, research_data: Dict[str, Any]) -> str:
        """Format research data for LLM prompts"""
        
        formatted = "Research Data Summary:\n\n"
        
        # Add key incidents
        key_incidents = research_data.get("key_incidents", [])
        if key_incidents:
            formatted += f"Key Incidents ({len(key_incidents)}):\n"
            for incident in key_incidents[:5]:  # Top 5 incidents
                formatted += f"- {incident.get('description', 'Unknown')} ({incident.get('severity', 'Unknown')})\n"
            formatted += "\n"
        
        # Add cause analysis
        cause_analysis = research_data.get("cause_analysis", {})
        if cause_analysis:
            formatted += "Cause Analysis:\n"
            formatted += f"Primary Causes: {', '.join(cause_analysis.get('primary_causes', []))}\n"
            formatted += f"Contributing Factors: {', '.join(cause_analysis.get('contributing_factors', []))}\n"
            formatted += f"Confidence: {cause_analysis.get('cause_confidence', 0):.2f}\n\n"
        
        # Add research insights
        insights = research_data.get("research_insights", {})
        if insights:
            formatted += "Research Insights:\n"
            formatted += f"Summary: {insights.get('summary', 'No summary available')}\n"
            formatted += f"Key Findings: {', '.join(insights.get('key_findings', []))}\n"
            formatted += f"Recommendations: {', '.join(insights.get('recommendations', []))}\n"
        
        return formatted
    
    def _format_incidents_for_prompt(self, incidents: List[Dict[str, Any]]) -> str:
        """Format incidents for prompt"""
        
        formatted = "Traffic Incidents:\n"
        for incident in incidents[:5]:  # Top 5 incidents
            formatted += f"- {incident.get('description', 'Unknown')} "
            formatted += f"({incident.get('severity', 'Unknown')}) "
            formatted += f"at {incident.get('location', 'Unknown location')}\n"
        
        return formatted
    
    def _format_causes_for_prompt(self, causes: Dict[str, Any]) -> str:
        """Format causes for prompt"""
        
        formatted = "Identified Causes:\n"
        formatted += f"Primary: {', '.join(causes.get('primary_causes', []))}\n"
        formatted += f"Contributing: {', '.join(causes.get('contributing_factors', []))}\n"
        
        return formatted
    
    def _format_patterns_for_prompt(self, patterns: Dict[str, Any]) -> str:
        """Format patterns for prompt"""
        
        formatted = "Traffic Patterns:\n"
        if patterns.get("temporal_patterns"):
            formatted += f"Temporal: {len(patterns['temporal_patterns'])} hourly patterns identified\n"
        if patterns.get("spatial_patterns"):
            formatted += f"Spatial: {len(patterns['spatial_patterns'])} location patterns identified\n"
        
        return formatted
    
    def _format_trends_for_prompt(self, trends: Dict[str, Any]) -> str:
        """Format trends for prompt"""
        
        formatted = "Trends and Insights:\n"
        formatted += f"Key Findings: {', '.join(trends.get('key_findings', []))}\n"
        formatted += f"Recommendations: {', '.join(trends.get('recommendations', []))}\n"
        
        return formatted
    
    def _create_narrative_metadata(self, research_data: Dict[str, Any], 
                                 location: str, query_type: str) -> Dict[str, Any]:
        """Create metadata for the narrative"""
        
        return {
            "narrative_type": query_type,
            "location": location,
            "data_sources": list(research_data.keys()),
            "incident_count": len(research_data.get("key_incidents", [])),
            "cause_confidence": research_data.get("cause_analysis", {}).get("cause_confidence", 0.5),
            "pattern_detected": research_data.get("pattern_analysis", {}).get("patterns_detected", False),
            "generated_at": datetime.now().isoformat()
        }
    
    def _assess_narrative_quality(self, executive_summary: str, 
                                detailed_narrative: str) -> float:
        """Assess the quality of generated narratives"""
        
        # Simple quality assessment based on length and content
        summary_quality = min(1.0, len(executive_summary) / 500)  # Expect ~500 chars
        narrative_quality = min(1.0, len(detailed_narrative) / 2000)  # Expect ~2000 chars
        
        return (summary_quality + narrative_quality) / 2
