#!/bin/bash

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}   HOI4 Web Translator를 시작합니다!${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""

# 백엔드 실행
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "가상환경(venv)이 없습니다. setup 스크립트를 먼저 실행해주세요."
    # 강제 실행 시도
fi
cd ..

python3 start.py
