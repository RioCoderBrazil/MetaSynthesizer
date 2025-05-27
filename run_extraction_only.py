#!/usr/bin/env python3
"""
Run only the extraction phase of the MetaSynthesizer pipeline
"""
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import sys

# Setup path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from pass2.rag_extractor import RAGExtractor
from utils import FileUtils

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('extraction')

def main():
    """Run extraction phase only"""
    logger.info("="*60)
    logger.info("METASYNTHESIZER - EXTRACTION PHASE ONLY")
    logger.info("="*60)
    
    # Initialize paths
    chunks_dir = project_root / '02_chunks'
    extractions_dir = project_root / '03_extracted_data'
    extractions_dir.mkdir(exist_ok=True)
    
    # Initialize extractor
    logger.info("Initializing RAG extractor...")
    rag_extractor = RAGExtractor()
    
    # Find all chunk files
    chunk_files = sorted(chunks_dir.glob('*_chunks.json'))
    logger.info(f"Found {len(chunk_files)} documents to extract from")
    
    all_extractions = []
    
    # Process each document
    for chunk_file in tqdm(chunk_files, desc="Extracting data"):
        doc_id = chunk_file.stem.replace('_chunks', '')
        logger.info(f"\nExtracting from: {doc_id}")
        
        try:
            # Extract data
            extraction = rag_extractor.extract_all_categories(doc_id)
            
            if extraction:
                # Create full extraction object
                full_extraction = {
                    'document_id': doc_id,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'extraction_method': "RAG with Claude 3.5 Sonnet v2",
                    'categories': extraction
                }
                
                # Save individual extraction
                extraction_file = extractions_dir / f"{doc_id}_extraction.json"
                FileUtils.save_json(full_extraction, extraction_file)
                
                all_extractions.append(full_extraction)
                
                # Show progress
                filled = sum(1 for cat in extraction.values() if cat)
                logger.info(f"  Extracted {filled}/9 categories")
            else:
                logger.error(f"  Failed to extract from {doc_id}")
                
        except Exception as e:
            logger.error(f"  Error extracting from {doc_id}: {e}")
    
    # Save all extractions
    if all_extractions:
        all_file = extractions_dir / "all_extractions.json"
        FileUtils.save_json(all_extractions, all_file)
        logger.info(f"\nSaved all extractions to {all_file}")
    
    # Summary
    logger.info(f"\nExtraction complete: {len(all_extractions)} successful, {len(chunk_files) - len(all_extractions)} failed")


if __name__ == "__main__":
    main()
