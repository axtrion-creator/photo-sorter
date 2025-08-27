#!/usr/bin/env python3
"""
quick_sort_photos_rename.py — Sorttaa kuvat/videot Year/Month-kansioihin ja
nimeää tiedostot muotoon YYYYMMDD_HHMMSS.ext.

- Kuvat: yrittää EXIF DateTimeOriginal (exifread), muuten käyttää tiedoston mtimea
- Videot: käyttää mtimea
- Oletus kopioi; --move siirtää
- Nimikonfliktit: lisää _1, _2, ...

Riippuvuus (valinnainen mutta suositeltava kuville):
    pip install exifread
"""

import argparse, shutil
from pathlib import Path
from datetime import datetime

try:
    import exifread   # asenna: pip install exifread
except Exception:
    exifread = None

IMG_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".dng", ".nef", ".cr2", ".arw"}
VID_EXT = {".mp4", ".mov", ".3gp", ".m4v"}

def exif_datetime(p: Path):
    """Palauttaa EXIF-ajankohdan jos löytyy, muuten None."""
    if not exifread or p.suffix.lower() not in IMG_EXT:
        return None
    try:
        with open(p, "rb") as f:
            tags = exifread.process_file(f, details=False)
        for k in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
            v = tags.get(k)
            if v:
                try:
                    return datetime.strptime(str(v), "%Y:%m:%d %H:%M:%S")
                except Exception:
                    pass
    except Exception:
        pass
    return None

def file_datetime(p: Path) -> datetime:
    """Varapäiväys: tiedoston muokkausaika."""
    return datetime.fromtimestamp(p.stat().st_mtime)

def y_m_folder(dt: datetime) -> str:
    return f"{dt.year}/{dt.month:02d}"

def next_free(target: Path) -> Path:
    """Palauttaa polun joka ei törmää olemassa olevaan nimeen."""
    if not target.exists():
        return target
    i = 1
    stem, ext = target.stem, target.suffix
    while True:
        c = target.with_name(f"{stem}_{i}{ext}")
        if not c.exists():
            return c
        i += 1

def process(src: Path, dst: Path, move=False, recursive=True, dry=False):
    exts = IMG_EXT | VID_EXT
    files = (src.rglob("*") if recursive else src.glob("*"))
    for p in files:
        if not p.is_file() or p.suffix.lower() not in exts or any(part.startswith(".") for part in p.parts):
            continue
        dt = exif_datetime(p) or file_datetime(p)
        outdir = (dst / y_m_folder(dt))
        outdir.mkdir(parents=True, exist_ok=True)

        newname = f"{dt.strftime('%Y%m%d_%H%M%S')}{p.suffix.lower()}"
        target = next_free(outdir / newname)

        action = "MOVE" if move else "COPY"
        print(f"[{action}] {p} -> {target}")
        if not dry:
            if move:
                shutil.move(str(p), str(target))
            else:
                shutil.copy2(str(p), str(target))

def main():
    ap = argparse.ArgumentParser(description="Sort & rename photos/videos by date into Year/Month folders.")
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--dst", required=True, type=Path)
    ap.add_argument("--move", action="store_true", help="Siirrä (ei jätä kopiota lähteeseen)")
    ap.add_argument("--no-recursive", action="store_true", help="Älä käy alikansioita")
    ap.add_argument("--dry-run", action="store_true", help="Näytä toimet tekemättä muutoksia")
    args = ap.parse_args()
    process(args.src, args.dst, move=args.move, recursive=not args.no_recursive, dry=args.dry_run)

if __name__ == "__main__":
    main()