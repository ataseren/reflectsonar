# Utility functions and classes for the report generation
from reportlab.platypus import Flowable, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Circle, String
import os
import traceback

# Custom flowable to add bookmarks to PDF
class BookmarkFlowable(Flowable):
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

# Custom flowable for severity-level bookmarks that link to specific anchors
class SeverityBookmarkFlowable(Flowable):
    def __init__(self, title, anchor_id, level=1):
        self.title = title
        self.anchor_id = anchor_id
        self.level = level
        self.width = 0
        self.height = 0
    
    def draw(self):
        # Add bookmark that links to a specific anchor
        canvas = self.canv
        # Create unique bookmark key for this title
        key = f"severity_bookmark_{id(self)}_{self.title.replace(' ', '_')}"
        # Create anchor key that matches the InvisibleAnchor
        anchor_key = f"anchor_{self.anchor_id}"
        
        # Add to PDF outline with reference to the anchor
        canvas.addOutlineEntry(self.title, anchor_key, level=self.level)

# Specialized Paragraph that can create an anchor point when drawn
class ParagraphWithAnchor(Paragraph):
    def __init__(self, text, style, anchor_id=None):
        super().__init__(text, style)
        self.anchor_id = anchor_id
    
    def draw(self):
        # Create anchor at this location if specified
        if self.anchor_id:
            canvas = self.canv
            key = f"anchor_{self.anchor_id}"
            canvas.bookmarkPage(key)
        # Then draw the normal paragraph content
        super().draw()

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
style_rule_title = ParagraphStyle("RuleTitle", parent=styles["Heading2"], fontSize=12, spaceAfter=6)
style_rule_subtitle = ParagraphStyle("RuleSubtitle", parent=styles["Heading3"], alignment=2, fontSize=10, spaceAfter=12)
style_section_key = ParagraphStyle("SectionKey", parent=styles["Heading3"], fontSize=11, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=6, italic=False)


# Custom flowable for creating circular badges
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
        d.add(String(self.radius, self.radius - 4, self.letter, fontName="Helvetica",
                     fontSize=self.radius, textAnchor="middle"))
        d.drawOn(self.canv, 0, 0)

# Create a colored grade badge
def badge(letter):
    color_map = {
        "A": HexColor("#D1FADF"),
        "B": HexColor("#E1F4A9"),
        "C": HexColor("#FCE8A2"),
        "D": HexColor("#FFD6AF"),
        "E": HexColor("#FECCCB"),
    }
    return CircleBadge(letter, radius=12, color=color_map.get(letter, HexColor("#9E9E9E")))

def log(verbose: bool, message: str):
    if verbose:
        print(message)

# Convert numeric score to letter grade
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

# Extract measure value from measures dictionary
def get_measure_value(measures, metric, default="0"):
    return float(measures.get(metric).value if metric in measures else default)

# Get numeric order for severity sorting (lower number = higher priority)
def get_severity_order(severity: str, mode: str = "STANDARD") -> int:
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

# Return color for severity badge
def get_severity_color(severity: str, mode: str = "STANDARD") -> HexColor:
    if mode == "MQR":
        color_map = {
            "BLOCKER": HexColor("#940404"),
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

# Get ordered list of severities for the given mode
def get_severity_list(mode: str = "STANDARD") -> list:
    if mode == "MQR":
        return ["BLOCKER","HIGH", "MEDIUM", "LOW", "INFO"]
    else:  # STANDARD mode
        return ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]

# Draw logo on the canvas with transparency handling
def draw_logo(canvas, logo_path, x, y, width, height):
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
    except Exception:
        print("WARNING: Failed to add the logo.")

# Create a colored badge for issue severity
def severity_badge(severity: str, mode: str = "MQR"):
    return CircleBadge(severity[0].upper(), radius=8, color=get_severity_color(severity, mode))

def handle_exception(e: Exception, verbose: bool) -> int:
    # Map simple exception types to their fixed messages
    table = {
        KeyboardInterrupt: (
            ["\n", "🛑 Report generation interrupted by user", "✨ Thanks for using ReflectSonar!"],
            1,
        ),
        ConnectionError: (
            [
                "\n🌐 Connection Error: Unable to connect to SonarQube server",
                f"❌ {str(e)}",
                "\n💡 Check your SonarQube URL and network connection",
            ],
            1,
        ),
        PermissionError: (
            [
                "\n🔒 Permission Error: Cannot write to output location",
                f"❌ {str(e)}",
                "\n💡 Check file permissions or choose a different output path",
            ],
            1,
        ),
        FileNotFoundError: (
            [
                "\n📁 File Not Found: Missing required file",
                f"❌ {str(e)}",
                "\n💡 Ensure all required files (like logo) are in place",
            ],
            1,
        ),
    }

    payload = table.get(type(e))
    if payload:
        lines, code = payload
        for line in lines:
            print(line)
        return code

    # Generic classification by message content
    msg = str(e)
    lower = msg.lower()
    if "401" in lower or "unauthorized" in lower:
        print("\n🔐 Authentication Error: Invalid SonarQube token")
        print("💡 Check your token and permissions")
    elif "404" in lower or "not found" in lower:
        print("\n🔍 Project Not Found: Cannot find the specified project")
        print("💡 Verify your project key is correct")
    else:
        print(f"\n❌ Error generating report: {msg}")

    if verbose:
        print("\n🔍 Detailed error information:")
        traceback.print_exc()
    else:
        print("\n💡 Run with --verbose for detailed error information")
    return 1