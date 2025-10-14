# Open Deep Research - Complete Call Stack

## Overview
This document provides a complete call stack visualization showing how functions are called throughout the Deep Research system execution.

---

## Main Execution Flow

### Entry Point
```
USER INPUT
    ↓
deep_researcher.astream()
    ├─ config: Configuration
    └─ state: {"messages": [user_message]}
```

---

## Level 1: Main Graph Nodes

### 1. clarify_with_user()
**File**: `open_deep_library/deep_researcher.py` (lines 60-115)

```
clarify_with_user(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ get_api_key_for_model(model, config)
    │   └─ utils.py:892-914
    │       └─ os.getenv()
    │
    ├─ configurable_model.with_structured_output(ClarifyWithUser)
    │   └─ langchain.chat_models.init_chat_model()
    │
    ├─ get_today_str()
    │   └─ utils.py:872-879
    │       └─ datetime.now()
    │
    ├─ get_buffer_string(messages)
    │   └─ langchain_core.messages.get_buffer_string()
    │
    ├─ clarification_model.ainvoke([HumanMessage])
    │   ├─ LLM API Call (Anthropic/OpenAI)
    │   └─ Returns: ClarifyWithUser
    │
    └─ Command(goto="write_research_brief" | END)
```

**Decision Points**:
- If `allow_clarification=False` → skip to `write_research_brief`
- If `need_clarification=True` → END with question
- If `need_clarification=False` → proceed to `write_research_brief`

---

### 2. write_research_brief()
**File**: `open_deep_library/deep_researcher.py` (lines 118-175)

```
write_research_brief(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ get_api_key_for_model(model, config)
    │   └─ utils.py:892-914
    │
    ├─ configurable_model.with_structured_output(ResearchQuestion)
    │   └─ langchain.chat_models.init_chat_model()
    │
    ├─ get_today_str()
    │   └─ utils.py:872-879
    │
    ├─ get_buffer_string(state.messages)
    │   └─ langchain_core.messages.get_buffer_string()
    │
    ├─ research_model.ainvoke([HumanMessage])
    │   ├─ LLM API Call
    │   └─ Returns: ResearchQuestion
    │
    └─ Command(goto="research_supervisor")
        └─ update: {
            "research_brief": response.research_brief,
            "supervisor_messages": [SystemMessage, HumanMessage]
        }
```

---

### 3. research_supervisor (supervisor_subgraph)
**File**: `open_deep_library/deep_researcher.py` (lines 351-363)

This is a compiled subgraph containing:

#### 3a. supervisor()
**File**: `open_deep_library/deep_researcher.py` (lines 178-223)

```
supervisor(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ get_api_key_for_model(model, config)
    │   └─ utils.py:892-914
    │
    ├─ configurable_model.bind_tools([ConductResearch, ResearchComplete, think_tool])
    │   └─ langchain.chat_models.init_chat_model()
    │
    ├─ research_model.ainvoke(supervisor_messages)
    │   ├─ LLM API Call with tools
    │   └─ Returns: AIMessage with tool_calls
    │
    └─ Command(goto="supervisor_tools")
        └─ update: {
            "supervisor_messages": [response],
            "research_iterations": count + 1
        }
```

#### 3b. supervisor_tools()
**File**: `open_deep_library/deep_researcher.py` (lines 225-349)

