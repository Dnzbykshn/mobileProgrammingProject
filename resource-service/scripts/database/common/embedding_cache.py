import json
from pathlib import Path
from typing import Any


def load_json_cache(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default.copy() if default is not None else {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
