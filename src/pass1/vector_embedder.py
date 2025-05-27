"""
VectorEmbedder: Embedding generation and Qdrant storage
"""

import logging
from typing import List, Dict, Optional
from uuid import uuid4
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import json

logger = logging.getLogger(__name__)


class VectorEmbedder:
    """Generates embeddings and stores them in Qdrant"""
    
    def __init__(self, qdrant_host: str = "localhost", collection_name: str = "metasynthesizer"):
        self.encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.qdrant = QdrantClient(host=qdrant_host, port=6333)
        self.collection_name = collection_name
        self.vector_dim = 768  # all-mpnet-base-v2 dimension
        self._ensure_collection_exists()
        
    def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists"""
        try:
            # Try to create collection
            logger.info(f"Creating collection '{self.collection_name}'")
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
            )
        except Exception as e:
            # If error contains "already exists", that's fine
            if "already exists" in str(e):
                logger.info(f"Collection '{self.collection_name}' already exists")
            else:
                logger.error(f"Error creating collection: {e}")
                raise
                
    def embed_and_store(self, chunks: List, doc_id: str) -> bool:
        """
        Embed chunks and store in Qdrant
        Returns True if successful
        """
        try:
            # Prepare texts for embedding
            texts = [chunk.text for chunk in chunks]
            
            # Generate embeddings in batches
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = self.encoder.encode(texts, batch_size=32, show_progress_bar=True)
            
            # Prepare points for Qdrant
            points = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid4())
                
                # Prepare metadata
                metadata = {
                    "doc_id": doc_id,
                    "chunk_id": chunk.chunk_id,
                    "label": chunk.label,
                    "start_page": chunk.start_page,
                    "end_page": chunk.end_page,
                    "tokens": chunk.tokens,
                    "text": chunk.text[:1000],  # Store first 1000 chars for preview
                    "overlap_context": chunk.overlap_context[:500] if chunk.overlap_context else None
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=metadata
                )
                points.append(point)
                
            # Batch upload to Qdrant
            logger.info(f"Uploading {len(points)} vectors to Qdrant")
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            # Verify upload
            collection_info = self.qdrant.get_collection(self.collection_name)
            logger.info(f"Collection now contains {collection_info.points_count} points")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in embed_and_store: {str(e)}")
            return False
            
    def search_similar(self, query: str, label_filter: Optional[str] = None, 
                      limit: int = 10) -> List[Dict]:
        """
        Search for similar chunks
        Optionally filter by label
        """
        # Generate query embedding
        query_embedding = self.encoder.encode(query)
        
        # Prepare filter if label specified
        search_filter = None
        if label_filter:
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="label",
                        match=models.MatchValue(value=label_filter)
                    )
                ]
            )
            
        # Perform search
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=False
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "score": result.score,
                "doc_id": result.payload.get("doc_id"),
                "chunk_id": result.payload.get("chunk_id"),
                "label": result.payload.get("label"),
                "text": result.payload.get("text"),
                "pages": f"p. {result.payload.get('start_page')}-{result.payload.get('end_page')}"
            }
            formatted_results.append(formatted_result)
            
        return formatted_results
        
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        info = self.qdrant.get_collection(self.collection_name)
        
        # Get label distribution
        label_counts = {}
        offset = None
        
        while True:
            # Scroll through all points
            records, offset = self.qdrant.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            for record in records:
                label = record.payload.get("label", "unknown")
                label_counts[label] = label_counts.get(label, 0) + 1
                
            if offset is None:
                break
                
        return {
            "total_vectors": info.points_count,
            "vector_dimension": self.vector_dim,
            "label_distribution": label_counts
        }
        
    def delete_by_doc_id(self, doc_id: str) -> bool:
        """Delete all vectors for a specific document"""
        try:
            self.qdrant.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="doc_id",
                                match=models.MatchValue(value=doc_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Deleted all vectors for document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            return False
