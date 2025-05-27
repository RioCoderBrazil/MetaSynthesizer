"""
ColorParser: Extracts colored sections from DOCX documents with page tracking
"""

import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from docx import Document
from docx.shared import RGBColor
import webcolors

logger = logging.getLogger(__name__)


@dataclass
class ColoredSection:
    """Represents a colored section in the document"""
    label: str
    text: str
    start_page: int
    end_page: int
    confidence: float
    color_rgb: Tuple[int, int, int]
    
    def add_title(self, title: str):
        """Prepends title to the text content"""
        self.text = f"{title}\n{self.text}".strip()


class PageTracker:
    """Tracks page numbers based on document structure"""
    def __init__(self):
        self.current_page = 1
        self.paragraph_count = 0
        self.approx_paragraphs_per_page = 30  # Estimate, can be adjusted
        
    def get_current_page(self, paragraph) -> int:
        """Estimates current page based on paragraph position"""
        # Check for explicit page breaks
        if hasattr(paragraph, '_element'):
            for elem in paragraph._element.xpath('.//w:br[@w:type="page"]'):
                self.current_page += 1
                self.paragraph_count = 0
                
        self.paragraph_count += 1
        
        # Estimate page change based on paragraph count
        if self.paragraph_count >= self.approx_paragraphs_per_page:
            self.current_page += 1
            self.paragraph_count = 0
            
        return self.current_page


