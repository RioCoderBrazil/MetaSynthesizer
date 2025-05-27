#!/usr/bin/env python3
"""
MetaSynthesizer Chunk Visualizer
Generate interactive visualizations of document chunks
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class ChunkVisualizer:
    """Create visualizations for chunked documents"""
    
    def __init__(self, chunks_dir: Path = Path("02_chunked_data")):
        self.chunks_dir = Path(chunks_dir)
        self.chunk_data = self._load_all_chunks()
    
    def _load_all_chunks(self) -> List[Dict[str, Any]]:
        """Load all chunk data"""
        chunk_files = list(self.chunks_dir.glob("*_chunks.json"))
        all_chunks = []
        
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_chunks.append(data)
        
        return all_chunks
    
    def generate_overview_html(self, output_path: Path):
        """Generate comprehensive chunk overview HTML"""
        if not self.chunk_data:
            print("❌ No chunk data found")
            return
            
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Chunks per Document',
                'Chunk Size Distribution',
                'Color Distribution',
                'Section Distribution'
            ),
            specs=[
                [{"type": "bar"}, {"type": "histogram"}],
                [{"type": "pie"}, {"type": "bar"}]
            ]
        )
        
        # 1. Chunks per document
        doc_names = []
        chunk_counts = []
        for data in self.chunk_data:
            if isinstance(data, dict) and "document" in data:
                doc_name = data["document"].replace(".docx", "")[:20] + "..."
                doc_names.append(doc_name)
                chunk_counts.append(data["statistics"]["total_chunks"])
        
        fig.add_trace(
            go.Bar(x=doc_names, y=chunk_counts, name="Chunks"),
            row=1, col=1
        )
        
        # 2. Chunk size distribution
        all_sizes = []
        for data in self.chunk_data:
            if isinstance(data, dict) and "chunks" in data:
                for chunk in data["chunks"]:
                    all_sizes.append(len(chunk["text"]))
        
        fig.add_trace(
            go.Histogram(x=all_sizes, nbinsx=30, name="Size Distribution"),
            row=1, col=2
        )
        
        # 3. Color distribution
        color_counts = {}
        for data in self.chunk_data:
            if isinstance(data, dict) and "chunks" in data:
                for chunk in data["chunks"]:
                    colors = chunk.get("metadata", {}).get("colors", [])
                    for color in colors:
                        color_counts[color] = color_counts.get(color, 0) + 1
        
        if color_counts:
            fig.add_trace(
                go.Pie(
                    labels=list(color_counts.keys()),
                    values=list(color_counts.values()),
                    name="Colors"
                ),
                row=2, col=1
            )
        
        # 4. Section distribution
        section_counts = {}
        for data in self.chunk_data:
            if isinstance(data, dict) and "chunks" in data:
                for chunk in data["chunks"]:
                    section = chunk.get("metadata", {}).get("section", "Unknown")
                    section_counts[section] = section_counts.get(section, 0) + 1
        
        # Get top 10 sections
        top_sections = dict(sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        fig.add_trace(
            go.Bar(
                x=list(top_sections.values()),
                y=list(top_sections.keys()),
                orientation='h',
                name="Sections"
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="MetaSynthesizer Chunk Analysis Overview",
            height=800,
            showlegend=False
        )
        
        # Add detailed statistics table
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MetaSynthesizer Chunk Overview</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 MetaSynthesizer Chunk Analysis</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(self.chunk_data)}</div>
                <div class="stat-label">Documents Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(d['statistics']['total_chunks'] for d in self.chunk_data if isinstance(d, dict) and 'statistics' in d)}</div>
                <div class="stat-label">Total Chunks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{int(sum(all_sizes) / len(all_sizes)) if all_sizes else 0}</div>
                <div class="stat-label">Avg Chunk Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(color_counts)}</div>
                <div class="stat-label">Unique Colors</div>
            </div>
        </div>
        
        <div id="plotly-div"></div>
        
        <h2>📊 Document Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Document</th>
                    <th>Total Chunks</th>
                    <th>Avg Chunk Size</th>
                    <th>Colors Used</th>
                    <th>Primary Sections</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add document details
        for data in self.chunk_data:
            if isinstance(data, dict) and "document" in data and "statistics" in data and "chunks" in data:
                doc_name = data["document"].replace(".docx", "")
                total_chunks = data["statistics"]["total_chunks"]
                avg_size = int(data["statistics"]["avg_chunk_size"])
                
                # Get unique colors
                doc_colors = set()
                for chunk in data["chunks"]:
                    doc_colors.update(chunk.get("metadata", {}).get("colors", []))
                
                # Get top sections
                doc_sections = {}
                for chunk in data["chunks"]:
                    section = chunk.get("metadata", {}).get("section", "Unknown")
                    doc_sections[section] = doc_sections.get(section, 0) + 1
                top_doc_sections = sorted(doc_sections.items(), key=lambda x: x[1], reverse=True)[:3]
                sections_str = ", ".join([f"{s[0]} ({s[1]})" for s in top_doc_sections])
                
                html_content += f"""
                    <tr>
                        <td>{doc_name}</td>
                        <td>{total_chunks}</td>
                        <td>{avg_size}</td>
                        <td>{len(doc_colors)}</td>
                        <td>{sections_str}</td>
                    </tr>
