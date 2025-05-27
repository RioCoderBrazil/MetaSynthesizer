#!/usr/bin/env python3
"""
Analyze extraction results with CORRECT categories
"""

import json
from pathlib import Path
from collections import Counter
import pandas as pd

def analyze_extractions():
    """Analyze the extraction results"""
    
    # Load extractions
    extractions_file = Path("03_extracted_data/all_extractions_correct.json")
    if not extractions_file.exists():
        print("No extractions found. Please run extraction first.")
        return
    
    with open(extractions_file, 'r', encoding='utf-8') as f:
        extractions = json.load(f)
    
    print(f"\n=== EXTRACTION ANALYSIS (CORRECT CATEGORIES) ===")
    print(f"Total documents processed: {len(extractions)}")
    
    # Category completeness analysis
    category_stats = {}
    for ext in extractions:
        for cat, value in ext['categories'].items():
            if cat not in category_stats:
                category_stats[cat] = {'filled': 0, 'total': 0}
            category_stats[cat]['total'] += 1
            if value and value not in ['NULL erfasst', 'NULL erfasst, falls nicht erwähnt']:
                category_stats[cat]['filled'] += 1
    
    # Calculate percentages and sort
    category_results = []
    for cat, stats in category_stats.items():
        percentage = (stats['filled'] / stats['total']) * 100 if stats['total'] > 0 else 0
        category_results.append({
            'Category': cat,
            'Filled': stats['filled'],
            'Total': stats['total'],
            'Percentage': round(percentage, 1)
        })
    
    # Sort by percentage descending
    category_results.sort(key=lambda x: x['Percentage'], reverse=True)
    
    print("\n=== CATEGORY EXTRACTION RATES ===")
    print(f"{'Category':<45} {'Filled':>7} {'Total':>7} {'Rate':>7}")
    print("-" * 70)
    
    for cat in category_results:
        print(f"{cat['Category']:<45} {cat['Filled']:>7} {cat['Total']:>7} {cat['Percentage']:>6.1f}%")
    
    # Overall statistics
    total_possible = sum(stats['total'] for stats in category_stats.values())
    total_filled = sum(stats['filled'] for stats in category_stats.values())
    overall_percentage = (total_filled / total_possible) * 100 if total_possible > 0 else 0
    
    print(f"\n{'OVERALL COMPLETENESS':<45} {total_filled:>7} {total_possible:>7} {overall_percentage:>6.1f}%")
    
    # Categories that need improvement
    print("\n=== CATEGORIES NEEDING IMPROVEMENT (<50%) ===")
    for cat in category_results:
        if cat['Percentage'] < 50:
            print(f"- {cat['Category']}: {cat['Percentage']}%")
    
    # Quote categories analysis
    print("\n=== QUOTE CATEGORIES (Wörtliche Zitate) ===")
    quote_categories = [
        'Umwelt, Info A (Relevante Akteure)',
        'Umwelt, Info B (Berichtsprache/Datei)',
        'Umwelt, Info C (Bedenken/Monitoring)',
        'Flankieigend A (kein Plan)',
        'Flankieigend B (Plan unvollständig)',
        'Flankieigend C (in der Nachverfolgung)',
        'Umsetzungsstatus',
        'Unrelevante Faktoren',
        'Anpassungen',
        'Empfehlungen'
    ]
    
    for cat in quote_categories:
        if cat in category_stats:
            stats = category_stats[cat]
            percentage = (stats['filled'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"- {cat}: {percentage:.1f}%")
    
    # Document-level analysis
    print("\n=== DOCUMENT COMPLETENESS ===")
    doc_completeness = []
    for ext in extractions:
        filled = sum(1 for v in ext['categories'].values() if v and v not in ['NULL erfasst', 'NULL erfasst, falls nicht erwähnt'])
        total = len(ext['categories'])
        percentage = (filled / total) * 100 if total > 0 else 0
        doc_completeness.append({
            'Document': ext['document_id'][:50],
            'Filled': filled,
            'Total': total,
            'Percentage': round(percentage, 1)
        })
    
    # Sort by percentage
    doc_completeness.sort(key=lambda x: x['Percentage'], reverse=True)
    
    print("\nTop 5 most complete documents:")
    for doc in doc_completeness[:5]:
        print(f"- {doc['Document']}: {doc['Percentage']}%")
    
    print("\nBottom 5 least complete documents:")
    for doc in doc_completeness[-5:]:
        print(f"- {doc['Document']}: {doc['Percentage']}%")
    
    # Priority and status analysis
    print("\n=== EMPFEHLUNGEN ANALYSIS ===")
    priority_counter = Counter()
    status_counter = Counter()
    
    for ext in extractions:
        priority = ext['categories'].get('Empfehlung Priorität')
        if priority:
            priority_counter[priority] += 1
        
        status = ext['categories'].get('Umsetzungsstratus Empfehlung')
        if status:
            status_map = {'O': 'Offen', 'B': 'In Bearbeitung', 'G': 'Gelöst', 'K': 'Kein Plan'}
            status_counter[status_map.get(status, status)] += 1
    
    print("\nPriority distribution:")
    for priority, count in sorted(priority_counter.items()):
        print(f"- Priority {priority}: {count} documents")
    
    print("\nImplementation status:")
    for status, count in status_counter.most_common():
        print(f"- {status}: {count} documents")
    
    # Export summary to CSV
    df = pd.DataFrame(category_results)
    df.to_csv("03_extracted_data/extraction_analysis_correct.csv", index=False)
    print(f"\n✓ Analysis saved to 03_extracted_data/extraction_analysis_correct.csv")


if __name__ == "__main__":
    analyze_extractions()
