#!/bin/bash

# 색상 설정
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===============================================================================${NC}"
echo -e "${GREEN}               HOI4 Web Translator - 원클릭 설치 마법사 (Mac/Linux)${NC}"
echo -e "${GREEN}===============================================================================${NC}"
echo ""

# 1. Python 확인
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[오류] Python3가 설치되지 않았습니다.${NC}"
    echo "공식 홈페이지나 패키지 매니저(brew, apt 등)를 통해 설치해주세요."
    exit 1
fi
echo -e "${GREEN}[확인] Python3 감지됨${NC}"

# 2. Node.js 확인
if ! command -v node &> /dev/null; then
    echo -e "${RED}[오류] Node.js가 설치되지 않았습니다.${NC}"
    echo "프론트엔드 빌드를 위해 Node.js가 필요합니다."
    exit 1
fi
echo -e "${GREEN}[확인] Node.js 감지됨${NC}"
echo ""

# 3. 백엔드 설정
echo -e "${YELLOW}[1/4] 백엔드 가상환경 설정 중...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "   - 가상환경 생성 중..."
    python3 -m venv venv
fi

echo "   - 패키지 설치 중..."
source venv/bin/activate

# UV 확인
if command -v uv &> /dev/null; then
    echo "   - UV 감지됨! 초고속 설치!"
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}[오류] 백엔드 패키지 설치 실패!${NC}"
    exit 1
fi
cd ..
echo -e "${GREEN}[완료] 백엔드 설정 완료!${NC}"
echo ""

# 4. 프론트엔드 설정
echo -e "${YELLOW}[2/4] 프론트엔드 패키지 설치 중...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "   - 이미 설치되어 있습니다."
fi

echo -e "${YELLOW}[3/4] 프론트엔드 빌드 중...${NC}"
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}[오류] 프론트엔드 빌드 실패!${NC}"
    exit 1
fi
cd ..
echo -e "${GREEN}[완료] 프론트엔드 설정 완료!${NC}"
echo ""

# 5. ParaTranz SDK 확인
echo -e "${YELLOW}[4/4] ParaTranz SDK 확인${NC}"
if [ ! -d "paratranz-sdk" ]; then
    echo -e "${YELLOW}[알림] 'paratranz-sdk' 폴더가 없습니다.${NC}"
    echo "ParaTranz 기능을 쓰시려면 README를 참고하여 SDK를 설치해주세요."
else
    echo -e "${GREEN}[확인] SDK 감지됨${NC}"
fi

echo ""
echo -e "${GREEN}===============================================================================${NC}"
echo -e "${GREEN} 설치가 완료되었습니다! './run_mac_linux.sh'를 실행하세요.${NC}"
echo -e "${GREEN}===============================================================================${NC}"
