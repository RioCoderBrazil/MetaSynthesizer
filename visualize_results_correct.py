#!/usr/bin/env python3
"""
Visualize extraction results with CORRECT categories
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime

def create_visualizations():
    """Create comprehensive visualizations of extraction results"""
    
    # Load extractions
    extractions_file = Path("03_extracted_data/all_extractions_correct.json")
    if not extractions_file.exists():
        print("No extractions found. Please run extraction first.")
        return
    
    with open(extractions_file, 'r', encoding='utf-8') as f:
        extractions = json.load(f)
    
    # Create output directory
    viz_dir = Path("05_visualizations")
    viz_dir.mkdir(exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Category Completeness Chart
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Calculate category statistics
    category_stats = {}
    for ext in extractions:
        for cat, value in ext['categories'].items():
            if cat not in category_stats:
                category_stats[cat] = {'filled': 0, 'total': 0}
            category_stats[cat]['total'] += 1
            if value and value not in ['NULL erfasst', 'NULL erfasst, falls nicht erwähnt']:
                category_stats[cat]['filled'] += 1
    
    # Prepare data for plotting
    categories = []
    percentages = []
    for cat, stats in category_stats.items():
        categories.append(cat)
        percentage = (stats['filled'] / stats['total']) * 100 if stats['total'] > 0 else 0
        percentages.append(percentage)
    
    # Create horizontal bar chart
    df = pd.DataFrame({'Category': categories, 'Percentage': percentages})
    df = df.sort_values('Percentage', ascending=True)
    
    bars = ax.barh(df['Category'], df['Percentage'])
    
    # Color bars based on percentage
    for i, (bar, pct) in enumerate(zip(bars, df['Percentage'])):
        if pct >= 80:
            bar.set_color('#2ecc71')  # Green
        elif pct >= 50:
            bar.set_color('#f39c12')  # Orange
        else:
            bar.set_color('#e74c3c')  # Red
    
    ax.set_xlabel('Extraction Completeness (%)', fontsize=12)
    ax.set_title('Category Extraction Rates - CORRECT Schema', fontsize=16, fontweight='bold')
    ax.set_xlim(0, 100)
    
    # Add percentage labels
    for i, (cat, pct) in enumerate(zip(df['Category'], df['Percentage'])):
        ax.text(pct + 1, i, f'{pct:.1f}%', va='center')
    
    plt.tight_layout()
    plt.savefig(viz_dir / 'category_completeness_correct.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Document Completeness Heatmap
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Create matrix for heatmap
    doc_names = []
    category_names = sorted(category_stats.keys())
    data_matrix = []
    
    for ext in extractions:
        doc_names.append(ext['document_id'][:30] + '...' if len(ext['document_id']) > 30 else ext['document_id'])
        row = []
        for cat in category_names:
            value = ext['categories'].get(cat)
            if value and value not in ['NULL erfasst', 'NULL erfasst, falls nicht erwähnt']:
                row.append(1)  # Filled
            else:
                row.append(0)  # Empty
        data_matrix.append(row)
    
    # Create heatmap
    sns.heatmap(data_matrix, 
                xticklabels=[cat[:20] + '...' if len(cat) > 20 else cat for cat in category_names],
                yticklabels=doc_names,
                cmap='RdYlGn',
                cbar_kws={'label': 'Data Available'},
                ax=ax)
    
    ax.set_title('Document-Category Extraction Matrix', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(viz_dir / 'document_category_matrix_correct.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Priority Distribution Pie Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Priority distribution
    priority_counts = {}
    for ext in extractions:
        priority = ext['categories'].get('Empfehlung Priorität')
        if priority:
            priority_counts[f'Priority {priority}'] = priority_counts.get(f'Priority {priority}', 0) + 1
    
    if priority_counts:
        ax1.pie(priority_counts.values(), labels=priority_counts.keys(), autopct='%1.1f%%', 
                colors=['#e74c3c', '#f39c12', '#2ecc71', '#3498db'])
        ax1.set_title('Recommendation Priority Distribution', fontsize=14, fontweight='bold')
    
    # Implementation status distribution
    status_counts = {}
    status_map = {'O': 'Open', 'B': 'In Progress', 'G': 'Resolved', 'K': 'No Plan'}
    
    for ext in extractions:
        status = ext['categories'].get('Umsetzungsstratus Empfehlung')
        if status:
            status_label = status_map.get(status, status)
            status_counts[status_label] = status_counts.get(status_label, 0) + 1
    
    if status_counts:
        ax2.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%',
                colors=['#e74c3c', '#f39c12', '#2ecc71', '#95a5a6'])
        ax2.set_title('Implementation Status Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(viz_dir / 'priority_status_distribution_correct.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Quote Categories Analysis
    fig, ax = plt.subplots(figsize=(12, 8))
    
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
    
    quote_stats = []
    for cat in quote_categories:
        if cat in category_stats:
            stats = category_stats[cat]
            percentage = (stats['filled'] / stats['total']) * 100 if stats['total'] > 0 else 0
            quote_stats.append({'Category': cat, 'Percentage': percentage})
    
    if quote_stats:
        df_quotes = pd.DataFrame(quote_stats)
        df_quotes = df_quotes.sort_values('Percentage', ascending=True)
        
        bars = ax.barh(df_quotes['Category'], df_quotes['Percentage'])
        
        # Color bars
        for bar, pct in zip(bars, df_quotes['Percentage']):
            if pct >= 70:
                bar.set_color('#2ecc71')
            elif pct >= 40:
                bar.set_color('#f39c12')
            else:
                bar.set_color('#e74c3c')
        
        ax.set_xlabel('Extraction Rate (%)', fontsize=12)
        ax.set_title('Quote Categories Extraction Performance', fontsize=16, fontweight='bold')
        ax.set_xlim(0, 100)
        
        # Add percentage labels
        for i, (cat, pct) in enumerate(zip(df_quotes['Category'], df_quotes['Percentage'])):
            ax.text(pct + 1, i, f'{pct:.1f}%', va='center')
    
    plt.tight_layout()
    plt.savefig(viz_dir / 'quote_categories_performance_correct.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Visualizations created in {viz_dir}/")
    print(f"  - category_completeness_correct.png")
    print(f"  - document_category_matrix_correct.png")
    print(f"  - priority_status_distribution_correct.png")
    print(f"  - quote_categories_performance_correct.png")
    
    # Generate summary statistics
    total_possible = sum(stats['total'] for stats in category_stats.values())
    total_filled = sum(stats['filled'] for stats in category_stats.values())
    overall_percentage = (total_filled / total_possible) * 100 if total_possible > 0 else 0
    
    print(f"\n=== EXTRACTION STATISTICS ===")
    print(f"Total documents: {len(extractions)}")
    print(f"Total data points: {total_possible}")
    print(f"Filled data points: {total_filled}")
    print(f"Overall completeness: {overall_percentage:.1f}%")
    
    # Save summary report
    summary = {
        'extraction_date': datetime.now().isoformat(),
        'total_documents': len(extractions),
        'total_categories': len(category_stats),
        'overall_completeness': round(overall_percentage, 2),
        'category_performance': {cat: round((stats['filled']/stats['total'])*100, 2) 
                                for cat, stats in category_stats.items()},
        'priority_distribution': dict(priority_counts) if 'priority_counts' in locals() else {},
        'status_distribution': dict(status_counts) if 'status_counts' in locals() else {}
    }
    
    with open(viz_dir / 'extraction_summary_correct.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Summary report saved to {viz_dir}/extraction_summary_correct.json")


if __name__ == "__main__":
    create_visualizations()
