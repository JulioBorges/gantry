"""A minimal greeting function used by the Gantry reference fixture."""
from __future__ import annotations


def greet(name: str) -> str:
    """Return a friendly greeting for ``name``."""
    name = name.strip()
    if not name:
        raise ValueError("name must be a non-empty string")
    return f"Hello, {name}!"
