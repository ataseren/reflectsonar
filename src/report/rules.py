"""
Rules page generation for PDF reports
"""

import re
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import cm
from .utils import style_section_title, style_normal


def escape_html_for_reportlab(text):
    """Escape HTML characters to prevent ReportLab parsing issues"""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def get_section_title(section_key):
    """Convert SonarQube section keys to readable titles"""
    section_titles = {
        "why": "Why is this an issue?",
        "how_to_fix": "How to fix it",
        "how_to_fix_it": "How to fix it",
        "pitfalls": "Pitfalls",
        "exceptions": "Exceptions",
        "resources": "Resources",
        "more_info": "More Information",
        "root_cause": "Root cause",
        "assess_the_problem": "Assess the problem",
        "introduction": "Introduction",
        "noncompliant_code_example": "Noncompliant Code Example",
        "compliant_solution": "Compliant Solution",
        "see": "See also",
        "recommended_secure_coding_practices": "Recommended Secure Coding Practices",
    }
    return section_titles.get(section_key, section_key.replace("_", " ").title())


def process_html_content(html_content):
    """Process HTML content for ReportLab display with code formatting"""
    if not html_content:
        return "No content available"

    content = html_content

    # Handle code blocks - extract and format them
    def format_code_block(match):
        code_content = match.group(1)
        # Remove HTML tags from code content
        clean_code = re.sub(r"<[^>]+>", "", code_content)
        # Format with monospace font
        return f'<font name="Courier" size="9">{escape_html_for_reportlab(clean_code.strip())}</font>'

    # Convert <pre> blocks to formatted code
    content = re.sub(
        r"<pre[^>]*>(.*?)</pre>", format_code_block, content, flags=re.DOTALL
    )

    # Handle inline code
    def format_inline_code(match):
        code_text = match.group(1)
        return f'<font name="Courier">{escape_html_for_reportlab(code_text)}</font>'

    content = re.sub(
        r"<code[^>]*>(.*?)</code>", format_inline_code, content, flags=re.DOTALL
    )

    # Convert other HTML elements
    content = re.sub(
        r"<h[1-6][^>]*>(.*?)</h[1-6]>",
        lambda m: f"<b>{escape_html_for_reportlab(m.group(1))}</b><br/>",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"<p[^>]*>(.*?)</p>",
        lambda m: f"{process_paragraph_content(m.group(1))}<br/><br/>",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"<strong[^>]*>(.*?)</strong>",
        lambda m: f"<b>{escape_html_for_reportlab(m.group(1))}</b>",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"<em[^>]*>(.*?)</em>",
        lambda m: f"<i>{escape_html_for_reportlab(m.group(1))}</i>",
        content,
        flags=re.DOTALL,
    )

    # Handle lists
    content = re.sub(r"<ul[^>]*>", "<br/>", content)
    content = re.sub(r"</ul>", "<br/>", content)
    content = re.sub(
        r"<li[^>]*>(.*?)</li>",
        lambda m: f"• {escape_html_for_reportlab(m.group(1))}<br/>",
        content,
        flags=re.DOTALL,
    )

    # Remove remaining HTML tags
    content = re.sub(r"<(?!/?(?:b|i|u|br|font)\b)[^>]*>", "", content)

    # Clean up line breaks
    content = re.sub(r"(<br/>\s*){3,}", "<br/><br/>", content)
    content = re.sub(r"\s+", " ", content)

    return content.strip()


def process_paragraph_content(p_content):
    """Process content within paragraph tags"""
    # Handle nested tags within paragraphs
    content = p_content
    content = re.sub(
        r"<strong[^>]*>(.*?)</strong>",
        lambda m: f"<b>{escape_html_for_reportlab(m.group(1))}</b>",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"<em[^>]*>(.*?)</em>",
        lambda m: f"<i>{escape_html_for_reportlab(m.group(1))}</i>",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"<code[^>]*>(.*?)</code>",
        lambda m: f'<font name="Courier">{escape_html_for_reportlab(m.group(1))}</font>',
        content,
        flags=re.DOTALL,
    )

    # Remove other HTML tags and escape content
    content = re.sub(r"<[^>]+>", "", content)
    return escape_html_for_reportlab(content)


def generate_rules_page(report, elements, verbose=False):
    """Generate a basic Rules Reference section"""
    if verbose:
        print("Generating Rules Reference section...")

    # Add page title
    elements.append(Paragraph("Rules Reference", style_section_title))
    elements.append(Spacer(1, 0.5 * cm))

    # Check if we have any rules
    if not report.rules:
        elements.append(
            Paragraph("<i>No rule descriptions available.</i>", style_normal)
        )
        return

    # Add basic introduction
    intro_text = (
        f"This section contains {len(report.rules)} rules found in the analysis."
    )
    elements.append(Paragraph(intro_text, style_normal))
    elements.append(Spacer(1, 0.5 * cm))

    # List each rule with basic information
    for rule_key, rule in sorted(report.rules.items()):
        # Rule name - escape HTML characters to prevent parsing issues
        rule_name = rule.name if rule.name else rule_key
        escaped_rule_name = escape_html_for_reportlab(rule_name)

        elements.append(Paragraph(f"<b>{escaped_rule_name}</b>", style_normal))

        # Rule key - also escape in case it contains HTML-like content
        escaped_rule_key = escape_html_for_reportlab(rule_key)
        elements.append(Paragraph(f"Key: {escaped_rule_key}", style_normal))

        # Process all description sections
        if rule.description_sections:
            for section in rule.description_sections:
                section_key = section.get("key", "")
                section_content = section.get("content", "")

                if section_content:
                    # Add section heading
                    if section_key:
                        section_title = get_section_title(section_key)
                        elements.append(
                            Paragraph(f"<b><i>{section_title}</i></b>", style_normal)
                        )

                    # Process and add content
                    processed_content = escape_html_for_reportlab(section_content)

                    if (
                        processed_content
                        and processed_content != "No content available"
                    ):
                        try:
                            elements.append(Paragraph(processed_content, style_normal))
                        except Exception:
                            # Fallback to plain text
                            plain_text = re.sub(r"<[^>]+>", "", processed_content)
                            if plain_text.strip():
                                elements.append(
                                    Paragraph(
                                        escape_html_for_reportlab(plain_text),
                                        style_normal,
                                    )
                                )

                    elements.append(Spacer(1, 0.2 * cm))
        else:
            elements.append(
                Paragraph("<i>No description sections available</i>", style_normal)
            )

        elements.append(Spacer(1, 0.3 * cm))

    elements.append(Spacer(1, 1 * cm))
