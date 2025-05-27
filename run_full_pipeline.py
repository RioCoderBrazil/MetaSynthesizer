#!/usr/bin/env python3
"""
MetaSynthesizer Full Pipeline Runner
Process all documents through chunking, vectorization, and extraction
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
import logging
from tqdm import tqdm
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.pass1 import ColorParser, HybridChunker, VectorEmbedder
from src.pass2.rag_extractor import RAGExtractor
from src.utils import FileUtils, setup_logger
from src.utils.validator import DataValidator
from src.utils.html_generator import HTMLReportGenerator
from src.visualization.meta_dashboard import MetaDashboard
from src.visualization.chunk_visualizer import ChunkVisualizer

# Load environment
load_dotenv('config/.env')

# Setup logger
logger = setup_logger("pipeline")


class FullPipeline:
    """Run the complete MetaSynthesizer pipeline"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.input_dir = self.project_root / "01_colored_reports"
        self.output_dirs = {
            'chunks': self.project_root / "02_chunked_data",
            'extractions': self.project_root / "03_extracted_data",
            'html_reports': self.project_root / "05_html_reports",
            'validation': self.project_root / "06_validation_logs",
            'dashboard': self.project_root / "07_meta_dashboard",
            'visualization': self.project_root / "08_chunk_visualization"
        }
        
        # Create output directories
        for dir_path in self.output_dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Initialize components
        self.color_parser = ColorParser(str(self.project_root / 'config' / 'color_mappings.json'))
        self.hybrid_chunker = HybridChunker()
        self.vector_embedder = VectorEmbedder()
        self.rag_extractor = RAGExtractor()
        self.validator = DataValidator()
        self.html_generator = HTMLReportGenerator()
    
    def get_all_documents(self):
        """Get all colored DOCX files"""
        docs = list(self.input_dir.glob("*.docx"))
        logger.info(f"Found {len(docs)} documents to process")
        return sorted(docs)
    
    def process_chunking(self, doc_path: Path):
        """Process a single document through chunking and vectorization"""
        try:
            doc_id = doc_path.stem
            logger.info(f"Processing: {doc_id}")
            
            # Step 1: Parse colored sections
            sections = self.color_parser.parse_document(str(doc_path))
            logger.info(f"  Found {len(sections)} colored sections")
            
            # Save sections
            sections_data = [{
                'label': s.label,
                'text': s.text,
                'start_page': s.start_page,
                'end_page': s.end_page,
                'confidence': s.confidence,
                'color_rgb': s.color_rgb
            } for s in sections]
            
            sections_file = self.output_dirs['chunks'] / f"{doc_id}_sections.json"
            FileUtils.save_json(sections_data, sections_file)
            
            # Step 2: Create chunks
            chunks = self.hybrid_chunker.chunk_sections(sections, doc_id)
            logger.info(f"  Created {len(chunks)} chunks")
            
            # Save chunks
            chunks_data = [chunk.to_dict() for chunk in chunks]
            chunks_file = self.output_dirs['chunks'] / f"{doc_id}_chunks.json"
            FileUtils.save_json(chunks_data, chunks_file)
            
            # Step 3: Vectorize and store
            success = self.vector_embedder.embed_and_store(chunks, doc_id)
            if success:
                logger.info("  Successfully vectorized and stored")
            else:
                logger.error("  Failed to vectorize")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing {doc_path}: {e}")
            return False
    
    def run_chunking_phase(self):
        """Run Pass 1: Chunking and vectorization for all documents"""
        logger.info("\n=== PASS 1: DOCUMENT CHUNKING & VECTORIZATION ===")
        
        docs = self.get_all_documents()
        successful = 0
        failed = 0
        
        for doc in tqdm(docs, desc="Chunking documents"):
            if self.process_chunking(doc):
                successful += 1
            else:
                failed += 1
        
        logger.info(f"\nChunking complete: {successful} successful, {failed} failed")
        
        # Get collection stats
        stats = self.vector_embedder.get_collection_stats()
        logger.info(f"Vector store stats:")
        logger.info(f"  Total vectors: {stats['total_vectors']}")
        logger.info(f"  Label distribution: {stats['label_distribution']}")
        
        return successful > 0
    
    def run_extraction_phase(self):
        """Run Pass 2: RAG extraction for all documents"""
        logger.info("\n=== PASS 2: RAG EXTRACTION ===")
        
        # Get all chunk files
        chunk_files = list(self.output_dirs['chunks'].glob("*_chunks.json"))
        logger.info(f"Found {len(chunk_files)} documents to extract from")
        
        all_extractions = []
        
        for chunk_file in tqdm(chunk_files, desc="Extracting data"):
            doc_id = chunk_file.stem.replace('_chunks', '')
            logger.info(f"\nExtracting from: {doc_id}")
            
            # Extract data
            extraction = self.rag_extractor.extract_all_categories(doc_id)
            
            if extraction:
                # Create full extraction object
                full_extraction = {
                    'document_id': doc_id,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'extraction_method': "RAG with Claude 3.5 Sonnet v2",
                    'categories': extraction
                }
                
                # Save individual extraction
                extraction_file = self.output_dirs['extractions'] / f"{doc_id}_extraction.json"
                FileUtils.save_json(full_extraction, extraction_file)
                
                all_extractions.append(full_extraction)
                
                # Show progress
                filled = sum(1 for cat in extraction.values() if cat)
                logger.info(f"  Extracted {filled}/9 categories")
            else:
                logger.error(f"  Failed to extract from {doc_id}")
        
        # Save all extractions
        if all_extractions:
            all_file = self.output_dirs['extractions'] / "all_extractions.json"
            FileUtils.save_json(all_extractions, all_file)
            logger.info(f"\nSaved {len(all_extractions)} extractions to {all_file}")
        
        return all_extractions
    
    def run_validation_phase(self, extractions):
        """Run validation on all extractions"""
        logger.info("\n=== VALIDATION PHASE ===")
        
        # Validate batch
        validation_report = self.validator.validate_batch(
            extractions, 
            self.output_dirs['validation']
        )
        
        logger.info(f"Validation results:")
        logger.info(f"  Valid documents: {validation_report['valid_documents']}")
        logger.info(f"  Invalid documents: {validation_report['invalid_documents']}")
        logger.info(f"  Average completeness: {validation_report['average_completeness']:.1f}%")
        
        # Show category coverage
        logger.info("\nCategory coverage:")
        for category, coverage in validation_report['category_coverage'].items():
            logger.info(f"  {category}: {coverage:.1f}%")
        
        return validation_report
    
    def run_output_generation(self, extractions):
        """Generate all output formats"""
        logger.info("\n=== OUTPUT GENERATION ===")
        
        # 1. Generate HTML reports
        logger.info("\nGenerating HTML reports...")
        html_results = self.html_generator.generate_batch_reports(
            extractions,
            self.output_dirs['html_reports']
        )
        logger.info(f"  Generated {html_results['successful']} HTML reports")
        
        # 2. Generate chunk visualization
        logger.info("\nGenerating chunk visualization...")
        try:
            visualizer = ChunkVisualizer(self.output_dirs['chunks'])
            visualizer.generate_overview_html(
                self.output_dirs['visualization'] / "chunk_overview.html"
            )
            logger.info("  Successfully generated chunk visualization")
        except Exception as e:
            logger.error(f"  Failed to generate visualization: {e}")
        
        # 3. Export to Excel/CSV
        logger.info("\nExporting to Excel/CSV...")
        try:
            from export_all import export_all_data
            export_results = export_all_data()
            logger.info(f"  Successfully exported to {export_results['excel_file']}")
        except Exception as e:
            logger.error(f"  Failed to export: {e}")
        
        # 4. Create dashboard data
        logger.info("\nPreparing dashboard data...")
        dashboard_data = {
            'extractions': extractions,
            'timestamp': datetime.now().isoformat(),
            'total_documents': len(extractions),
            'average_completeness': sum(e.get('completeness_score', 0) for e in extractions) / len(extractions) if extractions else 0
        }
        
        dashboard_file = self.output_dirs['dashboard'] / "dashboard_data.json"
        FileUtils.save_json(dashboard_data, dashboard_file)
        logger.info(f"  Successfully saved dashboard data")
        
        return True
    
    def run_full_pipeline(self):
        """Run the complete pipeline"""
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("METASYNTHESIZER FULL PIPELINE")
        logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        try:
            # Phase 1: Chunking and Vectorization
            if not self.run_chunking_phase():
                logger.error("Chunking phase failed, aborting pipeline")
                return False
            
            # Phase 2: RAG Extraction
            extractions = self.run_extraction_phase()
            if not extractions:
                logger.error("No extractions generated, aborting pipeline")
                return False
            
            # Phase 3: Validation
            validation_report = self.run_validation_phase(extractions)
            
            # Phase 4: Output Generation
            self.run_output_generation(extractions)
            
            # Complete
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("\n" + "="*60)
            logger.info("PIPELINE COMPLETE")
            logger.info(f"Duration: {duration}")
            logger.info(f"Documents processed: {len(extractions)}")
            logger.info(f"Average completeness: {validation_report['average_completeness']:.1f}%")
            logger.info("="*60)
            
            # Show next steps
            logger.info("\nNext steps:")
            logger.info("1. View HTML reports: 05_html_reports/index.html")
            logger.info("2. View chunk visualization: 08_chunk_visualization/chunk_overview.html")
            logger.info("3. Run dashboard: streamlit run src/visualization/meta_dashboard.py")
            logger.info("4. View Excel export: MetaSynthesizer_Export_*.xlsx")
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MetaSynthesizer full pipeline")
    parser.add_argument("--skip-chunking", action="store_true", help="Skip chunking phase if already done")
    parser.add_argument("--skip-extraction", action="store_true", help="Skip extraction phase")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation phase")
    parser.add_argument("--skip-output", action="store_true", help="Skip output generation")
    
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = FullPipeline()
    
    if args.skip_chunking and args.skip_extraction:
        # Just run validation and output on existing data
        logger.info("Loading existing extractions...")
        all_file = pipeline.output_dirs['extractions'] / "all_extractions.json"
        if all_file.exists():
            extractions = FileUtils.load_json(all_file)
            if not args.skip_validation:
                pipeline.run_validation_phase(extractions)
            if not args.skip_output:
                pipeline.run_output_generation(extractions)
        else:
            logger.error("No existing extractions found")
    else:
        # Run full pipeline
        pipeline.run_full_pipeline()


if __name__ == "__main__":
    main()
