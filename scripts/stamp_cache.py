import hashlib
from pathlib import Path

# Paths relative to this script
ROOT_DIR = Path(__file__).parent.parent
STATIC_DIR = ROOT_DIR / "src" / "game" / "static"
INDEX_FILE = STATIC_DIR / "index.html"

FILES_TO_HASH = {
    "__CSS_HASH__": STATIC_DIR / "css" / "style.css",
    "__JS_HASH__": STATIC_DIR / "js" / "app.js",
    "__TRANSLATIONS_HASH__": STATIC_DIR / "js" / "translations.js",
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

    for placeholder, asset_path in FILES_TO_HASH.items():
        if placeholder not in html:
            continue

        h = file_hash(asset_path)
        html = html.replace(placeholder, h)
        print(f"{placeholder} -> {h}  ({asset_path})")
        any_changed = True

    if any_changed:
        INDEX_FILE.write_text(html)
        print(f"✓ Stamped {INDEX_FILE}")
    else:
        print(f"ℹ No placeholders found in {INDEX_FILE}")


if __name__ == "__main__":
    main()
