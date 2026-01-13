# Paradox Localisation Manager (HOI4 Web Translater)

An automated tool to translate Hearts of Iron IV mods using a modern web interface. Designed for ease of use and extensibility.

![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB.svg)

## Features

*   **Auto-Detection**: Automatically finds your Steam Workshop mods.
*   **One-Click Translation**: Generates a standalone translation mod with proper structure.
*   **Smart Parsing**: Handles Paradox `.mod` and `.txt` files accurately.
*   **Encoding Safe**: Preserves UTF-8 BOM encoding for HOI4 compatibility.
*   **Web Interface**: A premium, responsive UI for managing your translations.
*   **AI Powered**: Supports Google Translate, Ollama (Local LLM), OpenAI, Claude, Gemini.

---

## Installation & Usage (English)

### Prerequisites
*   Git
*   Python 3.9+
*   Node.js & npm (for building frontend)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/hoi4-web-translater.git
cd hoi4-web-translater
```

### 2. Install Dependencies

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 3. Run the Application
The `start.py` script initializes the backend server.
```bash
python start.py
```
*   The backend will start at `http://127.0.0.1:8080` (or similar port).
*   If you are in development mode, run the frontend separately with `npm run dev` in the `frontend` folder.

### 4. How to Use
1.  Open the web interface in your browser.
2.  The app will scan your Steam Workshop folder for HOI4 mods.
3.  Select a mod to translate.
4.  Choose your translation service (Google, Ollama, OpenAI, etc.).
5.  Click "Start Translation".
6.  Once finished, the translation mod will be generated in your Documents/Paradox Interactive/Hearts of Iron IV/mod folder.
7.  Enable the new translation mod in the HOI4 Launcher.

---

## 설치 및 사용법 (한국어)

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

---

## License

This project is open source and available under the [GNU Affero General Public License v3.0](LICENSE).
