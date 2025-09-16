"""
Agent Service for Financial ReAct Agent
Provides factory methods to create and configure the agent with all necessary tools
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from .react_agent import FinancialReactAgent, FinancialAgentResponse
from .llm_clients import LLMClientFactory
from .tools.rag_kb import RAGKnowledgeBaseTool
from .tools.get_weather_info import GetWeatherInfoTool
from .tools.get_user_profile import GetUserProfileTool
from .tools.get_chat_history import GetChatHistoryTool

logger = logging.getLogger(__name__)

class AgentService:
    """Service for creating and managing ReAct agents"""
    
    @staticmethod
    def create_agent(model_name: str = "claude-3-sonnet-20240229-v1:0") -> FinancialReactAgent:
        """
        Create a fully configured ReAct agent with all tools
        
        Args:
            model_name: The name of the model to use (default: Claude Sonnet)
            
        Returns:
            FinancialReactAgent: Configured agent instance
        """
        try:
            # Create LLM client
            llm = LLMClientFactory.create_llm(model_name)
            
            # Create tools
            tools = AgentService._create_tools()
            
            # Create agent
            agent = FinancialReactAgent(
                llm=llm,
                tools=tools,
                verbose=True
            )
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    @staticmethod
    def _create_tools() -> List[Any]:
        """Create all tools needed for the agent"""
        tools = []
        
        # Create RAG Knowledge Base tool
        try:
            rag_tool = RAGKnowledgeBaseTool()
            tools.append(rag_tool)
            logger.info("RAG Knowledge Base tool created successfully")
        except Exception as e:
            logger.error(f"Error creating RAG tool: {str(e)}")
        
        # Create Weather Info tool
        try:
            weather_tool = GetWeatherInfoTool()
            tools.append(weather_tool)
            logger.info("Weather Info tool created successfully")
        except Exception as e:
            logger.error(f"Error creating Weather tool: {str(e)}")
        
        # Create User Profile tool
        try:
            profile_tool = GetUserProfileTool()
            tools.append(profile_tool)
            logger.info("User Profile tool created successfully")
        except Exception as e:
            logger.error(f"Error creating User Profile tool: {str(e)}")
        
        # Create Chat History tool
        try:
            history_tool = GetChatHistoryTool()
            tools.append(history_tool)
            logger.info("Chat History tool created successfully")
        except Exception as e:
            logger.error(f"Error creating Chat History tool: {str(e)}")
        
        return tools
    
    @staticmethod
    async def process_query(
        agent: FinancialReactAgent,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> FinancialAgentResponse:
        """
        Process a user query with the agent
        
        Args:
            agent: The agent instance
            query: User's query text
            user_id: User ID for context retrieval
            conversation_id: Optional conversation ID for history
            
        Returns:
            FinancialAgentResponse: The agent's response
        """
        try:
            # Set up context with user ID and conversation ID
            context = {
                "user_id": user_id,
                "conversation_id": conversation_id
            }
            
            # Process the query
            response = await agent.aprocess_query(query, context)
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise