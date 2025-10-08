"""
This module generates hotspot pages of the report
by using data from SonarQube.
"""

import re
import html

from reportlab.platypus import (
     Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

from .utils import ( # pylint: disable=relative-beyond-top-level
    style_section_title, style_issue_meta, style_normal, # pylint: disable=relative-beyond-top-level
    CircleBadge, BookmarkFlowable # pylint: disable=relative-beyond-top-level
)

def create_hotspot_table(hotspots):
    """ Creates a table displaying security hotspots
        with vulnerability probability, rule, and message
    """
    if not hotspots:
        # Create a list with spacer and paragraph for better formatting
        content = [
            Spacer(1, 5*cm),
            Paragraph(
                "<i>No security hotspots found. This indicates good security practices in the codebase.</i>", # pylint: disable=line-too-long
                style_normal
            )
        ]
        return KeepTogether(content)

    # Sort hotspots by vulnerability probability (highest risk first)
    def get_hotspot_priority(hotspot):
        probability_order = {
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3
        }
        return probability_order.get(hotspot.vulnerability_probability.upper(), 4)

    sorted_hotspots = sorted(hotspots, key=get_hotspot_priority)

    table_data = []

    # Add header
    header_style = ParagraphStyle("Header", parent=style_normal,
                                  fontName="Helvetica-Bold", fontSize=10)
    table_data.append([
        Paragraph("Risk", header_style),
        Paragraph("File Path", header_style),
        Paragraph("Rule & Message", header_style)
    ])

    for hotspot in sorted_hotspots:
        # Use full component path instead of just filename
        full_path = hotspot.component
        # Remove project key prefix if present
        full_path = full_path.replace(":", "")

        # Smart path formatting - break long paths for better readability
        if len(full_path) > 40:
            # Find good break points (after / or before long segments)
            parts = full_path.split('/')
            if len(parts) > 1:
                # Group parts to keep lines under ~40 chars when possible
                formatted_parts = []
                current_line = ""

                for part in parts:
                    if not current_line:
                        current_line = part
                    elif len(current_line + "/" + part) <= 40:
                        current_line += "/" + part
                    else:
                        formatted_parts.append(current_line)
                        current_line = part

                if current_line:
                    formatted_parts.append(current_line)

                filename = "<br/>".join(formatted_parts)
            else:
                filename = full_path
        else:
            filename = full_path

        if hotspot.line:
            filename += f"<br/><b>(Line {hotspot.line})</b>"

        # Remove all HTML tags from the message to prevent parsing conflicts
        cleaned_message = re.sub(r'<[^>]+>', '', hotspot.message)
        # Also clean up any HTML entities that might remain
        cleaned_message = html.unescape(cleaned_message)

        # Include security category if available
        category_info = ""
        if hotspot.security_category:
            formatted_category = format_security_category_name(hotspot.security_category)
            category_info = f"<br/><font size=8 color='gray'>Category: {formatted_category}</font>"

        rule_and_message = f"<b>{hotspot.rule_key }</b><br/>{cleaned_message}{category_info}"

        # Create vulnerability probability badge
        prob_colors = {
            "HIGH": colors.Color(0.8, 0.2, 0.2),    # Red
            "MEDIUM": colors.Color(0.9, 0.6, 0.1),  # Orange  
            "LOW": colors.Color(0.9, 0.9, 0.2)      # Yellow
        }
        prob_color = prob_colors.get(hotspot.vulnerability_probability.upper(), colors.gray)

        risk_badge = CircleBadge(hotspot.vulnerability_probability[0].upper(),
                                 radius=8, color=prob_color)

        # Create a custom style for file paths
        file_path_style = ParagraphStyle(
            "FilePathStyle",
            parent=style_issue_meta,
            fontSize=8,  # Slightly smaller for paths
            wordWrap='LTR'  # Better word wrapping for long paths
        )

        # Add main hotspot row
        table_data.append([
            risk_badge,
            Paragraph(filename, file_path_style),
            Paragraph(rule_and_message, style_normal)
        ])

        # Add code snippet row if available
        if hasattr(hotspot, 'code_snippet') and hotspot.code_snippet and hotspot.code_snippet.strip(): # pylint: disable=line-too-long
            # Create enhanced code style for better formatting
            code_style = ParagraphStyle(
                "CodeStyle", 
                parent=style_normal,
                fontName="Courier-Bold",  # Use bold Courier for better visibility
                fontSize=9,  # Slightly larger font
                textColor=colors.black,  # Black text for better readability
                backColor=colors.Color(1.0, 0.95, 0.95),  # Light red background for security focus
                leftIndent=15,
                rightIndent=15,
                spaceBefore=6,
                spaceAfter=6,
                borderWidth=1,
                borderColor=colors.Color(0.9, 0.7, 0.7),  # Light red border
                borderPadding=8
            )

            # Enhanced code formatting with indentation preservation
            formatted_code = hotspot.code_snippet

            # First, handle line breaks
            formatted_code = formatted_code.replace('\n', '<br/>')

            # Remove HTML span tags
            formatted_code = re.sub(r"</?span[^>]*>", "", formatted_code)

            # Preserve indentation by converting leading spaces to non-breaking spaces
            # This regex finds spaces at the beginning of lines (after <br/> or at start)
            formatted_code = re.sub(r'(^|\<br/\>)( +)',
                                  lambda m: m.group(1) + '&nbsp;' * len(m.group(2)),
                                  formatted_code)

            # Also preserve spaces within the code (multiple spaces)
            formatted_code = re.sub(r'  +', lambda m: '&nbsp;' * len(m.group(0)), formatted_code)

            # Convert tabs to 4 non-breaking spaces
            formatted_code = formatted_code.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')

            # Highlight the problematic line (>>>) with red color
            formatted_code = re.sub(r'(&gt;&gt;&gt;[^<]+)', r'<font color="red"><b>\1</b></font>',
                                    formatted_code)

            # Make line numbers slightly gray (but preserve their spacing)
            formatted_code = re.sub(r'(\s*)(\d+)(:)', r'\1<font color="gray">\2</font>\3',
                                    formatted_code)

            code_paragraph = Paragraph(
                f"<b><font color='darkred'>🔒 Security Hotspot Code:</font></b><br/>"
                f"<font name='Courier' size='8'>{formatted_code}</font>",
                code_style
            )

            table_data.append([
                code_paragraph,  # Code paragraph spans all columns
                "",  # Placeholder for span
                ""   # Placeholder for span  
            ])

    table = Table(table_data, colWidths=[2*cm, 5*cm, 11*cm])

    # Build dynamic table styling
    table_style = [
        # Header styling
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),

        # General table styling
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Risk column centered
        ("VALIGN", (0, 0), (-1, -1), "TOP"),

        # Grid lines
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # Padding
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]

    # Apply enhanced styling for code snippet rows
    for i, row in enumerate(table_data[1:], start=1):  # Skip header
        if (isinstance(row[1], str) and row[1] == "" and
            isinstance(row[2], str) and row[2] == ""):
            # This is a code snippet row - first column has content, others are empty
            table_style.append(("BACKGROUND", (0, i), (-1, i),
                                colors.Color(1.0, 0.98, 0.98)))  # Very light red
            table_style.append(("SPAN", (0, i), (2, i)))  # Span from column 0 to 2
            table_style.append(("LEFTPADDING", (0, i), (0, i), 10))
            table_style.append(("RIGHTPADDING", (0, i), (0, i), 10))
            table_style.append(("TOPPADDING", (0, i), (0, i), 8))
            table_style.append(("BOTTOMPADDING", (0, i), (0, i), 8))
            # Add a subtle border around code snippet rows
            table_style.append(("BOX", (0, i), (2, i), 1, colors.Color(0.9, 0.7, 0.7)))

    table.setStyle(TableStyle(table_style))

    return table

