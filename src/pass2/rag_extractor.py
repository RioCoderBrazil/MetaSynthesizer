"""
RAG Extractor - Semantic search and context retrieval for category extraction
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchAny
from sentence_transformers import SentenceTransformer
import anthropic
import os
from ..utils.logger import logger
import numpy as np


@dataclass
class RetrievedContext:
    """Retrieved context from vector search"""
    text: str
    label: str
    pages: str
    score: float
    chunk_id: str


class RAGExtractor:
    """
    Extracts data for 23 categories using RAG approach
    """
    
    def __init__(self, 
                 qdrant_host: str = 'localhost',
                 qdrant_port: int = 6333,
                 collection_name: str = 'metasynthesizer',
                 anthropic_api_key: str = None,
                 embedding_model: str = 'sentence-transformers/all-mpnet-base-v2'):
        """
        Initialize RAG extractor
        
        Args:
            qdrant_host: Qdrant host
            qdrant_port: Qdrant port
            collection_name: Collection name
            anthropic_api_key: Anthropic API key
            embedding_model: Embedding model name
        """
        # Initialize Qdrant client
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        
        # Initialize LLM
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"  # Latest Claude Sonnet 4 model
        
        # Initialize embedding model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Load schemas
        with open('config/categories_schema_full.json', 'r') as f:
            self.categories_schema = json.load(f)
        
        with open('config/color_mappings.json', 'r') as f:
            self.color_mappings = json.load(f)
    
    def extract_for_category(self, category_name: str, doc_id: str, max_contexts: int = 10) -> Dict[str, Any]:
        """
        Extract data for a specific category
        
        Args:
            category_name: Name of the category to extract
            doc_id: Document ID
            max_contexts: Maximum number of contexts to retrieve
            
        Returns:
            Extracted data for the category
        """
        logger.info(f"Extracting data for category: {category_name}")
        
        # Get category schema
        category_schema = self.categories_schema['categories'].get(category_name)
        if not category_schema:
            logger.error(f"Category {category_name} not found in schema")
            return {}
        
        # Generate search queries
        queries = self._generate_queries(category_name, category_schema)
        
        # Retrieve relevant contexts
        contexts = self._retrieve_contexts(queries, doc_id, max_contexts)
        
        # Extract data using LLM
        extracted_data = self._llm_extract(category_name, category_schema, contexts)
        
        return extracted_data
    
    def _generate_queries(self, category_name: str, category_schema: Dict) -> List[str]:
        """
        Generate multiple search queries for a category
        
        Args:
            category_name: Category name
            category_schema: Category schema
            
        Returns:
            List of search queries
        """
        queries = []
        
        # Add category name as query
        queries.append(category_name)
        
        # Add field names as queries
        if 'fields' in category_schema:
            for field_name, field_info in category_schema['fields'].items():
                queries.append(field_name)
                
                # Add field description if available
                if 'description' in field_info:
                    queries.append(field_info['description'])
        
        # Add German translations/synonyms
        query_expansions = {
            "findings": ["Feststellungen", "Befunde", "Ergebnisse"],
            "recommendations": ["Empfehlungen", "Vorschläge", "Massnahmen"],
            "costs": ["Kosten", "Ausgaben", "Aufwand", "Franken", "CHF"],
            "risks": ["Risiken", "Gefahren", "Risikomanagement"],
            "compliance": ["Compliance", "Rechtskonformität", "Einhaltung"],
            "environmental": ["Umwelt", "Altlasten", "Sanierung", "Boden"],
            "responsible_entity": ["Verantwortlich", "Zuständig", "Stelle"],
            "timeline": ["Zeitplan", "Frist", "Termin", "Datum"],
            "status": ["Status", "Stand", "Zustand"],
            "priority": ["Priorität", "Wichtigkeit", "Dringlichkeit"]
        }
        
        # Add expansions
        for key, expansions in query_expansions.items():
            if key in category_name.lower() or any(key in field.lower() for field in category_schema.get('fields', {})):
                queries.extend(expansions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)
        
        logger.info(f"Generated {len(unique_queries)} queries for {category_name}")
        return unique_queries
    
    def _retrieve_contexts(self, queries: List[str], doc_id: str, max_contexts: int) -> List[RetrievedContext]:
        """
        Retrieve relevant contexts using semantic search
        
        Args:
            queries: List of search queries
            doc_id: Document ID
            max_contexts: Maximum contexts to retrieve
            
        Returns:
            List of retrieved contexts
        """
        all_contexts = []
        seen_chunks = set()
        
        # Search with each query
        for query in queries:
            query_vector = self.embedder.encode(query).tolist()
            
            # Search in Qdrant with doc_id filter
            search_result = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=max_contexts,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match={"value": doc_id}
                        )
                    ]
                )
            )
            
            # Process results
            for hit in search_result:
                chunk_id = hit.payload.get('chunk_idx', '')
                
                # Avoid duplicates
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    
                    context = RetrievedContext(
                        text=hit.payload['text'],
                        label=hit.payload['label'],
                        pages=f"p. {hit.payload['start_page']}-{hit.payload['end_page']}",
                        score=hit.score,
                        chunk_id=chunk_id
                    )
                    all_contexts.append(context)
        
        # Sort by score and take top contexts
        all_contexts.sort(key=lambda x: x.score, reverse=True)
        top_contexts = all_contexts[:max_contexts]
        
        logger.info(f"Retrieved {len(top_contexts)} unique contexts from {len(all_contexts)} total")
        return top_contexts
    
    def _llm_extract(self, category_name: str, category_schema: Dict, contexts: List[RetrievedContext]) -> Dict[str, Any]:
        """
        Extract structured data using LLM
        
        Args:
            category_name: Category name
            category_schema: Category schema
            contexts: Retrieved contexts
            
        Returns:
            Extracted structured data
        """
        # Prepare context text
        context_text = "\n\n".join([
            f"[{ctx.label.upper()} - {ctx.pages} - Score: {ctx.score:.3f}]\n{ctx.text}"
            for ctx in contexts
        ])
        
        # Prepare field descriptions
        field_descriptions = []
        for field_name, field_info in category_schema.get('fields', {}).items():
            field_type = field_info.get('type', 'text')
            max_length = field_info.get('max_length', 'unlimited')
            description = field_info.get('description', '')
            
            field_desc = f"- {field_name} ({field_type}, max length: {max_length}): {description}"
            field_descriptions.append(field_desc)
        
        # Create extraction prompt
        prompt = f"""You are an expert data extractor for Swiss Federal Audit Office (EFK) reports.

