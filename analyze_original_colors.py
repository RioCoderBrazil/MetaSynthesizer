#!/usr/bin/env python3
"""
Analyze the original colored Word document to understand what was lost
"""

from docx import Document
from collections import Counter
import sys

def analyze_original_doc(doc_path):
    try:
        doc = Document(doc_path)
        
        print(f"ANALYZING: {doc_path}")
        print("="*80)
        
        color_counter = Counter()
        text_by_color = {}
        
        for para in doc.paragraphs:
            for run in para.runs:
                if run.font.color and run.font.color.rgb:
                    # Get RGB values properly
                    rgb_obj = run.font.color.rgb
                    # RGBColor object has attributes
                    if hasattr(rgb_obj, '__iter__'):
                        color = tuple(rgb_obj)
                    else:
                        # Try to extract RGB values
                        color = (0, 0, 0)  # Default
                    
                    color_counter[color] += len(run.text)
                    
                    if color not in text_by_color:
                        text_by_color[color] = []
                    
                    if run.text.strip() and len(text_by_color[color]) < 3:
                        text_by_color[color].append(run.text.strip()[:100])
        
        print("COLORS FOUND (RGB -> character count):")
        print("-"*50)
        
        color_names = {
            (0, 255, 255): "CYAN (wik)",
            (255, 255, 0): "YELLOW (introduction)",
            (0, 0, 255): "BLUE (evaluation)",
            (255, 0, 255): "PINK (response)",
            (0, 255, 0): "GREEN (findings)",
            (128, 128, 128): "GRAY (annex)",
            (192, 192, 192): "LIGHT GRAY (annex variant)"
        }
        
        total_chars = sum(color_counter.values())
        
        for color, count in color_counter.most_common():
            name = color_names.get(color, f"Unknown {color}")
            percentage = (count / total_chars * 100) if total_chars > 0 else 0
            print(f"  {name:40}: {count:8,} chars ({percentage:5.1f}%)")
        
        # Show sample texts
        print("\n" + "="*80)
        print("SAMPLE TEXTS BY COLOR:")
        print("="*80)
        
        for color, samples in text_by_color.items():
            name = color_names.get(color, f"Unknown {color}")
            print(f"\n{name}:")
            for i, sample in enumerate(samples[:2], 1):
                print(f"  {i}. \"{sample}...\"")
                
    except Exception as e:
        print(f"Error analyzing document: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check the original colored document
    doc_path = "01_colored_reports/22723BE Prüfbericht V04 - DOC - Prüfung der Investitionsplanung  - farbcoded.docx"
    analyze_original_doc(doc_path)
