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
    global userId, conversation_manager    
    userId = uuid.uuid4().hex
    # Reset conversation manager to clear history
    conversation_manager = SlidingWindowConversationManager(window_size=5)
    logger.info(f"userId: {userId}, conversation manager reset")

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
        maxOutputTokens = 4096  # 4k
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
    window_size=5,  # Reduced from 10 to 5 to prevent token overflow
)

# MCP Client for Tavily web search
tavily_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="python", args=["application/mcp_server_tavily.py"])
))

# MCP Client for ChEMBL database
chembl_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="node", args=["application/ChEMBL-MCP-Server/build/index.js"])
))

# MCP Client for UniProt database
uniprot_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="node", args=["application/UniProt-MCP-Server/build/index.js"])
))

# MCP Client for PDB database
pdb_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="node", args=["application/PDB-MCP-Server/build/index.js"])
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
    웹 검색 전문 에이전트입니다. Tavily 도구로 웹을 검색하고 한글로 답변합니다.
    - 일반 검색: 포괄적 결과 반환
    - 답변 검색: 증빙과 함께 직접 답변
    - 뉴스 검색: 최근 뉴스 기사
    정보 언급 시 [제목](URL) 형태로 출처 표기하세요.
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
    ChEMBL 데이터베이스 전문 에이전트입니다. 
    쿼리에서 유전자/화합물/세포 이름, 화합물 구조 정보를 추출하여 ChEMBL을 검색합니다.
    구조화된 화합물 정보를 스마일 및 활동 정보와 함께 한글로 반환합니다.
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

@tool
def uniprot_agent(query: str, search_type: str = "protein", history_mode: str = "Enable") -> str:
    """
    Specialized agent for searching UniProt database for protein information.

    Args:
        query: The search query
        search_type: Type of search - "protein", "gene", "sequence", "feature", or "structure" (default: "protein")
        history_mode: Whether to enable conversation history (default: "Enable")

    Returns:
        Structured information from UniProt database
    """
    client = _session_manager.get_client("uniprot")
    if client is None:
        return "Error: UniProt client session not available"
    
    # Validate client session is usable
    uniprot_tools = client.list_tools_sync()
    if not uniprot_tools:
        error_msg = (
            "Error: UniProt client session is invalid or has no available tools"
        )
        logger.error(error_msg)
        return error_msg

    logger.info(f"uniprot_tools: {uniprot_tools}")

    # Create a specialized UniProt search agent
    system_prompt = """
    UniProt 데이터베이스 전문 에이전트입니다.
    단백질, 유전자, 서열, 기능, 구조 정보를 분석하여 UniProt의 26가지 도구를 활용합니다.
    핵심 분석: 단백질 검색, 상세 정보, 서열, 기능 특성
    비교 분석: 단백질 비교, 상동체, 직교체, 계통발생
    구조 분석: 3D 구조, 도메인, 변이, 서열 조성
    생물학적 맥락: 경로, 상호작용, 기능 분류, 세포 위치
    구조화된 단백질 정보를 UniProt 접근 번호와 함께 한글로 반환합니다.
    """

    model = get_model()

    # Create the agent with the provided client tools    
    if history_mode == "Enable":
        logger.info("history_mode: Enable")
        uniprot_search_agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=uniprot_tools,
            conversation_manager=conversation_manager,
        )
    else:
        logger.info("history_mode: Disable")
        uniprot_search_agent = Agent(model=model, system_prompt=system_prompt, tools=uniprot_tools)
    return uniprot_search_agent

@tool
def pdb_agent(query: str, search_type: str = "structure", history_mode: str = "Enable") -> str:
    """
    Specialized agent for searching PDB database for protein structure information.

    Args:
        query: The search query
        search_type: Type of search - "structure", "quality", "ligand", or "validation" (default: "structure")
        history_mode: Whether to enable conversation history (default: "Enable")

    Returns:
        Structured information from PDB database
    """
    client = _session_manager.get_client("pdb")
    if client is None:
        return "Error: PDB client session not available"
    
    # Validate client session is usable
    pdb_tools = client.list_tools_sync()
    if not pdb_tools:
        error_msg = (
            "Error: PDB client session is invalid or has no available tools"
        )
        logger.error(error_msg)
        return error_msg

    logger.info(f"pdb_tools: {pdb_tools}")

    # Create a specialized PDB search agent
    system_prompt = """
    PDB(Protein Data Bank) 데이터베이스 전문 에이전트입니다.
    단백질 3D 구조, 핵산, 복합체 조립 정보를 분석하여 PDB의 28가지 도구를 활용합니다.
    구조 검색: PDB ID, 단백질명, 키워드로 구조 검색
    구조 정보: 상세 구조 정보, 품질 지표, 검증 데이터
    다운로드: PDB, mmCIF, mmTF, XML 형식으로 구조 좌표 다운로드
    UniProt 연동: UniProt 접근 번호로 PDB 구조 검색
    리간드 정보: 결합 부위 및 리간드 정보 분석
    구조화된 단백질 구조 정보를 PDB ID와 함께 한글로 반환합니다.
    """

    model = get_model()

    # Create the agent with the provided client tools    
    if history_mode == "Enable":
        logger.info("history_mode: Enable")
        pdb_search_agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=pdb_tools,
            conversation_manager=conversation_manager,
        )
    else:
        logger.info("history_mode: Disable")
        pdb_search_agent = Agent(model=model, system_prompt=system_prompt, tools=pdb_tools)
    return pdb_search_agent

