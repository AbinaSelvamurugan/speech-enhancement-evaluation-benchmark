"""Evaluation-only manifest with required attribution, safe deterministic selection."""
from pathlib import Path
import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    recording_id: str
    clean: Path
    noise: Path
    noise_category: str
    clean_license: str
    noise_license: str
    clean_source: str
    noise_source: str


def read_manifest(path: Path) -> list[Example]:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Dataset manifest absent: {path}. Read data/README.md")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") not in {"real_recordings", "synthetic_test_only"}:
        raise ValueError("Manifest kind must be real_recordings or synthetic_test_only")
    if not isinstance(data.get("recordings"), list) or not data["recordings"]:
        raise ValueError("Manifest must contain at least one recording")
    result = []
    seen = set()
    for item in data["recordings"]:
        for field in ("id", "clean", "noise", "noise_category", "clean_license",
                      "noise_license", "clean_source", "noise_source"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Recording missing {field}")
        for field in ("id", "noise_category"):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", item[field]):
                raise ValueError(f"Unsafe {field}: {item[field]!r}")
        if item["id"] in seen:
            raise ValueError(f"Duplicate recording ID: {item['id']}")
        seen.add(item["id"])
        clean = (path.parent / item["clean"]).resolve()
        noise = (path.parent / item["noise"]).resolve()
        if not clean.is_file() or not noise.is_file():
            raise FileNotFoundError(f"{item['id']}: missing {clean if not clean.is_file() else noise}")
        result.append(Example(item["id"], clean, noise, item["noise_category"],
                              item["clean_license"], item["noise_license"],
                              item["clean_source"], item["noise_source"]))
    return sorted(result, key=lambda v: v.recording_id)


def manifest_kind(path: Path) -> str:
    return json.loads(Path(path).read_text(encoding="utf-8"))["kind"]
