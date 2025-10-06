"""
Basic rules page generation for PDF reports
"""
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import cm
from .utils import style_section_title, style_normal, style_issue_title, style_section_key, style_rule_title


def generate_rules_page(report, elements, verbose=False):
    """Generate basic Rules Reference section with raw data printing"""
    if verbose:
        print("🔧 Generating basic Rules Reference section...")
    
    # Add section title
    elements.append(Paragraph("Rules Reference", style_section_title))
    elements.append(Spacer(1, 0.5*cm))
    
    # Check if we have rules data
    if not hasattr(report, 'rules') or not report.rules:
        elements.append(Paragraph("<i>No rule data available.</i>", style_normal))
        if verbose:
            print("   No rules found in report")
        return
    
    # Print raw data for debugging
    if verbose:
        print(f"   Found {len(report.rules)} rules:")
        for rule_key, rule in report.rules.items():
            print(f"   - {rule_key}: {rule.name}")
            print(f"     Description sections: {len(rule.description_sections)}")
            for i, section in enumerate(rule.description_sections):
                section_key = section.get('key', 'unknown')
                content_length = len(section.get('content', ''))
                print(f"       Section {i}: {section_key} ({content_length} chars)")
    
    # Add basic introduction
    intro_text = f"This section contains {len(report.rules)} rules found in the analysis."
    elements.append(Paragraph(intro_text, style_normal))
    elements.append(Spacer(1, 0.3*cm))
    
    # Add basic rule information (no complex parsing)
    for rule_key, rule in sorted(report.rules.items()):
        try:
            # Rule title - escape HTML special characters to prevent parsing issues
            rule_title = rule.name or rule_key
            # Escape HTML special characters that could interfere with markup
            escaped_title = (rule_title
                           .replace('&', '&amp;')
                           .replace('<', '&lt;')
                           .replace('>', '&gt;')
                           .replace('"', '&quot;')
                           .replace("'", '&#39;'))
            elements.append(Paragraph(f"<b>{escaped_title}</b>", style_rule_title))
            
            # Rule key
            elements.append(Paragraph(f"Key: {rule_key}", style_normal))
            
            # Rule description sections with content
            if rule.description_sections:
                
                # Display each section with its content
                for section in rule.description_sections:
                    section_key = section.get('key', 'unknown')
                    content = section.get('content', '')
                    
                    # Add section header
                    section_title = section_key.replace('_', ' ').title()
                    elements.append(Paragraph(f"{section_title}:", style_section_key))
                    
                    # Add section content (basic display without complex parsing)
                    if content:
                        import re
                        
                        # Handle newlines intelligently
                        safe_content = content
                        
                        # First, handle code blocks to preserve indentation
                        def format_code_block(match):
                            code_content = match.group(1)
                            # Preserve spaces by converting them to non-breaking spaces
                            lines = code_content.split('\n')
                            formatted_lines = []
                            for line in lines:
                                # Convert leading spaces to non-breaking spaces to preserve indentation
                                leading_spaces = len(line) - len(line.lstrip(' '))
                                if leading_spaces > 0:
                                    preserved_line = '&nbsp;' * leading_spaces + line.lstrip(' ')
                                else:
                                    preserved_line = line
                                formatted_lines.append(preserved_line)
                            
                            # Join lines and remove leading/trailing empty lines
                            formatted_code = '<br/>'.join(formatted_lines).strip()
                            return f'<font name="Courier" size="9">{formatted_code}</font>'
                        
                        # Handle <pre> and <code> blocks with indentation preservation
                        safe_content = re.sub(r'<pre[^>]*>(.*?)</pre>', format_code_block, safe_content, flags=re.DOTALL)
                        safe_content = re.sub(r'<code[^>]*>(.*?)</code>', format_code_block, safe_content, flags=re.DOTALL)
                        
                        # Clean up extra newlines around code blocks
                        safe_content = re.sub(r'<br/>\s*<font name="Courier"', '<font name="Courier"', safe_content)
                        safe_content = re.sub(r'</font>\s*<br/>', '</font>', safe_content)
                        
                        # Handle HTML headings before processing newlines
                        safe_content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'<b>\1</b><br/>', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        
                        # Handle different types of newlines:
                        # 1. Double newlines (paragraph breaks) -> double line breaks
                        safe_content = safe_content.replace('\n\n', '<br/><br/>')
                        
                        # 2. Newlines between words (word wrapping) -> spaces
                        # This handles cases like "wordhere\nwordhere" 
                        safe_content = re.sub(r'([a-zA-Z0-9])\n([a-zA-Z0-9])', r'\1 \2', safe_content)
                        
                        # 3. Remaining single newlines (sentence breaks) -> single line breaks
                        safe_content = safe_content.replace('\n', '<br/>')
                        
                        # Also handle escaped newlines
                        safe_content = safe_content.replace('\\n', ' ')
                        
                        # Handle HTML lists - convert to bullet points
                        # Remove list container tags and convert to line breaks
                        safe_content = re.sub(r'<ul[^>]*>', '<br/>', safe_content, flags=re.IGNORECASE)
                        safe_content = re.sub(r'</ul>', '<br/>', safe_content, flags=re.IGNORECASE)
                        safe_content = re.sub(r'<ol[^>]*>', '<br/>', safe_content, flags=re.IGNORECASE)
                        safe_content = re.sub(r'</ol>', '<br/>', safe_content, flags=re.IGNORECASE)
                        
                        # Convert list items to bullet points
                        safe_content = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1<br/>', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        
                        # Handle other common HTML elements
                        safe_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1<br/><br/>', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        safe_content = re.sub(r'<br[^>]*>', '<br/>', safe_content, flags=re.IGNORECASE)
                        safe_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'<b>\1</b>', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        safe_content = re.sub(r'<em[^>]*>(.*?)</em>', r'<i>\1</i>', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        
                        # Convert anchor tags to ReportLab clickable links (blue and underlined)
                        def convert_link(match):
                            href = re.search(r'href=["\']([^"\'>]+)["\']', match.group(0))
                            link_text = match.group(1)
                            if href:
                                url = href.group(1)
                                return f'<link href="{url}" color="blue"><u>{link_text}</u></link>'
                            else:
                                # If no href found, just return the text
                                return link_text
                        
                        safe_content = re.sub(r'<a[^>]*>(.*?)</a>', convert_link, safe_content, flags=re.IGNORECASE | re.DOTALL)
                        
                        # Clean up any remaining broken anchor tags
                        safe_content = re.sub(r'<a[^>]*(?!>)', '', safe_content, flags=re.IGNORECASE)
                        safe_content = re.sub(r'</a>', '', safe_content, flags=re.IGNORECASE)
                        
                        # Remove other potentially problematic tags but keep content
                        safe_content = re.sub(r'<para[^>]*>(.*?)</para>', r'\1', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        safe_content = re.sub(r'<div[^>]*>(.*?)</div>', r'\1', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        safe_content = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', safe_content, flags=re.IGNORECASE | re.DOTALL)
                        
                        # Remove any remaining unsupported HTML tags but keep content
                        # Allow: b, i, u, br, font, link tags
                        safe_content = re.sub(r'<(?!/?(?:b|i|u|br/?|font|link)\b)[^>]*>', '', safe_content, flags=re.IGNORECASE)
                        
                        # Clean up excessive line breaks
                        safe_content = re.sub(r'(<br/>){3,}', '<br/><br/>', safe_content)
                        safe_content = safe_content.strip()
                        
                        # Remove leading/trailing line breaks
                        safe_content = re.sub(r'^(<br/>)+', '', safe_content)
                        safe_content = re.sub(r'(<br/>)+$', '', safe_content)
                        
                        # Try to create paragraph with HTML parsing, fallback to plain text if it fails
                        try:
                            elements.append(Paragraph(safe_content, style_normal))
                        except Exception as parse_error:
                            if verbose:
                                print(f"   Warning: HTML parsing failed for section '{section_key}': {parse_error}")
                            # Fallback: strip all HTML and use plain text
                            plain_content = re.sub(r'<[^>]+>', '', safe_content)
                            plain_content = plain_content.replace('&nbsp;', ' ')
                            plain_content = re.sub(r'\s+', ' ', plain_content).strip()
                            if plain_content:
                                elements.append(Paragraph(plain_content, style_normal))
                            else:
                                elements.append(Paragraph("<i>Content could not be processed</i>", style_normal))
                    else:
                        elements.append(Paragraph("<i>No content available</i>", style_normal))
                    
                    elements.append(Spacer(1, 0.1*cm))
            else:
                elements.append(Paragraph("No description sections available.", style_normal))
            
            elements.append(Spacer(1, 0.2*cm))
            
        except Exception as e:
            if verbose:
                print(f"   Error processing rule {rule_key}: {e}")
            # Add minimal fallback
            elements.append(Paragraph(f"Rule: {rule_key} (processing error)", style_normal))
            elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Spacer(1, 0.5*cm))
