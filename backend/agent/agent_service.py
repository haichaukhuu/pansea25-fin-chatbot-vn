"""
Agent Service for Financial ReAct Agent
Provides factory methods to create and configure the agent with all necessary tools
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, AsyncGenerator

from .react_agent import FinancialReactAgent, FinancialAgentResponse
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

logger = logging.getLogger(__name__)

class AgentService:
    """Service for creating and managing ReAct agents"""
    
    @staticmethod
    def create_agent(use_vietnamese_model: bool = True) -> FinancialReactAgent:
        """
        Create a fully configured ReAct agent with all tools
        
        Args:
            use_vietnamese_model: Whether to use SEA-LION for Vietnamese response generation
            
        Returns:
            FinancialReactAgent: Configured agent instance
        """
        try:
            logger.info("Creating financial ReAct agent...")
            
            # Create the agent
            agent = FinancialReactAgent(use_vietnamese_model=use_vietnamese_model, use_modern_implementation=True)
            
            logger.info("Successfully created financial ReAct agent")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    @staticmethod
    async def process_query(
        agent: FinancialReactAgent,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        stream: bool = True
    ) -> Union[FinancialAgentResponse, AsyncGenerator[str, None]]:
        """
        Process a user query with the agent
        
        Args:
            agent: The agent instance
            query: User's query text
            user_id: User ID for context retrieval
            conversation_id: Optional conversation ID for history
            stream: Whether to stream the response
            
        Returns:
            FinancialAgentResponse or AsyncGenerator for streaming
        """
        try:
            # Set up context with user ID and conversation ID
            context = {
                "user_id": user_id,
                "conversation_id": conversation_id
            }
            
            # Process the query
            response = await agent.aprocess_query(query, context, stream=stream)
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            
            # Return appropriate error response
            error_response = FinancialAgentResponse(
                response=f"Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi của bạn: {str(e)}",
                conversation_id=conversation_id
            )
            
            if stream:
                async def error_generator():
                    yield error_response.response
                return error_generator()
            else:
                return error_response
    
    @staticmethod
    def reset_conversation_memory(agent: FinancialReactAgent, conversation_id: Optional[str] = None):
        """
        Reset conversation memory for the agent
        
        Args:
            agent: The agent instance
            conversation_id: Optional specific conversation to reset
        """
        try:
            agent.reset_memory(conversation_id)
            logger.info(f"Reset memory for conversation: {conversation_id or 'all'}")
        except Exception as e:
            logger.error(f"Error resetting memory: {str(e)}")
    
    @staticmethod
    def get_conversation_history(
        agent: FinancialReactAgent, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a specific conversation
        
        Args:
            agent: The agent instance
            conversation_id: Conversation ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        try:
            return agent.get_conversation_history(conversation_id, limit)
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []
    
    @staticmethod
    def get_agent_info(agent: FinancialReactAgent) -> Dict[str, Any]:
        """
        Get information about the agent configuration
        
        Args:
            agent: The agent instance
            
        Returns:
            Dictionary with agent information
        """
        try:
            return {
                "model_config": {
                    "reasoning_model": "Claude Sonnet 4 (anthropic.claude-sonnet-4-20250514-v1:0)",
                    "response_model": "SEA-LION" if agent.use_vietnamese_model else "Claude Sonnet 4",
                    "streaming_enabled": True
                },
                "tools": [tool.name for tool in agent.tools] if hasattr(agent, 'tools') else [],
                "capabilities": [
                    "Vietnamese agricultural financial advice",
                    "Real-time weather information",
                    "User profile management", 
                    "Conversation memory",
                    "RAG knowledge base",
                    "Multi-turn conversations",
                    "Streaming responses"
                ]
            }
        except Exception as e:
            logger.error(f"Error getting agent info: {str(e)}")
            return {"error": str(e)}