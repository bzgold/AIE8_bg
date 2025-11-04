"""Tool for calling the A2A agent via HTTP."""
import asyncio
import logging
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def call_a2a_agent(query: str, base_url: str = "http://localhost:10000") -> str:
    """Call the A2A research agent and return the response.
    
    Args:
        query: The question or query to send to the A2A agent
        base_url: Base URL of the A2A agent server
        
    Returns:
        The agent's text response
    """
    try:
        # Create HTTP client with extended timeout
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
            # Initialize resolver and fetch agent card
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=base_url,
            )
            
            logger.info(f"Fetching agent card from {base_url}")
            agent_card = await resolver.get_agent_card()
            logger.info(f"Agent capabilities: {[skill.name for skill in agent_card.skills]}")
            
            # Initialize A2A client
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            
            # Prepare message payload
            send_message_payload: dict[str, Any] = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': query}
                    ],
                    'message_id': uuid4().hex,
                },
            }
            
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            logger.info(f"Sending query to A2A agent: {query}")
            response = await client.send_message(request)
            
            # Extract the text response from A2A response structure
            if response.root and response.root.result:
                result = response.root.result
                if result.messages and len(result.messages) > 0:
                    last_message = result.messages[-1]
                    if last_message.parts and len(last_message.parts) > 0:
                        # Extract text from message parts
                        for part in last_message.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                return part.root.text
                        # Fallback to string representation
                        return str(last_message.parts[-1])
                
                # Check for artifacts (final results)
                if result.artifacts and len(result.artifacts) > 0:
                    artifact = result.artifacts[-1]
                    if artifact.parts and len(artifact.parts) > 0:
                        for part in artifact.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                return part.root.text
            
            # Fallback: return formatted JSON
            return response.model_dump_json(indent=2, exclude_none=True)
            
    except Exception as e:
        error_msg = f"Error calling A2A agent: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg) from e


