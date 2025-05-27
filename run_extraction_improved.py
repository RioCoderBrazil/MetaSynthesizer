#!/usr/bin/env python3
"""
Improved RAG-based Extraction Pipeline for CORRECT Categories
Extracts 23 categories with proper quote handling and page numbers
"""

import json
import os
import sys
import asyncio
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from dotenv import load_dotenv
from anthropic import Anthropic
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction_improved.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('extraction')

@dataclass
class ExtractionResult:
    """Result of extracting categories from a document"""
    document_id: str
    categories: Dict[str, Any]
    extraction_timestamp: str
    analysis: Dict[str, Any]

class ImprovedRAGExtractor:
    """Improved RAG-based extractor with better quote handling"""
    
    def __init__(self):
        # Load environment variables from project root
        project_root = Path(__file__).parent.absolute()
        env_path = project_root / '.env'
        load_dotenv(env_path)
        
        # Initialize clients
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        
        # Setup
        self.collection_name = "metasynthesizer"
        self.load_categories_schema()
        
    def load_categories_schema(self):
        """Load the correct categories schema"""
        schema_path = Path(__file__).parent / 'config' / 'categories_schema_correct.json'
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.categories_schema = json.load(f)
    
    def extract_berichtdatum_from_context(self, context: str) -> str:
        """Extract Berichtdatum using multiple date patterns"""
        # Various date patterns to try
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # ISO format
            r'(\d{1,2}\.\d{1,2}\.\d{4})',  # German format
            r'(\d{1,2})\.\s*(\w+)\s+(\d{4})',  # Written date
            r'Berichtdatum[:\s]+(\d{4}-\d{2}-\d{2})',  # With label
            r'Datum[:\s]+(\d{1,2}\.\d{1,2}\.\d{4})',  # With Datum label
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:  # Written date
                    # Convert written month to number
                    months = {
                        'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
                        'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
                        'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
                    }
                    day, month_name, year = match.groups()
                    month = months.get(month_name.lower(), '01')
                    return f"{year}-{month}-{day.zfill(2)}"
                else:
                    date_str = match.group(1)
                    # Convert German format to ISO
                    if '.' in date_str:
                        parts = date_str.split('.')
                        if len(parts) == 3:
                            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    return date_str
        
        return None
    
    def extract_quotes_with_pages(self, doc_id: str, category_name: str, query_vector) -> Optional[str]:
        """Extract quotes with page numbers for quote categories"""
        # Search for relevant chunks
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=10,
            query_filter=Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]
            )
        )
        
        quotes = []
        seen_quotes = set()
        
        # Define patterns based on category
        if category_name == "Umwelt, Info A (Relevante Akteure)":
            patterns = [
                r'["""](.*?(?:zuvorkommend erteilt|Rolle zur konformen Umsetzung|Verantwortlich für die Umsetzung|nutzt das KbS aktiv|notwendigen Auskünfte|Vollzugsbehörde).*?)["""]',
                r'(Die notwendigen Auskünfte.*?erteilt\.)',
                r'(Die Rolle.*?zugewiesen\.)',
                r'(Verantwortlich für.*?VBS)'
            ]
        elif category_name == "Umwelt, Info B (Berichtsprache/Datei)":
            patterns = [
                r'["""](.*?(?:technischen Untersuchungen|fehlende Frist führt|Beide Dokumente|können bis.*?dauern|nicht messbar geplant).*?)["""]',
                r'(Die technischen Untersuchungen.*?bedingt\.)',
                r'(Die fehlende Frist.*?darstellen\.)',
                r'(Beide Dokumente.*?pendent\.)'
            ]
        elif category_name == "Umwelt, Info C (Bedenken/Monitoring)":
            patterns = [
                r'["""](.*?(?:kein Berichtswesen|keine erkennbare Aufsicht|Prozessbeschrieb.*?liegt nicht vor|nicht ausreichend.*?informiert).*?)["""]',
                r'(Bisher bestand kein Berichtswesen.*?informiert\.)',
                r'(Es wird keine erkennbare Aufsicht.*?erwähnt\.)',
                r'(Ein Prozessbeschrieb.*?nicht vor\.)'
            ]
        elif "Flankieigend" in category_name:
            patterns = [
                r'["""](.*?)["""]',
                r'(Die fehlende Frist.*?darstellen\.)',
                r'(Der.*?Aktionsplan.*?detailliert)',
                r'(Die technischen Untersuchungen.*?angeordnet\.)'
            ]
        else:
            patterns = [r'["""](.*?)["""]']
        
        # Process each chunk
        for result in results:
            chunk = result.payload
            text = chunk.get('text', '')
            start_page = chunk.get('start_page', 0)
            end_page = chunk.get('end_page', start_page)
            
            # Try each pattern
            for pattern in patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                
                for match in matches:
                    # Clean the quote
                    if isinstance(match, tuple):
                        match = match[0]
                    cleaned = match.strip()
                    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
                    
                    # Check if quote is valid and not duplicate
                    if cleaned and len(cleaned) > 30 and cleaned not in seen_quotes:
                        seen_quotes.add(cleaned)
                        # Format with page reference
                        page_ref = f"(S. {start_page})" if start_page == end_page else f"(S. {start_page}-{end_page})"
                        quotes.append(f'"{cleaned}" {page_ref}')
        
        # Return formatted quotes
        if quotes:
            return "\n\n".join(quotes[:5])  # Limit to 5 best quotes
        return None
    
    def extract_recommendations_with_pages(self, doc_id: str, query_vector) -> Optional[str]:
        """Extract recommendations with page numbers"""
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=10,
            query_filter=Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]
            )
        )
        
        recommendations = []
        seen_recs = set()
        
        # Pattern for recommendations
        patterns = [
            r'Empfehlung\s+(\d+)\s*\(Priorität\s*(\d+)\)\s*\n?(.*?)(?=Empfehlung|\Z)',
            r'Die EFK empfiehlt.*?[,\.](?:\s*[A-Z]|$)',
            r'EFK-Empfehlung.*?[,\.](?:\s*[A-Z]|$)'
        ]
        
        for result in results:
            chunk = result.payload
            text = chunk.get('text', '')
            start_page = chunk.get('start_page', 0)
            
            # Try structured pattern first
            matches = re.findall(patterns[0], text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                emp_num, priority, text_content = match
                cleaned = text_content.strip()
                if cleaned and cleaned not in seen_recs:
                    seen_recs.add(cleaned)
                    page_ref = f"(S. {start_page})"
                    recommendations.append(f"Empfehlung {emp_num} (Priorität {priority}): {cleaned} {page_ref}")
            
            # Try other patterns
            for pattern in patterns[1:]:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    cleaned = match.strip()
                    if cleaned and len(cleaned) > 20 and cleaned not in seen_recs:
                        seen_recs.add(cleaned)
                        page_ref = f"(S. {start_page})"
                        recommendations.append(f"{cleaned} {page_ref}")
        
        if recommendations:
            return "\n\n".join(recommendations[:5])  # Limit to 5 recommendations
        return None
    
    def extract_category(self, doc_id: str, category_name: str, context: str) -> Optional[str]:
        """Extract a single category from context"""
        logger.info(f"    Extracting {category_name}...")
        
        try:
            # Special handling for PA-Nummer from filename
            if category_name == "PA-Nummer":
                # Extract from filename
                match = re.search(r'^(\d+[A-Z]{2})', doc_id)
                if match:
                    return match.group(1)
            
            # Special handling for Berichtdatum
            if category_name == "Berichtdatum":
                date_result = self.extract_berichtdatum_from_context(context)
                if date_result:
                    return date_result
            
            schema = self.categories_schema[category_name]
            query_vector = self.encoder.encode(category_name).tolist()
            
            # Handle quote categories with page numbers
            if category_name in [
                "Umwelt, Info A (Relevante Akteure)",
                "Umwelt, Info B (Berichtsprache/Datei)",
                "Umwelt, Info C (Bedenken/Monitoring)",
                "Flankieigend A (kein Plan)",
                "Flankieigend B (Plan unvollständig)",
                "Flankieigend C (in der Nachverfolgung)"
            ]:
                result = self.extract_quotes_with_pages(doc_id, category_name, query_vector)
                if result:
                    return result
            
            # Handle recommendations with page numbers
            if category_name == "Empfehlungen":
                result = self.extract_recommendations_with_pages(doc_id, query_vector)
                if result:
                    return result
            
            # For other categories, use standard extraction
            # Build extraction prompt
            prompt = f"""Du bist ein Experte für die Analyse von EFK-Prüfberichten.

Kategorie: {category_name}
Beschreibung: {schema.get('description', '')}
Typ: {schema.get('type', 'text')}
Max. Länge: {schema.get('max_length', 'unbegrenzt')}

Kontext aus dem Dokument:
{context[:3000]}

Extrahiere NUR die spezifische Information für diese Kategorie.
Bei Zitaten: Gib das EXAKTE Zitat aus dem Text wieder.
Bei Werten mit Optionen: Wähle NUR aus {schema.get('values', [])}

Antwort (nur der extrahierte Wert):"""

            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = response.content[0].text.strip()
            
            # Validate enums
            if 'values' in schema and result not in schema['values']:
                if 'default' in schema:
                    result = schema['default']
            
            return result if result else schema.get('default', None)
            
        except Exception as e:
            logger.error(f"Error extracting {category_name}: {str(e)}")
            return schema.get('default', None)
    
    def get_context_for_category(self, doc_id: str, category_name: str, schema: Dict) -> str:
        """Get relevant context for a category from Qdrant"""
        # Build query based on category
        query_parts = []
        
        # Add category name
        query_parts.append(category_name)
        
        # Add relevant keywords from schema
        if 'extract_from' in schema:
            query_parts.extend(schema['extract_from'])
        
        # Add description keywords
        if 'description' in schema:
            desc_words = schema['description'].split()[:5]
            query_parts.extend(desc_words)
        
        query = ' '.join(query_parts)
        query_vector = self.encoder.encode(query).tolist()
        
        # Search for relevant chunks
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=5,
            query_filter=Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]
            )
        )
        
        # Combine results
        contexts = []
        for result in results:
            chunk = result.payload
            contexts.append(chunk.get('text', ''))
        
        return '\n\n'.join(contexts)
    
    async def extract_document(self, doc_id: str) -> ExtractionResult:
        """Extract all categories from a document"""
        logger.info(f"\nProcessing document: {doc_id}")
        
        categories = {}
        
        # Extract each category
        for category_name in self.categories_schema.keys():
            # Get context for category
            context = self.get_context_for_category(
                doc_id, 
                category_name,
                self.categories_schema[category_name]
            )
            
            # Extract category
            result = self.extract_category(doc_id, category_name, context)
            
            if result:
                categories[category_name] = result
            else:
                # Use default or NULL erfasst
                schema = self.categories_schema[category_name]
                categories[category_name] = schema.get('default', 'NULL erfasst')
        
        # Generate analysis
        analysis = self.generate_analysis(categories)
        
        return ExtractionResult(
            document_id=doc_id,
            categories=categories,
            extraction_timestamp=datetime.now().isoformat(),
            analysis=analysis
        )
    
    def generate_analysis(self, categories: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI analysis of the extraction"""
        try:
            # Build analysis prompt
            prompt = f"""Analysiere die extrahierten Daten aus dem EFK-Prüfbericht:

Kernproblem: {categories.get('Kernproblem', 'Nicht erfasst')}
Assoziierte Kosten: {categories.get('Assoziierte Kosten', 'Nicht erfasst')}
Risiken des Bundes: {categories.get('Risiken des Bundes', 'Nicht erfasst')}
Empfehlungen: {categories.get('Empfehlungen', 'Nicht erfasst')}

Erstelle eine strukturierte Analyse mit:
1. Hauptrisiken und Auswirkungen
2. Kostenimplikationen
3. Kritische Handlungsempfehlungen
4. Umsetzungsstand und Hindernisse

Format: Strukturierter Text mit nummerierten Punkten."""

            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "analysis": response.content[0].text.strip(),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return {
                "analysis": "Analyse konnte nicht generiert werden.",
                "generated_at": datetime.now().isoformat()
            }
    
    async def run_extraction(self):
        """Run extraction for all documents"""
        # Get all document IDs from chunked data
        chunked_dir = Path(__file__).parent / '02_chunked_data'
        doc_ids = []
        
        for chunk_file in chunked_dir.glob('*_chunks.json'):
            # Extract document ID from filename
            doc_id = chunk_file.stem.replace('_chunks', '')
            doc_ids.append(doc_id)
        
        logger.info(f"Found {len(doc_ids)} documents to process")
        
        # Process each document
        results = []
        for doc_id in doc_ids:
            try:
                result = await self.extract_document(doc_id)
                results.append(result)
                
                # Save individual result
                output_file = Path(__file__).parent / '03_extracted_data' / f'{doc_id}_improved_extraction.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'document_id': result.document_id,
                        'extraction_timestamp': result.extraction_timestamp,
                        'extraction_method': 'Improved RAG with Claude 3.5 Sonnet v2',
                        'categories': result.categories,
                        'analysis': result.analysis
                    }, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved extraction to {output_file}")
                
            except Exception as e:
                logger.error(f"Error processing {doc_id}: {str(e)}")
        
        # Save summary
        summary_file = Path(__file__).parent / '03_extracted_data' / 'extraction_summary_improved.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_timestamp': datetime.now().isoformat(),
                'total_documents': len(results),
                'successful_extractions': len(results),
                'extraction_method': 'Improved RAG with Claude 3.5 Sonnet v2'
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Extraction complete!")
        logger.info(f"Processed {len(results)} documents")
        logger.info(f"Results saved to 03_extracted_data/")
        logger.info(f"{'='*50}")

def main():
    """Main entry point"""
    extractor = ImprovedRAGExtractor()
    asyncio.run(extractor.run_extraction())

if __name__ == "__main__":
    main()
