"""
HybridChunker: Intelligent chunking within label boundaries
"""

import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import re
import tiktoken
from transformers import AutoTokenizer
import nltk
from nltk.tokenize import sent_tokenize
from src.utils.logger import logger
from src.utils.file_utils import FileUtils

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab', quiet=True)
    except:
        nltk.download('punkt', quiet=True)


@dataclass
class Chunk:
    """Represents a chunk of text with metadata"""
    text: str
    label: str
    doc_id: str
    chunk_id: str
    start_page: int
    end_page: int
    tokens: int
    overlap_context: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert chunk to dictionary for storage"""
        return {
            'text': self.text,
            'label': self.label,
            'doc_id': self.doc_id,
            'chunk_id': self.chunk_id,
            'start_page': self.start_page,
            'end_page': self.end_page,
            'tokens': self.tokens,
            'overlap_context': self.overlap_context
        }


class HybridChunker:
    """Creates intelligent chunks within label boundaries"""
    
    def __init__(self, max_tokens: int = 500, min_tokens: int = 50, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
        
    def chunk_sections(self, sections: List, doc_id: str) -> List[Chunk]:
        """
        Create chunks from colored sections
        - Respects label boundaries
        - Maintains semantic coherence
        - Includes page metadata
        """
        chunks = []
        
        for idx, section in enumerate(sections):
            # Check if section needs splitting
            if self._needs_splitting(section):
                # Split intelligently
                sub_chunks = self._split_intelligently(section, doc_id, idx)
            else:
                # Small sections remain whole
                chunk = Chunk(
                    text=section.text,
                    label=section.label,
                    doc_id=doc_id,
                    chunk_id=f"{doc_id}_s{idx}_c0",
                    start_page=section.start_page,
                    end_page=section.end_page,
                    tokens=len(self.tokenizer.encode(section.text))
                )
                sub_chunks = [chunk]
                
            chunks.extend(sub_chunks)
            
        # Add context overlap between chunks
        chunks = self._add_context_overlap(chunks)
        
        logger.info(f"Created {len(chunks)} chunks from {len(sections)} sections")
        return chunks
        
    def _needs_splitting(self, section) -> bool:
        """Check if section needs to be split into multiple chunks"""
        token_count = len(self.tokenizer.encode(section.text))
        return token_count > self.max_tokens
        
    def _split_intelligently(self, section, doc_id: str, section_idx: int) -> List[Chunk]:
        """Split section into chunks while preserving semantic boundaries"""
        chunks = []
        
        # First, try to split by paragraphs
        paragraphs = section.text.split('\n\n')
        
        current_chunk_text = ""
        current_chunk_start_page = section.start_page
        chunk_idx = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Check if adding this paragraph would exceed max tokens
            combined_text = f"{current_chunk_text}\n\n{para}".strip() if current_chunk_text else para
            token_count = len(self.tokenizer.encode(combined_text))
            
            if token_count <= self.max_tokens:
                # Add to current chunk
                current_chunk_text = combined_text
            else:
                # Save current chunk if it has content
                if current_chunk_text and len(self.tokenizer.encode(current_chunk_text)) >= self.min_tokens:
                    chunk = Chunk(
                        text=current_chunk_text,
                        label=section.label,
                        doc_id=doc_id,
                        chunk_id=f"{doc_id}_s{section_idx}_c{chunk_idx}",
                        start_page=current_chunk_start_page,
                        end_page=self._estimate_end_page(
                            current_chunk_text, 
                            current_chunk_start_page, 
                            section
                        ),
                        tokens=len(self.tokenizer.encode(current_chunk_text))
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                    current_chunk_start_page = self._estimate_start_page(para, section)
                    current_chunk_text = ""
                
                # Check if the paragraph itself is too large
                para_tokens = len(self.tokenizer.encode(para))
                if para_tokens > self.max_tokens:
                    # Split the paragraph by sentences
                    para_chunks = self._split_paragraph(
                        para, section, doc_id, section_idx, chunk_idx
                    )
                    chunks.extend(para_chunks)
                    chunk_idx += len(para_chunks)
                    current_chunk_text = ""
                else:
                    # Start new chunk with current paragraph
                    current_chunk_text = para
                    
        # Don't forget the last chunk
        if current_chunk_text:
            chunk = Chunk(
                text=current_chunk_text,
                label=section.label,
                doc_id=doc_id,
                chunk_id=f"{doc_id}_s{section_idx}_c{chunk_idx}",
                start_page=current_chunk_start_page,
                end_page=section.end_page,
                tokens=len(self.tokenizer.encode(current_chunk_text))
            )
            chunks.append(chunk)
            
        return chunks
        
    def _split_paragraph(self, para: str, section, doc_id: str, 
                        section_idx: int, start_chunk_idx: int) -> List[Chunk]:
        """Split a large paragraph into smaller chunks by sentences"""
        chunks = []
        sentences = self._split_into_sentences(para)
        
        current_text = ""
        chunk_idx = start_chunk_idx
        
        for sentence in sentences:
            combined = f"{current_text} {sentence}".strip() if current_text else sentence
            if len(self.tokenizer.encode(combined)) <= self.max_tokens:
                current_text = combined
            else:
                if current_text:
                    chunk = Chunk(
                        text=current_text,
                        label=section.label,
                        doc_id=doc_id,
                        chunk_id=f"{doc_id}_s{section_idx}_c{chunk_idx}",
                        start_page=section.start_page,
                        end_page=section.end_page,
                        tokens=len(self.tokenizer.encode(current_text))
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                
                # If single sentence is too long, split by tokens
                if len(self.tokenizer.encode(sentence)) > self.max_tokens:
                    # Fallback: split by token count
                    tokens = self.tokenizer.encode(sentence)
                    for i in range(0, len(tokens), self.max_tokens):
                        token_chunk = tokens[i:i + self.max_tokens]
                        text_chunk = self.tokenizer.decode(token_chunk)
                        chunk = Chunk(
                            text=text_chunk,
                            label=section.label,
                            doc_id=doc_id,
                            chunk_id=f"{doc_id}_s{section_idx}_c{chunk_idx}",
                            start_page=section.start_page,
                            end_page=section.end_page,
                            tokens=len(token_chunk)
                        )
                        chunks.append(chunk)
                        chunk_idx += 1
                    current_text = ""
                else:
                    current_text = sentence
                    
        # Add remaining text
        if current_text:
            chunk = Chunk(
                text=current_text,
                label=section.label,
                doc_id=doc_id,
                chunk_id=f"{doc_id}_s{section_idx}_c{chunk_idx}",
                start_page=section.start_page,
                end_page=section.end_page,
                tokens=len(self.tokenizer.encode(current_text))
            )
            chunks.append(chunk)
            
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK"""
        try:
            sentences = sent_tokenize(text, language='german')
        except:
            # Fallback to simple splitting
            sentences = text.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')
            sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
        
    def _add_context_overlap(self, chunks: List[Chunk]) -> List[Chunk]:
        """Add overlapping context between adjacent chunks"""
        for i in range(len(chunks)):
            if i > 0 and chunks[i].label == chunks[i-1].label:
                # Get last sentences from previous chunk
                prev_sentences = sent_tokenize(chunks[i-1].text)
                if prev_sentences:
                    # Take last 1-2 sentences as context
                    context_sentences = prev_sentences[-2:] if len(prev_sentences) > 1 else prev_sentences
                    context = " ".join(context_sentences)
                    
                    # Check token limit
                    context_tokens = len(self.tokenizer.encode(context))
                    if context_tokens <= self.overlap_tokens:
                        chunks[i].overlap_context = context
                        
        return chunks
        
    def _estimate_end_page(self, chunk_text: str, start_page: int, section) -> int:
        """Estimate end page based on text proportion"""
        chunk_proportion = len(chunk_text) / len(section.text)
        page_span = section.end_page - section.start_page
        estimated_span = int(chunk_proportion * page_span)
        return min(start_page + estimated_span, section.end_page)
        
    def _estimate_start_page(self, text: str, section) -> int:
        """Estimate start page based on text position"""
        text_before = section.text.split(text)[0]
        position_ratio = len(text_before) / len(section.text)
        page_span = section.end_page - section.start_page
        estimated_offset = int(position_ratio * page_span)
        return section.start_page + estimated_offset
