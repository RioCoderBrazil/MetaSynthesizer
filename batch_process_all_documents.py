"""
Batch processing script for all documents in the MetaSynthesizer pipeline
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
project_root = Path(__file__).parent
env_path = project_root / '.env'
load_dotenv(env_path, override=True)

# Import all necessary components
from src.pass2.chunker import DocumentChunker
from src.pass2.vectorizer import DocumentVectorizer
from src.pass2.rag_extractor import RAGExtractor
from src.pass2.schema_validator import SchemaValidator
from src.pass2.category_merger import CategoryMerger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('batch_processor')

class BatchProcessor:
    """Process all documents through the complete pipeline"""
    
    def __init__(self):
        self.chunker = DocumentChunker()
        self.vectorizer = DocumentVectorizer(
            qdrant_host='localhost',
            qdrant_port=6333,
            collection_name='metasynthesizer'
        )
        self.extractor = RAGExtractor(
            qdrant_host='localhost',
            qdrant_port=6333,
            collection_name='metasynthesizer'
        )
        self.validator = SchemaValidator()
        self.merger = CategoryMerger()
        
        # Track processing statistics
        self.stats = {
            'total_documents': 0,
            'processed_documents': 0,
            'total_chunks': 0,
            'total_vectors': 0,
            'extraction_results': {},
            'errors': []
        }
    
    def get_unprocessed_documents(self) -> List[Path]:
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
    
    def process_document(self, doc_path: Path) -> Dict:
        """Process a single document through the pipeline"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {doc_path.name}")
        logger.info(f"{'='*60}")
        
        result = {
            'document': doc_path.name,
            'status': 'started',
            'chunks': 0,
            'vectors': 0,
            'extraction_completeness': 0,
            'errors': []
        }
        
        try:
            # Step 1: Chunk the document
            logger.info("📄 Step 1: Chunking document...")
            chunks = self.chunker.chunk_document(str(doc_path))
            result['chunks'] = len(chunks)
            logger.info(f"✓ Created {len(chunks)} chunks")
            
            # Save chunks
            chunk_file = Path('02_chunked_data') / f"{doc_path.stem}_chunks.json"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            
            # Step 2: Create sections (for better context)
            logger.info("📑 Step 2: Creating document sections...")
            sections = self.chunker.create_sections(chunks)
            
            section_file = Path('02_chunked_data') / f"{doc_path.stem}_sections.json"
            with open(section_file, 'w', encoding='utf-8') as f:
                json.dump(sections, f, indent=2, ensure_ascii=False)
            
            # Step 3: Vectorize and store
            logger.info("🔢 Step 3: Vectorizing chunks...")
            doc_id = doc_path.stem
            vector_count = self.vectorizer.vectorize_and_store(chunks, doc_id)
            result['vectors'] = vector_count
            logger.info(f"✓ Stored {vector_count} vectors in Qdrant")
            
            # Step 4: Extract data for all categories
            logger.info("🎯 Step 4: Extracting data...")
            extraction_results = {}
            
            categories = self.extractor.categories_schema.keys()
            for category in categories:
                try:
                    extracted = self.extractor.extract_for_category(category, doc_id)
                    extraction_results[category] = extracted
                except Exception as e:
                    logger.error(f"Failed to extract {category}: {e}")
                    result['errors'].append(f"Extraction error in {category}: {str(e)}")
            
            # Step 5: Validate results
            logger.info("✅ Step 5: Validating extraction...")
            validation_summary = {}
            valid_count = 0
            
            for category, data in extraction_results.items():
                is_valid, errors = self.validator.validate_category_data(category, data)
                validation_summary[category] = {
                    'valid': is_valid,
                    'errors': errors
                }
                if is_valid:
                    valid_count += 1
            
            # Step 6: Save extraction results
            output_file = Path('03_extracted_data') / f"{doc_id}_extracted.json"
            merged_results = self.merger.merge_extractions(extraction_results)
            
            final_output = {
                'document_id': doc_id,
                'extraction_timestamp': datetime.now().isoformat(),
                'categories': merged_results,
                'validation_summary': validation_summary,
                'statistics': self.merger.generate_report(merged_results)
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_output, f, indent=2, ensure_ascii=False)
            
            # Calculate completeness
            completeness = (valid_count / len(categories)) * 100 if categories else 0
            result['extraction_completeness'] = round(completeness, 2)
            result['status'] = 'completed'
            
            logger.info(f"✓ Document processed successfully!")
            logger.info(f"  - Completeness: {result['extraction_completeness']}%")
            
        except Exception as e:
            logger.error(f"❌ Error processing document: {e}")
            result['status'] = 'failed'
            result['errors'].append(str(e))
        
        return result
    
    def run_batch_processing(self):
        """Run batch processing for all unprocessed documents"""
        logger.info("=== Starting Batch Processing ===")
        
        # Get unprocessed documents
        unprocessed = self.get_unprocessed_documents()
        self.stats['total_documents'] = len(unprocessed)
        
        if not unprocessed:
            logger.info("✓ All documents already processed!")
            return
        
        logger.info(f"Found {len(unprocessed)} documents to process")
        
        # Process each document
        for i, doc_path in enumerate(unprocessed, 1):
            logger.info(f"\n[{i}/{len(unprocessed)}] Processing document...")
            
            result = self.process_document(doc_path)
            self.stats['extraction_results'][doc_path.name] = result
            
            if result['status'] == 'completed':
                self.stats['processed_documents'] += 1
                self.stats['total_chunks'] += result['chunks']
                self.stats['total_vectors'] += result['vectors']
            else:
                self.stats['errors'].append({
                    'document': doc_path.name,
                    'errors': result['errors']
                })
            
            # Small delay between documents
            if i < len(unprocessed):
                time.sleep(2)
        
        # Save processing report
        self.save_processing_report()
    
    def save_processing_report(self):
        """Save a summary report of the batch processing"""
        report = {
            'processing_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_documents': self.stats['total_documents'],
                'successfully_processed': self.stats['processed_documents'],
                'failed': len(self.stats['errors']),
                'total_chunks_created': self.stats['total_chunks'],
                'total_vectors_stored': self.stats['total_vectors']
            },
            'document_results': self.stats['extraction_results'],
            'errors': self.stats['errors']
        }
        
        report_file = Path('logs') / f"batch_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 Batch Processing Complete!")
        logger.info(f"{'='*60}")
        logger.info(f"✓ Processed: {self.stats['processed_documents']}/{self.stats['total_documents']} documents")
        logger.info(f"✓ Total chunks: {self.stats['total_chunks']}")
        logger.info(f"✓ Total vectors: {self.stats['total_vectors']}")
        if self.stats['errors']:
            logger.info(f"⚠️  Errors: {len(self.stats['errors'])} documents failed")
        logger.info(f"\n📄 Report saved to: {report_file}")

def main():
    """Main entry point"""
    processor = BatchProcessor()
    
    # Check if we want to process all or just show status
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        unprocessed = processor.get_unprocessed_documents()
        logger.info(f"Status: {len(unprocessed)} documents pending processing")
        for doc in unprocessed:
            logger.info(f"  - {doc.name}")
    else:
        processor.run_batch_processing()

if __name__ == "__main__":
    main()
