"""D14 two-party interoperability lab for the selected digest migration.

This is a controlled legacy-to-migrated compatibility experiment. It is not
a PQC KEM, TLS hybrid, or proof of compatibility with an external protocol.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import platform
import socket
import statistics
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

LAB_VERSION = "2026.10.02-d14.1"
SUPPORTED_MODES = ("sha256", "md5")
MAX_MESSAGE_BYTES = 64 * 1024

@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    client_modes: tuple[str, ...]
    server_modes: tuple[str, ...]
    expected_success: bool
    expected_mode: str | None
    tamper_digest: bool = False

SCENARIOS = (
    Scenario("legacy_match", ("md5",), ("md5",), True, "md5"),
    Scenario("migrated_match", ("sha256",), ("sha256",), True, "sha256"),
    Scenario("transitional_prefers_migrated", ("sha256", "md5"), ("sha256", "md5"), True, "sha256"),
    Scenario("transitional_legacy_fallback", ("sha256", "md5"), ("md5",), True, "md5"),
    Scenario("mismatched_peers", ("md5",), ("sha256",), False, None),
    Scenario("digest_mismatch", ("sha256",), ("sha256",), False, "sha256", True),
)

def _send(endpoint: socket.socket, message: dict[str, Any]) -> int:
    payload = json.dumps(message, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    endpoint.sendall(payload)
    return len(payload)

def _receive(endpoint: socket.socket) -> tuple[dict[str, Any], int]:
    chunks = bytearray()
    while not chunks.endswith(b"\n"):
        part = endpoint.recv(4096)
        if not part:
            raise ConnectionError("peer closed before a complete message")
        chunks.extend(part)
        if len(chunks) > MAX_MESSAGE_BYTES:
            raise ValueError("message exceeds lab limit")
    return json.loads(chunks.decode()), len(chunks)

def _server(endpoint: socket.socket, modes: tuple[str, ...], payload: bytes,
            observation: dict[str, Any]) -> None:
    wire_bytes = 0
    try:
        hello, received = _receive(endpoint); wire_bytes += received
        offered = hello.get("modes", [])
        selected = next((m for m in modes if m in offered and m in SUPPORTED_MODES), None)
        if selected is None:
            wire_bytes += _send(endpoint, {"status": "no_common_mode", "selected_mode": None})
            observation.update(status="no_common_mode", selected_mode=None, success=False)
            return
        wire_bytes += _send(endpoint, {"status": "selected", "selected_mode": selected})
        proof, received = _receive(endpoint); wire_bytes += received
        expected = hashlib.new(selected, payload).hexdigest()
        accepted = hmac.compare_digest(str(proof.get("digest", "")), expected)
        status = "accepted" if accepted else "digest_mismatch"
        wire_bytes += _send(endpoint, {"status": status, "selected_mode": selected})
        observation.update(status=status, selected_mode=selected, success=accepted)
    except Exception as exc:
        observation.update(status="server_error", selected_mode=None, success=False, error=type(exc).__name__)
    finally:
        observation["wire_bytes"] = wire_bytes
        endpoint.close()

def run_exchange(scenario: Scenario, payload: bytes = b"pqmigrate-d14-interoperability") -> dict[str, Any]:
    for mode in (*scenario.client_modes, *scenario.server_modes):
        if mode not in SUPPORTED_MODES:
            raise ValueError(f"unsupported mode: {mode}")
    client, server = socket.socketpair()
    client.settimeout(2); server.settimeout(2)
    observation: dict[str, Any] = {}
    worker = threading.Thread(target=_server, args=(server, scenario.server_modes, payload, observation), daemon=True)
    started = time.perf_counter_ns(); worker.start()
    client_wire = _send(client, {"modes": list(scenario.client_modes)})
    selection, received = _receive(client); client_wire += received
    if selection["status"] == "selected":
        selected = selection["selected_mode"]
        digest = hashlib.new(selected, payload).hexdigest()
        if scenario.tamper_digest:
            digest = "0" * len(digest)
        client_wire += _send(client, {"digest": digest})
        final, received = _receive(client); client_wire += received
        client_status = final["status"]
    else:
        client_status = selection["status"]
    client.close(); worker.join(timeout=2)
    success = bool(observation.get("success")) and client_status == "accepted"
    chosen = observation.get("selected_mode")
    return {
        "scenario_id": scenario.scenario_id, "success": success, "status": client_status,
        "selected_mode": chosen, "duration_ns": time.perf_counter_ns() - started,
        "wire_bytes": client_wire,
        "digest_bytes": hashlib.new(chosen).digest_size if chosen else 0,
        "expected_success": scenario.expected_success, "expected_mode": scenario.expected_mode,
        "expectation_met": success == scenario.expected_success and chosen == scenario.expected_mode,
    }

def run_interop_lab(repeats: int = 20) -> dict[str, Any]:
    if repeats < 1 or repeats > 1000:
        raise ValueError("repeats must be in the range 1..1000")
    raw = []
    for scenario in SCENARIOS:
        for sample in range(repeats):
            result = run_exchange(scenario); result["sample_index"] = sample; raw.append(result)
    summaries = []
    for scenario in SCENARIOS:
        samples = [r for r in raw if r["scenario_id"] == scenario.scenario_id]
        durations = [r["duration_ns"] for r in samples]
        summaries.append({
            "scenario_id": scenario.scenario_id, "client_modes": list(scenario.client_modes),
            "server_modes": list(scenario.server_modes), "expected_success": scenario.expected_success,
            "expected_mode": scenario.expected_mode, "sample_count": len(samples),
            "observed_successes": sum(r["success"] for r in samples),
            "observed_failures": sum(not r["success"] for r in samples),
            "expectations_met": all(r["expectation_met"] for r in samples),
            "duration_ns": {"min": min(durations), "median": int(statistics.median(durations)), "max": max(durations)},
            "selected_modes": sorted({r["selected_mode"] for r in samples if r["selected_mode"]}),
            "visible_failure_statuses": sorted({r["status"] for r in samples if not r["success"]}),
        })
    return {
        "schema_version": LAB_VERSION, "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass_bounded" if all(r["expectation_met"] for r in raw) else "fail",
        "roadmap_hybrid_matrix_completed": False,
        "claim_scope": "controlled_md5_to_sha256_two_party_compatibility",
        "not_claimed": ["PQC or hybrid KEM interoperability", "TLS, SSH, JWT, certificate, database, or external-provider compatibility", "production performance"],
        "transport": "local_os_socket_pair", "payload_bytes": len(b"pqmigrate-d14-interoperability"),
        "repeats_per_scenario": repeats, "scenario_count": len(SCENARIOS), "total_samples": len(raw),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "implementation": platform.python_implementation()},
        "summaries": summaries, "samples": raw,
    }
