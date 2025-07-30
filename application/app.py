import streamlit as st
import chat
import logging
import sys

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("streamlit")

# title
st.set_page_config(
    page_title='신약 개발 보조 에이전트',
    page_icon='💊',
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None
)

with st.sidebar:
    # st.title("메뉴")
    
    # st.markdown(
    #     "Strands Agent SDK를 사용하여 다양한 유형의 에이전트를 구현합니다. "
    #     "자세한 코드는 [Github](https://github.com/hsr87/drug-discovery-agent)를 참조하세요."
    # )

    # model selection box
    # model selection box
    modelName = st.selectbox(
        '파운데이션 모델 선택',
        ('Claude 4 Sonnet', 'Claude 3.7 Sonnet', 'Claude 3.5 Sonnet', 'Claude 3.5 Haiku'), index=0
    )
    
    # extended thinking of claude 3.7 sonnet
    select_reasoning = st.checkbox('추론 모드 (Claude 4 Sonnet and Claude 3.7 Sonnet)', value=False)
    reasoningMode = 'Enable' if select_reasoning and modelName in ["Claude 4 Sonnet", "Claude 3.7 Sonnet"] else "Disable"
    logger.info(f"reasoningMode: {reasoningMode}")

    chat.update(modelName, reasoningMode)
    
    # Agent selection
    st.markdown("---")
    st.markdown("### 🤖 에이전트 선택")
    
    # Available agents
    available_agents = {
        "web_search": "🌐 웹 검색 에이전트 - 웹에서 최신 정보를 검색하고 분석",
        "chembl": "🧬 ChEMBL 에이전트 - ChEMBL 데이터베이스에서 화합물, 표적, 생물활성 데이터 검색",
        "uniprot": "🧪 UniProt 에이전트 - UniProt 데이터베이스에서 단백질 정보, 구조, 기능 분석",
        "pdb": "🔬 PDB 에이전트 - PDB 데이터베이스에서 단백질 3D 구조, 품질 지표, 검증 데이터 분석",
        "multi_agent": "🤖 멀티 에이전트 오케스트레이터 - ChEMBL, UniProt, PDB 에이전트를 통합하여 종합적 분석"
    }
    
    # Create selectbox for agent selection
    selected_agent = st.selectbox(
        '에이전트 선택:',
        options=list(available_agents.keys()),
        format_func=lambda x: available_agents[x],
        index=0,  # Default to web_search
        help="웹 검색 에이전트를 사용합니다"
    )
    
    # Display selected agent description
    if selected_agent:
        agent_desc = available_agents[selected_agent]
        st.info(f"**선택됨:** {agent_desc}")
    
    # Add expandable help section
    with st.expander("ℹ️ 에이전트 가이드", expanded=False):
        st.markdown("""
        **🌐 웹 검색 에이전트**: 
        - 웹에서 최신 정보 검색
                    
        **🧬 ChEMBL 에이전트**: 
        - 화합물 구조, 특성, 개발 단계 정보
        - 단백질 표적 정보 및 기능 분석
        - 생물활성 데이터 (IC50, EC50, Ki 등)
        - 분석법 및 실험 데이터
                    
        **🧪 UniProt 에이전트**: 
        - 단백질 서열, 구조, 기능 정보
        - 유전자 기반 단백질 검색
        - 단백질 도메인 및 특성 분석
        - 진화적 관계 및 상동체 분석
        - 단백질 상호작용 및 경로 정보
                    
        **🔬 PDB 에이전트**: 
        - 단백질 3D 구조 및 좌표 데이터
        - 구조 품질 지표 및 검증 데이터
        - 리간드 결합 부위 정보
        - 결정학, NMR, Cryo-EM 구조 데이터
        - 구조 비교 및 분석
        
        **🤖 멀티 에이전트 오케스트레이터**:
        - 쿼리 분석 후 적절한 전문 에이전트 자동 선택
        - ChEMBL, UniProt, PDB 에이전트 통합 활용
        - 다중 데이터베이스 교차 참조 분석
        - 종합적 신약 개발 연구 지원
        - 화합물-타겟-구조 통합 분석
        """)
    
    # Add example questions section
    with st.expander("💡 예시 질문", expanded=False):
        if selected_agent == "web_search":
            st.markdown("""
            **웹 검색 에이전트 예시 질문:**
            - "HER2 표적 치료제의 최신 연구 동향을 알려줘"
            - "BRCA1 억제제 관련 최근 뉴스를 찾아줘"
            - "코로나바이러스 단백질 표적 약물 후보를 검색해줘"
            - "알츠하이머 치료제 개발 현황을 조사해줘"
            """)
        elif selected_agent == "chembl":
            st.markdown("""
            **ChEMBL 에이전트 예시 질문:**
            
            **화합물 검색:**
            - "아스피린의 ChEMBL 정보를 찾아줘"
            - "CHEMBL25 화합물의 상세 정보를 보여줘"
            
            **표적 단백질 검색:**
            - "도파민 수용체 D2의 정보를 찾아줘"
            - "HER2 표적에 대한 화합물들을 검색해줘"
            - "키나제 표적들을 검색해줘"
            
            **생물활성 데이터:**
            - "CHEMBL2095173 표적에 대한 IC50 데이터를 보여줘"
            - "EGFR 억제제의 생물활성 데이터를 찾아줘"
            - "Ki 값이 낮은 화합물들을 검색해줘"
            
            **배치 처리:**
            - "CHEMBL25, CHEMBL59, CHEMBL1642 화합물들의 정보를 한번에 조회해줘"
            """)
        elif selected_agent == "uniprot":
            st.markdown("""
            **UniProt 에이전트 예시 질문:**
            
            **단백질 검색:**
            - "인슐린 단백질의 정보를 찾아줘"
            - "P01308 접근 번호의 단백질 정보를 보여줘"
            - "인간의 BRCA1 단백질을 검색해줘"
            
            **유전자 기반 검색:**
            - "BRCA1 유전자의 단백질을 찾아줘"
            - "TP53 유전자와 관련된 단백질 정보를 보여줘"
            
            **서열 및 구조 분석:**
            - "P01308의 아미노산 서열을 보여줘"
            - "인슐린의 3D 구조 정보를 찾아줘"
            - "EGFR의 도메인 구조를 분석해줘"
            
            **비교 및 진화 분석:**
            - "인간과 마우스의 인슐린을 비교해줘"
            - "BRCA1의 상동체를 찾아줘"
            - "p53의 진화적 관계를 분석해줘"
            
            **기능 및 상호작용:**
            - "인슐린의 생물학적 경로를 찾아줘"
            - "EGFR과 상호작용하는 단백질들을 보여줘"
            - "키나제 활성을 가진 단백질들을 검색해줘"
            """)
        elif selected_agent == "pdb":
            st.markdown("""
            **PDB 에이전트 예시 질문:**
            
            **구조 검색:**
            - "1HHO PDB 구조의 정보를 보여줘"
            - "인슐린의 PDB 구조를 찾아줘"
            - "COVID-19 스파이크 단백질 구조를 검색해줘"
            
            **UniProt 연동 검색:**
            - "P01308 UniProt ID의 PDB 구조를 찾아줘"
            - "BRCA1 단백질의 PDB 구조를 검색해줘"
            
            **구조 품질 및 검증:**
            - "1HHO 구조의 품질 지표를 보여줘"
            - "인슐린 구조의 검증 데이터를 분석해줘"
            - "해상도가 높은 EGFR 구조를 찾아줘"
            
            **구조 다운로드:**
            - "1HHO 구조를 PDB 형식으로 다운로드해줘"
            - "인슐린 구조를 mmCIF 형식으로 받아줘"
            - "COVID 스파이크 구조를 XML 형식으로 다운로드해줘"
            
            **리간드 및 결합 부위:**
            - "1HHO 구조의 리간드 정보를 보여줘"
            - "ATP 결합 부위가 있는 구조를 찾아줘"
            - "약물 결합 부위 정보를 분석해줘"
            """)
        elif selected_agent == "multi_agent":
            st.markdown("""
            **멀티 에이전트 오케스트레이터 예시 질문:**
            
            **종합적 화합물 분석:**
            - "아스피린의 타겟 단백질과 3D 구조 정보를 모두 찾아줘"
            - "이부프로fen의 화합물 정보, 타겟 단백질, 구조 데이터를 종합 분석해줘"
            - "CHEMBL25 화합물의 전체적인 프로파일을 분석해줘"
            
            **타겟 중심 통합 연구:**
            - "EGFR 단백질의 기능, 구조, 관련 억제제를 모두 조사해줘"
            - "cyclooxygenase의 단백질 정보와 PDB 구조, 관련 화합물을 찾아줘"
            - "인슐린 수용체의 종합적인 정보를 분석해줘"
            
            **신약 개발 워크플로우:**
            - "COVID-19 스파이크 단백질을 타겟으로 하는 약물 후보를 찾고 구조 분석해줘"
            - "알츠하이머 관련 타겟 단백질과 후보 화합물, 구조 정보를 종합해줘"
            - "항암제 개발을 위한 HER2 타겟 분석을 해줘"
            
            **교차 참조 분석:**
            - "P01308 UniProt ID의 단백질 정보, PDB 구조, 관련 화합물을 모두 찾아줘"
            - "1HHO PDB 구조의 단백질 정보와 관련 화합물을 분석해줘"
            - "키나제 억제제들의 화합물-타겟-구조 관계를 분석해줘"
            """)
    
    
    clear_button = st.button("대화 초기화", key="clear")