class ColorParser:
    """Parses DOCX documents to extract colored sections with labels"""
    
    def __init__(self, color_config_path: str):
        self.color_mappings = self._load_color_mappings(color_config_path)
        self.page_tracker = PageTracker()
        self.tolerance = self.color_mappings.get('tolerance', 10)
        
    def _load_color_mappings(self, config_path: str) -> Dict:
        """Load color to label mappings from config file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def parse_document(self, docx_path: str) -> List[ColoredSection]:
        """
        Extract colored sections from DOCX document
        Returns list of ColoredSection objects with labels, text, and page numbers
        """
        doc = Document(docx_path)
        sections = []
        current_section = None
        self.page_tracker = PageTracker()  # Reset for new document
        
        for paragraph in doc.paragraphs:
            # Skip empty paragraphs
            if not paragraph.text.strip():
                continue
                
            # Get color and page info
            color_rgb = self._extract_color(paragraph)
            page_num = self.page_tracker.get_current_page(paragraph)
            
            if color_rgb:
                # Map color to label
                label, confidence = self._map_color_to_label(color_rgb)
                
                if label:
                    # Check if this is a title (bold or larger font)
                    is_title = self._is_title(paragraph)
                    
                    # If we have a current section and this is a new color
                    if current_section and current_section.label != label:
                        # Save the current section
                        sections.append(current_section)
                        current_section = None
                    
                    # Create new section or append to existing
                    if current_section is None:
                        current_section = ColoredSection(
                            label=label,
                            text=paragraph.text,
                            start_page=page_num,
                            end_page=page_num,
                            confidence=confidence,
                            color_rgb=color_rgb
                        )
                    else:
                        # If it's a title and we already have text, prepend it
                        if is_title and current_section.text:
                            current_section.add_title(paragraph.text)
                        else:
                            # Otherwise append normally
                            current_section.text += f"\n{paragraph.text}"
                        current_section.end_page = page_num
            else:
                # Non-colored text - if we have a current section, it might be continuation
                if current_section:
                    current_section.text += f"\n{paragraph.text}"
                    current_section.end_page = page_num
                    
        # Don't forget the last section
        if current_section:
            sections.append(current_section)
            
        return self._validate_sections(sections)
        
    def _extract_color(self, paragraph) -> Optional[Tuple[int, int, int]]:
        """Extract the dominant color from a paragraph"""
        colors = []
        
        # Check paragraph-level shading (using XML directly)
        if hasattr(paragraph, '_element'):
            # XPath without namespaces
            shading_elements = paragraph._element.xpath('.//w:shd')
            for shading in shading_elements:
                fill = shading.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if fill and fill != 'auto':
                    try:
                        # Convert hex to RGB
                        if fill.startswith('#'):
                            fill = fill[1:]
                        r = int(fill[0:2], 16)
                        g = int(fill[2:4], 16)
                        b = int(fill[4:6], 16)
                        colors.append((r, g, b))
                    except:
                        pass
                    
        # Check run-level highlighting
        for run in paragraph.runs:
            if run.font.highlight_color is not None:
                # Convert highlight color enum to RGB
                try:
                    # Get the actual color value
                    if hasattr(run.font.highlight_color, 'real'):
                        color_val = run.font.highlight_color.real
                    else:
                        color_val = run.font.highlight_color
                    
                    # Map numeric values to color names
                    highlight_map = {
                        1: 'black',
                        2: 'blue',  
                        3: 'turquoise',
                        4: 'bright_green',
                        5: 'pink',
                        6: 'red',
                        7: 'yellow',
                        8: 'white',
                        9: 'dark_blue',
                        10: 'teal',
                        11: 'green',
                        12: 'violet',
                        13: 'dark_red',
                        14: 'dark_yellow',
                        15: 'gray_50',
                        16: 'gray_25'
                    }
                    
                    color_name = highlight_map.get(color_val, str(color_val))
                    rgb = self._highlight_enum_to_rgb(color_name)
                    if rgb:
                        colors.append(rgb)
                except:
                    pass
                    
            # Check run-level shading
            if hasattr(run, '_element'):
                shading = run._element.xpath('.//w:shd')
                if shading:
                    fill = shading[0].get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                    if fill and fill != 'auto':
                        try:
                            # Convert hex to RGB
                            if fill.startswith('#'):
                                fill = fill[1:]
                            r = int(fill[0:2], 16)
                            g = int(fill[2:4], 16)
                            b = int(fill[4:6], 16)
                            colors.append((r, g, b))
                        except:
                            pass
                            
        # Return the most common color if any
        if colors:
            # For simplicity, return the first color found
            # In production, might want to find the most frequent
            return colors[0]
            
        return None
        
    def _highlight_enum_to_rgb(self, color_name: str) -> Optional[Tuple[int, int, int]]:
        """Convert Word highlight color names to RGB values"""
        highlight_colors = {
            'yellow': (255, 255, 0),
            'bright_green': (0, 255, 0),
            'turquoise': (0, 255, 255),
            'pink': (255, 0, 255),
            'blue': (0, 0, 255),
            'red': (255, 0, 0),
            'dark_blue': (0, 0, 128),
            'teal': (0, 128, 128),
            'green': (0, 128, 0),
            'violet': (128, 0, 128),
            'dark_red': (128, 0, 0),
            'dark_yellow': (255, 140, 0),
            'gray_50': (128, 128, 128),
            'gray_25': (192, 192, 192),
            'black': (0, 0, 0),
        }
        
        # Clean color name
        color_name = color_name.replace('wdhighlight', '').replace('_', '').lower()
        
        return highlight_colors.get(color_name)
        
    def _map_color_to_label(self, color_rgb: Tuple[int, int, int]) -> Tuple[Optional[str], float]:
        """Map RGB color to label with confidence score"""
        best_label = None
        best_distance = float('inf')
        
        for color_name, color_info in self.color_mappings.get('color_to_label', {}).items():
            target_rgb = color_info['rgb']
            
            # Calculate Euclidean distance
            distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(color_rgb, target_rgb)))
            
            if distance < best_distance and distance <= self.tolerance:
                best_distance = distance
                best_label = color_info['label']
                
        # Calculate confidence (inverse of distance, normalized)
        confidence = 1.0 - (best_distance / 255.0) if best_label else 0.0
        
        return best_label, confidence
        
    def _is_title(self, paragraph) -> bool:
        """Check if paragraph is likely a title"""
        # Check if bold
        if paragraph.runs and all(run.bold for run in paragraph.runs if run.text.strip()):
            return True
            
        # Check if larger font size
        if paragraph.runs:
            avg_size = sum(run.font.size.pt for run in paragraph.runs if run.font.size) / len(paragraph.runs)
            if avg_size > 12:  # Assuming normal text is 11pt
                return True
                
        # Check paragraph style
        if paragraph.style and 'heading' in paragraph.style.name.lower():
            return True
            
        return False
        
    def _validate_sections(self, sections: List[ColoredSection]) -> List[ColoredSection]:
        """Validate and clean sections"""
        validated = []
        
        for section in sections:
            # Remove sections with very little text
            if len(section.text.strip()) < 10:
                logger.warning(f"Skipping section with label '{section.label}' - too short")
                continue
                
            # Ensure page numbers are valid
            if section.start_page < 1:
                section.start_page = 1
            if section.end_page < section.start_page:
                section.end_page = section.start_page
                
            validated.append(section)
            
        logger.info(f"Validated {len(validated)} sections from {len(sections)} raw sections")
        return validated
