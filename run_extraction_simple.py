#!/usr/bin/env python3
"""
Simple extraction runner that avoids import issues
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List, Any
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import anthropic
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('extraction')

# Load environment
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')

class SimpleRAGExtractor:
    """Simplified RAG extractor without import issues"""
    
    def __init__(self):
        self.qdrant_client = QdrantClient("localhost", port=6333)
        self.encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.collection_name = "metasynthesizer"
        
        # Load schema
        schema_path = project_root / 'config' / 'categories_schema.json'
        with open(schema_path, 'r') as f:
            self.categories_schema = json.load(f)
    
    def retrieve_contexts(self, query: str, doc_id: str, label: str = None, limit: int = 10) -> List[Dict]:
        """Retrieve relevant contexts for a query"""
        query_vector = self.encoder.encode(query).tolist()
        
        # Build filter
        filter_conditions = [{"key": "doc_id", "match": {"value": doc_id}}]
        if label:
            filter_conditions.append({"key": "label", "match": {"value": label}})
        
        # Search
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter={"must": filter_conditions}
        )
        
        contexts = []
        for hit in results:
            contexts.append({
                'text': hit.payload['text'],
                'label': hit.payload['label'],
                'score': hit.score
            })
        
        return contexts
    
    def extract_category(self, category_name: str, doc_id: str) -> Dict[str, Any]:
        """Extract data for a single category"""
        schema = self.categories_schema[category_name]
        
        # Generate query
        query = f"Extract {category_name}: {schema.get('description', '')}"
        
        # Retrieve contexts
        contexts = self.retrieve_contexts(query, doc_id, limit=10)
        
        if not contexts:
            return None
        
        # Build prompt
        context_text = "\n\n".join([f"[{ctx['label']}]\n{ctx['text']}" for ctx in contexts[:5]])
        
        prompt = f"""Based on the following audit document contexts, extract information for the category '{category_name}'.

{schema.get('description', '')}

Required fields:
{json.dumps(schema.get('properties', {}), indent=2)}

Contexts:
{context_text}

Return a valid JSON object for this category. If information is not available, use null for optional fields or appropriate empty values.
Only return the JSON object, no additional text."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            content = response.content[0].text.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error extracting {category_name}: {e}")
            return None
    
    def extract_all_categories(self, doc_id: str) -> Dict[str, Any]:
        """Extract all categories for a document"""
        results = {}
        
        for category_name in self.categories_schema.keys():
            logger.info(f"    Extracting {category_name}...")
            try:
                data = self.extract_category(category_name, doc_id)
                results[category_name] = data
            except Exception as e:
                logger.error(f"    Failed to extract {category_name}: {e}")
                results[category_name] = None
        
        return results


def main():
    """Run extraction"""
    logger.info("="*60)
    logger.info("METASYNTHESIZER - SIMPLE EXTRACTION")
    logger.info("="*60)
    
    # Initialize
    extractor = SimpleRAGExtractor()
    
    # Get all chunk files
    chunks_dir = project_root / '02_chunked_data'
    chunk_files = sorted(chunks_dir.glob('*_chunks.json'))
    logger.info(f"Found {len(chunk_files)} documents to extract from")
    
    # Output directory
    output_dir = project_root / '03_extracted_data'
    output_dir.mkdir(exist_ok=True)
    
    all_extractions = []
    
    # Process each document
    for chunk_file in tqdm(chunk_files, desc="Extracting documents"):
        doc_id = chunk_file.stem.replace('_chunks', '')
        logger.info(f"\nProcessing: {doc_id}")
        
        try:
            # Extract
            categories = extractor.extract_all_categories(doc_id)
            
            # Create full extraction
            extraction = {
                'document_id': doc_id,
                'extraction_timestamp': datetime.now().isoformat(),
                'extraction_method': "RAG with Claude 3.5 Sonnet v2",
                'categories': categories
            }
            
            # Save individual
            out_file = output_dir / f"{doc_id}_extraction.json"
            with open(out_file, 'w') as f:
                json.dump(extraction, f, indent=2)
            
            all_extractions.append(extraction)
            
            # Count filled
            filled = sum(1 for v in categories.values() if v)
            logger.info(f"  Extracted {filled}/{len(categories)} categories")
            
        except Exception as e:
            logger.error(f"  Failed: {e}")
    
    # Save all
    if all_extractions:
        all_file = output_dir / "all_extractions.json"
        with open(all_file, 'w') as f:
            json.dump(all_extractions, f, indent=2)
        logger.info(f"\nSaved {len(all_extractions)} extractions to {all_file}")
    
    logger.info("\nExtraction complete!")


if __name__ == "__main__":
    main()
