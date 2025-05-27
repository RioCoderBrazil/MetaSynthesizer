#!/usr/bin/env python3
"""
Fix ALL 20 documents with proper text extraction
"""

import json
from pathlib import Path
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from collections import defaultdict
import re
from datetime import datetime

def fix_broken_text(text):
    """Fix text that was broken with newlines in the middle of words"""
    # Remove newlines that appear within words
    text = re.sub(r'([a-zäöüß])\n([a-zäöüß])', r'\1\2', text)
    text = re.sub(r'([,.])\n([a-zA-ZäöüßÄÖÜ])', r'\1 \2', text)
    text = re.sub(r'([a-zäöüß])\n\s*([a-zäöüß])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_document_properly(doc_path):
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
    chunks = []
    chunk_id = 0
    
    # Process by tracking continuous sections
    current_section = None
    page_num = 1
    
    for para_idx, paragraph in enumerate(doc.paragraphs):
        # Check for page breaks (simplified)
        if para_idx > 0 and para_idx % 40 == 0:
            page_num += 1
        
        # Build paragraph text properly
        para_text = ""
        para_label = None
        
        for run in paragraph.runs:
            if run.text:
                para_text += run.text
                if para_label is None and run.font.highlight_color in highlight_to_label:
                    para_label = highlight_to_label[run.font.highlight_color]
        
        para_text = para_text.strip()
        
        if para_text and para_label:
            # Continue or start section
            if current_section and current_section['label'] == para_label:
                current_section['text'] += " " + para_text
                current_section['end_page'] = page_num
            else:
                # Save previous section
                if current_section:
                    current_section['text'] = fix_broken_text(current_section['text'])
                    sections.append(current_section)
                    
                    # Create chunks from section
                    text = current_section['text']
                    if len(text) <= 2000:
                        chunks.append({
                            'chunk_id': f"chunk_{chunk_id}",
                            'text': text,
                            'label': current_section['label'],
                            'start_page': current_section['start_page'],
                            'end_page': current_section['end_page']
                        })
                        chunk_id += 1
                    else:
                        # Split intelligently at sentence boundaries
                        sentences = re.split(r'(?<=[.!?])\s+', text)
                        current_chunk = ""
                        
                        for sentence in sentences:
                            if len(current_chunk) + len(sentence) <= 2000:
                                current_chunk += sentence + " "
                            else:
                                if current_chunk:
                                    chunks.append({
                                        'chunk_id': f"chunk_{chunk_id}",
                                        'text': current_chunk.strip(),
                                        'label': current_section['label'],
                                        'start_page': current_section['start_page'],
                                        'end_page': current_section['end_page']
                                    })
                                    chunk_id += 1
                                current_chunk = sentence + " "
                        
                        if current_chunk:
                            chunks.append({
                                'chunk_id': f"chunk_{chunk_id}",
                                'text': current_chunk.strip(),
                                'label': current_section['label'],
                                'start_page': current_section['start_page'],
                                'end_page': current_section['end_page']
                            })
                            chunk_id += 1
                
                # Start new section
                current_section = {
                    'text': para_text,
                    'label': para_label,
                    'start_page': page_num,
                    'end_page': page_num
                }
    
    # Don't forget last section
    if current_section:
        current_section['text'] = fix_broken_text(current_section['text'])
        sections.append(current_section)
        
        # Create final chunks
        text = current_section['text']
        if len(text) <= 2000:
            chunks.append({
                'chunk_id': f"chunk_{chunk_id}",
                'text': text,
                'label': current_section['label'],
                'start_page': current_section['start_page'],
                'end_page': current_section['end_page']
            })
        else:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= 2000:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        chunks.append({
                            'chunk_id': f"chunk_{chunk_id}",
                            'text': current_chunk.strip(),
                            'label': current_section['label'],
                            'start_page': current_section['start_page'],
                            'end_page': current_section['end_page']
                        })
                        chunk_id += 1
                    current_chunk = sentence + " "
            if current_chunk:
                chunks.append({
                    'chunk_id': f"chunk_{chunk_id}",
                    'text': current_chunk.strip(),
                    'label': current_section['label'],
                    'start_page': current_section['start_page'],
                    'end_page': current_section['end_page']
                })
    
    return sections, chunks

def process_all_documents():
    """Process all colored documents"""
    input_dir = Path("01_colored_reports")
    output_dir = Path("02_chunked_data_CORRECTED")
    output_dir.mkdir(exist_ok=True)
    
    # Get all colored Word documents
    doc_files = list(input_dir.glob("*coloured*.docx"))
    doc_files.extend(list(input_dir.glob("*colored*.docx")))

    print(f"Found {len(doc_files)} documents to process")
    print("="*80)
    
    overall_stats = defaultdict(int)
    processed_count = 0
    
    for doc_path in doc_files:
        doc_name = doc_path.stem
        print(f"\nProcessing: {doc_name}")
        
        try:
            sections, chunks = extract_document_properly(doc_path)
            
            # Save sections
            sections_file = output_dir / f"{doc_name}_sections.json"
            with open(sections_file, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            # Save chunks with proper naming
            chunks_with_ids = []
            for chunk in chunks:
                chunk['chunk_id'] = f"{doc_name}_{chunk['chunk_id']}"
                chunks_with_ids.append(chunk)
            
            chunks_file = output_dir / f"{doc_name}_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_with_ids, f, ensure_ascii=False, indent=2)
            
            # Calculate stats
            label_stats = defaultdict(int)
            for section in sections:
                label_stats[section['label']] += len(section['text'])
                overall_stats[section['label']] += len(section['text'])
            
            # Show stats
            total = sum(label_stats.values())
            print(f"✓ Extracted {len(sections)} sections, {len(chunks)} chunks, {total:,} chars")
            
            # Check text quality
            if chunks:
                sample = chunks[0]['text'][:100]
                if '\n' in sample and not '. ' in sample:
                    print("⚠️  WARNING: Text might still have breaks!")
                else:
                    print("✓ Text quality looks good")
            
            processed_count += 1
            
        except Exception as e:
            print(f"❌ ERROR processing {doc_name}: {e}")
    
    # Summary
    print("\n" + "="*80)
    print(f"PROCESSING COMPLETE: {processed_count}/{len(doc_files)} documents")
    print("\nOVERALL STATISTICS:")
    print("-"*50)
    
    total_chars = sum(overall_stats.values())
    for label, count in sorted(overall_stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_chars * 100) if total_chars > 0 else 0
        print(f"{label:20}: {count:10,} chars ({pct:5.1f}%)")
    
    print(f"\nTOTAL CHARACTERS: {total_chars:,}")
    
    # Create summary file
    summary = {
        'processing_date': datetime.now().isoformat(),
        'documents_processed': processed_count,
        'total_documents': len(doc_files),
        'total_characters': total_chars,
        'statistics': dict(overall_stats),
        'output_directory': str(output_dir)
    }
    
    with open(output_dir / 'PROCESSING_SUMMARY.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ All corrected files saved to: {output_dir}/")

if __name__ == "__main__":
    process_all_documents()
