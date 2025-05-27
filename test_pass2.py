"""
Test Pass 2: RAG-based extraction to 23 categories
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.pass2 import RAGExtractor, SchemaValidator, CategoryMerger
from src.utils.logger import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables from root .env file
project_root = Path(__file__).parent
env_path = project_root / '.env'
load_dotenv(env_path, override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


def test_pass2():
    """Test Pass 2 pipeline"""
    
    # Get test document
    doc_id = "11380BE_Revisionsbericht - Bewirtschaftung von Umweltrisiken - Altlasten und Sanierungskosten - coloured"
    logger.info(f"Testing Pass 2 with document: {doc_id}")
    
    # Check if Pass 1 results exist
    chunks_file = f"02_chunked_data/{doc_id}_chunks.json"
    if not os.path.exists(chunks_file):
        logger.error(f"Pass 1 results not found: {chunks_file}")
        logger.error("Please run test_pass1.py first")
        return
    
    # Initialize components
    logger.info("\n=== Initializing Pass 2 Components ===")
    
    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        logger.error("Please set it in your .env file")
        return
    
    # Initialize RAG extractor
    rag_extractor = RAGExtractor(
        qdrant_host='localhost',
        collection_name='metasynthesizer',
        anthropic_api_key=api_key
    )
    
    # Initialize validator and merger
    validator = SchemaValidator()
    merger = CategoryMerger()
    
    # Test single category extraction first
    logger.info("\n=== Testing Single Category Extraction ===")
    test_category = "finding_summary"
    logger.info(f"Extracting category: {test_category}")
    
    category_data = rag_extractor.extract_for_category(test_category, doc_id)
    logger.info(f"Extracted data: {json.dumps(category_data, indent=2, ensure_ascii=False)}")
    
    # Validate extracted data
    is_valid, errors = validator.validate_category_data(test_category, category_data)
    if is_valid:
        logger.info(f"✓ Validation passed for {test_category}")
    else:
        logger.warning(f"✗ Validation failed for {test_category}: {errors}")
        
        # Try to fix common issues
        fixed_data = validator.fix_common_issues(test_category, category_data)
        is_valid_fixed, errors_fixed = validator.validate_category_data(test_category, fixed_data)
        if is_valid_fixed:
            logger.info(f"✓ Fixed validation issues for {test_category}")
            category_data = fixed_data
        else:
            logger.error(f"✗ Could not fix validation issues: {errors_fixed}")
    
    # Extract all categories
    logger.info("\n=== Extracting All Categories ===")
    logger.info("This may take a few minutes...")
    
    # For testing, extract only a subset of categories
    test_categories = [
        "finding_summary",
        "recommendation_tracking", 
        "cost_analysis",
        "risk_assessment",
        "environmental_impact"
    ]
    
    all_extracted = {}
    for category in test_categories:
        logger.info(f"\nExtracting: {category}")
        try:
            data = rag_extractor.extract_for_category(category, doc_id, max_contexts=5)
            all_extracted[category] = data
            
            # Quick validation
            is_valid, _ = validator.validate_category_data(category, data)
            status = "✓" if is_valid else "✗"
            logger.info(f"{status} {category}: {len(data)} fields extracted")
            
        except Exception as e:
            logger.error(f"Failed to extract {category}: {e}")
            all_extracted[category] = {}
    
    # Validate all
    logger.info("\n=== Validating All Categories ===")
    validation_results = validator.validate_all_categories(all_extracted)
    
    valid_count = sum(1 for is_valid, _ in validation_results.values() if is_valid)
    logger.info(f"Validation summary: {valid_count}/{len(validation_results)} categories valid")
    
    # Fix validation issues
    logger.info("\n=== Fixing Validation Issues ===")
    fixed_data = {}
    for category, data in all_extracted.items():
        fixed_data[category] = validator.fix_common_issues(category, data)
    
    # Merge and consolidate
    logger.info("\n=== Merging and Consolidating Results ===")
    merged_data = merger.merge_extractions(fixed_data)
    
    # Create final report
    report = merger.consolidate_report(merged_data, doc_id)
    
    # Show summary
    logger.info("\n=== Extraction Summary ===")
    summary = report['summary']
    logger.info(f"Total categories: {summary['total_categories']}")
    logger.info(f"Populated categories: {summary['populated_categories']}")
    logger.info(f"Total findings: {summary['total_findings']}")
    logger.info(f"Total recommendations: {summary['total_recommendations']}")
    logger.info(f"Total costs identified: {summary['total_costs_identified']:,.2f} CHF")
    
    # Show statistics
    logger.info("\n=== Extraction Statistics ===")
    stats = report['statistics']
    logger.info(f"Overall completeness: {stats['overall_completeness']}%")
    for category, completeness in stats['extraction_completeness'].items():
        coverage = stats['field_coverage'][category]
        logger.info(f"  {category}: {completeness}% complete ({coverage} fields)")
    
    # Save results
    output_path = merger.save_results(report)
    logger.info(f"\n✓ Results saved to: {output_path}")
    
    # Show sample of extracted data
    logger.info("\n=== Sample Extracted Data ===")
    for category in test_categories[:3]:
        if category in merged_data:
            logger.info(f"\n{category}:")
            cat_data = merged_data[category]
            for field, value in list(cat_data.items())[:3]:
                if not field.startswith('_'):
                    logger.info(f"  {field}: {value}")
    
    logger.info("\n=== Pass 2 Test Complete ===")


if __name__ == "__main__":
    test_pass2()
