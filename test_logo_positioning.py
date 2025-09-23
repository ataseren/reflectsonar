#!/usr/bin/env python3
"""
Test script to verify the logo positioning in the PDF report
"""

from src.data.models import ReportData, SonarQubeProject, SonarQubeIssue, SonarQubeMeasure
from src.report.pdfgen import generate_pdf
from datetime import datetime

def create_test_report():
    """Create a minimal test report to verify logo positioning"""
    
    # Create test project
    project = SonarQubeProject(
        key="test-project",
        name="Test Project for Logo Positioning", 
        qualifier="TRK",
        visibility="public"
    )
    
    # Create some test issues
    test_issues = [
        SonarQubeIssue(
            key="TEST-1",
            component="test:src/main.py",
            project="test-project",
            rule="python:S1234",
            severity="MAJOR",
            status="OPEN",
            message="Test maintainability issue",
            type="CODE_SMELL",
            impacts=[{"softwareQuality": "MAINTAINABILITY", "severity": "MEDIUM"}]
        ),
        SonarQubeIssue(
            key="TEST-2", 
            component="test:src/security.py",
            project="test-project",
            rule="python:S5542",
            severity="HIGH",
            status="OPEN", 
            message="Test security vulnerability",
            type="VULNERABILITY",
            impacts=[{"softwareQuality": "SECURITY", "severity": "HIGH"}]
        )
    ]
    
    # Create test measures
    measures = {
        "coverage": SonarQubeMeasure(metric="coverage", value=85.5),
        "duplicated_lines_density": SonarQubeMeasure(metric="duplicated_lines_density", value=3.2),
        "lines": SonarQubeMeasure(metric="lines", value=1500),
        "lines_to_cover": SonarQubeMeasure(metric="lines_to_cover", value=1200),
        "software_quality_security_rating": SonarQubeMeasure(metric="software_quality_security_rating", value=2.0),
        "software_quality_reliability_rating": SonarQubeMeasure(metric="software_quality_reliability_rating", value=1.0), 
        "software_quality_maintainability_rating": SonarQubeMeasure(metric="software_quality_maintainability_rating", value=3.0),
        "software_quality_security_issues": SonarQubeMeasure(metric="software_quality_security_issues", value=1),
        "software_quality_reliability_issues": SonarQubeMeasure(metric="software_quality_reliability_issues", value=0),
        "software_quality_maintainability_issues": SonarQubeMeasure(metric="software_quality_maintainability_issues", value=1),
    }
    
    return ReportData(
        project=project,
        issues=test_issues,
        measures=measures,
        hotspots=[],
        quality_gate={},
        quality_profiles=[]
    )

def test_logo_positioning():
    """Test the logo positioning by generating a sample PDF"""
    print("Creating test report with enhanced logo positioning...")
    
    test_report = create_test_report()
    output_file = "test_logo_report.pdf"
    
    try:
        generate_pdf(test_report, output_file)
        print(f"✅ Test PDF generated successfully: {output_file}")
        print("📋 Check the PDF to verify:")
        print("   ✓ First page: LARGE logo (5cm x 5cm) in top left")
        print("   ✓ Other pages: BIGGER logo (4cm x 4cm) positioned VERY HIGH")
        print("   ✓ Black background removed/transparent handling")
        print("   ✓ Title remains centered and unaffected")
        print("   ✓ SonarQube mode line REMOVED from display")
        print("   ✓ Page numbers appear in bottom right")
        print("   ✓ Content layout preserved")
        print()
        print("🔧 Logo transparency methods attempted:")
        print("   1. mask='auto' - Automatic transparency detection")
        print("   2. mask=[0,0,0] - Make black pixels transparent")
        print("   3. Normal drawing - Fallback if transparency fails")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        print("💡 Make sure you have:")
        print("   - reflect-sonar.png file in the project root")
        print("   - reportlab library installed")
        print("   - PNG file ideally with transparent background")
        print()
        print("🆘 If black background persists:")
        print("   - Convert PNG to have transparent background")
        print("   - Use image editing software to remove black background")
        print("   - Save as PNG with alpha channel")

if __name__ == "__main__":
    test_logo_positioning()