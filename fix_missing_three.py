#!/usr/bin/env python3
"""
Process the 3 missing documents with different naming patterns
"""

import sys
sys.path.append('.')
from fix_all_documents import extract_document_properly
import json
from pathlib import Path
from collections import defaultdict

def process_missing_documents():
    """Process the 3 documents that were missed due to naming variations"""
    
    missing_docs = [
        "18185BE_R3_V03 - Audit de surveillance financière de la troisième correction du Rhône - Coloured.docx",
        "18360BE DFAE_DOI_V04 - Audit de la nécessité des mesures pour renforcer la Suisse comme Etat hôte - farcoded.docx",
        "22723BE Prüfbericht V04 - DOC - Prüfung der Investitionsplanung  - farbcoded.docx"
    ]
    
    input_dir = Path("01_colored_reports")
    output_dir = Path("02_chunked_data_CORRECTED")
    
    print("Processing 3 missing documents...")
    print("="*80)
    
    for doc_name in missing_docs:
        doc_path = input_dir / doc_name
        
        if not doc_path.exists():
            print(f"❌ Not found: {doc_name}")
            continue
            
        print(f"\nProcessing: {doc_name}")
        
        try:
            sections, chunks = extract_document_properly(doc_path)
            
            # Save with consistent naming
            base_name = doc_path.stem
            
            # Save sections
            sections_file = output_dir / f"{base_name}_sections.json"
            with open(sections_file, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            # Save chunks with proper IDs
            chunks_with_ids = []
            for i, chunk in enumerate(chunks):
                chunk['chunk_id'] = f"{base_name}_chunk_{i}"
                chunks_with_ids.append(chunk)
            
            chunks_file = output_dir / f"{base_name}_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_with_ids, f, ensure_ascii=False, indent=2)
            
            # Stats
            label_stats = defaultdict(int)
            for section in sections:
                label_stats[section['label']] += len(section['text'])
            
            total = sum(label_stats.values())
            print(f"✓ Extracted {len(sections)} sections, {len(chunks)} chunks, {total:,} chars")
            
            # Show what was found
            if 'findings' in label_stats:
                pct = (label_stats['findings'] / total * 100)
                print(f"  ✓ GREEN (findings): {pct:.1f}%")
            if 'appendix' in label_stats:
                pct = (label_stats['appendix'] / total * 100)
                print(f"  ✓ GRAY (appendix): {pct:.1f}%")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Update the summary
    print("\n" + "="*80)
    print("Updating overall statistics...")
    
    # Count all files now
    all_chunks = list(output_dir.glob("*_chunks.json"))
    print(f"\n✅ TOTAL DOCUMENTS NOW: {len(all_chunks)}")
    
    # Recalculate overall stats
    overall_stats = defaultdict(int)
    total_docs = 0
    
    for chunk_file in all_chunks:
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        for chunk in chunks:
            if 'label' in chunk:
                overall_stats[chunk['label']] += len(chunk['text'])
        
        total_docs += 1
    
    # Show updated stats
    total_chars = sum(overall_stats.values())
    print(f"\nUPDATED STATISTICS (ALL {total_docs} DOCUMENTS):")
    print("-"*50)
    
    for label, count in sorted(overall_stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_chars * 100) if total_chars > 0 else 0
        print(f"{label:20}: {count:10,} chars ({pct:5.1f}%)")
    
    print(f"\nTOTAL CHARACTERS: {total_chars:,}")
    
    # Update summary file
    summary = {
        'processing_date': str(Path("02_chunked_data_CORRECTED/PROCESSING_SUMMARY.json")),
        'documents_processed': total_docs,
        'total_documents': 20,
        'total_characters': total_chars,
        'statistics': dict(overall_stats),
        'note': 'Updated with all 20 documents including farcoded/farbcoded/Coloured variants'
    }
    
    with open(output_dir / 'PROCESSING_SUMMARY_COMPLETE.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_missing_documents()
