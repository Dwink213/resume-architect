"""Single source of truth for loading profile.yaml (identity constants).

Every engine script and gate calls load_profile() so path logic + the
'profile missing' error message live in exactly one place.
"""
import re
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


def _name_slug(profile: dict | None) -> str:
    """Lowercase-hyphenated slug from profile.identity.name (e.g. 'Dustin Winkler'
    -> 'dustin-winkler'). Used to name export files generically. Falls back to
    'candidate' when the name is missing/empty so exports are never anonymous-blank.
    """
    name = ((profile or {}).get("identity") or {}).get("name") or ""
    # Drop apostrophes first so "O'Brien" -> "obrien" (one token), not "o-brien".
    name = name.lower().replace("'", "").replace("’", "")
    slug = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return slug or "candidate"
