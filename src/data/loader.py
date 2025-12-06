import yaml
from pathlib import Path
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str | Path = "configs/config.yaml") -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def load_words(filepath: str | Path) -> Dict[int, str]:
    """Load words from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        Dictionary of {id: word}
    """
    path = Path(filepath)
    if not path.exists():
        logger.error(f"Word file not found: {path}")
        raise FileNotFoundError(f"Word file not found: {path}")

    logger.info(f"Loading words from {path}")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    words = {}
    for i, line in enumerate(lines[1:]):  # Skip header
        parts = line.split(",")
        if len(parts) >= 2:
            words[i] = parts[1]

    logger.info(f"Loaded {len(words)} words.")
    return words
