#!/usr/bin/env python3
"""
EMERGENCY FIX: Re-extract documents properly without breaking words
"""

import json
from pathlib import Path
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from collections import defaultdict
import re

def fix_broken_text(text):
    """Fix text that was broken with newlines in the middle of words"""
    # Remove newlines that appear within words
    # Pattern: lowercase letter + \n + lowercase letter
    text = re.sub(r'([a-zäöüß])\n([a-zäöüß])', r'\1\2', text)
    
    # Remove newlines after commas and other punctuation
    text = re.sub(r'([,.])\n([a-zA-ZäöüßÄÖÜ])', r'\1 \2', text)
    
    # Remove standalone newlines between text
    text = re.sub(r'([a-zäöüß])\n\s*([a-zäöüß])', r'\1 \2', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_properly(doc_path):
    """Extract text from document WITHOUT breaking it"""
    doc = Document(doc_path)
    
    highlight_to_label = {
        WD_COLOR_INDEX.BRIGHT_GREEN: 'findings',
        WD_COLOR_INDEX.GRAY_25: 'appendix',
        WD_COLOR_INDEX.GRAY_50: 'appendix',
        WD_COLOR_INDEX.TURQUOISE: 'wik',
        WD_COLOR_INDEX.YELLOW: 'introduction',
        WD_COLOR_INDEX.BLUE: 'evaluation', 
        WD_COLOR_INDEX.PINK: 'response',
        WD_COLOR_INDEX.DARK_YELLOW: 'recommendations'
    }
    
    sections = []
    current_section = None
    
    for para_idx, paragraph in enumerate(doc.paragraphs):
        para_text = ""
        para_label = None
        
        # Build complete paragraph text first
        for run in paragraph.runs:
            if run.text.strip():
                para_text += run.text
                
                # Get label from first highlighted run
                if para_label is None and run.font.highlight_color in highlight_to_label:
                    para_label = highlight_to_label[run.font.highlight_color]
        
        if para_text.strip() and para_label:
            # Check if we need to start a new section or continue current
            if current_section and current_section['label'] == para_label:
                # Add to current section with proper spacing
                current_section['text'] += " " + para_text.strip()
            else:
                # Save previous section if exists
                if current_section:
                    current_section['text'] = fix_broken_text(current_section['text'])
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'text': para_text.strip(),
                    'label': para_label,
                    'start_paragraph': para_idx
                }
    
    # Don't forget last section
    if current_section:
        current_section['text'] = fix_broken_text(current_section['text'])
        sections.append(current_section)
    
    return sections

def process_document(doc_path, doc_name):
    """Process a single document and save fixed extraction"""
    print(f"Processing: {doc_name}")
    
    sections = extract_properly(doc_path)
    
    # Save fixed sections
    output_dir = Path("02_chunked_data_FIXED")
    output_dir.mkdir(exist_ok=True)
    
    sections_file = output_dir / f"{doc_name}_fixed_sections.json"
    with open(sections_file, 'w', encoding='utf-8') as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)
    
    # Create chunks (but properly!)
    chunks = []
    chunk_id = 0
    
    for section in sections:
        # Split into reasonable chunks if too long
        text = section['text']
        max_chunk_size = 2000
        
        if len(text) <= max_chunk_size:
            chunks.append({
                'chunk_id': f"{doc_name}_chunk_{chunk_id}",
                'text': text,
                'label': section['label']
            })
            chunk_id += 1
        else:
            # Split at sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', text)
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= max_chunk_size:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        chunks.append({
                            'chunk_id': f"{doc_name}_chunk_{chunk_id}",
                            'text': current_chunk.strip(),
                            'label': section['label']
                        })
                        chunk_id += 1
                    current_chunk = sentence + " "
            
            if current_chunk:
                chunks.append({
                    'chunk_id': f"{doc_name}_chunk_{chunk_id}",
                    'text': current_chunk.strip(),
                    'label': section['label']
                })
                chunk_id += 1
    
    chunks_file = output_dir / f"{doc_name}_fixed_chunks.json"
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    # Print sample to verify
    if chunks:
        print(f"✓ Fixed {len(chunks)} chunks")
        print(f"Sample text (first 200 chars):")
        print(chunks[0]['text'][:200])
        print()
    
    return sections, chunks

# Process the specific document user is concerned about
if __name__ == "__main__":
    doc_path = Path("01_colored_reports/23489BE Prüfbericht V03 - Querschnittsprüfung des Umgangs des Bundes mit problematischen Stoffen - coloured.docx")
    
    if doc_path.exists():
        sections, chunks = process_document(doc_path, "23489BE")
        
        # Show statistics
        label_stats = defaultdict(int)
        for section in sections:
            label_stats[section['label']] += len(section['text'])
        
        print("\nFixed extraction statistics:")
        print("-" * 50)
        total = sum(label_stats.values())
        for label, count in sorted(label_stats.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            print(f"{label:20}: {count:8,} chars ({pct:5.1f}%)")
    else:
        print(f"Error: {doc_path} not found!")
