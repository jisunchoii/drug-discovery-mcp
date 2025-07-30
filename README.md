# 신약 개발 보조 에이전트 (Drug Discovery MCP)

💊 MCP(Model Context Protocol)를 활용한 신약 개발 연구 보조 AI 에이전트입니다.

## 프로젝트 개요

이 프로젝트는 신약 개발 과정에서 필요한 다양한 정보 수집과 분석을 도와주는 AI 에이전트입니다. ChEMBL 데이터베이스, 논문 검색, 임상시험 정보 등을 통합하여 연구자들에게 유용한 인사이트를 제공합니다.

## 주요 기능

- 🔬 ChEMBL 데이터베이스 연동을 통한 화합물 정보 검색
- 🧪 UniProt 데이터베이스 연동을 통한 단백질 정보 검색
- 🔬 PDB 데이터베이스 연동을 통한 단백질 3D 구조 정보 검색
- 🌐 Tavily API를 통한 웹 검색 기능
- 📊 Streamlit 기반 웹 인터페이스


## 설치 방법

1. 저장소 클론
```bash
git clone <repository-url>
cd drug-discovery-mcp
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

## 환경 설정

1. 환경 변수 파일 설정
```bash
cp .env.example .env
```

2. `.env` 파일에 필요한 API 키 입력
```
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_SESSION_TOKEN="your_aws_session_token"
TAVILY_API_KEY="your_tavily_api_key"
```

## 애플리케이션 실행 방법

### 1. Streamlit 웹 애플리케이션 실행

메인 웹 인터페이스를 실행하려면:

```bash
streamlit run application/app.py
```

브라우저에서 `http://localhost:8501`로 접속하여 사용할 수 있습니다.


## 프로젝트 구조

```
drug-discovery-mcp/
├── application/
│   ├── app.py                    # Streamlit 메인 애플리케이션
│   ├── chat.py                   # 채팅 인터페이스
│   ├── launcher.py               # 애플리케이션 런처
│   ├── info.py                   # 정보 관리 모듈
│   ├── mcp_server_tavily.py      # Tavily MCP 서버
│   ├── ChEMBL-MCP-Server/        # ChEMBL MCP 서버
│   ├── UniProt-MCP-Server/       # UniProt MCP 서버
│   └── PDB-MCP-Server/           # PDB MCP 서버
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경 변수 템플릿
├── .gitignore                    # Git 무시 파일
└── biological_paper_parsing_prompt.md  # 생물학 논문 파싱 프롬프트
```