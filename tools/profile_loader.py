"""Single source of truth for loading profile.yaml (identity constants).

Every engine script and gate calls load_profile() so path logic + the
'profile missing' error message live in exactly one place.
"""
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_PROFILE = REPO_ROOT / "profile.yaml"


def load_profile(path: Path | str = DEFAULT_PROFILE) -> dict:
    """Load and return the profile dict. Raises FileNotFoundError with an
    actionable message if it is missing (tells the user to run /onboard)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"profile.yaml not found at {p}. Run the /onboard wizard to create it, "
            f"or copy profile.example-jane.yaml to profile.yaml to try the engine."
        )
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
