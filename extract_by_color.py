#!/usr/bin/env python3
"""
Extract text from Word documents based on actual COLOR, not text patterns.
This will capture ALL colored sections including GREEN (findings) and GRAY (annex).
"""

import json
from pathlib import Path
from docx import Document
from docx.shared import RGBColor
from collections import defaultdict
import sys

def rgb_to_hex(r, g, b):
    """Convert RGB to hex color"""
    return f"#{r:02x}{g:02x}{b:02x}".upper()

def extract_color_sections(doc_path):
    """Extract all text sections with their colors from a Word document"""
    try:
        doc = Document(doc_path)
        
        # Color mapping based on your requirements
        color_to_label = {
            "#00FF00": "findings",      # GREEN - Main findings (the biggest part)
            "#808080": "appendix",      # GRAY - Annex sections
            "#C0C0C0": "appendix",      # Light gray variant
            "#696969": "appendix",      # Dark gray variant
            "#00FFFF": "wik",          # CYAN - Executive summary
            "#FFFF00": "introduction",  # YELLOW - Introduction
            "#0000FF": "evaluation",    # BLUE - Evaluation
            "#FF00FF": "response",      # PINK/MAGENTA - Response
            "#FFA500": "recommendations", # ORANGE - Recommendations
            "#FFD700": "recommendations", # GOLD/DARK YELLOW - Recommendations
            "#FF8C00": "recommendations", # DARK ORANGE - Recommendations
        }
        
        sections = []
        current_section = None
        page_num = 1
        
        print(f"\nProcessing: {doc_path.name}")
        print("-" * 80)
        
        color_stats = defaultdict(int)
        
        for para_idx, para in enumerate(doc.paragraphs):
            # Track page breaks (approximate)
            if para_idx > 0 and para_idx % 30 == 0:
                page_num += 1
            
            para_text = para.text.strip()
            if not para_text:
                continue
                
            # Check all runs in the paragraph for color
            for run in para.runs:
                if not run.text.strip():
                    continue
                    
                # Get the color of this run
                color_hex = "#000000"  # Default black
                
                if run.font.color and run.font.color.rgb:
                    try:
                        rgb = run.font.color.rgb
                        # Handle different RGBColor formats
                        if hasattr(rgb, 'r') and hasattr(rgb, 'g') and hasattr(rgb, 'b'):
                            r, g, b = rgb.r, rgb.g, rgb.b
                        elif isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
                            r, g, b = rgb[0], rgb[1], rgb[2]
                        else:
                            # Try to extract from integer representation
                            rgb_int = int(str(rgb), 16) if isinstance(rgb, str) else rgb
                            r = (rgb_int >> 16) & 0xff
                            g = (rgb_int >> 8) & 0xff
                            b = rgb_int & 0xff
                        
                        color_hex = rgb_to_hex(r, g, b)
                    except:
                        pass
                
                # Map color to label
                label = color_to_label.get(color_hex, "unknown")
                
                # Count characters by color
                color_stats[color_hex] += len(run.text)
                
                # Create or extend section
                if current_section and current_section['label'] == label and current_section['end_page'] >= page_num - 1:
                    # Extend current section
                    current_section['text'] += '\n' + run.text
                    current_section['end_page'] = page_num
                else:
                    # Start new section
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = {
                        'label': label,
                        'text': run.text,
                        'start_page': page_num,
                        'end_page': page_num,
                        'confidence': 1.0,
                        'color_rgb': [int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)],
                        'color_hex': color_hex
                    }
        
        # Add final section
        if current_section:
            sections.append(current_section)
        
        # Print color statistics
        print("\nCOLOR STATISTICS:")
        total_chars = sum(color_stats.values())
        for color_hex, char_count in sorted(color_stats.items(), key=lambda x: x[1], reverse=True):
            label = color_to_label.get(color_hex, "unknown")
            percentage = (char_count / total_chars * 100) if total_chars > 0 else 0
            print(f"  {color_hex} ({label:15}): {char_count:8,} chars ({percentage:5.1f}%)")
        
        # Check for important colors
        green_chars = color_stats.get("#00FF00", 0)
        gray_chars = sum(color_stats.get(c, 0) for c in ["#808080", "#C0C0C0", "#696969"])
        
        if green_chars > 0:
            print(f"\n✓ GREEN (findings) found: {green_chars:,} characters")
        else:
            print("\n❌ NO GREEN (findings) sections found!")
            
        if gray_chars > 0:
            print(f"✓ GRAY (appendix) found: {gray_chars:,} characters")
        else:
            print("❌ NO GRAY (appendix) sections found!")
        
        return sections
        
    except Exception as e:
        print(f"Error processing {doc_path}: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_all_documents():
    """Process all colored documents and create new chunk files"""
    
    colored_dir = Path("01_colored_reports")
    output_dir = Path("02_chunked_data_color_based")
    output_dir.mkdir(exist_ok=True)
    
    # Get all colored Word documents
    doc_files = list(colored_dir.glob("*.docx"))
    
    print(f"Found {len(doc_files)} colored documents to process")
    print("=" * 80)
    
    all_stats = {
        'findings': 0,
        'appendix': 0,
        'wik': 0,
        'introduction': 0,
        'evaluation': 0,
        'response': 0,
        'recommendations': 0,
        'unknown': 0
    }
    
    for doc_file in doc_files:
        sections = extract_color_sections(doc_file)
        
        if sections:
            # Save sections file
            output_file = output_dir / f"{doc_file.stem}_color_sections.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"  → Saved {len(sections)} sections to {output_file.name}")
            
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
                            'color_hex': section['color_hex'],
                            'color_rgb': section['color_rgb']
                        })
                        chunk_id += 1
            
            # Save chunks file
            chunks_file = output_dir / f"{doc_file.stem}_color_chunks.json"
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
    if all_stats['findings'] == 0:
        print("⚠️  WARNING: No GREEN (findings) sections found in any document!")
        print("   This might indicate an issue with color detection.")
    if all_stats['appendix'] == 0:
        print("⚠️  WARNING: No GRAY (appendix) sections found in any document!")
        print("   This might indicate an issue with color detection.")

if __name__ == "__main__":
    process_all_documents()