st.title('💊 신약 개발 보조 에이전트')  

if clear_button is True:
    chat.initiate()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greetings = False

# Display chat messages from history on app rerun
import re

def extract_and_format_references(content):
    """웹 검색 결과에서 출처를 추출하고 숫자 링크로 포맷팅"""
    # URL 패턴 매칭 (다양한 형태의 URL 참조 처리)
    url_patterns = [
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',  # [text](url) 형태
        r'출처:\s*(https?://[^\s]+)',  # 출처: url 형태
        r'Source:\s*(https?://[^\s]+)',  # Source: url 형태
        r'참고:\s*(https?://[^\s]+)',  # 참고: url 형태
        r'Reference:\s*(https?://[^\s]+)',  # Reference: url 형태
        r'(https?://[^\s]+)',  # 단순 URL 형태
    ]
    
    references = []
    reference_counter = 1
    formatted_content = content
    
    # URL과 제목을 매칭하여 참고문헌 추출
    for pattern in url_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 2:  # [text](url) 형태
                title, url = match.groups()
                if url not in [ref['url'] for ref in references]:
                    references.append({
                        'number': reference_counter,
                        'title': title,
                        'url': url
                    })
                    # 본문에서 해당 부분을 숫자 링크로 교체
                    formatted_content = formatted_content.replace(
                        match.group(0), 
                        f"{title} [{reference_counter}]"
                    )
                    reference_counter += 1
            else:  # 단순 URL 형태
                url = match.group(1) if len(match.groups()) >= 1 else match.group(0)
                if url not in [ref['url'] for ref in references]:
                    # URL에서 도메인명 추출하여 제목으로 사용
                    domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
                    title = domain.group(1) if domain else url
                    references.append({
                        'number': reference_counter,
                        'title': title,
                        'url': url
                    })
                    # 본문에서 해당 URL을 숫자 링크로 교체
                    formatted_content = formatted_content.replace(
                        url, 
                        f"[{reference_counter}]"
                    )
                    reference_counter += 1
    
    return formatted_content, references

