#!/usr/bin/env python3
# Beispielskript zum Extrahieren von hervorgehobenem Text aus Word-Dokumenten

import os
import sys
from docx import Document
import json
from collections import defaultdict

def extract_highlighted_text(docx_path, output_path=None):
    """Extrahiert Text mit Hervorhebungen aus einer Word-Datei"""
    if not os.path.exists(docx_path):
        print(f"Fehler: Datei {docx_path} nicht gefunden.")
        return None
        
    # Farbzuordnung (Highlight-Werte in Word)
    color_map = {
        4: "findings",       # BRIGHT_GREEN
        15: "appendix",      # GRAY_50
        2: "evaluation",     # BLUE
        7: "introduction",   # YELLOW
        5: "response",       # PINK
        3: "wik",            # TURQUOISE
        14: "recommendations" # DARK_YELLOW
    }
    
    # Lade das Dokument
    doc = Document(docx_path)
    
    # Extrahiere Text und Farben
    results = defaultdict(list)
    
    for para in doc.paragraphs:
        for run in para.runs:
            if run.font.highlight_color:
                color_id = run.font.highlight_color
                label = color_map.get(color_id, f"unknown_{color_id}")
                text = run.text.strip()
                
                if text:
                    results[label].append(text)
    
    # Erstelle Zusammenfassung
    summary = {
        "document": os.path.basename(docx_path),
        "sections": {}
    }
    
    for label, texts in results.items():
        summary["sections"][label] = {
            "count": len(texts),
            "text": "\n".join(texts)
        }
    
    # Speichere Ergebnisse
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✅ Ergebnisse gespeichert in: {output_path}")
    
    return summary

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python extract_highlighted_text.py <pfad_zur_docx_datei> [ausgabepfad]")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    extract_highlighted_text(docx_path, output_path)
