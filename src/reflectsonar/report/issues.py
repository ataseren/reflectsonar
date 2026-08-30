"""
This module generates issue pages of the report
by using data from SonarQube.
"""

from typing import Dict, List, Set

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

from .utils import (
    style_section_title,
    style_issue_meta,
    style_normal,  # pylint: disable=relative-beyond-top-level
    get_severity_order,
    get_severity_list,  # pylint: disable=relative-beyond-top-level
    severity_badge,
    SeverityBookmarkFlowable,
    ParagraphWithAnchor,  # pylint: disable=relative-beyond-top-level
    escape_reportlab_text,
    plain_text_to_reportlab,
    split_code_snippet_for_reportlab,
)  # pylint: disable=relative-beyond-top-level

ISSUE_TABLE_MAX_ROWS = 120


def get_issues_by_impact_category(issues, category: str):
    """Filters issues by their impact category"""
    filtered_issues = []

    for issue in issues:
        # For MQR mode, always use impacts field
        if issue.impacts:
            # Look for the category in the impacts
            for impact in issue.impacts:
                if impact.get("softwareQuality", "").upper() == category.upper():
                    filtered_issues.append(issue)
                    break
        else:
            # Fallback to legacy categorization for older SonarQube versions
            if category.upper() == "SECURITY":
                if (
                    issue.type.upper() == "VULNERABILITY"
                    or issue.type.upper() == "SECURITY_HOTSPOT"
                    or any(tag.lower() in ["security", "cwe", "owasp"] for tag in issue.tags)
                ):
                    filtered_issues.append(issue)
            elif category.upper() == "RELIABILITY":
                if issue.type.upper() == "BUG":
                    filtered_issues.append(issue)
            elif category.upper() == "MAINTAINABILITY":
                if issue.type.upper() == "CODE_SMELL":
                    filtered_issues.append(issue)

    return filtered_issues


def get_issue_display_severity(issue, mode: str, category: str = None):
    """Returns the severity label that should be shown in the report"""
    if mode == "MQR" and issue.impacts:
        matching_impacts = [
            impact
            for impact in issue.impacts
            if not category or impact.get("softwareQuality", "").upper() == category.upper()
        ]
        impact_severities = [
            impact.get("severity", "").upper()
            for impact in matching_impacts
            if impact.get("severity")
        ]
        if impact_severities:
            return min(impact_severities, key=lambda value: get_severity_order(value, mode))
    return issue.severity


def get_issue_sort_order(issue, mode: str, category: str = None):
    """Returns the sort order for an issue based on the active SonarQube mode"""
    return get_severity_order(get_issue_display_severity(issue, mode, category), mode)


