# MetaSynthesizer Plan - Teil 4: Visualisierung, Output & Testing

## 🎨 Visualisierung & Output-Generierung

### 4.1 ChunkVisualizer (chunk_visualizer.py)
**Aufgabe**: Farbcodierte Chunk-Darstellung zur Qualitätskontrolle

**Claude Opus 4 Features**:
- Interaktive HTML-Visualisierung
- Original-Farben beibehalten
- Chunk-Grenzen anzeigen
- Statistiken pro Label

```python
class ChunkVisualizer:
    def __init__(self):
        self.color_map = {
            'wik': '#00FFFF',
            'introduction': '#FFFF00',
            'findings': '#00FF00',
            'evaluation': '#0000FF',
            'recommendations': '#FF8C00',
            'response': '#FF00FF',
            'annex': '#808080'
        }
        
    def visualize_chunks(self, chunks: List[Chunk], output_path: str):
        """
        Erstellt HTML-Visualisierung mit:
        - Farbcodierten Chunks
        - Hover-Informationen
        - Label-Statistiken
        - Seitenzahl-Anzeige
        """
        html_content = self._generate_html_header()
        
        # Chunk-Darstellung
        for chunk in chunks:
            html_content += self._render_chunk(chunk)
            
        # Statistiken
        html_content += self._generate_statistics(chunks)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
```

### 4.2 HTMLTableGenerator (html_generator.py)
**Aufgabe**: Professionelle HTML-Tabellen für 23 Kategorien

**Claude Opus 4 Features**:
- Responsive Design
- Sortierbare Spalten
- Export-Funktionen
- Mehrsprachige Headers

```python
class HTMLTableGenerator:
    def __init__(self, template_path: str):
        self.template = self._load_template(template_path)
        
    def generate_report(self, category_data: Dict, doc_info: Dict) -> str:
        """
        Erstellt HTML-Report mit:
        - 23-Kategorie-Tabelle
        - Analyse-Spalte (≤40 Wörter)
        - Seitenzahl-Referenzen
        - Export-Buttons (Excel, PDF)
        """
        html = self.template.render(
            doc_title=doc_info['title'],
            doc_number=doc_info['number'],
            categories=self._format_categories(category_data),
            generation_date=datetime.now().strftime('%d.%m.%Y'),
            statistics=self._calculate_statistics(category_data)
        )
        
        return self._add_interactivity(html)
```

### 4.3 MetaDashboard (meta_dashboard.py)
**Aufgabe**: Interaktives Dashboard für alle 20 Berichte

**Claude Opus 4 Features**:
- Streamlit-basiert
- Vergleichsanalysen
- Trend-Visualisierungen
- Such- und Filterfunktionen

```python
class MetaDashboard:
    def __init__(self, data_path: str):
        self.reports = self._load_all_reports(data_path)
        
    def create_dashboard(self):
        """
        Streamlit-Dashboard mit:
        - Übersicht aller 20 Berichte
        - Kategorie-Vergleiche
        - Empfehlungs-Tracking
        - Export-Funktionen
        """
        st.set_page_config(page_title="MetaSynthesizer Dashboard", layout="wide")
        
        # Sidebar
        with st.sidebar:
            selected_report = st.selectbox("Bericht wählen", self.reports.keys())
            category_filter = st.multiselect("Kategorien", self.get_all_categories())
            
        # Hauptbereich
        if selected_report:
            self._display_report_summary(selected_report)
            self._display_category_analysis(selected_report, category_filter)
            
        # Vergleichsansicht
        if st.checkbox("Vergleichsmodus"):
            self._display_comparison_view()
```

## 🧪 Integrierte Testing & Validierung

### 5.1 ChunkValidator (chunk_validator.py)
**Tests nach Pass 1**:
- Alle Farben korrekt erkannt?
- Titel mit Text verbunden?
- Keine verwaisten Chunks?
- Seitenzahlen vorhanden?

