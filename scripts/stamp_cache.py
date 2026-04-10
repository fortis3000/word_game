"""Stamp cache-busting hashes into index.html.

Reads static CSS/JS files, computes a short MD5 hash of each,
and replaces __CSS_HASH__ / __JS_HASH__ placeholders in index.html.

Run this as part of the Docker build or CI pipeline:
    uv run python scripts/stamp_cache.py
"""

import hashlib
from pathlib import Path

STATIC_DIR = Path("src/game/static")
INDEX_FILE = STATIC_DIR / "index.html"

FILES_TO_HASH = {
    "__CSS_HASH__": STATIC_DIR / "css" / "style.css",
    "__JS_HASH__": STATIC_DIR / "js" / "app.js",
    "__TRANSLATIONS_HASH__": STATIC_DIR / "js" / "translations.js",
}


def file_hash(path: Path) -> str:
    """Return first 8 chars of the MD5 hex digest of a file."""
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def main():
    html = INDEX_FILE.read_text()

    for placeholder, asset_path in FILES_TO_HASH.items():
        if not asset_path.exists():
            print(f"WARNING: {asset_path} not found, skipping {placeholder}")
            continue

        h = file_hash(asset_path)
        html = html.replace(placeholder, h)
        print(f"{placeholder} -> {h}  ({asset_path})")

    INDEX_FILE.write_text(html)
    print(f"✓ Stamped {INDEX_FILE}")


if __name__ == "__main__":
    main()
