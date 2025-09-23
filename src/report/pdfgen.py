from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Flowable, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

from reportlab.graphics.shapes import Drawing, Circle, String


from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from data.models import ReportData
import os

styles = getSampleStyleSheet()
style_normal = styles["Normal"]
style_title = ParagraphStyle("Title", parent=styles["Heading1"], alignment=2, fontSize=20)
style_subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], alignment=2, fontSize=10, italic=True)
style_meta = ParagraphStyle("Meta", parent=style_normal, spaceAfter=6)
style_footer = ParagraphStyle("Footer", parent=style_normal, alignment=0, fontSize=10)
style_section_title = ParagraphStyle("SectionTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=12, spaceBefore=12)
style_issue_title = ParagraphStyle("IssueTitle", parent=styles["Heading2"], fontSize=12, spaceAfter=6)
style_issue_meta = ParagraphStyle("IssueMeta", parent=style_normal, fontSize=9, textColor=colors.gray)




class CircleBadge(Flowable):
    def __init__(self, letter, radius=12, color=HexColor("#D50000")):
        super().__init__()
        self.letter = letter
        self.radius = radius
        self.color = color
        self.width = self.height = 2 * radius

    def draw(self):
        d = Drawing(self.width, self.height)
        d.add(Circle(self.radius, self.radius, self.radius, fillColor=self.color, strokeColor=self.color))
        d.add(String(self.radius, self.radius - 4, self.letter,fontName="Helvetica",
                     fontSize=self.radius, textAnchor="middle"))
        d.drawOn(self.canv, 0, 0)



def badge(letter):
    color_map = {
        "A": HexColor("#D1FADF"),
        "B": HexColor("#E1F4A9"),
        "C": HexColor("#FCE8A2"),
        "D": HexColor("#FFD6AF"),
        "E": HexColor("#FECCCB"),
    }
    return CircleBadge(letter, radius=12, color=color_map.get(letter, HexColor("#9E9E9E")))

def score_to_grade(score: float) -> str:
    if score <= 1.0:
        return "A"
    elif score <= 2.0:
        return "B"
    elif score <= 3.0:
        return "C"
    elif score <= 4.0:
        return "D"
    else:
        return "E"

def get_severity_order(severity: str, mode: str = "STANDARD") -> int:
    """Return numeric order for severity sorting (lower number = higher priority)"""
    if mode == "MQR":
        severity_map = {
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3
        }
    else:  # STANDARD mode
        severity_map = {
            "BLOCKER": 1,
            "CRITICAL": 2,
            "MAJOR": 3,
            "MINOR": 4,
            "INFO": 5
        }
    return severity_map.get(severity.upper(), 99)


def get_severity_color(severity: str, mode: str = "STANDARD") -> HexColor:
    """Return color for severity badge"""
    if mode == "MQR":
        color_map = {
            "BLOCKER": HexColor("#6B0101"),
            "HIGH": HexColor("#EB0A0A"),
            "MEDIUM": HexColor("#FF6600"),
            "LOW": HexColor("#FFD001"),
            "INFO": HexColor("#4CA3EB")
        }
    else:  # STANDARD mode
        color_map = {
            "BLOCKER": HexColor("#D50000"),
            "CRITICAL": HexColor("#FF5722"),
            "MAJOR": HexColor("#FF9800"),
            "MINOR": HexColor("#FFC107"),
            "INFO": HexColor("#2196F3")
        }
    return color_map.get(severity.upper(), HexColor("#9E9E9E"))


def detect_sonarqube_mode(issues):
    """Detect if SonarQube instance is using Standard or MQR mode based on issue data"""
    # Check if any issues have impacts field (MQR mode indicator)
    has_impacts = any(issue.impacts for issue in issues)
    
    # Check severity types used
    severities = set()
    for issue in issues:
        severities.add(issue.severity.upper())
        # Also check impact severities if available
        if issue.impacts:
            for impact in issue.impacts:
                if 'severity' in impact:
                    severities.add(impact['severity'].upper())
    
    # MQR mode uses HIGH, MEDIUM, LOW
    mqr_severities = {'HIGH', 'MEDIUM', 'LOW'}
    # Standard mode uses BLOCKER, CRITICAL, MAJOR, MINOR, INFO
    standard_severities = {'BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO'}
    
    # If we have impacts and MQR severities, it's MQR mode
    if has_impacts and mqr_severities.intersection(severities):
        return "MQR"
    # If we have standard severities, it's standard mode
    elif standard_severities.intersection(severities):
        return "STANDARD"
    # Default fallback
    else:
        return "STANDARD"


def get_severity_list(mode: str = "STANDARD") -> list:
    """Get ordered list of severities for the given mode"""
    if mode == "MQR":
        return ["HIGH", "MEDIUM", "LOW"]
    else:  # STANDARD mode
        return ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]


