"""End-to-end PSD -> Spine 4.2 project conversion.

Pure function (no MCP/IO framework coupling) so it's directly testable. The MCP
tool in `server.py` is a thin wrapper over this.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .atlas.writer import compose_pages, write_atlas_text
from .psd.parser import parse_psd
from .spine.builder import build
from .spine.writer import write_json


@dataclass
class ImportResult:
    project_path: Path
    atlas_path: Path
    png_paths: list[Path]


def import_psd_to_spine(psd_path: str, out_dir: str) -> ImportResult:
    psd_path = str(psd_path)
    stem = Path(psd_path).stem
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    parsed = parse_psd(psd_path)
    result = build(parsed)

    project_path = write_json(result.project, out / f"{stem}.json")
    atlas_path = write_atlas_text(result.atlas, stem, out / f"{stem}.atlas")
    images = {name: layer.image for name, layer in result.images.items()}
    png_paths = compose_pages(result.atlas, images, stem, out)

    return ImportResult(
        project_path=project_path,
        atlas_path=atlas_path,
        png_paths=png_paths,
    )
