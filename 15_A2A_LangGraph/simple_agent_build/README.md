# Simple Agent Build - LangGraph A2A UI

A FastAPI web application that serves as a simple LangGraph agent UI, forwarding queries to the A2A research agent and displaying streaming responses in a browser.

## 🎯 Overview

This satisfies **Activity #1** requirements:
> "Build a LangGraph Graph to use your application. Do this by creating a Simple Agent that can make API calls to the 🤖Agent Node above through the A2A protocol."

### Features

- ✅ **LangGraph Agent** - Single-node graph that calls the A2A agent
- ✅ **A2A Protocol** - Uses A2A SDK to communicate with research agent
- ✅ **FastAPI Web UI** - Beautiful browser interface
- ✅ **Streaming Support** - Real-time partial responses as they arrive
- ✅ **Simple Architecture** - Minimal code demonstrating A2A communication

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Browser (User)                     │
│   - HTML/JavaScript UI               │
└──────────────┬──────────────────────┘
               │ HTTP/SSE
               ▼
┌─────────────────────────────────────┐
│   FastAPI Web App                    │
│   (simple_agent_build/app.py)        │
│   - Serves HTML UI                   │
│   - Handles /query/stream endpoint   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   LangGraph Agent                    │
│   (agent_graph.py)                   │
│   - Single node: calls A2A agent    │
│   - Returns response                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   A2A Tool                           │
│   (a2a_tool.py)                      │
│   - Discovers agent via AgentCard    │
│   - Formats A2A protocol messages           │
│   - Streams responses                │
└──────────────┬──────────────────────┘
               │ A2A Protocol (HTTP)
               ▼
┌─────────────────────────────────────┐
│   A2A Research Agent                 │
│   (http://localhost:10000)           │
│   - Web Search (Tavily)              │
│   - Academic Papers (ArXiv)          │
│   - Document Retrieval (RAG)         │
│   - Helpfulness Evaluation           │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **A2A Agent Server** must be running:
```bash
# Terminal 1
uv run python -m app
```

### Run the Web App

```bash
# Terminal 2
uv run python simple_agent_build/app.py
```

Or with custom host/port:

```bash
uv run python -m uvicorn simple_agent_build.app:app --host 0.0.0.0 --port 8000
```

### Access the UI

Open your browser to:
```
http://localhost:8000
```

## 📁 File Structure

```
simple_agent_build/
├── __init__.py          # Package initialization
├── a2a_tool.py          # Tool for calling A2A agent (HTTP client)
├── agent_graph.py       # LangGraph with single node
├── app.py               # FastAPI web application
└── README.md            # This file
```

## 🔧 How It Works

### 1. LangGraph Agent (`agent_graph.py`)

Simple single-node graph:
```python
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)  # One node that calls A2A
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)
```

The `agent_node` function:
1. Extracts user query from messages
2. Calls `call_a2a_agent()` to forward to A2A server
3. Returns the response

### 2. A2A Tool (`a2a_tool.py`)

Two main functions:

**`call_a2a_agent(query)`** - Synchronous call:
- Fetches AgentCard from A2A server
- Formats query in A2A protocol
- Sends HTTP request
- Returns text response

**`stream_a2a_agent(query)`** - Streaming call:
- Same discovery and formatting
- Uses `client.send_message_streaming()`
- Yields chunks as they arrive

### 3. FastAPI App (`app.py`)

**Endpoints:**

- `GET /` - Serves HTML UI page
- `POST /query` - Non-streaming query endpoint
- `POST /query/stream` - **Streaming endpoint** (used by UI)

**Streaming Implementation:**
```python
@app.post("/query/stream")
async def query_stream_endpoint(request: Request):
    async def generate():
        # Stream from A2A agent
        async for chunk in stream_a2a_agent(query):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 4. HTML UI

**Features:**
- Beautiful gradient design
- Real-time status indicator (checks if A2A agent is connected)
- Example query buttons
- Streaming response display (updates as chunks arrive)
- Auto-scroll to latest content
- Error handling

**JavaScript Streaming:**
```javascript
const reader = response.body.getReader();
while (true) {
    const { done, value } = await reader.read();
    // Parse and display chunks
    responseBox.textContent += data.content;
}
```

## 📊 Example Usage

1. **Start A2A Agent** (Terminal 1):
```bash
uv run python -m app
```

2. **Start Web App** (Terminal 2):
```bash
uv run python simple_agent_build/app.py
```

3. **Open Browser**: `http://localhost:8000`

4. **Try Example Queries:**
   - "What are the latest developments in AI reasoning models?"
   - "Find recent papers about transformer architectures"
   - "What do studies say about how people use AI tools?"

5. **Watch Streaming**: Responses appear in real-time as the A2A agent processes your query!

## 🎨 UI Features

- **Status Badge**: Shows connection status to A2A agent
- **Example Queries**: Quick buttons for common queries
- **Streaming Display**: Text appears incrementally
- **Error Messages**: Clear error display if A2A agent is unavailable
- **Keyboard Shortcut**: Ctrl/Cmd + Enter to submit

## 🔍 Key Components for Activity #1

This implementation demonstrates:

✅ **LangGraph Graph** - Created in `agent_graph.py`  
✅ **Single Node** - One agent node that calls A2A  
✅ **A2A Protocol** - Uses `a2a.client.A2AClient` and `A2ACardResolver`  
✅ **API Calls** - HTTP requests via A2A SDK  
✅ **Simple Architecture** - Minimal, focused implementation  

## 🐛 Troubleshooting

**"A2A Agent Disconnected" badge:**
- Ensure A2A agent is running: `uv run python -m app`
- Check it's accessible at `http://localhost:10000`
- Test with: `curl http://localhost:10000/.well-known/agent.json`

**No streaming responses:**
- Check browser console for errors
- Verify A2A agent supports streaming (it does!)
- Try non-streaming endpoint: `POST /query`

**Import errors:**
- Install dependencies: `uv sync`
- Ensure you're in project root

## 📝 Dependencies

Required packages (already in `pyproject.toml`):
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langgraph` - Graph orchestration
- `a2a-sdk` - A2A protocol client
- `httpx` - Async HTTP client
- `langchain-core` - For messages

## 🎯 Next Steps

This satisfies Activity #1! For Advanced Build, you could:
- Add multiple personas with different goals
- Chain multiple agents together
- Add conversation history
- Implement retry logic
- Add response quality scoring

---

**Built for AIE8 Session 15: A2A LangGraph Agent** 🚀

