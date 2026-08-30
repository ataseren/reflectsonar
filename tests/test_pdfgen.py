"""End-to-end smoke test for the current PDF generator."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from pypdf import PdfReader

from reflectsonar.data.models import (
    ReportData,
    SonarQubeHotspot,
    SonarQubeIssue,
    SonarQubeMeasure,
    SonarQubeProject,
    SonarQubeRule,
)
from reflectsonar.report.pdfgen import generate_pdf


def build_report():
    issues = [
        SonarQubeIssue(
            key="security",
            component="demo:src/security.py",
            project="demo",
            rule="python:S1",
            severity="CRITICAL",
            status="OPEN",
            message="Security message",
            type="VULNERABILITY",
            line=8,
            impacts=[{"softwareQuality": "SECURITY", "severity": "HIGH"}],
            code_snippet='>>>   8: token = "example"',
        ),
        SonarQubeIssue(
            key="reliability",
            component="demo:src/service.py",
            project="demo",
            rule="python:S2",
            severity="MAJOR",
            status="OPEN",
            message="Reliability message",
            type="BUG",
            line=4,
            impacts=[{"softwareQuality": "RELIABILITY", "severity": "MEDIUM"}],
        ),
        SonarQubeIssue(
            key="maintainability",
            component="demo:src/model.py",
            project="demo",
            rule="python:S3",
            severity="MINOR",
            status="OPEN",
            message="Maintainability message",
            type="CODE_SMELL",
            line=12,
            impacts=[{"softwareQuality": "MAINTAINABILITY", "severity": "LOW"}],
        ),
    ]
    hotspots = [
        SonarQubeHotspot(
            key="hotspot",
            component="demo:src/auth.py",
            project="demo",
            rule="python:S4",
            rule_key="python:S4",
            status="TO_REVIEW",
            message="Review secret handling",
            line=10,
            vulnerability_probability="HIGH",
            security_category="auth",
            code_snippet='>>>  10: token = "example"',
        )
    ]
    values = {
        "software_quality_security_rating": "2",
        "software_quality_reliability_rating": "3",
        "software_quality_maintainability_rating": "1",
        "coverage": "82.5",
        "lines_to_cover": "100",
        "duplicated_lines_density": "1.2",
        "lines": "250",
        "accepted_issues": "4",
    }
    measures = {key: SonarQubeMeasure(key, value) for key, value in values.items()}
    rules = {
        "python:S1": SonarQubeRule(
            "python:S1",
            "Synthetic rule",
            [{"key": "root_cause", "content": "Use <strong>safe</strong> input."}],
        )
    }
    return ReportData(
        project=SonarQubeProject("demo", "Demo Project", "TRK", "private"),
        issues=issues,
        measures=measures,
        hotspots=hotspots,
        quality_gate={},
        quality_profiles=[],
        mode_setting=True,
        rules=rules,
    )


def find_text_y(page, target):
    positions = []

    def visit(text, cm, tm, _font_dict, _font_size):
        if target in text:
            absolute_y = (tm[4] * cm[1]) + (tm[5] * cm[3]) + cm[5]
            positions.append(absolute_y)

    page.extract_text(visitor_text=visit)
    return positions


def test_generate_pdf_has_complete_sections_metadata_and_layout(tmp_path):
    output = tmp_path / "smoke.pdf"

    generate_pdf(build_report(), str(output), "demo")

    assert output.read_bytes().startswith(b"%PDF-")
    reader = PdfReader(output)
    assert len(reader.pages) == 6
    assert reader.metadata.title == "ReflectSonar Report - Demo Project"

    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    for heading in (
        "Security Issues",
        "Reliability Issues",
        "Maintainability Issues",
        "Security Hotspots",
        "Rules Reference",
        "Accepted Issues",
        "4",
    ):
        assert heading in text

    for page, heading in zip(
        reader.pages[1:],
        (
            "Security Issues",
            "Reliability Issues",
            "Maintainability Issues",
            "Security Hotspots",
            "Rules Reference",
        ),
    ):
        y_positions = find_text_y(page, heading)
        assert y_positions, f"Missing heading position for {heading}"
        assert max(y_positions) <= A4[1] - 2.5 * cm
        assert max(y_positions) >= A4[1] - 5.5 * cm
        xobjects = page.get("/Resources", {}).get("/XObject", {})
        assert xobjects, f"Missing logo image on page containing {heading}"


def test_generate_pdf_splits_oversized_issue_and_hotspot_snippets(tmp_path):
    output = tmp_path / "long-snippets.pdf"
    report = build_report()
    long_snippet = (
        ">>>   1: " + ("<p style=color:red>content</p>" * 300) + "\n      2: END_OF_LONG_SNIPPET"
    )
    report.issues[0].code_snippet = long_snippet
    report.hotspots[0].code_snippet = long_snippet

    generate_pdf(report, str(output), "long-snippets")

    reader = PdfReader(output)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert len(reader.pages) > 6
    assert text.count("END_OF_LONG_SNIPPET") == 2
    assert "Problematic Code (continued):" in text
    assert "Security Hotspot Code (continued):" in text
