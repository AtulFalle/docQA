"""Write the ai-api OpenAPI document: `python -m docqa_ai_api.openapi <out.json>`.

The document is the contract with the NestJS backend; `make contracts` regenerates the
TypeScript client types from it and CI fails if the committed copy is stale.
"""

import json
import sys
from pathlib import Path
from typing import Any

from docqa_ai_api.main import create_app
from docqa_core.config import Settings


def build_openapi() -> dict[str, Any]:
    """Build the OpenAPI document without starting the app or touching a database."""
    return create_app(Settings(_env_file=None)).openapi()


def main(argv: list[str]) -> int:
    """Write the document to the path in `argv[1]`, or to stdout."""
    text = json.dumps(build_openapi(), indent=2, sort_keys=True) + "\n"
    if len(argv) > 1:
        Path(argv[1]).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
