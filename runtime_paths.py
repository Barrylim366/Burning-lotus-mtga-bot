from __future__ import annotations

import sys
from pathlib import Path


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return get_repo_root()


def get_runtime_root() -> Path:
    path = get_app_root() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_runtime_subdir(*parts: str) -> Path:
    path = get_runtime_root().joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_file(*parts: str) -> Path:
    if len(parts) > 1:
        ensure_runtime_subdir(*parts[:-1])
    else:
        get_runtime_root()
    return get_runtime_root().joinpath(*parts)

