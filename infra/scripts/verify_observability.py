"""End-to-end observability check against the running compose stack (`make up-app`).

Sends one request with a fresh request id through backend -> ai-api, then asserts in Grafana that:
  1. Loki has log lines with that request_id from both docqa-backend and docqa-ai-api,
  2. those lines share one trace_id,
  3. Tempo has that trace with spans from both services.

Stdlib only. Usage:  uv run python -I infra/scripts/verify_observability.py
Exit code 0 on success, 1 on failure. Prints a Grafana link to the trace.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

SERVICES = ("docqa-backend", "docqa-ai-api")
HTTP_OK = 200


def _say(message: str, *, error: bool = False) -> None:
    (sys.stderr if error else sys.stdout).write(message + "\n")


def _get(url: str, headers: dict[str, str] | None = None) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers=headers or {})  # noqa: S310 - fixed local URLs
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as err:
        body = err.read()
        return err.code, json.loads(body) if body.startswith(b"{") else None


def send_request(backend: str, request_id: str) -> None:
    """Call readiness, which makes the backend call ai-api's /healthz."""
    status, _ = _get(f"{backend}/api/v1/health/ready", {"X-Request-ID": request_id})
    _say(f"backend readiness -> HTTP {status} (request_id={request_id})")


def _trace_id_of(entry: dict[str, Any], line: str) -> str | None:
    trace_id = entry.get("trace_id")
    if isinstance(trace_id, str):
        return trace_id
    try:
        parsed = json.loads(line)
    except ValueError:
        return None
    value = parsed.get("trace_id") if isinstance(parsed, dict) else None
    return value if isinstance(value, str) else None


def find_logs(grafana: str, request_id: str) -> dict[str, set[str]]:
    """Return {service: {trace_id, ...}} for log lines carrying ``request_id``."""
    selector = "|".join(SERVICES)
    query = f'{{service_name=~"{selector}"}} | request_id="{request_id}"'
    params = urllib.parse.urlencode(
        {"query": query, "start": str(int((time.time() - 900) * 1e9)), "limit": "100"}
    )
    url = f"{grafana}/api/datasources/proxy/uid/loki/loki/api/v1/query_range?{params}"
    status, body = _get(url)
    found: dict[str, set[str]] = {}
    if status != HTTP_OK or not body:
        return found
    for stream in body["data"]["result"]:
        labels: dict[str, Any] = stream["stream"]
        service = labels.get("service_name", "?")
        for _ts, line, *meta in stream["values"]:
            entry = {**labels, **(meta[0] if meta and isinstance(meta[0], dict) else {})}
            trace_id = _trace_id_of(entry, line)
            found.setdefault(service, set())
            if trace_id:
                found[service].add(trace_id)
    return found


def trace_services(grafana: str, trace_id: str) -> set[str]:
    """Return the service.name of every resource in the Tempo trace."""
    status, body = _get(f"{grafana}/api/datasources/proxy/uid/tempo/api/traces/{trace_id}")
    if status != HTTP_OK or not body:
        return set()
    names: set[str] = set()
    for batch in body.get("batches") or body.get("resourceSpans") or []:
        for attr in batch.get("resource", {}).get("attributes", []):
            if attr.get("key") == "service.name":
                names.add(attr["value"].get("stringValue", ""))
    return names


def _check_once(grafana: str, request_id: str) -> tuple[bool, str, str | None]:
    logs = find_logs(grafana, request_id)
    missing = [s for s in SERVICES if s not in logs]
    if missing:
        return False, f"no Loki logs yet from {missing}", None
    trace_ids = set().union(*logs.values())
    if len(trace_ids) != 1:
        return False, f"expected one trace_id across services, got {sorted(trace_ids)}", None
    trace_id = trace_ids.pop()
    in_trace = trace_services(grafana, trace_id)
    missing = [s for s in SERVICES if s not in in_trace]
    if missing:
        return False, f"trace {trace_id} has no spans from {missing} (has {sorted(in_trace)})", None
    return True, f"logs and trace {trace_id} span {sorted(in_trace)}", trace_id


def main() -> int:
    """Run the check, retrying while telemetry is still being exported."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--backend", default="http://localhost:3000")
    parser.add_argument("--grafana", default="http://localhost:3002")
    parser.add_argument("--timeout", type=float, default=90.0, help="seconds to wait")
    args = parser.parse_args()

    request_id = f"obs-check-{uuid.uuid4()}"
    send_request(args.backend, request_id)
    deadline = time.monotonic() + args.timeout
    reason = ""
    while time.monotonic() < deadline:
        ok, reason, trace_id = _check_once(args.grafana, request_id)
        if ok:
            _say(f"OK: request_id={request_id}: {reason}")
            _say(
                f"Trace: {args.grafana}/explore?left="
                + urllib.parse.quote(
                    json.dumps({"datasource": "tempo", "queries": [{"query": trace_id}]})
                )
            )
            return 0
        time.sleep(3)
    _say(f"FAIL: request_id={request_id}: {reason}", error=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
