#!/usr/bin/env python3
"""
MetaSynthesizer RAG Extraction with CORRECT Categories
Based on the Excel specification with 23 categories
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import anthropic
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('extraction_correct.log')
    ]
)
logger = logging.getLogger('extraction')

class CorrectRAGExtractor:
    """RAG-based extractor with the CORRECT 23 categories"""
    
    def __init__(self):
        self.qdrant_client = QdrantClient("localhost", port=6333)
        self.encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.collection_name = "metasynthesizer"
        
        # Load correct schema
        project_root = Path(__file__).parent
        schema_path = project_root / 'config' / 'categories_schema_correct.json'
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.categories_schema = json.load(f)
    
    def extract_pa_nummer_from_filename(self, doc_id: str) -> Optional[str]:
        """Extract PA-Nummer from document filename"""
        # Pattern: digits followed by BE or other suffixes at the start
        match = re.match(r'^(\d+[A-Z]+)', doc_id)
        if match:
            return match.group(1)
        return None
    
    def extract_berichtdatum_from_context(self, context: str) -> str:
        """Extract Berichtdatum using multiple date patterns"""
        
        # Various date patterns to try
        patterns = [
            # ISO format: 2023-12-31
            r'(\d{4}-\d{2}-\d{2})',
            # German format: 31.12.2023
            r'(\d{1,2}\.\d{1,2}\.\d{4})',
            # Written format: 31. Dezember 2023
            r'(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4})',
            # Date in header: Datum: 31.12.2023
            r'Datum[:\s]+(\d{1,2}\.\d{1,2}\.\d{4})',
            # Report date: Berichtsdatum: 31.12.2023
            r'Berichtsdatum[:\s]+(\d{1,2}\.\d{1,2}\.\d{4})',
            # Date of: Stand vom 31.12.2023
            r'Stand\s+vom\s+(\d{1,2}\.\d{1,2}\.\d{4})',
            # Date per: Per 31.12.2023
            r'Per\s+(\d{1,2}\.\d{1,2}\.\d{4})',
        ]
        
        # Try each pattern
        for pattern in patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                # Take the first match and convert to ISO format
                date_str = matches[0]
                
                # Convert German format to ISO
                if '.' in date_str and len(date_str.split('.')) == 3:
                    parts = date_str.split('.')
                    if len(parts[2]) == 4:  # DD.MM.YYYY
                        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                
                # Already in ISO format
                if '-' in date_str and len(date_str.split('-')) == 3:
                    return date_str
                
                # Handle written dates
                month_map = {
                    'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
                    'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
                    'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
                }
                
                for month_name, month_num in month_map.items():
                    if month_name in date_str.lower():
                        # Extract day and year
                        day_match = re.search(r'(\d{1,2})', date_str)
                        year_match = re.search(r'(\d{4})', date_str)
                        if day_match and year_match:
                            return f"{year_match.group(1)}-{month_num}-{day_match.group(1).zfill(2)}"
        
        return None
    
    def get_context_for_category(self, doc_id: str, category_name: str, schema: Dict) -> str:
        """Get relevant context for a specific category"""
        try:
            # Build query based on category needs
            query_parts = []
            
            # Add category-specific search terms
            if 'extract_from' in schema:
                for section in schema['extract_from']:
                    if section == 'title':
                        query_parts.append("Titel Bericht")
                    elif section == 'header':
                        query_parts.append("Kopfzeile Header")
                    elif section == 'findings':
                        query_parts.append("Feststellungen Erkenntnisse")
                    elif section == 'recommendations':
                        query_parts.append("Empfehlungen")
                    elif section == 'costs':
                        query_parts.append("Kosten Ausgaben Finanzen")
                    elif section == 'risks':
                        query_parts.append("Risiken Risikobewertung")
                    elif section == 'monitoring':
                        query_parts.append("Monitoring Überwachung Controlling")
                    elif section == 'planning_issues':
                        query_parts.append("Planungsprobleme fehlende Planung")
                    elif section == 'implementation_status':
                        query_parts.append("Umsetzungsstatus Implementierung")
            
            # Add category description
            query_parts.append(category_name)
            query_parts.append(schema.get('description', ''))
            
            query = " ".join(query_parts)
            
            # Search for relevant chunks
            query_embedding = self.encoder.encode(query)
            
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter={"must": [{"key": "doc_id", "match": {"value": doc_id}}]},
                limit=15  # Increased for better coverage
            )
            
            # Combine relevant chunks
            contexts = []
            for hit in search_result:
                chunk_text = hit.payload.get('text', '')
                color = hit.payload.get('color', 'none')
                if chunk_text:
                    contexts.append(f"[Color: {color}] {chunk_text}")
            
            return "\n\n".join(contexts)
            
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return ""
    
    def extract_category(self, doc_id: str, category_name: str, context: str) -> Any:
        """Extract a single category using Claude"""
        try:
            # Handle PA-Nummer specially
            if category_name == "PA-Nummer":
                pa_nummer = self.extract_pa_nummer_from_filename(doc_id)
                if pa_nummer:
                    return pa_nummer
            
            # Handle Berichtdatum specially
            if category_name == "Berichtdatum":
                berichtdatum = self.extract_berichtdatum_from_context(context)
                if berichtdatum:
                    return berichtdatum
            
            schema = self.categories_schema[category_name]
            
            # Quote categories - collect multiple entries with page numbers
            if category_name in [
                "Umwelt, Info A (Relevante Akteure)",
                "Umwelt, Info B (Berichtsprache/Datei)",
                "Umwelt, Info C (Bedenken/Monitoring)",
                "Flankieigend A (kein Plan)",
                "Flankieigend B (Plan unvollständig)",
                "Flankieigend C (in der Nachverfolgung)"
            ]:
                # Get context from Qdrant chunks
                results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=self.encoder.encode(category_name),
                    limit=10,
                    query_filter={"must": [{"key": "doc_id", "match": {"value": doc_id}}]}
                )
                
                quotes = []
                seen_quotes = set()
                
                for result in results:
                    chunk = result.payload
                    context = chunk.get('text', '')
                    start_page = chunk.get('start_page', 0)
                    end_page = chunk.get('end_page', start_page)
                    
                    # Find quotes that match the category
                    if category_name == "Umwelt, Info A (Relevante Akteure)":
                        pattern = r'["""](.*?(?:zuvorkommend erteilt|Rolle zur konformen Umsetzung|Verantwortlich für die Umsetzung|nutzt das KbS aktiv).*?)["""]'
                    elif category_name == "Umwelt, Info B (Berichtsprache/Datei)":
                        pattern = r'["""](.*?(?:technischen Untersuchungen|fehlende Frist führt|Beide Dokumente).*?)["""]'
                    elif category_name == "Umwelt, Info C (Bedenken/Monitoring)":
                        pattern = r'["""](.*?(?:kein Berichtswesen|keine erkennbare Aufsicht|Prozessbeschrieb.*?liegt nicht vor).*?)["""]'
                    else:
                        # For Flankieigend categories
                        pattern = r'["""](.*?)["""]'
                    
                    matches = re.findall(pattern, context, re.DOTALL | re.IGNORECASE)
                    
                    for match in matches:
                        cleaned = match.strip()
                        if cleaned and len(cleaned) > 30 and cleaned not in seen_quotes:
                            seen_quotes.add(cleaned)
                            # Format: quote text followed by page reference
                            page_ref = f"(S. {start_page})" if start_page == end_page else f"(S. {start_page}-{end_page})"
                            quotes.append(f"{cleaned} {page_ref}")
                
                # Return quotes as a list formatted string
                if quotes:
                    return "\n\n".join(quotes[:5])  # Limit to 5 quotes
                else:
                    # Try direct extraction from context
                    return self._extract_from_context(context, category_name)
            
            # For Empfehlungen category - handle multiple recommendations
            if category_name == "Empfehlungen":
                recommendations = []
                recommendation_pattern = r'Empfehlung\s+(\d+)\s*\(Priorität\s*(\d+)\)\s*([^\.]+\.)'
                
                for result in self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=self.encoder.encode(category_name),
                    limit=10,
                    query_filter={"must": [{"key": "doc_id", "match": {"value": doc_id}}]}
                ):
                    chunk = result.payload
                    context = chunk.get('text', '')
                    start_page = chunk.get('start_page', 0)
                    
                    matches = re.findall(recommendation_pattern, context, re.IGNORECASE)
                    for match in matches:
                        emp_num, priority, text = match
                        page_ref = f"(S. {start_page})"
                        recommendations.append(f"Empfehlung {emp_num} (Priorität {priority}): {text.strip()} {page_ref}")
                
                if recommendations:
                    return "\n\n".join(recommendations)
            
            # Build extraction prompt
            prompt = f"""Du bist ein Experte für die Analyse von EFK-Prüfberichten.

Extrahiere die folgende Information aus dem gegebenen Kontext:

KATEGORIE: {category_name}
BESCHREIBUNG: {schema['description']}
TYP: {schema['type']}
MAX LÄNGE: {schema.get('max_length', 'N/A')} {'Wörter' if schema['type'] == 'text' else 'Zeichen'}

SPEZIELLE ANWEISUNGEN:"""

            if schema.get('is_quote', False):
                prompt += "\n- Dies muss ein WÖRTLICHES ZITAT aus dem Dokument sein!"
                prompt += "\n- Wenn es MEHRERE relevante Zitate/Zeilen gibt, gib ALLE zurück!"
                prompt += "\n- Trenne mehrere Zitate mit \\n\\n"
            
            if 'values' in schema:
                prompt += f"\n- Nur diese Werte sind erlaubt: {', '.join(schema['values'])}"
            
            if 'default' in schema:
                prompt += f"\n- Wenn nicht gefunden, verwende: {schema['default']}"
            
            # Special handling for multi-line categories
            multi_line_categories = ["Empfehlungen", "Umwelt, Info A (Relevante Akteure)", 
                                    "Umwelt, Info B (Berichtsprache/Datei)", 
                                    "Umwelt, Info C (Bedenken/Monitoring)",
                                    "Flankieigend A (kein Plan)",
                                    "Flankieigend B (Plan unvollständig)", 
                                    "Flankieigend C (in der Nachverfolgung)"]
            
            if category_name in multi_line_categories:
                prompt += "\n- WICHTIG: Extrahiere ALLE relevanten Informationen/Zeilen zu dieser Kategorie!"
                prompt += "\n- Wenn es mehrere Punkte/Absätze gibt, inkludiere ALLE!"

            prompt += f"""

KONTEXT:
{context}

ANTWORTFORMAT:
- Wenn ein wörtliches Zitat verlangt ist, gib das exakte Zitat aus dem Text zurück
- Bei mehreren relevanten Einträgen, gib ALLE zurück (getrennt durch Zeilenumbrüche)
- Wenn die Information nicht gefunden wird und es einen Default gibt, verwende diesen
- Wenn die Information nicht gefunden wird und kein Default existiert, antworte mit null
- Halte dich STRIKT an die maximale Länge
- Für Dropdown-Felder verwende NUR die erlaubten Werte

Deine Antwort (NUR der extrahierte Wert/die extrahierten Werte, keine Erklärung):"""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,  # Increased for multi-line responses
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            extracted_value = response.content[0].text.strip()
            
            # Post-process based on type
            if schema['type'] == 'date' and extracted_value and extracted_value != 'null':
                # Ensure date format
                pass  # Add date parsing if needed
            
            if 'values' in schema and extracted_value not in schema['values'] + ['null']:
                # Use default if invalid value
                extracted_value = schema.get('default', 'null')
            
            return extracted_value if extracted_value != 'null' else None
            
        except Exception as e:
            logger.error(f"Error extracting {category_name}: {str(e)}")
            return schema.get('default', None)
    
    def extract_all_categories(self, doc_id: str) -> Dict[str, Any]:
        """Extract all categories for a document"""
        results = {}
        
        for category_name in self.categories_schema.keys():
            logger.info(f"    Extracting {category_name}...")
            
            # Get context
            context = self.get_context_for_category(doc_id, category_name, self.categories_schema[category_name])
            
            if context:
                # Extract value
                value = self.extract_category(doc_id, category_name, context)
                results[category_name] = value
            else:
                # Use default if no context
                results[category_name] = self.categories_schema[category_name].get('default', None)
        
        return results
    
    def analyze_document(self, doc_id: str, categories: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis based on extracted categories"""
        try:
            # Create analysis prompt
            prompt = f"""Als EFK-Experte, analysiere die extrahierten Daten und erstelle eine Zusammenfassung:

EXTRAHIERTE DATEN:
- Berichtstitel: {categories.get('Berichtstitel', 'N/A')}
- Kernproblem: {categories.get('Kernproblem', 'N/A')}
- Assoziierte Kosten: {categories.get('Assoziierte Kosten', 'N/A')}
- Risiken des Bundes: {categories.get('Risiken des Bundes', 'N/A')}
- Empfehlungen: {categories.get('Empfehlungen', 'N/A')}
- Umsetzungsstatus: {categories.get('Umsetzungsstatus', 'N/A')}

Erstelle eine prägnante Analyse mit folgenden Elementen:
1. Hauptrisiken und deren Auswirkungen
2. Kostenimplikationen
3. Kritische Handlungsempfehlungen
4. Umsetzungsstand und Hindernisse

Format: Strukturierte Stichpunkte, max. 200 Wörter."""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "analysis": response.content[0].text.strip(),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return {"analysis": "Analyse konnte nicht erstellt werden", "error": str(e)}


def main():
    """Main extraction process with correct categories"""
    # Load environment variables
    project_root = Path(__file__).parent
    env_path = project_root / '.env'
    load_dotenv(env_path)
    
    # Initialize extractor
    extractor = CorrectRAGExtractor()
    
    # Get all documents from chunked data
    chunks_dir = Path("02_chunked_data")
    chunk_files = list(chunks_dir.glob("*_chunks.json"))
    
    # Extract unique document IDs
    doc_ids = set()
    for chunk_file in chunk_files:
        # Extract doc_id from filename (before _chunks.json)
        doc_id = chunk_file.stem.replace('_chunks', '').replace('_coloured', '').replace('_colored', '').replace('_farcoded', '').replace('_farbcoded', '')
        doc_ids.add(doc_id)
    
    all_extractions = []
    
    for doc_id in tqdm(sorted(doc_ids), desc="Extracting documents"):
        logger.info(f"\nProcessing: {doc_id}")
        
        try:
            # Extract all categories
            categories = extractor.extract_all_categories(doc_id)
            
            # Generate analysis
            analysis = extractor.analyze_document(doc_id, categories)
            
            # Combine results
            extraction = {
                'document_id': doc_id,
                'extraction_timestamp': datetime.now().isoformat(),
                'extraction_method': 'RAG with Claude 3.5 Sonnet v2 - CORRECT Schema',
                'categories': categories,
                'analysis': analysis
            }
            
            all_extractions.append(extraction)
            
            # Save individual extraction
            output_dir = Path("03_extracted_data")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"{doc_id}_correct_extraction.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extraction, f, ensure_ascii=False, indent=2)
            
            # Log progress
            filled = sum(1 for v in categories.values() if v)
            logger.info(f"  Extracted {filled}/{len(categories)} categories")
            
        except Exception as e:
            logger.error(f"Failed to process {doc_id}: {str(e)}")
    
    # Save all extractions
    all_output = Path("03_extracted_data/all_extractions_correct.json")
    with open(all_output, 'w', encoding='utf-8') as f:
        json.dump(all_extractions, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\nSaved {len(all_extractions)} extractions to {all_output}")
    logger.info("\nExtraction complete!")


if __name__ == "__main__":
    main()
