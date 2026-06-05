# tests/test_gate_merge.py
import importlib.util
from pathlib import Path
TOOLS = Path(__file__).resolve().parent.parent / "tools"

def _load():
    spec = importlib.util.spec_from_file_location("check_resume", TOOLS / "check-resume.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_merge_adds_profile_required():
    cr = _load()
    base = {"required": ["EDUCATION"], "banned": [], "max_occurrences": {}}
    profile = {"gate_overrides": {"required": ["AWACS"], "banned": ["#37550"], "max_occurrences": {"11k": 1}}}
    merged = cr.merge_overrides(base, profile)
    assert "EDUCATION" in merged["required"] and "AWACS" in merged["required"]
    assert "#37550" in merged["banned"]
    assert merged["max_occurrences"]["11k"] == 1

def test_merge_handles_missing_overrides():
    cr = _load()
    base = {"required": ["EDUCATION"], "banned": [], "max_occurrences": {}}
    merged = cr.merge_overrides(base, {})
    assert merged["required"] == ["EDUCATION"]
