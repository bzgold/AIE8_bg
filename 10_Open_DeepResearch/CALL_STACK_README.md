# Call Stack Documentation - Navigation Guide

## 📚 Documentation Suite

I've generated a comprehensive call stack analysis for the Open Deep Research system across three complementary documents:

### 1. 📄 [CALL_STACK.md](CALL_STACK.md) - Complete Call Stack
**Best for**: Understanding detailed execution flow and function calls

**Contents**:
- Complete execution timeline with all function calls
- Detailed breakdown of each node function
- Nested call hierarchies with line number references
- External API calls and LLM interactions
- Error handling call stacks
- State update flows

**When to use**: 
- Debugging specific execution paths
- Understanding exact function call sequences
- Tracing where errors occur
- Finding implementation details

---

### 2. 🎨 [CALL_STACK_DIAGRAM.md](CALL_STACK_DIAGRAM.md) - Visual Diagrams
**Best for**: Visual understanding of architecture and flow

**Contents**:
- Hierarchical architecture diagrams (ASCII art)
- Main graph, supervisor, and researcher flows
- Parallel execution visualization
- Tool execution deep dives
- MCP tools loading flow
- Error handling paths
- State flow diagrams
- Timeline examples with millisecond breakdowns

**When to use**:
- Getting a high-level overview
- Understanding parallel execution
- Explaining the system to others
- Visualizing the architecture

---

### 3. 🔍 [CALL_STACK_SUMMARY.md](CALL_STACK_SUMMARY.md) - Quick Reference
**Best for**: Quick lookups and troubleshooting

**Contents**:
- Function signature reference
- Configuration options table
- Parallel execution points summary
- Error handling quick guide
- Troubleshooting checklist
- LLM call inventory and cost estimation
- File navigation map
- Quick reference tables

**When to use**:
- Quick lookups during development
- Troubleshooting common issues
- Finding function signatures
- Configuration reference
- Cost estimation

---

## 🚀 Quick Start Guide

### Understanding the Architecture