```
supervisor_tools(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ Check exit conditions:
    │   ├─ exceeded_iterations?
    │   ├─ no_tool_calls?
    │   └─ research_complete_called?
    │   → If YES: Command(goto=END)
    │
    ├─ Process think_tool calls:
    │   └─ Create ToolMessage for each reflection
    │
    ├─ Process ConductResearch calls:
    │   │
    │   ├─ Limit to max_concurrent_research_units
    │   │
    │   ├─ FOR EACH research delegation:
    │   │   │
    │   │   ├─ researcher_subgraph.ainvoke()  ← SPAWN RESEARCHER
    │   │   │   └─ See "Level 2: Researcher Subgraph" below
    │   │   │
    │   │   └─ Returns: {
    │   │       "compressed_research": str,
    │   │       "raw_notes": [str]
    │   │   }
    │   │
    │   ├─ asyncio.gather(*research_tasks)  ← PARALLEL EXECUTION
    │   │
    │   ├─ Create ToolMessage for each result
    │   │
    │   ├─ Aggregate raw_notes from all researchers
    │   │
    │   └─ Error handling:
    │       └─ is_token_limit_exceeded(e, model)
    │           └─ utils.py:665-701
    │
    └─ Command(goto="supervisor" | END)
        └─ update: {
            "supervisor_messages": [tool_messages],
            "raw_notes": [aggregated_notes]
        }
```

**Loop**: `supervisor` ↔ `supervisor_tools` (until max iterations or ResearchComplete)

---

## Level 2: Researcher Subgraph

### researcher_subgraph Execution
**File**: `open_deep_library/deep_researcher.py` (lines 587-605)

This subgraph is spawned by `supervisor_tools` for each ConductResearch call.

#### 2a. researcher()
**File**: `open_deep_library/deep_researcher.py` (lines 365-424)

```
researcher(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ get_all_tools(config)
    │   └─ utils.py:569-597
    │       │
    │       ├─ Start with: [ResearchComplete, think_tool]
    │       │
    │       ├─ get_search_tool(search_api)
    │       │   └─ utils.py:531-567
    │       │       ├─ If ANTHROPIC: return [{"type": "web_search_20250305"}]
    │       │       ├─ If OPENAI: return [{"type": "web_search_preview"}]
    │       │       ├─ If TAVILY: return [tavily_search]
    │       │       └─ If NONE: return []
    │       │
    │       └─ load_mcp_tools(config, existing_tool_names)
    │           └─ utils.py:449-524
    │               │
    │               ├─ fetch_tokens(config)
    │               │   └─ utils.py:352-383
    │               │       ├─ get_tokens(config)
    │               │       │   └─ utils.py:293-329
    │               │       │       └─ get_store().aget()
    │               │       │
    │               │       └─ get_mcp_access_token(token, url)
    │               │           └─ utils.py:250-291
    │               │               └─ aiohttp.ClientSession().post()
    │               │
    │               ├─ MultiServerMCPClient(mcp_server_config)
    │               │   └─ langchain_mcp_adapters.client
    │               │
    │               ├─ client.get_tools()
    │               │
    │               └─ wrap_mcp_authenticate_tool(tool)
    │                   └─ utils.py:385-447
    │
    ├─ get_today_str()
    │   └─ utils.py:872-879
    │
    ├─ configurable_model.bind_tools(tools)
    │   └─ langchain.chat_models.init_chat_model()
    │
    ├─ research_model.ainvoke([SystemMessage, ...researcher_messages])
    │   ├─ LLM API Call with tools
    │   └─ Returns: AIMessage with tool_calls
    │
    └─ Command(goto="researcher_tools")
        └─ update: {
            "researcher_messages": [response],
            "tool_call_iterations": count + 1
        }
```

#### 2b. researcher_tools()
**File**: `open_deep_library/deep_researcher.py` (lines 435-509)

