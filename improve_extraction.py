"""
Improved extraction script with targeted queries for missing categories
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
project_root = Path(__file__).parent
env_path = project_root / '.env'
load_dotenv(env_path, override=True)

from src.pass2.rag_extractor import RAGExtractor
from src.pass2.schema_validator import SchemaValidator
from src.pass2.category_merger import CategoryMerger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('improved_extraction')

class ImprovedRAGExtractor(RAGExtractor):
    """Enhanced RAG extractor with better query generation for empty categories"""
    
    def generate_extraction_queries(self, category_name: str, schema: Dict) -> List[str]:
        """Generate improved queries for empty categories"""
        
        # Special queries for problematic categories
        special_queries = {
            'audit_metadata': [
                "Revisionsbericht Nummer Prüfungsnummer Audit Report Number",
                "Prüfungszeitraum Audit Period Berichtsdatum Report Date", 
                "Eidgenössische Finanzkontrolle EFK Prüfer Auditor Names",
                "Bericht Nr. Report ID Dokument Nummer",
                "Verantwortlich Responsible Audit Team"
            ],
            'compliance_status': [
                "Compliance Anforderungen Requirements Vorschriften Regulations",
                "Gesetzliche Bestimmungen Legal Requirements Compliance Status",
                "Einhaltung Adherence Konformität Conformity",
                "Regulatorische Anforderungen Regulatory Requirements",
                "Compliance Bewertung Assessment Evaluation"
            ],
            'process_assessment': [
                "Prozessbewertung Process Evaluation Assessment",
                "Wirksamkeit Effectiveness Effizienz Efficiency",
                "Verbesserungsbereiche Improvement Areas Optimierung",
                "Prozessreife Process Maturity Bewertung",
                "Kontrollmechanismen Control Mechanisms"
            ],
            'stakeholder_analysis': [
                "Stakeholder Beteiligte Parties Akteure",
                "ar Immo BAV UVEK Departement",
                "Verantwortlichkeiten Responsibilities Rollen Roles",
                "Betroffene Affected Parties Impacts",
                "Bundesamt Federal Office Ministry"
            ],
            'cost_analysis': [
                "Kosten Costs CHF Franken Amount",
                "Sanierungskosten Remediation Costs Cleanup",
                "Finanzielle Financial Monetary Betrag",
                "Rückstellungen Provisions Reserves",
                "Einsparungspotenzial Savings Potential"
            ]
        }
        
        if category_name in special_queries:
            return special_queries[category_name]
        
        # Fall back to original query generation
        return super().generate_extraction_queries(category_name, schema)
    
    def create_extraction_prompt(self, category_name: str, schema: Dict, contexts: List[str]) -> str:
        """Create improved extraction prompt with better instructions"""
        
        # Enhanced prompts for specific categories
        enhanced_instructions = {
            'finding_summary': """
IMPORTANT: Extract the MAIN finding or conclusion from the audit report.
Look for:
- Key findings (Feststellungen)
- Main conclusions (Hauptschlussfolgerungen)  
- Summary statements about risks or issues
- Overall assessment of the audited area

For 'main_finding', provide a clear summary sentence of the primary audit finding.
For 'affected_areas', list all organizational units, departments, or areas impacted.
""",
            'risk_assessment': """
IMPORTANT: For 'risk_level', use ONLY one of these values: 'high', 'medium', 'low', 'none'
For 'residual_risk', use ONLY one of these values: 'high', 'medium', 'low', 'none'

Do NOT use descriptive text for these fields - only the allowed values.
Extract the actual risk level assessment from the document.
""",
            'audit_metadata': """
Extract metadata about the audit report itself:
- Report number (e.g., "22415" or similar)
- Audit period (dates covered by the audit)
- Report date (when the report was issued)
- Auditor names or audit team
- Department or organization conducting the audit (e.g., "Eidgenössische Finanzkontrolle")
"""
        }
        
        base_prompt = super().create_extraction_prompt(category_name, schema, contexts)
        
        if category_name in enhanced_instructions:
            # Insert enhanced instructions after the schema description
            parts = base_prompt.split("\n\n")
            parts.insert(2, enhanced_instructions[category_name])
            return "\n\n".join(parts)
        
        return base_prompt

def main():
    """Run improved extraction"""
    logger.info("=== Starting Improved Extraction ===")
    
    # Initialize components
    extractor = ImprovedRAGExtractor(
        qdrant_host="localhost",
        qdrant_port=6333,
        collection_name="metasynthesizer"
    )
    validator = SchemaValidator()
    merger = CategoryMerger()
    
    # Test document
    test_doc = "11380BE_Revisionsbericht - Bewirtschaftung von Umweltrisiken - Altlasten und Sanierungskosten - coloured"
    
    # Focus on empty and incomplete categories
    priority_categories = [
        'audit_metadata',      # Empty
        'compliance_status',   # Empty
        'finding_summary',     # Has validation issues
        'risk_assessment',     # Has validation issues
        'cost_analysis'        # Empty fields
    ]
    
    results = {}
    
    for category in priority_categories:
        logger.info(f"\n📋 Extracting: {category}")
        try:
            extracted = extractor.extract_for_category(category, test_doc)
            results[category] = extracted
            
            # Validate
            is_valid, errors = validator.validate_category_data(category, extracted)
            if is_valid:
                logger.info(f"✅ {category}: Valid extraction")
            else:
                logger.warning(f"⚠️  {category}: Validation issues - {errors}")
                
        except Exception as e:
            logger.error(f"❌ {category}: Extraction failed - {e}")
            results[category] = {}
    
    # Save improved results
    output_file = "03_extracted_data/improved_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "document_id": test_doc,
            "extraction_method": "improved_rag",
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ Improved results saved to: {output_file}")
    
    # Compare with original
    logger.info("\n📊 Extraction Improvement Summary:")
    for category in priority_categories:
        if category in results and results[category]:
            field_count = len([k for k in results[category].keys() if k != '_metadata' and results[category][k] is not None])
            logger.info(f"  - {category}: {field_count} fields extracted")

if __name__ == "__main__":
    main()
