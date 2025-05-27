#!/usr/bin/env python3
"""
Generate HTML reports with CORRECT categories
"""

import json
from pathlib import Path
from datetime import datetime

def generate_reports():
    """Generate HTML reports from extraction results"""
    
    # Ensure output directory exists
    output_dir = Path("04_html_reports_correct")
    output_dir.mkdir(exist_ok=True)
    
    # Load extraction results
    extraction_file = Path("03_extracted_data/all_extractions_correct.json")
    if not extraction_file.exists():
        print("No extraction results found!")
        return
        
    # Import report generator
    from src.reporting.html_report_correct import CorrectHTMLReportGenerator
    
    # Load extractions
    with open(extraction_file, 'r', encoding='utf-8') as f:
        extractions = json.load(f)
    
    print(f"\n=== GENERATING HTML REPORTS (CORRECT SCHEMA) ===")
    print(f"Processing {len(extractions)} documents...")
    
    # Initialize report generator
    generator = CorrectHTMLReportGenerator()
    
    # Generate individual reports
    success_count = 0
    for extraction in extractions:
        doc_id = extraction['document_id']
        print(f"\nGenerating report for: {doc_id[:50]}...")
        
        try:
            output_path = Path(f"04_html_reports_correct/{doc_id}_correct_report.html")
            if generator.generate_report(extraction, output_path):
                success_count += 1
                print(f"  ✓ Report generated: {output_path}")
            else:
                print(f"  ✗ Failed to generate report")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    # Generate index page
    try:
        index_path = Path("04_html_reports_correct/index_correct.html")
        generator.generate_index_page(extractions, index_path)
        print(f"\n✓ Index page generated: {index_path}")
    except Exception as e:
        print(f"\n✗ Failed to generate index: {str(e)}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Successfully generated {success_count}/{len(extractions)} reports")
    print(f"Reports location: 04_html_reports_correct/")
    
    # Generate statistics
    total_categories = 0
    filled_categories = 0
    
    for ext in extractions:
        for cat, value in ext['categories'].items():
            total_categories += 1
            if value and value not in ['NULL erfasst', 'NULL erfasst, falls nicht erwähnt']:
                filled_categories += 1
    
    completeness = (filled_categories / total_categories) * 100 if total_categories > 0 else 0
    print(f"Overall data completeness: {completeness:.1f}%")


if __name__ == "__main__":
    generate_reports()
