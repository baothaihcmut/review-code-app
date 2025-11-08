import json
from typing import Any, Dict


def safe_parse_json_response(response: str) -> Dict[str, Any]:
    """Try to parse response into dict if it contains JSON-like text."""
    try:
        return json.loads(response)
    except Exception:
        return {"raw": str(response)}
