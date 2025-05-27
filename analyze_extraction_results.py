#!/usr/bin/env python3
"""Analyze extraction results to assess data completeness."""

import json
from pathlib import Path
from collections import defaultdict


def analyze_extractions(extraction_file):
    """Analyze the extraction results."""
    with open(extraction_file, 'r', encoding='utf-8') as f:
        extractions = json.load(f)
    
    total_docs = len(extractions)
    category_stats = defaultdict(lambda: {'populated': 0, 'empty': 0})
    
    print(f"\n=== EXTRACTION ANALYSIS ===")
    print(f"Total documents: {total_docs}")
    print(f"Extraction file: {extraction_file}")
    
    # Analyze each document
    for doc in extractions:
        doc_id = doc['document_id']
        categories = doc.get('categories', {})
        
        # Count populated vs empty categories
        for cat_name, cat_value in categories.items():
            if cat_value and cat_value != {} and cat_value != []:
                # Check if it's actually populated
                if isinstance(cat_value, dict):
                    # Check if dict has non-null values
                    has_data = any(v for v in cat_value.values() if v is not None and v != [] and v != {})
                    if has_data:
                        category_stats[cat_name]['populated'] += 1
                    else:
                        category_stats[cat_name]['empty'] += 1
                elif isinstance(cat_value, list) and len(cat_value) > 0:
                    category_stats[cat_name]['populated'] += 1
                else:
                    category_stats[cat_name]['empty'] += 1
            else:
                category_stats[cat_name]['empty'] += 1
    
    # Print category statistics
    print("\n=== CATEGORY STATISTICS ===")
    print(f"{'Category':<30} {'Populated':<12} {'Empty':<12} {'Rate':<10}")
    print("-" * 65)
    
    total_populated = 0
    total_empty = 0
    
    for cat_name in sorted(category_stats.keys()):
        stats = category_stats[cat_name]
        populated = stats['populated']
        empty = stats['empty']
        rate = (populated / total_docs * 100) if total_docs > 0 else 0
        
        total_populated += populated
        total_empty += empty
        
        print(f"{cat_name:<30} {populated:<12} {empty:<12} {rate:>6.1f}%")
    
    # Overall statistics
    total_fields = total_populated + total_empty
    overall_rate = (total_populated / total_fields * 100) if total_fields > 0 else 0
    
    print("-" * 65)
    print(f"{'TOTAL':<30} {total_populated:<12} {total_empty:<12} {overall_rate:>6.1f}%")
    
    # Sample extraction details
    print("\n=== SAMPLE EXTRACTION (First Document) ===")
    if extractions:
        first_doc = extractions[0]
        print(f"Document: {first_doc['document_id']}")
        print(f"Categories with data:")
        for cat_name, cat_value in first_doc.get('categories', {}).items():
            if cat_value and cat_value != {} and cat_value != []:
                if isinstance(cat_value, dict):
                    has_data = any(v for v in cat_value.values() if v is not None and v != [] and v != {})
                    if has_data:
                        print(f"  - {cat_name}: {json.dumps(cat_value, ensure_ascii=False)[:100]}...")


if __name__ == "__main__":
    extraction_file = Path("03_extracted_data/all_extractions.json")
    
    if extraction_file.exists():
        analyze_extractions(extraction_file)
    else:
        print(f"Error: {extraction_file} not found!")
