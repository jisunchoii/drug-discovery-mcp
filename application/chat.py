import info
import streamlit as st
import asyncio
import logging
import traceback
import os
import uuid
from datetime import datetime

from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model_name = "Claude 3.7 Sonnet"
model_type = "claude"
debug_mode = "Enable"
model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
models = info.get_model_info(model_name)
reasoning_mode = 'Disable'

def update(modelName, reasoningMode):    
    global model_name, model_id, model_type, reasoning_mode
    
    if model_name != modelName:
        model_name = modelName
        logger.info(f"model_name: {model_name}")
        
        model_id = models[0]["model_id"]
        model_type = models[0]["model_type"]

    if reasoningMode != reasoning_mode:
        reasoning_mode = reasoningMode
        logger.info(f"reasoning_mode: {reasoning_mode}")

def initiate():
    global userId    
    userId = uuid.uuid4().hex
    logger.info(f"userId: {userId}")

#########################################################
# Strands Agent Model Configuration
#########################################################
def get_model():
    profile = models[0]
    if profile['model_type'] == 'nova':
        STOP_SEQUENCE = '"\n\n<thinking>", "\n<thinking>", " <thinking>"'
    elif profile['model_type'] == 'claude':
        STOP_SEQUENCE = "\n\nHuman:" 

    if model_type == 'claude':
        maxOutputTokens = 8094  # 4k
    else:
        maxOutputTokens = 5120  # 5k

    maxReasoningOutputTokens = 64000
    thinking_budget = min(maxOutputTokens, maxReasoningOutputTokens-1000)

    if reasoning_mode == 'Enable':
        model = BedrockModel(
            boto_client_config=Config(
               read_timeout=900,
               connect_timeout=900,
               retries=dict(max_attempts=3, mode="adaptive"),
            ),
            model_id=model_id,
            max_tokens=64000,
            stop_sequences=[STOP_SEQUENCE],
            temperature=1,
            additional_request_fields={
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": thinking_budget,
                }
            },
        )
    else:
        model = BedrockModel(
            boto_client_config=Config(
               read_timeout=900,
               connect_timeout=900,
               retries=dict(max_attempts=3, mode="adaptive"),
            ),
            model_id=model_id,
            max_tokens=maxOutputTokens,
            stop_sequences=[STOP_SEQUENCE],
            temperature=0.1,
            top_p=0.9,
            additional_request_fields={
                "thinking": {
                    "type": "disabled"
                }
            }
        )
    return model

# Conversation manager for maintaining context
conversation_manager = SlidingWindowConversationManager(
    window_size=10,  
)

# MCP Client for Tavily web search
tavily_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="python", args=["application/mcp_server_tavily.py"])
))

# MCP Client for ChEMBL database
chembl_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="node", args=["application/ChEMBL-MCP-Server/build/index.js"])
))

#########################################################
# MCP Client Session Distribution Mechanism
#########################################################

class MCPClientSessionManager:
    """Manages and distributes MCP client sessions to specialized agent tools"""

    def __init__(self):
        self._active_clients = {}
        self._session_status = {}

    def set_active_clients(self, client_sessions: dict):
        """
        Set the active MCP client sessions for distribution to agent tools

        Args:
            client_sessions: Dictionary mapping client types to active MCP client instances
        """
        self._active_clients = client_sessions.copy()
        # Track session status for each client
        for client_type, client in client_sessions.items():
            self._session_status[client_type] = {
                "active": True,
                "client": client,
                "last_used": None,
            }
        logger.info(
            f"Active MCP client sessions set: {list(self._active_clients.keys())}"
        )

    def get_client(self, client_type: str):
        """
        Get an active MCP client session by type

        Args:
            client_type: Type of client ('tavily', 'arxiv', 'pubmed', 'chembl', 'clinicaltrials')

        Returns:
            Active MCP client instance or None if not available
        """
        if client_type in self._active_clients:
            client = self._active_clients[client_type]
            # Update last used timestamp
            import datetime

            self._session_status[client_type]["last_used"] = datetime.datetime.now()
            return client
        return None

    def get_all_clients(self) -> dict:
        """Return dictionary of all active MCP client sessions"""
        return self._active_clients.copy()

    def is_client_available(self, client_type: str) -> bool:
        """Check if a specific client type is available and active"""
        return client_type in self._active_clients and self._session_status.get(
            client_type, {}
        ).get("active", False)

    def get_session_status(self) -> dict:
        """Get status information for all client sessions"""
        return self._session_status.copy()


# Global session manager instance
_session_manager = MCPClientSessionManager()

