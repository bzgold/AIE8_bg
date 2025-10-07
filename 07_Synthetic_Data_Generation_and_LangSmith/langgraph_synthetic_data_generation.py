"""
LangGraph-based Synthetic Data Generation using Evol Instruct Method
==================================================================

This module implements a sophisticated synthetic data generation system using LangGraph
with the Evol Instruct method, replacing the traditional RAGAS Knowledge Graph approach.

Features:
- Simple Evolution: Basic question generation and evolution
- Multi-Context Evolution: Questions requiring multiple document contexts
- Reasoning Evolution: Complex questions requiring logical reasoning
- Structured outputs for questions, answers, and contexts
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum

import asyncio
from operator import add

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver


class EvolutionType(Enum):
    """Types of question evolution supported by the system."""
    SIMPLE = "simple"
    MULTI_CONTEXT = "multi_context"
    REASONING = "reasoning"


@dataclass
class EvolvedQuestion:
    """Represents an evolved question with metadata."""
    id: str
    question: str
    evolution_type: EvolutionType
    original_question: Optional[str] = None
    evolution_prompt: Optional[str] = None
    difficulty_level: int = 1


@dataclass
class QuestionAnswer:
    """Represents an answer to an evolved question."""
    question_id: str
    answer: str
    confidence_score: float = 0.0
    source_citations: List[str] = None


@dataclass
class QuestionContext:
    """Represents relevant context for an evolved question."""
    question_id: str
    contexts: List[str]
    relevance_scores: List[float] = None
    source_documents: List[str] = None


class SyntheticDataState(TypedDict):
    """State for the LangGraph synthetic data generation workflow."""
    documents: List[Document]
    evolved_questions: List[EvolvedQuestion]
    question_answers: List[QuestionAnswer]
    question_contexts: List[QuestionContext]
    current_evolution_type: EvolutionType
    evolution_count: int
    messages: Annotated[List, add_messages]


class LangGraphSyntheticDataGenerator:
    """
    Main class for generating synthetic data using LangGraph with Evol Instruct method.
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        temperature: float = 0.7
    ):
        """Initialize the synthetic data generator."""
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize prompts for different evolution types
        self._setup_prompts()
        
        # Create the LangGraph workflow
        self._create_graph()
    
    def _setup_prompts(self):
        """Setup prompts for different evolution types."""
        
        # Simple Evolution Prompt
        self.simple_evolution_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at creating evolved questions for synthetic data generation.
            
            Your task is to take a basic question and evolve it into a more sophisticated version using the Evol Instruct method.
            
            Evolution Guidelines:
            1. Make the question more specific and detailed
            2. Add complexity while maintaining clarity
            3. Ensure the question can be answered from the provided context
            4. Make it more natural and conversational
            
            Return your response as JSON with the following structure:
            {
                "evolved_question": "the evolved question",
                "evolution_type": "simple",
                "difficulty_level": 1-5,
                "reasoning": "explanation of the evolution"
            }
            """),
            HumanMessage(content="""Original Question: {original_question}
            
            Context: {context}
            
            Please evolve this question using the Evol Instruct method for simple evolution.""")
        ])
        
        # Multi-Context Evolution Prompt
        self.multi_context_evolution_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at creating multi-context questions for synthetic data generation.
            
            Your task is to evolve a question that requires information from multiple contexts/documents.
            
            Multi-Context Evolution Guidelines:
            1. Create questions that need information from at least 2 different contexts
            2. Make the question require synthesis of information
            3. Add comparative or analytical elements
            4. Ensure the question is answerable from the combined contexts
            
            Return your response as JSON with the following structure:
            {
                "evolved_question": "the evolved question",
                "evolution_type": "multi_context",
                "difficulty_level": 1-5,
                "required_contexts": ["context1", "context2"],
                "reasoning": "explanation of the evolution"
            }
            """),
            HumanMessage(content="""Original Question: {original_question}
            
            Available Contexts: {contexts}
            
            Please evolve this question to require multiple contexts.""")
        ])
        
        # Reasoning Evolution Prompt
        self.reasoning_evolution_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at creating reasoning-based questions for synthetic data generation.
            
            Your task is to evolve a question that requires logical reasoning, analysis, or inference.
            
            Reasoning Evolution Guidelines:
            1. Create questions that require logical deduction
            2. Add analytical or evaluative components
            3. Include "why", "how", or "what if" elements
            4. Make the question require critical thinking
            
            Return your response as JSON with the following structure:
            {
                "evolved_question": "the evolved question",
                "evolution_type": "reasoning",
                "difficulty_level": 1-5,
                "reasoning_type": "deductive|inductive|analytical|evaluative",
                "reasoning": "explanation of the evolution"
            }
            """),
            HumanMessage(content="""Original Question: {original_question}
            
            Context: {context}
            
            Please evolve this question to require logical reasoning.""")
        ])
        
        # Answer Generation Prompt
        self.answer_generation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at generating accurate answers for evolved questions.
            
            Your task is to provide comprehensive, accurate answers based on the given contexts.
            
            Answer Guidelines:
            1. Base your answer strictly on the provided context
            2. Be comprehensive but concise
            3. Include relevant details and examples
            4. If information is insufficient, state what's missing
            5. Provide a confidence score (0.0 to 1.0)
            
            Return your response as JSON with the following structure:
            {
                "answer": "comprehensive answer",
                "confidence_score": 0.0-1.0,
                "source_citations": ["source1", "source2"],
                "missing_information": "what's missing if any"
            }
            """),
            HumanMessage(content="""Question: {question}
            
            Context: {context}
            
            Please provide a comprehensive answer.""")
        ])
        
        # Context Selection Prompt
        self.context_selection_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at selecting relevant contexts for questions.
            
            Your task is to identify and rank the most relevant contexts for answering a question.
            
            Context Selection Guidelines:
            1. Identify contexts that directly relate to the question
            2. Rank contexts by relevance (0.0 to 1.0)
            3. Include multiple contexts if needed
            4. Provide reasoning for your selection
            
            Return your response as JSON with the following structure:
            {
                "relevant_contexts": [
                    {
                        "context": "context text",
                        "relevance_score": 0.0-1.0,
                        "source_document": "document_id"
                    }
                ],
                "reasoning": "explanation of selection"
            }
            """),
            HumanMessage(content="""Question: {question}
            
            Available Contexts: {contexts}
            
            Please select and rank the most relevant contexts.""")
        ])
    
    def _create_graph(self):
        """Create the LangGraph workflow for synthetic data generation."""
        
        # Create the state graph
        workflow = StateGraph(SyntheticDataState)
        
        # Add nodes for each step
        workflow.add_node("initialize", self._initialize_generation)
        workflow.add_node("simple_evolution", self._simple_evolution_node)
        workflow.add_node("multi_context_evolution", self._multi_context_evolution_node)
        workflow.add_node("reasoning_evolution", self._reasoning_evolution_node)
        workflow.add_node("generate_answers", self._generate_answers_node)
        workflow.add_node("select_contexts", self._select_contexts_node)
        workflow.add_node("finalize", self._finalize_generation)
        
        # Define the workflow edges
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "simple_evolution")
        workflow.add_edge("simple_evolution", "multi_context_evolution")
        workflow.add_edge("multi_context_evolution", "reasoning_evolution")
        workflow.add_edge("reasoning_evolution", "generate_answers")
        workflow.add_edge("generate_answers", "select_contexts")
        workflow.add_edge("select_contexts", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile the graph
        memory = MemorySaver()
        self.graph = workflow.compile(checkpointer=memory)
    
    async def _initialize_generation(self, state: SyntheticDataState) -> SyntheticDataState:
        """Initialize the synthetic data generation process."""
        print("🚀 Initializing synthetic data generation...")
        
        # Initialize empty lists
        state["evolved_questions"] = []
        state["question_answers"] = []
        state["question_contexts"] = []
        state["evolution_count"] = 0
        
        # Generate initial questions from documents
        initial_questions = await self._generate_initial_questions(state["documents"])
        
        # Add initial questions to state
        for question in initial_questions:
            evolved_question = EvolvedQuestion(
                id=str(uuid.uuid4()),
                question=question,
                evolution_type=EvolutionType.SIMPLE
            )
            state["evolved_questions"].append(evolved_question)
        
        print(f"✅ Generated {len(initial_questions)} initial questions")
        return state
    
    async def _generate_initial_questions(self, documents: List[Document]) -> List[str]:
        """Generate initial questions from documents."""
        # Combine document content
        combined_content = "\n\n".join([doc.page_content for doc in documents])
        
        initial_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Generate diverse, interesting questions based on the provided document content.
            
            Create questions that:
            1. Cover different aspects of the content
            2. Range from simple to complex
            3. Are answerable from the provided text
            4. Are natural and conversational
            
            Return 5-10 questions as a JSON list of strings."""),
            HumanMessage(content=f"Document Content:\n{combined_content}")
        ])
        
        parser = JsonOutputParser()
        response = await self.llm.ainvoke(initial_prompt.format_messages())
        questions = parser.parse(response.content)
        
        return questions if isinstance(questions, list) else [questions]
    
    async def _simple_evolution_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Perform simple evolution on questions."""
        print("🔄 Performing simple evolution...")
        
        for question in state["evolved_questions"]:
            if question.evolution_type == EvolutionType.SIMPLE:
                # Get relevant context
                context = await self._get_relevant_context(question.question, state["documents"])
                
                # Evolve the question
                evolution_response = await self.llm.ainvoke(
                    self.simple_evolution_prompt.format_messages(
                        original_question=question.question,
                        context=context
                    )
                )
                
                parser = JsonOutputParser()
                evolution_result = parser.parse(evolution_response.content)
                
                # Update the question
                question.question = evolution_result["evolved_question"]
                question.difficulty_level = evolution_result.get("difficulty_level", 1)
                question.evolution_prompt = evolution_result.get("reasoning", "")
        
        print(f"✅ Completed simple evolution for {len(state['evolved_questions'])} questions")
        return state
    
    async def _multi_context_evolution_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Perform multi-context evolution on questions."""
        print("🔄 Performing multi-context evolution...")
        
        # Create new multi-context questions
        multi_context_questions = await self._create_multi_context_questions(state["documents"])
        
        for question_text in multi_context_questions:
            # Get multiple contexts
            contexts = await self._get_multiple_contexts(question_text, state["documents"])
            
            # Evolve the question
            evolution_response = await self.llm.ainvoke(
                self.multi_context_evolution_prompt.format_messages(
                    original_question=question_text,
                    contexts=contexts
                )
            )
            
            parser = JsonOutputParser()
            evolution_result = parser.parse(evolution_response.content)
            
            # Create new evolved question
            evolved_question = EvolvedQuestion(
                id=str(uuid.uuid4()),
                question=evolution_result["evolved_question"],
                evolution_type=EvolutionType.MULTI_CONTEXT,
                original_question=question_text,
                difficulty_level=evolution_result.get("difficulty_level", 2)
            )
            state["evolved_questions"].append(evolved_question)
        
        print(f"✅ Completed multi-context evolution, added {len(multi_context_questions)} questions")
        return state
    
    async def _reasoning_evolution_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Perform reasoning evolution on questions."""
        print("🔄 Performing reasoning evolution...")
        
        # Create new reasoning questions
        reasoning_questions = await self._create_reasoning_questions(state["documents"])
        
        for question_text in reasoning_questions:
            # Get relevant context
            context = await self._get_relevant_context(question_text, state["documents"])
            
            # Evolve the question
            evolution_response = await self.llm.ainvoke(
                self.reasoning_evolution_prompt.format_messages(
                    original_question=question_text,
                    context=context
                )
            )
            
            parser = JsonOutputParser()
            evolution_result = parser.parse(evolution_response.content)
            
            # Create new evolved question
            evolved_question = EvolvedQuestion(
                id=str(uuid.uuid4()),
                question=evolution_result["evolved_question"],
                evolution_type=EvolutionType.REASONING,
                original_question=question_text,
                difficulty_level=evolution_result.get("difficulty_level", 3)
            )
            state["evolved_questions"].append(evolved_question)
        
        print(f"✅ Completed reasoning evolution, added {len(reasoning_questions)} questions")
        return state
    
    async def _generate_answers_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Generate answers for all evolved questions."""
        print("📝 Generating answers for all questions...")
        
        for question in state["evolved_questions"]:
            # Get relevant context
            if question.evolution_type == EvolutionType.MULTI_CONTEXT:
                context = await self._get_multiple_contexts(question.question, state["documents"])
            else:
                context = await self._get_relevant_context(question.question, state["documents"])
            
            # Generate answer
            answer_response = await self.llm.ainvoke(
                self.answer_generation_prompt.format_messages(
                    question=question.question,
                    context=context
                )
            )
            
            parser = JsonOutputParser()
            answer_result = parser.parse(answer_response.content)
            
            # Create question answer
            question_answer = QuestionAnswer(
                question_id=question.id,
                answer=answer_result["answer"],
                confidence_score=answer_result.get("confidence_score", 0.8),
                source_citations=answer_result.get("source_citations", [])
            )
            state["question_answers"].append(question_answer)
        
        print(f"✅ Generated answers for {len(state['evolved_questions'])} questions")
        return state
    
    async def _select_contexts_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Select relevant contexts for all questions."""
        print("🎯 Selecting relevant contexts...")
        
        for question in state["evolved_questions"]:
            # Get all available contexts
            all_contexts = [doc.page_content for doc in state["documents"]]
            
            # Select relevant contexts
            context_response = await self.llm.ainvoke(
                self.context_selection_prompt.format_messages(
                    question=question.question,
                    contexts=all_contexts
                )
            )
            
            parser = JsonOutputParser()
            context_result = parser.parse(context_response.content)
            
            # Create question context
            question_context = QuestionContext(
                question_id=question.id,
                contexts=[ctx["context"] for ctx in context_result["relevant_contexts"]],
                relevance_scores=[ctx["relevance_score"] for ctx in context_result["relevant_contexts"]],
                source_documents=[ctx["source_document"] for ctx in context_result["relevant_contexts"]]
            )
            state["question_contexts"].append(question_context)
        
        print(f"✅ Selected contexts for {len(state['evolved_questions'])} questions")
        return state
    
    async def _finalize_generation(self, state: SyntheticDataState) -> SyntheticDataState:
        """Finalize the synthetic data generation process."""
        print("🏁 Finalizing synthetic data generation...")
        
        state["evolution_count"] = len(state["evolved_questions"])
        
        print(f"✅ Synthetic data generation completed!")
        print(f"📊 Generated {len(state['evolved_questions'])} evolved questions")
        print(f"📝 Generated {len(state['question_answers'])} answers")
        print(f"🎯 Generated {len(state['question_contexts'])} context selections")
        
        return state
    
    async def _get_relevant_context(self, question: str, documents: List[Document]) -> str:
        """Get the most relevant context for a question."""
        # Simple similarity-based context selection
        # In a production system, you might use embeddings for better selection
        
        # For now, return the first document's content
        # This can be enhanced with proper embedding-based retrieval
        return documents[0].page_content if documents else ""
    
    async def _get_multiple_contexts(self, question: str, documents: List[Document]) -> List[str]:
        """Get multiple relevant contexts for a question."""
        # Return multiple document contexts
        return [doc.page_content for doc in documents[:3]]  # First 3 documents
    
    async def _create_multi_context_questions(self, documents: List[Document]) -> List[str]:
        """Create questions that require multiple contexts."""
        multi_context_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Create questions that require information from multiple documents/contexts.
            
            These questions should:
            1. Need information from at least 2 different sources
            2. Require comparison or synthesis
            3. Be answerable from the provided documents
            
            Return 3-5 questions as a JSON list of strings."""),
            HumanMessage(content=f"Documents: {len(documents)} documents available")
        ])
        
        parser = JsonOutputParser()
        response = await self.llm.ainvoke(multi_context_prompt.format_messages())
        questions = parser.parse(response.content)
        
        return questions if isinstance(questions, list) else [questions]
    
    async def _create_reasoning_questions(self, documents: List[Document]) -> List[str]:
        """Create questions that require logical reasoning."""
        reasoning_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Create questions that require logical reasoning, analysis, or inference.
            
            These questions should:
            1. Require "why", "how", or "what if" thinking
            2. Need analysis or evaluation
            3. Require logical deduction
            4. Be answerable from the provided documents
            
            Return 3-5 questions as a JSON list of strings."""),
            HumanMessage(content=f"Documents: {len(documents)} documents available")
        ])
        
        parser = JsonOutputParser()
        response = await self.llm.ainvoke(reasoning_prompt.format_messages())
        questions = parser.parse(response.content)
        
        return questions if isinstance(questions, list) else [questions]
    
    async def generate_synthetic_data(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Main method to generate synthetic data from a list of LangChain documents.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            Dictionary containing evolved questions, answers, and contexts
        """
        print("🎯 Starting LangGraph-based synthetic data generation...")
        
        # Initialize state
        initial_state = SyntheticDataState(
            documents=documents,
            evolved_questions=[],
            question_answers=[],
            question_contexts=[],
            current_evolution_type=EvolutionType.SIMPLE,
            evolution_count=0,
            messages=[]
        )
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        # Format the output
        return self._format_output(final_state)
    
    def _format_output(self, state: SyntheticDataState) -> Dict[str, Any]:
        """Format the final output in the required structure."""
        
        # Format evolved questions
        evolved_questions = []
        for q in state["evolved_questions"]:
            evolved_questions.append({
                "id": q.id,
                "question": q.question,
                "evolution_type": q.evolution_type.value,
                "original_question": q.original_question,
                "difficulty_level": q.difficulty_level,
                "evolution_prompt": q.evolution_prompt
            })
        
        # Format question answers
        question_answers = []
        for a in state["question_answers"]:
            question_answers.append({
                "question_id": a.question_id,
                "answer": a.answer,
                "confidence_score": a.confidence_score,
                "source_citations": a.source_citations or []
            })
        
        # Format question contexts
        question_contexts = []
        for c in state["question_contexts"]:
            question_contexts.append({
                "question_id": c.question_id,
                "contexts": c.contexts,
                "relevance_scores": c.relevance_scores or [],
                "source_documents": c.source_documents or []
            })
        
        return {
            "evolved_questions": evolved_questions,
            "question_answers": question_answers,
            "question_contexts": question_contexts,
            "summary": {
                "total_questions": len(evolved_questions),
                "total_answers": len(question_answers),
                "total_contexts": len(question_contexts),
                "evolution_types": {
                    "simple": len([q for q in evolved_questions if q["evolution_type"] == "simple"]),
                    "multi_context": len([q for q in evolved_questions if q["evolution_type"] == "multi_context"]),
                    "reasoning": len([q for q in evolved_questions if q["evolution_type"] == "reasoning"])
                }
            }
        }


