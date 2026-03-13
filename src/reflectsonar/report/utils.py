"""
Utility functions and classes for report generation
"""

import os
import html
import re
import traceback

from reportlab.platypus import Flowable, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Circle, String

# Custom flowable to add bookmarks to PDF
class BookmarkFlowable(Flowable):
    """Flowable to add bookmarks to the PDF outline to create a table of contents"""
    def __init__(self, title, level=0): # pylint: disable=super-init-not-called
        self.title = title
        self.level = level
        self.width = 0
        self.height = 0

    def draw(self):
        """Draw the flowable and add the bookmark to the PDF outline"""

        canvas = self.canv

        # Create unique bookmark key for this title
        key = f"bookmark_{id(self)}_{self.title.replace(' ', '_')}"

        # First bookmark the current page
        canvas.bookmarkPage(key)

        # Then add to PDF outline with proper level and title
        canvas.addOutlineEntry(self.title, key, level=self.level)

class SeverityBookmarkFlowable(Flowable):
    """Flowable to add severity-level bookmarks that link to specific anchors in the document"""
    def __init__(self, title, anchor_id, level=1): # pylint: disable=super-init-not-called
        self.title = title
        self.anchor_id = anchor_id
        self.level = level
        self.width = 0
        self.height = 0

    def draw(self):
        """Draw the flowable and add the severity bookmark to the PDF outline"""

        canvas = self.canv

        # Create anchor key that matches the InvisibleAnchor
        anchor_key = f"anchor_{self.anchor_id}"

        # Add to PDF outline with reference to the anchor
        canvas.addOutlineEntry(self.title, anchor_key, level=self.level)

class ParagraphWithAnchor(Paragraph):
    """Paragraph that can create an anchor point when drawn"""
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
style_subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"],
                                alignment=2, fontSize=10, italic=True)
style_meta = ParagraphStyle("Meta", parent=style_normal, spaceAfter=6)
style_footer = ParagraphStyle("Footer", parent=style_normal, alignment=0, fontSize=10)
style_section_title = ParagraphStyle("SectionTitle", parent=styles["Heading1"],
                                     fontSize=16, spaceAfter=12, spaceBefore=12)
style_issue_title = ParagraphStyle("IssueTitle", parent=styles["Heading2"],
                                   fontSize=12, spaceAfter=6)
style_issue_meta = ParagraphStyle("IssueMeta", parent=style_normal, fontSize=9,
                                  textColor=colors.gray)
style_rule_title = ParagraphStyle("RuleTitle", parent=styles["Heading2"],
                                  fontSize=12, spaceAfter=6)
style_rule_subtitle = ParagraphStyle("RuleSubtitle", parent=styles["Heading3"],
                                     alignment=2, fontSize=10, spaceAfter=12)
style_section_key = ParagraphStyle("SectionKey", parent=styles["Heading3"],fontSize=11,
                            fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=6, italic=False)

_PROGRESS_ACTIVE = False
_PROGRESS_LENGTH = 0

class CircleBadge(Flowable):
    """Flowable to create a circular badge with a letter inside"""
    def __init__(self, letter, radius=12, color=HexColor("#D50000")):
        super().__init__()
        self.letter = letter
        self.radius = radius
        self.color = color
        self.width = self.height = 2 * radius

    def draw(self):
        """Draw the circular badge with the letter"""
        d = Drawing(self.width, self.height)
        d.add(Circle(self.radius, self.radius, self.radius,
                     fillColor=self.color, strokeColor=self.color))
        d.add(String(self.radius, self.radius - 4, self.letter, fontName="Helvetica",
                     fontSize=self.radius, textAnchor="middle"))
        d.drawOn(self.canv, 0, 0)

def badge(letter):
    """Create a colored badge for the given letter grade"""
    color_map = {
        "A": HexColor("#D1FADF"),
        "B": HexColor("#E1F4A9"),
        "C": HexColor("#FCE8A2"),
        "D": HexColor("#FFD6AF"),
        "E": HexColor("#FECCCB"),
    }
    return CircleBadge(letter, radius=12, color=color_map.get(letter, HexColor("#9E9E9E")))

def log(verbose: bool, message: str):
    """Print message if verbose mode is enabled"""
    if verbose:
        finish_progress()
        print(message)