```
researcher_tools(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ Check early exit conditions:
    │   ├─ openai_websearch_called(message)
    │   │   └─ utils.py:639-658
    │   │
    │   ├─ anthropic_websearch_called(message)
    │   │   └─ utils.py:607-637
    │   │
    │   └─ If no tool calls and no native search:
    │       → Command(goto="compress_research")
    │
    ├─ get_all_tools(config)
    │   └─ (See detailed call tree above in researcher())
    │
    ├─ FOR EACH tool_call:
    │   │
    │   ├─ execute_tool_safely(tool, args, config)
    │   │   └─ deep_researcher.py:427-432
    │   │       │
    │   │       └─ TOOL EXECUTION (depends on tool type):
    │   │           │
    │   │           ├─ IF tavily_search:
    │   │           │   └─ tavily_search(queries, config)
    │   │           │       └─ utils.py:43-136
    │   │           │           │
    │   │           │           ├─ tavily_search_async(queries, config)
    │   │           │           │   └─ utils.py:138-173
    │   │           │           │       ├─ AsyncTavilyClient(api_key)
    │   │           │           │       │   └─ get_tavily_api_key(config)
    │   │           │           │       │       └─ utils.py:916-925
    │   │           │           │       │
    │   │           │           │       ├─ tavily_client.search(query)  ← API CALL
    │   │           │           │       │
    │   │           │           │       └─ asyncio.gather(*search_tasks)
    │   │           │           │
    │   │           │           ├─ Deduplicate results by URL
    │   │           │           │
    │   │           │           ├─ Configuration.from_runnable_config(config)
    │   │           │           │
    │   │           │           ├─ init_chat_model(summarization_model)
    │   │           │           │   └─ langchain.chat_models.init_chat_model()
    │   │           │           │
    │   │           │           ├─ FOR EACH unique result:
    │   │           │           │   │
    │   │           │           │   └─ summarize_webpage(model, content)
    │   │           │           │       └─ utils.py:175-213
    │   │           │           │           │
    │   │           │           │           ├─ get_today_str()
    │   │           │           │           │
    │   │           │           │           ├─ asyncio.wait_for(
    │   │           │           │           │   model.ainvoke([HumanMessage]),
    │   │           │           │           │   timeout=60.0
    │   │           │           │           │   )
    │   │           │           │           │   ├─ LLM API Call
    │   │           │           │           │   └─ Returns: Summary
    │   │           │           │           │
    │   │           │           │           └─ Format as:
    │   │           │           │               "<summary>...</summary>
    │   │           │           │                <key_excerpts>...</key_excerpts>"
    │   │           │           │
    │   │           │           ├─ asyncio.gather(*summarization_tasks)
    │   │           │           │
    │   │           │           └─ Format final output string
    │   │           │
    │   │           ├─ IF think_tool:
    │   │           │   └─ think_tool(reflection)
    │   │           │       └─ utils.py:219-244
    │   │           │           └─ Return: f"Reflection recorded: {reflection}"
    │   │           │
    │   │           ├─ IF ResearchComplete:
    │   │           │   └─ tool(ResearchComplete)
    │   │           │       └─ Returns empty/completion signal
    │   │           │
    │   │           └─ IF MCP tool:
    │   │               └─ (MCP tool execution with authentication wrapper)
    │   │
    │   └─ asyncio.gather(*tool_execution_tasks)  ← PARALLEL TOOL EXECUTION
    │
    ├─ Create ToolMessage for each result
    │
    ├─ Check late exit conditions:
    │   ├─ exceeded_iterations (> max_react_tool_calls)?
    │   └─ research_complete_called?
    │   → If YES: Command(goto="compress_research")
    │
    └─ Command(goto="researcher" | "compress_research")
        └─ update: {"researcher_messages": [tool_outputs]}
```

**Loop**: `researcher` ↔ `researcher_tools` (until max iterations or ResearchComplete)

#### 2c. compress_research()
**File**: `open_deep_library/deep_researcher.py` (lines 511-585)