# Example usage and testing
async def main():
    """Example usage of the LangGraph synthetic data generator."""
    
    # Sample documents (replace with your actual documents)
    sample_documents = [
        Document(
            page_content="Artificial Intelligence (AI) is transforming various industries including healthcare, finance, and transportation. Machine learning algorithms can analyze large datasets to identify patterns and make predictions.",
            metadata={"source": "ai_overview.txt", "page": 1}
        ),
        Document(
            page_content="Large Language Models (LLMs) like GPT-4 have revolutionized natural language processing. These models can understand context, generate human-like text, and perform various language tasks.",
            metadata={"source": "llm_overview.txt", "page": 1}
        ),
        Document(
            page_content="The implementation of AI systems requires careful consideration of ethics, bias, and fairness. Responsible AI development involves ensuring transparency, accountability, and avoiding harmful biases.",
            metadata={"source": "ai_ethics.txt", "page": 1}
        )
    ]
    
    # Initialize the generator
    generator = LangGraphSyntheticDataGenerator()
    
    # Generate synthetic data
    try:
        result = await generator.generate_synthetic_data(sample_documents)
        
        print("\n" + "="*80)
        print("🎉 SYNTHETIC DATA GENERATION COMPLETED!")
        print("="*80)
        
        # Display results
        print(f"\n📊 SUMMARY:")
        print(f"Total Questions Generated: {result['summary']['total_questions']}")
        print(f"Evolution Types: {result['summary']['evolution_types']}")
        
        print(f"\n🔍 SAMPLE EVOLVED QUESTIONS:")
        for i, q in enumerate(result['evolved_questions'][:3]):
            print(f"{i+1}. [{q['evolution_type'].upper()}] {q['question']}")
        
        print(f"\n💡 SAMPLE ANSWERS:")
        for i, a in enumerate(result['question_answers'][:3]):
            print(f"{i+1}. QID: {a['question_id'][:8]}... - {a['answer'][:100]}...")
        
        print(f"\n🎯 SAMPLE CONTEXTS:")
        for i, c in enumerate(result['question_contexts'][:3]):
            print(f"{i+1}. QID: {c['question_id'][:8]}... - {len(c['contexts'])} contexts")
        
        # Save results to file
        with open("synthetic_data_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Results saved to 'synthetic_data_results.json'")
        
    except Exception as e:
        print(f"❌ Error during synthetic data generation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
