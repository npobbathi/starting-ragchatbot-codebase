import anthropic
from typing import List, Optional, Dict, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **One search per query maximum**
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key, timeout=30.0)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response from Claude with fallback handling
        try:
            response = self.client.messages.create(**api_params)
            
            # Handle tool execution if needed
            if response.stop_reason == "tool_use" and tool_manager:
                return self._handle_tool_execution(response, api_params, tool_manager)
            
            # Return direct response
            return response.content[0].text
            
        except anthropic.BadRequestError as e:
            logger.warning(f"Anthropic API error: {e}")
            if "credit balance" in str(e).lower():
                return self._generate_fallback_response(query, conversation_history)
            else:
                return f"Sorry, I'm experiencing technical difficulties. Please try again later. (Error: {str(e)})"
                
        except (anthropic.APITimeoutError, TimeoutError) as e:
            logger.warning(f"Anthropic API timeout: {e}")
            return self._generate_fallback_response(query, conversation_history)
                
        except Exception as e:
            logger.error(f"Unexpected error calling Anthropic API: {e}")
            return self._generate_fallback_response(query, conversation_history)
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.
        
        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            
        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        
        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name, 
                    **content_block.input
                )
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })
        
        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }
        
        # Get final response with fallback handling
        try:
            final_response = self.client.messages.create(**final_params)
            return final_response.content[0].text
        except Exception as e:
            logger.error(f"Error in final tool response: {e}")
            # Extract query from messages if possible
            query = base_params["messages"][0]["content"] if base_params["messages"] else "your question"
            return self._generate_fallback_response(query, None)
    
    def _generate_fallback_response(self, query: str, conversation_history: Optional[str] = None) -> str:
        """
        Generate a helpful fallback response when the API is unavailable.
        
        Args:
            query: The user's question
            conversation_history: Previous conversation context
            
        Returns:
            A helpful fallback response
        """
        query_lower = query.lower()
        
        # Provide helpful responses for common question types
        if any(word in query_lower for word in ['python', 'programming', 'code', 'function', 'variable']):
            return """I'm currently experiencing an issue with my AI service (insufficient API credits). 
            
For Python programming questions, I'd recommend:
- Check the official Python documentation at docs.python.org
- Try Python's built-in help() function
- Use interactive Python shell to test code snippets
- Visit Stack Overflow for specific programming questions

Please contact the administrator to restore full AI functionality."""

        elif any(word in query_lower for word in ['course', 'lesson', 'learn', 'study', 'material']):
            return """I'm currently unable to access my AI service due to insufficient API credits.
            
For course-related questions, you can:
- Check the course materials in the docs folder
- Review any provided course scripts or documentation
- Look for README files or course outlines
- Contact your instructor for specific course questions

Please ask an administrator to add credits to restore full functionality."""

        elif any(word in query_lower for word in ['what', 'how', 'why', 'when', 'where']):
            return f"""I'm currently experiencing technical difficulties (insufficient API credits) and cannot fully process your question: "{query}"

To get a complete answer, please:
1. Ask an administrator to add credits to the Anthropic API account
2. Try rephrasing your question more specifically
3. Consult relevant documentation or course materials
4. Contact support for urgent assistance

I apologize for the inconvenience!"""

        else:
            return f"""I'm currently unable to process your request due to insufficient API credits.

Your question: "{query}"

Please contact an administrator to restore service, or try:
- Consulting available documentation
- Using alternative resources
- Contacting support directly

Thank you for your patience!"""