**Start here**: [CALL_STACK_DIAGRAM.md](CALL_STACK_DIAGRAM.md#hierarchical-architecture-diagram)

Read the hierarchical architecture diagram to understand the 3-layer structure:
1. **Main Graph** - Entry point, clarification, final report
2. **Supervisor Subgraph** - Planning and delegation
3. **Researcher Subgraph** - Individual research execution

### Following Execution Flow

**Start here**: [CALL_STACK.md](CALL_STACK.md#main-execution-flow)

Follow the complete execution flow from user input to final report:
1. User initiates research
2. Clarification (optional)
3. Research brief generation
4. Supervisor loop with parallel researchers
5. Each researcher searches and compresses
6. Final report generation

### Finding Specific Functions

**Start here**: [CALL_STACK_SUMMARY.md](CALL_STACK_SUMMARY.md#key-function-signatures)

Look up function signatures and locations:
- Main graph nodes
- Supervisor nodes
- Researcher nodes
- Utility functions

### Debugging Issues

**Start here**: [CALL_STACK_SUMMARY.md](CALL_STACK_SUMMARY.md#quick-troubleshooting)

Common issues and solutions:
- Token limit exceeded
- Too many concurrent requests
- Research not deep enough
- MCP tools not working

---

## 📊 Key Concepts

### Parallel Execution (3 Levels)

```
Level 1: supervisor_tools spawns N researchers
         └─ Default: 5 concurrent researchers

Level 2: researcher_tools executes M tool calls
         └─ All tool calls run in parallel

Level 3: tavily_search summarizes P pages
         └─ All summarizations run in parallel
```

**See**: [CALL_STACK_DIAGRAM.md - Parallel Execution Architecture](CALL_STACK_DIAGRAM.md#parallel-execution-architecture)

### State Hierarchy

```
AgentState (Top)
    ├─ messages
    ├─ supervisor_messages
    ├─ research_brief
    ├─ notes
    └─ final_report
    
SupervisorState (Middle)
    ├─ supervisor_messages
    ├─ research_brief
    ├─ research_iterations
    └─ notes
    
ResearcherState (Bottom)
    ├─ researcher_messages
    ├─ research_topic
    ├─ tool_call_iterations
    └─ compressed_research
```

**See**: [CALL_STACK_SUMMARY.md - State Management](CALL_STACK_SUMMARY.md#state-management)

### Configuration Options

| Setting | Default | Purpose |
|---------|---------|---------|
| `max_concurrent_research_units` | 5 | Parallel researchers |
| `max_researcher_iterations` | 6 | Supervisor loop limit |
| `max_react_tool_calls` | 10 | Researcher tool limit |
| `max_content_length` | 50000 | Chars before summarization |
| `allow_clarification` | True | Ask clarifying questions |

**See**: [CALL_STACK_SUMMARY.md - Configuration Flow](CALL_STACK_SUMMARY.md#configuration-flow)

---

## 🔧 Common Use Cases

### 1. Understanding How a Feature Works

**Example**: "How does parallel research work?"

1. Read: [CALL_STACK_DIAGRAM.md - Supervisor Subgraph Detail](CALL_STACK_DIAGRAM.md#supervisor-subgraph-detail)
2. Then: [CALL_STACK.md - supervisor_tools()](CALL_STACK.md#3b-supervisor_tools)
3. Reference: [CALL_STACK_SUMMARY.md - Parallel Execution Points](CALL_STACK_SUMMARY.md#parallel-execution-points)

### 2. Debugging an Error

**Example**: "Token limit exceeded error"

1. Check: [CALL_STACK_SUMMARY.md - Quick Troubleshooting](CALL_STACK_SUMMARY.md#issue-token-limit-exceeded)
2. Understand: [CALL_STACK_DIAGRAM.md - Error Handling Flow](CALL_STACK_DIAGRAM.md#error-handling-flow-token-limit-exceeded)
3. Trace: [CALL_STACK.md - Error Handling Call Stack](CALL_STACK.md#error-handling-call-stack)

### 3. Modifying Configuration

**Example**: "Need deeper research results"

1. Find settings: [CALL_STACK_SUMMARY.md - Configuration Structure](CALL_STACK_SUMMARY.md#configuration-structure)
2. Understand impact: [CALL_STACK_SUMMARY.md - Issue: Research Not Deep Enough](CALL_STACK_SUMMARY.md#issue-research-not-deep-enough)
3. See how it's used: [CALL_STACK.md - Configuration Loading Flow](CALL_STACK.md#configuration-loading-flow)

### 4. Adding New Tools

**Example**: "How to add MCP tools?"

1. Understand flow: [CALL_STACK_DIAGRAM.md - MCP Tools Loading Flow](CALL_STACK_DIAGRAM.md#mcp-tools-loading-flow)
2. See details: [CALL_STACK.md - MCP Utils](CALL_STACK.md#mcp-utils)
3. Reference function: [CALL_STACK_SUMMARY.md - load_mcp_tools](CALL_STACK_SUMMARY.md#key-function-signatures)

### 5. Estimating Costs

**Example**: "How many LLM calls will this make?"

1. Check inventory: [CALL_STACK_SUMMARY.md - LLM Call Inventory](CALL_STACK_SUMMARY.md#llm-call-inventory)
2. See formula: [CALL_STACK_SUMMARY.md - Cost Estimation Formula](CALL_STACK_SUMMARY.md#cost-estimation-formula)
3. Understand timeline: [CALL_STACK_DIAGRAM.md - End-to-End Example Timeline](CALL_STACK_DIAGRAM.md#end-to-end-example-timeline)

---

## 🗺️ File Navigation Map

### Core Implementation Files

```
open_deep_library/
├── deep_researcher.py (719 lines)
│   ├── Node functions (8 nodes)
│   ├── Subgraph construction (3 graphs)
│   └── Error handling
│
├── utils.py (926 lines)
│   ├── Search tools (tavily_search)
│   ├── Reflection tool (think_tool)
│   ├── MCP integration
│   ├── Token limit detection
│   └── Helper utilities
│
├── state.py (96 lines)
│   ├── State definitions (3 levels)
│   ├── Structured outputs (5 models)
│   └── Reducers
│
├── configuration.py (252 lines)
│   ├── Configuration class
│   ├── Default settings
│   └── from_runnable_config()
│
└── prompts.py (308 lines)
    ├── System prompts (6 phases)
    └── Instruction templates
```

**See**: [CALL_STACK_SUMMARY.md - File Reference Map](CALL_STACK_SUMMARY.md#file-reference-map)

---

## 🎯 Decision Tree: Which Document to Use?

```
START: What do you need?
    │
    ├─ Visual understanding of flow?
    │   └─ → CALL_STACK_DIAGRAM.md
    │
    ├─ Detailed function calls and implementation?
    │   └─ → CALL_STACK.md
    │
    ├─ Quick reference or troubleshooting?
    │   └─ → CALL_STACK_SUMMARY.md
    │
    ├─ Understanding specific node?
    │   ├─ See visual flow → CALL_STACK_DIAGRAM.md
    │   ├─ See detailed implementation → CALL_STACK.md
    │   └─ See function signature → CALL_STACK_SUMMARY.md
    │
    ├─ Debugging an error?
    │   ├─ Quick fix → CALL_STACK_SUMMARY.md (Troubleshooting)
    │   ├─ Understand error path → CALL_STACK_DIAGRAM.md
    │   └─ Trace exact calls → CALL_STACK.md
    │
    └─ Learning the system?
        ├─ Step 1: Architecture → CALL_STACK_DIAGRAM.md
        ├─ Step 2: Execution flow → CALL_STACK.md
        └─ Step 3: Reference → CALL_STACK_SUMMARY.md
```

---

## 📖 Reading Order Recommendations

### For New Users
1. **CALL_STACK_DIAGRAM.md** - Hierarchical Architecture Diagram
2. **CALL_STACK_DIAGRAM.md** - Main Graph, Supervisor, Researcher flows
3. **CALL_STACK.md** - Main Execution Flow
4. **CALL_STACK_SUMMARY.md** - Configuration options

### For Developers
1. **CALL_STACK_SUMMARY.md** - Key Function Signatures
2. **CALL_STACK.md** - Complete node implementations
3. **CALL_STACK_DIAGRAM.md** - Parallel execution details
4. **CALL_STACK_SUMMARY.md** - File Reference Map

### For Debugging
1. **CALL_STACK_SUMMARY.md** - Quick Troubleshooting
2. **CALL_STACK_DIAGRAM.md** - Error Handling Flow
3. **CALL_STACK.md** - Detailed error handling paths
4. **CALL_STACK_SUMMARY.md** - Configuration adjustments

### For System Design
1. **CALL_STACK_DIAGRAM.md** - Complete architecture
2. **CALL_STACK.md** - State Updates Flow
3. **CALL_STACK_SUMMARY.md** - State Management
4. **CALL_STACK_DIAGRAM.md** - Timeline examples

---

## 💡 Tips for Using These Documents

### Search Tips
- **Find a function**: Search for function name across all three docs
- **Find a concept**: Start with CALL_STACK_SUMMARY.md table of contents
- **Find implementation details**: Use CALL_STACK.md with line numbers

### Cross-Reference
- Each document references the others for related information
- Line numbers in CALL_STACK.md link to actual source files
- CALL_STACK_SUMMARY.md provides file navigation shortcuts

### Updates
- These documents are generated from the current codebase
- Regenerate if the code changes significantly
- Version noted at bottom of each document

---

## 🔗 Quick Links

### Main Documents
- [Complete Call Stack](CALL_STACK.md)
- [Visual Diagrams](CALL_STACK_DIAGRAM.md)
- [Quick Reference](CALL_STACK_SUMMARY.md)

### Key Sections

#### Architecture
- [3-Layer Architecture](CALL_STACK_DIAGRAM.md#hierarchical-architecture-diagram)
- [Supervisor Subgraph](CALL_STACK_DIAGRAM.md#supervisor-subgraph-detail)
- [Researcher Subgraph](CALL_STACK_DIAGRAM.md#researcher-subgraph-detail)

#### Execution
- [Main Execution Flow](CALL_STACK.md#main-execution-flow)
- [Sequential Flow](CALL_STACK_SUMMARY.md#sequential-flow-happy-path)
- [Parallel Execution](CALL_STACK_DIAGRAM.md#parallel-execution-architecture)

#### Reference
- [Function Signatures](CALL_STACK_SUMMARY.md#key-function-signatures)
- [Configuration Options](CALL_STACK_SUMMARY.md#configuration-structure)
- [File Navigation](CALL_STACK_SUMMARY.md#file-reference-map)

#### Troubleshooting
- [Quick Troubleshooting](CALL_STACK_SUMMARY.md#quick-troubleshooting)
- [Error Handling](CALL_STACK_DIAGRAM.md#error-handling-flow-token-limit-exceeded)
- [Token Limits](CALL_STACK.md#token-limit-exceeded-flow)

---

## ✅ Checklist: Understanding the System

- [ ] Understand 3-layer architecture (Main → Supervisor → Researcher)
- [ ] Know the 8 main node functions
- [ ] Understand 3 levels of parallel execution
- [ ] Know how to configure research depth
- [ ] Understand error handling (especially token limits)
- [ ] Can estimate LLM call costs
- [ ] Know how to add MCP tools
- [ ] Understand state management and reducers
- [ ] Can trace a call from user input to final report
- [ ] Know where to look for implementation details

---

## 📝 Document Statistics

| Document | Lines | Words | Focus |
|----------|-------|-------|-------|
| CALL_STACK.md | ~1,000 | ~8,000 | Detailed execution |
| CALL_STACK_DIAGRAM.md | ~800 | ~6,000 | Visual architecture |
| CALL_STACK_SUMMARY.md | ~600 | ~5,000 | Quick reference |
| **Total** | **~2,400** | **~19,000** | **Complete coverage** |

---

## 🚀 Next Steps

1. **Start with the overview**: Read CALL_STACK_DIAGRAM.md architecture section
2. **Understand execution**: Review CALL_STACK.md main execution flow
3. **Keep reference handy**: Bookmark CALL_STACK_SUMMARY.md for quick lookups
4. **Try it out**: Run the notebook and trace execution using these docs
5. **Customize**: Use configuration reference to adjust behavior

---

**Generated**: October 14, 2025  
**System**: Open Deep Research (LangGraph)  
**Purpose**: Complete call stack documentation and navigation guide  

---

For questions or updates, refer to the original source code in `open_deep_library/`

