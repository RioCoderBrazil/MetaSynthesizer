"""
Analyze extraction quality and generate improvement recommendations
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('extraction_analyzer')

def load_extraction_results(file_path: str) -> Dict:
    """Load extracted data from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_empty_categories(data: Dict) -> List[str]:
    """Identify categories with no extracted data"""
    empty_categories = []
    for category, content in data['categories'].items():
        # Check if category only has metadata
        if len(content) == 1 and '_metadata' in content:
            empty_categories.append(category)
    return empty_categories

def analyze_incomplete_fields(data: Dict) -> Dict[str, List[str]]:
    """Identify fields with null or empty values"""
    incomplete_fields = {}
    
    for category, content in data['categories'].items():
        if category in ['audit_metadata', 'compliance_status', 'process_assessment', 'stakeholder_analysis']:
            continue  # Skip empty categories
            
        missing_fields = []
        for field, value in content.items():
            if field != '_metadata':
                if value is None or (isinstance(value, str) and value == "") or (isinstance(value, list) and len(value) == 0):
                    missing_fields.append(field)
        
        if missing_fields:
            incomplete_fields[category] = missing_fields
    
    return incomplete_fields

def analyze_validation_issues(data: Dict) -> Dict[str, List[str]]:
    """Identify potential validation issues"""
    validation_issues = {}
    
    # Check finding_summary
    if 'finding_summary' in data['categories']:
        finding = data['categories']['finding_summary']
        issues = []
        if not finding.get('main_finding'):
            issues.append("main_finding is empty")
        if not finding.get('affected_areas'):
            issues.append("affected_areas is empty")
        if issues:
            validation_issues['finding_summary'] = issues
    
    # Check risk_assessment
    if 'risk_assessment' in data['categories']:
        risk = data['categories']['risk_assessment']
        issues = []
        if not risk.get('risk_level'):
            issues.append("risk_level is empty")
        if risk.get('residual_risk') and risk['residual_risk'] not in ['high', 'medium', 'low', 'none']:
            issues.append(f"residual_risk has invalid value: '{risk['residual_risk']}'")
        if issues:
            validation_issues['risk_assessment'] = issues
    
    return validation_issues

def generate_improvement_suggestions(empty_categories: List[str], incomplete_fields: Dict, validation_issues: Dict) -> List[str]:
    """Generate specific suggestions for improving extraction"""
    suggestions = []
    
    # Suggestions for empty categories
    if empty_categories:
        suggestions.append("\n### Empty Categories Need Attention:")
        for category in empty_categories:
            if category == 'audit_metadata':
                suggestions.append(f"- **{category}**: Look for audit report metadata like report number, audit period, auditor names, report date")
            elif category == 'compliance_status':
                suggestions.append(f"- **{category}**: Search for compliance requirements, regulations, and adherence status")
            elif category == 'process_assessment':
                suggestions.append(f"- **{category}**: Extract process evaluations, effectiveness ratings, and improvement areas")
            elif category == 'stakeholder_analysis':
                suggestions.append(f"- **{category}**: Identify stakeholders mentioned, their roles, and impacts")
    
    # Suggestions for incomplete fields
    if incomplete_fields:
        suggestions.append("\n### Incomplete Fields to Complete:")
        for category, fields in incomplete_fields.items():
            suggestions.append(f"- **{category}**: Missing {', '.join(fields)}")
    
    # Suggestions for validation issues
    if validation_issues:
        suggestions.append("\n### Validation Issues to Fix:")
        for category, issues in validation_issues.items():
            for issue in issues:
                suggestions.append(f"- **{category}**: {issue}")
    
    return suggestions

def main():
    """Main analysis function"""
    logger.info("=== Extraction Quality Analysis ===")
    
    # Load extracted data
    extraction_file = "03_extracted_data/11380BE_Revisionsbericht - Bewirtschaftung von Umweltrisiken - Altlasten und Sanierungskosten - coloured_extracted.json"
    data = load_extraction_results(extraction_file)
    
    # Analyze extraction quality
    empty_categories = analyze_empty_categories(data)
    incomplete_fields = analyze_incomplete_fields(data)
    validation_issues = analyze_validation_issues(data)
    
    # Display analysis results
    logger.info(f"\n📊 Extraction Statistics:")
    logger.info(f"Overall completeness: {data['statistics']['overall_completeness']:.1f}%")
    logger.info(f"Populated categories: {data['summary']['populated_categories']}/{data['summary']['total_categories']}")
    
    logger.info(f"\n❌ Empty Categories ({len(empty_categories)}):")
    for category in empty_categories:
        logger.info(f"  - {category}")
    
    logger.info(f"\n⚠️  Incomplete Fields:")
    for category, fields in incomplete_fields.items():
        logger.info(f"  - {category}: {len(fields)} missing fields")
    
    logger.info(f"\n🔧 Validation Issues:")
    for category, issues in validation_issues.items():
        logger.info(f"  - {category}: {len(issues)} issues")
    
    # Generate improvement suggestions
    suggestions = generate_improvement_suggestions(empty_categories, incomplete_fields, validation_issues)
    
    logger.info("\n💡 Improvement Suggestions:")
    for suggestion in suggestions:
        logger.info(suggestion)
    
    # Create improvement report
    improvement_report = {
        "analysis_timestamp": datetime.now().isoformat(),
        "statistics": {
            "overall_completeness": data['statistics']['overall_completeness'],
            "empty_categories": len(empty_categories),
            "categories_with_issues": len(incomplete_fields) + len(validation_issues)
        },
        "empty_categories": empty_categories,
        "incomplete_fields": incomplete_fields,
        "validation_issues": validation_issues,
        "improvement_actions": [
            {
                "priority": "high",
                "action": "Fix validation issues in risk_assessment and finding_summary",
                "details": "Update residual_risk to use valid enum values, fill main_finding field"
            },
            {
                "priority": "high", 
                "action": "Extract audit metadata",
                "details": "Look for report number, audit period, auditor information"
            },
            {
                "priority": "medium",
                "action": "Extract compliance and process information",
                "details": "Search for compliance requirements and process assessments"
            },
            {
                "priority": "medium",
                "action": "Complete cost analysis",
                "details": "Extract financial data, cost estimates, and savings potential"
            }
        ]
    }
    
    # Save improvement report
    report_path = "03_extracted_data/extraction_improvement_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(improvement_report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ Improvement report saved to: {report_path}")
    
    return improvement_report

if __name__ == "__main__":
    report = main()