def draw_logo_with_transparency(canvas, logo_path, x, y, width, height):
    """Draw logo with enhanced transparency handling"""
    try:
        if os.path.exists(logo_path):
            # Try different approaches for transparency
            try:
                # Method 1: Use mask='auto' for automatic transparency detection
                canvas.drawImage(logo_path, x, y, width=width, height=height, 
                               preserveAspectRatio=True, mask='auto')
            except:
                try:
                    # Method 2: Use mask=[0,0,0] to make black transparent (if black background)
                    canvas.drawImage(logo_path, x, y, width=width, height=height, 
                                   preserveAspectRatio=True, mask=[0,0,0])
                except:
                    # Method 3: Fallback to normal drawing without transparency
                    canvas.drawImage(logo_path, x, y, width=width, height=height, 
                                   preserveAspectRatio=True)
        else:
            # If logo file doesn't exist, draw a placeholder
            canvas.setStrokeColor(colors.lightgrey)
            canvas.setFillColor(colors.lightgrey)
            canvas.rect(x, y, width, height, fill=1, stroke=1)
            canvas.setFillColor(colors.black)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(x + 5, y + height/2, "Logo")
    except Exception as e:
        # Silent fail - don't break the report if logo fails
        pass


def severity_badge(severity: str, mode: str = "STANDARD"):
    """Create a colored badge for issue severity"""
    return CircleBadge(severity[0].upper(), radius=8, color=get_severity_color(severity, mode))


def filter_issues_by_type(issues, issue_type: str):
    """Filter issues by software quality impact type"""
    return [issue for issue in issues if issue.type.upper() == issue_type.upper()]



def get_issues_by_impact_category(issues, category: str, mode: str = "MQR"):
    """Get issues by software quality impact category (SECURITY, RELIABILITY, MAINTAINABILITY)"""
    filtered_issues = []
    
    for issue in issues:
        # For MQR mode, always use impacts field
        if mode == "MQR" and issue.impacts:
            # Look for the category in the impacts
            for impact in issue.impacts:
                if impact.get('softwareQuality', '').upper() == category.upper():
                    filtered_issues.append(issue)
                    break
        # For Standard mode or fallback
        elif issue.impacts:
            # Look for the category in the impacts (modern SonarQube)
            for impact in issue.impacts:
                if impact.get('softwareQuality', '').upper() == category.upper():
                    filtered_issues.append(issue)
                    break
        else:
            # Fallback to legacy categorization for older SonarQube versions
            if category.upper() == "SECURITY":
                if (issue.type.upper() == "VULNERABILITY" or 
                    issue.type.upper() == "SECURITY_HOTSPOT" or
                    any(tag.lower() in ['security', 'cwe', 'owasp'] for tag in issue.tags)):
                    filtered_issues.append(issue)
            elif category.upper() == "RELIABILITY": 
                if issue.type.upper() == "BUG":
                    filtered_issues.append(issue)
            elif category.upper() == "MAINTAINABILITY":
                if issue.type.upper() == "CODE_SMELL":
                    filtered_issues.append(issue)
    
    return filtered_issues


def create_issue_section(title: str, issues, elements, mode: str = "STANDARD"):
    """Create a complete issue section with title, summary, and table"""
    elements.append(Paragraph(title, style_section_title))
    
    # Add issue count summary
    if issues:
        severity_counts = {}
        
        # Count severities differently based on mode
        for issue in issues:
            if mode == "MQR" and issue.impacts:
                # For MQR mode, use impact severity
                for impact in issue.impacts:
                    impact_severity = impact.get('severity', '').upper()
                    if impact_severity:
                        severity_counts[impact_severity] = severity_counts.get(impact_severity, 0) + 1
                        break  # Use first impact severity
            else:
                # For Standard mode, use issue severity
                severity = issue.severity.upper()
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary_parts = []
        severity_list = get_severity_list(mode)
        
        for severity in severity_list:
            count = severity_counts.get(severity, 0)
            if count > 0:
                summary_parts.append(f"{severity.title()}: {count}")
        
        if summary_parts:
            summary_text = f"<b>Total: {len(issues)} issues</b> ({', '.join(summary_parts)})"
            elements.append(Paragraph(summary_text, style_issue_meta))
    else:
        elements.append(Paragraph("<b>Total: 0 issues</b>", style_issue_meta))
    
    elements.append(Spacer(1, 0.3*cm))
    elements.append(create_issue_table(issues, mode))
    elements.append(Spacer(1, 1*cm))


