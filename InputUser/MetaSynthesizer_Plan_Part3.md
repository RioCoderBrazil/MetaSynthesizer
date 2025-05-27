# MetaSynthesizer Plan - Teil 3: 2-Pass-Architektur & Implementation

## 🔄 Pass 1: Farberkennung → Chunking → Vektorisierung

### 1.1 ColorParser (color_parser.py)
**Aufgabe**: DOCX-Farben extrahieren und Labels zuweisen

**Claude Opus 4 Verbesserungen**:
- Robuste Farberkennung mit Toleranzbereich
- Multi-Format-Unterstützung (verschiedene Highlight-Methoden)
- Titel-Text-Integration garantiert
- Seitenzahl-Tracking von Anfang an

```python
class ColorParser:
    def __init__(self, color_config_path: str):
        self.color_mappings = self._load_color_mappings(color_config_path)
        self.page_tracker = PageTracker()
        
    def parse_document(self, docx_path: str) -> List[ColoredSection]:
        """
        Extrahiert gefärbte Sektionen mit:
        - Label (wik, introduction, findings, etc.)
        - Text (Titel + Inhalt kombiniert)
        - Seitenzahlen (start_page, end_page)
        - Konfidenz-Score
        """
        sections = []
        current_section = None
        
        for paragraph in document.paragraphs:
            color = self._extract_color(paragraph)
            label = self._map_color_to_label(color)
            page_num = self.page_tracker.get_current_page(paragraph)
            
            # KRITISCH: Titel mit Text verbinden
            if self._is_title(paragraph) and current_section:
                current_section.add_title(paragraph.text)
            else:
                # Neue Sektion oder Fortsetzung
                ...
                
        return self._validate_sections(sections)
```

### 1.2 HybridChunker (hybrid_chunker.py)
**Aufgabe**: Intelligentes Chunking innerhalb Label-Grenzen

**Claude Opus 4 Verbesserungen**:
- Semantische Grenzen respektieren
- Keine Chunk-Splits mitten im Satz
- Optimale Chunk-Größe (300-500 Tokens)
- Metadaten-Erhaltung

```python
class HybridChunker:
    def __init__(self, max_tokens: int = 500, min_tokens: int = 50):
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
        
    def chunk_sections(self, sections: List[ColoredSection]) -> List[Chunk]:
        """
        Erstellt Chunks mit:
        - Respekt vor Label-Grenzen
        - Semantischer Kohärenz
        - Seitenzahl-Metadaten
        - Referenz zur Original-Sektion
        """
        chunks = []
        
        for section in sections:
            if self._needs_splitting(section):
                # Intelligentes Splitting
                sub_chunks = self._split_intelligently(section)
            else:
                # Kleine Sektionen bleiben ganz
                sub_chunks = [section.to_chunk()]
                
            chunks.extend(sub_chunks)
            
        return self._add_context_overlap(chunks)
```

### 1.3 VectorEmbedder (vector_embedder.py)
**Aufgabe**: Embedding-Generierung und Qdrant-Speicherung

**Claude Opus 4 Verbesserungen**:
- Batch-Processing für Effizienz
- Label-spezifische Embeddings
- Metadata-reiche Vektoren
- Automatische Collection-Erstellung

```python
class VectorEmbedder:
    def __init__(self, qdrant_host: str, collection_name: str):
        self.encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.qdrant = QdrantClient(host=qdrant_host, port=6333)
        self._ensure_collection(collection_name)
        
    def embed_and_store(self, chunks: List[Chunk], doc_id: str) -> bool:
        """
        Speichert Chunks in Qdrant mit:
        - Vektor-Embeddings
        - Reichhaltigen Metadaten
        - Label-Information
        - Seitenzahlen
        """
        embeddings = self.encoder.encode([c.text for c in chunks], batch_size=32)
        
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=f"{doc_id}_{idx}",
                vector=embedding.tolist(),
                payload={
                    "text": chunk.text,
                    "label": chunk.label,
                    "start_page": chunk.start_page,
                    "end_page": chunk.end_page,
                    "doc_id": doc_id,
                    "chunk_idx": idx
                }
            )
            points.append(point)
            
        return self.qdrant.upsert(collection_name=self.collection_name, points=points)
```

