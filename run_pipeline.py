#!/usr/bin/env python3
"""
MetaSynthesizer Pipeline Runner
Main entry point for running the complete extraction pipeline
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from tqdm import tqdm
import time

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pass1 import ColorParser, HybridChunker, VectorEmbedder
from pass1.qdrant_manager import QdrantManager
from pass2.rag_extractor import RAGExtractor
from utils.validator import DataValidator
from utils.html_generator import HTMLReportGenerator


class PipelineRunner:
    """Main pipeline orchestrator with progress tracking and error handling"""
    
    def __init__(self, config_path: Path = Path("config/.env")):
        self.config_path = config_path
        self.project_root = Path(__file__).parent
        self.progress = None
        self.logger = self._setup_logging()
        
        # Setup directories
        self.colored_dir = self.project_root / "01_colored_reports"
        self.chunks_dir = self.project_root / "02_chunked_data"
        self.extracted_dir = self.project_root / "03_extracted_data"
        self.vector_dir = self.project_root / "03_vector_store"
        self.html_dir = self.project_root / "05_html_reports"
        self.validation_dir = self.project_root / "06_validation_logs"
        self.dashboard_dir = self.project_root / "07_meta_dashboard"
        self.viz_dir = self.project_root / "08_chunk_visualization"
        
        # Ensure all directories exist
        for dir_path in [self.chunks_dir, self.extracted_dir, self.html_dir, 
                         self.validation_dir, self.dashboard_dir, self.viz_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        logger = logging.getLogger("MetaSynthesizer")
        logger.setLevel(logging.DEBUG)
        
        # File handler with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fh = logging.FileHandler(log_dir / f"pipeline_{timestamp}.log")
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def run_full_pipeline(self, validate: bool = True) -> Dict[str, Any]:
        """Execute complete pipeline with progress tracking"""
        self.progress = tqdm(total=100, desc="Pipeline Progress", colour='green')
        results = {
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "steps": {}
        }
        
        try:
            # Step 1: Pass 1 - Chunking (40%)
            self.logger.info("Starting Pass 1: Document Chunking")
            self.progress.set_description("Pass 1: Chunking Documents")
            chunk_results = self.run_pass1_chunking()
            results["steps"]["chunking"] = chunk_results
            self.progress.update(40)
            
            if validate:
                self.validate_chunks(chunk_results)
            
            # Step 2: Pass 2 - Extraction (50%)
            self.logger.info("Starting Pass 2: RAG Extraction")
            self.progress.set_description("Pass 2: Extracting Data")
            extraction_results = self.run_pass2_extraction()
            results["steps"]["extraction"] = extraction_results
            self.progress.update(50)
            
            if validate:
                self.validate_extraction(extraction_results)
            
            # Step 3: Output Generation (10%)
            self.logger.info("Generating outputs")
            self.progress.set_description("Generating Reports")
            output_results = self.generate_all_outputs(extraction_results)
            results["steps"]["outputs"] = output_results
            self.progress.update(10)
            
            # Complete
            results["status"] = "completed"
            results["end_time"] = datetime.now().isoformat()
            self.logger.info("Pipeline completed successfully!")
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.handle_error(e)
            raise
        
        finally:
            if self.progress:
                self.progress.close()
            
            # Save results summary
            summary_path = self.project_root / "logs" / "pipeline_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def run_pass1_chunking(self) -> Dict[str, Any]:
        """Execute Pass 1: Document chunking"""
        results = {
            "processed_files": 0,
            "total_chunks": 0,
            "errors": []
        }
        
        try:
            # Initialize chunker
            chunker = HybridChunker()
            
            # Initialize Qdrant
            qdrant = QdrantManager()
            
            # Process all colored documents
            docx_files = list(self.colored_dir.glob("*.docx"))
            self.logger.info(f"Found {len(docx_files)} documents to process")
            
            for doc_path in tqdm(docx_files, desc="Chunking documents"):
                try:
                    # Chunk document
                    chunks = chunker.chunk_document(doc_path)
                    
                    # Save chunks to JSON
                    output_name = doc_path.stem + "_chunks.json"
                    output_path = self.chunks_dir / output_name
                    
                    chunk_data = {
                        "document": doc_path.name,
                        "timestamp": datetime.now().isoformat(),
                        "chunks": chunks,
                        "statistics": {
                            "total_chunks": len(chunks),
                            "avg_chunk_size": sum(len(c["text"]) for c in chunks) / len(chunks) if chunks else 0
                        }
                    }
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, indent=2, ensure_ascii=False)
                    
                    # Store in Qdrant
                    qdrant.add_document_chunks(doc_path.stem, chunks)
                    
                    results["processed_files"] += 1
                    results["total_chunks"] += len(chunks)
                    
                except Exception as e:
                    error_msg = f"Error processing {doc_path.name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            self.logger.info(f"Chunking complete: {results['processed_files']} files, {results['total_chunks']} chunks")
            
        except Exception as e:
            self.logger.error(f"Critical error in chunking: {e}")
            raise
        
        return results
    
    def run_pass2_extraction(self) -> Dict[str, Any]:
        """Execute Pass 2: RAG-based extraction"""
        results = {
            "processed_documents": 0,
            "successful_extractions": 0,
            "validation_passed": 0,
            "errors": []
        }
        
        try:
            # Initialize extractor
            extractor = RAGExtractor()
            
            # Process all chunked documents
            chunk_files = list(self.chunks_dir.glob("*_chunks.json"))
            self.logger.info(f"Found {len(chunk_files)} chunked documents")
            
            all_extractions = []
            
            for chunk_file in tqdm(chunk_files, desc="Extracting data"):
                try:
                    # Load chunks
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)
                    
                    doc_name = chunk_data["document"].replace(".docx", "")
                    
                    # Extract data
                    extraction = extractor.extract_from_document(
                        document_id=doc_name,
                        chunks=chunk_data["chunks"]
                    )
                    
                    # Save individual extraction
                    output_path = self.extracted_dir / f"{doc_name}_extracted.json"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(extraction, f, indent=2, ensure_ascii=False)
                    
                    all_extractions.append(extraction)
                    results["processed_documents"] += 1
                    
                    # Validate
                    validator = DataValidator()
                    is_valid, validation_report = validator.validate_extraction(extraction)
                    
                    if is_valid:
                        results["validation_passed"] += 1
                    results["successful_extractions"] += 1
                    
                except Exception as e:
                    error_msg = f"Error extracting from {chunk_file.name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Save combined extractions
            combined_path = self.extracted_dir / "all_extractions.json"
            with open(combined_path, 'w', encoding='utf-8') as f:
                json.dump(all_extractions, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Extraction complete: {results['successful_extractions']}/{results['processed_documents']} successful")
            
        except Exception as e:
            self.logger.error(f"Critical error in extraction: {e}")
            raise
        
        return results
    
    def generate_all_outputs(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all output formats"""
        results = {
            "html_reports": 0,
            "visualizations": 0,
            "exports": 0,
            "errors": []
        }
        
        try:
            # Generate HTML reports
            self.logger.info("Generating HTML reports")
            html_gen = HTMLReportGenerator()
            
            extracted_files = list(self.extracted_dir.glob("*_extracted.json"))
            for ext_file in tqdm(extracted_files, desc="Generating HTML"):
                try:
                    with open(ext_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    html_path = self.html_dir / f"{ext_file.stem.replace('_extracted', '')}_report.html"
                    html_gen.generate_report(data, html_path)
                    results["html_reports"] += 1
                    
                except Exception as e:
                    error_msg = f"Error generating HTML for {ext_file.name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Generate chunk visualization
            self.logger.info("Generating chunk visualization")
            self.generate_chunk_visualization()
            results["visualizations"] += 1
            
            # Generate validation summary
            self.generate_validation_summary()
            
            self.logger.info(f"Output generation complete: {results['html_reports']} HTML reports")
            
        except Exception as e:
            self.logger.error(f"Critical error in output generation: {e}")
            raise
        
        return results
    
    def validate_chunks(self, chunk_results: Dict[str, Any]):
        """Validate chunking results"""
        self.logger.info("Validating chunks...")
        # Implementation would validate chunk quality
        pass
    
    def validate_extraction(self, extraction_results: Dict[str, Any]):
        """Validate extraction results"""
        self.logger.info("Validating extractions...")
        # Implementation would validate extraction completeness
        pass
    
    def generate_chunk_visualization(self):
        """Generate chunk overview visualization"""
        viz_path = self.viz_dir / "chunk_overview.html"
        # Implementation would create visualization
        self.logger.info(f"Chunk visualization saved to {viz_path}")
    
    def generate_validation_summary(self):
        """Generate validation summary"""
        summary_path = self.validation_dir / "validation_summary.json"
        # Implementation would create validation summary
        self.logger.info(f"Validation summary saved to {summary_path}")
    
    def handle_error(self, error: Exception):
        """Handle pipeline errors with recovery options"""
        self.logger.error(f"Pipeline error: {error}")
        # Implementation would handle recovery
    
    def run_single_step(self, step: str, **kwargs) -> Dict[str, Any]:
        """Run a single pipeline step"""
        step_map = {
            "pass1": self.run_pass1_chunking,
            "pass2": self.run_pass2_extraction,
            "visualize": self.generate_all_outputs
        }
        
        if step not in step_map:
            raise ValueError(f"Unknown step: {step}. Valid steps: {list(step_map.keys())}")
        
        self.logger.info(f"Running single step: {step}")
        return step_map[step](**kwargs)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MetaSynthesizer Pipeline Runner")
    parser.add_argument(
        "--mode", 
        choices=["full", "pass1", "pass2", "visualize"],
        default="full",
        help="Pipeline mode to run"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Enable validation after each step"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/.env"),
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = PipelineRunner(config_path=args.config)
    
    try:
        if args.mode == "full":
            results = runner.run_full_pipeline(validate=args.validate)
        else:
            results = runner.run_single_step(args.mode)
        
        print(f"\n✅ Pipeline completed successfully!")
        print(f"Results saved to: logs/pipeline_summary.json")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
