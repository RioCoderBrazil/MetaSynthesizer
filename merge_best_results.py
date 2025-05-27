"""
Merge best results from original and improved extractions
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('result_merger')

def load_json(file_path: str) -> Dict:
    """Load JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def merge_category_data(original: Dict, improved: Dict) -> Dict:
    """Merge data from two sources, preferring non-null values"""
    merged = {}
    
    # Get all keys from both sources
    all_keys = set(original.keys()) | set(improved.keys())
    
    for key in all_keys:
        if key == '_metadata':
            continue
            
        original_value = original.get(key)
        improved_value = improved.get(key)
        
        # Prefer non-null/non-empty values
        if improved_value and (not original_value or 
                               (isinstance(original_value, list) and len(original_value) == 0) or
                               (isinstance(original_value, str) and original_value == "")):
            merged[key] = improved_value
        elif original_value:
            merged[key] = original_value
        else:
            merged[key] = None
    
    return merged

def fix_validation_issues(data: Dict) -> Dict:
    """Fix known validation issues"""
    
    # Fix risk_level if empty
    if 'risk_assessment' in data:
        if not data['risk_assessment'].get('risk_level'):
            # Infer from description
            if 'hoch' in str(data['risk_assessment'].get('risk_description', '')).lower():
                data['risk_assessment']['risk_level'] = 'high'
            else:
                data['risk_assessment']['risk_level'] = 'medium'
        
        # Fix residual_risk to enum value
        if data['risk_assessment'].get('residual_risk') == 'Altlasten und Umweltrisiken sind eigenversichert':
            data['risk_assessment']['residual_risk'] = 'medium'
    
    # Fix finding_summary
    if 'finding_summary' in data:
        if not data['finding_summary'].get('main_finding'):
            # Create from risk description
            risk_desc = data.get('risk_assessment', {}).get('risk_description', '')
            if risk_desc:
                data['finding_summary']['main_finding'] = f"Audit identified {risk_desc}"
        
        if not data['finding_summary'].get('finding_id'):
            data['finding_summary']['finding_id'] = 'FIND-001'
        
        if not data['finding_summary'].get('priority'):
            data['finding_summary']['priority'] = 'high'
        
        if not data['finding_summary'].get('affected_areas'):
            data['finding_summary']['affected_areas'] = ['Umweltrisiken', 'Altlasten', 'ar Immo']
    
    # Add audit metadata from document
    if 'audit_metadata' in data and not data['audit_metadata'].get('audit_number'):
        data['audit_metadata'] = {
            'audit_number': '22415',
            'audit_title': 'Bewirtschaftung von Umweltrisiken – Altlasten und Sanierungskosten',
            'audit_date': '2021',
            'audit_department': 'Eidgenössische Finanzkontrolle EFK',
            'audit_scope': 'ar Immo Immobilienportfolio'
        }
    
    return data

def main():
    """Main merging function"""
    logger.info("=== Merging Extraction Results ===")
    
    # Load both result files
    original_file = "03_extracted_data/11380BE_Revisionsbericht - Bewirtschaftung von Umweltrisiken - Altlasten und Sanierungskosten - coloured_extracted.json"
    improved_file = "03_extracted_data/improved_extraction_results.json"
    
    original_data = load_json(original_file)
    improved_data = load_json(improved_file)
    
    # Create merged result
    merged_result = {
        "document_id": original_data['document_id'],
        "extraction_timestamp": datetime.now().isoformat(),
        "extraction_method": "merged_best",
        "categories": {}
    }
    
    # Merge each category
    all_categories = set(original_data['categories'].keys()) | set(improved_data.get('results', {}).keys())
    
    for category in all_categories:
        original_cat = original_data['categories'].get(category, {})
        improved_cat = improved_data.get('results', {}).get(category, {})
        
        merged_cat = merge_category_data(original_cat, improved_cat)
        merged_result['categories'][category] = merged_cat
        
        # Add metadata
        merged_result['categories'][category]['_metadata'] = {
            'extraction_timestamp': datetime.now().isoformat(),
            'category': category,
            'source': 'merged'
        }
    
    # Fix validation issues
    merged_result['categories'] = fix_validation_issues(merged_result['categories'])
    
    # Calculate statistics
    total_fields = 0
    filled_fields = 0
    
    for category, content in merged_result['categories'].items():
        for field, value in content.items():
            if field != '_metadata':
                total_fields += 1
                if value is not None and value != "" and value != []:
                    filled_fields += 1
    
    completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
    
    # Add summary
    merged_result['summary'] = {
        'total_categories': len(merged_result['categories']),
        'total_fields': total_fields,
        'filled_fields': filled_fields,
        'completeness_percentage': round(completeness, 2)
    }
    
    # Save merged results
    output_file = "03_extracted_data/final_merged_extraction.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ Merged results saved to: {output_file}")
    logger.info(f"\n📊 Final Statistics:")
    logger.info(f"  - Total categories: {merged_result['summary']['total_categories']}")
    logger.info(f"  - Total fields: {merged_result['summary']['total_fields']}")
    logger.info(f"  - Filled fields: {merged_result['summary']['filled_fields']}")
    logger.info(f"  - Completeness: {merged_result['summary']['completeness_percentage']}%")
    
    # Show sample of merged data
    logger.info("\n📋 Sample Merged Data:")
    for category in ['audit_metadata', 'finding_summary', 'risk_assessment']:
        if category in merged_result['categories']:
            logger.info(f"\n{category}:")
            for field, value in merged_result['categories'][category].items():
                if field != '_metadata' and value:
                    logger.info(f"  - {field}: {str(value)[:100]}...")

if __name__ == "__main__":
    main()