```
compress_research(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ get_api_key_for_model(compression_model, config)
    │   └─ utils.py:892-914
    │
    ├─ configurable_model.with_config(compression_model_config)
    │   └─ langchain.chat_models.init_chat_model()
    │
    ├─ Append HumanMessage(compress_research_simple_human_message)
    │
    ├─ RETRY LOOP (max 3 attempts):
    │   │
    │   ├─ get_today_str()
    │   │   └─ utils.py:872-879
    │   │
    │   ├─ synthesizer_model.ainvoke([SystemMessage, ...messages])
    │   │   ├─ LLM API Call
    │   │   └─ Returns: AIMessage with compressed research
    │   │
    │   ├─ filter_messages(messages, include_types=["tool", "ai"])
    │   │   └─ langchain_core.messages.filter_messages()
    │   │
    │   ├─ Extract raw notes from filtered messages
    │   │
    │   └─ ERROR HANDLING:
    │       │
    │       ├─ is_token_limit_exceeded(e, model)
    │       │   └─ utils.py:665-701
    │       │       ├─ _check_openai_token_limit()
    │       │       ├─ _check_anthropic_token_limit()
    │       │       └─ _check_gemini_token_limit()
    │       │
    │       └─ If token limit exceeded:
    │           └─ remove_up_to_last_ai_message(messages)
    │               └─ utils.py:848-866
    │
    └─ Returns: {
        "compressed_research": str,
        "raw_notes": [str]
    }
```

---

### 4. final_report_generation()
**File**: `open_deep_library/deep_researcher.py` (lines 607-697)

```
final_report_generation(state, config)
    │
    ├─ Configuration.from_runnable_config(config)
    │
    ├─ Extract notes from state
    │   └─ findings = "\n".join(state.notes)
    │
    ├─ get_api_key_for_model(final_report_model, config)
    │   └─ utils.py:892-914
    │
    ├─ configurable_model.with_config(writer_model_config)
    │   └─ langchain.chat_models.init_chat_model()
    │
    ├─ RETRY LOOP (max 3 attempts):
    │   │
    │   ├─ get_today_str()
    │   │   └─ utils.py:872-879
    │   │
    │   ├─ get_buffer_string(state.messages)
    │   │   └─ langchain_core.messages.get_buffer_string()
    │   │
    │   ├─ Format final_report_generation_prompt
    │   │   └─ prompts.py:228-308
    │   │
    │   ├─ writer_model.ainvoke([HumanMessage])
    │   │   ├─ LLM API Call
    │   │   └─ Returns: AIMessage with final report
    │   │
    │   └─ ERROR HANDLING:
    │       │
    │       ├─ is_token_limit_exceeded(e, model)
    │       │   └─ utils.py:665-701
    │       │
    │       └─ If token limit exceeded:
    │           │
    │           ├─ get_model_token_limit(model)
    │           │   └─ utils.py:831-846
    │           │       └─ Lookup in MODEL_TOKEN_LIMITS dict
    │           │
    │           └─ Truncate findings progressively:
    │               ├─ First retry: token_limit * 4 chars
    │               └─ Subsequent: reduce by 10%
    │
    └─ Returns: {
        "final_report": str,
        "messages": [AIMessage],
        "notes": []  ← cleared
    }
```

---

## Complete Execution Timeline

### Sequential Flow (Single Thread)