Extract information for the category "{category_name}" from the following document contexts.

Category fields to extract:
{chr(10).join(field_descriptions)}

Important guidelines:
1. Extract ONLY information that is explicitly stated in the contexts
2. Use the exact wording from the document when possible
3. For numeric values, include units (e.g., "33.3 Mio. CHF")
4. For dates, use the format found in the document
5. If information is not found, use null
6. Pay attention to the label (WIK, INTRODUCTION, EVALUATION, etc.) as it indicates the section type
7. Respect max_length constraints for each field

Document contexts:
{context_text}

Return the extracted data as a valid JSON object with the field names as keys.
"""

        try:
            # Call Claude
            response = self.client.messages.create(
                model=self.model,  
                max_tokens=2000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response
            response_text = response.content[0].text
            
            # Extract JSON from response
            try:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    extracted_data = json.loads(response_text)
                    
                logger.info(f"Successfully extracted data for {category_name}")
                return extracted_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response: {response_text}")
                return {}
                
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {}
    
    def extract_all_categories(self, doc_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract data for all categories
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary with category data
        """
        results = {}
        
        for category_name in self.categories_schema['categories']:
            logger.info(f"Processing category: {category_name}")
            category_data = self.extract_for_category(category_name, doc_id)
            results[category_name] = category_data
            
        return results
