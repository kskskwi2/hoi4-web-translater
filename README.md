# Paradox Localisation Manager (HOI4 웹 번역기)

![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)
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

## 🚀 초간편 설치 및 실행 (Windows)

복잡한 명령어 없이 원클릭으로 설치하세요.

### 필수 요구사항
*   [Python 3.10 이상](https://www.python.org/) (**설치 시 'Add Python to PATH' 체크 필수**)
*   [Node.js 18 이상](https://nodejs.org/) (LTS 버전 추천)
*   [Ollama](https://ollama.com/) (로컬 AI 사용 시 선택 사항)

### 1. 프로젝트 다운로드
```bash
git clone https://github.com/kskskwi2/hoi4-web-translater.git
cd hoi4-web-translater
```

### 2. 원클릭 설치
폴더 안에 있는 **`setup_windows.bat`** 파일을 더블 클릭하세요.
*   자동으로 가상환경을 만들고 필요한 라이브러리를 모두 설치합니다.
*   프론트엔드(웹 화면)까지 자동으로 빌드합니다.

### 3. 프로그램 실행
설치가 끝나면 **`run_windows.bat`** 파일을 더블 클릭하세요.
*   서버가 켜지고 잠시 후 브라우저가 자동으로 열립니다 (`http://localhost:8080`).

---

## 🐧 맥/리눅스 (Mac/Linux) 설치

터미널을 열고 아래 명령어를 순서대로 입력하세요.

```bash
chmod +x setup_mac_linux.sh run_mac_linux.sh
./setup_mac_linux.sh  # 설치
./run_mac_linux.sh    # 실행
```

---

## 📖 사용 가이드

1.  **모드 선택**: 앱을 켜면 자동으로 스캔된 모드 목록이 뜹니다. 번역하고 싶은 모드를 선택하세요.
2.  **AI 서비스 선택**:
    *   **Ollama**: 내 컴퓨터 성능을 사용 (무료, 개인 정보 보호). `Qwen2.5-7B` 모델을 강력 추천합니다.
    *   **OpenAI/Claude/Gemini**: API 키를 입력하여 사용 (유료, 고성능).
3.  **번역 시작**: 설정(타겟 언어, 용어집 등)을 확인하고 'Start Translation'을 누르세요.
4.  **적용**: 번역이 끝나면 `문서/Paradox Interactive/Hearts of Iron IV/mod` 폴더에 번역 모드가 생성됩니다. 게임 런처에서 해당 모드를 켜고 게임을 즐기세요.

## 🤝 ParaTranz 연동 (협업 번역)
혼자가 아니라 팀으로 번역하고 싶다면 파라트랜즈를 연동하세요. (SDK 설치 필요)

1.  **SDK 준비**: [ParaTranz API 문서](https://paratranz.cn/docs)를 참고하여 `openapi-generator`로 SDK를 생성하거나, 미리 빌드된 `paratranz-sdk` 폴더를 프로젝트 폴더(`hoi4-web-translater`) 안에 넣으세요.
2.  **설정**: 웹 설정 메뉴에서 API Token 입력.
3.  **동기화**: 원본 파일 업로드 및 번역물 다운로드/동기화 가능.

## 📄 라이선스 (License)
**GNU Affero General Public License v3.0 (AGPL-3.0)**
이 소프트웨어를 네트워크를 통해 서비스하는 경우, 전체 소스 코드를 공개해야 합니다.
