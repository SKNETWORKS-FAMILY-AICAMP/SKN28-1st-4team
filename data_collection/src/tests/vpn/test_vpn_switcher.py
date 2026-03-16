"""Smoke tests for NordVPN helper parsing and probing logic."""

import asyncio
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[3]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts import vpn_switcher  # noqa: E402


async def main() -> None:
    status = vpn_switcher.parse_vpn_status(
        "\n".join(
            [
                "Status: Connected",
                "Server: Japan #805",
                "Hostname: jp805.nordvpn.com",
                "IP: 217.217.114.105",
                "Country: Japan",
                "City: Tokyo",
                "Uptime: 5 minutes 23 seconds",
            ]
        )
    )
    assert status.is_connected is True
    assert status.country == "Japan"
    assert status.server == "Japan #805"
    assert vpn_switcher._matches_target(status, "jp805") is True
    assert vpn_switcher._matches_target(status, "jp805.nordvpn.com") is True
    assert vpn_switcher._matches_target(status, "kr115") is False

    probe = await vpn_switcher.probe_url("https://api.ipify.org?format=text", timeout_seconds=10.0)
    assert probe.ok is True
    assert probe.status_code == 200
    assert probe.elapsed_seconds is not None

    print(
        {
            "parsed_status": status.to_dict(),
            "probe": probe.to_dict(),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
