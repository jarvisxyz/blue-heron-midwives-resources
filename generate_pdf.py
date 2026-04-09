#!/usr/bin/env python3

# PDF Generator for Blue Heron Midwives Resources
# Install dependencies: pip install markdown reportlab

import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf(input_md, output_pdf):
    '''Convert markdown to PDF'''
    
    # Read markdown content
    with open(input_md, 'r') as f:
        md_content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#34495e')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph("Blue Heron Midwives - Connecting Pregnancy Program Resources", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Process markdown and convert to PDF elements
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # Simple conversion (for full markdown support, use more advanced parser)
    lines = md_content.split('\n')
    for line in lines:
        if line.startswith('## '):
            story.append(Paragraph(line[3:], heading_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], heading_style))
        elif line.strip() and not line.startswith('#'):
            story.append(Paragraph(line, normal_style))
        elif line.strip() == '':
            story.append(Spacer(1, 0.1*inch))
    
    doc.build(story)
    print(f"PDF created: {output_pdf}")

if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    base_dir = Path('/tmp/bhm_resources')
    input_file = base_dir / 'COMPREHENSIVE_GUIDE.md'
    output_file = base_dir / 'COMPREHENSIVE_GUIDE.pdf'
    
    if input_file.exists():
        generate_pdf(str(input_file), str(output_file))
    else:
        print(f"Input file not found: {input_file}")