def chunk_issues_for_tables(issues, max_rows: int = None):
    """Split large issue lists into smaller chunks to avoid giant ReportLab tables"""
    if max_rows is None:
        max_rows = ISSUE_TABLE_MAX_ROWS

    chunks = []
    current_chunk: List[object] = []
    current_rows = 0

    for issue in issues:
        snippet_chunks = (
            split_code_snippet_for_reportlab(issue.code_snippet)
            if issue.code_snippet and issue.code_snippet.strip()
            else []
        )
        row_cost = 1 + len(snippet_chunks)

        if current_chunk and current_rows + row_cost > max_rows:
            chunks.append(current_chunk)
            current_chunk = []
            current_rows = 0

        current_chunk.append(issue)
        current_rows += row_cost

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# Create a table displaying issues with severity, rule, and message
def create_issue_table(
    issues,
    mode: str = "STANDARD",
    section_name: str = "",
    seen_severities=None,
    sort_issues: bool = True,
    category: str = None,
):
    """Creates a table of issues with severity, file path, rule, message, and code snippet"""
    if not issues:
        # Create a list with spacer and paragraph for better formatting
        content = [
            Spacer(1, 5 * cm),
            Paragraph("<i>No issues found in this category.</i>", style_normal),
        ]
        return KeepTogether(content)

    if seen_severities is None:
        seen_severities = set()

    sorted_issues = (
        sorted(issues, key=lambda issue: get_issue_sort_order(issue, mode, category))
        if sort_issues
        else issues
    )

    table_data = []

    # Add header
    header_style = ParagraphStyle(
        "Header", parent=style_normal, fontName="Helvetica-Bold", fontSize=10
    )
    table_data.append(
        [
            Paragraph("Severity", header_style),
            Paragraph("File Path", header_style),
            Paragraph("Rule & Message", header_style),
        ]
    )

    file_path_style = ParagraphStyle(
        "FilePathStyle",
        parent=style_issue_meta,
        fontSize=8,  # Slightly smaller for paths
        wordWrap="LTR",  # Better word wrapping for long paths
    )
    code_style = ParagraphStyle(
        "CodeStyle",
        parent=style_normal,
        fontName="Courier-Bold",  # Use bold Courier for better visibility
        fontSize=9,  # Slightly larger font
        textColor=colors.black,  # Black text for better readability
        backColor=colors.Color(0.95, 0.95, 0.95),  # Light gray background
        leftIndent=15,
        rightIndent=15,
        spaceBefore=6,
        spaceAfter=6,
        borderWidth=1,
        borderColor=colors.Color(0.8, 0.8, 0.8),  # Light border
        borderPadding=8,
    )

    for issue in sorted_issues:
        display_severity = get_issue_display_severity(issue, mode, category)

        # Check if this is the first occurrence of this severity level
        anchor_id = None
        if display_severity not in seen_severities:
            seen_severities.add(display_severity)
            # Create anchor ID for this severity in this section
            anchor_id = f"{section_name}_{display_severity}".replace(" ", "_")

        # Use full component path instead of just filename
        full_path = issue.component
        # Remove project key prefix if present
        if ":" in full_path:
            full_path = full_path.split(":", 1)[1]

        # Smart path formatting - break long paths for better readability
        if len(full_path) > 40:
            # Find good break points (after / or before long segments)
            parts = full_path.split("/")
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

                filename = "<br/>".join(escape_reportlab_text(part) for part in formatted_parts)
            else:
                filename = escape_reportlab_text(full_path)
        else:
            filename = escape_reportlab_text(full_path)

        if issue.line:
            filename += f"<br/><b>(Line {issue.line})</b>"

        rule_and_message = (
            f"<b>{escape_reportlab_text(issue.rule)}</b><br/>"
            f"{plain_text_to_reportlab(issue.message)}"
        )

        # Create filename paragraph, with anchor if this is first occurrence of severity
        if anchor_id:
            filename_paragraph = ParagraphWithAnchor(filename, file_path_style, anchor_id)
        else:
            filename_paragraph = Paragraph(filename, file_path_style)

        # Add main issue row
        table_data.append(
            [
                severity_badge(display_severity, mode),
                filename_paragraph,
                Paragraph(rule_and_message, style_normal),
            ]
        )

        # Add code snippet row if available
        if issue.code_snippet and issue.code_snippet.strip():
            snippet_chunks = split_code_snippet_for_reportlab(issue.code_snippet)

            for chunk_index, formatted_code in enumerate(snippet_chunks):
                label = "Problematic Code:" if chunk_index == 0 else "Problematic Code (continued):"
                code_paragraph = Paragraph(
                    f"<b><font color='darkblue'>📄 {label}</font></b><br/>"
                    f"<font name='Courier' size='8'>{formatted_code}</font>",
                    code_style,
                )

                table_data.append(
                    [
                        code_paragraph,  # Code paragraph spans all columns
                        "",  # Placeholder for span
                        "",  # Placeholder for span
                    ]
                )

    table = Table(table_data, colWidths=[1.8 * cm, 4.7 * cm, 10.5 * cm], repeatRows=1)

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
        ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Severity column centered
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
        if isinstance(row[1], str) and row[1] == "" and isinstance(row[2], str) and row[2] == "":
            # This is a code snippet row - first column has content, others are empty
            table_style.append(
                ("BACKGROUND", (0, i), (-1, i), colors.Color(0.98, 0.98, 1.0))
            )  # Very light blue
            table_style.append(("SPAN", (0, i), (2, i)))  # Span from column 0 to 2
            table_style.append(("LEFTPADDING", (0, i), (0, i), 10))
            table_style.append(("RIGHTPADDING", (0, i), (0, i), 10))
            table_style.append(("TOPPADDING", (0, i), (0, i), 8))
            table_style.append(("BOTTOMPADDING", (0, i), (0, i), 8))
            # Add a subtle border around code snippet rows
            table_style.append(("BOX", (0, i), (2, i), 1, colors.Color(0.7, 0.7, 0.9)))

    table.setStyle(TableStyle(table_style))

    return table


