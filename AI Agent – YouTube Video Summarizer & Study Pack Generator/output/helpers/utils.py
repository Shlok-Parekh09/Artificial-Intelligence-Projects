import os
import yaml
import logging

def load_config(path="config.yaml"):
    """Load YAML config file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)

def ensure_dir(path):
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def setup_logging():
    """Configure logging for debugging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)

