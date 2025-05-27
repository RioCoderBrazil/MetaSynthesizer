#!/usr/bin/env python3
"""
Extract text from Word documents based on HIGHLIGHT COLOR.
This properly captures all colored sections including GREEN (findings) and GRAY (annex).
"""

import json
from pathlib import Path
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from collections import defaultdict
import sys

def highlight_to_label(highlight_color):
    """Map Word highlight colors to our labels"""
    
    # Word highlight color mapping
    # Based on the output: BRIGHT_GREEN (4), TURQUOISE (3), YELLOW (7), BLUE (2), PINK (5)
    highlight_map = {
        WD_COLOR_INDEX.BRIGHT_GREEN: "findings",      # GREEN - Main findings (the biggest part!)
        WD_COLOR_INDEX.GRAY_25: "appendix",           # GRAY - Annex sections  
        WD_COLOR_INDEX.GRAY_50: "appendix",           # GRAY variant
        WD_COLOR_INDEX.TURQUOISE: "wik",             # CYAN - Executive summary
        WD_COLOR_INDEX.YELLOW: "introduction",        # YELLOW - Introduction
        WD_COLOR_INDEX.BLUE: "evaluation",            # BLUE - Evaluation
        WD_COLOR_INDEX.PINK: "response",              # PINK - Response
        WD_COLOR_INDEX.RED: "recommendations",        # RED - Recommendations (might be used)
        WD_COLOR_INDEX.DARK_YELLOW: "recommendations", # DARK YELLOW - Recommendations
        
        # Numeric values (in case enum doesn't match)
        4: "findings",      # BRIGHT_GREEN
        3: "wik",          # TURQUOISE
        7: "introduction",  # YELLOW
        2: "evaluation",    # BLUE
        5: "response",      # PINK
        15: "appendix",     # GRAY_25
        16: "appendix",     # GRAY_50
    }
    
    # Try both enum and numeric lookup
    label = highlight_map.get(highlight_color, None)
    if label is None and hasattr(highlight_color, 'value'):
        label = highlight_map.get(highlight_color.value, None)
    
    return label or "unknown"

