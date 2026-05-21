#!/usr/bin/env python3
"""Lista collections principais no sandbox (somente leitura)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _config import get_client  # noqa: E402


def _print_block(title: str, items: list, limit: int = 5) -> None:
    print(f"\n=== {title} ({len(items)} total, mostrando até {limit}) ===")
    for item in items[:limit]:
        label = getattr(item, "name", None) or getattr(item, "email", None) or item.id
        extra = getattr(item, "status", None)
        suffix = f" [{extra}]" if extra else ""
        print(f"  - {item.id}  {label}{suffix}")
    if len(items) > limit:
        print(f"  ... +{len(items) - limit} itens")


def main() -> None:
    import os

    from clicksign.configuration import _ENVIRONMENTS

    client = get_client()
    env = os.environ.get("CLICKSIGN_ENVIRONMENT", "sandbox")
    print(f"Ambiente: {env} → {_ENVIRONMENTS.get(env, env)}")

    envelopes = client.notarial.envelopes.list()
    _print_block("Envelopes", envelopes)

    try:
        folders = client.folders.list()
        _print_block("Folders", folders)
    except Exception as exc:
        print(f"\n=== Folders (erro: {exc}) ===")

    try:
        webhooks = client.webhooks.list()
        _print_block("Webhooks", webhooks)
    except Exception as exc:
        print(f"\n=== Webhooks (erro: {exc}) ===")

    try:
        users = client.users.list()
        _print_block("Users", users)
    except Exception as exc:
        print(f"\n=== Users (erro: {exc}) ===")

    print("\nOK — consultas concluídas.")


if __name__ == "__main__":
    main()
