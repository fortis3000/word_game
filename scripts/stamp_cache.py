import hashlib
import re
from pathlib import Path

from typing import TypedDict

# Paths relative to this script
ROOT_DIR = Path(__file__).parent.parent
STATIC_DIR = ROOT_DIR / "src" / "game" / "static"
INDEX_FILE = STATIC_DIR / "index.html"


class AssetInfo(TypedDict):
    path: Path
    pattern: str


# Mapping of asset filename to its path and placeholder/regex pattern
ASSETS: dict[str, AssetInfo] = {
    "style.css": {
        "path": STATIC_DIR / "css" / "style.css",
        "pattern": r"style\.css\?h=([a-f0-9]+|__CSS_HASH__)",
    },
    "app.js": {
        "path": STATIC_DIR / "js" / "app.js",
        "pattern": r"app\.js\?h=([a-f0-9]+|__JS_HASH__)",
    },
    "translations.js": {
        "path": STATIC_DIR / "js" / "translations.js",
        "pattern": r"translations\.js\?h=([a-f0-9]+|__TRANSLATIONS_HASH__)",
    },
}


def file_hash(path: Path) -> str:
    """Return first 8 chars of the MD5 hex digest of a file."""
    if not path.exists():
        return "notfound"
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def main():
    if not INDEX_FILE.exists():
        print(f"ERROR: {INDEX_FILE} not found")
        return

    html = INDEX_FILE.read_text()
    any_changed = False

    for filename, info in ASSETS.items():
        asset_path = info["path"]
        pattern = info["pattern"]

        h = file_hash(asset_path)
        new_val = f"{filename}?h={h}"

        # Replace the entire match (e.g., style.css?h=123) with the new one
        new_html, count = re.subn(pattern, new_val, html)

        if count > 0:
            html = new_html
            print(f"✓ Updated {filename} -> {h} ({count} occurrences)")
            any_changed = True
        else:
            print(f"⚠ Could not find pattern for {filename} in index.html")

    if any_changed:
        INDEX_FILE.write_text(html)
        print(f"✓ Successfully updated {INDEX_FILE}")
    else:
        print(f"ℹ No changes needed for {INDEX_FILE}")


if __name__ == "__main__":
    main()
