# Open Deep Research - Call Stack Quick Reference

## 📋 Table of Contents
1. [High-Level Overview](#high-level-overview)
2. [Main Execution Path](#main-execution-path)
3. [Key Function Signatures](#key-function-signatures)
4. [Parallel Execution Points](#parallel-execution-points)
5. [Error Handling Paths](#error-handling-paths)
6. [Configuration Flow](#configuration-flow)
7. [State Management](#state-management)

---

## High-Level Overview

### The 3-Layer Architecture

```
┌─────────────────────────────────────────┐
│  MAIN GRAPH (Top Level)                 │
│  • Entry point for user requests        │
│  • Clarification & Report Generation    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  SUPERVISOR SUBGRAPH (Middle Level)     │
│  • Planning & Delegation                │
│  • Manages multiple researchers         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  RESEARCHER SUBGRAPH (Bottom Level)     │
│  • Individual research execution        │
│  • Search & Synthesis                   │
└─────────────────────────────────────────┘
```

### Core Components
- **8 Main Nodes**: 4 in main graph, 2 in supervisor, 2 in researcher
- **3 Subgraphs**: Main deep_researcher, supervisor_subgraph, researcher_subgraph
- **3 Levels of Parallelism**: Researchers, Tool Calls, Summarizations

---

## Main Execution Path

### Sequential Flow (Happy Path)

```python
# 1. USER INPUT
user_message = "Research how people use AI"

# 2. CLARIFY (if enabled)
clarify_with_user(state, config)
    → LLM: Analyze request clarity
    → Decision: Continue or Ask Question

# 3. RESEARCH BRIEF
write_research_brief(state, config)
    → LLM: Transform to structured brief
    → Initialize supervisor

# 4. SUPERVISOR LOOP (1-6 iterations)
supervisor(state, config)
    → LLM: Plan delegation strategy
    → Tool Calls: [ConductResearch, think_tool, ResearchComplete]

supervisor_tools(state, config)
    → Execute reflections
    → Spawn N researchers (parallel)
    → Aggregate results
    → Loop or Exit

# 5. RESEARCHER LOOP (per researcher, 1-10 iterations)
researcher(state, config)
    → LLM: Generate search queries
    → Tool Calls: [tavily_search, think_tool, ResearchComplete]

researcher_tools(state, config)
    → Execute searches (parallel)
    → Process reflections
    → Loop or Compress

compress_research(state, config)
    → LLM: Synthesize findings
    → Return compressed research

# 6. FINAL REPORT
final_report_generation(state, config)
    → LLM: Generate comprehensive report
    → Return to user
```

---

## Key Function Signatures

### Main Graph Nodes

```python
async def clarify_with_user(
    state: AgentState, 
    config: RunnableConfig
) -> Command[Literal["write_research_brief", "__end__"]]:
    """Analyze and optionally ask clarifying questions."""
    # File: deep_researcher.py:60-115
    # Returns: Command to next node or END

async def write_research_brief(
    state: AgentState, 
    config: RunnableConfig
) -> Command[Literal["research_supervisor"]]:
    """Transform messages into structured research brief."""
    # File: deep_researcher.py:118-175
    # Returns: Command to supervisor with brief

async def final_report_generation(
    state: AgentState, 
    config: RunnableConfig
) -> dict:
    """Generate final comprehensive report."""
    # File: deep_researcher.py:607-697
    # Returns: {"final_report": str, "messages": [AIMessage]}
```

### Supervisor Subgraph Nodes

```python
async def supervisor(
    state: SupervisorState, 
    config: RunnableConfig
) -> Command[Literal["supervisor_tools"]]:
    """Plan and delegate research tasks."""
    # File: deep_researcher.py:178-223
    # Returns: Command with tool calls

async def supervisor_tools(
    state: SupervisorState, 
    config: RunnableConfig
) -> Command[Literal["supervisor", "__end__"]]:
    """Execute supervisor tool calls and spawn researchers."""
    # File: deep_researcher.py:225-349
    # Returns: Command to loop or end
```

### Researcher Subgraph Nodes

```python
async def researcher(
    state: ResearcherState, 
    config: RunnableConfig
) -> Command[Literal["researcher_tools"]]:
    """Conduct focused research on specific topic."""
    # File: deep_researcher.py:365-424
    # Returns: Command with tool calls

async def researcher_tools(
    state: ResearcherState, 
    config: RunnableConfig
) -> Command[Literal["researcher", "compress_research"]]:
    """Execute research tool calls."""
    # File: deep_researcher.py:435-509
    # Returns: Command to loop or compress

async def compress_research(
    state: ResearcherState, 
    config: RunnableConfig
) -> dict:
    """Synthesize research findings."""
    # File: deep_researcher.py:511-585
    # Returns: {"compressed_research": str, "raw_notes": [str]}
```

### Key Utility Functions

```python
async def tavily_search(
    queries: List[str],
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    config: RunnableConfig = None
) -> str:
    """Search and summarize web results."""
    # File: utils.py:43-136
    # Returns: Formatted search results with summaries

async def get_all_tools(config: RunnableConfig) -> list[BaseTool]:
    """Assemble complete toolkit."""
    # File: utils.py:569-597
    # Returns: [ResearchComplete, think_tool, search_tools, mcp_tools]

def is_token_limit_exceeded(
    exception: Exception, 
    model_name: str = None
) -> bool:
    """Detect token limit errors."""
    # File: utils.py:665-701
    # Returns: True if token limit exceeded
```

---

## Parallel Execution Points

### Level 1: Multiple Researchers (Supervisor Level)

```python
# In supervisor_tools()
research_tasks = [
    researcher_subgraph.ainvoke({
        "researcher_messages": [HumanMessage(content=topic)],
        "research_topic": topic
    }, config) 
    for topic in research_topics[:max_concurrent_research_units]
]

results = await asyncio.gather(*research_tasks)
# Default: max 5 researchers in parallel
```

**Location**: `deep_researcher.py:295-305`  
**Control**: `max_concurrent_research_units` (default: 5)

### Level 2: Multiple Tool Calls (Researcher Level)

```python
# In researcher_tools()
tool_execution_tasks = [
    execute_tool_safely(tools_by_name[tc["name"]], tc["args"], config) 
    for tc in tool_calls
]

observations = await asyncio.gather(*tool_execution_tasks)
# All tool calls execute in parallel
```

**Location**: `deep_researcher.py:475-479`  
**Control**: Number of tool calls from LLM

### Level 3: Multiple Summarizations (Search Level)

```python
# In tavily_search()
summarization_tasks = [
    summarize_webpage(model, result['raw_content'][:max_chars])
    for result in unique_results.values()
    if result.get("raw_content")
]

summaries = await asyncio.gather(*summarization_tasks)
# All page summarizations execute in parallel
```

**Location**: `utils.py:100-110`  
**Control**: Number of unique search results

---

## Error Handling Paths

### Token Limit Exceeded

#### Detection
```python
is_token_limit_exceeded(exception, model_name)
    ├─ Check provider (OpenAI/Anthropic/Gemini)
    ├─ Check error codes and types
    └─ Return True/False
```
**Location**: `utils.py:665-701`

#### Recovery in compress_research()
```python
try:
    response = await model.ainvoke(messages)
except Exception as e:
    if is_token_limit_exceeded(e, model):
        # Remove messages up to last AI message
        messages = remove_up_to_last_ai_message(messages)
        continue  # Retry (max 3 attempts)
```
**Location**: `deep_researcher.py:565-574`

#### Recovery in final_report_generation()
```python
try:
    report = await model.ainvoke([HumanMessage(prompt)])
except Exception as e:
    if is_token_limit_exceeded(e, model):
        # Get token limit and truncate findings
        token_limit = get_model_token_limit(model)
        findings_limit = token_limit * 4  # chars
        findings = findings[:findings_limit]
        # Reduce by 10% on subsequent retries
        findings_limit = int(findings_limit * 0.9)
        continue  # Retry (max 3 attempts)
```
**Location**: `deep_researcher.py:661-683`

### MCP Tool Authentication Errors

```python
# In wrap_mcp_authenticate_tool()
try:
    return await original_coroutine(**kwargs)
except BaseException as error:
    mcp_error = _find_mcp_error_in_exception_chain(error)
    if mcp_error and error_code == -32003:  # Interaction required
        message = error_data.get("message", {}).get("text")
        url = error_data.get("url")
        raise ToolException(f"{message} {url}")
```
**Location**: `utils.py:396-443`

---

## Configuration Flow

### Loading Configuration

```python
# In any node
configurable = Configuration.from_runnable_config(config)

# Access settings
model = configurable.research_model  # "anthropic:claude-sonnet-4-20250514"
max_tokens = configurable.research_model_max_tokens  # 10000
search_api = configurable.search_api  # SearchAPI.TAVILY
max_concurrent = configurable.max_concurrent_research_units  # 5
```

**Location**: `configuration.py:130-159`

### Configuration Structure

```python
config = {
    "configurable": {
        # Model Settings
        "research_model": "anthropic:claude-sonnet-4-20250514",
        "research_model_max_tokens": 10000,
        "compression_model": "anthropic:claude-sonnet-4-20250514",
        "compression_model_max_tokens": 8192,
        "final_report_model": "anthropic:claude-sonnet-4-20250514",
        "final_report_model_max_tokens": 10000,
        "summarization_model": "anthropic:claude-sonnet-4-20250514",
        "summarization_model_max_tokens": 8192,
        
        # Research Behavior
        "allow_clarification": True,
        "max_concurrent_research_units": 5,
        "max_researcher_iterations": 6,
        "max_react_tool_calls": 10,
        
        # Search Configuration
        "search_api": "tavily",  # or "anthropic", "openai", "none"
        "max_content_length": 50000,
        
        # Thread ID
        "thread_id": "uuid-string"
    }
}
```

### API Key Resolution

```python
def get_api_key_for_model(model_name: str, config: RunnableConfig):
    """Get API key from config or environment."""
    # Check environment variable GET_API_KEYS_FROM_CONFIG
    if os.getenv("GET_API_KEYS_FROM_CONFIG") == "true":
        # Get from config.configurable.apiKeys
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if model_name.startswith("openai:"):
            return api_keys.get("OPENAI_API_KEY")
        elif model_name.startswith("anthropic:"):
            return api_keys.get("ANTHROPIC_API_KEY")
    else:
        # Get from environment variables
        if model_name.startswith("openai:"):
            return os.getenv("OPENAI_API_KEY")
        elif model_name.startswith("anthropic:"):
            return os.getenv("ANTHROPIC_API_KEY")
```

**Location**: `utils.py:892-914`

---

## State Management

### State Hierarchy

```python
# Top Level
class AgentState(MessagesState):
    supervisor_messages: list[MessageLikeRepresentation]  # override_reducer
    research_brief: Optional[str]
    raw_notes: list[str]  # override_reducer
    notes: list[str]  # override_reducer
    final_report: str

# Middle Level (Subgraph)
class SupervisorState(TypedDict):
    supervisor_messages: list[MessageLikeRepresentation]  # override_reducer
    research_brief: str
    notes: list[str]  # override_reducer
    research_iterations: int
    raw_notes: list[str]  # override_reducer

# Bottom Level (Subgraph)
class ResearcherState(TypedDict):
    researcher_messages: list[MessageLikeRepresentation]  # operator.add
    tool_call_iterations: int
    research_topic: str
    compressed_research: str
    raw_notes: list[str]  # override_reducer
```

**Location**: `state.py:55-96`

### Override Reducer

```python
def override_reducer(current_value, new_value):
    """Allow overriding entire list instead of appending."""
    if isinstance(new_value, dict) and new_value.get("type") == "override":
        return new_value.get("value", new_value)
    else:
        return operator.add(current_value, new_value)
```

**Usage Example**:
```python
# Append to supervisor_messages (default)
update = {"supervisor_messages": [new_message]}

# Override supervisor_messages completely
update = {
    "supervisor_messages": {
        "type": "override",
        "value": [SystemMessage(...), HumanMessage(...)]
    }
}
```

**Location**: `state.py:55-60`

---

## Call Depth Analysis

### Maximum Call Depth Example

```
USER
 └─ deep_researcher.astream()                    [Depth 1]
     └─ supervisor_subgraph.ainvoke()            [Depth 2]
         └─ supervisor_tools()                   [Depth 3]
             └─ researcher_subgraph.ainvoke()    [Depth 4]
                 └─ researcher_tools()           [Depth 5]
                     └─ tavily_search()          [Depth 6]
                         └─ summarize_webpage()  [Depth 7]
                             └─ model.ainvoke()  [Depth 8]
                                 └─ LLM API      [Depth 9]
```

**Maximum Depth**: 9 levels

### Typical Call Paths

#### Path 1: Clarification → Brief → Research → Report
```
clarify_with_user → write_research_brief → supervisor_subgraph → final_report_generation
```
**Nodes**: 4 (+ supervisor and researcher subgraphs)

#### Path 2: Skip Clarification
```
write_research_brief → supervisor_subgraph → final_report_generation
```
**Nodes**: 3 (+ supervisor and researcher subgraphs)

---

## LLM Call Inventory

### Typical Execution (3 researchers, 2 supervisor iterations)

| Phase | Calls | Description |
|-------|-------|-------------|
| Clarification | 1 | Analyze if clarification needed |
| Research Brief | 1 | Generate structured brief |
| Supervisor Iteration 1 | 1 | Plan first delegation |
| Researcher 1 | 3 | 3 research iterations |
| Researcher 1 Searches | 6 | 2 searches × 3 pages each |
| Researcher 1 Compress | 1 | Synthesize findings |
| Researcher 2 | 3 | 3 research iterations |
| Researcher 2 Searches | 6 | 2 searches × 3 pages each |
| Researcher 2 Compress | 1 | Synthesize findings |
| Researcher 3 | 3 | 3 research iterations |
| Researcher 3 Searches | 6 | 2 searches × 3 pages each |
| Researcher 3 Compress | 1 | Synthesize findings |
| Supervisor Iteration 2 | 1 | Review and complete |
| Final Report | 1 | Generate final report |
| **TOTAL** | **35** | **Total LLM API calls** |

### Cost Estimation Formula

```python
total_calls = (
    1  # clarification
    + 1  # research brief
    + supervisor_iterations  # supervisor planning
    + (num_researchers * researcher_iterations)  # research calls
    + (num_researchers * searches_per_researcher * pages_per_search)  # summarizations
    + num_researchers  # compression calls
    + 1  # final report
)

# Example: 3 researchers, 2 supervisor iters, 3 research iters, 2 searches, 3 pages
total_calls = 1 + 1 + 2 + (3*3) + (3*2*3) + 3 + 1 = 35 calls
```

---

## Quick Troubleshooting

### Issue: Token Limit Exceeded

**Symptoms**: 
- Error mentioning "token", "context", "length"
- "prompt is too long" (Anthropic)
- ResourceExhausted (Gemini)

**Check**:
1. `is_token_limit_exceeded()` in utils.py:665-701
2. Retry logic in `compress_research()` (deep_researcher.py:565-574)
3. Retry logic in `final_report_generation()` (deep_researcher.py:661-683)

**Solution**:
- Increase `max_content_length` in config (default: 50000)
- Reduce `max_researcher_iterations` (default: 6)
- Use models with larger context windows

### Issue: Too Many Concurrent Requests

**Symptoms**:
- Rate limit errors
- Timeouts

**Check**:
- `max_concurrent_research_units` in config (default: 5)

**Solution**:
```python
config = {
    "configurable": {
        "max_concurrent_research_units": 2,  # Reduce parallelism
        # ...
    }
}
```

### Issue: Research Not Deep Enough

**Symptoms**:
- Shallow results
- Missing information

**Check**:
- `max_researcher_iterations` (default: 6)
- `max_react_tool_calls` per researcher (default: 10)

**Solution**:
```python
config = {
    "configurable": {
        "max_researcher_iterations": 8,  # More supervisor iterations
        "max_react_tool_calls": 15,      # More searches per researcher
        # ...
    }
}
```

### Issue: MCP Tools Not Working

**Symptoms**:
- Tools not appearing
- Authentication errors

**Check**:
1. MCP config in `load_mcp_tools()` (utils.py:449-524)
2. Token fetching in `fetch_tokens()` (utils.py:352-383)
3. Authentication wrapper (utils.py:385-447)

**Solution**:
- Verify `mcp_config.url` is correct
- Check `mcp_config.tools` list matches available tools
- Ensure authentication tokens are valid

---

## File Reference Map

| File | Lines | Purpose |
|------|-------|---------|
| `deep_researcher.py` | 719 | Main orchestration & node functions |
| `utils.py` | 926 | Tools, utilities, error handling |
| `state.py` | 96 | State definitions & reducers |
| `configuration.py` | 252 | Configuration management |
| `prompts.py` | 308 | Prompt templates |

### Quick File Navigation

```python
# Node implementations
deep_researcher.py:60-115     # clarify_with_user
deep_researcher.py:118-175    # write_research_brief
deep_researcher.py:178-223    # supervisor
deep_researcher.py:225-349    # supervisor_tools
deep_researcher.py:365-424    # researcher
deep_researcher.py:435-509    # researcher_tools
deep_researcher.py:511-585    # compress_research
deep_researcher.py:607-697    # final_report_generation

# Graph construction
deep_researcher.py:351-363    # supervisor_subgraph
deep_researcher.py:587-605    # researcher_subgraph
deep_researcher.py:699-719    # deep_researcher (main graph)

# Tools
utils.py:43-136               # tavily_search
utils.py:219-244              # think_tool
utils.py:569-597              # get_all_tools
utils.py:449-524              # load_mcp_tools

# Error handling
utils.py:665-701              # is_token_limit_exceeded
utils.py:703-785              # Provider-specific checks
utils.py:848-866              # remove_up_to_last_ai_message

# Configuration
configuration.py:130-159      # from_runnable_config
utils.py:892-914              # get_api_key_for_model
```

---

## Summary Checklist

### Execution Flow
- [ ] User input → Main graph
- [ ] Clarification (optional) → Research brief
- [ ] Supervisor loop (1-6 iterations)
- [ ] Parallel researchers (1-5 concurrent)
- [ ] Each researcher loop (1-10 tool calls)
- [ ] Compression → Aggregation
- [ ] Final report generation

### Parallel Execution
- [ ] Level 1: Multiple researchers (supervisor_tools)
- [ ] Level 2: Multiple tool calls (researcher_tools)
- [ ] Level 3: Multiple summarizations (tavily_search)

### Error Handling
- [ ] Token limit detection (all providers)
- [ ] Retry with truncation (compress_research)
- [ ] Progressive reduction (final_report_generation)
- [ ] MCP authentication errors

### Configuration
- [ ] Model settings (4 models configurable)
- [ ] Research behavior (3 key limits)
- [ ] Search API (4 options)
- [ ] API key resolution (env or config)

---

## Additional Resources

- **Full Call Stack**: See `CALL_STACK.md`
- **Visual Diagrams**: See `CALL_STACK_DIAGRAM.md`
- **Architecture Overview**: See notebook cells 1-2
- **Original Repo**: [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research)

---

Generated: October 14, 2025  
Version: 1.0  
System: Open Deep Research (LangGraph)

