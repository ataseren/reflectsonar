"""
Rules page generation for PDF reports - FIXED VERSION
"""
import re
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import cm
from .utils import style_section_title, style_normal, ParagraphStyle

def get_section_title(section_key: str) -> str:
    """Convert SonarQube section keys to readable titles"""
    section_titles = {
        'why': 'Why is this an issue?',
        'how_to_fix': 'How to fix it',
        'how_to_fix_it': 'How to fix it',
        'pitfalls': 'Pitfalls',
        'exceptions': 'Exceptions',
        'resources': 'Resources',
        'root_cause': 'Root cause',
        'assess_the_problem': 'Assess the problem',
        'introduction': 'Introduction',
        'noncompliant_code_example': 'Noncompliant Code Example',
        'compliant_solution': 'Compliant Solution',
        'see': 'See also',
        'recommended_secure_coding_practices': 'Recommended Secure Coding Practices'
    }
    return section_titles.get(section_key, section_key.replace('_', ' ').title())

def clean_html_content(content: str) -> str:
    """Clean HTML content for ReportLab paragraph parsing - FIXED to avoid \1 artifacts"""
    if not content:
        return ""
    
    try:
        # First, handle code blocks by extracting and formatting them properly
        def format_code_block(match):
            code_content = match.group(1)
            # Remove HTML tags from code content
            code_content = re.sub(r'<[^>]+>', '', code_content)
            # Format as code block with proper indentation
            lines = code_content.strip().split('\n')
            formatted_lines = []
            formatted_lines.append('<font name="Courier" size="9">')
            for line in lines:
                formatted_lines.append(f'    {line}')
            formatted_lines.append('</font>')
            return '<br/>'.join(formatted_lines)
        
        # Convert <pre> blocks to formatted code
        content = re.sub(r'<pre[^>]*>(.*?)</pre>', format_code_block, content, flags=re.DOTALL)
        
        # Convert inline <code> to monospace font
        def replace_inline_code(match):
            return f'<font name="Courier">{match.group(1)}</font>'
        content = re.sub(r'<code[^>]*>(.*?)</code>', replace_inline_code, content, flags=re.DOTALL)
        
        # Remove any HTML tags with complex attributes that cause issues
        content = re.sub(r'<[^>]*data-[^>]*>', '', content)
        
        # Convert HTML entities
        entity_map = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&nbsp;': ' ',
            '&#39;': "'",
            '&#34;': '"'
        }
        for entity, replacement in entity_map.items():
            content = content.replace(entity, replacement)
        
        # Handle lists by converting to bullet points
        content = re.sub(r'<ul[^>]*>', '<br/>', content)
        content = re.sub(r'</ul>', '<br/>', content)
        content = re.sub(r'<ol[^>]*>', '<br/>', content)
        content = re.sub(r'</ol>', '<br/>', content)
        
        def replace_list_item(match):
            return f'• {match.group(1)}<br/>'
        content = re.sub(r'<li[^>]*>(.*?)</li>', replace_list_item, content, flags=re.DOTALL)
        
        # Convert headings (but skip them since we handle section headings separately)
        def replace_heading(match):
            return f'<b>{match.group(1)}</b><br/>'
        content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', replace_heading, content, flags=re.DOTALL)
        
        # Convert paragraphs to text with line breaks
        def replace_paragraph(match):
            return f'{match.group(1)}<br/><br/>'
        content = re.sub(r'<p[^>]*>(.*?)</p>', replace_paragraph, content, flags=re.DOTALL)
        
        # Convert div elements
        def replace_div(match):
            return f'{match.group(1)}<br/>'
        content = re.sub(r'<div[^>]*>(.*?)</div>', replace_div, content, flags=re.DOTALL)
        
        # Convert strong/em tags
        def replace_strong(match):
            return f'<b>{match.group(1)}</b>'
        content = re.sub(r'<strong[^>]*>(.*?)</strong>', replace_strong, content, flags=re.DOTALL)
        
        def replace_em(match):
            return f'<i>{match.group(1)}</i>'
        content = re.sub(r'<em[^>]*>(.*?)</em>', replace_em, content, flags=re.DOTALL)
        
        # Handle links by keeping just the text
        def replace_link(match):
            return match.group(1)
        content = re.sub(r'<a[^>]*>(.*?)</a>', replace_link, content, flags=re.DOTALL)
        
        # Remove all remaining HTML tags except basic formatting and font
        content = re.sub(r'<(?!/?(?:b|i|u|br/?|font)\b)[^>]*>', '', content)
        
        # Clean up line breaks - replace <br> variants with standard <br/>
        content = re.sub(r'<br[^>]*>', '<br/>', content)
        
        # Clean up excessive line breaks
        content = re.sub(r'(<br/>[\s\n]*){3,}', '<br/><br/>', content)
        content = re.sub(r'[\n\r\t]+', ' ', content)
        
        # Clean up excessive whitespace
        content = re.sub(r' +', ' ', content)
        
        # Clean up leading/trailing content
        content = content.strip()
        content = re.sub(r'^(<br/>[\s]*)+', '', content)
        content = re.sub(r'(<br/>[\s]*)+$', '', content)
        
        # If content is too long, truncate but try to keep complete sentences
        if len(content) > 3000:
            truncate_pos = 2800
            for i in range(truncate_pos, min(len(content), truncate_pos + 200)):
                if content[i] in '.!?':
                    truncate_pos = i + 1
                    break
            content = content[:truncate_pos] + "<br/><i>[content truncated for brevity]</i>"
        
        return content
        
    except Exception:
        # If all HTML processing fails, return plain text
        plain_text = re.sub(r'<[^>]+>', '', content)
        return plain_text.strip()

