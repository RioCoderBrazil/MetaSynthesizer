"""
HTML Report Generator for CORRECT Categories
Generates reports matching the EFK Meta-Analyse format
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from jinja2 import Template

class CorrectHTMLReportGenerator:
    """Generate HTML reports with correct format"""
    
    def __init__(self):
        self.template = self._create_template()
    
    def _create_template(self) -> Template:
        """Create the HTML template matching the screenshots"""
        template_str = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>EFK Meta-Analyse: Bericht {{ doc_id }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #003366;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .section {
            background-color: white;
            margin-bottom: 20px;
            padding: 20px;
            border: 1px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section-title {
            background-color: #e6f2ff;
            color: #003366;
            padding: 10px;
            margin: -20px -20px 15px -20px;
            font-weight: bold;
            font-size: 16px;
            border-bottom: 2px solid #003366;
        }
        .category-row {
            display: flex;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 4px solid #0066cc;
        }
        .category-label {
            font-weight: bold;
            color: #003366;
            width: 30%;
            padding-right: 20px;
        }
        .category-value {
            flex: 1;
            color: #333;
        }
        .quote {
            font-style: italic;
            color: #2c3e50;
            line-height: 1.6;
        }
        .quote-item {
            margin-bottom: 10px;
            padding: 8px;
            background: #f0f0f0;
            border-left: 3px solid #FF6900;
            border-radius: 3px;
        }
        .quote-item:last-child {
            margin-bottom: 0;
        }
        .analysis-section {
            background-color: #f0f8ff;
            border: 2px solid #0066cc;
            padding: 20px;
            margin-top: 30px;
        }
        .analysis-title {
            color: #003366;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .revision-section {
            background-color: #fff9e6;
            border: 2px solid #ff9900;
            padding: 20px;
            margin-top: 20px;
        }
        .metadata {
            font-size: 12px;
            color: #666;
            text-align: right;
            margin-top: 20px;
        }
        .priority-1 { color: #d32f2f; font-weight: bold; }
        .priority-2 { color: #f57c00; font-weight: bold; }
        .priority-3 { color: #388e3c; }
        .status-O { background-color: #ffebee; }
        .status-B { background-color: #fff3e0; }
        .status-G { background-color: #e8f5e9; }
        .status-K { background-color: #f3e5f5; }
    </style>
</head>
<body>
    <div class="header">
        <h1>EFK Meta-Analyse: Bericht {{ doc_id }}</h1>
        <p>Bericht-Extraktion: {{ extraction_date }}</p>
    </div>

    <!-- Teil 1: Basisdaten -->
    <div class="section">
        <div class="section-title">Basisdaten</div>
        
        <div class="category-row">
            <div class="category-label">PA-Nummer:</div>
            <div class="category-value">{{ categories['PA-Nummer'] or 'Nicht gefunden' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Berichtstitel:</div>
            <div class="category-value">{{ categories['Berichtstitel'] or 'Nicht angegeben' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Berichtdatum:</div>
            <div class="category-value">{{ categories['Berichtdatum'] or 'Unbekannt' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Themenbericht:</div>
            <div class="category-value">{{ categories['Themenbericht'] or 'Keine Themen' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Berichtssprache:</div>
            <div class="category-value">{{ categories['Umwelt, Info B (Berichtsprache/Datei)'] or 'Nicht spezifiziert' }}</div>
        </div>
    </div>

    <!-- Teil 2: Kernerkenntnisse -->
    <div class="section">
        <div class="section-title">Kernerkenntnisse</div>
        
        <div class="category-row">
            <div class="category-label">Kernproblem:</div>
            <div class="category-value">{{ categories['Kernproblem'] or 'Kein Problem identifiziert' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Assoziierte Kosten:</div>
            <div class="category-value">{{ categories['Assoziierte Kosten'] or 'Keine Kosten erwähnt' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Risiken des Bundes:</div>
            <div class="category-value">{{ categories['Risiken des Bundes'] or 'Keine Risiken identifiziert' }}</div>
        </div>
    </div>

    <!-- Teil 3: Umweltfaktoren -->
    <div class="section">
        <div class="section-title">Umwelt-/Kontextfaktoren</div>
        
        {% if categories['Umwelt, Info A (Relevante Akteure)'] %}
        <div class="category-row">
            <div class="category-label">Relevante Akteure:</div>
            <div class="category-value quote">
                {% for quote in categories['Umwelt, Info A (Relevante Akteure)'].split('\n\n') %}
                    <div class="quote-item">{{ quote }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if categories['Umwelt, Info B (Berichtsprache/Datei)'] %}
        <div class="category-row">
            <div class="category-label">Berichtsprache/Datei:</div>
            <div class="category-value quote">
                {% for quote in categories['Umwelt, Info B (Berichtsprache/Datei)'].split('\n\n') %}
                    <div class="quote-item">{{ quote }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if categories['Umwelt, Info C (Bedenken/Monitoring)'] %}
        <div class="category-row">
            <div class="category-label">Bedenken/Monitoring:</div>
            <div class="category-value quote">
                {% for quote in categories['Umwelt, Info C (Bedenken/Monitoring)'].split('\n\n') %}
                    <div class="quote-item">{{ quote }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Teil 4: Umsetzung & Status -->
    <div class="section">
        <div class="section-title">Umsetzung & Status</div>
        
        {% if categories['Flankieigend A (kein Plan)'] %}
        <div class="category-row">
            <div class="category-label">Kein Plan:</div>
            <div class="category-value quote">
                {% for quote in categories['Flankieigend A (kein Plan)'].split('\n\n') %}
                    <div class="quote-item">{{ quote }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if categories['Flankieigend B (Plan unvollständig)'] %}
        <div class="category-row">
            <div class="category-label">Plan unvollständig:</div>
            <div class="category-value quote">
                {% for quote in categories['Flankieigend B (Plan unvollständig)'].split('\n\n') %}
                    <div class="quote-item">{{ quote }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if categories['Flankieigend C (in der Nachverfolgung)'] %}
        <div class="category-row">
            <div class="category-label">In Nachverfolgung:</div>
            <div class="category-value quote">
                {% for quote in categories['Flankieigend C (in der Nachverfolgung)'].split('\n\n') %}
                    <div class="quote-item">{{ quote }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Teil 5: Empfehlungen -->
    <div class="section">
        <div class="section-title">Empfehlungen</div>
        
        {% if categories['Empfehlungen'] %}
        <div class="category-row">
            <div class="category-label">EFK-Empfehlungen:</div>
            <div class="category-value quote">
                {% for rec in categories['Empfehlungen'].split('\n\n') %}
                    <div class="quote-item">{{ rec }}</div>
                {% endfor %}
            </div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Priorität:</div>
            <div class="category-value priority-{{ categories['Empfehlung Priorität'] or '1' }}">
                Stufe {{ categories['Empfehlung Priorität'] or '1' }}
            </div>
        </div>
        
        <div class="category-row status-{{ categories['Umsetzungsstratus Empfehlung'] or 'O' }}">
            <div class="category-label">Umsetzungsstatus:</div>
            <div class="category-value">
                {% set status_map = {'O': 'Offen', 'B': 'In Bearbeitung', 'G': 'Gelöst', 'K': 'Kein Plan'} %}
                {{ status_map[categories['Umsetzungsstratus Empfehlung'] or 'O'] }}
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Teil 6: Weitere Faktoren -->
    <div class="section">
        <div class="section-title">Weitere relevante Faktoren</div>
        
        {% if categories['Umsetzungsstatus'] %}
        <div class="category-row">
            <div class="category-label">Umsetzungsverzögerungen:</div>
            <div class="category-value quote">{{ categories['Umsetzungsstatus'] }}</div>
        </div>
        {% endif %}
        
        <div class="category-row">
            <div class="category-label">Verzögerungskosten:</div>
            <div class="category-value">{{ categories['Verdigungskosten'] or 'Nicht quantifiziert' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Selbsteinschätzung:</div>
            <div class="category-value">{{ categories['Selbsteinlassung'] or 'No' }}</div>
        </div>
        
        <div class="category-row">
            <div class="category-label">Relevante Anhänge:</div>
            <div class="category-value">{{ 'Ja' if categories['Anhänge relevant'] == 'Y' else 'Nein' }}</div>
        </div>
    </div>

    <!-- Neue Analyse-Sektion -->
    <div class="analysis-section">
        <div class="analysis-title">KI-generierte Analyse</div>
        <div>{{ analysis['analysis'] | replace('\n', '<br>') }}</div>
    </div>

    <!-- Revisionsleiter-Sektion -->
    <div class="revision-section">
        <div class="section-title">Verantwortlichkeit</div>
        <div class="category-row">
            <div class="category-label">Revisionsleiter:</div>
            <div class="category-value">{{ categories['Revisionsletter'] or 'Nicht angegeben' }}</div>
        </div>
    </div>

    <div class="metadata">
        <p>Erstellt am: {{ extraction_date }}<br>
        Extraktionsmethode: RAG mit Claude 3.5 Sonnet v2<br>
        Datenqualität: {{ data_completeness }}% vollständig</p>
    </div>
</body>
</html>
"""
        return Template(template_str)
    
    def generate_report(self, extraction: Dict[str, Any], output_path: Path) -> bool:
        """Generate HTML report for extraction"""
        try:
            # Calculate data completeness
            categories = extraction['categories']
            filled = sum(1 for v in categories.values() if v and v != 'NULL erfasst')
            total = len(categories)
            completeness = round(filled / total * 100, 1)
            
            # Prepare template data
            template_data = {
                'doc_id': extraction['document_id'],
                'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'categories': categories,
                'analysis': extraction.get('analysis', {'analysis': 'Keine Analyse verfügbar'}),
                'data_completeness': completeness
            }
            
            # Generate HTML
            html_content = self.template.render(**template_data)
            
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"Error generating report: {str(e)}")
            return False
    
    def generate_all_reports(self, extractions_file: Path, output_dir: Path):
        """Generate reports for all extractions"""
        with open(extractions_file, 'r', encoding='utf-8') as f:
            extractions = json.load(f)
        
        success_count = 0
        for extraction in extractions:
            doc_id = extraction['document_id']
            output_path = output_dir / f"{doc_id}_report.html"
            
            if self.generate_report(extraction, output_path):
                success_count += 1
                print(f"✓ Generated report for {doc_id}")
            else:
                print(f"✗ Failed to generate report for {doc_id}")
        
        print(f"\nGenerated {success_count}/{len(extractions)} reports")
        
        # Generate index page
        self._generate_index(extractions, output_dir)
    
    def _generate_index(self, extractions: List[Dict], output_dir: Path):
        """Generate index page"""
        index_template = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>EFK Meta-Analyse: Übersicht</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background-color: #003366; color: white; padding: 20px; margin-bottom: 20px; }
        .header h1 { margin: 0; }
        table { width: 100%; background-color: white; border-collapse: collapse; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background-color: #003366; color: white; padding: 12px; text-align: left; border-bottom: 2px solid #003366; }
        td { padding: 12px; border-bottom: 1px solid #eee; }
        tr:hover { background-color: #f5f5f5; }
        a { color: #003366; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .stats { background-color: white; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="header">
        <h1>EFK Meta-Analyse: Berichtsübersicht</h1>
        <p>{{ reports|length }} Berichte analysiert</p>
    </div>
    
    <div class="stats">
        <h2>Gesamtstatistik</h2>
        <p>Durchschnittliche Datenqualität: {{ avg_completeness }}%</p>
        <p>Berichte mit Empfehlungen: {{ reports_with_recommendations }}</p>
        <p>Offene Empfehlungen: {{ open_recommendations }}</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>PA-Nummer</th>
                <th>Berichtstitel</th>
                <th>Datum</th>
                <th>Kernproblem</th>
                <th>Priorität</th>
                <th>Status</th>
                <th>Report</th>
            </tr>
        </thead>
        <tbody>
            {% for report in reports %}
            <tr>
                <td>{{ report.categories['PA-Nummer'] or 'N/A' }}</td>
                <td>{{ report.categories['Berichtstitel'] or 'Kein Titel' }}</td>
                <td>{{ report.categories['Berichtdatum'] or '-' }}</td>
                <td>{{ (report.categories['Kernproblem'] or '')[:50] }}{% if report.categories['Kernproblem']|length > 50 %}...{% endif %}</td>
                <td>{{ report.categories['Empfehlung Priorität'] or '-' }}</td>
                <td>{{ {'O': 'Offen', 'B': 'In Bearbeitung', 'G': 'Gelöst', 'K': 'Kein Plan'}[report.categories['Umsetzungsstratus Empfehlung'] or 'O'] }}</td>
                <td><a href="{{ report.document_id }}_report.html">Öffnen</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""
        
        # Calculate statistics
        total_completeness = 0
        reports_with_rec = 0
        open_rec = 0
        
        for ext in extractions:
            cats = ext['categories']
            filled = sum(1 for v in cats.values() if v and v != 'NULL erfasst')
            total_completeness += filled / len(cats) * 100
            
            if cats.get('Empfehlungen'):
                reports_with_rec += 1
            
            if cats.get('Umsetzungsstratus Empfehlung') == 'O':
                open_rec += 1
        
        avg_completeness = round(total_completeness / len(extractions), 1)
        
        # Generate index
        template = Template(index_template)
        html = template.render(
            reports=extractions,
            avg_completeness=avg_completeness,
            reports_with_recommendations=reports_with_rec,
            open_recommendations=open_rec
        )
        
        with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Generated index page")

    def generate_index_page(self, extractions: List[Dict], output_path: Path) -> bool:
        """Generate an index page for all reports"""
        try:
            # Create index template
            index_template = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>EFK Meta-Analyse - Übersicht</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #003366;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        .summary {
            background-color: white;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        .summary-item {
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .summary-value {
            font-size: 36px;
            font-weight: bold;
            color: #003366;
        }
        .summary-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        .reports-table {
            background-color: white;
            padding: 20px;
            border: 1px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background-color: #003366;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: normal;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        a {
            color: #003366;
            text-decoration: none;
            font-weight: bold;
        }
        a:hover {
            text-decoration: underline;
        }
        .completeness-bar {
            width: 100px;
            height: 20px;
            background-color: #eee;
            position: relative;
            display: inline-block;
        }
        .completeness-fill {
            height: 100%;
            background-color: #28a745;
            position: absolute;
            left: 0;
            top: 0;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .status-open {
            background-color: #ffc107;
            color: #333;
        }
        .status-progress {
            background-color: #17a2b8;
            color: white;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>EFK Meta-Analyse - Übersicht aller Berichte</h1>
        <p>Generiert am {{ generation_date }}</p>
    </div>
    
    <div class="summary">
        <h2>Zusammenfassung</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-value">{{ total_documents }}</div>
                <div class="summary-label">Dokumente analysiert</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{{ overall_completeness }}%</div>
                <div class="summary-label">Gesamtvollständigkeit</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{{ filled_datapoints }}</div>
                <div class="summary-label">Datenpunkte gefüllt</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{{ recommendations_count }}</div>
                <div class="summary-label">Empfehlungen</div>
            </div>
        </div>
    </div>
    
    <div class="reports-table">
        <h2>Berichte</h2>
        <table>
            <thead>
                <tr>
                    <th>PA-Nummer</th>
                    <th>Berichtstitel</th>
                    <th>Vollständigkeit</th>
                    <th>Empfehlung Status</th>
                    <th>Priorität</th>
                    <th>Bericht</th>
                </tr>
            </thead>
            <tbody>
                {% for report in reports %}
                <tr>
                    <td>{{ report.categories.get('PA-Nummer', '-') }}</td>
                    <td>{{ report.categories.get('Berichtstitel', report.document_id[:50] + '...') }}</td>
                    <td>
                        <div class="completeness-bar">
                            <div class="completeness-fill" style="width: {{ report.completeness }}%"></div>
                        </div>
                        {{ report.completeness }}%
                    </td>
                    <td>
                        {% if report.categories.get('Umsetzungsstratus Empfehlung') == 'O' %}
                        <span class="status-badge status-open">Offen</span>
                        {% elif report.categories.get('Umsetzungsstratus Empfehlung') == 'I' %}
                        <span class="status-badge status-progress">In Bearbeitung</span>
                        {% else %}
                        -
                        {% endif %}
                    </td>
                    <td>{{ report.categories.get('Empfehlung Priorität', '-') }}</td>
                    <td><a href="{{ report.document_id }}_correct_report.html">Bericht anzeigen</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
            
            # Calculate statistics
            total_documents = len(extractions)
            total_categories = 23  # CORRECT schema has 23 categories
            filled_datapoints = 0
            total_datapoints = total_documents * total_categories
            recommendations_count = 0
            
            # Process reports and calculate completeness
            reports = []
            for extraction in extractions:
                doc_filled = 0
                categories = extraction.get('categories', {})
                
                for cat, value in categories.items():
                    if value and value not in ['NULL erfasst', 'NULL erfasst, falls nicht erwähnt']:
                        doc_filled += 1
                        filled_datapoints += 1
                
                if categories.get('Empfehlungen'):
                    recommendations_count += 1
                
                completeness = round((doc_filled / total_categories) * 100, 1)
                
                reports.append({
                    'document_id': extraction['document_id'],
                    'categories': categories,
                    'completeness': completeness
                })
            
            overall_completeness = round((filled_datapoints / total_datapoints) * 100, 1)
            
            # Render template
            template = Template(index_template)
            html = template.render(
                generation_date=datetime.now().strftime("%d.%m.%Y %H:%M"),
                total_documents=total_documents,
                overall_completeness=overall_completeness,
                filled_datapoints=filled_datapoints,
                recommendations_count=recommendations_count,
                reports=reports
            )
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return True
            
        except Exception as e:
            print(f"Error generating index page: {str(e)}")
            return False
