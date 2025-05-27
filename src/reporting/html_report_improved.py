"""
Improved HTML Report Generator for CORRECT Categories
Generates beautiful HTML reports with proper quote formatting and page numbers
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from jinja2 import Template

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedHTMLReportGenerator:
    """Generates improved HTML reports with better quote formatting"""
    
    def __init__(self):
        self.template = self._create_template()
        
    def _create_template(self) -> Template:
        """Create the improved HTML template"""
        template_str = '''
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EFK Prüfbericht - {{ document_id }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #1e3a5f;
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header .subtitle {
            margin-top: 10px;
            font-size: 1.2em;
            opacity: 0.9;
        }
        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .metadata-item {
            background-color: rgba(255,255,255,0.1);
            padding: 10px 15px;
            border-radius: 5px;
        }
        .metadata-label {
            font-weight: bold;
            display: block;
            margin-bottom: 5px;
        }
        .section {
            background-color: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #1e3a5f;
            margin-top: 0;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }
        .category {
            margin-bottom: 25px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #1e3a5f;
            border-radius: 5px;
        }
        .category-name {
            font-weight: bold;
            color: #1e3a5f;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .category-value {
            color: #444;
            white-space: pre-line;
        }
        .quote-section {
            background-color: #f0f4f8;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .quote-item {
            background-color: white;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #4a90e2;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .quote-text {
            font-style: italic;
            color: #555;
            margin-bottom: 5px;
        }
        .page-ref {
            color: #666;
            font-size: 0.9em;
            font-weight: bold;
        }
        .recommendation-item {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .recommendation-header {
            font-weight: bold;
            color: #856404;
            margin-bottom: 5px;
        }
        .analysis-section {
            background-color: #e8f5e9;
            padding: 25px;
            border-radius: 10px;
            margin-top: 30px;
        }
        .analysis-section h3 {
            color: #2e7d32;
            margin-top: 0;
        }
        .empty-value {
            color: #999;
            font-style: italic;
        }
        .timestamp {
            text-align: right;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
        }
        .priority-1 { border-left-color: #dc3545; }
        .priority-2 { border-left-color: #ffc107; }
        .priority-3 { border-left-color: #28a745; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ categories.get('Berichtstitel', 'EFK Prüfbericht') }}</h1>
        <div class="subtitle">{{ document_id }}</div>
        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">PA-Nummer:</span>
                {{ categories.get('PA-Nummer', '-') }}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Berichtdatum:</span>
                {{ categories.get('Berichtdatum', '-') }}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Extraktionsdatum:</span>
                {{ extraction_timestamp[:10] }}
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Kernthemen</h2>
        <div class="category">
            <div class="category-name">Themenbericht</div>
            <div class="category-value">{{ categories.get('Themenbericht', 'Nicht erfasst') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Kernproblem</div>
            <div class="category-value">{{ categories.get('Kernproblem', 'Nicht erfasst') }}</div>
        </div>
    </div>

    <div class="section">
        <h2>Kosten und Risiken</h2>
        <div class="category">
            <div class="category-name">Assoziierte Kosten</div>
            <div class="category-value">{{ categories.get('Assoziierte Kosten', 'NULL erfasst') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Risiken des Bundes</div>
            <div class="category-value">{{ categories.get('Risiken des Bundes', 'NULL erfasst') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Verdigungskosten</div>
            <div class="category-value">{{ categories.get('Verdigungskosten', 'NULL erfasst') }}</div>
        </div>
    </div>

    <div class="section">
        <h2>Umwelt-Informationen</h2>
        {% for info_key, info_name in [
            ('Umwelt, Info A (Relevante Akteure)', 'Relevante Akteure'),
            ('Umwelt, Info B (Berichtsprache/Datei)', 'Berichtsprache/Datei'),
            ('Umwelt, Info C (Bedenken/Monitoring)', 'Bedenken/Monitoring')
        ] %}
            <div class="quote-section">
                <h3>{{ info_name }}</h3>
                {% if categories.get(info_key) %}
                    {% for quote in categories.get(info_key, '').split('\\n\\n') if quote.strip() %}
                        <div class="quote-item">
                            {% if '(S.' in quote %}
                                {% set parts = quote.rsplit('(S.', 1) %}
                                <div class="quote-text">{{ parts[0].strip(' "') }}</div>
                                <div class="page-ref">(S.{{ parts[1] }}</div>
                            {% else %}
                                <div class="quote-text">{{ quote.strip(' "') }}</div>
                            {% endif %}
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-value">Keine Einträge gefunden</div>
                {% endif %}
            </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Flankierende Maßnahmen</h2>
        {% for flank_key, flank_name in [
            ('Flankieigend A (kein Plan)', 'Kein Plan vorhanden'),
            ('Flankieigend B (Plan unvollständig)', 'Plan unvollständig'),
            ('Flankieigend C (in der Nachverfolgung)', 'In der Nachverfolgung')
        ] %}
            <div class="quote-section">
                <h3>{{ flank_name }}</h3>
                {% if categories.get(flank_key) %}
                    {% for quote in categories.get(flank_key, '').split('\\n\\n') if quote.strip() %}
                        <div class="quote-item">
                            {% if '(S.' in quote %}
                                {% set parts = quote.rsplit('(S.', 1) %}
                                <div class="quote-text">{{ parts[0].strip(' "') }}</div>
                                <div class="page-ref">(S.{{ parts[1] }}</div>
                            {% else %}
                                <div class="quote-text">{{ quote.strip(' "') }}</div>
                            {% endif %}
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-value">Keine Einträge gefunden</div>
                {% endif %}
            </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Empfehlungen</h2>
        {% if categories.get('Empfehlungen') %}
            {% for rec in categories.get('Empfehlungen', '').split('\\n\\n') if rec.strip() %}
                {% if 'Empfehlung' in rec and 'Priorität' in rec %}
                    {% set priority = '1' %}
                    {% if 'Priorität 2' in rec %}
                        {% set priority = '2' %}
                    {% elif 'Priorität 3' in rec %}
                        {% set priority = '3' %}
                    {% endif %}
                    <div class="recommendation-item priority-{{ priority }}">
                        {% if '(S.' in rec %}
                            {% set parts = rec.rsplit('(S.', 1) %}
                            <div class="recommendation-header">
                                {{ parts[0].split(':')[0] if ':' in parts[0] else 'Empfehlung' }}
                            </div>
                            <div class="recommendation-text">
                                {{ parts[0].split(':', 1)[1].strip() if ':' in parts[0] else parts[0] }}
                            </div>
                            <div class="page-ref">(S.{{ parts[1] }}</div>
                        {% else %}
                            <div class="recommendation-text">{{ rec }}</div>
                        {% endif %}
                    </div>
                {% else %}
                    <div class="quote-item">
                        <div class="quote-text">{{ rec }}</div>
                    </div>
                {% endif %}
            {% endfor %}
        {% else %}
            <div class="empty-value">Keine Empfehlungen gefunden</div>
        {% endif %}
        
        <div class="category">
            <div class="category-name">Empfehlung Priorität</div>
            <div class="category-value">{{ categories.get('Empfehlung Priorität', '1') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Umsetzungsstatus Empfehlung</div>
            <div class="category-value">
                {% set status_map = {'O': 'Offen', 'B': 'In Bearbeitung', 'G': 'Gelöst', 'K': 'Kein Plan'} %}
                {{ status_map.get(categories.get('Umsetzungsstratus Empfehlung', 'O'), 'Offen') }}
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Weitere Informationen</h2>
        <div class="category">
            <div class="category-name">Umsetzungsstatus</div>
            <div class="category-value">{{ categories.get('Umsetzungsstatus', 'Nicht erfasst') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Unrelevante Faktoren</div>
            <div class="category-value">{{ categories.get('Unrelevante Faktoren', 'Nicht erfasst') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Anpassungen</div>
            <div class="category-value">{{ categories.get('Anpassungen', 'Nicht erfasst') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Selbsteinlassung</div>
            <div class="category-value">{{ categories.get('Selbsteinlassung', 'No') }}</div>
        </div>
        <div class="category">
            <div class="category-name">Anhänge relevant</div>
            <div class="category-value">
                {% set attach_map = {'Y': 'Yes', 'N': 'No'} %}
                {{ attach_map.get(categories.get('Anhänge relevant', 'N'), 'No') }}
            </div>
        </div>
        <div class="category">
            <div class="category-name">Revisionsletter</div>
            <div class="category-value">{{ categories.get('Revisionsletter', 'Nicht erfasst') }}</div>
        </div>
    </div>

    {% if analysis %}
    <div class="analysis-section">
        <h3>AI-Analyse</h3>
        <div style="white-space: pre-line;">{{ analysis.get('analysis', '') }}</div>
    </div>
    {% endif %}

    <div class="timestamp">
        Generiert am: {{ datetime.now().strftime('%d.%m.%Y %H:%M:%S') }}
    </div>
</body>
</html>
        '''
        return Template(template_str)
    
    def generate_report(self, extraction: Dict[str, Any], output_path: Path) -> bool:
        """Generate HTML report from extraction data"""
        try:
            # Render the template
            html_content = self.template.render(
                document_id=extraction.get('document_id', 'Unbekannt'),
                categories=extraction.get('categories', {}),
                extraction_timestamp=extraction.get('extraction_timestamp', ''),
                analysis=extraction.get('analysis', {}),
                datetime=datetime
            )
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML report: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return False
    
    def generate_all_reports(self, input_dir: Path, output_dir: Path, suffix: str = '_improved_extraction.json'):
        """Generate reports for all extractions"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        extraction_files = list(input_dir.glob(f'*{suffix}'))
        logger.info(f"Found {len(extraction_files)} extraction files")
        
        for extraction_file in extraction_files:
            try:
                # Load extraction data
                with open(extraction_file, 'r', encoding='utf-8') as f:
                    extraction_data = json.load(f)
                
                # Generate output filename
                doc_id = extraction_data.get('document_id', extraction_file.stem.replace(suffix.replace('.json', ''), ''))
                output_file = output_dir / f'{doc_id}_improved_report.html'
                
                # Generate report
                self.generate_report(extraction_data, output_file)
                
            except Exception as e:
                logger.error(f"Error processing {extraction_file}: {str(e)}")

def main():
    """Main entry point"""
    import sys
    
    generator = ImprovedHTMLReportGenerator()
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    input_dir = project_root / '03_extracted_data'
    output_dir = project_root / '04_html_reports_improved'
    
    # Generate all reports
    generator.generate_all_reports(input_dir, output_dir)
    
    logger.info(f"All reports generated in {output_dir}")

if __name__ == "__main__":
    main()
