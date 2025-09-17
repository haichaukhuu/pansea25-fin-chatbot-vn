import json
import os
from typing import Dict, List, Any, Optional, Union

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

from .llm_clients import LLMClientFactory
from .tools import RAGKnowledgeBaseTool, GetWeatherInfoTool


class FinancialAgentResponse:
    """Response format for the financial agent."""
    
    def __init__(self, response: str, sources: List[Dict[str, Any]] = None, 
                 tool_usage: List[Dict[str, Any]] = None):
        self.response = response
        self.sources = sources or []
        self.tool_usage = tool_usage or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "sources": self.sources,
            "tool_usage": self.tool_usage
        }


class FinancialReactAgent:
    """ReAct agent for financial services in Vietnam."""
    
    def __init__(self, use_vietnamese_model: bool = True):
        """Initialize the financial ReAct agent.
        
        Args:
            use_vietnamese_model: Whether to use the Vietnamese-optimized model for responses
        """
        # Load prompt templates
        self.system_prompt = self._load_prompt("system")
        self.human_prompt = self._load_prompt("human")
        
        # Initialize tools
        self.tools = [
            RAGKnowledgeBaseTool(),
            GetWeatherInfoTool()
        ]
        
        # Initialize LLMs
        self.reasoning_llm = LLMClientFactory.create_claude_llm(temperature=0.2)
        self.response_llm = LLMClientFactory.create_llama_llm(temperature=0.7) if use_vietnamese_model else self.reasoning_llm
        
        # Create the agent
        self.agent = self._create_agent()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(return_messages=True)
    
    def _load_prompt(self, prompt_type: str) -> str:
        """Load a prompt template from file.
        
        Args:
            prompt_type: Type of prompt to load (system, human)
            
        Returns:
            Prompt template string
        """
        try:
            prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
            if prompt_type == "system":
                # Prefer the assistant system prompt and append tool guidance if available
                sys_path = os.path.join(prompt_dir, "system_prompt_assistant.txt")
                tool_path = os.path.join(prompt_dir, "system_prompt_tool.txt")
                parts = []
                if os.path.exists(sys_path):
                    with open(sys_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            parts.append(content)
                if os.path.exists(tool_path):
                    with open(tool_path, "r", encoding="utf-8") as f:
                        tool_content = f.read().strip()
                        if tool_content:
                            parts.append(tool_content)
                if parts:
                    return "\n\n".join(parts)
                # Fallback to generic when files empty/missing
            else:
                with open(os.path.join(prompt_dir, f"{prompt_type}_prompt.txt"), "r", encoding="utf-8") as f:
                    return f.read().strip()
        except FileNotFoundError:
            # Return default prompts if files don't exist
            if prompt_type == "system":
                return (
                    "You are a helpful financial assistant for Vietnamese farmers and small agricultural businesses. "
                    "You have access to information about financial services, banking, and agricultural finance in Vietnam. "
                    "You can also provide weather information to help with agricultural planning. "
                    "Always be accurate, helpful, and provide sources for your information."
                )
            else:  # human prompt
                return "Question: {input}\nThought: I need to help answer this question about financial services or agriculture in Vietnam."
    
    def _create_agent(self):
        """Create the ReAct agent with a Vietnamese ReAct-style prompt and required variables."""
        react_instructions = (
            self.system_prompt
            + "\n\n"
            + self.human_prompt
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
        )
        prompt = PromptTemplate.from_template(
            template=react_instructions,
            input_variables=["input", "chat_history", "tools", "tool_names", "agent_scratchpad"]
        )
        
        # Create the agent
        agent = create_react_agent(
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
    
    def process_query(self, query: str, conversation_id: Optional[str] = None) -> FinancialAgentResponse:
        """Process a user query and return a response.
        
        Args:
            query: The user's query
            conversation_id: Optional conversation ID for tracking
            
        Returns:
            FinancialAgentResponse object with response, sources, and tool usage
        """
        # Get chat history from memory
        chat_history = self.memory.chat_memory.messages if self.memory.chat_memory.messages else []
        
        # Run the agent
        result = self.agent.invoke({
            "input": query,
            "chat_history": chat_history
        })
        
        # Extract sources and tool usage
        sources = self._extract_sources(result)
        tool_usage = self._extract_tool_usage(result)
        
        # Generate the final response using the Vietnamese-optimized model if specified
        if self.response_llm != self.reasoning_llm:
            # Format the prompt for the response model
            response_prompt = f"""Based on the following information, provide a helpful response in Vietnamese to the user's query.
            
            User query: {query}
            
            Information: {result['output']}
            
            Respond in a helpful, accurate manner in Vietnamese. Include relevant details from the sources."""
            
            # Generate the response
            response = self.response_llm.invoke(response_prompt)
        else:
            # Use the reasoning model's output directly
            response = result["output"]
        
        # Update memory
        self.memory.chat_memory.add_user_message(query)
        self.memory.chat_memory.add_ai_message(response)
        
        return FinancialAgentResponse(
            response=response,
            sources=sources,
            tool_usage=tool_usage
        )
    
    async def aprocess_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> FinancialAgentResponse:
        """Async variant to process a user query using the agent. Context may include user_id, conversation_id, etc."""
        # Get chat history from memory
        chat_history = self.memory.chat_memory.messages if self.memory.chat_memory.messages else []
        
        # Run the agent asynchronously
        result = await self.agent.ainvoke({
            "input": query,
            "chat_history": chat_history
        })
        
        # Extract sources and tool usage
        sources = self._extract_sources(result)
        tool_usage = self._extract_tool_usage(result)
        
        # Generate the final response using the Vietnamese-optimized model if specified
        if self.response_llm != self.reasoning_llm:
            response_prompt = f"""Dựa trên thông tin sau, hãy trả lời bằng tiếng Việt một cách rõ ràng, hữu ích và chính xác.
\nCâu hỏi của người dùng: {query}
\nThông tin phản hồi từ tác nhân: {result['output']}
\nHãy trả lời ngắn gọn, súc tích, dễ hiểu cho nông hộ nhỏ lẻ ở Việt Nam. Nếu có thể, hãy đưa ra gợi ý hành động cụ thể và cảnh báo rủi ro liên quan."""
            response = self.response_llm.invoke(response_prompt)
        else:
            response = result["output"]
        
        # Update memory
        self.memory.chat_memory.add_user_message(query)
        self.memory.chat_memory.add_ai_message(response)
        
        return FinancialAgentResponse(
            response=response,
            sources=sources,
            tool_usage=tool_usage
        )
    
    def _extract_sources(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sources from the agent result.
        
        Args:
            result: The agent execution result
            
        Returns:
            List of source dictionaries
        """
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
    
    def _extract_tool_usage(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool usage from the agent result.
        
        Args:
            result: The agent execution result
            
        Returns:
            List of tool usage dictionaries
        """
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
    
    def reset_memory(self):
        """Reset the conversation memory."""
        self.memory = ConversationBufferMemory(return_messages=True)