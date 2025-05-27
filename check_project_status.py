"""
Check the current status of the MetaSynthesizer project
"""

import json
from pathlib import Path
from collections import defaultdict

def check_status():
    """Check project processing status"""
    
    print("=== MetaSynthesizer Projekt Status ===\n")
    
    # 1. Check colored documents
    colored_dir = Path('01_colored_reports')
    colored_docs = list(colored_dir.glob('*.docx'))
    print(f"📄 Gefärbte Dokumente: {len(colored_docs)}")
    
    # 2. Check chunked documents
    chunked_dir = Path('02_chunked_data')
    chunk_files = list(chunked_dir.glob('*_chunks.json'))
    print(f"🔪 Gechunkte Dokumente: {len(chunk_files)}")
    
    # Show which document was chunked
    if chunk_files:
        print("  ✓ Verarbeitet:")
        for cf in chunk_files:
            print(f"    - {cf.stem.replace('_chunks', '')}")
    
    # 3. Check Qdrant status
    try:
        import requests
        response = requests.get('http://localhost:6333/collections/metasynthesizer')
        if response.status_code == 200:
            data = response.json()
            points = data.get('result', {}).get('points_count', 0)
            print(f"\n🔢 Vektoren in Qdrant: {points}")
        else:
            print("\n⚠️  Qdrant nicht erreichbar")
    except:
        print("\n⚠️  Qdrant nicht erreichbar")
    
    # 4. Check extracted data
    extracted_dir = Path('03_extracted_data')
    extracted_files = list(extracted_dir.glob('*_extracted.json'))
    print(f"\n📊 Extrahierte Dokumente: {len(extracted_files)}")
    
    if extracted_files:
        print("  ✓ Extrahiert:")
        for ef in extracted_files:
            # Load and show completeness
            try:
                with open(ef, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats = data.get('statistics', {})
                    completeness = stats.get('completeness_percentage', 0)
                    print(f"    - {ef.stem.replace('_extracted', '')} ({completeness}% vollständig)")
            except:
                print(f"    - {ef.stem.replace('_extracted', '')}")
    
    # 5. Show next steps
    print("\n🚀 Nächste Schritte:")
    
    remaining_docs = len(colored_docs) - len(chunk_files)
    if remaining_docs > 0:
        print(f"  1. {remaining_docs} Dokumente müssen noch gechunkt werden")
        print(f"  2. Diese Chunks müssen vektorisiert werden")
        print(f"  3. Daten aus diesen Dokumenten extrahieren")
    else:
        print("  ✓ Alle Dokumente wurden verarbeitet!")
    
    print("\n📋 Projektstruktur:")
    print("  - Pass 1: Farbmarkierung ✓")
    print(f"  - Pass 2: Chunking & Extraktion ({len(chunk_files)}/{len(colored_docs)} Dokumente)")
    print("  - Pass 3: Validierung (ausstehend)")
    print("  - Pass 4: Meta-Dashboard (ausstehend)")
    
    # Show what we need to implement
    print("\n⚠️  Fehlende Komponenten:")
    missing_files = []
    
    if not Path('src/pass2/chunker.py').exists():
        missing_files.append("src/pass2/chunker.py - Dokumenten-Chunking")
    if not Path('src/pass2/vectorizer.py').exists():
        missing_files.append("src/pass2/vectorizer.py - Vektor-Speicherung")
    
    if missing_files:
        for mf in missing_files:
            print(f"  - {mf}")
    else:
        print("  ✓ Alle Kernkomponenten vorhanden")

if __name__ == "__main__":
    check_status()
