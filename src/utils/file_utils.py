"""
File utility functions
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import hashlib


def save_json(data: Any, directory: str, filename: str) -> str:
    """
    Save data as JSON file
    
    Args:
        data: Data to save
        directory: Directory path
        filename: Filename
        
    Returns:
        Full path to saved file
    """
    # Ensure directory exists
    Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create full path
    filepath = os.path.join(directory, filename)
    
    # Save data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath


class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def ensure_directory(path: str) -> Path:
        """Ensure directory exists, create if not"""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
        
    @staticmethod
    def get_doc_id(file_path: str) -> str:
        """Generate consistent document ID from file path"""
        file_name = Path(file_path).stem
        # Remove common prefixes/suffixes
        doc_id = file_name.replace('colored_', '').replace('_colored', '')
        return doc_id
        
    @staticmethod
    def save_json(data: Any, file_path: str, indent: int = 2):
        """Save data as JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            
    @staticmethod
    def load_json(file_path: str) -> Any:
        """Load JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    @staticmethod
    def list_docx_files(directory: str) -> List[str]:
        """List all DOCX files in directory"""
        dir_path = Path(directory)
        return sorted([str(f) for f in dir_path.glob('*.docx')])
        
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    @staticmethod
    def get_output_paths(doc_id: str, base_dir: str = ".") -> Dict[str, Path]:
        """Get standard output paths for a document"""
        base = Path(base_dir)
        
        return {
            'chunks': base / '02_chunked_data' / f'{doc_id}_chunks.json',
            'vectors': base / '03_vector_store' / f'{doc_id}_vectors.json',
            'extracted': base / '04_extracted_data' / f'{doc_id}_extracted.json',
            'html': base / '05_html_reports' / f'{doc_id}_report.html',
            'validation': base / '06_validation_logs' / f'{doc_id}_validation.log',
            'visualization': base / '08_chunk_visualization' / f'{doc_id}_chunks.html'
        }
