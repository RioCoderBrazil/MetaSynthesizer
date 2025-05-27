#!/usr/bin/env python3
"""
Test script for Pass 1 of MetaSynthesizer pipeline
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.pass1 import ColorParser, HybridChunker, VectorEmbedder
from src.utils import FileUtils, setup_logger

# Load environment variables
load_dotenv('config/.env')

# Setup logger
logger = setup_logger("test_pass1")


def test_pass1_pipeline():
    """Test the complete Pass 1 pipeline with one document"""
    
    # Configuration
    color_config = "config/color_mappings.json"
    docs_dir = "01_colored_reports"
    
    # Get first document
    docx_files = FileUtils.list_docx_files(docs_dir)
    if not docx_files:
        logger.error(f"No DOCX files found in {docs_dir}")
        return
        
    test_doc = docx_files[0]
    doc_id = FileUtils.get_doc_id(test_doc)
    
    logger.info(f"Testing Pass 1 with document: {test_doc}")
    logger.info(f"Document ID: {doc_id}")
    
    # Initialize components
    logger.info("\n=== Initializing Components ===")
    color_parser = ColorParser(color_config)
    hybrid_chunker = HybridChunker(max_tokens=400, min_tokens=50)
    vector_embedder = VectorEmbedder()
    
    # Step 1: Color Parsing
    logger.info("\n=== Step 1: Color Parsing ===")
    sections = color_parser.parse_document(test_doc)
    
    logger.info(f"Found {len(sections)} colored sections:")
    for i, section in enumerate(sections):
        logger.info(f"  Section {i+1}:")
        logger.info(f"    Label: {section.label}")
        logger.info(f"    Pages: {section.start_page}-{section.end_page}")
        logger.info(f"    Text length: {len(section.text)} chars")
        logger.info(f"    Confidence: {section.confidence:.2f}")
        logger.info(f"    Preview: {section.text[:100]}...")
        
    # Save sections
    output_paths = FileUtils.get_output_paths(doc_id)
    FileUtils.ensure_directory(output_paths['chunks'].parent)
    
    sections_data = [{
        'label': s.label,
        'text': s.text,
        'start_page': s.start_page,
        'end_page': s.end_page,
        'confidence': s.confidence,
        'color_rgb': s.color_rgb
    } for s in sections]
    
    sections_file = output_paths['chunks'].parent / f"{doc_id}_sections.json"
    FileUtils.save_json(sections_data, sections_file)
    logger.info(f"Saved sections to: {sections_file}")
    
    # Step 2: Hybrid Chunking
    logger.info("\n=== Step 2: Hybrid Chunking ===")
    chunks = hybrid_chunker.chunk_sections(sections, doc_id)
    
    logger.info(f"Created {len(chunks)} chunks:")
    
    # Show chunk distribution by label
    label_counts = {}
    for chunk in chunks:
        label_counts[chunk.label] = label_counts.get(chunk.label, 0) + 1
        
    for label, count in label_counts.items():
        logger.info(f"  {label}: {count} chunks")
        
    # Show sample chunks
    logger.info("\nSample chunks:")
    for i in range(min(3, len(chunks))):
        chunk = chunks[i]
        logger.info(f"  Chunk {chunk.chunk_id}:")
        logger.info(f"    Label: {chunk.label}")
        logger.info(f"    Pages: {chunk.start_page}-{chunk.end_page}")
        logger.info(f"    Tokens: {chunk.tokens}")
        logger.info(f"    Has overlap: {'Yes' if chunk.overlap_context else 'No'}")
        logger.info(f"    Preview: {chunk.text[:100]}...")
        
    # Save chunks
    chunks_data = [chunk.to_dict() for chunk in chunks]
    FileUtils.save_json(chunks_data, output_paths['chunks'])
    logger.info(f"Saved chunks to: {output_paths['chunks']}")
    
    # Step 3: Vector Embedding
    logger.info("\n=== Step 3: Vector Embedding ===")
    success = vector_embedder.embed_and_store(chunks, doc_id)
    
    if success:
        logger.info("Successfully embedded and stored vectors")
        
        # Get collection stats
        stats = vector_embedder.get_collection_stats()
        logger.info(f"Collection stats:")
        logger.info(f"  Total vectors: {stats['total_vectors']}")
        logger.info(f"  Vector dimension: {stats['vector_dimension']}")
        logger.info(f"  Label distribution: {stats['label_distribution']}")
        
        # Test search
        logger.info("\n=== Testing Vector Search ===")
        test_queries = [
            ("Empfehlungen", "recommendations"),
            ("Feststellungen", "findings"),
            ("Prüfung", None)
        ]
        
        for query, label_filter in test_queries:
            logger.info(f"\nSearching for: '{query}' (filter: {label_filter})")
            results = vector_embedder.search_similar(query, label_filter, limit=3)
            
            for j, result in enumerate(results):
                logger.info(f"  Result {j+1}:")
                logger.info(f"    Score: {result['score']:.3f}")
                logger.info(f"    Label: {result['label']}")
                logger.info(f"    Pages: {result['pages']}")
                logger.info(f"    Preview: {result['text'][:100]}...")
    else:
        logger.error("Failed to embed and store vectors")
        
    logger.info("\n=== Pass 1 Test Complete ===")


if __name__ == "__main__":
    test_pass1_pipeline()
