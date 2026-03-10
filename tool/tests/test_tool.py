from __future__ import annotations


def test_import() -> None:
    import tool

    assert tool.__name__ == "tool"