```
1. USER INITIATES RESEARCH
    ↓
2. clarify_with_user()
    ├─ LLM Call → Analyze if clarification needed
    └─ Decision: Continue or Ask Question
    ↓
3. write_research_brief()
    ├─ LLM Call → Generate structured research brief
    └─ Initialize supervisor context
    ↓
4. SUPERVISOR SUBGRAPH STARTS
    ↓
5. supervisor() [Iteration 1]
    ├─ LLM Call → Plan research strategy
    └─ Tool calls: [ConductResearch, ConductResearch, think_tool, ...]
    ↓
6. supervisor_tools() [Iteration 1]
    ├─ Process think_tool reflections
    │
    └─ Spawn N researcher_subgraphs in parallel (N ≤ max_concurrent_research_units)
        │
        ├─── RESEARCHER 1 ─────────────────────┐
        │    ├─ researcher() [Iter 1]          │
        │    │   └─ LLM Call → Tool calls      │
        │    ├─ researcher_tools() [Iter 1]    │
        │    │   └─ tavily_search()            │
        │    │       ├─ Tavily API Call        │
        │    │       └─ summarize_webpage()    │
        │    │           └─ LLM Call           │  PARALLEL
        │    ├─ researcher() [Iter 2]          │  EXECUTION
        │    │   └─ LLM Call → More searches   │
        │    ├─ researcher_tools() [Iter 2]    │
        │    │   └─ tavily_search()            │
        │    └─ compress_research()            │
        │        └─ LLM Call → Synthesize      │
        │                                       │
        ├─── RESEARCHER 2 ─────────────────────┤
        │    ├─ [Same flow as Researcher 1]    │
        │    └─ ...                             │
        │                                       │
        └─── RESEARCHER N ─────────────────────┘
             └─ [Same flow as Researcher 1]
        │
        ↓ (All researchers complete)
        │
    └─ Aggregate results from all researchers
    ↓
7. supervisor() [Iteration 2]
    ├─ LLM Call → Review findings, decide next steps
    └─ Tool calls: [ConductResearch, ...] OR [ResearchComplete]
    ↓
8. supervisor_tools() [Iteration 2]
    └─ Either spawn more researchers OR exit to final report
    ↓
    ... (Loop continues until max iterations or ResearchComplete)
    ↓
9. SUPERVISOR SUBGRAPH ENDS
    └─ All research notes collected
    ↓
10. final_report_generation()
    ├─ LLM Call → Generate comprehensive report
    └─ Returns final report to user
    ↓
11. END
```

---

## Parallel Execution Summary

### Concurrent Operations

1. **Supervisor Tools Level**:
   - Up to `max_concurrent_research_units` researchers run in parallel
   - Default: 5 researchers simultaneously
   - Controlled by: `asyncio.gather(*research_tasks)`

2. **Researcher Tools Level** (within each researcher):
   - All tool calls execute in parallel
   - Controlled by: `asyncio.gather(*tool_execution_tasks)`

3. **Search Summarization** (within tavily_search):
   - All webpage summarizations execute in parallel
   - Controlled by: `asyncio.gather(*summarization_tasks)`

### Example Timeline with 3 Parallel Researchers

```
Time →
|
├─ supervisor() [200ms]
│
├─ supervisor_tools() spawns 3 researchers ─────────────────┐
│                                                            │
├─ RESEARCHER 1 ──────────┐                                 │
│  ├─ researcher() [300ms]│                                 │
│  ├─ tools() [2000ms]    │  Search + Summarize            │
│  ├─ researcher() [300ms]│                                 │  ALL IN
│  ├─ tools() [2000ms]    │  Search + Summarize            │  PARALLEL
│  └─ compress() [500ms]  │                                 │
│                         │                                 │
├─ RESEARCHER 2 ──────────┤ (same timing)                  │
│                         │                                 │
├─ RESEARCHER 3 ──────────┘ (same timing)                  │
│                                                            │
├─ supervisor_tools() aggregates results [100ms] ───────────┘
│
├─ supervisor() [200ms] → ResearchComplete
│
├─ final_report_generation() [1000ms]
│
└─ END

Total Time: ~6 seconds (vs. ~18 seconds if sequential)
```

---

## Key LLM API Calls Summary

### Total LLM Calls in Typical Execution

1. **Clarification Phase**: 1 call
2. **Research Brief**: 1 call
3. **Supervisor Iterations**: N calls (default max: 6)
4. **Researchers** (per researcher):
   - Research iterations: M calls (default max: 10)
   - Search summarizations: P calls per search
   - Compression: 1 call
5. **Final Report**: 1 call

**Example with defaults** (3 concurrent researchers, 2 supervisor iterations):
- Clarification: 1
- Research Brief: 1
- Supervisor: 2
- Researchers: 3 × (3 research calls + 3×2 summarization calls + 1 compression) = 3 × 10 = 30
- Final Report: 1
- **Total: ~35 LLM calls**

