# Open Deep Research - Visual Call Stack Diagram

## Hierarchical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT / QUERY                          │
│                              ↓                                      │
│                    deep_researcher.astream()                        │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        MAIN GRAPH EXECUTION                         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 1. clarify_with_user()                                       │ │
│  │    ├─ LLM: Analyze request clarity                          │ │
│  │    └─ Decision: Need clarification? → YES: END / NO: Next   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                 ↓                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 2. write_research_brief()                                    │ │
│  │    ├─ LLM: Transform messages → structured research brief   │ │
│  │    └─ Initialize supervisor context                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                 ↓                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 3. research_supervisor (SUBGRAPH)                            │ │
│  │    └─ See "Supervisor Subgraph" below                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                 ↓                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 4. final_report_generation()                                 │ │
│  │    ├─ Aggregate all research findings                        │ │
│  │    ├─ LLM: Generate comprehensive report                     │ │
│  │    └─ Handle token limits with progressive truncation        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                 ↓                                   │
│                             END ✓                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Supervisor Subgraph Detail

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SUPERVISOR SUBGRAPH                          │
│                                                                     │
│    ┌──────────────────────────────────────────────────────┐        │
│  ┌─┤ supervisor()                                         │        │
│  │ │ ├─ LLM with tools: [ConductResearch,                │        │
│  │ │ │                   ResearchComplete,                │        │
│  │ │ │                   think_tool]                      │        │
│  │ │ ├─ Analyze research brief                           │        │
│  │ │ ├─ Plan delegation strategy                         │        │
│  │ │ └─ Generate tool calls                              │        │
│  │ └──────────────────────────────────────────────────────┘        │
│  │                          ↓                                       │
│  │ ┌──────────────────────────────────────────────────────┐        │
│  │ │ supervisor_tools()                                   │        │
│  │ │ ├─ Process think_tool reflections                    │        │
│  │ │ ├─ Check exit conditions:                            │        │
│  │ │ │   • Max iterations exceeded?                       │        │
│  │ │ │   • ResearchComplete called?                       │        │
│  └─┤ │   • No tool calls?                                 │        │
│    │ ├─ Limit to max_concurrent_research_units            │        │
│    │ └─ Spawn researcher_subgraphs in PARALLEL ─────────┐ │        │
│    └──────────────────────────────────────────────────────┘ │      │
│                                                            │        │
│    ┌───────────────────────────────────────────────────────┘       │
│    │                                                                │
│    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│    └─►│ RESEARCHER 1│  │ RESEARCHER 2│  │ RESEARCHER N│  (Parallel)│
│       │   SUBGRAPH  │  │   SUBGRAPH  │  │   SUBGRAPH  │           │
│       └─────┬───────┘  └─────┬───────┘  └─────┬───────┘           │
│             │                 │                 │                   │
│             └─────────────────┴─────────────────┘                   │
│                              │                                      │
│                    asyncio.gather()                                 │
│                              ↓                                      │
│                    Aggregate results                                │
│                              ↓                                      │
│                    Loop back to supervisor()                        │
│                                                                     │
│    (Loop until max_researcher_iterations or ResearchComplete)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Researcher Subgraph Detail

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RESEARCHER SUBGRAPH                          │
│                    (Spawned by supervisor_tools)                    │
│                                                                     │
│    ┌──────────────────────────────────────────────────────┐        │
│  ┌─┤ researcher()                                         │        │
│  │ │ ├─ Load tools:                                       │        │
│  │ │ │   • get_all_tools(config)                         │        │
│  │ │ │     ├─ Search tools (Tavily/Anthropic/OpenAI)     │        │
│  │ │ │     ├─ ResearchComplete                            │        │
│  │ │ │     ├─ think_tool                                  │        │
│  │ │ │     └─ MCP tools (if configured)                   │        │
│  │ │ ├─ LLM with tools bound                              │        │
│  │ │ └─ Generate tool calls                               │        │
│  │ └──────────────────────────────────────────────────────┘        │
│  │                          ↓                                       │
│  │ ┌──────────────────────────────────────────────────────┐        │
│  │ │ researcher_tools()                                   │        │
│  │ │ ├─ Check early exit (no tools/native search)         │        │
│  │ │ ├─ Execute all tool calls in PARALLEL:               │        │
│  └─┤ │   ├─ tavily_search() ──────────┐                   │        │
│    │ │   ├─ think_tool()              │                   │        │
│    │ │   ├─ MCP tools                 │ (asyncio.gather)  │        │
│    │ │   └─ ResearchComplete          │                   │        │
│    │ ├─ Check late exit:              ↓                   │        │
│    │ │   • Max tool_call_iterations?                      │        │
│    │ │   • ResearchComplete called?                       │        │
│    │ └─ Loop back OR continue to compress                 │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ compress_research()                                  │        │
│    │ ├─ LLM: Synthesize all findings                      │        │
│    │ ├─ Extract raw notes from messages                   │        │
│    │ ├─ Handle token limits (retry with truncation)       │        │
│    │ └─ Return: {compressed_research, raw_notes}          │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│                          SUBGRAPH END                               │
│             (Returns to supervisor_tools for aggregation)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tool Execution Deep Dive: tavily_search()