def create_hotspot_section(title: str, hotspots, elements):
    """Creates the security hotspot section of the report"""
    elements.append(Paragraph(title, style_section_title))

    # Add hotspot count summary
    if hotspots:
        risk_counts = {}

        # Count vulnerability probabilities
        for hotspot in hotspots:
            risk = hotspot.vulnerability_probability.upper()
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        summary_parts = []
        risk_list = ["HIGH", "MEDIUM", "LOW"]

        for risk in risk_list:
            count = risk_counts.get(risk, 0)
            if count > 0:
                summary_parts.append(f"{risk.title()}: {count}")

        if summary_parts:
            summary_text = f"<b>Total: {len(hotspots)} hotspots</b> ({', '.join(summary_parts)})"
            elements.append(Paragraph(summary_text, style_issue_meta))
    else:
        elements.append(Paragraph("<b>Total: 0 hotspots</b>", style_issue_meta))

    elements.append(Spacer(1, 0.5*cm))
    elements.append(create_hotspot_table(hotspots))
    elements.append(Spacer(1, 1*cm))

def categorize_hotspots_by_security_category(hotspots):
    """Returns a dictionary categorizing hotspots by their security category"""
    categories = {}
    uncategorized = []

    for hotspot in hotspots:
        category = hotspot.security_category
        if category:
            if category not in categories:
                categories[category] = []
            categories[category].append(hotspot)
        else:
            uncategorized.append(hotspot)

    return categories, uncategorized

