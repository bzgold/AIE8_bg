"""FastAPI web app serving a simple LangGraph agent UI that uses the A2A agent."""
import json
import logging
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn

from simple_agent_build.agent_graph import run_agent
from simple_agent_build.a2a_tool import stream_a2a_agent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Agent Build - A2A LangGraph UI")


@app.get("/api/check-a2a")
async def check_a2a():
    """Check if A2A agent is accessible."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            response = await client.get("http://localhost:10000/.well-known/agent.json")
            if response.status_code == 200:
                return {"connected": True, "status": "connected"}
            else:
                return {"connected": False, "status": "not_responding"}
    except Exception as e:
        return {"connected": False, "status": "error", "error": str(e)}


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main HTML page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Agent Build - A2A LangGraph UI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 0.95em;
        }
        
        .status-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-top: 10px;
        }
        
        .status-badge.connected {
            background: rgba(76, 175, 80, 0.3);
        }
        
        .status-badge.disconnected {
            background: rgba(244, 67, 54, 0.3);
        }
        
        .content {
            padding: 30px;
        }
        
        .query-section {
            margin-bottom: 30px;
        }
        
        .query-section label {
            display: block;
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }
        
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            min-height: 120px;
            transition: border-color 0.3s;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
            margin-top: 15px;
        }
        
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .response-section {
            margin-top: 30px;
        }
        
        .response-section h2 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #333;
        }
        
        .response-box {
            background: #f5f5f5;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            min-height: 200px;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .response-box:empty::before {
            content: "Response will appear here...";
            color: #999;
            font-style: italic;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
            vertical-align: middle;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            color: #d32f2f;
            background: #ffebee;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #d32f2f;
            margin-top: 15px;
        }
        
        .example-queries {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 8px;
        }
        
        .example-queries h3 {
            font-size: 0.95em;
            margin-bottom: 10px;
            color: #666;
        }
        
        .example-queries button {
            background: #f0f0f0;
            color: #333;
            padding: 8px 15px;
            margin: 5px 5px 5px 0;
            font-size: 0.85em;
            width: auto;
        }
        
        .example-queries button:hover {
            background: #e0e0e0;
        }
        
        .status-tracker {
            margin-top: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f0f4ff;
            border: 2px solid #667eea;
            border-radius: 8px;
            display: none;
        }
        
        .status-tracker.active {
            display: block;
        }
        
        .status-tracker h3 {
            font-size: 0.95em;
            margin-bottom: 10px;
            color: #667eea;
            font-weight: 600;
        }
        
        .status-current {
            font-size: 1em;
            color: #333;
            font-weight: 600;
            padding: 8px 12px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #667eea;
            margin-top: 5px;
        }
        
        .status-current.error {
            border-left-color: #d32f2f;
            color: #d32f2f;
        }
        
        .status-current.complete {
            border-left-color: #4caf50;
            color: #4caf50;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Simple Agent Build</h1>
            <p>LangGraph Agent UI - A2A Protocol Communication</p>
            <span class="status-badge" id="statusBadge" style="display: inline-block;">Checking...</span>
        </div>
        
        <div class="content">
            <div class="query-section">
                <label for="query">Enter your query:</label>
                <textarea id="query" placeholder="Ask me anything! The agent will forward your query to the A2A research agent with access to web search, academic papers, and document retrieval..."></textarea>
                
                <div class="example-queries">
                    <h3>Example queries:</h3>
                    <button onclick="setQuery('What are the latest developments in AI reasoning models?')">AI Reasoning Models</button>
                    <button onclick="setQuery('Find recent papers about transformer architectures')">Transformer Papers</button>
                    <button onclick="setQuery('What do studies say about how people use AI tools?')">AI Usage Studies</button>
                </div>
                
                <button id="submitBtn" onclick="submitQuery()">Send Query →</button>
            </div>
            
            <div class="status-tracker" id="statusTracker">
                <h3>🔍 A2A Process Tracker:</h3>
                <div class="status-current" id="statusCurrent">Ready...</div>
            </div>
            
            <div class="response-section">
                <h2>Response:</h2>
                <div class="response-box" id="responseBox"></div>
            </div>
        </div>
    </div>
    
    <script>
        (function() {
            'use strict';
            
            let isStreaming = false;
            
            // Status check function - simplified and reliable
            async function checkA2AAgent() {
                const badge = document.getElementById('statusBadge');
                if (!badge) {
                    return;
                }
                
                try {
                    // Use a shorter timeout for faster feedback
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 3000);
                    
                    const response = await fetch('/api/check-a2a', {
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    // Only log if status changed
                    const wasConnected = badge.className.includes('connected');
                    const isConnected = data && data.connected === true;
                    
                    if (isConnected) {
                        badge.textContent = '✓ A2A Agent Connected';
                        badge.className = 'status-badge connected';
                        if (!wasConnected) {
                            console.log('A2A Agent: Connected');
                        }
                    } else {
                        badge.textContent = '✗ A2A Agent Disconnected';
                        badge.className = 'status-badge disconnected';
                        if (wasConnected) {
                            console.warn('A2A Agent: Disconnected', data.status || '');
                        }
                    }
                } catch (error) {
                    // Only update badge if it was previously connected
                    const badge = document.getElementById('statusBadge');
                    if (!badge) return;
                    
                    const wasConnected = badge.className.includes('connected');
                    
                    // If it was connected and now we get an error, mark as disconnected
                    // But don't spam console on every failed check
                    if (wasConnected && error.name !== 'AbortError') {
                        console.warn('A2A Agent: Connection check failed', error.message);
                        badge.textContent = '✗ A2A Agent Disconnected';
                        badge.className = 'status-badge disconnected';
                    } else if (!wasConnected && error.name === 'AbortError') {
                        // Timeout - might be temporary, don't spam
                        // badge already shows disconnected
                    }
                }
            }
            
            // Initialize status check - ensure DOM is ready
            function init() {
                checkA2AAgent();
                setInterval(checkA2AAgent, 10000);
            }
            
            // Wait for DOM to be ready - use window.onload as backup
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', init);
            } else {
                // DOM already ready, run immediately
                init();
            }
            
            // Backup initialization on window load
            window.addEventListener('load', function() {
                const badge = document.getElementById('statusBadge');
                if (badge && badge.textContent === 'Checking...') {
                    checkA2AAgent();
                }
            });
            
            // Export for manual testing
            window.checkA2AAgent = checkA2AAgent;
            
            // Query helper function
            function setQuery(text) {
                document.getElementById('query').value = text;
            }
            window.setQuery = setQuery;
            
            // Update status tracker
            function updateStatusTracker(statusText, isError = false, isComplete = false) {
                const tracker = document.getElementById('statusTracker');
                const current = document.getElementById('statusCurrent');
                
                if (tracker && current) {
                    tracker.classList.add('active');
                    current.textContent = statusText;
                    current.className = 'status-current';
                    if (isError) {
                        current.classList.add('error');
                    } else if (isComplete) {
                        current.classList.add('complete');
                    }
                }
            }
            
            // Submit query function
            async function submitQuery() {
                const query = document.getElementById('query').value.trim();
                const responseBox = document.getElementById('responseBox');
                const submitBtn = document.getElementById('submitBtn');
                
                if (!query) {
                    alert('Please enter a query!');
                    return;
                }
                
                if (isStreaming) {
                    alert('Please wait for the current query to complete.');
                    return;
                }
                
                // Reset UI
                responseBox.textContent = '';
                updateStatusTracker('Preparing query...', false, false);
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loading"></span> Processing...';
                isStreaming = true;
                
                try {
                    const response = await fetch('/query/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: query })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '';
                    
                    while (true) {
                        const { done, value } = await reader.read();
                        
                        if (done) break;
                        
                        buffer += decoder.decode(value, { stream: true });
                        const newlineChar = String.fromCharCode(10);
                        const lines = buffer.split(newlineChar);
                        buffer = lines.pop() || '';
                        
                        for (const line of lines) {
                            const trimmed = line.trim();
                            if (!trimmed || !trimmed.startsWith('data: ')) continue;
                            
                            try {
                                const jsonStr = trimmed.substring(6);
                                const data = JSON.parse(jsonStr);
                                
                                // Check for status messages
                                if (data.content) {
                                    const content = data.content;
                                    
                                    // Check if this is a status message
                                    if (content.startsWith('STATUS:')) {
                                        const parts = content.split('|');
                                        if (parts.length === 2) {
                                            const statusType = parts[0].substring(7); // Remove "STATUS:"
                                            const statusMessage = parts[1];
                                            
                                            // Update status tracker
                                            const isError = statusType === 'error';
                                            const isComplete = statusType === 'complete';
                                            updateStatusTracker(statusMessage, isError, isComplete);
                                            
                                            // Don't add status messages to response box
                                            continue;
                                        }
                                    }
                                    
                                    // Regular content - add to response box
                                    responseBox.textContent += content;
                                    responseBox.scrollTop = responseBox.scrollHeight;
                                }
                                if (data.error) {
                                    updateStatusTracker(`Error: ${data.error}`, true);
                                    responseBox.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                                    break;
                                }
                            } catch (e) {
                                console.warn('Failed to parse SSE data:', trimmed);
                            }
                        }
                    }
                    
                    if (buffer.trim()) {
                        try {
                            const data = JSON.parse(buffer);
                            if (data.content) {
                                const content = data.content;
                                
                                // Check if this is a status message
                                if (content.startsWith('STATUS:')) {
                                    const parts = content.split('|');
                                    if (parts.length === 2) {
                                        const statusMessage = parts[1];
                                        const statusType = parts[0].substring(7);
                                        const isError = statusType === 'error';
                                        const isComplete = statusType === 'complete';
                                        updateStatusTracker(statusMessage, isError, isComplete);
                                        // Don't add to response box
                                    }
                                } else {
                                    responseBox.textContent += content;
                                }
                            }
                        } catch (e) {
                            // Ignore parse errors for leftover buffer
                        }
                    }
                    
                } catch (error) {
                    updateStatusTracker(`Connection Error: ${error.message}`, true);
                    responseBox.innerHTML = `<div class="error">❌ Error: ${error.message}<br><br>Make sure the A2A agent is running:<br><code>uv run python -m app</code></div>`;
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Send Query →';
                    isStreaming = false;
                }
            }
            
            window.submitQuery = submitQuery;
            
            // Allow Enter key to submit (Ctrl/Cmd + Enter)
            document.addEventListener('DOMContentLoaded', function() {
                const queryTextarea = document.getElementById('query');
                if (queryTextarea) {
                    queryTextarea.addEventListener('keydown', function(e) {
                        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                            submitQuery();
                        }
                    });
                }
            });
        })();
    </script>
</body>
</html>
    """
    return html_content


