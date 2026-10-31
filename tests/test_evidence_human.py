from __future__ import annotations

import copy
import json

from research_audit_kit.cli import main
from research_audit_kit.evidence import run
from research_audit_kit.evidence.human import MAX_LINES, display, render_human
from test_evidence_graph_b1 import fixture, save


def test_human_impact_contains_problem_claim_path_and_review(tmp_path):
    path, graph, n = fixture(tmp_path)
    (tmp_path / "artifact.txt").write_bytes(b"changed")
    result = run(path, "impact")
    before = copy.deepcopy(result)
    report = render_human(result)
    for expected in ["Problem file: artifact.txt [IDENTITY_MISMATCH]", "Claim to review:",
                     n["claim"]["statement"], "Declared path (current; NOT_SUPERSEDED):",
                     "SUPPORTS", "Review items:", "confirmed stable-byte mismatch"]:
        assert expected in report
    assert result == before


def test_missing_is_not_presented_as_confirmed_change(tmp_path):
    path, graph, n = fixture(tmp_path)
    (tmp_path / "artifact.txt").unlink()
    report = render_human(run(path, "impact"))
    assert "[MISSING]" in report and "Identity: identity unresolved" in report
    assert "confirmed stable-byte mismatch" not in report


def test_json_default_and_written_report_are_unchanged_by_human_stdout(tmp_path, capsys):
    path, graph, n = fixture(tmp_path)
    expected = run(path, "impact")
    assert main(["evidence", "impact", str(path)]) == 2
    assert json.loads(capsys.readouterr().out) == expected
    assert main(["evidence", "impact", str(path), "--format", "human", "--out", "report.json"]) == 2
    human = capsys.readouterr().out
    assert "ResearchAuditKit evidence impact" in human
    assert json.loads((tmp_path / "report.json").read_text()) == expected


def test_untrusted_terminal_controls_and_bidi_are_escaped(tmp_path):
    path, graph, n = fixture(tmp_path)
    n["claim"]["statement"] = "read me\n\x1b[2J\u202eunsafe"
    save(path, graph)
    (tmp_path / "artifact.txt").unlink()
    report = render_human(run(path, "impact"))
    assert "\x1b" not in report and "\u202e" not in report
    assert r"\u001b" in report and r"\u202e" in report and r"\n" in report
    assert "[truncated; see JSON]" in display("x" * 1000)


def test_text_truncation_is_explicit_and_keeps_result_and_boundary(tmp_path):
    path, graph, n = fixture(tmp_path)
    (tmp_path / "artifact.txt").unlink()
    result = run(path, "impact")
    result["impact_analysis"]["analysis_status"] = "INCOMPLETE"
    result["impact_analysis"]["artifacts"] *= MAX_LINES
    report = render_human(result)
    assert "Result: UNRESOLVED" in report and "Impact analysis: INCOMPLETE" in report
    assert "Text report truncated" in report and "no scientific adjudication" in report
    assert len(report.splitlines()) <= MAX_LINES + 2


def test_structure_only_report_does_not_claim_artifact_verification(tmp_path):
    path, graph, n = fixture(tmp_path)
    text = render_human(run(path, "validate"))
    assert "artifact contents were not read" in text
    assert "observed artifacts: 0" in text
