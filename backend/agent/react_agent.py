"""
Unified ReAct Agent Implementation for Vietnamese Agricultural Financial Services
This implementation combines the best features from both legacy and modern approaches.

Supports both:
1. Legacy approach: Basic ReAct agent with ConversationBufferMemory
2. Modern approach: LangGraph-based agent with MemorySaver and streaming

Workflow:
User input → Claude Sonnet 4 (ReAct reasoning + tool usage) → SEA-LION (Vietnamese response) → Output
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from uuid import uuid4

# Legacy LangChain imports
from langchain.agents import AgentExecutor, create_react_agent as create_legacy_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

# Modern LangChain Core and LangGraph imports
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from .llm_clients import LLMClientFactory
from .tools.rag_kb import RAGKnowledgeBaseTool
from .tools.get_weather_info import GetWeatherInfoTool
from .tools.get_user_profile import GetUserProfileTool
from .tools.get_chat_history import GetChatHistoryTool

logger = logging.getLogger(__name__)


def clean_response_content(response: str) -> str:
    """
    Clean the response content to remove any unwanted headers or prefixes
    that might be added by the AI models.
    
    Args:
        response: Raw response from the AI model
        
    Returns:
        Cleaned response content
    """
    if not response:
        return response
    
    # List of potential headers that might cause duplication
    headers_to_remove = [
        "Phản hồi cuối cùng:",
        "Phản hồi cuối cùng :",
        "Câu trả lời cuối cùng:",
        "Câu trả lời cuối cùng :",
        "Kết luận:",
        "Kết luận :",
        "Final response:",
        "Final answer:",
        "Response:",
        "Answer:"
    ]
    
    cleaned_response = response.strip()
    
    # Remove any of the headers if they appear at the beginning
    for header in headers_to_remove:
        if cleaned_response.lower().startswith(header.lower()):
            cleaned_response = cleaned_response[len(header):].strip()
            break
    
    return cleaned_response


class FinancialAgentResponse:
    """Enhanced response format for the financial agent with backward compatibility."""
    
    def __init__(self, 
                 response: str = "", 
                 sources: List[Dict[str, Any]] = None, 
                 tool_usage: List[Dict[str, Any]] = None,
                 is_streaming: bool = True,
                 conversation_id: Optional[str] = None):
        self.response = response
        self.sources = sources or []
        self.tool_usage = tool_usage or []
        self.is_streaming = is_streaming
        self.conversation_id = conversation_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "response": self.response,
            "sources": self.sources,
            "tool_usage": self.tool_usage,
            "is_streaming": self.is_streaming,
            "conversation_id": self.conversation_id
        }


class FinancialReactAgent:
    """
    Unified ReAct agent for Vietnamese Agricultural Financial services.
    
    Supports both legacy and modern implementations:
    - Legacy: Basic LangChain agent with ConversationBufferMemory
    - Modern: LangGraph-based agent with MemorySaver and streaming
    
    Workflow:
    1. User input → Claude Sonnet 4 (ReAct reasoning + tool usage)
    2. Claude output → SEA-LION (Vietnamese response generation)
    3. Final Vietnamese response → User
    """
    
    def __init__(self, use_vietnamese_model: bool = True, use_modern_implementation: bool = True):
        """
        Initialize the financial ReAct agent.
        
        Args:
            use_vietnamese_model: Whether to use SEA-LION for Vietnamese response generation
            use_modern_implementation: Whether to use LangGraph (True) or legacy LangChain (False)
        """
        self.use_vietnamese_model = use_vietnamese_model
        self.use_modern_implementation = use_modern_implementation
        
        # Load prompt templates
        self.system_prompt = self._load_system_prompt()
        
        # Initialize LLMs
        self.reasoning_llm = LLMClientFactory.create_claude_llm(
            temperature=0.2,
            max_tokens=4000
        )
        
        self.response_llm = None
        if use_vietnamese_model:
            try:
                # Use the new direct client for SEA-LION imported model
                self.response_llm = LLMClientFactory.create_sealion_direct_client(
                    temperature=0.3,
                    max_tokens=2000
                )
                logger.info("Successfully initialized SEA-LION direct client for Vietnamese responses")
            except Exception as e:
                logger.warning(f"Failed to initialize SEA-LION direct client: {e}")
                logger.info("Attempting to use Llama4 Maverick as fallback chat model")
                try:
                    self.response_llm = LLMClientFactory.create_llama4_maverick_llm(
                        temperature=0.4,
                        max_tokens=2000
                    )
                    logger.info("Successfully initialized Llama4 Maverick as fallback chat model")
                    # Keep use_vietnamese_model=True since we have a chat model
                except Exception as fallback_error:
                    logger.error(f"Failed to initialize Llama4 Maverick fallback: {fallback_error}")
                    logger.error("No chat model available - Claude will be used for reasoning only")
                    self.use_vietnamese_model = False
                    self.response_llm = None
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize memory and agent based on implementation choice
        if use_modern_implementation:
            self.memory = MemorySaver()
            self.agent = self._create_modern_agent()
            logger.info("Initialized modern LangGraph-based ReAct agent")
        else:
            self.memory = ConversationBufferMemory(return_messages=True)
            self.agent = self._create_legacy_agent()
            logger.info("Initialized legacy LangChain-based ReAct agent")
        
        logger.info(f"Initialized FinancialReactAgent with {len(self.tools)} tools")
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize all available tools for the agent."""
        tools = []
        
        try:
            # RAG Knowledge Base tool
            rag_tool = RAGKnowledgeBaseTool()
            tools.append(rag_tool)
            logger.info("Initialized RAG Knowledge Base tool")
        except Exception as e:
            logger.error(f"Failed to initialize RAG tool: {e}")
        
        try:
            # Weather Information tool
            weather_tool = GetWeatherInfoTool()
            tools.append(weather_tool)
            logger.info("Initialized Weather Info tool")
        except Exception as e:
            logger.error(f"Failed to initialize Weather tool: {e}")
        
        try:
            # User Profile tool
            profile_tool = GetUserProfileTool()
            tools.append(profile_tool)
            logger.info("Initialized User Profile tool")
        except Exception as e:
            logger.error(f"Failed to initialize User Profile tool: {e}")
        
        try:
            # Chat History tool
            history_tool = GetChatHistoryTool()
            tools.append(history_tool)
            logger.info("Initialized Chat History tool")
        except Exception as e:
            logger.error(f"Failed to initialize Chat History tool: {e}")
        
        return tools
    
    def _load_system_prompt(self) -> str:
        """Load and combine system prompts from files."""
        prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
        # Load the main tool-specific prompt
        tool_prompt_path = os.path.join(prompt_dir, "system_prompt_tool.txt")
        assistant_prompt_path = os.path.join(prompt_dir, "system_prompt_assistant.txt")
        
        prompts = []
        
        # Load assistant prompt first
        try:
            with open(assistant_prompt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    prompts.append(content)
        except FileNotFoundError:
            logger.warning(f"Assistant prompt file not found: {assistant_prompt_path}")
        
        # Load tool prompt
        try:
            with open(tool_prompt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    prompts.append(content)
        except FileNotFoundError:
            logger.warning(f"Tool prompt file not found: {tool_prompt_path}")
            # Fallback prompt
            prompts.append("""
Bạn là trợ lý tài chính AI chuyên nghiệp cho nông dân Việt Nam. 
Hãy suy nghĩ logic và sử dụng các công cụ phù hợp để trả lời câu hỏi.
Luôn trả lời bằng tiếng Việt và đưa ra lời khuyên thiết thực.
            """.strip())
        
        # If no prompts loaded, use fallback
        if not prompts:
            prompts.append(
                "You are a helpful financial assistant for Vietnamese farmers and small agricultural businesses. "
                "You have access to information about financial services, banking, and agricultural finance in Vietnam. "
                "You can also provide weather information to help with agricultural planning. "
                "Always be accurate, helpful, and provide sources for your information."
            )
        
        return "\n\n".join(prompts)
    
    def _load_legacy_prompt(self, prompt_type: str) -> str:
        """Load a prompt template from file (legacy format).
        
        Args:
            prompt_type: Type of prompt to load (system, human)
            
        Returns:
            Prompt template string
        """
        try:
            prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
            if prompt_type == "system":
                # Use the system prompt we already loaded
                return self.system_prompt
            else:  # human prompt
                try:
                    with open(os.path.join(prompt_dir, f"{prompt_type}_prompt.txt"), "r", encoding="utf-8") as f:
                        return f.read().strip()
                except FileNotFoundError:
                    return "Question: {input}\nThought: I need to help answer this question about financial services or agriculture in Vietnam."
        except Exception as e:
            logger.error(f"Error loading {prompt_type} prompt: {e}")
            if prompt_type == "system":
                return self.system_prompt
            else:
                return "Question: {input}\nThought: I need to help answer this question about financial services or agriculture in Vietnam."
    
    def _create_modern_agent(self) -> CompiledStateGraph:
        """Create the modern ReAct agent using LangGraph."""
        agent = create_react_agent(
            model=self.reasoning_llm,
            tools=self.tools,
            checkpointer=self.memory,
            prompt=self.system_prompt
        )
        return agent
    
    def _create_legacy_agent(self) -> AgentExecutor:
        """Create the legacy ReAct agent using LangChain."""
        human_prompt = self._load_legacy_prompt("human")
        
        react_instructions = (
            self.system_prompt
            + "\n\n"
            + human_prompt
            + "\n\nBạn có quyền truy cập các công cụ sau:\n{tools}\n\n"
              "Quy tắc sử dụng ReAct (lặp lại Thought-Action-Observation nếu cần):\n"
              "- Câu hỏi: {input}\n"
              "- Suy nghĩ: nêu lập luận ngắn gọn\n"
              "- Hành động: chọn một trong [{tool_names}]\n"
              "- Đầu vào hành động: tham số cho công cụ\n"
              "- Quan sát: kết quả từ công cụ\n"
              "...\n"
              "- Suy nghĩ: đã đủ thông tin\n"
              "- Trả lời cuối cùng (tiếng Việt): rõ ràng, súc tích, có thể thực hành\n\n"
              "Lịch sử hội thoại (tóm tắt): {chat_history}\n\n"
              "Lưu ý: Nếu thiếu thông tin, hãy hỏi lại để làm rõ. Tránh bịa đặt."
              "{agent_scratchpad}"
        )
        
        # Create prompt template
        prompt = PromptTemplate.from_template(template=react_instructions)
        
        # Create the agent
        agent = create_legacy_react_agent(
            llm=self.reasoning_llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    # Query Processing Methods
    
    def process_query(self, query: str, conversation_id: Optional[str] = None) -> FinancialAgentResponse:
        """
        Process a user query and return a response (legacy compatible method).
        
        Args:
            query: The user's query
            conversation_id: Optional conversation ID for tracking
            
        Returns:
            FinancialAgentResponse object with response, sources, and tool usage
        """
        if self.use_modern_implementation:
            # Use modern async method but run synchronously for backward compatibility
            import asyncio
            
            context = {"conversation_id": conversation_id} if conversation_id else {}
            
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.aprocess_query(query, context, stream=False))
            except RuntimeError:
                # If no event loop is running, create a new one
                return asyncio.run(self.aprocess_query(query, context, stream=False))
        else:
            return self._process_legacy_query(query, conversation_id)
    
    def _process_legacy_query(self, query: str, conversation_id: Optional[str] = None) -> FinancialAgentResponse:
        """Process a query using the legacy LangChain implementation."""
        # ENFORCE STRICT ARCHITECTURE: Claude must never chat with users
        if not self.response_llm:
            error_msg = "Error: No chat model available. Claude cannot respond to users directly. Please ensure SEA-LION or Llama4 Maverick is properly configured."
            logger.error(error_msg)
            return FinancialAgentResponse(
                response=error_msg,
                sources=[],
                tool_usage=[],
                conversation_id=conversation_id
            )
        
        # Get chat history from memory
        chat_history = self.memory.chat_memory.messages if self.memory.chat_memory.messages else []
        
        # Run the agent (Claude does reasoning and tool calling ONLY)
        result = self.agent.invoke({
            "input": query,
            "chat_history": chat_history
        })
        
        # Extract sources and tool usage
        sources = self._extract_legacy_sources(result)
        tool_usage = self._extract_legacy_tool_usage(result)
        
        # STRICT SEPARATION: Always use response_llm for user-facing responses
        claude_analysis = result["output"]
        try:
            # Check if we're using the direct SEA-LION client
            if hasattr(self.response_llm, 'generate_response'):
                # Direct SEA-LION client
                response = self.response_llm.generate_response(
                    user_query=query,
                    claude_analysis=claude_analysis
                )
                response = clean_response_content(response)
            else:
                # Traditional LangChain model (fallback like Llama4 Maverick)
                response_prompt = f"""Dựa trên phân tích và công cụ từ hệ thống AI, hãy viết câu trả lời bằng tiếng Việt.

Câu hỏi của người dùng: {query}

Phân tích từ hệ thống: {claude_analysis}

Hãy viết một câu trả lời thân thiện, hữu ích và chính xác cho nông dân Việt Nam. Sử dụng ngôn ngữ đơn giản, dễ hiểu và đưa ra lời khuyên thiết thực. Trả lời trực tiếp ."""
                
                response = self.response_llm.invoke(response_prompt)
                if hasattr(response, 'content'):
                    response = response.content
                response = clean_response_content(response)
        except Exception as e:
            logger.error(f"Error generating user response: {e}")
            # Return error instead of Claude's output
            response = f"Xin lỗi, có lỗi xảy ra khi tạo phản hồi. Vui lòng thử lại sau. Lỗi: {str(e)}"
        
        # Update memory with user query and final response (not Claude's analysis)
        self.memory.chat_memory.add_user_message(query)
        self.memory.chat_memory.add_ai_message(response)
        
        return FinancialAgentResponse(
            response=response,
            sources=sources,
            tool_usage=tool_usage,
            conversation_id=conversation_id
        )

    async def aprocess_query(self, 
                           query: str, 
                           context: Optional[Dict[str, Any]] = None,
                           stream: bool = True) -> Union[FinancialAgentResponse, AsyncGenerator[str, None]]:
        """
        Process a user query with streaming support (modern implementation).
        
        Args:
            query: User's query
            context: Additional context (user_id, conversation_id, etc.)
            stream: Whether to stream the response
            
        Returns:
            FinancialAgentResponse or async generator for streaming
        """
        if not self.use_modern_implementation:
            # Fall back to legacy method for consistency
            conversation_id = context.get("conversation_id") if context else None
            return self._process_legacy_query(query, conversation_id)
        
        context = context or {}
        user_id = context.get("user_id", "anonymous")
        conversation_id = context.get("conversation_id", str(uuid4()))
        
        # Configuration for the agent run
        config: RunnableConfig = {
            "configurable": {
                "thread_id": conversation_id,
                "user_id": user_id
            }
        }
        
        try:
            # Prepare input message
            input_message = HumanMessage(content=query)
            
            if stream:
                return self._stream_response(input_message, config, conversation_id)
            else:
                return await self._process_non_streaming(input_message, config, conversation_id)
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
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
    
    async def _stream_response(self, 
                             input_message: HumanMessage, 
                             config: RunnableConfig, 
                             conversation_id: str) -> AsyncGenerator[str, None]:
        """Stream the agent's response."""
        
        # Collect reasoning steps and final output
        reasoning_content = ""
        tool_calls = []
        
        async for chunk in self.agent.astream(
            {"messages": [input_message]}, 
            config, 
            stream_mode="values"
        ):
            if "messages" in chunk and chunk["messages"]:
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    reasoning_content = last_message.content
                    # Note: This is internal reasoning, not user-facing
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': last_message.content})}\n\n"
        
        if self.use_vietnamese_model and self.response_llm:
            try:
                # Check if we're using the direct SEA-LION client
                if hasattr(self.response_llm, 'stream_response'):
                    # Direct SEA-LION client with streaming support
                    chunk_buffer = ""
                    async for chunk in self.response_llm.stream_response(
                        user_query=input_message.content,
                        claude_analysis=reasoning_content
                    ):
                        chunk_buffer += chunk
                        # Clean each chunk to prevent headers from appearing
                        cleaned_chunk = clean_response_content(chunk_buffer) if chunk_buffer else chunk
                        # Only send the new part that was added
                        if len(cleaned_chunk) > len(chunk_buffer) - len(chunk):
                            new_content = cleaned_chunk[len(chunk_buffer) - len(chunk):]
                            yield f"data: {json.dumps({'type': 'response', 'content': new_content})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'response', 'content': cleaned_chunk[-len(chunk):] if cleaned_chunk else chunk})}\n\n"
                elif hasattr(self.response_llm, 'agenerate_response'):
                    # Direct SEA-LION client without streaming (fallback to async)
                    response = await self.response_llm.agenerate_response(
                        user_query=input_message.content,
                        claude_analysis=reasoning_content
                    )
                    # Clean and send the complete response
                    cleaned_response = clean_response_content(response)
                    yield f"data: {json.dumps({'type': 'response', 'content': cleaned_response})}\n\n"
                else:
                    # Traditional LangChain model with streaming
                    vietnamese_prompt = f"""Dựa trên thông tin sau, hãy viết câu trả lời bằng tiếng Việt:

Câu hỏi: {input_message.content}
Phân tích và suy luận: {reasoning_content}

Hãy viết một câu trả lời hữu ích, chính xác và dễ hiểu cho nông dân Việt Nam. Đưa ra lời khuyên thiết thực ."""

                    async for chunk in self.response_llm.astream(vietnamese_prompt):
                        if hasattr(chunk, 'content'):
                            cleaned_content = clean_response_content(chunk.content)
                            yield f"data: {json.dumps({'type': 'response', 'content': cleaned_content})}\n\n"
                        
            except Exception as e:
                logger.error(f"Error in Vietnamese response generation: {e}")
                # No fallback to Claude's reasoning - strict separation
                error_message = "Xin lỗi, tôi không thể tạo phản hồi phù hợp lúc này."
                yield f"data: {json.dumps({'type': 'response', 'content': error_message})}\n\n"
        else:
            # No chat model available - strict separation prevents returning Claude's reasoning
            logger.error("No chat model available for response generation")
            error_message = "Xin lỗi, hệ thống chat hiện không khả dụng."
            yield f"data: {json.dumps({'type': 'response', 'content': error_message})}\n\n"
    
    async def _process_non_streaming(self, 
                                   input_message: HumanMessage, 
                                   config: RunnableConfig, 
                                   conversation_id: str) -> FinancialAgentResponse:
        """Process query without streaming."""
        
        # Run the agent
        result = await self.agent.ainvoke(
            {"messages": [input_message]}, 
            config
        )
        
        # Extract information from result
        messages = result.get("messages", [])
        final_message = messages[-1] if messages else None
        
        reasoning_response = final_message.content if final_message else "Không có phản hồi"
        
        # Extract sources and tool usage
        sources = self._extract_modern_sources(result)
        tool_usage = self._extract_modern_tool_usage(result)
        
        if self.use_vietnamese_model and self.response_llm:
            try:
                # Check if we're using the direct SEA-LION client
                if hasattr(self.response_llm, 'agenerate_response'):
                    # Direct SEA-LION client
                    final_response = await self.response_llm.agenerate_response(
                        user_query=input_message.content,
                        claude_analysis=reasoning_response
                    )
                    final_response = clean_response_content(final_response)
                else:
                    # Traditional LangChain model (fallback like Llama4 Maverick)
                    vietnamese_prompt = f"""Dựa trên thông tin sau, hãy viết câu trả lời bằng tiếng Việt.

Câu hỏi: {input_message.content}
Phân tích và suy luận: {reasoning_response}

Hãy viết một câu trả lời hữu ích, chính xác và dễ hiểu cho nông dân Việt Nam. Đưa ra lời khuyên thiết thực ."""

                    response = await self.response_llm.ainvoke(vietnamese_prompt)
                    if hasattr(response, 'content'):
                        final_response = response.content
                    else:
                        logger.error("Chat model response has no content")
                        final_response = "Xin lỗi, tôi không thể tạo phản hồi phù hợp lúc này."
                    final_response = clean_response_content(final_response)
                    
            except Exception as e:
                logger.error(f"Error generating Vietnamese response: {e}")
                final_response = "Xin lỗi, tôi không thể tạo phản hồi phù hợp lúc này."
        else:
            # No chat model available - strict separation prevents returning Claude's reasoning
            logger.error("No chat model available for response generation")
            final_response = "Xin lỗi, hệ thống chat hiện không khả dụng."
        
        return FinancialAgentResponse(
            response=final_response,
            sources=sources,
            tool_usage=tool_usage,
            conversation_id=conversation_id
        )
    
    # Source and Tool Usage Extraction Methods
    
    def _extract_legacy_sources(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sources from the legacy agent result."""
        sources = []
        
        # Extract sources from intermediate steps
        for step in result.get("intermediate_steps", []):
            action, action_output = step
            
            # Check if this was a RAG tool call
            if action.tool == "rag_kb" and isinstance(action_output, dict):
                # Extract sources from each index
                for index_name, index_results in action_output.get("results", {}).items():
                    for item in index_results:
                        source = {
                            "content": item.get("content", ""),
                            "source": item.get("source", "Unknown"),
                            "index": index_name
                        }
                        # Add metadata if available
                        if "metadata" in item and isinstance(item["metadata"], dict):
                            source.update(item["metadata"])
                        
                        sources.append(source)
        
        return sources
    
    def _extract_legacy_tool_usage(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool usage from the legacy agent result."""
        tool_usage = []
        
        # Extract tool usage from intermediate steps
        for step in result.get("intermediate_steps", []):
            action, action_output = step
            
            tool_info = {
                "tool": action.tool,
                "tool_input": action.tool_input,
                "success": True
            }
            
            # Check if the tool execution was successful
            if isinstance(action_output, dict) and action_output.get("success") is False:
                tool_info["success"] = False
                tool_info["error"] = action_output.get("error", "Unknown error")
            
            tool_usage.append(tool_info)
        
        return tool_usage
    
    def _extract_modern_sources(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sources from the modern agent result."""
        sources = []
        
        # Check messages for tool calls with sources
        messages = result.get("messages", [])
        for message in messages:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.get("name") == "rag_kb":
                        # Extract sources from tool result
                        pass  # Implementation depends on actual tool response format
        
        return sources
    
    def _extract_modern_tool_usage(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool usage from the modern agent result."""
        tool_usage = []
        
        messages = result.get("messages", [])
        for message in messages:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_info = {
                        "tool": tool_call.get("name", "unknown"),
                        "tool_input": tool_call.get("args", {}),
                        "success": True  # Modern implementation typically succeeds or raises exception
                    }
                    tool_usage.append(tool_info)
        
        return tool_usage
    
    # Memory Management Methods
    
    def reset_memory(self, conversation_id: Optional[str] = None):
        """Reset conversation memory."""
        if self.use_modern_implementation:
            if conversation_id:
                # Reset specific conversation
                # Note: MemorySaver doesn't have built-in reset for specific threads
                # This would require custom implementation
                logger.info(f"Memory reset requested for conversation: {conversation_id}")
            else:
                # Reset all memory
                self.memory = MemorySaver()
                logger.info("All conversation memory reset")
        else:
            # Legacy memory reset
            self.memory = ConversationBufferMemory(return_messages=True)
            logger.info("Legacy conversation memory reset")
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a specific thread."""
        try:
            if self.use_modern_implementation:
                # This would require accessing the checkpointer's stored data
                # Implementation depends on the specific checkpointer used
                logger.info(f"Conversation history requested for: {conversation_id}")
                return []
            else:
                # Legacy memory - return recent messages
                messages = self.memory.chat_memory.messages[-limit*2:] if self.memory.chat_memory.messages else []
                history = []
                for i in range(0, len(messages), 2):
                    if i + 1 < len(messages):
                        history.append({
                            "user": messages[i].content if hasattr(messages[i], 'content') else str(messages[i]),
                            "assistant": messages[i+1].content if hasattr(messages[i+1], 'content') else str(messages[i+1])
                        })
                return history
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []


# Backward Compatibility Aliases
ImprovedFinancialReactAgent = FinancialReactAgent  # For backward compatibility