```
┌─────────────────────────────────────────────────────────────────────┐
│                          tavily_search()                            │
│                         (utils.py:43-136)                           │
│                                                                     │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 1. Execute Search                                    │        │
│    │    ├─ tavily_search_async(queries)                   │        │
│    │    │   ├─ AsyncTavilyClient(api_key)                 │        │
│    │    │   ├─ FOR EACH query:                            │        │
│    │    │   │   └─ tavily_client.search() ← API CALL      │        │
│    │    │   └─ asyncio.gather(*tasks) → PARALLEL          │        │
│    │    └─ Returns: [search_results]                      │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 2. Deduplicate by URL                                │        │
│    │    └─ unique_results = {url: result}                 │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 3. Summarize Content (PARALLEL)                      │        │
│    │    ├─ FOR EACH unique result:                        │        │
│    │    │   └─ summarize_webpage(model, content)          │        │
│    │    │       ├─ LLM with structured output (Summary)   │        │
│    │    │       ├─ asyncio.wait_for(timeout=60s)          │        │
│    │    │       └─ Format: <summary>...<key_excerpts>...  │        │
│    │    └─ asyncio.gather(*summarization_tasks)           │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 4. Format Output                                     │        │
│    │    ├─ Combine summaries with URLs                    │        │
│    │    └─ Return formatted string                        │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│                        Return to caller                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## MCP Tools Loading Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      get_all_tools(config)                          │
│                       (utils.py:569-597)                            │
│                                                                     │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 1. Initialize Base Tools                             │        │
│    │    └─ [ResearchComplete, think_tool]                 │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 2. Add Search Tools                                  │        │
│    │    ├─ get_search_tool(search_api)                    │        │
│    │    │   ├─ ANTHROPIC → web_search_20250305            │        │
│    │    │   ├─ OPENAI → web_search_preview                │        │
│    │    │   ├─ TAVILY → tavily_search                     │        │
│    │    │   └─ NONE → []                                  │        │
│    │    └─ Append to tools list                           │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 3. Load MCP Tools (if configured)                    │        │
│    │    ├─ load_mcp_tools(config, existing_names)         │        │
│    │    │   │                                              │        │
│    │    │   ├─ Authenticate:                               │        │
│    │    │   │   ├─ fetch_tokens(config)                   │        │
│    │    │   │   │   ├─ get_tokens() → Check store         │        │
│    │    │   │   │   └─ get_mcp_access_token()             │        │
│    │    │   │   │       └─ OAuth token exchange via HTTP  │        │
│    │    │   │   └─ set_tokens() → Store tokens            │        │
│    │    │   │                                              │        │
│    │    │   ├─ Connect to MCP Server:                     │        │
│    │    │   │   ├─ MultiServerMCPClient(server_config)    │        │
│    │    │   │   └─ client.get_tools()                     │        │
│    │    │   │                                              │        │
│    │    │   └─ Filter & Wrap Tools:                       │        │
│    │    │       ├─ Check name conflicts                   │        │
│    │    │       ├─ Filter by configured tool names        │        │
│    │    │       └─ wrap_mcp_authenticate_tool()           │        │
│    │    │           └─ Add error handling wrapper         │        │
│    │    │                                                  │        │
│    │    └─ Append MCP tools to list                       │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│                    Return: [all_tools]                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow: Token Limit Exceeded

```
┌─────────────────────────────────────────────────────────────────────┐
│                  ANY LLM API CALL (throws exception)                │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│              is_token_limit_exceeded(exception, model)              │
│                       (utils.py:665-701)                            │
│                                                                     │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 1. Determine Provider                                │        │
│    │    ├─ Check model_name prefix:                       │        │
│    │    │   ├─ "openai:" → provider = 'openai'            │        │
│    │    │   ├─ "anthropic:" → provider = 'anthropic'      │        │
│    │    │   └─ "google:" → provider = 'gemini'            │        │
│    │    └─ Optimize checks based on provider             │        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ 2. Check Provider-Specific Patterns                  │        │
│    │    ├─ _check_openai_token_limit()                    │        │
│    │    │   ├─ Error type: BadRequestError                │        │
│    │    │   ├─ Error code: context_length_exceeded        │        │
│    │    │   └─ Keywords: token, context, length           │        │
│    │    │                                                  │        │
│    │    ├─ _check_anthropic_token_limit()                 │        │
│    │    │   ├─ Error type: BadRequestError                │        │
│    │    │   └─ Message: "prompt is too long"              │        │
│    │    │                                                  │        │
│    │    └─ _check_gemini_token_limit()                    │        │
│    │        ├─ Error type: ResourceExhausted              │        │
│    │        └─ Exception type contains "resourceexhausted"│        │
│    └──────────────────────────────────────────────────────┘        │
│                              ↓                                      │
│                     Return: True or False                           │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        IF TRUE: RETRY LOGIC                         │
│                                                                     │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ IN compress_research():                              │        │
│    │ ├─ remove_up_to_last_ai_message(messages)            │        │
│    │ │   └─ Truncate message history                      │        │
│    │ └─ Retry compression (max 3 attempts)                │        │
│    └──────────────────────────────────────────────────────┘        │
│                              OR                                     │
│    ┌──────────────────────────────────────────────────────┐        │
│    │ IN final_report_generation():                        │        │
│    │ ├─ get_model_token_limit(model)                      │        │
│    │ │   └─ Lookup in MODEL_TOKEN_LIMITS dict             │        │
│    │ ├─ Calculate character limit (token_limit * 4)       │        │
│    │ ├─ Truncate findings progressively (-10% each retry) │        │
│    │ └─ Retry report generation (max 3 attempts)          │        │
│    └──────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Parallel Execution Architecture

### Level 1: Supervisor spawns Multiple Researchers

```
supervisor_tools()
    │
    ├─ Create research_tasks = [
    │      researcher_subgraph.ainvoke(research_topic_1),
    │      researcher_subgraph.ainvoke(research_topic_2),
    │      researcher_subgraph.ainvoke(research_topic_3),
    │      ...
    │  ]
    │
    └─ asyncio.gather(*research_tasks)
           │
           ├────────────────┬────────────────┬────────────────┐
           │                │                │                │
           ▼                ▼                ▼                ▼
    RESEARCHER 1      RESEARCHER 2      RESEARCHER 3   ... RESEARCHER N
    (Complete flow)   (Complete flow)   (Complete flow)  (Complete flow)
           │                │                │                │
           └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
                          Aggregated Results
```

### Level 2: Each Researcher executes Multiple Tool Calls

```
researcher_tools()
    │
    ├─ Create tool_execution_tasks = [
    │      tavily_search(query_1),
    │      tavily_search(query_2),
    │      think_tool(reflection),
    │      mcp_tool(args),
    │      ...
    │  ]
    │
    └─ asyncio.gather(*tool_execution_tasks)
           │
           ├──────────────┬──────────────┬──────────────┐
           │              │              │              │
           ▼              ▼              ▼              ▼
      SEARCH 1        SEARCH 2      THINK TOOL      MCP TOOL
           │              │              │              │
           └──────────────┴──────────────┴──────────────┘
                                │
                                ▼
                         Tool Results
```

