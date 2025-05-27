# MetaSynthesizer v1.0 - Enhanced Human-in-the-Loop Document Analysis Pipeline
## 🚀 Powered by Claude Opus 4 - Next Generation Architecture

### 🎯 Project Overview

MetaSynthesizer ist die nächste Evolution der EFK-Dokumentenanalyse, die menschliche Expertise mit modernster KI kombiniert. Durch manuelle Farbmarkierung und eine intelligente 2-Pass-Architektur erreichen wir höchste Präzision bei der Extraktion strukturierter Daten aus komplexen Audit-Berichten.

### 🔍 Was wir verbessert haben (mit Claude Opus 4)

1. **Intelligentere Farberkennung**: Basierend auf 528 analysierten Sektionen
2. **Robuste 2-Pass-Architektur**: Trennung von Struktur und Semantik
3. **Integrierte Qualitätssicherung**: Tests nach jedem Pipeline-Schritt
4. **Visuelle Kontrolle**: Farbcodierte Chunk-Darstellung
5. **Präzises Zitat-Tracking**: Seitenzahlen für jede Referenz (p. XX)
6. **MCP-Integration**: Erweiterte Funktionalität durch Model Context Protocol

### ✨ Die MetaSynthesizer-Lösung

- **Human-in-the-Loop**: Experten färben Dokumente manuell für perfekte Genauigkeit
- **2-Pass-Processing**: 
  - Pass 1: Farberkennung → Hybrides Chunking → Vektorisierung
  - Pass 2: RAG-basierte Extraktion → 23-Kategorie-Schema → Validierung
- **Qdrant Vector Store**: Semantische Suche für präzise Informationsextraktion
- **Claude Opus 4**: Neueste Sprachmodell-Technologie für beste Ergebnisse
- **Kontinuierliche Validierung**: Eingebaute Tests garantieren Qualität

### 🎨 Farbschema für manuelle Markierung

| Farbe | RGB/Hex | Label | Deutsch | Französisch | Verwendung |
|-------|---------|-------|---------|-------------|------------|
| 🟦 TURQUOISE | #00FFFF | WIK | Wesentliches in Kürze | L'essentiel en bref | Zusammenfassung am Anfang |
| 🟨 YELLOW | #FFFF00 | Introduction | Einleitung, Auftrag, Ausgangslage | Introduction | Kapitel 1, Kontext |
| 🟩 BRIGHT_GREEN | #00FF00 | Findings | Feststellungen | Constatations | Hauptinhalt Kapitel 2+ |
| 🔵 BLUE | #0000FF | Evaluation | Beurteilung | Évaluation/Appréciation | Bewertende Abschnitte |
| 🟧 DARK_YELLOW | #FF8C00 | Recommendations | Empfehlungen | Recommandations | Mit Priorität |
| 🟪 PINK | #FF00FF | Response | Stellungnahme | Prise de position | Antworten der Geprüften |
| ⬜ GRAY | #808080 | Annex | Anhang | Annexe | Anhänge, Glossar, Abkürzungen |

### 📁 Projektstruktur

```
MetaSynthesizer/
├── 01_colored_reports/          # 20 manuell gefärbte DOCX-Berichte
├── 02_chunked_data/            # Pass 1: Chunk-Daten mit Labels (JSONL)
├── 03_vector_store/            # Qdrant Vektor-Datenbank
├── 04_extracted_data/          # Pass 2: Extrahierte 23 Kategorien (JSON)
├── 05_html_reports/            # Individuelle HTML-Tabellen
├── 06_validation_logs/         # Test- und Validierungsergebnisse
├── 07_meta_dashboard/          # Interaktives Meta-Dashboard
├── 08_chunk_visualization/     # Farbcodierte Chunk-Kontrolle
├── config/
│   ├── .env                    # API-Schlüssel und Einstellungen
│   ├── color_mappings.json     # Farb-zu-Label-Zuordnungen
│   ├── categories_schema.json  # 23-Kategorie-Definitionen
│   └── validation_rules.json   # Validierungsregeln
├── src/
│   ├── pass1/
│   │   ├── color_parser.py     # DOCX-Farbextraktion
│   │   ├── hybrid_chunker.py   # Intelligentes Chunking
│   │   └── vector_embedder.py  # Embedding-Generierung
│   ├── pass2/
│   │   ├── rag_extractor.py    # RAG-basierte Extraktion
│   │   ├── category_filler.py  # 23-Kategorie-Befüllung
│   │   └── analysis_generator.py # 40-Wort-Analysen
│   ├── validation/
│   │   ├── chunk_validator.py   # Chunk-Qualitätsprüfung
│   │   ├── data_validator.py    # Datenvalidierung
│   │   └── pipeline_tester.py   # Pipeline-Tests
│   ├── visualization/
│   │   ├── chunk_visualizer.py  # Farbcodierte Darstellung
│   │   ├── html_generator.py    # HTML-Tabellenerstellung
│   │   └── meta_dashboard.py    # Dashboard-Generator
│   └── utils/
│       ├── mcp_integration.py   # MCP-Server-Anbindung
│       └── page_tracker.py      # Seitenzahl-Tracking
├── tests/                       # Umfassende Testsuite
├── docker-compose.yml          # Qdrant + Services
├── requirements.txt            # Python-Abhängigkeiten
├── Makefile                    # Automatisierung
└── README.md                   # Dokumentation
```
