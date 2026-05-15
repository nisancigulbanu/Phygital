import base64
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib import request

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _encode_demo_label(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def live_server():
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                _request_json("GET", f"http://127.0.0.1:{port}/api/v1/health")
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("server_start_timeout")
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_scan_success(live_server):
    body = _request_json(
        "POST",
        f"{live_server}/api/v1/scan",
        {
            "image": _encode_demo_label("80% Cotton 20% Polyester Made in Bangladesh Wash at 30C Zara"),
            "price": 299.9,
        },
    )
    assert body["fabric_composition"]["pamuk"] == 80
    assert body["fabric_composition"]["polyester"] == 20
    assert body["origin_country"] == "Bangladesh"
    assert body["quality_grade"] == "C"
    assert body["scan_id"]


def test_scan_without_fabric_returns_null_quality(live_server):
    body = _request_json(
        "POST",
        f"{live_server}/api/v1/scan",
        {"image": _encode_demo_label("Made in Turkey Dry clean only")},
    )
    assert body["quality_score"] is None
    assert body["fabric_composition"] == {}


def test_chat_success(live_server):
    scan = _request_json(
        "POST",
        f"{live_server}/api/v1/scan",
        {"image": _encode_demo_label("80% Cotton 20% Polyester Made in Bangladesh"), "price": 299.9},
    )
    body = _request_json(
        "POST",
        f"{live_server}/api/v1/chat",
        {"message": "Bu urunu almali miyim?", "context": scan},
    )
    assert "kalite skoru" in body["reply"].lower()


def _request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))