```python
class ChunkValidator:
    def validate_chunks(self, chunks: List[Chunk], original_doc: str) -> ValidationReport:
        """
        Validiert:
        - Label-Verteilung (mind. WIK, Findings, Recommendations)
        - Chunk-Größen (50-500 Tokens)
        - Keine Überlappungen
        - Vollständigkeit
        """
        tests = [
            self._test_label_distribution,
            self._test_chunk_sizes,
            self._test_no_overlaps,
            self._test_completeness,
            self._test_page_numbers
        ]
        
        results = []
        for test in tests:
            result = test(chunks, original_doc)
            results.append(result)
            
        return ValidationReport(results)
```

### 5.2 DataValidator (data_validator.py)
**Tests nach Pass 2**:
- Alle 23 Kategorien befüllt?
- Analysen ≤40 Wörter?
- Seitenzahlen im Format "p. XX"?
- Keine leeren Kategorien?

```python
class DataValidator:
    def validate_extraction(self, extracted_data: Dict) -> ValidationReport:
        """
        Validiert:
        - Kategorie-Vollständigkeit
        - Analyse-Wortlimit
        - Seitenzahl-Format
        - Datenqualität
        """
        validations = {
            'completeness': self._check_all_categories_filled(extracted_data),
            'analysis_length': self._check_analysis_word_count(extracted_data),
            'page_format': self._check_page_reference_format(extracted_data),
            'data_quality': self._check_data_quality(extracted_data)
        }
        
        return self._generate_report(validations)
```

### 5.3 PipelineTester (pipeline_tester.py)
**End-to-End Tests**:
- Kompletter Durchlauf mit Testdokument
- Performance-Messung
- Fehlerbehandlung
- Qualitäts-Scoring

```python
class PipelineTester:
    def run_full_test(self, test_doc_path: str) -> TestReport:
        """
        Testet gesamte Pipeline:
        - Pass 1: Chunking
        - Pass 2: Extraktion
        - Visualisierung
        - Output-Generierung
        """
        start_time = time.time()
        
        try:
            # Pass 1
            chunks = self.run_pass1(test_doc_path)
            pass1_validation = self.validate_pass1(chunks)
            
            # Pass 2
            extracted = self.run_pass2(chunks)
            pass2_validation = self.validate_pass2(extracted)
            
            # Output
            outputs = self.generate_outputs(extracted)
            output_validation = self.validate_outputs(outputs)
            
            # Performance
            duration = time.time() - start_time
            
            return TestReport(
                success=True,
                duration=duration,
                validations={
                    'pass1': pass1_validation,
                    'pass2': pass2_validation,
                    'output': output_validation
                }
            )
            
        except Exception as e:
            return TestReport(success=False, error=str(e))
```

## 📊 Output-Formate

### JSON-Output (pro Bericht)
```json
{
  "doc_id": "22723BE",
  "title": "Prüfung der Investitionsplanung",
  "processing_date": "2024-01-15",
  "categories": {
    "pruefungsziel": {
      "extracted_text": "Die EFK prüfte...",
      "analysis": "Überprüfung der SBB-Investitionsplanung bezüglich Substanzerhalt und Priorisierung der Infrastrukturprojekte",
      "page_references": ["p. 8", "p. 9"],
      "confidence": 0.95
    },
    // ... weitere 22 Kategorien
  },
  "metadata": {
    "total_chunks": 118,
    "label_distribution": {
      "wik": 12,
      "introduction": 15,
      "findings": 45,
      "evaluation": 20,
      "recommendations": 15,
      "response": 11
    },
    "processing_time": 45.2
  }
}
```

### HTML-Tabelle (pro Bericht)
- Responsive 23-Kategorie-Tabelle
- Sortier- und Suchfunktionen
- Export zu Excel/PDF
- Druckoptimiert

### Meta-Dashboard (alle Berichte)
- Interaktive Übersicht
- Vergleichsanalysen
- Trend-Visualisierungen
- Batch-Export