def generate_rules_page(report, elements, verbose=False):
    """Generate Rules Reference section"""
    if verbose:
        print("🔧 Generating Rules Reference section...")
    
    try:
        elements.append(Paragraph("Rules Reference", style_section_title))
        elements.append(Spacer(1, 0.5*cm))
        
        if not report.rules:
            elements.append(Paragraph(
                "<i>No rule descriptions available.</i>", 
                style_normal
            ))
            return
        
        # Add introduction
        intro_text = f"This section contains descriptions for {len(report.rules)} rules found in the analysis. Each rule includes explanations of why issues occur and how to fix them."
        elements.append(Paragraph(intro_text, style_normal))
        elements.append(Spacer(1, 0.5*cm))
        
        # Create rule description style
        rule_title_style = ParagraphStyle(
            "RuleTitle",
            parent=style_normal,
            fontSize=12,
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.darkblue
        )
        
        rule_key_style = ParagraphStyle(
            "RuleKey", 
            parent=style_normal,
            fontSize=9,
            fontName="Courier",
            textColor=colors.grey,
            spaceBefore=3,
            spaceAfter=6
        )
        
        # Style for section headings within rules
        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=style_normal,
            fontSize=11,
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.darkred
        )
        
        # Sort rules by key for consistent ordering
        sorted_rules = sorted(report.rules.items())
        
        for rule_key, rule in sorted_rules:
            try:
                # Rule title
                elements.append(Paragraph(rule.name or rule_key, rule_title_style))
                
                # Rule key
                elements.append(Paragraph(f"Key: {rule_key}", rule_key_style))
                
                # Rule description sections
                if rule.description_sections:
                    sections_added = False
                    for section in rule.description_sections:
                        section_key = section.get('key', '')
                        content = section.get('content', '')
                        
                        if content:
                            # Add section heading
                            if section_key:
                                section_title = get_section_title(section_key)
                                elements.append(Paragraph(section_title, section_heading_style))
                            
                            # Clean HTML content to prevent parsing errors
                            cleaned_content = clean_html_content(content)
                            
                            if cleaned_content:
                                try:
                                    elements.append(Paragraph(cleaned_content, style_normal))
                                    sections_added = True
                                except Exception as parse_error:
                                    if verbose:
                                        print(f"Warning: HTML parsing failed for {rule_key}, section {section_key}: {parse_error}")
                                    # Fallback to plain text if HTML parsing still fails
                                    plain_text = re.sub(r'<[^>]+>', '', cleaned_content)
                                    if plain_text.strip():
                                        elements.append(Paragraph(plain_text, style_normal))
                                        sections_added = True
                                
                            elements.append(Spacer(1, 0.2*cm))
                    
                    # If no sections were successfully added, add a placeholder
                    if not sections_added:
                        elements.append(Paragraph("<i>Rule description could not be processed.</i>", style_normal))
                else:
                    # No description sections available
                    elements.append(Paragraph("<i>No detailed description available for this rule.</i>", style_normal))
                        
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not process rule {rule_key}: {e}")
                # Add minimal rule info if processing fails
                elements.append(Paragraph(f"Rule: {rule_key}", rule_key_style))
                elements.append(Paragraph("Description processing failed.", style_normal))
                        
            elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Spacer(1, 1*cm))
        
    except Exception as e:
        if verbose:
            print(f"Error generating rules page: {e}")
        # Add fallback message
        elements.append(Paragraph("Rules Reference", style_section_title))
        elements.append(Paragraph("Error loading rule descriptions.", style_normal))