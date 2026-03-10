"""Documentation helper commands."""
from __future__ import annotations

from pathlib import Path


def mkdocs_init(root: str | Path, *, force: bool = False) -> None:
    root_path = Path(root).expanduser().resolve()
    mkdocs_path = root_path / "mkdocs.yml"
    docs_dir = root_path / "docs"
    index_md = docs_dir / "index.md"

    if mkdocs_path.exists() and not force:
        print(f"[SKIP] {mkdocs_path.name} already exists")
    else:
        mkdocs_path.write_text(
            f"site_name: {root_path.name}\ndocs_dir: docs\ntheme:\n  name: material\n",
            encoding="utf-8",
        )
        print(f"[OK] wrote {mkdocs_path.relative_to(root_path)}")

    docs_dir.mkdir(exist_ok=True)
    if index_md.exists() and not force:
        print(f"[SKIP] {index_md.relative_to(root_path)} already exists")
    else:
        index_md.write_text(f"# {root_path.name}\n", encoding="utf-8")
        print(f"[OK] wrote {index_md.relative_to(root_path)}")
