"""
🌊 Real-Time Streaming System for AI Sports Debate Arena
Provides WebSocket connections, streaming responses, and real-time user experience
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, AsyncGenerator, Set
from datetime import datetime
from collections import defaultdict
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class StreamMessage:
    """Structure for streaming messages"""
    type: str
    content: Any
    timestamp: str
    debate_id: str
    user_id: str
    sequence: int
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)

class StreamingSession:
    """Manages individual streaming session"""
    
    def __init__(self, user_id: str, debate_id: str):
        self.user_id = user_id
        self.debate_id = debate_id
        self.session_id = f"{user_id}_{debate_id}_{int(time.time())}"
        self.start_time = datetime.utcnow()
        self.sequence = 0
        self.message_buffer: List[StreamMessage] = []
        self.is_active = True
        self.last_heartbeat = time.time()
        
        # Performance tracking
        self.messages_sent = 0
        self.bytes_sent = 0
        self.connection_quality = "excellent"
        
    def create_message(self, msg_type: str, content: Any, metadata: Dict[str, Any] = None) -> StreamMessage:
        """Create a new stream message"""
        self.sequence += 1
        return StreamMessage(
            type=msg_type,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            debate_id=self.debate_id,
            user_id=self.user_id,
            sequence=self.sequence,
            metadata=metadata or {}
        )
    
    def add_message(self, message: StreamMessage):
        """Add message to buffer"""
        self.message_buffer.append(message)
        self.messages_sent += 1
        self.bytes_sent += len(message.to_json().encode())
        
        # Keep only last 100 messages in buffer
        if len(self.message_buffer) > 100:
            self.message_buffer = self.message_buffer[-100:]
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = time.time()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "debate_id": self.debate_id,
            "duration_seconds": duration,
            "messages_sent": self.messages_sent,
            "bytes_sent": self.bytes_sent,
            "connection_quality": self.connection_quality,
            "is_active": self.is_active,
            "last_heartbeat": self.last_heartbeat
        }

class RealTimeStreamer:
    """Production real-time streaming system"""
    
    def __init__(self):
        self.active_sessions: Dict[str, StreamingSession] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.is_processing = False
        
        # Performance metrics
        self.total_sessions = 0
        self.total_messages = 0
        self.total_bytes = 0
        
        # WebSocket connections (would be WebSocket objects in real implementation)
        self.websocket_connections: Dict[str, Any] = {}
        
    async def start_streaming_session(self, user_id: str, debate_id: str, 
                                    connection_info: Dict[str, Any] = None) -> StreamingSession:
        """Start a new streaming session"""
        session = StreamingSession(user_id, debate_id)
        
        self.active_sessions[session.session_id] = session
        self.user_sessions[user_id].add(session.session_id)
        self.total_sessions += 1
        
        # Send initial connection message
        initial_msg = session.create_message(
            "session_started",
            {
                "message": "🌊 Real-time streaming connected!",
                "session_id": session.session_id,
                "capabilities": ["real_time_updates", "typing_indicators", "live_analytics"],
                "connection_quality": "excellent"
            }
        )
        
        await self.send_message(session.session_id, initial_msg)
        
        logger.info(f"Started streaming session {session.session_id} for user {user_id}")
        return session
    
    async def send_message(self, session_id: str, message: StreamMessage):
        """Send message to streaming session"""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            return
        
        session.add_message(message)
        self.total_messages += 1
        self.total_bytes += len(message.to_json().encode())
        
        # Add to message queue for processing
        await self.message_queue.put((session_id, message))
        
        # Start processing if not already running
        if not self.is_processing:
            asyncio.create_task(self._process_message_queue())
    
    async def stream_debate_response(self, session_id: str, content: str, 
                                   chunk_size: int = 50, delay: float = 0.1) -> AsyncGenerator[StreamMessage, None]:
        """Stream debate content in real-time chunks"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Break content into chunks for streaming effect
        words = content.split()
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            if not session.is_active:
                break
                
            # Create streaming message
            msg = session.create_message(
                "debate_chunk",
                {
                    "chunk": chunk,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "is_final": i == len(chunks) - 1,
                    "typing_indicator": i < len(chunks) - 1
                },
                metadata={"streaming": True, "chunk_size": len(chunk)}
            )
            
            await self.send_message(session_id, msg)
            yield msg
            
            # Add delay for streaming effect (except for last chunk)
            if i < len(chunks) - 1:
                await asyncio.sleep(delay)
        
        # Send completion message
        completion_msg = session.create_message(
            "debate_chunk_complete",
            {
                "message": "Debate response completed",
                "total_chunks_sent": len(chunks),
                "total_words": len(words)
            }
        )
        
        await self.send_message(session_id, completion_msg)
        yield completion_msg
    
    async def send_typing_indicator(self, session_id: str, is_typing: bool = True):
        """Send typing indicator to show AI is thinking"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        msg = session.create_message(
            "typing_indicator",
            {
                "is_typing": is_typing,
                "message": "🤖 AI is analyzing and crafting response..." if is_typing else "🤖 Analysis complete"
            }
        )
        
        await self.send_message(session_id, msg)
    
    async def send_live_analytics(self, session_id: str, analytics_data: Dict[str, Any]):
        """Send live analytics updates during debate"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        msg = session.create_message(
            "live_analytics",
            {
                "analytics": analytics_data,
                "update_time": datetime.utcnow().isoformat(),
                "chart_data": {
                    "confidence_score": analytics_data.get("confidence", 85),
                    "data_sources": analytics_data.get("sources", 3),
                    "processing_time": analytics_data.get("processing_time", 2.5)
                }
            },
            metadata={"premium_feature": True}
        )
        
        await self.send_message(session_id, msg)
    
    async def send_system_notification(self, session_id: str, notification: Dict[str, Any]):
        """Send system notifications (upgrades, limits, etc.)"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        msg = session.create_message(
            "system_notification",
            notification,
            metadata={"priority": notification.get("priority", "normal")}
        )
        
        await self.send_message(session_id, msg)
    
    async def end_streaming_session(self, session_id: str, reason: str = "completed"):
        """End streaming session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        session.is_active = False
        
        # Send final message
        final_msg = session.create_message(
            "session_ended",
            {
                "reason": reason,
                "session_stats": session.get_session_stats(),
                "message": "🌊 Streaming session ended"
            }
        )
        
        await self.send_message(session_id, final_msg)
        
        # Clean up
        self.user_sessions[session.user_id].discard(session_id)
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
        
        # Keep session in history for a while before cleanup
        asyncio.create_task(self._cleanup_session_later(session_id))
        
        logger.info(f"Ended streaming session {session_id}: {reason}")
    
    async def broadcast_to_user(self, user_id: str, message_type: str, content: Any):
        """Broadcast message to all sessions for a user"""
        user_session_ids = self.user_sessions.get(user_id, set())
        
        for session_id in user_session_ids.copy():  # Copy to avoid modification during iteration
            session = self.active_sessions.get(session_id)
            if session and session.is_active:
                msg = session.create_message(message_type, content)
                await self.send_message(session_id, msg)
    
    async def get_streaming_stats(self) -> Dict[str, Any]:
        """Get comprehensive streaming statistics"""
        active_count = len([s for s in self.active_sessions.values() if s.is_active])
        
        # Connection quality distribution
        quality_dist = defaultdict(int)
        for session in self.active_sessions.values():
            if session.is_active:
                quality_dist[session.connection_quality] += 1
        
        return {
            "active_sessions": active_count,
            "total_sessions": self.total_sessions,
            "total_messages": self.total_messages,
            "total_bytes": self.total_bytes,
            "avg_messages_per_session": self.total_messages / max(1, self.total_sessions),
            "connection_quality_distribution": dict(quality_dist),
            "queue_size": self.message_queue.qsize()
        }
    
    async def _process_message_queue(self):
        """Process message queue (simulates WebSocket sending)"""
        self.is_processing = True
        
        try:
            while not self.message_queue.empty():
                try:
                    session_id, message = await asyncio.wait_for(
                        self.message_queue.get(), timeout=1.0
                    )
                    
                    # Simulate sending to WebSocket
                    # In real implementation: await websocket.send(message.to_json())
                    logger.debug(f"Streaming message to {session_id}: {message.type}")
                    
                    # Simulate network delay
                    await asyncio.sleep(0.01)
                    
                except asyncio.TimeoutError:
                    break
                    
        finally:
            self.is_processing = False
    
    async def _cleanup_session_later(self, session_id: str, delay: int = 300):
        """Clean up session after delay (5 minutes)"""
        await asyncio.sleep(delay)
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.debug(f"Cleaned up session {session_id}")

