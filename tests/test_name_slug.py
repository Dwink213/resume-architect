# tests/test_name_slug.py
import importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _load():
    spec = importlib.util.spec_from_file_location("profile_loader", TOOLS / "profile_loader.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_slug_dustin():
    pl = _load()
    assert pl._name_slug({"identity": {"name": "Dustin Winkler"}}) == "dustin-winkler"


def test_slug_jane():
    pl = _load()
    assert pl._name_slug({"identity": {"name": "Jane Developer"}}) == "jane-developer"


def test_slug_empty_name_falls_back():
    pl = _load()
    assert pl._name_slug({"identity": {"name": ""}}) == "candidate"


def test_slug_missing_identity_falls_back():
    pl = _load()
    assert pl._name_slug({}) == "candidate"


def test_slug_none_profile_falls_back():
    pl = _load()
    assert pl._name_slug(None) == "candidate"


def test_slug_collapses_and_strips_punctuation():
    pl = _load()
    # extra whitespace + punctuation collapse to single hyphens
    assert pl._name_slug({"identity": {"name": "  Mary  Jane  O'Brien  "}}) == "mary-jane-obrien"
