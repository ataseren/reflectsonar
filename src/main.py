from data.models import ReportData, SonarQubeProject, SonarQubeIssue, SonarQubeMeasure, SonarQubeHotspot
from report.pdfgen import generate_pdf
from datetime import datetime

# --- Dummy data to simulate input ---
project = SonarQubeProject(
    key="/opt/projects/blackdagger",
    name="Blackdagger",
    qualifier="TRK",
    visibility="public",
    last_analysis_date=datetime.now(),
    revision="abc123"
)

issues = [
    SonarQubeIssue(
        key="ISSUE-1",
        component="com.example.ClassA",
        project="Blackdagger",
        rule="java:S123",
        severity="CRITICAL",
        status="OPEN",
        message="Null pointer dereference",
        type="BUG"
    ),
    SonarQubeIssue(
        key="ISSUE-2",
        component="com.example.ClassB",
        project="Blackdagger",
        rule="java:S456",
        severity="MAJOR",
        status="OPEN",
        message="Code smell",
        type="CODE_SMELL"
    ),
    SonarQubeIssue(
        key="ISSUE-3",
        component="com.example.ClassC",
        project="Blackdagger",
        rule="java:S789",
        severity="MINOR",
        status="OPEN",
        message="Optimization suggestion",
        type="CODE_SMELL"
    )
]

measures = {
    "coverage": SonarQubeMeasure(metric="coverage", value="85.3"),
    "lines_to_cover": SonarQubeMeasure(metric="lines_to_cover", value="12345"),
    "duplicated_lines_density": SonarQubeMeasure(metric="duplicated_lines_density", value="12.5"),
    "ncloc": SonarQubeMeasure(metric="ncloc", value="23456")
}

hotspots = [
    SonarQubeHotspot(
        key="HOT-1",
        component="com.example.ClassX",
        project="Blackdagger",
        rule="java:H001",
        status="TO_REVIEW",
        message="Sensitive function detected"
    )
]

quality_gate = {}
quality_profiles = []

report_data = ReportData(
    project=project,
    issues=issues,
    measures=measures,
    hotspots=hotspots,
    quality_gate=quality_gate,
    quality_profiles=quality_profiles
)

generate_pdf(report_data)
