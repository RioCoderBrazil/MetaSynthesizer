#!/usr/bin/env python3
"""
Check how colors are stored in the Word documents - might be highlighting or shading
"""

from docx import Document
from docx.shared import RGBColor
from collections import defaultdict
import sys

def check_document_colors(doc_path):
    """Check all possible color sources in a Word document"""
    
    doc = Document(doc_path)
    print(f"\nAnalyzing: {doc_path}")
    print("="*80)
    
    # Track different color sources
    font_colors = defaultdict(int)
    highlight_colors = defaultdict(int)
    shading_colors = defaultdict(int)
    
    for para in doc.paragraphs:
        # Check paragraph shading
        if para.paragraph_format and hasattr(para.paragraph_format, '_element'):
            pPr = para.paragraph_format._element
            shd = pPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd')
            if shd is not None and 'fill' in shd.attrib:
                fill = shd.attrib.get('fill', '')
                if fill and fill != 'auto':
                    shading_colors[fill] += len(para.text)
        
        for run in para.runs:
            # Check font color
            if run.font.color and run.font.color.rgb:
                try:
                    rgb = run.font.color.rgb
                    font_colors[str(rgb)] += len(run.text)
                except:
                    pass
            
            # Check highlight color
            if run.font.highlight_color:
                highlight_colors[str(run.font.highlight_color)] += len(run.text)
            
            # Check run shading
            if hasattr(run, '_element'):
                rPr = run._element.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
                if rPr is not None:
                    shd = rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd')
                    if shd is not None and 'fill' in shd.attrib:
                        fill = shd.attrib.get('fill', '')
                        if fill and fill != 'auto':
                            shading_colors[fill] += len(run.text)
    
    # Report findings
    print("\n1. FONT COLORS:")
    if font_colors:
        for color, count in sorted(font_colors.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {color}: {count} chars")
    else:
        print("   No font colors found")
    
    print("\n2. HIGHLIGHT COLORS:")
    if highlight_colors:
        for color, count in sorted(highlight_colors.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {color}: {count} chars")
    else:
        print("   No highlight colors found")
        
    print("\n3. SHADING/BACKGROUND COLORS:")
    if shading_colors:
        # Map hex colors to names
        color_names = {
            "00FF00": "GREEN (findings)",
            "C0C0C0": "GRAY (appendix)",
            "808080": "GRAY (appendix)",
            "00FFFF": "CYAN (wik)",
            "FFFF00": "YELLOW (introduction)",
            "0000FF": "BLUE (evaluation)",
            "FF00FF": "PINK (response)",
            "FFA500": "ORANGE (recommendations)",
            "FFD700": "GOLD (recommendations)"
        }
        
        for color, count in sorted(shading_colors.items(), key=lambda x: x[1], reverse=True):
            name = color_names.get(color.upper(), color)
            print(f"   {name}: {count} chars")
    else:
        print("   No shading colors found")

if __name__ == "__main__":
    # Check first document
    from pathlib import Path
    
    colored_dir = Path("01_colored_reports")
    doc_files = list(colored_dir.glob("*.docx"))[:3]  # Check first 3 docs
    
    for doc_file in doc_files:
        check_document_colors(doc_file)
