"""
Storyteller Agent - Creates compelling narratives from analysis results
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from agents.base_agent import BaseAgent
from models import StoryElement, ReportMode, AnalysisResult
from config import settings


class StorytellerAgent(BaseAgent):
    """Agent responsible for creating compelling narratives from analysis results"""
    
    def __init__(self):
        super().__init__("storyteller")
        self.llm = OpenAI(
            openai_api_key=settings.openai_api_key,
            temperature=0.7,
            max_tokens=1500
        )
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup LLM prompts for storytelling"""
        self.story_generation_prompt = PromptTemplate(
            input_variables=["analysis_result", "collected_data", "location", "mode"],
            template="""
            Create a compelling traffic analysis story based on the following data:
            
            Location: {location}
            Analysis Mode: {mode}
            
            Analysis Results:
            {analysis_result}
            
            Supporting Data:
            {collected_data}
            
            Create a narrative that includes:
            1. Introduction - Set the scene and context
            2. Problem Identification - What traffic issues were found
            3. Root Cause Analysis - Why these issues occurred
            4. Impact Assessment - How this affects commuters and the community
            5. Evidence Presentation - Supporting data and facts
            6. Resolution/Recommendations - What can be done
            
            Write in a clear, engaging style suitable for traffic analysts and decision-makers.
            Use specific data points and make the story compelling and actionable.
            """
        )
        
        self.executive_summary_prompt = PromptTemplate(
            input_variables=["story_elements", "location"],
            template="""
            Create an executive summary for the traffic analysis story:
            
            Location: {location}
            Story Elements: {story_elements}
            
            Write a concise 2-3 paragraph summary that highlights:
            - Key findings
            - Main causes of traffic issues
            - Critical recommendations
            - Expected impact of implementing recommendations
            
            Keep it professional and suitable for senior management.
            """
        )
        
        self.story_element_prompt = PromptTemplate(
            input_variables=["element_type", "analysis_data", "supporting_data"],
            template="""
            Create a story element of type "{element_type}" based on:
            
            Analysis Data: {analysis_data}
            Supporting Data: {supporting_data}
            
            Element types:
            - introduction: Set context and background
            - cause: Explain root causes of traffic issues
            - impact: Describe effects on traffic and community
            - resolution: Present solutions and recommendations
            - conclusion: Summarize key points and next steps
            
            Write 2-3 paragraphs that are engaging and data-driven.
            """
        )
    
    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create compelling narrative from analysis results"""
        analysis_result = input_data.get("analysis_result", {})
        collected_data = input_data.get("collected_data", {})
        location = input_data.get("location", "Unknown")
        mode = input_data.get("mode", ReportMode.QUICK)
        
        self.logger.info(f"Creating story for {location} in {mode} mode")
        
        try:
            # Generate main story
            main_story = await self._generate_main_story(analysis_result, collected_data, location, mode)
            
            # Generate story elements
            story_elements = await self._generate_story_elements(analysis_result, collected_data, location)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(story_elements, location)
            
            # Calculate story confidence
            confidence_score = self._calculate_story_confidence(analysis_result, story_elements)
            
            return {
                "main_story": main_story,
                "story_elements": [element.dict() for element in story_elements],
                "executive_summary": executive_summary,
                "confidence_score": confidence_score,
                "story_metadata": {
                    "location": location,
                    "mode": mode,
                    "generated_at": datetime.now().isoformat(),
                    "element_count": len(story_elements)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Story generation failed: {e}")
            raise
    
    async def _generate_main_story(self, analysis_result: Dict[str, Any], collected_data: Dict[str, Any], 
                                 location: str, mode: ReportMode) -> str:
        """Generate the main narrative story"""
        try:
            chain = LLMChain(llm=self.llm, prompt=self.story_generation_prompt)
            
            # Prepare data for the prompt
            analysis_text = self._format_analysis_for_prompt(analysis_result)
            data_text = self._format_collected_data_for_prompt(collected_data)
            
            story = await chain.arun(
                analysis_result=analysis_text,
                collected_data=data_text,
                location=location,
                mode=mode.value
            )
            
            return story
            
        except Exception as e:
            self.logger.error(f"Main story generation failed: {e}")
            return f"Unable to generate story for {location}. Analysis indicates traffic issues that require attention."
    
    async def _generate_story_elements(self, analysis_result: Dict[str, Any], 
                                     collected_data: Dict[str, Any], location: str) -> List[StoryElement]:
        """Generate individual story elements"""
        elements = []
        element_types = ["introduction", "cause", "impact", "resolution", "conclusion"]
        
        for element_type in element_types:
            try:
                element = await self._generate_story_element(element_type, analysis_result, collected_data)
                elements.append(element)
            except Exception as e:
                self.logger.error(f"Failed to generate {element_type} element: {e}")
                # Create fallback element
                elements.append(StoryElement(
                    element_type=element_type,
                    content=f"Analysis of {element_type} for {location} is incomplete.",
                    supporting_data=[],
                    confidence=0.1
                ))
        
        return elements
    
    async def _generate_story_element(self, element_type: str, analysis_result: Dict[str, Any], 
                                    collected_data: Dict[str, Any]) -> StoryElement:
        """Generate a single story element"""
        try:
            chain = LLMChain(llm=self.llm, prompt=self.story_element_prompt)
            
            analysis_text = self._format_analysis_for_prompt(analysis_result)
            data_text = self._format_collected_data_for_prompt(collected_data)
            
            content = await chain.arun(
                element_type=element_type,
                analysis_data=analysis_text,
                supporting_data=data_text
            )
            
            # Extract supporting data for this element
            supporting_data = self._extract_supporting_data(element_type, analysis_result, collected_data)
            
            # Calculate confidence based on data availability
            confidence = self._calculate_element_confidence(element_type, analysis_result, collected_data)
            
            return StoryElement(
                element_type=element_type,
                content=content,
                supporting_data=supporting_data,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Story element generation failed for {element_type}: {e}")
            raise
    
    async def _generate_executive_summary(self, story_elements: List[StoryElement], location: str) -> str:
        """Generate executive summary"""
        try:
            chain = LLMChain(llm=self.llm, prompt=self.executive_summary_prompt)
            
            elements_text = "\n\n".join([
                f"{element.element_type}: {element.content[:200]}..."
                for element in story_elements
            ])
            
            summary = await chain.arun(
                story_elements=elements_text,
                location=location
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Executive summary generation failed: {e}")
            return f"Traffic analysis for {location} reveals significant patterns requiring attention and action."
    
    def _format_analysis_for_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """Format analysis result for LLM prompt"""
        if not analysis_result:
            return "No analysis data available"
        
        text = f"Anomaly Detected: {analysis_result.get('anomaly_detected', False)}\n"
        text += f"Confidence: {analysis_result.get('confidence_score', 0):.2f}\n"
        text += f"Primary Causes: {', '.join(analysis_result.get('primary_causes', []))}\n"
        text += f"Impact: {analysis_result.get('impact_assessment', 'Unknown')}\n"
        text += f"Recommendations: {', '.join(analysis_result.get('recommendations', []))}\n"
        
        return text
    
    def _format_collected_data_for_prompt(self, collected_data: Dict[str, Any]) -> str:
        """Format collected data for LLM prompt"""
        text = ""
        
        traffic_data = collected_data.get("traffic_data", [])
        if traffic_data:
            text += f"Traffic Data Points: {len(traffic_data)}\n"
            text += f"Speed Range: {min(item.get('speed', 0) for item in traffic_data):.1f}-{max(item.get('speed', 0) for item in traffic_data):.1f} mph\n"
        
        news_data = collected_data.get("news_articles", [])
        if news_data:
            text += f"News Articles: {len(news_data)}\n"
            for article in news_data[:2]:
                text += f"- {article.get('title', 'No title')}\n"
        
        incidents = collected_data.get("incidents", [])
        if incidents:
            text += f"Incidents: {len(incidents)}\n"
            for incident in incidents:
                text += f"- {incident.get('description', 'No description')}\n"
        
        return text or "No supporting data available"
    
    def _extract_supporting_data(self, element_type: str, analysis_result: Dict[str, Any], 
                               collected_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relevant supporting data for a story element"""
        supporting_data = []
        
        if element_type == "cause":
            # Add primary causes as supporting data
            for cause in analysis_result.get("primary_causes", []):
                supporting_data.append({"type": "cause", "value": cause})
        
        elif element_type == "impact":
            # Add impact assessment
            impact = analysis_result.get("impact_assessment", "")
            if impact:
                supporting_data.append({"type": "impact", "value": impact})
        
        elif element_type == "resolution":
            # Add recommendations
            for rec in analysis_result.get("recommendations", []):
                supporting_data.append({"type": "recommendation", "value": rec})
        
        # Add statistical data for all elements
        traffic_data = collected_data.get("traffic_data", [])
        if traffic_data:
            avg_speed = sum(item.get("speed", 0) for item in traffic_data) / len(traffic_data)
            supporting_data.append({"type": "statistic", "value": f"Average speed: {avg_speed:.1f} mph"})
        
        return supporting_data
    
    def _calculate_element_confidence(self, element_type: str, analysis_result: Dict[str, Any], 
                                    collected_data: Dict[str, Any]) -> float:
        """Calculate confidence score for a story element"""
        base_confidence = analysis_result.get("confidence_score", 0.5)
        
        # Adjust based on data availability
        data_quality = 0.0
        if collected_data.get("traffic_data"):
            data_quality += 0.3
        if collected_data.get("news_articles"):
            data_quality += 0.2
        if collected_data.get("incidents"):
            data_quality += 0.2
        
        # Adjust based on analysis completeness
        if analysis_result.get("primary_causes"):
            data_quality += 0.1
        if analysis_result.get("recommendations"):
            data_quality += 0.1
        if analysis_result.get("supporting_evidence"):
            data_quality += 0.1
        
        return min(1.0, base_confidence + data_quality)
    
    def _calculate_story_confidence(self, analysis_result: Dict[str, Any], 
                                  story_elements: List[StoryElement]) -> float:
        """Calculate overall story confidence"""
        if not story_elements:
            return 0.0
        
        # Average confidence of all elements
        element_confidence = sum(element.confidence for element in story_elements) / len(story_elements)
        
        # Weight with analysis confidence
        analysis_confidence = analysis_result.get("confidence_score", 0.5)
        
        return (element_confidence + analysis_confidence) / 2