### Level 3: Search Tool summarizes Multiple Pages

```
tavily_search()
    │
    ├─ Step 1: Parallel Searches
    │    ├─ search_tasks = [
    │    │      tavily_client.search(query_1),
    │    │      tavily_client.search(query_2),
    │    │      ...
    │    │  ]
    │    └─ asyncio.gather(*search_tasks)
    │           → Get all search results
    │
    ├─ Step 2: Deduplicate by URL
    │    └─ unique_results = {...}
    │
    ├─ Step 3: Parallel Summarization
    │    ├─ summarization_tasks = [
    │    │      summarize_webpage(model, page_1),
    │    │      summarize_webpage(model, page_2),
    │    │      summarize_webpage(model, page_3),
    │    │      ...
    │    │  ]
    │    └─ asyncio.gather(*summarization_tasks)
    │           │
    │           ├────────┬────────┬────────┬────────┐
    │           │        │        │        │        │
    │           ▼        ▼        ▼        ▼        ▼
    │      LLM CALL  LLM CALL LLM CALL LLM CALL  ...
    │     (Summary 1)(Summary 2)(Summary 3)(Summary 4)
    │           │        │        │        │        │
    │           └────────┴────────┴────────┴────────┘
    │                           │
    │                           ▼
    │                  All Summaries Ready
    │
    └─ Step 4: Format and Return
```

---

## State Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AgentState                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ messages: [HumanMessage("Research request"), ...]             │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ supervisor_messages: [SystemMessage, HumanMessage, ...]       │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ research_brief: "Detailed research brief..."                  │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ raw_notes: ["Note 1", "Note 2", ...]                          │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ notes: ["Compressed 1", "Compressed 2", ...]                  │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ final_report: "# Final Report\n\n..."                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┴────────────────────────┐
        │                                                  │
        ▼                                                  ▼
┌───────────────────────┐                    ┌───────────────────────┐
│   SupervisorState     │                    │   ResearcherState     │
│  ┌─────────────────┐  │                    │  ┌─────────────────┐  │
│  │ supervisor_msgs │  │                    │  │ researcher_msgs │  │
│  ├─────────────────┤  │                    │  ├─────────────────┤  │
│  │ research_brief  │  │                    │  │ research_topic  │  │
│  ├─────────────────┤  │                    │  ├─────────────────┤  │
│  │ notes           │  │                    │  │ tool_call_iters │  │
│  ├─────────────────┤  │                    │  ├─────────────────┤  │
│  │ research_iters  │  │                    │  │ compressed_res  │  │
│  ├─────────────────┤  │                    │  ├─────────────────┤  │
│  │ raw_notes       │  │                    │  │ raw_notes       │  │
│  └─────────────────┘  │                    │  └─────────────────┘  │
└───────────────────────┘                    └───────────────────────┘
```

---

## Configuration Flow

```
RunnableConfig
    │
    ├─ configurable: {
    │      # Model Settings
    │      research_model: "anthropic:claude-sonnet-4-20250514",
    │      research_model_max_tokens: 10000,
    │      compression_model: "anthropic:claude-sonnet-4-20250514",
    │      compression_model_max_tokens: 8192,
    │      final_report_model: "anthropic:claude-sonnet-4-20250514",
    │      final_report_model_max_tokens: 10000,
    │      summarization_model: "anthropic:claude-sonnet-4-20250514",
    │      summarization_model_max_tokens: 8192,
    │      
    │      # Research Behavior
    │      allow_clarification: True,
    │      max_concurrent_research_units: 3,
    │      max_researcher_iterations: 4,
    │      max_react_tool_calls: 10,
    │      
    │      # Search Configuration
    │      search_api: "tavily",  # or "anthropic", "openai", "none"
    │      max_content_length: 50000,
    │      
    │      # MCP Configuration (optional)
    │      mcp_config: {
    │          url: "https://mcp-server.example.com",
    │          tools: ["tool1", "tool2"],
    │          auth_required: True
    │      },
    │      
    │      # Session Info
    │      thread_id: "uuid-string"
    │  }
    │
    └─ Configuration.from_runnable_config(config)
           └─ Returns configured Configuration object
