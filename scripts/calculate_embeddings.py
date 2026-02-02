import argparse
import os
import pickle
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer

# Add project root to sys.path to allow imports from src
sys.path.append(os.getcwd())

from src.data.loader import load_words
from src.utils.logger import get_logger

logger = get_logger(__name__)

EMBEDDING_DIM = 768

def load_model(model_name: str | None = None) -> SentenceTransformer:
    """Load the SentenceTransformer model."""
    if model_name is None:
        model_name = "google/embeddinggemma-300M"

    model_path = os.getenv("MODEL_PATH", model_name)
    logger.info(f"Loading model from: {model_path}")

    try:
        # Try loading with local_files_only=True first (like in API)
        # If it fails, try downloading (assuming we might be in an env where we want to cache it)
        try:
             model = SentenceTransformer(
                model_path,
                device="cpu",
                truncate_dim=EMBEDDING_DIM,
                backend="torch",
                local_files_only=True,
                model_kwargs={
                    "dtype": "float32",
                },
            )
        except Exception:
            logger.info(f"Model not found locally at {model_path}. Attempting to download...")
            model = SentenceTransformer(
                model_path,
                device="cpu",
                truncate_dim=EMBEDDING_DIM,
                backend="torch",
                local_files_only=False,
                model_kwargs={
                    "dtype": "float32",
                },
            )

        logger.info(f"Model '{model_name}' loaded successfully.")
        return model
    except Exception as e:
        logger.exception(f"Error loading model from {model_path}")
        raise RuntimeError(f"Failed to load model: {str(e)}")

def process_file(filepath: Path, model: SentenceTransformer, input_root: Path, output_root: Path):
    """Process a single dictionary file."""
    try:
        words_dict = load_words(filepath)
    except Exception as e:
        logger.error(f"Failed to load words from {filepath}: {e}")
        return

    words = list(words_dict.values())

    if not words:
        logger.warning(f"No words found in {filepath}. Skipping.")
        return

    logger.info(f"Computing embeddings for {len(words)} words in {filepath}...")
    try:
        embeddings = model.encode(words, convert_to_numpy=True, normalize_embeddings=True)
    except Exception as e:
        logger.error(f"Failed to compute embeddings for {filepath}: {e}")
        return

    # Create result dict {word: embedding}
    result = {word: emb for word, emb in zip(words, embeddings)}

    # Determine output path
    # Calculate relative path from input_root
    try:
        rel_path = filepath.relative_to(input_root)
    except ValueError:
        # If filepath is not relative to input_root (e.g. if absolute paths mixed), fallback
        rel_path = filepath.name

    output_path = output_root / rel_path.with_suffix('.pkl')

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving embeddings to {output_path}")
    try:
        with open(output_path, "wb") as f:
            pickle.dump(result, f)
    except Exception as e:
        logger.error(f"Failed to save embeddings to {output_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Calculate embeddings for dictionary files.")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="data/dicts",
        help="Directory containing input CSV dictionaries."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/processed/embeddings",
        help="Directory to save output pickle files."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="google/embeddinggemma-300M",
        help="Name or path of the model to use."
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist.")
        return

    # Load model
    model = load_model(args.model)

    # Find all CSV files
    files = list(input_dir.rglob("*.csv"))
    if not files:
        logger.warning(f"No CSV files found in {input_dir}")
        return

    logger.info(f"Found {len(files)} dictionary files to process.")

    for filepath in files:
        process_file(filepath, model, input_dir, output_dir)

    logger.info("Processing complete.")

if __name__ == "__main__":
    main()