async def stream_a2a_agent(query: str, base_url: str = "http://localhost:10000"):
    """Stream responses from the A2A research agent.
    
    Args:
        query: The question or query to send to the A2A agent
        base_url: Base URL of the A2A agent server
        
    Yields:
        Chunks of text as they arrive from the agent
    """
    try:
        logger.info(f"stream_a2a_agent called with query: {query[:50]}...")
        
        # Longer timeout to allow for helpfulness evaluation loops (up to 10 iterations)
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as httpx_client:
            logger.info("HTTP client created")
            # Initialize resolver and fetch agent card
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=base_url,
            )
            
            # Send status: Initializing
            logger.info("Yielding initializing status...")
            yield "STATUS:initializing|🚀 Initializing A2A connection..."
            logger.info("Fetching agent card...")
            agent_card = await resolver.get_agent_card()
            logger.info(f"Agent card retrieved: {agent_card.name}")
            
            # Send status: Connected
            yield "STATUS:connected|✅ Connected to A2A agent"
            
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            logger.info("A2A client initialized, preparing streaming request")
            
            # Prepare streaming message request
            send_message_payload: dict[str, Any] = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': query}
                    ],
                    'message_id': uuid4().hex,
                },
            }
            
            from a2a.types import SendStreamingMessageRequest
            streaming_request = SendStreamingMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            logger.info(f"Streaming query to A2A agent: {query[:50]}...")
            logger.info(f"Base URL: {base_url}")
            
            # Send status: Sending query
            yield "STATUS:sending|📤 Sending query to research agent..."
            logger.info("Sent initial status message")
            
            chunk_count = 0
            last_yield_time = None
            last_text_yield_time = None
            import asyncio
            from datetime import datetime
            start_time = datetime.now()
            
            # Stream the response with timeout
            logger.info("Starting to stream response from A2A agent...")
            yield "STATUS:waiting|⏳ Waiting for agent response..."
            async for chunk in client.send_message_streaming(streaming_request):
                logger.debug(f"Received chunk #{chunk_count + 1}")
                chunk_count += 1
                current_time = datetime.now()
                elapsed = (current_time - start_time).total_seconds()
                
                # Send periodic status updates if no text yet
                if not last_text_yield_time:
                    if elapsed > 3 and chunk_count == 1:
                        yield "STATUS:processing|🔄 Agent is processing your query..."
                    elif elapsed > 15 and chunk_count < 5:
                        yield "STATUS:evaluating|🧠 Running helpfulness evaluation (may take 30-60 seconds)..."
                    elif elapsed > 45:
                        yield "STATUS:evaluating|⏳ Still evaluating (the helpfulness loop can take up to 2-3 minutes)..."
                    elif elapsed > 120:
                        yield "STATUS:evaluating|🔄 Complex query - agent is doing multiple evaluation passes..."
                
                # Extract text from chunks - try multiple approaches
                text_found = False
                
                # First, try dumping the whole chunk to find text anywhere
                if not text_found:
                    try:
                        chunk_dict = chunk.model_dump(mode='json', exclude_none=True) if hasattr(chunk, 'model_dump') else None
                        if chunk_dict:
                            # Recursively search for text fields
                            def find_text(obj, path=""):
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if key == 'text' and isinstance(value, str) and value.strip():
                                            return value
                                        result = find_text(value, f"{path}.{key}")
                                        if result:
                                            return result
                                elif isinstance(obj, list):
                                    for i, item in enumerate(obj):
                                        result = find_text(item, f"{path}[{i}]")
                                        if result:
                                            return result
                                return None
                            
                            found_text = find_text(chunk_dict)
                            if found_text:
                                if not last_text_yield_time:
                                    yield "STATUS:receiving|📥 Receiving response from agent..."
                                yield found_text
                                text_found = True
                                last_text_yield_time = current_time
                                last_yield_time = current_time
                                logger.info(f"Yielded text from chunk dump {chunk_count}: {found_text[:50]}...")
                    except Exception as e:
                        logger.debug(f"Could not dump chunk: {e}")
                
                if hasattr(chunk, 'root') and chunk.root:
                    # Try to extract text from various chunk structures
                    if hasattr(chunk.root, 'result') and chunk.root.result:
                        result = chunk.root.result
                        
                        # Check messages first (streaming updates)
                        if hasattr(result, 'messages') and result.messages:
                            for msg in result.messages:
                                if hasattr(msg, 'parts') and msg.parts:
                                    for part in msg.parts:
                                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                            text = part.root.text
                                            if text and text.strip():
                                                # If this is the first text chunk, send status update
                                                if not last_text_yield_time:
                                                    yield "STATUS:receiving|📥 Receiving response from agent..."
                                                yield text
                                                text_found = True
                                                last_yield_time = current_time
                                                last_text_yield_time = current_time
                                                logger.info(f"Yielded text chunk {chunk_count}: {text[:50]}...")
                                        elif hasattr(part, 'root') and part.root:
                                            # Try to find text in nested structure
                                            text = str(part.root)
                                            if text and text != "None" and text.strip():
                                                yield text
                                                text_found = True
                                                last_yield_time = current_time
                        
                        # Check artifacts (final results)
                        if hasattr(result, 'artifacts') and result.artifacts:
                            for artifact in result.artifacts:
                                if hasattr(artifact, 'parts') and artifact.parts:
                                    for part in artifact.parts:
                                        if hasattr(part, 'root'):
                                            if hasattr(part.root, 'text'):
                                                text = part.root.text
                                                if text and text.strip():
                                                    if not last_text_yield_time:
                                                        yield "STATUS:receiving|📥 Receiving response from agent..."
                                                    yield text
                                                    text_found = True
                                                    last_yield_time = current_time
                                                    last_text_yield_time = current_time
                                                    logger.info(f"Yielded artifact text chunk {chunk_count}: {text[:50]}...")
                                            else:
                                                # Try model dump to find text
                                                try:
                                                    if hasattr(part.root, 'model_dump'):
                                                        dumped = part.root.model_dump()
                                                        if 'text' in dumped and dumped['text']:
                                                            text = dumped['text']
                                                            if text and text.strip():
                                                                if not last_text_yield_time:
                                                                    yield "STATUS:receiving|📥 Receiving response from agent..."
                                                                yield text
                                                                text_found = True
                                                                last_yield_time = current_time
                                                                last_text_yield_time = current_time
                                                                logger.info(f"Yielded dumped text chunk {chunk_count}: {text[:50]}...")
                                                except:
                                                    pass
                    
                    # Also check task state updates
                    if hasattr(chunk.root, 'result') and hasattr(chunk.root.result, 'task_state'):
                        task_state = chunk.root.result.task_state
                        if task_state:
                            yield f"STATUS:task_state|📊 Task State: {task_state}"
                            text_found = True
                
                # If no text found but we have a chunk, log structure for debugging
                if not text_found:
                    # Log chunk structure for debugging on first few chunks
                    if chunk_count <= 3:
                        logger.info(f"Chunk #{chunk_count} structure: {type(chunk)}, has root: {hasattr(chunk, 'root')}")
                        if hasattr(chunk, 'root') and chunk.root:
                            if hasattr(chunk.root, 'result'):
                                result = chunk.root.result
                                logger.info(f"  Result has messages: {hasattr(result, 'messages') and result.messages is not None}")
                                logger.info(f"  Result has artifacts: {hasattr(result, 'artifacts') and result.artifacts is not None}")
                                # Try to dump the structure to see what we have
                                try:
                                    if hasattr(result, 'model_dump'):
                                        dumped = result.model_dump(mode='json', exclude_none=True)
                                        logger.info(f"  Result structure keys: {list(dumped.keys()) if isinstance(dumped, dict) else 'not dict'}")
                                        # Log full structure for first chunk
                                        if chunk_count == 1:
                                            import json
                                            logger.info(f"  Full result structure: {json.dumps(dumped, indent=2)[:1000]}")
                                except Exception as e:
                                    logger.warning(f"  Could not dump result: {e}")
                            # Also try to dump the whole chunk
                            try:
                                if hasattr(chunk.root, 'model_dump'):
                                    chunk_dumped = chunk.root.model_dump(mode='json', exclude_none=True)
                                    logger.info(f"  Root structure keys: {list(chunk_dumped.keys()) if isinstance(chunk_dumped, dict) else 'not dict'}")
                            except:
                                pass
                    # Yield progress indicator every 20 chunks if no text yet
                    if chunk_count % 20 == 0 and not last_text_yield_time:
                        yield "."  # Progress indicator every 20 chunks
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)
            
            logger.info(f"Streaming finished. Total chunks: {chunk_count}, Text chunks: {bool(last_text_yield_time)}")
            
            # Send completion status
            yield "STATUS:complete|✅ Processing complete"
            
            # If we got very few chunks or no text, the agent might have sent everything at once
            if chunk_count < 3 or not last_text_yield_time:
                yield "\n\n✅ Processing complete.\n"
                        
    except Exception as e:
        error_msg = f"Error streaming from A2A agent: {str(e)}"
        logger.error(error_msg, exc_info=True)
        yield f"STATUS:error|❌ Error: {error_msg}"
        yield f"❌ Error: {error_msg}"

