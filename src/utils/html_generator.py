#!/usr/bin/env python3
"""
MetaSynthesizer HTML Report Generator
Generate HTML reports for extracted data
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json
from jinja2 import Template


class HTMLReportGenerator:
    """Generate HTML reports for extraction results"""
    
    def __init__(self):
        self.template = self._create_template()
    
    def _create_template(self) -> Template:
        """Create the HTML template"""
        template_str = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ document_name }} - Extraction Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header .meta { opacity: 0.9; font-size: 1.1em; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .stat-label { color: #666; font-size: 1.1em; }
        .section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }
        .risk-high { 
            background: #fee2e2; 
            color: #991b1b;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 500;
        }
        .risk-medium { 
            background: #fed7aa; 
            color: #92400e;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 500;
        }
        .risk-low { 
            background: #d1fae5; 
            color: #065f46;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 500;
        }
        .status-open { color: #dc2626; font-weight: 500; }
        .status-in_progress { color: #f59e0b; font-weight: 500; }
        .status-closed { color: #10b981; font-weight: 500; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        th {
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }
        tr:hover { background: #f9fafb; }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #9ca3af;
            font-style: italic;
        }
        .tag {
            display: inline-block;
            background: #e5e7eb;
            color: #374151;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875em;
            margin: 4px;
        }
        .timeline-item {
            position: relative;
            padding-left: 40px;
            margin-bottom: 20px;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: 10px;
            top: 5px;
            width: 10px;
            height: 10px;
            background: #667eea;
            border-radius: 50%;
        }
        .timeline-item::after {
            content: '';
            position: absolute;
            left: 14px;
            top: 15px;
            width: 2px;
            height: calc(100% + 10px);
            background: #e5e7eb;
        }
        .timeline-item:last-child::after { display: none; }
        .priority-high { color: #dc2626; font-weight: 600; }
        .priority-medium { color: #f59e0b; font-weight: 600; }
        .priority-low { color: #10b981; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ document_name }}</h1>
            <div class="meta">
                <div>Extracted: {{ extraction_date }}</div>
                <div>Method: {{ extraction_method }}</div>
                <div>Completeness: {{ completeness }}%</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ risk_count }}</div>
                <div class="stat-label">Risks Identified</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ recommendation_count }}</div>
                <div class="stat-label">Recommendations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ finding_count }}</div>
                <div class="stat-label">Key Findings</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ categories_filled }}/9</div>
                <div class="stat-label">Categories Filled</div>
            </div>
        </div>
        
        {% if risk_assessment %}
        <div class="section">
            <h2>🎯 Risk Assessment</h2>
            {% if risk_assessment.risk_level %}
            <p><strong>Overall Risk Level:</strong> 
                <span class="risk-{{ risk_assessment.risk_level }}">{{ risk_assessment.risk_level|upper }}</span>
            </p>
            {% endif %}
            {% if risk_assessment.risk_description %}
            <p><strong>Description:</strong> {{ risk_assessment.risk_description }}</p>
            {% endif %}
            {% if risk_assessment.mitigation_measures %}
            <p><strong>Mitigation Measures:</strong></p>
            <ul>
                {% for measure in risk_assessment.mitigation_measures %}
                <li>{{ measure }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            {% if risk_assessment.residual_risk %}
            <p><strong>Residual Risk:</strong> 
                <span class="risk-{{ risk_assessment.residual_risk }}">{{ risk_assessment.residual_risk|upper }}</span>
            </p>
            {% endif %}
        </div>
        {% endif %}
        
        {% if recommendations %}
        <div class="section">
            <h2>📋 Recommendations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Recommendation</th>
                        <th>Status</th>
                        <th>Responsible</th>
                        <th>Deadline</th>
                    </tr>
                </thead>
                <tbody>
                    {% for rec in recommendations %}
                    <tr>
                        <td>{{ rec.recommendation_text|default('—') }}</td>
                        <td><span class="status-{{ rec.status|default('unknown') }}">{{ rec.status|default('Unknown')|upper }}</span></td>
                        <td>{{ rec.responsible_entity|default('—') }}</td>
                        <td>{{ rec.deadline|default('—') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if not recommendations %}
            <div class="empty-state">No recommendations found</div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if findings %}
        <div class="section">
            <h2>🔍 Key Findings</h2>
            {% for finding in findings %}
            <div style="margin-bottom: 20px; padding: 15px; background: #f9fafb; border-radius: 8px;">
                {% if finding.finding_id %}
                <p><strong>ID:</strong> {{ finding.finding_id }}</p>
                {% endif %}
                {% if finding.main_finding %}
                <p><strong>Finding:</strong> {{ finding.main_finding }}</p>
                {% endif %}
                {% if finding.priority %}
                <p><strong>Priority:</strong> <span class="priority-{{ finding.priority }}">{{ finding.priority|upper }}</span></p>
                {% endif %}
                {% if finding.affected_areas %}
                <p><strong>Affected Areas:</strong></p>
                <div>
                    {% for area in finding.affected_areas %}
                    <span class="tag">{{ area }}</span>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
            {% if not findings %}
            <div class="empty-state">No findings recorded</div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if environmental_impact %}
        <div class="section">
            <h2>🌍 Environmental Impact</h2>
            {% if environmental_impact.impact_level %}
            <p><strong>Impact Level:</strong> {{ environmental_impact.impact_level|upper }}</p>
            {% endif %}
            {% if environmental_impact.environmental_risks %}
            <p><strong>Environmental Risks:</strong></p>
            <ul>
                {% for risk in environmental_impact.environmental_risks %}
                <li>{{ risk }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            {% if environmental_impact.mitigation_strategies %}
            <p><strong>Mitigation Strategies:</strong></p>
            <ul>
                {% for strategy in environmental_impact.mitigation_strategies %}
                <li>{{ strategy }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endif %}
        
        {% if timeline_analysis %}
        <div class="section">
            <h2>📅 Timeline Analysis</h2>
            {% if timeline_analysis.audit_period %}
            <p><strong>Audit Period:</strong> 
                {{ timeline_analysis.audit_period.start|default('Unknown') }} - 
                {{ timeline_analysis.audit_period.end|default('Unknown') }}
            </p>
            {% endif %}
            {% if timeline_analysis.key_dates %}
            <p><strong>Key Dates:</strong></p>
            <div class="timeline">
                {% for date in timeline_analysis.key_dates %}
                <div class="timeline-item">
                    <strong>{{ date.date|default('Unknown Date') }}</strong>: {{ date.event|default('No description') }}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if compliance_status %}
        <div class="section">
            <h2>✅ Compliance Status</h2>
            {% if compliance_status.overall_compliance %}
            <p><strong>Overall Status:</strong> {{ compliance_status.overall_compliance|upper }}</p>
            {% endif %}
            {% if compliance_status.compliance_items %}
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Status</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in compliance_status.compliance_items %}
                    <tr>
                        <td>{{ item.item|default('—') }}</td>
                        <td>{{ item.status|default('—') }}</td>
                        <td>{{ item.notes|default('—') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
        {% endif %}
        
        {% if audit_metadata %}
        <div class="section">
            <h2>📑 Audit Metadata</h2>
            <table>
                <tr>
                    <th>Audit Type</th>
                    <td>{{ audit_metadata.audit_type|default('—') }}</td>
                </tr>
                <tr>
                    <th>Department</th>
                    <td>{{ audit_metadata.department|default('—') }}</td>
                </tr>
                <tr>
                    <th>Auditor</th>
                    <td>{{ audit_metadata.auditor|default('—') }}</td>
                </tr>
                <tr>
                    <th>Period</th>
                    <td>{{ audit_metadata.audit_period|default('—') }}</td>
                </tr>
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>'''
        
        return Template(template_str)
    
    def generate_report(self, extraction: Dict[str, Any], output_path: Path) -> bool:
        """Generate HTML report for a single extraction"""
        try:
            # Prepare data for template
            categories = extraction.get("categories", {})
            
            # Count items
            risk_count = len(categories.get("risk_assessment", {}))
            recommendation_count = 1 if categories.get("recommendation_tracking") else 0
            finding_count = 1 if categories.get("finding_summary") else 0
            categories_filled = sum(1 for cat in categories.values() if cat)
            
            # Prepare template data
            template_data = {
                "document_name": extraction.get("document_id", "Unknown Document"),
                "extraction_date": extraction.get("extraction_timestamp", datetime.now().isoformat()),
                "extraction_method": extraction.get("extraction_method", "RAG Extraction"),
                "completeness": round(extraction.get("completeness_score", 0), 1),
                "risk_count": risk_count,
                "recommendation_count": recommendation_count,
                "finding_count": finding_count,
                "categories_filled": categories_filled,
                "risk_assessment": categories.get("risk_assessment"),
                "recommendations": [categories.get("recommendation_tracking")] if categories.get("recommendation_tracking") else [],
                "findings": [categories.get("finding_summary")] if categories.get("finding_summary") else [],
                "environmental_impact": categories.get("environmental_impact"),
                "timeline_analysis": categories.get("timeline_analysis"),
                "compliance_status": categories.get("compliance_status"),
                "audit_metadata": categories.get("audit_metadata")
            }
            
            # Generate HTML
            html_content = self.template.render(**template_data)
            
            # Write to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return False
    
    def generate_batch_reports(self, extractions: List[Dict[str, Any]], output_dir: Path) -> Dict[str, Any]:
        """Generate HTML reports for multiple extractions"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "total": len(extractions),
            "successful": 0,
            "failed": 0,
            "reports": []
        }
        
        for extraction in extractions:
            doc_id = extraction.get("document_id", "unknown")
            # Clean filename
            clean_id = "".join(c for c in doc_id if c.isalnum() or c in "._- ")
            output_path = output_dir / f"{clean_id}_report.html"
            
            if self.generate_report(extraction, output_path):
                results["successful"] += 1
                results["reports"].append(str(output_path))
            else:
                results["failed"] += 1
        
        # Generate index page
        self._generate_index_page(results["reports"], output_dir / "index.html")
        
        return results
    
    def _generate_index_page(self, report_paths: List[str], output_path: Path):
        """Generate an index page linking to all reports"""
        index_template = '''<!DOCTYPE html>
<html>
<head>
    <title>MetaSynthesizer Report Index</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #667eea; }
        .report-list { list-style: none; padding: 0; }
        .report-list li { 
            margin: 10px 0; 
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .report-list a { 
            color: #667eea; 
            text-decoration: none;
            font-weight: 500;
        }
        .report-list a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>MetaSynthesizer Extraction Reports</h1>
    <p>Generated: {{ timestamp }}</p>
    <ul class="report-list">
        {% for report in reports %}
        <li><a href="{{ report }}">{{ report }}</a></li>
        {% endfor %}
    </ul>
</body>
</html>'''
        
        template = Template(index_template)
        html = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reports=[Path(p).name for p in report_paths]
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


def main():
    """Test the HTML generator"""
    generator = HTMLReportGenerator()
    
    # Test with sample data
    test_extraction = {
        "document_id": "Test Document",
        "extraction_timestamp": datetime.now().isoformat(),
        "completeness_score": 75.5,
        "categories": {
            "risk_assessment": {
                "risk_level": "high",
                "risk_description": "Significant compliance risks identified",
                "mitigation_measures": ["Implement controls", "Regular monitoring"]
            },
            "finding_summary": {
                "main_finding": "Lack of proper documentation",
                "priority": "high",
                "finding_id": "FIND-001"
            }
        }
    }
    
    output_path = Path("test_report.html")
    if generator.generate_report(test_extraction, output_path):
        print(f"✅ Test report generated: {output_path}")
    else:
        print("❌ Failed to generate test report")


if __name__ == "__main__":
    main()