#########################################################
# Specialized Tool Agents
@tool
def web_search_agent(query: str, search_type: str = "general", history_mode: str = "Enable") -> str:
    """
    Specialized agent for searching the web using Tavily's search engine.

    Args:
        query: The search query
        search_type: Type of search to perform - "general", "answer", or "news" (default: "general")

    Returns:
        Structured information from web search results
    """
    client = _session_manager.get_client("tavily")
    if client is None:
        return "Error: Tavily client session not available"
    # Validate client session is usable
    tavily_tools = client.list_tools_sync()
    if not tavily_tools:
        error_msg = (
            "Error: Tavily client session is invalid or has no available tools"
        )
        logger.error(error_msg)
        return error_msg

    logger.info(f"tavily_tools: {tavily_tools}")

    # Create a specialized web search agent
    system_prompt = """
    당신은 웹 검색 전문 에이전트입니다. 당신의 역할은 다음과 같습니다:
    1. 쿼리를 분석하여 최적의 검색 전략을 결정합니다.
    2. Tavily의 검색 도구를 사용하여 웹을 검색합니다.
    3. 일반 검색의 경우: 웹 전체에서 포괄적이고 형식이 잘 정돈된 결과를 반환합니다.
    4. 답변 검색의 경우: 증빙 자료와 함께 직접 답변을 반환합니다.
    5. 뉴스 검색의 경우: 검색어와 관련된 최근 뉴스 기사 반환
    6. 확인을 위해 항상 소스 URL을 포함하세요
    
    **중요한 출처 표기 규칙:**
    - 정보를 언급할 때마다 해당 출처를 바로 옆에 [제목](URL) 형태로 표기하세요
    - 예: "HER2는 유방암의 주요 표적입니다 [Nature Cancer Research](https://example.com/article1)"
    - 여러 출처가 있을 때는 각각 별도로 표기하세요
    - 본문 끝에 "참고문헌:" 섹션을 만들어 모든 출처를 정리하세요
    
    한글로 답변하세요.
    """

    model = get_model()

    # Create the agent with the provided client tools    
    if history_mode == "Enable":
        logger.info("history_mode: Enable")
        web_agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=tavily_tools,
            conversation_manager=conversation_manager,
        )
    else:
        logger.info("history_mode: Disable")
        web_agent = Agent(model=model, system_prompt=system_prompt, tools=tavily_tools)
    return web_agent

@tool
def chembl_agent(query: str, search_type: str = "compound", history_mode: str = "Enable") -> str:
    """
    Specialized agent for searching ChEMBL database for drug discovery information.

    Args:
        query: The search query
        search_type: Type of search - "compound", "target", "bioactivity", or "assay" (default: "compound")
        history_mode: Whether to enable conversation history (default: "Enable")

    Returns:
        Structured information from ChEMBL database
    """
    client = _session_manager.get_client("chembl")
    if client is None:
        return "Error: ChEMBL client session not available"
    
    # Validate client session is usable
    chembl_tools = client.list_tools_sync()
    if not chembl_tools:
        error_msg = (
            "Error: ChEMBL client session is invalid or has no available tools"
        )
        logger.error(error_msg)
        return error_msg

    logger.info(f"chembl_tools: {chembl_tools}")

    # Create a specialized ChEMBL search agent
    system_prompt = """
    당신은 ChEMBL 데이터베이스 전문 에이전트입니다. 당신의 역할은 다음과 같습니다:
    1. 쿼리에서 유전자(단백질)/화합물/세포 이름, 화합물 구조 정보 (smiles or 구조 직접 입력, 구조 유사도, 특정 구조 포함)을 추출합니다.
    2. 해당 이름으로 ChEMBL을 검색합니다.
    3. 이름에 대한 스마일 및 활동 정보와 함께 구조화되고 형식이 잘 지정된 컴파운드 정보를 반환합니다.
    
    한글로 답변하세요.
    """

    model = get_model()

    # Create the agent with the provided client tools    
    if history_mode == "Enable":
        logger.info("history_mode: Enable")
        chembl_search_agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=chembl_tools,
            conversation_manager=conversation_manager,
        )
    else:
        logger.info("history_mode: Disable")
        chembl_search_agent = Agent(model=model, system_prompt=system_prompt, tools=chembl_tools)
    return chembl_search_agent


def run_individual_agent(question, history_mode, st, agent_type):
    """
    Run a specific individual agent based on user selection
    
    Args:
        question: User's query
        history_mode: Whether to enable conversation history
        st: Streamlit object for UI updates
        agent_type: Type of agent to run ('web_search' or 'chembl')
        
    Returns:
        Agent response
    """
    message_placeholder = st.empty()
    full_response = ""
    
    async def process_streaming_response():
        nonlocal full_response
        try:
            # Initialize client sessions based on agent type
            if agent_type == "web_search":
                with tavily_mcp_client as tavily_client:
                    client_sessions = {
                        "tavily": tavily_client,
                    }
                    _session_manager.set_active_clients(client_sessions)
                    
                    agent = web_search_agent(history_mode)
                    agent_stream = agent.stream_async(question)
                    async for event in agent_stream:
                        if "data" in event:
                            full_response += event["data"]
                            message_placeholder.markdown(full_response)
            
            elif agent_type == "chembl":
                with chembl_mcp_client as chembl_client:
                    client_sessions = {
                        "chembl": chembl_client,
                    }
                    _session_manager.set_active_clients(client_sessions)
                    
                    agent = chembl_agent(history_mode)
                    agent_stream = agent.stream_async(question)
                    async for event in agent_stream:
                        if "data" in event:
                            full_response += event["data"]
                            message_placeholder.markdown(full_response)
            
            else:
                # Default to web search if unknown agent type
                with tavily_mcp_client as tavily_client:
                    client_sessions = {
                        "tavily": tavily_client,
                    }
                    _session_manager.set_active_clients(client_sessions)
                    
                    agent = web_search_agent(history_mode)
                    agent_stream = agent.stream_async(question)
                    async for event in agent_stream:
                        if "data" in event:
                            full_response += event["data"]
                            message_placeholder.markdown(full_response)

        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            message_placeholder.markdown(
                "Sorry, an error occurred while generating the response."
            )
            logger.error(traceback.format_exc())  # Detailed error logging

    asyncio.run(process_streaming_response())

    return full_response