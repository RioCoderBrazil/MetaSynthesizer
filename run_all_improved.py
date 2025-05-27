#!/usr/bin/env python3
"""
Run all improved MetaSynthesizer components in sequence
"""

import subprocess
import sys
import time
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: str, description: str):
    """Run a command and handle output"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting: {description}")
    logger.info(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            check=True
        )
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Completed in {elapsed:.1f} seconds")
        
        if result.stdout:
            logger.info(f"Output:\n{result.stdout}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed: {e}")
        if e.stderr:
            logger.error(f"Error output:\n{e.stderr}")
        sys.exit(1)

def main():
    """Run the complete improved pipeline"""
    logger.info("🚀 Starting MetaSynthesizer Improved Pipeline")
    
    # Change to project directory
    project_dir = Path(__file__).parent
    
    # 1. Run improved extraction (if not already done)
    extraction_files = list((project_dir / '03_extracted_data').glob('*_improved_extraction.json'))
    if len(extraction_files) < 20:
        run_command(
            f"python3 {project_dir}/run_extraction_improved.py",
            "Improved Extraction with Quote Page Numbers"
        )
    else:
        logger.info("✅ Extraction already complete - found {} files".format(len(extraction_files)))
    
    # 2. Analyze extraction results
    run_command(
        f"python3 {project_dir}/analyze_extraction_improved.py",
        "Analyzing Extraction Quality"
    )
    
    # 3. Generate HTML reports
    run_command(
        f"python3 {project_dir}/generate_html_reports_improved.py",
        "Generating HTML Reports"
    )
    
    # 4. Create visualizations
    run_command(
        f"python3 {project_dir}/visualize_results_improved.py",
        "Creating Quality Visualizations"
    )
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("🎉 PIPELINE COMPLETE!")
    logger.info(f"{'='*60}")
    
    logger.info("\n📊 Results Summary:")
    logger.info(f"  - Extractions: {project_dir}/03_extracted_data/*_improved_extraction.json")
    logger.info(f"  - Analysis: {project_dir}/03_extracted_data/extraction_analysis_improved.csv")
    logger.info(f"  - HTML Reports: {project_dir}/04_html_reports_improved/*.html")
    logger.info(f"  - Visualizations: {project_dir}/05_visualizations/*_improved.png")
    
    # Check for improvements
    analysis_file = project_dir / '03_extracted_data' / 'extraction_analysis_improved.csv'
    if analysis_file.exists():
        import pandas as pd
        df = pd.read_csv(analysis_file)
        
        if 'completion_rate' in df.columns:
            avg_completion = df['completion_rate'].mean() * 100
            logger.info(f"\n📈 Average Completion Rate: {avg_completion:.1f}%")
            
            # Count quote quality
            quote_cols = [col for col in df.columns if '_pages' in col and col.endswith('_pages')]
            if quote_cols:
                pages_count = sum(df[col].sum() for col in quote_cols if col in df.columns)
                logger.info(f"📄 Documents with page numbers in quotes: {pages_count}")

if __name__ == "__main__":
    main()
