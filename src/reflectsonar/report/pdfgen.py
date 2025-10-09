"""
This module is the main PDF generation module that orchestrates all report components
and outputs the final PDF document.
"""

import os
import time

from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from ..data.models import ReportData

from .utils import draw_logo, BookmarkFlowable, log # pylint: disable=relative-beyond-top-level
from .cover_page import generate_cover_page # pylint: disable=relative-beyond-top-level
from .issues import ( generate_security_issues_page, # pylint: disable=relative-beyond-top-level
    generate_reliability_issues_page, # pylint: disable=relative-beyond-top-level
    generate_maintainability_issues_page # pylint: disable=relative-beyond-top-level
)
from .hotspots import generate_security_hotspots_page # pylint: disable=relative-beyond-top-level
from .rules import generate_rules_page # pylint: disable=relative-beyond-top-level


def add_header_footer(canvas, doc):
    """Adds header and footer to each page of the PDF document"""
    canvas.saveState()

    # Add logo to all pages (including cover page)
    logo_path = os.path.join(os.path.dirname(__file__), "reflect-sonar.png")

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

# Main function to generate the PDF report
def generate_pdf(report: ReportData, output_path: str = None,
                 project_key: str = None, verbose: bool = False):
    """Main function that generates a PDF report from the provided ReportData object"""

    # Determine SonarQube mode
    mode = "MQR" if report.mode_setting else "STANDARD"

    log(verbose, f"Detected SonarQube mode: {mode}")
    log(verbose, "Report contains:")
    log(verbose, f"   • {len(report.issues)} issues")
    log(verbose, f"   • {len(report.hotspots)} security hotspots")
    log(verbose, f"   • {len(report.measures)} measures")

    # Create the PDF document
    if output_path:
        final_path = output_path
    else:
        final_path = f"reflect_sonar_report_{project_key}_{time.strftime('%Y%m%d')}.pdf"
    log(verbose,f"Creating PDF document: {final_path}")

    # Set document title for browser/viewer tab
    project_name = report.project.name if hasattr(report, 'project') and report.project and hasattr(report.project, 'name') else project_key
    document_title = f"ReflectSonar Report - {project_name}"
    
    doc = SimpleDocTemplate(
        final_path,
        pagesize=A4,
        topMargin=3*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
        title=document_title,
        author="ReflectSonar",
        subject=f"Quality Report for {project_name}",
        creator="ReflectSonar PDF Generator",
        keywords=f"SonarQube,Quality,Report,{project_name}"
    )

    # Container for all report elements
    elements = []

    # Add main bookmark for cover page
    elements.append(BookmarkFlowable("Report Overview", 0))

    # Generate cover page
    log(verbose, "Generating cover page...")
    generate_cover_page(report, elements)

    # Add page break before issues sections
    elements.append(PageBreak())

    # Add bookmark and generate security issues section
    elements.append(BookmarkFlowable("Security Issues", 0))
    log(verbose, "Generating Security Issues section...")
    generate_security_issues_page(report, elements, mode)
    elements.append(PageBreak())

    # Add bookmark and generate reliability issues section
    elements.append(BookmarkFlowable("Reliability Issues", 0))
    log(verbose, "Generating Reliability Issues section...")
    generate_reliability_issues_page(report, elements, mode)
    elements.append(PageBreak())

    # Add bookmark and generate maintainability issues section
    elements.append(BookmarkFlowable("Maintainability Issues", 0))
    log(verbose, "Generating Maintainability Issues section...")
    generate_maintainability_issues_page(report, elements, mode)
    elements.append(PageBreak())

    # Add bookmark and generate security hotspots section
    elements.append(BookmarkFlowable("Security Hotspots", 0))
    log(verbose, "Generating Security Hotspots section...")
    generate_security_hotspots_page(report, elements)

    # Add rules reference section if we have rules
    if report.rules:
        elements.append(PageBreak())
        elements.append(BookmarkFlowable("Rules Reference", 0))
        log(verbose, "Generating Rules Reference section...")
        generate_rules_page(report, elements, verbose)

    # Build the PDF
    if verbose:
        print("Building final PDF document...")
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    log(verbose, f"PDF saved to: {final_path}")

    return final_path
