#!/usr/bin/env python3
"""
Analyze all labeled chunks to show what labels are present in each document.
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_labels():
    chunks_dir = Path("02_chunked_data")
    all_stats = {}
    
    # Get all chunk files
    chunk_files = sorted(chunks_dir.glob("*_chunks.json"))
    
    print("="*100)
    print("LABEL ANALYSIS FOR ALL DOCUMENTS")
    print("="*100)
    print()
    
    label_color_map = {
        'wik': 'Cyan',
        'summary': 'Cyan', 
        'introduction': 'Yellow',
        'findings': 'Green',
        'evaluation': 'Blue',
        'recommendations': 'Dark Orange',
        'empfehlung': 'Dark Orange',
        'response': 'Pink',
        'appendix': 'Gray',
        'unknown': 'Gray'
    }
    
    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        # Count labels
        label_counts = defaultdict(int)
        for chunk in chunks:
            label = chunk.get('label', 'unknown')
            label_counts[label] += 1
        
        doc_name = chunk_file.stem.replace('_chunks', '')
        all_stats[doc_name] = dict(label_counts)
        
        print(f"📄 {doc_name[:60]}...")
        print(f"   Total chunks: {len(chunks)}")
        for label, count in sorted(label_counts.items()):
            color = label_color_map.get(label, '?')
            percentage = (count/len(chunks))*100
            print(f"   • {label:20} ({color:12}) : {count:3} chunks ({percentage:5.1f}%)")
        print()
    
    # Summary of all labels found
    all_labels = set()
    for stats in all_stats.values():
        all_labels.update(stats.keys())
    
    print("="*100)
    print("SUMMARY: Labels found across all documents")
    print("="*100)
    
    label_docs = defaultdict(int)
    for doc, stats in all_stats.items():
        for label in stats:
            label_docs[label] += 1
    
    for label in sorted(all_labels):
        color = label_color_map.get(label, '?')
        doc_count = label_docs[label]
        print(f"{label:20} ({color:12}) : Found in {doc_count:2} documents")
    
    # Check for green (findings) and gray (appendix)
    print()
    print("="*100)
    print("LOOKING FOR SPECIFIC COLORS:")
    print("="*100)
    print()
    
    findings_docs = []
    appendix_docs = []
    
    for doc, stats in all_stats.items():
        if 'findings' in stats:
            findings_docs.append(doc)
        if 'appendix' in stats:
            appendix_docs.append(doc)
    
    print(f"🟢 Documents with FINDINGS (Green): {len(findings_docs)}")
    for doc in findings_docs[:5]:  # Show first 5
        print(f"   • {doc[:60]}...")
    
    print()
    print(f"⚫ Documents with APPENDIX (Gray): {len(appendix_docs)}")
    for doc in appendix_docs[:5]:  # Show first 5
        print(f"   • {doc[:60]}...")

if __name__ == "__main__":
    analyze_labels()
