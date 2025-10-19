"""
Shared memory hook for multi-agent systems.

This module provides a reusable ShortTermMemoryHook that can be used by all agents
in the multi-agent system to share conversation context while maintaining
separate actor identities.
"""

import logging
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent

logger = logging.getLogger("agentcore-memory")

class ShortTermMemoryHook(HookProvider):
    """
    Memory hook for sharing conversation context across agents.
    
    Each agent gets its own unique actor_id but shares the same session_id,
    allowing for both individual agent memory and shared conversation context.
    """
    
    def __init__(self, memory_client, memory_id: str):
        """
        Initialize the memory hook.
        
        Args:
            memory_client: AgentCore memory client instance
            memory_id (str): Shared memory ID for all agents
        """
        self.memory_client = memory_client
        self.memory_id = memory_id
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load recent conversation history when agent starts"""
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            # Get last 5 conversation turns from shared session
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=5,
                branch_name="main"
            )
            
            if recent_turns:
                # Format conversation history for context
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        role = message['role'].lower()
                        content = message['content']['text']
                        context_messages.append(f"{role.title()}: {content}")
                
                context = "\n".join(context_messages)
                logger.info(f"🧠 [{actor_id}] Loaded context from memory")
                
                # Add context to agent's system prompt
                event.agent.system_prompt += f"\n\nRecent conversation history:\n{context}\n\nContinue the conversation naturally based on this context."
                
                logger.info(f"✅ [{actor_id}] Loaded {len(recent_turns)} recent conversation turns")
            else:
                logger.info(f"📝 [{actor_id}] No previous conversation history found")
                
        except Exception as e:
            logger.error(f"❌ [{actor_id}] Failed to load conversation history: {e}")
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store conversation turns in shared memory"""
        messages = event.agent.messages
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            # Store message in shared memory with unique actor_id but shared session_id
            self.memory_client.create_event(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                messages=[(messages[-1]["content"][0]["text"], messages[-1]["role"])]
            )
            
            logger.info(f"💾 [{actor_id}] Stored message in shared memory")
            
        except Exception as e:
            logger.error(f"❌ [{actor_id}] Failed to store message: {e}")
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """Register memory hooks with the agent"""
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)