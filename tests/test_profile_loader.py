# tests/test_profile_loader.py
import importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"

def _load():
    spec = importlib.util.spec_from_file_location("profile_loader", TOOLS / "profile_loader.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_loads_named_profile(tmp_path):
    pl = _load()
    p = tmp_path / "profile.yaml"
    p.write_text("identity:\n  name: Jane Developer\n", encoding="utf-8")
    prof = pl.load_profile(p)
    assert prof["identity"]["name"] == "Jane Developer"

def test_missing_profile_raises(tmp_path):
    pl = _load()
    import pytest
    with pytest.raises(FileNotFoundError):
        pl.load_profile(tmp_path / "nope.yaml")
