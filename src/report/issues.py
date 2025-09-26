"""
Issue pages generation for PDF reports
"""
import re

from .utils import (
    style_section_title, style_issue_meta, style_normal, Paragraph, Spacer, 
    Table, TableStyle, colors, cm, get_severity_order, get_severity_list,
    severity_badge, ParagraphStyle, KeepTogether, BookmarkFlowable
)


def get_issues_by_impact_category(issues, category: str, mode: str = "STANDARD"):
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


def create_issue_table(issues, mode: str = "STANDARD"):
    """Create a table displaying issues with severity, rule, and message"""
    if not issues:
        # Create a list with spacer and paragraph for better formatting
        content = [
            Spacer(1, 5*cm),
            Paragraph(
                "<i>No issues found in this category.</i>", 
                style_normal
            )
        ]
        return KeepTogether(content)
    
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
        Paragraph("File Path", header_style),
        Paragraph("Rule & Message", header_style)
    ])
    
    for issue in sorted_issues:
        # Use full component path instead of just filename
        full_path = issue.component
        # Remove project key prefix if present
        if ':' in full_path:
            full_path = full_path.split(':', 1)[1]
        
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
        
        if issue.line:
            filename += f"<br/><b>(Line {issue.line})</b>"
        
        # Format rule and message - clean HTML in the message to prevent parsing errors
        rule_name = issue.rule.split(':')[-1] if ':' in issue.rule else issue.rule
        
        # Clean HTML content from the message to prevent ReportLab parsing issues
        import re
        
        # Remove all HTML tags from the message to prevent parsing conflicts
        # This preserves the text content while removing problematic markup
        cleaned_message = re.sub(r'<[^>]+>', '', issue.message)
        
        # Also clean up any HTML entities that might remain
        import html
        cleaned_message = html.unescape(cleaned_message)
        
        rule_and_message = f"<b>{rule_name}</b><br/>{cleaned_message}"
        
        # Get the appropriate severity for badge
        display_severity = issue.severity
        if mode == "MQR" and issue.impacts:
            # For MQR mode, use impact severity for display
            for impact in issue.impacts:
                impact_severity = impact.get('severity', '')
                if impact_severity:
                    display_severity = impact_severity
                    break
        
        # Create a custom style for file paths
        file_path_style = ParagraphStyle(
            "FilePathStyle",
            parent=style_issue_meta,
            fontSize=8,  # Slightly smaller for paths
            wordWrap='LTR'  # Better word wrapping for long paths
        )
        
        # Add main issue row
        table_data.append([
            severity_badge(display_severity, mode),
            Paragraph(filename, file_path_style),
            Paragraph(rule_and_message, style_normal)
        ])
        
        # Add code snippet row if available
        if issue.code_snippet and issue.code_snippet.strip():
            # Create enhanced code style for better formatting
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
                borderPadding=8
            )
            
            # Enhanced code formatting with indentation preservation
            formatted_code = issue.code_snippet
            
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
            formatted_code = re.sub(r'(&gt;&gt;&gt;[^<]+)', r'<font color="red"><b>\1</b></font>', formatted_code)
            
            # Make line numbers slightly gray (but preserve their spacing)
            formatted_code = re.sub(r'(\s*)(\d+)(:)', r'\1<font color="gray">\2</font>\3', formatted_code)
            
            code_paragraph = Paragraph(
                f"<b><font color='darkblue'>📄 Problematic Code:</font></b><br/>"
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
        if (isinstance(row[1], str) and row[1] == "" and 
            isinstance(row[2], str) and row[2] == ""):
            # This is a code snippet row - first column has content, others are empty
            table_style.append(("BACKGROUND", (0, i), (-1, i), colors.Color(0.98, 0.98, 1.0)))  # Very light blue
            table_style.append(("SPAN", (0, i), (2, i)))  # Span from column 0 to 2
            table_style.append(("LEFTPADDING", (0, i), (0, i), 10))
            table_style.append(("RIGHTPADDING", (0, i), (0, i), 10))
            table_style.append(("TOPPADDING", (0, i), (0, i), 8))
            table_style.append(("BOTTOMPADDING", (0, i), (0, i), 8))
            # Add a subtle border around code snippet rows
            table_style.append(("BOX", (0, i), (2, i), 1, colors.Color(0.7, 0.7, 0.9)))
    
    table.setStyle(TableStyle(table_style))
    
    return table


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
        
        # Add sub-bookmarks for severities that have issues
        for severity in severity_list:
            count = severity_counts.get(severity, 0)
            if count > 0:
                summary_parts.append(f"{severity.title()}: {count}")
                # Add sub-bookmark for this severity level
                elements.append(BookmarkFlowable(f"{severity.title()} ({count})", 1))
        
        if summary_parts:
            summary_text = f"<b>Total: {len(issues)} issues</b> ({', '.join(summary_parts)})"
            elements.append(Paragraph(summary_text, style_issue_meta))
    else:
        elements.append(Paragraph("<b>Total: 0 issues</b>", style_issue_meta))
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(create_issue_table(issues, mode))
    elements.append(Spacer(1, 1*cm))


def generate_security_issues_page(report, elements, mode):
    """Generate Security issues section"""
    security_issues = get_issues_by_impact_category(report.issues, "SECURITY", mode)
    create_issue_section("Security Issues", security_issues, elements, mode)


def generate_reliability_issues_page(report, elements, mode):
    """Generate Reliability issues section"""
    reliability_issues = get_issues_by_impact_category(report.issues, "RELIABILITY", mode)
    create_issue_section("Reliability Issues", reliability_issues, elements, mode)


def generate_maintainability_issues_page(report, elements, mode):
    """Generate Maintainability issues section"""
    maintainability_issues = get_issues_by_impact_category(report.issues, "MAINTAINABILITY", mode)
    create_issue_section("Maintainability Issues", maintainability_issues, elements, mode)