## 🎯 Pass 2: RAG-basierte Extraktion → 23 Kategorien

### 2.1 RAGExtractor (rag_extractor.py)
**Aufgabe**: Semantische Suche und Kontext-Retrieval

**Claude Opus 4 Verbesserungen**:
- Multi-Query-Expansion
- Label-aware Retrieval
- Kontext-Fenster-Optimierung
- Relevanz-Scoring

```python
class RAGExtractor:
    def __init__(self, qdrant_client: QdrantClient, llm_client: Anthropic):
        self.qdrant = qdrant_client
        self.llm = llm_client
        self.encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        
    def extract_for_category(self, category: str, doc_id: str) -> CategoryData:
        """
        Extrahiert Daten für eine Kategorie mittels:
        - Intelligenter Query-Formulierung
        - Semantischer Suche
        - LLM-basierter Extraktion
        - Seitenzahl-Preservation
        """
        # Query-Expansion für bessere Abdeckung
        queries = self._expand_query(category)
        
        # Multi-Query Retrieval
        all_chunks = []
        for query in queries:
            chunks = self._retrieve_chunks(query, doc_id, limit=10)
            all_chunks.extend(chunks)
            
        # Deduplizierung und Ranking
        ranked_chunks = self._rank_and_deduplicate(all_chunks)
        
        # LLM-Extraktion mit Claude Opus 4
        extracted_data = self._extract_with_llm(category, ranked_chunks)
        
        return extracted_data
```

### 2.2 CategoryFiller (category_filler.py)
**Aufgabe**: 23-Kategorie-Schema befüllen

**Claude Opus 4 Verbesserungen**:
- Parallele Extraktion
- Validierung jeder Kategorie
- 40-Wort-Analysen generieren
- Zitat-Formatting mit Seitenzahlen

```python
class CategoryFiller:
    def __init__(self, schema_path: str, rag_extractor: RAGExtractor):
        self.schema = self._load_schema(schema_path)
        self.extractor = rag_extractor
        
    def fill_all_categories(self, doc_id: str) -> Dict[str, Any]:
        """
        Befüllt alle 23 Kategorien mit:
        - Extrahierten Texten
        - 40-Wort-Analysen
        - Seitenzahl-Referenzen (p. XX)
        - Validierung
        """
        results = {}
        
        # Parallele Verarbeitung für Effizienz
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for category in self.schema['categories']:
                future = executor.submit(self._process_category, category, doc_id)
                futures[future] = category
                
            for future in as_completed(futures):
                category = futures[future]
                result = future.result()
                results[category['id']] = self._format_result(result)
                
        return self._validate_completeness(results)
        
    def _format_result(self, raw_result: CategoryData) -> Dict:
        """Formatiert mit Seitenzahlen"""
        return {
            "extracted_text": raw_result.text,
            "analysis": self._generate_analysis(raw_result.text),  # ≤40 Wörter
            "page_references": [f"p. {p}" for p in raw_result.pages],
            "confidence": raw_result.confidence
        }
```

### 2.3 AnalysisGenerator (analysis_generator.py)
**Aufgabe**: Intelligente 40-Wort-Analysen

**Claude Opus 4 Verbesserungen**:
- Kontext-bewusste Zusammenfassungen
- Mehrsprachige Unterstützung
- Qualitäts-Scoring
- Iterative Verbesserung

```python
class AnalysisGenerator:
    def __init__(self, llm_client: Anthropic):
        self.llm = llm_client
        
    def generate_analysis(self, text: str, category: str, lang: str = 'de') -> str:
        """
        Generiert prägnante Analyse:
        - Max. 40 Wörter
        - Kategorie-spezifisch
        - Mehrsprachig
        - Hochwertig
        """
        prompt = self._build_analysis_prompt(text, category, lang)
        
        response = self.llm.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3
        )
        
        analysis = response.content[0].text
        
        # Validierung und ggf. Kürzung
        return self._ensure_word_limit(analysis, 40)
```