@tool
def multi_agent_orchestrator(query: str, research_type: str = "comprehensive", history_mode: str = "Enable") -> str:
    """
    Multi-agent orchestrator that coordinates ChEMBL, UniProt, and PDB agents for comprehensive drug discovery research.
    
    Args:
        query: The research query
        research_type: Type of research - "compound_focused", "target_focused", or "comprehensive" (default: "comprehensive")
        history_mode: Whether to enable conversation history (default: "Enable")
    
    Returns:
        Integrated analysis from multiple specialized agents
    """
    # Define the orchestrator system prompt with clear tool selection guidance
    ORCHESTRATOR_SYSTEM_PROMPT = """
    당신은 신약 개발 연구를 위한 멀티 에이전트 오케스트레이터입니다. 
    다음 전문 에이전트들을 도구로 활용하여 종합적인 분석을 제공합니다:

    - 화합물/약물 정보 및 생물학적 활성 데이터 → chembl_agent 도구 사용
    - 단백질 서열, 기능, 주석 정보 → uniprot_agent 도구 사용  
    - 단백질 3D 구조 및 결정학 데이터 → pdb_agent 도구 사용

    도구 선택 가이드라인:
    - 화합물명, 약물명, SMILES → chembl_agent(search_type="compound")
    - 단백질명, 유전자명, 효소명 → uniprot_agent(search_type="protein")
    - 단백질 구조, PDB ID, 결정학 → pdb_agent(search_type="structure")
    - 타겟-약물 관계 → chembl_agent(search_type="target")

    종합적인 연구를 위해 여러 도구를 순차적으로 사용하고 결과를 통합 분석하세요.
    항상 도구 선택 이유를 설명하고 결과의 통합 분석을 제공하세요.
    """

    model = get_model()

    # Create the orchestrator agent with specialized agents as tools
    if history_mode == "Enable":
        logger.info("Multi-agent orchestrator with history enabled")
        orchestrator = Agent(
            model=model,
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=[chembl_agent, uniprot_agent, pdb_agent],
            conversation_manager=conversation_manager,
        )
    else:
        logger.info("Multi-agent orchestrator with history disabled")
        orchestrator = Agent(
            model=model, 
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT, 
            tools=[chembl_agent, uniprot_agent, pdb_agent]
        )
    
    return orchestrator


def run_individual_agent(question, history_mode, st, agent_type):
    """
    Run a specific individual agent based on user selection
    
    Args:
        question: User's query
        history_mode: Whether to enable conversation history
        st: Streamlit object for UI updates
        agent_type: Type of agent to run ('web_search', 'chembl', 'uniprot', 'pdb', or 'multi_agent')
        
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
            
            elif agent_type == "uniprot":
                with uniprot_mcp_client as uniprot_client:
                    client_sessions = {
                        "uniprot": uniprot_client,
                    }
                    _session_manager.set_active_clients(client_sessions)
                    
                    agent = uniprot_agent(history_mode)
                    agent_stream = agent.stream_async(question)
                    async for event in agent_stream:
                        if "data" in event:
                            full_response += event["data"]
                            message_placeholder.markdown(full_response)
            
            elif agent_type == "pdb":
                with pdb_mcp_client as pdb_client:
                    client_sessions = {
                        "pdb": pdb_client,
                    }
                    _session_manager.set_active_clients(client_sessions)
                    
                    agent = pdb_agent(history_mode)
                    agent_stream = agent.stream_async(question)
                    async for event in agent_stream:
                        if "data" in event:
                            full_response += event["data"]
                            message_placeholder.markdown(full_response)
            
            elif agent_type == "multi_agent":
                # Multi-agent orchestrator needs all three database clients
                with chembl_mcp_client as chembl_client, \
                     uniprot_mcp_client as uniprot_client, \
                     pdb_mcp_client as pdb_client:
                    
                    client_sessions = {
                        "chembl": chembl_client,
                        "uniprot": uniprot_client,
                        "pdb": pdb_client,
                    }
                    _session_manager.set_active_clients(client_sessions)
                    
                    agent = multi_agent_orchestrator(history_mode)
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