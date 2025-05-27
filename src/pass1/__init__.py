"""
Pass 1: Color Detection → Hybrid Chunking → Vectorization Pipeline

This module contains the components for the first pass of the MetaSynthesizer pipeline:
- ColorParser: Extracts colored sections from DOCX documents
- HybridChunker: Creates intelligent chunks within label boundaries
- VectorEmbedder: Generates embeddings and stores them in Qdrant
"""

from .color_parser import ColorParser
from .hybrid_chunker import HybridChunker
from .vector_embedder import VectorEmbedder

__all__ = ['ColorParser', 'HybridChunker', 'VectorEmbedder']
