"""Bin-pack region images into one or more atlas pages.

PoC scope: no rotation (keeps the writer and Unity import simpler), power-of-two
pages capped at `max_size`. If regions don't fit, more pages are added.
"""

from __future__ import annotations

from dataclasses import dataclass

from rectpack import newPacker


@dataclass
class Region:
    name: str
    width: int
    height: int


@dataclass
class PlacedRegion:
    name: str
    x: int
    y: int
    width: int
    height: int
    page: int


@dataclass
class AtlasLayout:
    pages: list[tuple[int, int]]  # (width, height) per page
    regions: list[PlacedRegion]


def pack(
    regions: list[Region],
    max_size: int = 2048,
    padding: int = 2,
) -> AtlasLayout:
    """Pack regions into pages. `padding` is added around each region to avoid
    edge bleeding when Unity samples sprite borders."""
    if not regions:
        return AtlasLayout(pages=[], regions=[])

    packer = newPacker(rotation=False)
    for r in regions:
        packer.add_rect(r.width + 2 * padding, r.height + 2 * padding, rid=r.name)
    # Offer enough identical bins that everything fits.
    for _ in range(len(regions)):
        packer.add_bin(max_size, max_size)
    packer.pack()

    by_name = {r.name: r for r in regions}
    placed: list[PlacedRegion] = []
    used_pages: dict[int, tuple[int, int]] = {}
    for page_idx, x, y, w, h, rid in packer.rect_list():
        src = by_name[rid]
        placed.append(
            PlacedRegion(
                name=rid,
                x=x + padding,
                y=y + padding,
                width=src.width,
                height=src.height,
                page=page_idx,
            )
        )
        pw, ph = used_pages.get(page_idx, (0, 0))
        used_pages[page_idx] = (
            max(pw, x + w),
            max(ph, y + h),
        )

    if len(placed) != len(regions):
        missing = {r.name for r in regions} - {p.name for p in placed}
        raise ValueError(f"Regions did not fit in atlas: {sorted(missing)}")

    pages = [
        _pow2(used_pages[i][0], used_pages[i][1])
        for i in sorted(used_pages)
    ]
    return AtlasLayout(pages=pages, regions=placed)


def _pow2(w: int, h: int) -> tuple[int, int]:
    def up(n: int) -> int:
        p = 1
        while p < n:
            p <<= 1
        return max(p, 1)

    return up(w), up(h)
