"""
Schema Validator - Validates extracted data against category schema
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import re
from ..utils.logger import logger


class SchemaValidator:
    """
    Validates extracted data against the predefined schema
    """
    
    def __init__(self, schema_path: str = 'config/categories_schema_full.json'):
        """
        Initialize schema validator
        
        Args:
            schema_path: Path to category schema JSON
        """
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def validate_category_data(self, category_name: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data for a specific category
        
        Args:
            category_name: Name of the category
            data: Extracted data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if category exists
        if category_name not in self.schema['categories']:
            errors.append(f"Unknown category: {category_name}")
            return False, errors
        
        category_schema = self.schema['categories'][category_name]
        fields_schema = category_schema.get('fields', {})
        
        # Validate each field
        for field_name, field_schema in fields_schema.items():
            field_value = data.get(field_name)
            field_errors = self._validate_field(field_name, field_value, field_schema)
            errors.extend(field_errors)
        
        # Check for extra fields not in schema
        extra_fields = set(data.keys()) - set(fields_schema.keys())
        if extra_fields:
            errors.append(f"Extra fields not in schema: {', '.join(extra_fields)}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_field(self, field_name: str, value: Any, field_schema: Dict[str, Any]) -> List[str]:
        """
        Validate a single field
        
        Args:
            field_name: Name of the field
            value: Field value
            field_schema: Field schema definition
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check if required field is missing
        is_required = field_schema.get('required', False)
        if is_required and (value is None or value == ""):
            errors.append(f"Required field '{field_name}' is missing or empty")
            return errors
        
        # If value is None and not required, skip further validation
        if value is None:
            return errors
        
        # Validate field type
        field_type = field_schema.get('type', 'text')
        type_errors = self._validate_type(field_name, value, field_type)
        errors.extend(type_errors)
        
        # Validate max length for text fields
        if field_type in ['text', 'list'] and 'max_length' in field_schema:
            max_length = field_schema['max_length']
            if isinstance(value, str) and len(value) > max_length:
                errors.append(f"Field '{field_name}' exceeds max length of {max_length} characters")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and len(item) > max_length:
                        errors.append(f"Item {i} in field '{field_name}' exceeds max length of {max_length}")
        
        # Validate enum values
        if 'enum' in field_schema:
            allowed_values = field_schema['enum']
            if value not in allowed_values:
                errors.append(f"Field '{field_name}' has invalid value '{value}'. Allowed: {allowed_values}")
        
        # Validate date format
        if field_type == 'date' and isinstance(value, str):
            date_errors = self._validate_date_format(field_name, value)
            errors.extend(date_errors)
        
        # Validate numeric ranges
        if field_type == 'number' and isinstance(value, (int, float)):
            if 'min' in field_schema and value < field_schema['min']:
                errors.append(f"Field '{field_name}' value {value} is below minimum {field_schema['min']}")
            if 'max' in field_schema and value > field_schema['max']:
                errors.append(f"Field '{field_name}' value {value} is above maximum {field_schema['max']}")
        
        return errors
    
    def _validate_type(self, field_name: str, value: Any, expected_type: str) -> List[str]:
        """
        Validate field type
        
        Args:
            field_name: Field name
            value: Field value
            expected_type: Expected type
            
        Returns:
            List of type validation errors
        """
        errors = []
        
        type_mapping = {
            'text': str,
            'number': (int, float),
            'date': str,  # Dates are stored as strings
            'boolean': bool,
            'list': list,
            'object': dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type and not isinstance(value, expected_python_type):
            errors.append(f"Field '{field_name}' has wrong type. Expected {expected_type}, got {type(value).__name__}")
        
        return errors
    
    def _validate_date_format(self, field_name: str, date_str: str) -> List[str]:
        """
        Validate date format
        
        Args:
            field_name: Field name
            date_str: Date string
            
        Returns:
            List of date validation errors
        """
        errors = []
        
        # Common date formats in Swiss reports
        date_formats = [
            "%d.%m.%Y",  # 31.12.2023
            "%d. %B %Y",  # 31. Dezember 2023
            "%B %Y",  # Dezember 2023
            "%Y-%m-%d",  # ISO format
            "%d/%m/%Y"   # Alternative format
        ]
        
        valid_format = False
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                valid_format = True
                break
            except ValueError:
                continue
        
        if not valid_format:
            errors.append(f"Field '{field_name}' has invalid date format: '{date_str}'")
        
        return errors
    
    def validate_all_categories(self, extracted_data: Dict[str, Dict[str, Any]]) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all categories
        
        Args:
            extracted_data: Dictionary of category data
            
        Returns:
            Dictionary of validation results per category
        """
        validation_results = {}
        
        for category_name, category_data in extracted_data.items():
            is_valid, errors = self.validate_category_data(category_name, category_data)
            validation_results[category_name] = (is_valid, errors)
            
            if not is_valid:
                logger.warning(f"Validation failed for {category_name}: {errors}")
            else:
                logger.info(f"Validation passed for {category_name}")
        
        return validation_results
    
    def fix_common_issues(self, category_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to fix common validation issues
        
        Args:
            category_name: Category name
            data: Data to fix
            
        Returns:
            Fixed data
        """
        if category_name not in self.schema['categories']:
            return data
        
        fixed_data = data.copy()
        fields_schema = self.schema['categories'][category_name].get('fields', {})
        
        for field_name, field_schema in fields_schema.items():
            if field_name not in fixed_data:
                continue
                
            value = fixed_data[field_name]
            field_type = field_schema.get('type', 'text')
            
            # Fix None values for required fields
            if value is None and field_schema.get('required', False):
                if field_type == 'text':
                    fixed_data[field_name] = ""
                elif field_type == 'list':
                    fixed_data[field_name] = []
                elif field_type == 'number':
                    fixed_data[field_name] = 0
                elif field_type == 'boolean':
                    fixed_data[field_name] = False
            
            # Truncate text that's too long
            if field_type == 'text' and isinstance(value, str) and 'max_length' in field_schema:
                max_length = field_schema['max_length']
                if len(value) > max_length:
                    fixed_data[field_name] = value[:max_length-3] + "..."
                    logger.warning(f"Truncated {field_name} from {len(value)} to {max_length} characters")
            
            # Convert numeric strings to numbers
            if field_type == 'number' and isinstance(value, str):
                # Try to extract number from string like "33.3 Mio. CHF"
                number_match = re.search(r'[\d,]+\.?\d*', value.replace(',', ''))
                if number_match:
                    try:
                        fixed_data[field_name] = float(number_match.group())
                        if 'Mio' in value or 'Million' in value:
                            fixed_data[field_name] *= 1_000_000
                        logger.info(f"Converted '{value}' to {fixed_data[field_name]}")
                    except ValueError:
                        pass
            
            # Ensure lists are lists
            if field_type == 'list' and isinstance(value, str):
                # Try to split string into list
                if '\n' in value:
                    fixed_data[field_name] = [item.strip() for item in value.split('\n') if item.strip()]
                elif ',' in value:
                    fixed_data[field_name] = [item.strip() for item in value.split(',') if item.strip()]
                else:
                    fixed_data[field_name] = [value]
        
        return fixed_data