def format_references(content):
    """참고문헌 섹션을 더 읽기 쉽게 포맷팅하고 숫자 링크 추가"""
    # 먼저 URL 참조를 숫자 링크로 변환
    formatted_content, references = extract_and_format_references(content)
    
    # 기존 참고문헌 섹션 처리
    if "참고문헌:" in formatted_content or "References:" in formatted_content:
        lines = formatted_content.split('\n')
        formatted_lines = []
        in_references = False
        
        for line in lines:
            if line.strip().startswith("참고문헌:") or line.strip().startswith("References:"):
                in_references = True
                formatted_lines.append(f"\n## {line.strip()}\n")
            elif in_references and line.strip().startswith("["):
                formatted_lines.append(f"{line.strip()}\n")
            else:
                if in_references and line.strip() == "":
                    formatted_lines.append(line)
                elif in_references and not line.strip().startswith("[") and line.strip() != "":
                    in_references = False
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
        
        formatted_content = '\n'.join(formatted_lines)
    
    # 새로운 참고문헌이 있으면 추가
    if references:
        if "참고문헌:" not in formatted_content and "References:" not in formatted_content:
            formatted_content += "\n\n## 참고문헌\n\n"
        
        for ref in references:
            formatted_content += f"[{ref['number']}] [{ref['title']}]({ref['url']})\n\n"
    
    return formatted_content

def display_chat_messages():
    """메시지 기록 출력
    @returns None
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "images" in message:                
                for url in message["images"]:
                    logger.info(f"url: {url}")

                    file_name = url[url.rfind('/') + 1:]
                    st.image(url, caption=file_name, use_container_width=True)
            
            # 참고문헌 포맷팅 적용
            formatted_content = format_references(message["content"])
            st.markdown(formatted_content)

display_chat_messages()

# Greet user
if not st.session_state.greetings:
    with st.chat_message("assistant"):
        intro = "Amazon Bedrock 기반 신약 개발 에이전트를 사용해 주셔서 감사합니다. 편안한 대화를 즐기실 수 있습니다."
        st.markdown(intro)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": intro})
        st.session_state.greetings = True

if clear_button or "messages" not in st.session_state:
    st.session_state.messages = []        
    st.session_state.greetings = False
    st.rerun()
       
# Always show the chat input
if prompt := st.chat_input("메시지를 입력하세요."):
    with st.chat_message("user"):  # display user message in chat message container
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})  # add user message to chat history
    prompt = prompt.replace('"', "").replace("'", "")
    logger.info(f"prompt: {prompt}")

    with st.chat_message("assistant"):
        sessionState = ""
        response = chat.run_individual_agent(prompt, "Enable", st, selected_agent)

    # 참고문헌 포맷팅을 적용한 응답을 세션 상태에 저장
    formatted_response = format_references(response)
    st.session_state.messages.append({"role": "assistant", "content": formatted_response})