def create_issue_table(issues, mode: str = "STANDARD"):
    """Create a table displaying issues with severity, rule, and message"""
    if not issues:
        return Paragraph(
            "<i>No issues found in this category. This indicates good code quality in this area.</i>", 
            style_normal
        )
    
    # Sort issues by severity (most severe first)
    def get_issue_severity_for_sorting(issue):
        if mode == "MQR" and issue.impacts:
            # For MQR mode, use impact severity
            for impact in issue.impacts:
                impact_severity = impact.get('severity', '')
                if impact_severity:
                    return get_severity_order(impact_severity, mode)
            return 99  # fallback if no impact severity found
        else:
            # For Standard mode, use issue severity
            return get_severity_order(issue.severity, mode)
    
    sorted_issues = sorted(issues, key=get_issue_severity_for_sorting)
    
    table_data = []
    
    # Add header
    header_style = ParagraphStyle("Header", parent=style_normal, fontName="Helvetica-Bold", fontSize=10)
    table_data.append([
        Paragraph("Severity", header_style),
        Paragraph("File", header_style),
        Paragraph("Rule & Message", header_style)
    ])
    
    for issue in sorted_issues:
        # Extract filename from component path
        filename = issue.component.split('/')[-1] if '/' in issue.component else issue.component
        # Remove project key prefix if present
        if ':' in filename:
            filename = filename.split(':', 1)[1]
        
        if issue.line:
            filename += f" (Line {issue.line})"
        
        # Format rule and message
        rule_name = issue.rule.split(':')[-1] if ':' in issue.rule else issue.rule
        rule_and_message = f"<b>{rule_name}</b><br/>{issue.message}"
        
        # Get the appropriate severity for badge
        display_severity = issue.severity
        if mode == "MQR" and issue.impacts:
            # For MQR mode, use impact severity for display
            for impact in issue.impacts:
                impact_severity = impact.get('severity', '')
                if impact_severity:
                    display_severity = impact_severity
                    break
        
        table_data.append([
            severity_badge(display_severity, mode),
            Paragraph(filename, style_issue_meta),
            Paragraph(rule_and_message, style_normal)
        ])
    
    table = Table(table_data, colWidths=[2*cm, 4*cm, 12*cm])
    table.setStyle(TableStyle([
        # Header styling
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        
        # General table styling
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Severity column centered
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        
        # Grid lines
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        
        # Padding
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        
        # Alternating row colors for better readability
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    return table


def issue_count_by_severity(issues, severity):
    return sum(1 for i in issues if i.severity.upper() == severity.upper())

def get_measure_value(measures, metric, default="0"):
    return float(measures.get(metric).value if metric in measures else default)

def issue_block(title, value, grade):
    content = [
        Paragraph(f"<b>{title}</b>", style_normal),
        Paragraph(f"<font size=14><b>{value}</b></font> Open Issues", style_normal)
    ]
    return Table([[content, badge(grade)]], colWidths=[4*cm, 1*cm], style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

def project_data_block(title, value, grade):
    content = [
        Paragraph(f"<b>{title}</b>", style_normal),
        Paragraph(f"<font size=14><b>{value}</b></font>", style_normal)
    ]
    return Table([[content, badge(grade)]], colWidths=[4*cm, 1*cm], style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

def hotspot_block(title, value):
    content = [
        Paragraph(f"<b>{title}</b>", style_normal),
        Paragraph(f"<font size=14><b>{value}</b></font> Open Issues", style_normal)
    ]
    return Table([[content]], colWidths=[4*cm, 1*cm], style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

def generate_pdf(report: ReportData, output_path="reflect_sonar_report.pdf"):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []

    # Title centered on page (logo will be added via header function)
    title = Paragraph("SonarQube SAST Report", style_title)
    subtitle = Paragraph("generated by Reflect Sonar", style_subtitle)
    
    elements.append(title)
    elements.append(subtitle)
    elements.append(Spacer(1, 1*cm))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"<b>Date:</b> {now}", style_meta))
    elements.append(Paragraph(f"<b>SonarQube Project Name:</b> {report.project.name}", style_meta))
    elements.append(Spacer(1, 1*cm))

    coverage = float(get_measure_value(report.measures, "coverage", 0.0))
    cover_lines = int(get_measure_value(report.measures, "lines_to_cover", 0))
    duplication = float(get_measure_value(report.measures, "duplicated_lines_density", 0.0))
    dup_lines = int(get_measure_value(report.measures, "lines", 0))
    hotspot_count = len(report.hotspots)

    security_issues_count = int(get_measure_value(report.measures, "software_quality_security_issues", 0))
    reliability_issues_count = int(get_measure_value(report.measures, "software_quality_reliability_issues", 0))
    maintainability_issues_count = int(get_measure_value(report.measures, "software_quality_maintainability_issues", 0))

    security_rating = score_to_grade(get_measure_value(report.measures, "software_quality_security_rating", 5.0))
    reliability_rating = score_to_grade(get_measure_value(report.measures, "software_quality_reliability_rating", 5.0))
    maintainability_rating = score_to_grade(get_measure_value(report.measures, "software_quality_maintainability_rating", 5.0))


    dashboard_data = [
        [  # Row 1
            issue_block("Security", str(security_issues_count), security_rating),
            issue_block("Reliability", str(reliability_issues_count),  reliability_rating),
            issue_block("Maintainability", str(maintainability_issues_count), maintainability_rating)
        ],
        [  # Row 2
            project_data_block("Accepted Issues", "0<br/><font size=6>Valid issues that were not fixed</font>", "C"),
            project_data_block("Coverage", f"{coverage}%<br/><font size=8>on {cover_lines} lines to cover</font>", "B"),
            project_data_block("Duplications", f"{duplication}%<br/><font size=8>on {dup_lines} lines</font>", "D")
        ],
        [  # Row 3
            hotspot_block("Security Hotspots", f"<font size=14><b>{hotspot_count}</b></font>"),
            Spacer(0, 0), Spacer(0, 0)
        ]
    ]

    flattened_dashboard = [[cell for cell in row] for row in dashboard_data]
    t = Table(flattened_dashboard, colWidths=[6*cm]*3)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("SPAN", (0, 2), (2, 2)),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 2*cm))

    note = (
        "<i>This report is generated by ReflectSonar, an open-source tool to add the report generation mechanism to SonarQube Community and Developer Edition. </i>"
        "<i>It is not affiliated with SonarSource. </i>"
        "<i>The report is generated based on SonarQube instance that its information is provided. All data is fetched from SonarQube API. </i>"
        "<i>ReflectSonar just provides a way to generate the report. </i>"
    )
    elements.append(Paragraph(note, style_footer))

    # Add page break before issues section
    elements.append(PageBreak())

    # Detect SonarQube mode (Standard vs MQR)
    sonarqube_mode = detect_sonarqube_mode(report.issues)

    # Security Issues Section
    security_issues = get_issues_by_impact_category(report.issues, "SECURITY", sonarqube_mode)
    create_issue_section("Security Issues", security_issues, elements, sonarqube_mode)

    # Reliability Issues Section  
    reliability_issues = get_issues_by_impact_category(report.issues, "RELIABILITY", sonarqube_mode)
    create_issue_section("Reliability Issues", reliability_issues, elements, sonarqube_mode)

    # Maintainability Issues Section
    maintainability_issues = get_issues_by_impact_category(report.issues, "MAINTAINABILITY", sonarqube_mode)
    create_issue_section("Maintainability Issues", maintainability_issues, elements, sonarqube_mode)

    def first_page_header_footer(canvas, doc):
        # Draw larger logo on first page in top left corner
        logo_path = "reflect-sonar.png"
        # Bigger logo for first page: 5cm x 5cm, positioned lower for better visibility
        draw_logo_with_transparency(canvas, logo_path, 1.5*cm, A4[1] - 6*cm, 5*cm, 5*cm)
        
        # Draw page number in bottom right
        page_num = f"{doc.page}"
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(A4[0] - 2*cm, 1.5*cm, f"{page_num}")

    def other_pages_header_footer(canvas, doc):
        # Draw bigger logo on other pages, positioned much higher (closer to top)
        logo_path = "reflect-sonar.png"
        # Bigger logo for other pages: 4cm x 4cm, positioned very high (1.5cm from top)
        draw_logo_with_transparency(canvas, logo_path, 1*cm, A4[1] - 3.8*cm, 4*cm, 4*cm)
        
        # Draw page number in bottom right
        page_num = f"{doc.page}"
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(A4[0] - 2*cm, 1.5*cm, f"{page_num}")

    doc.build(elements, onFirstPage=first_page_header_footer, onLaterPages=other_pages_header_footer)
