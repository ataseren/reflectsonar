"""from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Flowable
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Circle, String
from reportlab.lib.enums import TA_CENTER
import osilities and styles for PDF report generation
"""
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Flowable, PageBreak, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Circle, String
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

class BookmarkFlowable(Flowable):
    """Custom flowable to add bookmarks to PDF"""
    def __init__(self, title, level=0):
        self.title = title
        self.level = level
        self.width = 0
        self.height = 0
    
    def draw(self):
        # Add bookmark at current position using proper PDF outline
        canvas = self.canv
        # Create unique bookmark key for this title
        key = f"bookmark_{id(self)}_{self.title.replace(' ', '_')}"
        
        # First bookmark the current page
        canvas.bookmarkPage(key)
        
        # Then add to PDF outline with proper level and title
        canvas.addOutlineEntry(self.title, key, level=self.level)

# Initialize styles
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
    """Custom flowable for creating circular badges"""
    def __init__(self, letter, radius=12, color=HexColor("#D50000")):
        super().__init__()
        self.letter = letter
        self.radius = radius
        self.color = color
        self.width = self.height = 2 * radius

    def draw(self):
        d = Drawing(self.width, self.height)
        d.add(Circle(self.radius, self.radius, self.radius, fillColor=self.color, strokeColor=self.color))
        d.add(String(self.radius, self.radius - 4, self.letter, fontName="Helvetica",
                     fontSize=self.radius, textAnchor="middle"))
        d.drawOn(self.canv, 0, 0)


def badge(letter):
    """Create a colored grade badge"""
    color_map = {
        "A": HexColor("#D1FADF"),
        "B": HexColor("#E1F4A9"),
        "C": HexColor("#FCE8A2"),
        "D": HexColor("#FFD6AF"),
        "E": HexColor("#FECCCB"),
    }
    return CircleBadge(letter, radius=12, color=color_map.get(letter, HexColor("#9E9E9E")))


def score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade"""
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


def get_measure_value(measures, metric, default="0"):
    """Extract measure value from measures dictionary"""
    return float(measures.get(metric).value if metric in measures else default)


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


def get_severity_order(severity: str, mode: str = "STANDARD") -> int:
    """Return numeric order for severity sorting (lower number = higher priority)"""
    if mode == "MQR":
        severity_map = {
            "BLOCKER": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "INFO": 5
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


def get_severity_list(mode: str = "STANDARD") -> list:
    """Get ordered list of severities for the given mode"""
    if mode == "MQR":
        return ["HIGH", "MEDIUM", "LOW"]
    else:  # STANDARD mode
        return ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]


def draw_logo(canvas, logo_path, x, y, width, height):
    """Draw logo with enhanced transparency handling"""
    try:
        if os.path.exists(logo_path):

            # Method 1: Use mask='auto' for automatic transparency detection
            canvas.drawImage(logo_path, x, y, width=width, height=height, 
                            preserveAspectRatio=True, mask='auto')
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