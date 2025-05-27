# MetaSynthesizer Plan - Teil 2: Installation & Konfiguration

## ✅ Vorbereitung der gefärbten Dokumente

### KRITISCH: Diese Regeln MÜSSEN befolgt werden!

- Alle Dokumente müssen manuell mit Word's Highlight-Funktion farbmarkiert sein
- Jede Farbe entspricht einer spezifischen Kategorie (siehe README.md)
- Vollständige Absätze müssen markiert werden (nicht einzelne Wörter oder Sätze)
- Dokumente müssen als DOCX gespeichert sein

### ✅ Installation der benötigten Python-Pakete

```bash
# Erstelle eine virtuelle Umgebung
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
# venv\Scripts\activate  # Windows

# Installiere Abhängigkeiten
pip install python-docx tqdm colorama pandas numpy matplotlib seaborn
pip install sentence-transformers qdrant-client python-dotenv
pip install pygithub torch
```

### ✅ Verzeichnisstruktur vorbereiten

```bash
mkdir -p 01_colored_reports
mkdir -p 02_chunked_data
mkdir -p 03_extracted_data
mkdir -p 04_html_reports
mkdir -p 05_visualizations
```

### ✅ Konfigurationsdateien einrichten

```bash
# Erstelle config-Verzeichnis
mkdir -p config

# Erstelle color_mappings.json
cat > config/color_mappings.json << 'EOF'
{
  "yellow": "introduction",
  "green": "findings",
  "blue": "evaluation",
  "dark_yellow": "recommendations",
  "pink": "response",
  "gray": "appendix",
  "cyan": "wik"
}
EOF

# Erstelle categories_schema.json
cat > config/categories_schema.json << 'EOF'
{
  "categories": [
    {
      "id": "introduction",
      "name": "Einleitung",
      "color": "yellow",
      "key_patterns": ["Einleitung", "Hintergrund", "Prüfungsauftrag"]
    },
    {
      "id": "findings",
      "name": "Feststellungen",
      "color": "green",
      "key_patterns": ["Feststellungen", "Sachverhalt", "Ist-Zustand"]
    },
    {
      "id": "evaluation",
      "name": "Beurteilung",
      "color": "blue",
      "key_patterns": ["Beurteilung", "Bewertung", "Analyse"]
    },
    {
      "id": "recommendations",
      "name": "Empfehlungen",
      "color": "dark_yellow",
      "key_patterns": ["Empfehlungen", "Vorschläge", "Handlungsvorschläge"]
    },
    {
      "id": "response",
      "name": "Stellungnahme",
      "color": "pink",
      "key_patterns": ["Stellungnahme", "Antwort", "Entgegnung"]
    },
    {
      "id": "appendix",
      "name": "Anhang",
      "color": "gray",
      "key_patterns": ["Anhang", "Anlagen", "Zusatzinformationen"]
    },
    {
      "id": "wik",
      "name": "Wesentliches in Kürze",
      "color": "cyan",
      "key_patterns": ["Wesentliches in Kürze", "WIK", "Zusammenfassung"]
    }
  ]
}
EOF
```

### ✅ Konfiguration (.env)
```bash
# Erstelle config/.env
mkdir -p config
cat > config/.env << 'EOF'
# API Provider (anthropic oder openai)
API_TYPE=anthropic

# Claude Opus 4 / Sonnet 4 Keys
ANTHROPIC_API_KEY=sk-ant-***********************************

# OpenAI (falls benötigt)
OPENAI_API_KEY=sk-***********************************

# GitHub Token
GITHUB_TOKEN=github_pat_***********************************

# Model Selection (Claude Opus 4)
MODEL_NAME=claude-3-opus-20240229
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Qdrant Settings
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=efk_meta_chunks

# Processing Settings
CHUNK_MAX_TOKENS=500
CHUNK_MIN_TOKENS=50
CHUNK_OVERLAP=0
EOF
```

## ✅ Qdrant Vector DB einrichten (für die Vektorisierung)

```bash
# Mit Docker (empfohlen)
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant

# Alternativ: Installation ohne Docker
# pip install qdrant-client
```