@app.post("/query")
async def query_endpoint(request: Request):
    """Handle query requests (non-streaming)."""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return {"error": "Query is required"}
        
        logger.info(f"Received query: {query}")
        response = await run_agent(query)
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        return {"error": str(e)}


@app.post("/query/stream")
async def query_stream_endpoint(request: Request):
    """Handle streaming query requests."""
    # Read request body BEFORE creating generator
    try:
        body = await request.body()
        if not body:
            async def error_gen():
                newline = "\n"
                yield f"data: {json.dumps({'error': 'Request body is empty'})}{newline}{newline}"
            return StreamingResponse(error_gen(), media_type="text/event-stream")
        
        data = json.loads(body)
        query = data.get("query", "")
        
        if not query:
            async def error_gen():
                newline = "\n"
                yield f"data: {json.dumps({'error': 'Query is required'})}{newline}{newline}"
            return StreamingResponse(error_gen(), media_type="text/event-stream")
    except Exception as e:
        async def error_gen():
            newline = "\n"
            yield f"data: {json.dumps({'error': f'Error reading request: {str(e)}'})}{newline}{newline}"
        return StreamingResponse(error_gen(), media_type="text/event-stream")
    
    logger.info(f"Streaming query: {query[:100]}...")
    
    async def generate():
        try:
            # Send status: Starting
            newline = "\n"
            yield f"data: {json.dumps({'content': 'STATUS:starting|🚀 Starting query processing...'})}{newline}{newline}"
            logger.info(f"Sent initial status for query: {query}")
            
            # Stream directly from A2A agent
            chunk_count = 0
            newline = "\n"
            async for chunk in stream_a2a_agent(query):
                if chunk:
                    chunk_count += 1
                    yield f"data: {json.dumps({'content': chunk})}{newline}{newline}"
                    
                    if chunk_count % 10 == 0:
                        logger.info(f"Streamed {chunk_count} chunks so far...")
            
            logger.info(f"Streaming complete. Total chunks: {chunk_count}")
            
        except Exception as e:
            logger.error(f"Error streaming query: {e}", exc_info=True)
            newline = "\n"
            yield f"data: {json.dumps({'error': str(e)})}{newline}{newline}"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
