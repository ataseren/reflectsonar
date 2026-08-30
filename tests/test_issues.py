"""Tests for issue categorization and severity rendering."""

from reflectsonar.data.models import SonarQubeIssue
from reflectsonar.report.issues import get_issue_display_severity


def make_issue(impacts):
    return SonarQubeIssue(
        key="issue",
        component="project:src/app.py",
        project="project",
        rule="python:S1",
        severity="MAJOR",
        status="OPEN",
        message="Message",
        type="CODE_SMELL",
        impacts=impacts,
    )


def test_mqr_severity_matches_the_rendered_category():
    issue = make_issue(
        [
            {"softwareQuality": "RELIABILITY", "severity": "HIGH"},
            {"softwareQuality": "SECURITY", "severity": "LOW"},
        ]
    )

    assert get_issue_display_severity(issue, "MQR", "SECURITY") == "LOW"
    assert get_issue_display_severity(issue, "MQR", "RELIABILITY") == "HIGH"


def test_mqr_uses_highest_matching_severity():
    issue = make_issue(
        [
            {"softwareQuality": "SECURITY", "severity": "MEDIUM"},
            {"softwareQuality": "SECURITY", "severity": "BLOCKER"},
        ]
    )

    assert get_issue_display_severity(issue, "MQR", "SECURITY") == "BLOCKER"
