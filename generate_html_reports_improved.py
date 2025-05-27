#!/usr/bin/env python3
"""
Generate HTML reports for improved extractions
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from reporting.html_report_improved import ImprovedHTMLReportGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Generate all HTML reports"""
    generator = ImprovedHTMLReportGenerator()
    
    # Setup paths
    project_root = Path(__file__).parent
    input_dir = project_root / '03_extracted_data'
    output_dir = project_root / '04_html_reports_improved'
    
    # Generate reports
    generator.generate_all_reports(input_dir, output_dir)
    
    logger.info(f"\nHTML reports generated in: {output_dir}")
    logger.info("You can open any .html file in your browser to view the report")

if __name__ == "__main__":
    main()
