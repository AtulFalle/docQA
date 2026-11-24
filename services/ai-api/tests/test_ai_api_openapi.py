import json
from pathlib import Path

from docqa_ai_api.openapi import build_openapi, main

COMMITTED = Path(__file__).parents[3] / "libs/shared/contracts/openapi/ai-api.openapi.json"


def test_openapi_documents_every_route_with_a_schema() -> None:
    doc = build_openapi()
    assert set(doc["paths"]) == {"/healthz", "/readyz", "/v1/info"}
    schemas = doc["components"]["schemas"]
    assert {"LivenessResponse", "ReadinessResponse", "ServiceInfo"} <= set(schemas)
    readyz = doc["paths"]["/readyz"]["get"]["responses"]
    assert readyz["503"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReadinessResponse"
    }


def test_committed_document_is_current() -> None:
    assert json.loads(COMMITTED.read_text(encoding="utf-8")) == build_openapi(), (
        "ai-api OpenAPI changed: run `make contracts` and commit the result"
    )


def test_main_writes_sorted_json(tmp_path: Path) -> None:
    out = tmp_path / "ai-api.json"
    assert main(["openapi", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == build_openapi()
