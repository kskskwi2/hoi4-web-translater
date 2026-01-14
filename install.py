import os
import sys
import subprocess
import time
import shutil


# 색상 코드 (Windows CMD 호환)
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


# 윈도우에서 ANSI 코드 활성화
os.system("")


def print_step(msg):
    print(f"\n{Colors.CYAN}[진행] {msg}{Colors.ENDC}")


def print_success(msg):
    print(f"{Colors.GREEN}[성공] {msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.FAIL}[오류] {msg}{Colors.ENDC}")


def print_header():
    print(f"{Colors.HEADER}========================================================")
    print(f"       HOI4 Web Translator - 설치 마법사")
    print(f"========================================================{Colors.ENDC}")
    print("이 스크립트는 번역기 실행에 필요한 모든 환경을 자동으로 설정합니다.\n")


def check_node():
    print_step("Node.js 설치 확인 중...")
    try:
        subprocess.run(
            ["node", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print_success("Node.js가 감지되었습니다.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Node.js가 설치되지 않았습니다!")
        print(f"{Colors.WARNING}프론트엔드 빌드를 위해 Node.js가 필요합니다.")
        print(f"다운로드: https://nodejs.org/ (LTS 버전 추천){Colors.ENDC}")
        return False


def setup_backend():
    print_step("백엔드 설정 중... (backend/venv)")
    backend_dir = os.path.join(os.getcwd(), "backend")

    if not os.path.exists(backend_dir):
        print_error("'backend' 폴더를 찾을 수 없습니다.")
        return False

    os.chdir(backend_dir)

    # 1. 가상환경 생성
    if not os.path.exists("venv"):
        print("  - 가상환경(venv) 생성 중...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

    # 2. 패키지 설치
    print("  - 필요한 패키지 설치 중... (pip install)")

    # 가상환경 내의 Python 실행 파일 경로 찾기
    if os.name == "nt":
        venv_python = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")

    if not os.path.exists(venv_python):
        print_error(f"가상환경 파이썬을 찾을 수 없습니다: {venv_python}")
        return False

    try:
        # pip 업그레이드 (python -m pip 방식이 가장 안전함)
        subprocess.run(
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.DEVNULL,
        )

        # requirements.txt 설치
        if os.path.exists("requirements.txt"):
            subprocess.run(
                [venv_python, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
            )
            print_success("백엔드 패키지 설치 완료.")
        else:
            print_error("requirements.txt 파일이 없습니다.")
            return False

    except subprocess.CalledProcessError as e:
        print_error(f"패키지 설치 실패: {e}")
        return False
    except FileNotFoundError:
        print_error(f"실행 파일을 찾을 수 없습니다: {venv_python}")
        return False

    os.chdir("..")
    return True


def setup_frontend():
    print_step("프론트엔드 설정 중... (frontend)")
    frontend_dir = os.path.join(os.getcwd(), "frontend")

    if not os.path.exists(frontend_dir):
        print_error("'frontend' 폴더를 찾을 수 없습니다.")
        return False

    os.chdir(frontend_dir)

    # 1. npm install
    if not os.path.exists("node_modules"):
        print("  - 라이브러리 설치 중 (npm install)... 시간이 걸릴 수 있습니다.")
        try:
            subprocess.run(["npm", "install"], check=True, shell=True)
        except subprocess.CalledProcessError:
            print_error("npm install 실패. Node.js 버전을 확인해주세요.")
            return False
    else:
        print("  - node_modules가 이미 존재합니다. 스킵.")

    # 2. npm run build
    print("  - 웹사이트 빌드 중 (npm run build)...")
    try:
        subprocess.run(["npm", "run", "build"], check=True, shell=True)
        print_success("프론트엔드 빌드 완료.")
    except subprocess.CalledProcessError:
        print_error("빌드 실패.")
        return False

    os.chdir("..")
    return True


def check_sdk():
    print_step("ParaTranz SDK 확인")
    sdk_path = os.path.join(os.getcwd(), "paratranz-sdk")
    if os.path.exists(sdk_path):
        print_success("SDK 폴더가 존재합니다.")
    else:
        print(f"{Colors.WARNING}[알림] 'paratranz-sdk' 폴더가 없습니다.")
        print(f"ParaTranz 연동 기능을 쓰시려면 나중에 SDK를 설치해주세요.{Colors.ENDC}")


def main():
    print_header()

    if not check_node():
        input("\n엔터를 누르면 종료합니다...")
        return

    if not setup_backend():
        input("\n엔터를 누르면 종료합니다...")
        return

    if not setup_frontend():
        input("\n엔터를 누르면 종료합니다...")
        return

    check_sdk()

    print(
        f"\n{Colors.GREEN}========================================================{Colors.ENDC}"
    )
    print(f"{Colors.GREEN}       설치가 모두 완료되었습니다!{Colors.ENDC}")
    print(f"{Colors.GREEN}       이제 'run_windows.bat'을 실행하세요.{Colors.ENDC}")
    print(
        f"{Colors.GREEN}========================================================{Colors.ENDC}"
    )
    input("\n엔터를 누르면 종료합니다...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n취소되었습니다.")
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        input("종료하려면 엔터를 누르세요...")
