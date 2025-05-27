#!/usr/bin/env python3
"""
MetaSynthesizer Data Validator
Validate extracted data for completeness and correctness
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import re
from pathlib import Path
import json


class DataValidator:
    """Validate extracted data against schema and business rules"""
    
    def __init__(self):
        self.required_categories = [
            "risk_assessment",
            "recommendation_tracking", 
            "finding_summary",
            "environmental_impact",
            "timeline_analysis",
            "stakeholder_info",
            "compliance_status",
            "audit_metadata",
            "financial_data"
        ]
        
        self.risk_levels = ["high", "medium", "low", "unknown"]
        self.priority_levels = ["high", "medium", "low", "unknown"]
        self.status_options = ["open", "in_progress", "closed", "unknown"]
    
    def validate_extraction(self, extraction: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a single extraction result
        Returns: (is_valid, validation_report)
        """
        report = {
            "document_id": extraction.get("document_id", "Unknown"),
            "validation_timestamp": datetime.now().isoformat(),
            "overall_valid": True,
            "errors": [],
            "warnings": [],
            "category_validation": {},
            "completeness_score": 0
        }
        
        # Check basic structure
        if not isinstance(extraction, dict):
            report["overall_valid"] = False
            report["errors"].append("Extraction is not a dictionary")
            return False, report
        
        if "categories" not in extraction:
            report["overall_valid"] = False
            report["errors"].append("Missing 'categories' field")
            return False, report
        
        categories = extraction.get("categories", {})
        
        # Validate each category
        filled_categories = 0
        for category in self.required_categories:
            cat_report = self._validate_category(category, categories.get(category, {}))
            report["category_validation"][category] = cat_report
            
            if cat_report["has_data"]:
                filled_categories += 1
            
            if not cat_report["is_valid"]:
                report["overall_valid"] = False
                report["errors"].extend(cat_report["errors"])
            
            report["warnings"].extend(cat_report["warnings"])
        
        # Calculate completeness score
        report["completeness_score"] = (filled_categories / len(self.required_categories)) * 100
        
        # Check extraction metadata
        if "extraction_timestamp" not in extraction:
            report["warnings"].append("Missing extraction timestamp")
        
        if "extraction_method" not in extraction:
            report["warnings"].append("Missing extraction method")
        
        return report["overall_valid"], report
    
    def _validate_category(self, category_name: str, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a specific category"""
        validation = {
            "category": category_name,
            "has_data": bool(category_data),
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "field_count": len(category_data) if category_data else 0
        }
        
        if not category_data:
            validation["warnings"].append(f"Category '{category_name}' is empty")
            return validation
        
        # Category-specific validation
        if category_name == "risk_assessment":
            validation = self._validate_risk_assessment(category_data, validation)
        elif category_name == "recommendation_tracking":
            validation = self._validate_recommendation_tracking(category_data, validation)
        elif category_name == "finding_summary":
            validation = self._validate_finding_summary(category_data, validation)
        elif category_name == "environmental_impact":
            validation = self._validate_environmental_impact(category_data, validation)
        elif category_name == "timeline_analysis":
            validation = self._validate_timeline_analysis(category_data, validation)
        elif category_name == "stakeholder_info":
            validation = self._validate_stakeholder_info(category_data, validation)
        elif category_name == "compliance_status":
            validation = self._validate_compliance_status(category_data, validation)
        elif category_name == "audit_metadata":
            validation = self._validate_audit_metadata(category_data, validation)
        elif category_name == "financial_data":
            validation = self._validate_financial_data(category_data, validation)
        
        return validation
    
    def _validate_risk_assessment(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate risk assessment data"""
        # Check risk level
        if "risk_level" in data:
            if data["risk_level"] not in self.risk_levels:
                validation["errors"].append(f"Invalid risk level: {data['risk_level']}")
                validation["is_valid"] = False
        else:
            validation["warnings"].append("Missing risk_level")
        
        # Check risk description
        if not data.get("risk_description"):
            validation["warnings"].append("Missing risk_description")
        
        # Check mitigation measures
        if "mitigation_measures" in data:
            if not isinstance(data["mitigation_measures"], list):
                validation["errors"].append("mitigation_measures must be a list")
                validation["is_valid"] = False
        
        # Check residual risk
        if "residual_risk" in data and data["residual_risk"] not in self.risk_levels:
            validation["warnings"].append(f"Invalid residual_risk: {data['residual_risk']}")
        
        return validation
    
    def _validate_recommendation_tracking(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate recommendation tracking data"""
        # Check recommendation text
        if not data.get("recommendation_text"):
            validation["warnings"].append("Missing recommendation_text")
        
        # Check status
        if "status" in data:
            if data["status"] not in self.status_options:
                validation["errors"].append(f"Invalid status: {data['status']}")
                validation["is_valid"] = False
        else:
            validation["warnings"].append("Missing status")
        
        # Check responsible entity
        if not data.get("responsible_entity"):
            validation["warnings"].append("Missing responsible_entity")
        
        # Check deadline format if present
        if "deadline" in data and data["deadline"]:
            if not self._is_valid_date(str(data["deadline"])):
                validation["warnings"].append(f"Invalid deadline format: {data['deadline']}")
        
        return validation
    
    def _validate_finding_summary(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate finding summary data"""
        # Check main finding
        if not data.get("main_finding"):
            validation["warnings"].append("Missing main_finding")
        
        # Check priority
        if "priority" in data:
            if data["priority"] not in self.priority_levels:
                validation["errors"].append(f"Invalid priority: {data['priority']}")
                validation["is_valid"] = False
        else:
            validation["warnings"].append("Missing priority")
        
        # Check affected areas
        if "affected_areas" in data:
            if not isinstance(data["affected_areas"], list):
                validation["errors"].append("affected_areas must be a list")
                validation["is_valid"] = False
        
        # Validate finding ID format
        if "finding_id" in data:
            if not self._is_valid_finding_id(data["finding_id"]):
                validation["warnings"].append(f"Invalid finding_id format: {data['finding_id']}")
        
        return validation
    
    def _validate_environmental_impact(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate environmental impact data"""
        if "impact_level" in data:
            if data["impact_level"] not in ["high", "medium", "low", "none", "unknown"]:
                validation["warnings"].append(f"Invalid impact_level: {data['impact_level']}")
        
        if "environmental_risks" in data:
            if not isinstance(data["environmental_risks"], list):
                validation["errors"].append("environmental_risks must be a list")
                validation["is_valid"] = False
        
        return validation
    
    def _validate_timeline_analysis(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate timeline analysis data"""
        if "key_dates" in data:
            if not isinstance(data["key_dates"], list):
                validation["errors"].append("key_dates must be a list")
                validation["is_valid"] = False
        
        if "audit_period" in data:
            period = data["audit_period"]
            if isinstance(period, dict):
                if "start" in period and period["start"]:
                    if not self._is_valid_date(str(period["start"])):
                        validation["warnings"].append(f"Invalid audit_period start date: {period['start']}")
                if "end" in period and period["end"]:
                    if not self._is_valid_date(str(period["end"])):
                        validation["warnings"].append(f"Invalid audit_period end date: {period['end']}")
        
        return validation
    
    def _validate_stakeholder_info(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stakeholder info data"""
        if "stakeholders" in data:
            if not isinstance(data["stakeholders"], list):
                validation["errors"].append("stakeholders must be a list")
                validation["is_valid"] = False
            else:
                for stakeholder in data["stakeholders"]:
                    if isinstance(stakeholder, dict):
                        if not stakeholder.get("name") and not stakeholder.get("role"):
                            validation["warnings"].append("Stakeholder missing name and role")
        
        return validation
    
    def _validate_compliance_status(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance status data"""
        if "overall_compliance" in data:
            if data["overall_compliance"] not in ["compliant", "non_compliant", "partially_compliant", "unknown"]:
                validation["warnings"].append(f"Invalid overall_compliance: {data['overall_compliance']}")
        
        if "compliance_items" in data:
            if not isinstance(data["compliance_items"], list):
                validation["errors"].append("compliance_items must be a list")
                validation["is_valid"] = False
        
        return validation
    
    def _validate_audit_metadata(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate audit metadata"""
        expected_fields = ["audit_type", "audit_period", "auditor", "department"]
        
        for field in expected_fields:
            if field not in data or not data[field]:
                validation["warnings"].append(f"Missing or empty {field}")
        
        return validation
    
    def _validate_financial_data(self, data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate financial data"""
        if "amounts" in data:
            if not isinstance(data["amounts"], list):
                validation["errors"].append("amounts must be a list")
                validation["is_valid"] = False
            else:
                for amount in data["amounts"]:
                    if isinstance(amount, dict):
                        if "value" in amount and not isinstance(amount["value"], (int, float)):
                            validation["warnings"].append("Financial amount value should be numeric")
        
        return validation
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if a string is a valid date"""
        # Accept various date formats
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}\.\d{2}\.\d{4}$',  # DD.MM.YYYY
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{4}$'  # Just year
        ]
        
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    def _is_valid_finding_id(self, finding_id: str) -> bool:
        """Check if finding ID follows expected format"""
        # Format: FIND-YYYYMMDD-HHMMSS or simple numeric/alphanumeric
        patterns = [
            r'^FIND-\d{8}-\d{6}$',  # FIND-20250526-201710
            r'^\d+(\.\d+)?$',  # 6.3
            r'^[A-Z0-9_-]+$'  # General ID
        ]
        
        return any(re.match(pattern, finding_id) for pattern in patterns)
    
    def validate_batch(self, extractions: List[Dict[str, Any]], output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Validate a batch of extractions"""
        batch_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_documents": len(extractions),
            "valid_documents": 0,
            "invalid_documents": 0,
            "average_completeness": 0,
            "category_coverage": {},
            "common_errors": {},
            "document_reports": []
        }
        
        completeness_scores = []
        all_errors = []
        
        for extraction in extractions:
            is_valid, report = self.validate_extraction(extraction)
            batch_report["document_reports"].append(report)
            
            if is_valid:
                batch_report["valid_documents"] += 1
            else:
                batch_report["invalid_documents"] += 1
            
            completeness_scores.append(report["completeness_score"])
            all_errors.extend(report["errors"])
        
        # Calculate average completeness
        if completeness_scores:
            batch_report["average_completeness"] = sum(completeness_scores) / len(completeness_scores)
        
        # Calculate category coverage
        for category in self.required_categories:
            filled_count = sum(
                1 for report in batch_report["document_reports"]
                if report["category_validation"].get(category, {}).get("has_data", False)
            )
            batch_report["category_coverage"][category] = (filled_count / len(extractions)) * 100
        
        # Find common errors
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        batch_report["common_errors"] = dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Save report if output directory provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            report_path = output_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(batch_report, f, indent=2, ensure_ascii=False)
            
            # Also save summary
            summary_path = output_dir / "validation_summary.json"
            summary = {
                "last_validation": batch_report["validation_timestamp"],
                "total_documents": batch_report["total_documents"],
                "valid_documents": batch_report["valid_documents"],
                "average_completeness": batch_report["average_completeness"],
                "category_coverage": batch_report["category_coverage"]
            }
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return batch_report
    
    def auto_fix_common_issues(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically fix common validation issues"""
        categories = extraction.get("categories", {})
        
        # Fix risk levels
        if "risk_assessment" in categories:
            risk_data = categories["risk_assessment"]
            if "risk_level" in risk_data and risk_data["risk_level"] not in self.risk_levels:
                # Try to map common variations
                level_map = {
                    "hoch": "high", "mittel": "medium", "niedrig": "low",
                    "high risk": "high", "medium risk": "medium", "low risk": "low"
                }
                risk_data["risk_level"] = level_map.get(risk_data["risk_level"].lower(), "unknown")
        
        # Fix status values
        if "recommendation_tracking" in categories:
            rec_data = categories["recommendation_tracking"]
            if "status" in rec_data and rec_data["status"] not in self.status_options:
                status_map = {
                    "offen": "open", "in bearbeitung": "in_progress", 
                    "geschlossen": "closed", "pending": "open"
                }
                rec_data["status"] = status_map.get(rec_data["status"].lower(), "unknown")
        
        # Fix priority values
        if "finding_summary" in categories:
            finding_data = categories["finding_summary"]
            if "priority" in finding_data and finding_data["priority"] not in self.priority_levels:
                priority_map = {
                    "hoch": "high", "mittel": "medium", "niedrig": "low",
                    "critical": "high", "normal": "medium", "minor": "low"
                }
                finding_data["priority"] = priority_map.get(finding_data["priority"].lower(), "unknown")
        
        return extraction


def main():
    """Test the validator"""
    validator = DataValidator()
    
    # Test with sample data
    test_extraction = {
        "document_id": "Test Document",
        "extraction_timestamp": datetime.now().isoformat(),
        "categories": {
            "risk_assessment": {
                "risk_level": "high",
                "risk_description": "Test risk",
                "mitigation_measures": ["Measure 1", "Measure 2"]
            },
            "finding_summary": {
                "main_finding": "Test finding",
                "priority": "medium"
            }
        }
    }
    
    is_valid, report = validator.validate_extraction(test_extraction)
    print(f"Validation result: {'VALID' if is_valid else 'INVALID'}")
    print(f"Completeness: {report['completeness_score']:.1f}%")
    print(f"Errors: {len(report['errors'])}")
    print(f"Warnings: {len(report['warnings'])}")


if __name__ == "__main__":
    main()