def format_security_category_name(category_key: str) -> str:
    """Maps SonarQube security category keys to human-readable names"""
    category_mapping = {
        # Add your mappings here, for example:
        "sql-injection": "SQL Injection",
        "rce": "Remote Code Execution",
        "object-injection": "Object Injection",
        "path-traversal-injection": "Path Traversal Injection",
        "ldap-injection": "LDAP Injection",
        "xpath-injection": "XPath Injection",
        "log-injection": "Log Injection",
        "xxe": "XML External Entity (XXE)",
        "xss": "Cross-Site Scripting (XSS)",
        "dos": "Denial of Service (DoS)",
        "ssrf": "Server-Side Request Forgery (SSRF)",
        "csrf": "Cross-Site Request Forgery (CSRF)",
        "http-response-splitting": "HTTP Response Splitting",
        "open-redirect": "Open Redirect",
        "auth": "Authentication",
        "weak-cryptography": "Weak Cryptography", 
        "insecure-conf": "Insecure Configuration",
        "file-manipulation": "File Manipulation",
        "encrypt-data": "Encrypt Data",
        "traceability": "Traceability",
        "permission": "Permission",
        "others": "Others",
    }

    # Return mapped name or fallback to formatted version
    return category_mapping.get(category_key,
                                category_key.replace('-', ' ').replace('_', ' ').title())

def generate_security_hotspots_page(report, elements):
    """Generates the security hotspots section of the report"""
    # Check if we have hotspots to categorize
    if not report.hotspots:
        create_hotspot_section("Security Hotspots", report.hotspots, elements)
        return

    # Categorize hotspots by security category
    categories, uncategorized = categorize_hotspots_by_security_category(report.hotspots)

    # Main section title
    elements.append(Paragraph("Security Hotspots", style_section_title))

    # Overall summary
    total_hotspots = len(report.hotspots)
    risk_counts = {}
    for hotspot in report.hotspots:
        risk = hotspot.vulnerability_probability.upper()
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    summary_parts = []
    risk_list = ["HIGH", "MEDIUM", "LOW"]
    for risk in risk_list:
        count = risk_counts.get(risk, 0)
        if count > 0:
            summary_parts.append(f"{risk.title()}: {count}")

    if summary_parts:
        summary_text = f"<b>Total: {total_hotspots} hotspots</b> ({', '.join(summary_parts)})"
        elements.append(Paragraph(summary_text, style_issue_meta))

    elements.append(Spacer(1, 0.5*cm))

    # Display categorized hotspots
    if categories:
        # Sort categories for consistent display
        sorted_categories = sorted(categories.keys())

        for category in sorted_categories:
            category_hotspots = categories[category]

            # Create category subsection
            category_title = f"{format_security_category_name(category)} ({len(category_hotspots)} hotspots)" # pylint: disable=line-too-long

            # Add sub-bookmark for this category (level 1 - indented under Security Hotspots)
            elements.append(BookmarkFlowable(f"{format_security_category_name(category)}", 1))

            # Create subsection style
            category_style = ParagraphStyle(
                "CategoryTitle", 
                parent=style_section_title,
                fontSize=14,
                spaceAfter=8,
                spaceBefore=16,
                textColor=colors.Color(0.2, 0.2, 0.6)  # Dark blue
            )

            elements.append(Paragraph(category_title, category_style))
            elements.append(create_hotspot_table(category_hotspots))
            elements.append(Spacer(1, 0.5*cm))

    # Display uncategorized hotspots if any
    if uncategorized:
        # Add sub-bookmark for uncategorized hotspots
        elements.append(BookmarkFlowable("Other Security Issues", 1))

        category_style = ParagraphStyle(
            "CategoryTitle", 
            parent=style_section_title,
            fontSize=14,
            spaceAfter=8,
            spaceBefore=16,
            textColor=colors.Color(0.6, 0.2, 0.2)  # Dark red
        )

        elements.append(Paragraph(f"Other Security Hotspots ({len(uncategorized)} hotspots)",
                                  category_style))
        elements.append(create_hotspot_table(uncategorized))
        elements.append(Spacer(1, 0.5*cm))