"""
        
        html_content += f"""
            </tbody>
        </table>
    </div>
    
    <script>
        var plotlyDiv = document.getElementById('plotly-div');
        var data = {fig.to_json()};
        Plotly.newPlot(plotlyDiv, data.data, data.layout);
    </script>
</body>
</html>
"""
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Chunk visualization saved to: {output_path}")
    
    def generate_document_specific_viz(self, document_id: str, output_path: Path):
        """Generate visualization for a specific document"""
        # Find the document data
        doc_data = None
        for data in self.chunk_data:
            if isinstance(data, dict) and "document" in data and document_id in data["document"]:
                doc_data = data
                break
        
        if not doc_data:
            print(f"❌ Document {document_id} not found")
            return
        
        # Create visualization
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Chunk Sizes in Document Order',
                'Color Usage by Chunk'
            ),
            row_heights=[0.6, 0.4]
        )
        
        # Chunk sizes
        chunk_sizes = [len(chunk["text"]) for chunk in doc_data["chunks"]]
        chunk_indices = list(range(len(chunk_sizes)))
        
        fig.add_trace(
            go.Scatter(
                x=chunk_indices,
                y=chunk_sizes,
                mode='lines+markers',
                name='Chunk Size'
            ),
            row=1, col=1
        )
        
        # Color usage heatmap
        colors = ["yellow", "cyan", "lime", "pink", "orange"]
        color_matrix = []
        
        for chunk in doc_data["chunks"]:
            chunk_colors = chunk.get("metadata", {}).get("colors", [])
            row = [1 if color in chunk_colors else 0 for color in colors]
            color_matrix.append(row)
        
        fig.add_trace(
            go.Heatmap(
                z=list(zip(*color_matrix)),  # Transpose for better visualization
                y=colors,
                x=chunk_indices,
                colorscale=[[0, 'white'], [1, 'blue']],
                showscale=False
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title_text=f"Chunk Analysis: {document_id}",
            height=700
        )
        
        # Save as HTML
        fig.write_html(output_path)
        print(f"✅ Document visualization saved to: {output_path}")


def main():
    """Generate chunk visualizations"""
    visualizer = ChunkVisualizer()
    
    # Generate overview
    output_dir = Path("08_chunk_visualization")
    output_dir.mkdir(exist_ok=True)
    
    visualizer.generate_overview_html(output_dir / "chunk_overview.html")
    
    # Generate individual document visualizations
    for i, data in enumerate(visualizer.chunk_data[:5]):  # First 5 documents
        if isinstance(data, dict) and "document" in data:
            doc_id = data["document"].replace(".docx", "")
            visualizer.generate_document_specific_viz(
                doc_id,
                output_dir / f"{doc_id}_chunks.html"
            )


if __name__ == "__main__":
    main()
