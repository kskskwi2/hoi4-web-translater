# Paradox Localisation Manager (HOI4 웹 번역기)

Hearts of Iron IV 모드를 최신 웹 인터페이스를 통해 자동으로 번역해주는 도구입니다. 사용 편의성과 확장성을 고려하여 설계되었습니다.

![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB.svg)

> [Read in English (영어 설명서)](README_EN.md)

## 주요 기능

*   **자동 감지**: 스팀 창작마당(Steam Workshop) 모드를 자동으로 찾아줍니다.
*   **원클릭 번역**: 올바른 구조를 갖춘 독립적인 번역 모드를 생성합니다.
*   **스마트 파싱**: Paradox의 `.mod` 및 `.txt` 파일을 정확하게 처리합니다.
*   **인코딩 안전성**: HOI4 호환성을 위해 UTF-8 BOM 인코딩을 보존합니다.
*   **웹 인터페이스**: 번역을 관리하기 위한 고급스럽고 반응형인 UI를 제공합니다.
*   **AI 기반**: Google 번역, Ollama (로컬 LLM), OpenAI, Claude, Gemini를 지원합니다.

## 설치 및 사용법

### 필수 요구사항
*   Git
*   Python 3.9 이상
*   Node.js 및 npm (프론트엔드 빌드용)

### 1. 저장소 복제 (Clone)
```bash
git clone https://github.com/yourusername/hoi4-web-translater.git
cd hoi4-web-translater
```

### 2. 의존성 설치

**백엔드 (Backend):**
```bash
pip install -r requirements.txt
```

**프론트엔드 (Frontend):**
```bash
cd frontend
npm install
cd ..
```

### 3. 프로그램 실행
`start.py` 스크립트를 실행하여 백엔드 서버를 시작합니다.
```bash
python start.py
```
*   백엔드 서버가 `http://127.0.0.1:8080` (또는 지정된 포트)에서 시작됩니다.
*   개발 모드인 경우, `frontend` 폴더에서 `npm run dev`를 실행하여 프론트엔드 서버를 별도로 띄워야 할 수 있습니다.

### 4. 사용 방법
1.  브라우저에서 웹 인터페이스를 엽니다.
2.  앱이 자동으로 스팀 창작마당(Steam Workshop) 폴더를 스캔하여 HOI4 모드 목록을 불러옵니다.
3.  번역할 모드를 선택합니다.
4.  번역 서비스(Google, Ollama, OpenAI 등)를 선택합니다.
5.  "Start Translation" 버튼을 클릭합니다.
6.  번역이 완료되면 `내 문서/Paradox Interactive/Hearts of Iron IV/mod` 폴더에 번역 모드가 생성됩니다.
7.  HOI4 런처를 실행하고 새로 생성된 번역 모드를 활성화하여 게임을 실행하세요.

## 라이선스

이 프로젝트는 오픈 소스이며 [GNU Affero General Public License v3.0](LICENSE) 하에 배포됩니다.
