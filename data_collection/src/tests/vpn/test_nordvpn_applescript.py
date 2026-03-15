"""NordVPN AppleScript 수동 테스트 스크립트.

이 스크립트는 NordVPN GUI 자동화를 직접 호출한다.
접근성 권한이 없으면 실패할 수 있다.

실행 예시:
    uv run python tests/vpn/test_nordvpn_applescript.py Japan
"""

import subprocess
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = SRC_DIR.parent / "scripts" / "nordvpn_connect_country.applescript"


def main() -> None:
    country = sys.argv[1] if len(sys.argv) > 1 else "Japan"
    completed = subprocess.run(
        ["osascript", str(SCRIPT_PATH), country],
        capture_output=True,
        text=True,
    )

    print({
        "returncode": completed.returncode,
        "country": country,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    })

    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