def create_issue_section(
    title: str, issues, elements, mode: str = "STANDARD", category: str = None
):
    """Creates a complete issue section with title, summary, and table"""
    elements.append(Paragraph(title, style_section_title))

    # Add issue count summary
    if issues:
        severity_counts: Dict[str, int] = {}

        # Count severities differently based on mode
        for issue in issues:
            if mode == "MQR" and issue.impacts:
                impact_severity = get_issue_display_severity(issue, mode, category).upper()
                if impact_severity:
                    severity_counts[impact_severity] = (
                        severity_counts.get(impact_severity, 0) + 1
                    )  # pylint: disable=line-too-long
            else:
                # For Standard mode, use issue severity
                severity = issue.severity.upper()
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        summary_parts = []
        severity_list = get_severity_list(mode)

        # Add sub-bookmarks for severities that have issues
        for severity in severity_list:
            count = severity_counts.get(severity, 0)
            if count > 0:
                summary_parts.append(f"{severity.title()}: {count}")
                # Create anchor ID for this severity in this section
                anchor_id = f"{title}_{severity}".replace(" ", "_")
                # Add severity-specific bookmark that will link to the anchor
                elements.append(
                    SeverityBookmarkFlowable(f"{severity.title()} ({count})", anchor_id, 1)
                )  # pylint: disable=line-too-long

        if summary_parts:
            summary_text = f"<b>Total: {len(issues)} issues</b> ({', '.join(summary_parts)})"
            elements.append(Paragraph(summary_text, style_issue_meta))
    else:
        elements.append(Paragraph("<b>Total: 0 issues</b>", style_issue_meta))

    elements.append(Spacer(1, 0.5 * cm))

    if not issues:
        elements.append(create_issue_table(issues, mode, title, category=category))
    else:
        sorted_issues = sorted(
            issues, key=lambda issue: get_issue_sort_order(issue, mode, category)
        )
        seen_severities: Set[str] = set()

        for issue_chunk in chunk_issues_for_tables(sorted_issues):
            elements.append(
                create_issue_table(
                    issue_chunk,
                    mode,
                    title,
                    seen_severities=seen_severities,
                    sort_issues=False,
                    category=category,
                )
            )

    elements.append(Spacer(1, 1 * cm))


# Generate Security issues section
def generate_security_issues_page(report, elements, mode):
    """Generates the Security Issues section of the report"""
    security_issues = get_issues_by_impact_category(report.issues, "SECURITY")
    create_issue_section("Security Issues", security_issues, elements, mode, "SECURITY")


# Generate Reliability issues section
def generate_reliability_issues_page(report, elements, mode):
    """Generates the Reliability Issues section of the report"""
    reliability_issues = get_issues_by_impact_category(report.issues, "RELIABILITY")
    create_issue_section("Reliability Issues", reliability_issues, elements, mode, "RELIABILITY")


# Generate Maintainability issues section
def generate_maintainability_issues_page(report, elements, mode):
    """Generates the Maintainability Issues section of the report"""
    maintainability_issues = get_issues_by_impact_category(report.issues, "MAINTAINABILITY")
    create_issue_section(
        "Maintainability Issues", maintainability_issues, elements, mode, "MAINTAINABILITY"
    )