# Global streaming instance
real_time_streamer = RealTimeStreamer()

# Streaming utilities
async def create_streaming_response(session_id: str, content: str, 
                                  response_type: str = "debate_response") -> AsyncGenerator[Dict[str, Any], None]:
    """Create streaming response for any content"""
    
    # Send typing indicator first
    await real_time_streamer.send_typing_indicator(session_id, True)
    await asyncio.sleep(0.5)  # Brief pause for realism
    
    # Stream the content
    async for message in real_time_streamer.stream_debate_response(session_id, content):
        yield {
            "type": response_type,
            "content": message.content,
            "streaming": True,
            "metadata": message.metadata
        }
    
    # Stop typing indicator
    await real_time_streamer.send_typing_indicator(session_id, False)

async def send_premium_analytics_stream(session_id: str, analytics_data: Dict[str, Any]):
    """Send premium analytics as streaming update"""
    await real_time_streamer.send_live_analytics(session_id, analytics_data)

async def send_tier_upgrade_notification(session_id: str, current_tier: str, suggested_tier: str):
    """Send tier upgrade notification via stream"""
    notification = {
        "type": "upgrade_suggestion",
        "current_tier": current_tier,
        "suggested_tier": suggested_tier,
        "message": f"💡 Unlock more features with {suggested_tier.title()} tier!",
        "benefits": ["More debates", "Advanced analytics", "Priority support"],
        "cta": "Upgrade Now"
    }
    
    await real_time_streamer.send_system_notification(session_id, notification) 