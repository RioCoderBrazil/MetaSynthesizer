"""
Category Merger - Merges and consolidates extracted data from multiple sources
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime
from ..utils.logger import logger
from ..utils.file_utils import save_json


class CategoryMerger:
    """
    Merges extracted data from multiple passes and sources
    """
    
    def __init__(self, schema_path: str = 'config/categories_schema_full.json'):
        """
        Initialize category merger
        
        Args:
            schema_path: Path to category schema
        """
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def merge_extractions(self, 
                         rag_data: Dict[str, Dict[str, Any]], 
                         manual_data: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Merge data from RAG extraction and optional manual annotations
        
        Args:
            rag_data: Data from RAG extraction
            manual_data: Optional manual annotations
            
        Returns:
            Merged data
        """
        merged = {}
        
        for category_name in self.schema['categories']:
            # Start with RAG data
            category_data = rag_data.get(category_name, {}).copy()
            
            # Merge with manual data if available
            if manual_data and category_name in manual_data:
                category_data = self._merge_category_data(
                    category_data, 
                    manual_data[category_name],
                    category_name
                )
            
            # Post-process merged data
            category_data = self._post_process_category(category_name, category_data)
            
            merged[category_name] = category_data
        
        return merged
    
    def _merge_category_data(self, 
                           rag_data: Dict[str, Any], 
                           manual_data: Dict[str, Any],
                           category_name: str) -> Dict[str, Any]:
        """
        Merge data for a single category
        
        Args:
            rag_data: RAG extracted data
            manual_data: Manual annotations
            category_name: Category name
            
        Returns:
            Merged data
        """
        merged = rag_data.copy()
        fields_schema = self.schema['categories'][category_name].get('fields', {})
        
        for field_name, manual_value in manual_data.items():
            if field_name not in fields_schema:
                continue
            
            field_type = fields_schema[field_name].get('type', 'text')
            rag_value = rag_data.get(field_name)
            
            # Merge based on field type
            if field_type == 'list':
                merged[field_name] = self._merge_lists(rag_value, manual_value)
            elif field_type == 'text':
                # Prefer manual over RAG if both exist
                if manual_value and (not rag_value or len(str(manual_value)) > len(str(rag_value))):
                    merged[field_name] = manual_value
            elif field_type == 'number':
                # Use manual if RAG is None or 0
                if manual_value is not None and (rag_value is None or rag_value == 0):
                    merged[field_name] = manual_value
            else:
                # For other types, prefer manual if available
                if manual_value is not None:
                    merged[field_name] = manual_value
        
        return merged
    
    def _merge_lists(self, list1: Optional[List], list2: Optional[List]) -> List:
        """
        Merge two lists, removing duplicates
        
        Args:
            list1: First list
            list2: Second list
            
        Returns:
            Merged list
        """
        if not list1:
            return list2 or []
        if not list2:
            return list1 or []
        
        # Combine and remove duplicates while preserving order
        seen = set()
        merged = []
        
        for item in list1 + list2:
            item_str = str(item).strip().lower()
            if item_str not in seen and item_str:
                seen.add(item_str)
                merged.append(item)
        
        return merged
    
    def _post_process_category(self, category_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process category data
        
        Args:
            category_name: Category name
            data: Category data
            
        Returns:
            Post-processed data
        """
        processed = data.copy()
        
        # Add metadata
        processed['_metadata'] = {
            'extraction_timestamp': datetime.now().isoformat(),
            'category': category_name,
            'source': 'rag_extraction'
        }
        
        # Category-specific processing
        if category_name == 'finding_summary':
            processed = self._process_finding_summary(processed)
        elif category_name == 'recommendation_tracking':
            processed = self._process_recommendations(processed)
        elif category_name == 'cost_analysis':
            processed = self._process_costs(processed)
        
        return processed
    
    def _process_finding_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process finding summary data
        
        Args:
            data: Finding data
            
        Returns:
            Processed data
        """
        # Auto-generate finding ID if missing
        if not data.get('finding_id'):
            data['finding_id'] = f"FIND-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Ensure priority is set
        if not data.get('priority'):
            # Try to infer from keywords
            text = str(data.get('main_finding', '')).lower()
            if any(word in text for word in ['kritisch', 'erheblich', 'wesentlich', 'hoch']):
                data['priority'] = 'high'
            elif any(word in text for word in ['mittel', 'moderat']):
                data['priority'] = 'medium'
            else:
                data['priority'] = 'low'
        
        return data
    
    def _process_recommendations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process recommendation data
        
        Args:
            data: Recommendation data
            
        Returns:
            Processed data
        """
        # Auto-generate recommendation ID if missing
        if not data.get('recommendation_id'):
            data['recommendation_id'] = f"REC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Set default status if missing
        if not data.get('status'):
            data['status'] = 'open'
        
        return data
    
    def _process_costs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process cost analysis data
        
        Args:
            data: Cost data
            
        Returns:
            Processed data
        """
        # Calculate total if individual components exist
        if 'identified_costs' in data and isinstance(data['identified_costs'], list):
            total = 0
            for cost_item in data['identified_costs']:
                if isinstance(cost_item, dict) and 'amount' in cost_item:
                    try:
                        total += float(cost_item['amount'])
                    except (ValueError, TypeError):
                        pass
            
            if total > 0 and not data.get('total_amount'):
                data['total_amount'] = total
        
        # Ensure currency is set
        if 'total_amount' in data and data['total_amount'] and not data.get('currency'):
            data['currency'] = 'CHF'
        
        return data
    
    def consolidate_report(self, merged_data: Dict[str, Dict[str, Any]], doc_id: str) -> Dict[str, Any]:
        """
        Consolidate all categories into final report structure
        
        Args:
            merged_data: Merged category data
            doc_id: Document ID
            
        Returns:
            Consolidated report
        """
        report = {
            'document_id': doc_id,
            'extraction_timestamp': datetime.now().isoformat(),
            'categories': merged_data,
            'summary': self._generate_summary(merged_data),
            'statistics': self._calculate_statistics(merged_data)
        }
        
        return report
    
    def _generate_summary(self, data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary of extracted data
        
        Args:
            data: All category data
            
        Returns:
            Summary dict
        """
        summary = {
            'total_categories': len(data),
            'populated_categories': sum(1 for cat_data in data.values() 
                                      if any(v for k, v in cat_data.items() 
                                           if not k.startswith('_'))),
            'total_findings': 0,
            'total_recommendations': 0,
            'total_costs_identified': 0
        }
        
        # Count findings
        if 'finding_summary' in data:
            findings = data['finding_summary'].get('related_findings', [])
            if isinstance(findings, list):
                summary['total_findings'] = len(findings)
        
        # Count recommendations  
        if 'recommendation_tracking' in data:
            recs = data['recommendation_tracking'].get('follow_up_actions', [])
            if isinstance(recs, list):
                summary['total_recommendations'] = len(recs)
        
        # Sum costs
        if 'cost_analysis' in data:
            total = data['cost_analysis'].get('total_amount', 0)
            if isinstance(total, (int, float)):
                summary['total_costs_identified'] = total
        
        return summary
    
    def _calculate_statistics(self, data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate extraction statistics
        
        Args:
            data: All category data
            
        Returns:
            Statistics dict
        """
        stats = {
            'extraction_completeness': {},
            'field_coverage': {}
        }
        
        for category_name, category_data in data.items():
            if category_name not in self.schema['categories']:
                continue
            
            fields_schema = self.schema['categories'][category_name].get('fields', {})
            total_fields = len(fields_schema)
            filled_fields = sum(1 for field_name in fields_schema 
                              if category_data.get(field_name) is not None)
            
            completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
            
            stats['extraction_completeness'][category_name] = round(completeness, 2)
            stats['field_coverage'][category_name] = f"{filled_fields}/{total_fields}"
        
        # Overall completeness
        all_completeness = list(stats['extraction_completeness'].values())
        stats['overall_completeness'] = round(
            sum(all_completeness) / len(all_completeness), 2
        ) if all_completeness else 0
        
        return stats
    
    def save_results(self, report: Dict[str, Any], output_dir: str = '03_extracted_data') -> str:
        """
        Save extraction results
        
        Args:
            report: Consolidated report
            output_dir: Output directory
            
        Returns:
            Path to saved file
        """
        doc_id = report['document_id']
        filename = f"{doc_id}_extracted.json"
        filepath = save_json(report, output_dir, filename)
        
        logger.info(f"Saved extraction results to: {filepath}")
        return filepath
