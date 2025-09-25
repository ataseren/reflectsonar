"""
Main PDF generation module - orchestrates all report components
"""
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from data.models import ReportData
import os
import time

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


def generate_pdf(report: ReportData, output_path: str = None, project_key: str = None, verbose: bool = False):
    """Generate complete PDF report with all sections"""
    # Detect SonarQube mode from issues
    mode = detect_sonarqube_mode(report.issues)
    
    if verbose:
        print(f"Detected SonarQube mode: {mode}")
        print(f"Report contains:")
        print(f"   • {len(report.issues)} issues")
        print(f"   • {len(report.hotspots)} security hotspots")
        print(f"   • {len(report.measures)} measures")
    
    # Create the PDF document
    final_path = output_path if output_path else f"reflect_sonar_report_{project_key}_{time.strftime('%Y%m%d')}.pdf"
    if verbose:
        print(f"Creating PDF document: {final_path}")
    
    doc = SimpleDocTemplate(
        final_path,
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
    if verbose:
        print(f"Generating cover page...")
    generate_cover_page(report, elements)
    
    # Add page break before issues sections
    elements.append(PageBreak())
    
    # Add bookmark and generate security issues section
    elements.append(BookmarkFlowable("Security Issues", 0))
    if verbose:
        print(f"Generating Security Issues section...")
    generate_security_issues_page(report, elements, mode)
    elements.append(PageBreak())
    
    # Add bookmark and generate reliability issues section
    elements.append(BookmarkFlowable("Reliability Issues", 0))
    if verbose:
        print(f"Generating Reliability Issues section...")
    generate_reliability_issues_page(report, elements, mode)
    elements.append(PageBreak())
    
    # Add bookmark and generate maintainability issues section
    elements.append(BookmarkFlowable("Maintainability Issues", 0))
    if verbose:
        print(f"Generating Maintainability Issues section...")
    generate_maintainability_issues_page(report, elements, mode)
    elements.append(PageBreak())
    
    # Add bookmark and generate security hotspots section
    elements.append(BookmarkFlowable("Security Hotspots", 0))
    if verbose:
        print(f"Generating Security Hotspots section...")
    generate_security_hotspots_page(report, elements)
    
    # Build the PDF
    if verbose:
        print(f"Building final PDF document...")
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    
    if verbose:
        print(f"PDF saved to: {final_path}")
    
    return final_path