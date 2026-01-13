# Paradox Localisation Manager (HOI4 Web Translater)

An automated tool to translate Hearts of Iron IV mods using a modern web interface. Designed for ease of use and extensibility.

![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB.svg)

> [한국어 설명서 보러가기 (Read in Korean)](README.md)

## Features

*   **Auto-Detection**: Automatically finds your Steam Workshop mods.
*   **One-Click Translation**: Generates a standalone translation mod with proper structure.
*   **Smart Parsing**: Handles Paradox `.mod` and `.txt` files accurately.
*   **Encoding Safe**: Preserves UTF-8 BOM encoding for HOI4 compatibility.
*   **Web Interface**: A premium, responsive UI for managing your translations.
*   **AI Powered**: Supports Google Translate, Ollama (Local LLM), OpenAI, Claude, Gemini.

## Installation & Usage

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

## License

This project is open source and available under the [GNU Affero General Public License v3.0](LICENSE).
