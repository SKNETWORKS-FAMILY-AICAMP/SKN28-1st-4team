from __future__ import annotations

import asyncio
import re
import subprocess
import time
import urllib.request
from dataclasses import asdict, dataclass
from typing import Sequence


def _normalize_target(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.strip().lower()
    normalized = normalized.removesuffix(".nordvpn.com")
    return normalized.replace(" ", "_")


def _extract_server_alias(value: str | None) -> str:
    normalized = _normalize_target(value)
    if not normalized:
        return ""
    if "." in normalized:
        normalized = normalized.split(".", 1)[0]
    return normalized


def _extract_server_number(value: str | None) -> str:
    if not value:
        return ""
    match = re.search(r"(\d+)", value)
    if not match:
        return ""
    return match.group(1)


@dataclass(slots=True)
class VpnStatus:
    raw_output: str
    status: str | None = None
    server: str | None = None
    hostname: str | None = None
    ip: str | None = None
    country: str | None = None
    city: str | None = None
    uptime: str | None = None
    is_connected: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ProbeResult:
    url: str
    ok: bool
    status_code: int | None
    elapsed_seconds: float | None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class SwitchResult:
    success: bool
    target: str | None
    next_target_index: int
    current_ip: str | None
    error: str | None
    elapsed_seconds: float
    attempted_targets: list[str]
    status_before: dict[str, object]
    status_after: dict[str, object] | None = None
    probe: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


async def _run_command(*args: str, timeout_seconds: float = 60.0) -> subprocess.CompletedProcess[str]:
    return await asyncio.to_thread(
        subprocess.run,
        ["nordvpn", *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


async def get_vpn_status(timeout_seconds: float = 15.0) -> VpnStatus:
    completed = await _run_command("status", timeout_seconds=timeout_seconds)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "nordvpn status failed")
    return parse_vpn_status(completed.stdout)


def parse_vpn_status(output: str) -> VpnStatus:
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    status = fields.get("Status")
    return VpnStatus(
        raw_output=output,
        status=status,
        server=fields.get("Server"),
        hostname=fields.get("Hostname"),
        ip=fields.get("IP"),
        country=fields.get("Country"),
        city=fields.get("City"),
        uptime=fields.get("Uptime"),
        is_connected=status == "Connected",
    )


async def disconnect_vpn(timeout_seconds: float = 30.0) -> None:
    completed = await _run_command("disconnect", timeout_seconds=timeout_seconds)
    if completed.returncode != 0:
        error_message = completed.stderr.strip() or completed.stdout.strip()
        if "not connected" not in error_message.lower():
            raise RuntimeError(error_message or "nordvpn disconnect failed")


async def fetch_public_ip(timeout_seconds: float = 10.0) -> str | None:
    def _fetch() -> str | None:
        request = urllib.request.Request(
            "https://api.ipify.org?format=text",
            headers={"User-Agent": "data-collection-vpn-switcher"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return response.read().decode("utf-8").strip() or None
        except Exception:
            return None

    return await asyncio.to_thread(_fetch)


async def probe_url(url: str, timeout_seconds: float = 15.0) -> ProbeResult:
    def _probe() -> ProbeResult:
        started_at = time.perf_counter()
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "data-collection-vpn-switcher"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                response.read(1)
                elapsed_seconds = round(time.perf_counter() - started_at, 2)
                status_code = getattr(response, "status", None) or response.getcode()
                return ProbeResult(
                    url=url,
                    ok=200 <= status_code < 400,
                    status_code=status_code,
                    elapsed_seconds=elapsed_seconds,
                )
        except Exception as exc:  # noqa: BLE001
            elapsed_seconds = round(time.perf_counter() - started_at, 2)
            return ProbeResult(
                url=url,
                ok=False,
                status_code=None,
                elapsed_seconds=elapsed_seconds,
                error=str(exc),
            )

    return await asyncio.to_thread(_probe)


def _matches_target(status: VpnStatus, target: str) -> bool:
    normalized_target = _normalize_target(target)
    target_alias = _extract_server_alias(target)
    hostname_alias = _extract_server_alias(status.hostname)
    target_number = _extract_server_number(target_alias)
    status_number = _extract_server_number(status.server) or _extract_server_number(hostname_alias)

    candidates = {
        _normalize_target(status.country),
        _normalize_target(status.city),
        _normalize_target(status.server),
        _normalize_target(status.hostname),
        hostname_alias,
    }
    if normalized_target in candidates or target_alias in candidates:
        return True
    return bool(target_number and status_number and target_number == status_number)


async def wait_for_connection_change(
    *,
    target: str,
    disallowed_ips: set[str] | None = None,
    disallowed_hostnames: set[str] | None = None,
    timeout_seconds: float = 90.0,
    poll_interval_seconds: float = 2.0,
) -> VpnStatus:
    started_at = time.perf_counter()
    blocked_ips = {value for value in (disallowed_ips or set()) if value}
    blocked_hostnames = {_normalize_target(value) for value in (disallowed_hostnames or set()) if value}

    while True:
        status = await get_vpn_status()
        current_ip = status.ip or await fetch_public_ip()
        current_hostname = _normalize_target(status.hostname)
        ip_is_new = current_ip is not None and current_ip not in blocked_ips
        hostname_is_new = current_hostname and current_hostname not in blocked_hostnames
        ready = status.is_connected and _matches_target(status, target) and (ip_is_new or hostname_is_new)
        if ready:
            if current_ip and current_ip != status.ip:
                status.ip = current_ip
            return status

        if time.perf_counter() - started_at >= timeout_seconds:
            raise TimeoutError(f"VPN switch timed out while waiting for target={target}")
        await asyncio.sleep(poll_interval_seconds)


async def switch_to_target(
    target: str,
    *,
    disallowed_ips: set[str] | None = None,
    disallowed_hostnames: set[str] | None = None,
    connect_timeout_seconds: float = 60.0,
    ready_timeout_seconds: float = 90.0,
    poll_interval_seconds: float = 2.0,
    probe_target_url: str | None = None,
    probe_timeout_seconds: float = 15.0,
    max_probe_latency_seconds: float | None = None,
) -> SwitchResult:
    started_at = time.perf_counter()
    status_before = await get_vpn_status()
    baseline_ip = status_before.ip or await fetch_public_ip()

    completed = await _run_command("connect", target, timeout_seconds=connect_timeout_seconds)
    if completed.returncode != 0:
        return SwitchResult(
            success=False,
            target=target,
            next_target_index=0,
            current_ip=baseline_ip,
            error=completed.stderr.strip() or completed.stdout.strip() or "nordvpn connect failed",
            elapsed_seconds=round(time.perf_counter() - started_at, 2),
            attempted_targets=[target],
            status_before=status_before.to_dict(),
        )

    try:
        status_after = await wait_for_connection_change(
            target=target,
            disallowed_ips=disallowed_ips,
            disallowed_hostnames=disallowed_hostnames,
            timeout_seconds=ready_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        return SwitchResult(
            success=False,
            target=target,
            next_target_index=0,
            current_ip=baseline_ip,
            error=str(exc),
            elapsed_seconds=round(time.perf_counter() - started_at, 2),
            attempted_targets=[target],
            status_before=status_before.to_dict(),
        )

    probe_result: ProbeResult | None = None
    if probe_target_url:
        probe_result = await probe_url(probe_target_url, timeout_seconds=probe_timeout_seconds)
        if not probe_result.ok:
            return SwitchResult(
                success=False,
                target=target,
                next_target_index=0,
                current_ip=status_after.ip,
                error=probe_result.error or f"probe failed for {probe_target_url}",
                elapsed_seconds=round(time.perf_counter() - started_at, 2),
                attempted_targets=[target],
                status_before=status_before.to_dict(),
                status_after=status_after.to_dict(),
                probe=probe_result.to_dict(),
            )
        if (
            max_probe_latency_seconds is not None
            and probe_result.elapsed_seconds is not None
            and probe_result.elapsed_seconds > max_probe_latency_seconds
        ):
            return SwitchResult(
                success=False,
                target=target,
                next_target_index=0,
                current_ip=status_after.ip,
                error=(
                    f"probe latency {probe_result.elapsed_seconds}s exceeded "
                    f"{max_probe_latency_seconds}s"
                ),
                elapsed_seconds=round(time.perf_counter() - started_at, 2),
                attempted_targets=[target],
                status_before=status_before.to_dict(),
                status_after=status_after.to_dict(),
                probe=probe_result.to_dict(),
            )

    return SwitchResult(
        success=True,
        target=target,
        next_target_index=0,
        current_ip=status_after.ip,
        error=None,
        elapsed_seconds=round(time.perf_counter() - started_at, 2),
        attempted_targets=[target],
        status_before=status_before.to_dict(),
        status_after=status_after.to_dict(),
        probe=probe_result.to_dict() if probe_result else None,
    )


async def rotate_vpn_connection(
    *,
    targets: Sequence[str],
    start_index: int = 0,
    max_attempts: int | None = None,
    connect_timeout_seconds: float = 60.0,
    ready_timeout_seconds: float = 90.0,
    poll_interval_seconds: float = 2.0,
    probe_target_url: str | None = None,
    probe_timeout_seconds: float = 15.0,
    max_probe_latency_seconds: float | None = None,
) -> dict[str, object]:
    if not targets:
        raise ValueError("targets must not be empty")

    attempts = min(max_attempts or len(targets), len(targets))
    status_before = await get_vpn_status()
    attempted_targets: list[str] = []
    disallowed_ips = {value for value in [status_before.ip or await fetch_public_ip()] if value}
    disallowed_hostnames = {value for value in [status_before.hostname] if value}

    for offset in range(attempts):
        target_index = (start_index + offset) % len(targets)
        target = targets[target_index]
        attempted_targets.append(target)

        result = await switch_to_target(
            target,
            disallowed_ips=disallowed_ips,
            disallowed_hostnames=disallowed_hostnames,
            connect_timeout_seconds=connect_timeout_seconds,
            ready_timeout_seconds=ready_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            probe_target_url=probe_target_url,
            probe_timeout_seconds=probe_timeout_seconds,
            max_probe_latency_seconds=max_probe_latency_seconds,
        )

        if result.success:
            result.next_target_index = (target_index + 1) % len(targets)
            result.attempted_targets = attempted_targets.copy()
            return result.to_dict()

        status_after = result.status_after or {}
        if result.current_ip:
            disallowed_ips.add(result.current_ip)
        if isinstance(status_after.get("ip"), str) and status_after["ip"]:
            disallowed_ips.add(status_after["ip"])
        if isinstance(status_after.get("hostname"), str) and status_after["hostname"]:
            disallowed_hostnames.add(status_after["hostname"])

        await disconnect_vpn()

    return SwitchResult(
        success=False,
        target=None,
        next_target_index=(start_index + attempts) % len(targets),
        current_ip=None,
        error="all VPN targets failed readiness checks",
        elapsed_seconds=0.0,
        attempted_targets=attempted_targets,
        status_before=status_before.to_dict(),
    ).to_dict()
