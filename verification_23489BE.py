#!/usr/bin/env python3
"""
Create a readable, ordered verification document for 23489BE
Shows all sections in proper order with clear labels and statistics
"""

import json
from pathlib import Path
from collections import defaultdict

def create_verification_document():
    """Create a text file showing the complete flow of document 23489BE"""
    
    # Load the highlighted sections (the complete data)
    sections_file = Path("02_chunked_data_highlighted/23489BE Prüfbericht V03 - Querschnittsprüfung des Umgangs des Bundes mit problematischen Stoffen - coloured_highlighted_sections.json")
    
    if not sections_file.exists():
        print(f"Error: {sections_file} not found!")
        return
    
    with open(sections_file, 'r', encoding='utf-8') as f:
        sections = json.load(f)
    
    # Create output file
    output_file = Path("23489BE_VERIFICATION_REPORT.txt")
    
    # Label descriptions in German and English
    label_descriptions = {
        'findings': 'FESTSTELLUNGEN / FINDINGS (GREEN)',
        'appendix': 'ANHANG / APPENDIX (GRAY)', 
        'wik': 'WESENTLICHES IN KÜRZE / EXECUTIVE SUMMARY (CYAN)',
        'introduction': 'AUFTRAG UND VORGEHEN / INTRODUCTION (YELLOW)',
        'evaluation': 'BEURTEILUNG DER EFK / EVALUATION (BLUE)',
        'response': 'STELLUNGNAHME / RESPONSE (PINK)',
        'recommendations': 'EMPFEHLUNGEN / RECOMMENDATIONS (DARK YELLOW)'
    }
    
    # Calculate statistics
    label_stats = defaultdict(int)
    label_sections = defaultdict(list)
    
    for section in sections:
        label = section['label']
        label_stats[label] += len(section['text'])
        label_sections[label].append(section)
    
    total_chars = sum(label_stats.values())
    
    # Write verification report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("VERIFICATION REPORT FOR DOCUMENT 23489BE\n")
        f.write("Prüfbericht V03 - Querschnittsprüfung des Umgangs des Bundes mit problematischen Stoffen\n")
        f.write("="*100 + "\n\n")
        
        # Statistics overview
        f.write("DOCUMENT STATISTICS:\n")
        f.write("-"*50 + "\n")
        for label, char_count in sorted(label_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (char_count / total_chars * 100) if total_chars > 0 else 0
            desc = label_descriptions.get(label, label)
            f.write(f"{desc:60}: {char_count:8,} chars ({percentage:5.1f}%)\n")
        
        f.write(f"\nTOTAL CHARACTERS: {total_chars:,}\n")
        
        # Special highlights
        f.write("\n" + "="*100 + "\n")
        f.write("IMPORTANT FINDINGS:\n")
        f.write("-"*50 + "\n")
        
        if label_stats['findings'] > 0:
            findings_pct = (label_stats['findings'] / total_chars * 100)
            f.write(f"✓ GREEN (FINDINGS) SECTIONS FOUND: {label_stats['findings']:,} chars ({findings_pct:.1f}%)\n")
            f.write(f"  - Number of findings sections: {len(label_sections['findings'])}\n")
        else:
            f.write("❌ NO GREEN (FINDINGS) SECTIONS FOUND!\n")
            
        if label_stats['appendix'] > 0:
            appendix_pct = (label_stats['appendix'] / total_chars * 100)
            f.write(f"✓ GRAY (APPENDIX) SECTIONS FOUND: {label_stats['appendix']:,} chars ({appendix_pct:.1f}%)\n")
            f.write(f"  - Number of appendix sections: {len(label_sections['appendix'])}\n")
        else:
            f.write("❌ NO GRAY (APPENDIX) SECTIONS FOUND!\n")
        
        # Document flow in logical order
        f.write("\n" + "="*100 + "\n")
        f.write("DOCUMENT CONTENT IN LOGICAL ORDER:\n")
        f.write("="*100 + "\n")
        
        # Order sections should appear
        section_order = ['wik', 'introduction', 'findings', 'evaluation', 'recommendations', 'response', 'appendix']
        
        for label in section_order:
            if label in label_sections and label_sections[label]:
                f.write("\n" + "="*80 + "\n")
                f.write(f"{label_descriptions.get(label, label)}\n")
                f.write(f"Total: {label_stats[label]:,} characters in {len(label_sections[label])} sections\n")
                f.write("="*80 + "\n\n")
                
                # Sort sections by page number
                sorted_sections = sorted(label_sections[label], key=lambda s: s['start_page'])
                
                for i, section in enumerate(sorted_sections, 1):
                    f.write(f"--- Section {i} (Pages {section['start_page']}-{section['end_page']}) ---\n")
                    
                    # Show first 500 chars and last 200 chars if section is long
                    text = section['text'].strip()
                    if len(text) > 800:
                        f.write(text[:500])
                        f.write("\n\n[... MIDDLE CONTENT TRUNCATED FOR READABILITY ...]\n\n")
                        f.write(text[-200:])
                    else:
                        f.write(text)
                    
                    f.write(f"\n\n[End of section {i}]\n\n")
        
        # Summary at the end
        f.write("\n" + "="*100 + "\n")
        f.write("VERIFICATION SUMMARY:\n")
        f.write("="*100 + "\n")
        f.write(f"Total sections processed: {len(sections)}\n")
        f.write(f"Unique labels found: {sorted(label_stats.keys())}\n")
        f.write("\nThis document shows the complete content flow with all colored sections properly extracted.\n")
        f.write("Compare this with your original document to verify completeness.\n")
    
    print(f"✓ Verification report created: {output_file}")
    return output_file

if __name__ == "__main__":
    create_verification_document()
