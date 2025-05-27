"""
Process all remaining documents through the complete pipeline
Using existing pass1 components
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
project_root = Path(__file__).parent
env_path = project_root / '.env'
load_dotenv(env_path, override=True)

# Import existing components
from src.pass1.hybrid_chunker import HybridChunker
from src.pass1.vector_embedder import VectorEmbedder
from src.pass1.color_parser import ColorParser
from src.pass2.rag_extractor import RAGExtractor
from src.pass2.schema_validator import SchemaValidator
from src.pass2.category_merger import CategoryMerger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('doc_processor')

def get_unprocessed_documents() -> List[Path]:
    """Get list of documents that haven't been processed yet"""
    colored_dir = Path('01_colored_reports')
    chunked_dir = Path('02_chunked_data')
    
    # Get all colored documents
    all_docs = list(colored_dir.glob('*.docx'))
    
    # Check which ones have been chunked
    unprocessed = []
    for doc in all_docs:
        chunk_file = chunked_dir / f"{doc.stem}_chunks.json"
        if not chunk_file.exists():
            unprocessed.append(doc)
    
    return unprocessed

def process_single_document(doc_path: Path) -> Dict:
    """Process a single document through the pipeline"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📄 Processing: {doc_path.name}")
    logger.info(f"{'='*60}")
    
    result = {
        'document': doc_path.name,
        'doc_id': doc_path.stem,
        'status': 'started',
        'chunks': 0,
        'vectors': 0,
        'extraction_completeness': 0,
        'errors': []
    }
    
    try:
        # Initialize components
        color_parser = ColorParser(color_config_path='config/color_mappings.json')
        chunker = HybridChunker(max_tokens=500, min_tokens=50, overlap_tokens=50)
        embedder = VectorEmbedder(
            collection_name='metasynthesizer',
            qdrant_host='localhost'
        )
        extractor = RAGExtractor(
            qdrant_host='localhost',
            qdrant_port=6333,
            collection_name='metasynthesizer'
        )
        validator = SchemaValidator()
        merger = CategoryMerger()
        
        # Step 1: Extract colored sections from document
        logger.info("🎨 Step 1: Extracting colored sections...")
        doc_id = doc_path.stem
        sections = color_parser.parse_document(str(doc_path))
        logger.info(f"✓ Extracted {len(sections)} sections")
        
        # Step 2: Create chunks from sections
        logger.info("🔪 Step 2: Creating chunks...")
        chunks = chunker.chunk_sections(sections, doc_id)
        
        # Save chunks to file
        chunk_file = Path('02_chunked_data') / f"{doc_id}_chunks.json"
        chunk_data = [chunk.__dict__ for chunk in chunks]
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        
        result['chunks'] = len(chunks)
        logger.info(f"✓ Created {len(chunks)} chunks")
        
        # Step 3: Store vectors
        logger.info("🔢 Step 3: Creating and storing vectors...")
        vector_success = embedder.embed_and_store(chunks, doc_id)
        if not vector_success:
            raise Exception("Failed to store vectors")
        
        result['vectors'] = len(chunks)
        logger.info(f"✓ Stored {len(chunks)} vectors in Qdrant")
        
        # Step 4: Extract data for all categories
        logger.info("🎯 Step 4: Extracting data...")
        extraction_results = {}
        
        categories = extractor.categories_schema.keys()
        successful_extractions = 0
        
        for i, category in enumerate(categories, 1):
            logger.info(f"  [{i}/{len(categories)}] Extracting {category}...")
            try:
                extracted = extractor.extract_for_category(category, doc_id)
                extraction_results[category] = extracted
                successful_extractions += 1
            except Exception as e:
                logger.error(f"    ❌ Failed: {e}")
                result['errors'].append(f"Extraction error in {category}: {str(e)}")
                extraction_results[category] = {}
        
        logger.info(f"✓ Successfully extracted {successful_extractions}/{len(categories)} categories")
        
        # Step 5: Validate results
        logger.info("✅ Step 5: Validating extraction...")
        validation_summary = {}
        valid_count = 0
        
        for category, data in extraction_results.items():
            is_valid, errors = validator.validate_category_data(category, data)
            validation_summary[category] = {
                'valid': is_valid,
                'errors': errors
            }
            if is_valid:
                valid_count += 1
        
        # Step 6: Save extraction results
        output_file = Path('03_extracted_data') / f"{doc_id}_extracted.json"
        merged_results = merger.merge_extractions(extraction_results)
        
        final_output = {
            'document_id': doc_id,
            'extraction_timestamp': datetime.now().isoformat(),
            'categories': merged_results,
            'validation_summary': validation_summary,
            'statistics': merger.generate_report(merged_results)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        
        # Calculate completeness
        stats = merger.generate_report(merged_results)
        completeness = stats.get('completeness_percentage', 0)
        result['extraction_completeness'] = completeness
        result['status'] = 'completed'
        
        logger.info(f"✓ Document processed successfully!")
        logger.info(f"  - Completeness: {result['extraction_completeness']}%")
        logger.info(f"  - Valid categories: {valid_count}/{len(categories)}")
        
    except Exception as e:
        logger.error(f"❌ Error processing document: {e}")
        result['status'] = 'failed'
        result['errors'].append(str(e))
    
    return result

def main():
    """Main processing function"""
    logger.info("=== Starting Document Processing ===")
    
    # Get unprocessed documents
    unprocessed = get_unprocessed_documents()
    
    if not unprocessed:
        logger.info("✓ All documents already processed!")
        return
    
    logger.info(f"Found {len(unprocessed)} documents to process")
    
    # Ask user if they want to process all or just a few
    print(f"\n📋 {len(unprocessed)} Dokumente müssen noch verarbeitet werden.")
    print("Optionen:")
    print("  1. Alle verarbeiten")
    print("  2. Nur die ersten 3 verarbeiten (Test)")
    print("  3. Abbrechen")
    
    choice = input("\nWähle eine Option (1-3): ").strip()
    
    if choice == '3':
        logger.info("Processing cancelled by user")
        return
    elif choice == '2':
        unprocessed = unprocessed[:3]
        logger.info(f"Processing first 3 documents only")
    
    # Process statistics
    stats = {
        'total': len(unprocessed),
        'completed': 0,
        'failed': 0,
        'total_chunks': 0,
        'results': []
    }
    
    # Process each document
    for i, doc_path in enumerate(unprocessed, 1):
        logger.info(f"\n[{i}/{len(unprocessed)}] Processing document...")
        
        result = process_single_document(doc_path)
        stats['results'].append(result)
        
        if result['status'] == 'completed':
            stats['completed'] += 1
            stats['total_chunks'] += result['chunks']
        else:
            stats['failed'] += 1
        
        # Small delay between documents to avoid overload
        if i < len(unprocessed):
            time.sleep(3)
    
    # Final report
    logger.info(f"\n{'='*60}")
    logger.info("📊 Processing Complete!")
    logger.info(f"{'='*60}")
    logger.info(f"✓ Successfully processed: {stats['completed']}/{stats['total']} documents")
    logger.info(f"✓ Total chunks created: {stats['total_chunks']}")
    if stats['failed'] > 0:
        logger.info(f"⚠️  Failed: {stats['failed']} documents")
    
    # Save processing report
    report_file = Path('logs') / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
