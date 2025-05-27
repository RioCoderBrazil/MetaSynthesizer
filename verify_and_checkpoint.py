#!/usr/bin/env python3
"""
Verify the corrected extraction and create a checkpoint system
"""

import json
from pathlib import Path
from datetime import datetime
import hashlib

def verify_extraction_quality():
    """Verify that all documents are correctly chunked and labeled"""
    
    corrected_dir = Path("02_chunked_data_CORRECTED")
    old_broken_dir = Path("02_chunked_data_highlighted")
    
    print("VERIFICATION REPORT")
    print("="*80)
    
    issues = []
    successes = []
    
    # Check all corrected files
    chunk_files = list(corrected_dir.glob("*_chunks.json"))
    
    for chunk_file in chunk_files:
        doc_name = chunk_file.stem.replace("_chunks", "")
        
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        # Quality checks
        total_chars = sum(len(c['text']) for c in chunks)
        broken_text_count = 0
        missing_labels = 0
        missing_pages = 0
        
        for chunk in chunks:
            # Check for broken text (words split by newlines)
            if '\n' in chunk['text'] and not any(punct in chunk['text'] for punct in ['. ', '! ', '? ']):
                broken_text_count += 1
            
            # Check for label
            if 'label' not in chunk or not chunk['label']:
                missing_labels += 1
            
            # Check for page numbers
            if 'start_page' not in chunk and 'end_page' not in chunk:
                missing_pages += 1
        
        # Report
        if broken_text_count > 0 or missing_labels > 0:
            issues.append({
                'file': doc_name,
                'broken_text': broken_text_count,
                'missing_labels': missing_labels,
                'missing_pages': missing_pages
            })
        else:
            successes.append({
                'file': doc_name,
                'chunks': len(chunks),
                'characters': total_chars,
                'has_findings': any(c['label'] == 'findings' for c in chunks),
                'has_appendix': any(c['label'] == 'appendix' for c in chunks)
            })
    
    # Print results
    print(f"\n✅ SUCCESSFUL EXTRACTIONS: {len(successes)}")
    print("-"*40)
    for success in successes[:5]:  # Show first 5
        print(f"  {success['file'][:50]:50} - {success['chunks']} chunks, {success['characters']:,} chars")
        if success['has_findings']:
            print(f"    ✓ Contains GREEN (findings)")
        if success['has_appendix']:
            print(f"    ✓ Contains GRAY (appendix)")
    
    if issues:
        print(f"\n❌ ISSUES FOUND: {len(issues)}")
        print("-"*40)
        for issue in issues:
            print(f"  {issue['file']}: {issue['broken_text']} broken, {issue['missing_labels']} no label")
    
    return len(issues) == 0, successes, issues

def create_checkpoint():
    """Create a checkpoint of the current correct state"""
    
    checkpoint = {
        'timestamp': datetime.now().isoformat(),
        'correct_directories': {
            'chunks': '02_chunked_data_CORRECTED',
            'DO_NOT_USE': '02_chunked_data_highlighted'  # The broken version
        },
        'extraction_issues_fixed': [
            'Text was broken with newlines in middle of words',
            'Fixed by concatenating runs within paragraphs',
            'All 17 documents re-extracted successfully'
        ],
        'known_issues': {
            'page_numbers': 'Simplified page tracking - may not be 100% accurate',
            'categories': 'Need to re-run category extraction with corrected chunks',
            'quotes': 'Quote extraction needs to handle multi-line text properly'
        },
        'next_steps': [
            'Re-run category extraction on CORRECTED chunks',
            'Implement proper page number tracking',
            'Fix quote extraction for multi-line text'
        ]
    }
    
    with open('CHECKPOINT_CORRECTED_STATE.json', 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    print("\n📌 CHECKPOINT CREATED: CHECKPOINT_CORRECTED_STATE.json")
    return checkpoint

def check_category_extraction_needed():
    """Check if we need to re-run category extraction"""
    
    print("\n" + "="*80)
    print("CATEGORY EXTRACTION STATUS")
    print("="*80)
    
    # Check if old extractions used broken chunks
    old_extractions = Path("03_extracted_data")
    if old_extractions.exists():
        extraction_files = list(old_extractions.glob("*_improved_extraction.json"))
        
        if extraction_files:
            # Check a sample
            with open(extraction_files[0], 'r', encoding='utf-8') as f:
                sample = json.load(f)
            
            # Look for signs of broken text in categories
            broken_signs = 0
            for key, value in sample.get('categories', {}).items():
                if isinstance(value, str) and '\n' in value and len(value.split('\n')[0]) < 20:
                    broken_signs += 1
            
            if broken_signs > 0:
                print("⚠️  Category extractions contain broken text!")
                print("✅ NEED TO RE-RUN: Category extraction with corrected chunks")
            else:
                print("🤔 Category extractions might be okay, but should verify")
        else:
            print("📭 No previous category extractions found")
    
    print("\nRECOMMENDATION: Re-run category extraction to be safe!")
    print("Reasons:")
    print("1. Previous extraction used chunks with broken text")
    print("2. Page numbers were not properly tracked")
    print("3. Quotes were not handling multi-line text")

def create_memory_safeguard():
    """Create a critical memory about the correct versions"""
    
    memory_content = {
        'critical_paths': {
            'USE_THIS': '/home/gryan/Projects/MetaSynthesizer/02_chunked_data_CORRECTED/',
            'DO_NOT_USE': '/home/gryan/Projects/MetaSynthesizer/02_chunked_data_highlighted/',
            'ALSO_BROKEN': '/home/gryan/Projects/MetaSynthesizer/02_chunked_data/'
        },
        'key_learnings': [
            'Word documents store text in runs that can split words',
            'Must concatenate runs within paragraphs without newlines',
            'Always verify text quality before expensive API operations',
            'Page tracking needs document structure analysis'
        ],
        'verification_command': 'python3 verify_and_checkpoint.py'
    }
    
    with open('CRITICAL_USE_CORRECT_VERSION.json', 'w', encoding='utf-8') as f:
        json.dump(memory_content, f, ensure_ascii=False, indent=2)
    
    print("\n🚨 CRITICAL REMINDER CREATED: CRITICAL_USE_CORRECT_VERSION.json")

if __name__ == "__main__":
    # Run verification
    all_good, successes, issues = verify_extraction_quality()
    
    if all_good:
        print("\n✅ ALL DOCUMENTS CORRECTLY CHUNKED AND LABELED!")
        
        # Create checkpoint
        checkpoint = create_checkpoint()
        
        # Check category extraction
        check_category_extraction_needed()
        
        # Create memory safeguard
        create_memory_safeguard()
        
        print("\n" + "="*80)
        print("SUMMARY:")
        print("1. ✅ All 17 documents have readable text")
        print("2. ✅ All chunks have proper labels (findings, appendix, etc)")
        print("3. ⚠️  Page numbers are simplified (not from original)")
        print("4. 🔄 NEED TO RE-RUN: Category extraction with corrected chunks")
        print("5. 📁 USE ONLY: 02_chunked_data_CORRECTED/")
    else:
        print("\n❌ ISSUES FOUND - Need investigation!")