```

---

## End-to-End Example Timeline

### Example: Research Request with 2 Iterations, 3 Parallel Researchers

```
Time (ms)     Event
─────────────────────────────────────────────────────────────────────
0             User initiates: "Analyze this PDF about AI usage"
              
100           clarify_with_user()
              └─ LLM call (200ms)
              
300           ✓ Clarification: No questions needed
              
350           write_research_brief()
              └─ LLM call (300ms)
              
650           ✓ Research brief generated
              
700           supervisor() [Iteration 1]
              └─ LLM call (200ms)
              
900           ✓ Tool calls generated: [
                  ConductResearch(topic1),
                  ConductResearch(topic2),
                  ConductResearch(topic3),
                  think_tool(reflection)
              ]
              
950           supervisor_tools() [Iteration 1]
              ├─ Process think_tool (50ms)
              └─ Spawn 3 researchers in parallel
              
1000          ┌─ RESEARCHER 1 ──────────────────────────────┐
              │  ├─ researcher() LLM (300ms)                │
              │  ├─ researcher_tools()                      │
              │  │  └─ tavily_search() (2000ms)             │
              │  │     ├─ API calls (500ms)                 │
1300          │  │     └─ Summarize 3 pages (1500ms)        │  PARALLEL
              │  ├─ researcher() LLM (300ms)                │  EXECUTION
              │  ├─ researcher_tools()                      │
              │  │  └─ tavily_search() (2000ms)             │
              │  └─ compress_research() LLM (500ms)         │
              │                                             │
              ├─ RESEARCHER 2 (same flow, 5600ms total)    │
              │                                             │
              └─ RESEARCHER 3 (same flow, 5600ms total)    ┘
              
6600          ✓ All researchers complete
              └─ Aggregate results (100ms)
              
6700          supervisor() [Iteration 2]
              └─ LLM call (200ms)
              
6900          ✓ Tool calls: [ResearchComplete]
              
6950          supervisor_tools() [Iteration 2]
              └─ Detect ResearchComplete → Exit supervisor
              
7000          final_report_generation()
              └─ LLM call (1000ms)
              
8000          ✓ Final report generated
              
8050          END - Return to user
              
─────────────────────────────────────────────────────────────────────
Total Time:   ~8 seconds
LLM Calls:    ~15 calls (1 clarify + 1 brief + 2 supervisor + 
                          3×3 research + 3×2 summarize + 3 compress + 
                          1 final = 15)
```

---

## Function Reference Quick Index

### Main Nodes
- `clarify_with_user()` → deep_researcher.py:60-115
- `write_research_brief()` → deep_researcher.py:118-175
- `supervisor()` → deep_researcher.py:178-223
- `supervisor_tools()` → deep_researcher.py:225-349
- `researcher()` → deep_researcher.py:365-424
- `researcher_tools()` → deep_researcher.py:435-509
- `compress_research()` → deep_researcher.py:511-585
- `final_report_generation()` → deep_researcher.py:607-697

### Utility Functions
- `tavily_search()` → utils.py:43-136
- `think_tool()` → utils.py:219-244
- `get_all_tools()` → utils.py:569-597
- `load_mcp_tools()` → utils.py:449-524
- `is_token_limit_exceeded()` → utils.py:665-701
- `get_today_str()` → utils.py:872-879
- `get_api_key_for_model()` → utils.py:892-914

### State & Configuration
- `Configuration.from_runnable_config()` → configuration.py:130-159
- `override_reducer()` → state.py:55-60
- State classes → state.py:62-96

---

Generated: October 14, 2025

