"""
Main PDF generation module - orchestrates all report components
"""
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from data.models import ReportData
import os

# Import modular components
from .utils import detect_sonarqube_mode, draw_logo, BookmarkFlowable
from .cover_page import generate_cover_page
from .issues import (
    generate_security_issues_page,
    generate_reliability_issues_page, 
    generate_maintainability_issues_page
)
from .hotspots import generate_security_hotspots_page


def add_header_footer(canvas, doc):
    """Add header and footer to each page"""
    canvas.saveState()
    
    # Add logo to all pages (including cover page)
    logo_path = os.path.join(os.path.dirname(__file__), "reflect-sonar.png")
    
    # Calculate position for top-left corner with margins
    x = 1.5 * cm  # Left margin
    y = A4[1] - 2 * cm  # Top margin
    
    # Make logos bigger - different sizes for cover vs other pages
    if doc.page == 1:  # Cover page
        logo_width = 6 * cm  # Bigger on cover page
        logo_height = 6 * cm
        x = 1.5 * cm  # Left margin
        y = A4[1] - 6 * cm  # Top margin
    else:  # Other pages
        logo_width = 4 * cm  # Bigger than before
        logo_height = 4 * cm
        x = 1.5 * cm  # Left margin
        y = A4[1] - 4 * cm  # Top margin
        
    draw_logo(canvas, logo_path, x, y, logo_width, logo_height)
    
    canvas.restoreState()


def generate_pdf(report: ReportData, output_path: str = "reflect_sonar_report.pdf"):
    """Generate complete PDF report with all sections"""
    # Detect SonarQube mode from issues
    mode = detect_sonarqube_mode(report.issues)
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=3*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    # Container for all report elements
    elements = []
    
    # Add main bookmark for cover page
    elements.append(BookmarkFlowable("Report Overview", 0))
    
    # Generate cover page
    generate_cover_page(report, elements)
    
    # Add page break before issues sections
    elements.append(PageBreak())
    
    # Add bookmark and generate security issues section
    elements.append(BookmarkFlowable("Security Issues", 0))
    generate_security_issues_page(report, elements, mode)
    elements.append(PageBreak())
    
    # Add bookmark and generate reliability issues section
    elements.append(BookmarkFlowable("Reliability Issues", 0))
    generate_reliability_issues_page(report, elements, mode)
    elements.append(PageBreak())
    
    # Add bookmark and generate maintainability issues section
    elements.append(BookmarkFlowable("Maintainability Issues", 0))
    generate_maintainability_issues_page(report, elements, mode)
    elements.append(PageBreak())
    
    # Add bookmark and generate security hotspots section
    elements.append(BookmarkFlowable("Security Hotspots", 0))
    generate_security_hotspots_page(report, elements)
    
    # Build the PDF
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    
    return output_path