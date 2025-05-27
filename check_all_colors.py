#!/usr/bin/env python3
"""
Check all color mappings across all documents
"""

import json
from pathlib import Path
from collections import defaultdict

def check_colors():
    chunks_dir = Path("02_chunked_data")
    
    # Get all sections files
    section_files = sorted(chunks_dir.glob("*_sections.json"))
    
    print("="*100)
    print("COLOR ANALYSIS ACROSS ALL DOCUMENTS")
    print("="*100)
    print()
    
    all_colors = defaultdict(int)
    missing_green = []
    missing_gray = []
    
    for section_file in section_files:
        with open(section_file, 'r', encoding='utf-8') as f:
            sections = json.load(f)
        
        doc_colors = set()
        for section in sections:
            color = tuple(section['color_rgb'])
            doc_colors.add(color)
            all_colors[color] += 1
        
        doc_name = section_file.stem.replace('_sections', '')
        
        # Check for green (0,255,0) - findings
        has_green = (0, 255, 0) in doc_colors
        # Check for gray (128,128,128) or similar
        has_gray = any(c[0] == c[1] == c[2] and 100 < c[0] < 200 for c in doc_colors)
        
        if not has_green:
            missing_green.append(doc_name)
        if not has_gray:
            missing_gray.append(doc_name)
            
    print("COLORS FOUND ACROSS ALL DOCUMENTS:")
    print("-" * 50)
    color_names = {
        (0, 255, 255): "Cyan (wik)",
        (255, 255, 0): "Yellow (introduction)", 
        (0, 0, 255): "Blue (evaluation)",
        (255, 0, 255): "Pink/Magenta (response)",
        (0, 255, 0): "GREEN (findings)",
        (128, 128, 128): "GRAY (annex)"
    }
    
    for color, count in sorted(all_colors.items()):
        name = color_names.get(color, "Unknown")
        print(f"RGB {color}: {name:30} - Found in {count} sections")
    
    print()
    print("="*100)
    print("MISSING COLORS REPORT:")
    print("="*100)
    
    print(f"\n🟢 Documents WITHOUT GREEN (findings): {len(missing_green)}/{len(section_files)}")
    if len(missing_green) == len(section_files):
        print("   ❌ ALL DOCUMENTS ARE MISSING GREEN SECTIONS!")
    
    print(f"\n⚫ Documents WITHOUT GRAY (annex): {len(missing_gray)}/{len(section_files)}")
    if len(missing_gray) == len(section_files):
        print("   ❌ ALL DOCUMENTS ARE MISSING GRAY SECTIONS!")
    
    # Check original PDFs
    print()
    print("="*100)
    print("CHECKING FOR ORIGINAL COLOR-CODED PDFs:")
    print("="*100)
    
    # Look for PDFs with color coding in filename
    pdf_dir = Path(".")
    color_pdfs = list(pdf_dir.rglob("*farb*coded*.pdf")) + list(pdf_dir.rglob("*color*coded*.pdf")) + list(pdf_dir.rglob("*colour*coded*.pdf"))
    
    if color_pdfs:
        print(f"\nFound {len(color_pdfs)} color-coded PDFs:")
        for pdf in color_pdfs[:5]:
            print(f"  • {pdf}")
    else:
        print("\n❌ No color-coded PDFs found in the project!")

if __name__ == "__main__":
    check_colors()