---

## External API Calls

### Search APIs
- **Tavily**: `tavily_client.search()` → utils.py:162-168
- **Anthropic Native**: Embedded in model calls
- **OpenAI Native**: Embedded in model calls

### MCP Servers (if configured)
- **Token Exchange**: `aiohttp.post()` → utils.py:278
- **Tool Execution**: MCP client tool calls

### Storage
- **Token Storage**: `get_store().aget()` / `aput()` → utils.py:314, 350

---

## Error Handling Call Stack

### Token Limit Exceeded Flow

```
ANY LLM CALL
    ↓ (throws exception)
    │
is_token_limit_exceeded(exception, model_name)
    └─ utils.py:665-701
        ├─ Determine provider from model_name
        │
        ├─ _check_openai_token_limit()
        │   └─ Check error codes and messages
        │
        ├─ _check_anthropic_token_limit()
        │   └─ Check for "prompt is too long"
        │
        └─ _check_gemini_token_limit()
            └─ Check for ResourceExhausted
    ↓
IF TRUE:
    │
    ├─ IN compress_research():
    │   └─ remove_up_to_last_ai_message(messages)
    │       └─ Retry with truncated messages
    │
    └─ IN final_report_generation():
        ├─ get_model_token_limit(model)
        │   └─ Lookup in MODEL_TOKEN_LIMITS dict
        │
        └─ Truncate findings progressively
            └─ Retry with reduced content
```

---

## Configuration Loading Flow

```
ANY NODE
    ↓
Configuration.from_runnable_config(config)
    └─ configuration.py:130-159
        │
        ├─ Extract configurable dict from RunnableConfig
        │
        ├─ Load model configurations:
        │   ├─ research_model
        │   ├─ compression_model
        │   ├─ final_report_model
        │   └─ summarization_model
        │
        ├─ Load research behavior:
        │   ├─ allow_clarification
        │   ├─ max_concurrent_research_units
        │   ├─ max_researcher_iterations
        │   └─ max_react_tool_calls
        │
        ├─ Load search configuration:
        │   ├─ search_api (TAVILY, ANTHROPIC, OPENAI, NONE)
        │   └─ max_content_length
        │
        └─ Load MCP configuration (if present):
            ├─ url
            ├─ tools
            └─ auth_required
```

---

## State Updates Flow

### State Reducers

```
AgentState Updates
    │
    ├─ messages: MessagesState (auto-append)
    │   └─ Built-in LangChain message reducer
    │
    ├─ supervisor_messages: override_reducer
    │   └─ state.py:55-60
    │       ├─ If {"type": "override"} → replace completely
    │       └─ Else → append (operator.add)
    │
    ├─ research_brief: str (direct assignment)
    │
    ├─ raw_notes: override_reducer (append by default)
    │
    ├─ notes: override_reducer (append by default)
    │
    └─ final_report: str (direct assignment)
```

---

## Summary Statistics

### Function Call Depth
- **Maximum depth**: 8-10 levels deep (e.g., user → graph → supervisor_tools → researcher_subgraph → researcher_tools → tavily_search → summarize_webpage → LLM call)

### Async Operations
- **3 levels of parallelism**:
  1. Multiple researchers (asyncio.gather in supervisor_tools)
  2. Multiple tool calls per researcher (asyncio.gather in researcher_tools)
  3. Multiple summarizations per search (asyncio.gather in tavily_search)

### File Dependencies
- **deep_researcher.py**: Main orchestration (719 lines)
- **utils.py**: Tools and utilities (926 lines)
- **state.py**: State definitions (96 lines)
- **configuration.py**: Config management (252 lines)
- **prompts.py**: Prompt templates (308 lines)

---

## End of Call Stack Documentation

Generated: October 14, 2025
System: Open Deep Research (LangGraph supervisor-researcher architecture)