def extract_highlighted_sections(doc_path):
    """Extract all text sections with their highlight colors from a Word document"""
    try:
        doc = Document(doc_path)
        
        sections = []
        current_section = None
        page_num = 1
        
        print(f"\nProcessing: {doc_path.name}")
        print("-" * 80)
        
        color_stats = defaultdict(int)
        label_stats = defaultdict(int)
        
        for para_idx, para in enumerate(doc.paragraphs):
            # Track page breaks (approximate)
            if para_idx > 0 and para_idx % 30 == 0:
                page_num += 1
            
            para_text = para.text.strip()
            if not para_text:
                continue
                
            # Check all runs in the paragraph for highlight color
            for run in para.runs:
                if not run.text.strip():
                    continue
                    
                # Get the highlight color of this run
                highlight = run.font.highlight_color
                label = "unknown"
                
                if highlight:
                    label = highlight_to_label(highlight)
                    color_stats[str(highlight)] += len(run.text)
                    label_stats[label] += len(run.text)
                
                # Create or extend section
                if current_section and current_section['label'] == label and current_section['end_page'] >= page_num - 1:
                    # Extend current section
                    current_section['text'] += '\n' + run.text
                    current_section['end_page'] = page_num
                else:
                    # Start new section
                    if current_section and current_section['label'] != "unknown":
                        sections.append(current_section)
                    
                    if label != "unknown":  # Only create sections for highlighted text
                        # Map to RGB colors for consistency
                        color_rgb_map = {
                            "findings": [0, 255, 0],      # GREEN
                            "appendix": [128, 128, 128],  # GRAY
                            "wik": [0, 255, 255],         # CYAN
                            "introduction": [255, 255, 0], # YELLOW
                            "evaluation": [0, 0, 255],     # BLUE
                            "response": [255, 0, 255],     # PINK
                            "recommendations": [255, 215, 0], # GOLD
                        }
                        
                        current_section = {
                            'label': label,
                            'text': run.text,
                            'start_page': page_num,
                            'end_page': page_num,
                            'confidence': 1.0,
                            'color_rgb': color_rgb_map.get(label, [0, 0, 0]),
                            'highlight_color': str(highlight)
                        }
        
        # Add final section
        if current_section and current_section['label'] != "unknown":
            sections.append(current_section)
        
        # Print color statistics
        print("\nHIGHLIGHT COLOR STATISTICS:")
        total_chars = sum(color_stats.values())
        for color, char_count in sorted(color_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (char_count / total_chars * 100) if total_chars > 0 else 0
            print(f"  {color:20}: {char_count:8,} chars ({percentage:5.1f}%)")
        
        print("\nLABEL STATISTICS:")
        for label, char_count in sorted(label_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (char_count / total_chars * 100) if total_chars > 0 else 0
            status = "✓" if char_count > 0 else "❌"
            print(f"{status} {label:15}: {char_count:8,} chars ({percentage:5.1f}%)")
        
        # Check for important labels
        if label_stats.get("findings", 0) > 0:
            print(f"\n✓ GREEN/findings found: {label_stats['findings']:,} characters")
        else:
            print("\n❌ NO findings sections found!")
            
        if label_stats.get("appendix", 0) > 0:
            print(f"✓ GRAY/appendix found: {label_stats['appendix']:,} characters")
        else:
            print("❌ NO appendix sections found!")
        
        return sections
        
    except Exception as e:
        print(f"Error processing {doc_path}: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_all_documents():
    """Process all colored documents and create new chunk files with proper labeling"""
    
    colored_dir = Path("01_colored_reports")
    output_dir = Path("02_chunked_data_highlighted")
    output_dir.mkdir(exist_ok=True)
    
    # Get all colored Word documents
    doc_files = list(colored_dir.glob("*.docx"))
    
    print(f"Found {len(doc_files)} colored documents to process")
    print("=" * 80)
    
    all_stats = defaultdict(int)
    docs_with_findings = 0
    docs_with_appendix = 0
    
    for doc_file in doc_files:
        sections = extract_highlighted_sections(doc_file)
        
        if sections:
            # Save sections file
            output_file = output_dir / f"{doc_file.stem}_highlighted_sections.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"  → Saved {len(sections)} sections to {output_file.name}")
            
            # Check what this doc has
            doc_labels = {s['label'] for s in sections}
            if 'findings' in doc_labels:
                docs_with_findings += 1
            if 'appendix' in doc_labels:
                docs_with_appendix += 1
            
            # Update statistics
            for section in sections:
                all_stats[section['label']] += len(section['text'])
            
            # Also create chunks (split long sections)
            chunks = []
            chunk_id = 0
            
            for section in sections:
                text = section['text']
                # Split into chunks of ~500 characters
                chunk_size = 500
                
                for i in range(0, len(text), chunk_size):
                    chunk_text = text[i:i+chunk_size]
                    if chunk_text.strip():
                        chunks.append({
                            'chunk_id': f"{doc_file.stem}_chunk_{chunk_id}",
                            'text': chunk_text,
                            'label': section['label'],
                            'start_page': section['start_page'],
                            'end_page': section['end_page'],
                            'color_rgb': section['color_rgb']
                        })
                        chunk_id += 1
            
            # Save chunks file
            chunks_file = output_dir / f"{doc_file.stem}_highlighted_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
                
            print(f"  → Saved {len(chunks)} chunks to {chunks_file.name}")
    
    # Print overall statistics
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS ACROSS ALL DOCUMENTS:")
    print("=" * 80)
    
    total_chars = sum(all_stats.values())
    for label, char_count in sorted(all_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (char_count / total_chars * 100) if total_chars > 0 else 0
        status = "✓" if char_count > 0 else "❌"
        print(f"{status} {label:15}: {char_count:10,} chars ({percentage:5.1f}%)")
    
    print("\n" + "=" * 80)
    print(f"Documents with findings (GREEN): {docs_with_findings}/{len(doc_files)}")
    print(f"Documents with appendix (GRAY): {docs_with_appendix}/{len(doc_files)}")
    
    if all_stats['findings'] > 0:
        print(f"\n✓ SUCCESS: Found {all_stats['findings']:,} characters of GREEN (findings) content!")
    else:
        print("\n⚠️  WARNING: No findings sections found in any document!")
        
    if docs_with_appendix == 0:
        print("\n⚠️  Note: No GRAY (appendix) sections found - they might not be highlighted in gray")

if __name__ == "__main__":
    process_all_documents()
