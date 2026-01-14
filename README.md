# Paradox Localisation Manager (HOI4 웹 번역기)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB.svg)

**Hearts of Iron IV** 모드 번역을 위한 AI 기반 자동 번역 도구입니다.  
스팀 창작마당 모드를 자동으로 감지하고, **Ollama(로컬), ChatGPT, Claude, Gemini** 등 다양한 AI를 활용해 고품질 번역 모드를 생성해줍니다.

## ✨ 주요 기능

*   **🤖 멀티 AI 지원**: 
    *   **로컬 AI**: Ollama를 통해 무료로 무제한 번역 (Qwen2.5, Llama3 추천)
    *   **클라우드 AI**: OpenAI (GPT-4o), Anthropic (Claude 3.5), Google (Gemini 1.5)
*   **🛠️ 모드 관리 편의성**: 
    *   내 PC의 스팀 창작마당 모드 자동 스캔
    *   원본 모드를 건드리지 않고 **별도의 번역 모드** 생성 (구독 해제해도 안전)
    *   번역된 모드를 바로 게임 런처에 등록
*   **🧠 똑똑한 번역 (Smart Context)**: 
    *   게임 특수 코드 완벽 보존 (`§Y`, `[Root.GetName]`, `$VAR$`)
    *   **HOI4 공식 한국어 스타일 준수** ('Army' -> '육군', 'Manpower' -> '인력', 어미 자동 변환)
    *   사용자 정의 용어집(Glossary) 적용 가능
*   **⚡ 강력한 성능**:
    *   비동기 병렬 처리로 초고속 번역
    *   ParaTranz(파라트랜즈) 연동으로 협업 번역 데이터 동기화

## 🚀 설치 및 실행 방법

### 필수 요구사항
*   [Python 3.12 이상](https://www.python.org/)
*   [Node.js 18 이상](https://nodejs.org/) (프론트엔드 빌드 시 필요)
*   [Ollama](https://ollama.com/) (로컬 AI 사용 시 선택 사항)

### 1. 프로젝트 다운로드
```bash
git clone https://github.com/yourusername/paradox-loc-manager.git
cd paradox-loc-manager
```

### 2. 백엔드(Backend) 설정
```bash
cd backend
python -m venv venv

# 윈도우 (Windows)
venv\Scripts\activate

# 맥/리눅스 (Mac/Linux)
source venv/bin/activate

pip install -r requirements.txt
```

### 3. ParaTranz SDK 설치 (중요)
이 프로젝트는 ParaTranz API 연동을 위해 별도의 SDK가 필요합니다.
[ParaTranz API 문서](https://paratranz.cn/docs)를 참고하여 생성하거나, 아래 방법대로 진행하세요.

1.  Java가 설치되어 있어야 합니다. (OpenAPI Generator 실행용)
2.  프로젝트 루트에서 아래 명령어로 SDK를 생성합니다. (또는 미리 생성된 SDK 폴더를 구해서 넣으세요)
    ```bash
    # openapi-generator-cli가 필요합니다
    openapi-generator-cli generate -i https://paratranz.cn/api/swagger.json -g python -o paratranz-sdk
    ```
3.  생성된 `paratranz-sdk` 폴더를 프로젝트 루트(또는 backend 폴더)에 위치시킵니다.

### 4. 프론트엔드(Frontend) 설정
```bash
cd ../frontend
npm install
npm run build
```

### 5. 프로그램 실행
프로젝트 최상위 폴더(`paradox-loc-manager`)로 돌아와서 실행 스크립트를 켭니다.
```bash
# 윈도우
python start.py
```
브라우저 주소창에 `http://localhost:8080`을 입력하여 접속합니다.

## 📖 사용 가이드

1.  **모드 선택**: 앱을 켜면 자동으로 스캔된 모드 목록이 뜹니다. 번역하고 싶은 모드를 선택하세요.
2.  **AI 서비스 선택**:
    *   **Ollama**: 내 컴퓨터 성능을 사용 (무료, 개인 정보 보호). `Qwen2.5-7B` 모델을 강력 추천합니다.
    *   **OpenAI/Claude/Gemini**: API 키를 입력하여 사용 (유료, 고성능).
3.  **번역 시작**: 설정(타겟 언어, 용어집 등)을 확인하고 'Start Translation'을 누르세요.
4.  **적용**: 번역이 끝나면 `문서/Paradox Interactive/Hearts of Iron IV/mod` 폴더에 번역 모드가 생성됩니다. 게임 런처에서 해당 모드를 켜고 게임을 즐기세요.

## 🤝 ParaTranz 연동 (협업 번역)
혼자가 아니라 팀으로 번역하고 싶다면 파라트랜즈를 연동하세요.
1.  [ParaTranz](https://paratranz.cn/)에서 프로젝트 생성.
2.  내 프로필 설정에서 **API Token** 발급.
3.  웹 인터페이스 설정 메뉴에 토큰 입력.
4.  **업로드**: 원본 파일(`l_english`)을 파라트랜즈로 업로드.
5.  **동기화**: 파라트랜즈에서 작업한 번역(`l_korean`)을 로컬로 내려받기.

## ⚠️ 주의사항
*   이 프로그램은 원본 모드 파일을 **절대 수정하지 않습니다**. 안전하게 별도의 모드를 만들어냅니다.
*   Gemini API는 무료 티어 사용 시 분당 요청 제한(Rate Limit)이 있어 속도가 다소 느릴 수 있습니다.
*   Ollama 사용 시 그래픽카드 메모리(VRAM) 8GB 이상을 권장합니다.

## 📄 라이선스
MIT License