def log_progress(verbose: bool, message: str):
    """Update a single-line progress message when verbose mode is enabled."""
    if not verbose:
        return

    global _PROGRESS_ACTIVE, _PROGRESS_LENGTH

    padded_message = message + (" " * max(0, _PROGRESS_LENGTH - len(message)))
    print(f"\r{padded_message}", end="", flush=True)
    _PROGRESS_ACTIVE = True
    _PROGRESS_LENGTH = len(message)

def finish_progress():
    """Finish the active single-line progress message, if any."""
    global _PROGRESS_ACTIVE, _PROGRESS_LENGTH

    if _PROGRESS_ACTIVE:
        print()
        _PROGRESS_ACTIVE = False
        _PROGRESS_LENGTH = 0

def print_message(message: str = ""):
    """Print a normal message without colliding with an active progress line."""
    finish_progress()
    print(message)

# Convert numeric score to letter grade
def score_to_grade(score: float) -> str:
    """Convert a numeric score (0-5) to a letter grade (A-E)"""
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
    """Get the numeric value of a measure or return default if not found"""
    return float(measures.get(metric).value if metric in measures else default)

def get_severity_order(severity: str, mode: str = "STANDARD") -> int:
    """Get the order of severity for sorting purposes"""
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
    """Get the color associated with a severity level"""
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

def get_severity_list(mode: str = "MQR") -> list:
    """Get the ordered list of severities based on the mode"""
    if mode == "STANDARD":
        return ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
    else:  # MQR mode
        return ["BLOCKER","HIGH", "MEDIUM", "LOW", "INFO"]

def draw_logo(canvas, logo_path, x, y, width, height):
    """Draw the logo image on the canvas at specified position and size"""
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
    except Exception: # pylint: disable=broad-exception-caught
        print_message("WARNING: Failed to add the logo.")

def severity_badge(severity: str, mode: str = "MQR"):
    """Create a colored badge for the given issue severity"""
    return CircleBadge(severity[0].upper(), radius=8, color=get_severity_color(severity, mode))

def _normalize_text(text) -> str:
    """Normalize external text content before embedding it in ReportLab markup."""
    if text is None:
        return ""
    return html.unescape(str(text)).replace("\r\n", "\n").replace("\r", "\n")

def escape_reportlab_text(text) -> str:
    """Escape text so ReportLab treats it as plain content, not markup."""
    return html.escape(_normalize_text(text), quote=True)

def plain_text_to_reportlab(text) -> str:
    """Convert plain text to safe ReportLab markup with preserved line breaks."""
    return escape_reportlab_text(text).replace("\n", "<br/>")

def format_code_snippet_for_reportlab(code) -> str:
    """Format raw source text as safe ReportLab markup for monospace display."""
    if not code:
        return ""

    formatted_lines = []
    for raw_line in _normalize_text(code).replace("\t", "    ").split("\n"):
        escaped_line = html.escape(raw_line, quote=True)
        escaped_line = re.sub(r" {2,}", lambda match: "&nbsp;" * len(match.group(0)),
                              escaped_line)
        escaped_line = re.sub(
            r'^((?:&gt;&gt;&gt; )?(?:&nbsp;| )*)(\d+)(:)',
            r'\1<font color="gray">\2</font>\3',
            escaped_line,
            count=1,
        )

        if escaped_line.startswith("&gt;&gt;&gt;"):
            escaped_line = f'<font color="red"><b>{escaped_line}</b></font>'

        formatted_lines.append(escaped_line)

    return "<br/>".join(formatted_lines)

def handle_exception(e: Exception, verbose: bool) -> int:
    """ Handle exceptions and print user-friendly messages"""
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
            print_message(line)
        return code

    # Generic classification by message content
    msg = str(e)
    lower = msg.lower()
    if "401" in lower or "unauthorized" in lower:
        print_message("\n🔐 Authentication Error: Invalid SonarQube token")
        print_message("💡 Check your token and permissions")
    elif "404" in lower or "not found" in lower:
        print_message("\n🔍 Project Not Found: Cannot find the specified project")
        print_message("💡 Verify your project key is correct")
    else:
        print_message(f"\n❌ Error generating report: {msg}")

    if verbose:
        print_message("\n🔍 Detailed error information:")
        traceback.print_exc()
    else:
        print_message("\n💡 Run with --verbose for detailed error information")
    return 1
