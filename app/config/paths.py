from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTERPRISE_REPOS = ROOT / "enterprise-repos"
DATA_DIR = ROOT / "data"
REGISTRY_PATH = DATA_DIR / "registry.json"
