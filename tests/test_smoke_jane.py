# tests/test_smoke_jane.py
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

SAMPLE_JD = """# Applied AI Engineer
We need someone to build production RAG and LLM evaluation systems in Python.
Required: retrieval augmented generation, embeddings, evals, production ai.
"""

def test_jane_resume_builds_without_dustin_data(tmp_path):
    gen = _load_module("generate_resume", "generate-resume.py")
    source = yaml.safe_load((FIXTURES / "jane-resume-source.yaml").read_text(encoding="utf-8"))

    app_folder = tmp_path / "applications" / "2026-06-05_Acme_Applied-AI-Engineer"
    app_folder.mkdir(parents=True)
    (app_folder / "job-posting.md").write_text(SAMPLE_JD, encoding="utf-8")

    role_type = gen.detect_role_type(SAMPLE_JD)
    resume_text, report = gen.build_resume(source, SAMPLE_JD, role_type, app_folder, dry_run=True)

    # Genericization assertions: NO Dustin facts leak from hardcoded logic
    for forbidden in ["AWACS", "Enterprise Health-Tech Co.", "National Cloud Provider", "#44707", "31-hour"]:
        assert forbidden not in resume_text, f"Dustin fact leaked: {forbidden}"
    # Jane's real content is present
    assert "Jane Developer" in resume_text
    assert "RAG" in resume_text
    assert "Acme Data Co" in resume_text
    assert "EDUCATION" in resume_text


def test_jane_resume_passes_lint(tmp_path):
    gen = _load_module("generate_resume", "generate-resume.py")
    chk = _load_module("check_resume", "check-resume.py")
    source = yaml.safe_load((FIXTURES / "jane-resume-source.yaml").read_text(encoding="utf-8"))
    source["_profile"] = yaml.safe_load((ROOT / "profile.example-jane.yaml").read_text(encoding="utf-8"))
    role_type = gen.detect_role_type(SAMPLE_JD)
    resume_text, _ = gen.build_resume(source, SAMPLE_JD, role_type, tmp_path, dry_run=True)
    cfg = yaml.safe_load((TOOLS / "resume-lint.yaml").read_text(encoding="utf-8")) or {}
    cfg = chk.merge_overrides(cfg, source["_profile"])
    violations = chk.lint(resume_text, cfg, [])
    assert violations == [], f"Jane resume failed lint: {violations}"
