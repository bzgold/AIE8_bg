# Architecture Comparison: Visual Diagrams

## RAGAS Knowledge Graph Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAGAS KNOWLEDGE GRAPH                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📄 Documents ──┐                                               │
│                 │                                               │
│                 ▼                                               │
│  🔗 Knowledge Graph Construction                                │
│  ├── Node Creation (per document)                               │
│  ├── Default Transformations                                    │
│  │   ├── 📝 Summaries                                          │
│  │   ├── 📰 Headlines                                          │
│  │   └── 🎯 Themes                                             │
│  └── Relationship Building                                      │
│      ├── 🔍 Cosine Similarity                                  │
│      └── 📊 Embedding-based Edges                              │
│                                                                 │
│                 ▼                                               │
│  🎯 Clustering (CRITICAL STEP)                                  │
│  ├── Group related nodes                                        │
│  └── Create clusters for multi-hop questions                   │
│                                                                 │
│                 ▼                                               │
│  ❌ FAILURE POINT: "No clusters found"                          │
│  └── Multi-hop synthesizers fail here                          │
│                                                                 │
│                 ▼                                               │
│  🔄 Query Synthesizers                                          │
│  ├── SingleHopSpecificQuerySynthesizer                         │
│  ├── MultiHopAbstractQuerySynthesizer                          │
│  └── MultiHopSpecificQuerySynthesizer                          │
│                                                                 │
│                 ▼                                               │
│  📋 Generated Questions                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

⚠️  FAILURE SCENARIOS:
• Insufficient relationships → No clusters
• Transform failures → Missing properties
• Memory issues → Large graphs
```

## LangGraph Evol Instruct Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                LANGGRAPH EVOL INSTRUCT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📄 Documents ──┐                                               │
│                 │                                               │
│                 ▼                                               │
│  🚀 LangGraph Workflow (Stateful)                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 1️⃣ INITIALIZE                                               ││
│  │ ├── Generate initial questions                              ││
│  │ └── Setup state management                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 2️⃣ SIMPLE EVOLUTION                                         ││
│  │ ├── Refine basic questions                                  ││
│  │ ├── Add specificity and detail                              ││
│  │ └── Make more conversational                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 3️⃣ MULTI-CONTEXT EVOLUTION                                  ││
│  │ ├── Create cross-document questions                         ││
│  │ ├── Require synthesis from multiple sources                ││
│  │ └── Add comparative elements                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 4️⃣ REASONING EVOLUTION                                      ││
│  │ ├── Generate analytical questions                           ││
│  │ ├── Require logical reasoning                               ││
│  │ └── Add "why", "how", "what if" elements                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 5️⃣ ANSWER GENERATION                                        ││
│  │ ├── Create comprehensive answers                            ││
│  │ ├── Add confidence scores                                   ││
│  │ └── Include source citations                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 6️⃣ CONTEXT SELECTION                                        ││
│  │ ├── Identify relevant contexts                              ││
│  │ ├── Rank by relevance                                       ││
│  │ └── Provide reasoning                                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 7️⃣ FINALIZE                                                 ││
│  │ ├── Compile structured results                              ││
│  │ ├── Format outputs                                          ││
│  │ └── Generate summary                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  📊 Structured Output                                           │
│  ├── 🔍 Evolved Questions (with IDs & types)                   │
│  ├── 💡 Question Answers (with confidence)                     │
│  └── 🎯 Question Contexts (with relevance)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

✅ ADVANTAGES:
• No clustering dependencies
• Fully customizable
• Graceful error handling
• Rich metadata output
```

## Key Differences Summary

### 🔄 Processing Flow
```
RAGAS:    Documents → Graph → Clusters → Synthesizers → Questions
LangGraph: Documents → Workflow → Evolution → Answers → Contexts
```

### 🎯 Question Generation
```
RAGAS:    Fixed synthesizers with predefined logic
LangGraph: Custom evolution prompts with LLM creativity
```

### ⚡ Performance
```
RAGAS:    Fast generation, slow setup, high memory
LangGraph: Slow generation, fast setup, lower memory
```

### 🛡️ Reliability
```
RAGAS:    Fails on clustering issues
LangGraph: Graceful degradation, no clustering dependencies
```

### 🔧 Customization
```
RAGAS:    Limited to predefined transformations
LangGraph: Fully customizable prompts and workflow
```

