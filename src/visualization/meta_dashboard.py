#!/usr/bin/env python3
"""
MetaSynthesizer Meta Dashboard
Interactive dashboard for visualizing extraction results across all documents
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np


class MetaDashboard:
    """Interactive dashboard for MetaSynthesizer results"""
    
    def __init__(self, data_dir: Path = Path("03_extracted_data")):
        self.data_dir = Path(data_dir)
        self.extractions = self._load_all_extractions()
        
    def _load_all_extractions(self) -> List[Dict[str, Any]]:
        """Load all extraction results"""
        extractions = []
        
        # Try to load combined file first
        combined_file = self.data_dir / "all_extractions.json"
        if combined_file.exists():
            with open(combined_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Otherwise load individual files
        for json_file in self.data_dir.glob("*_extracted.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                extractions.append(json.load(f))
        
        return extractions
    
    def run(self):
        """Run the Streamlit dashboard"""
        st.set_page_config(
            page_title="MetaSynthesizer Dashboard",
            page_icon="🔍",
            layout="wide"
        )
        
        st.title("🔍 MetaSynthesizer Meta Dashboard")
        st.markdown("**Comprehensive view of all extracted audit data**")
        
        # Sidebar for filtering
        with st.sidebar:
            st.header("🎛️ Filters")
            
            # Document filter
            all_docs = [ext.get("document_id", "Unknown") for ext in self.extractions]
            selected_docs = st.multiselect(
                "Select Documents",
                options=all_docs,
                default=all_docs[:5] if len(all_docs) > 5 else all_docs
            )
            
            # Risk level filter
            risk_levels = ["high", "medium", "low", "unknown"]
            selected_risks = st.multiselect(
                "Risk Levels",
                options=risk_levels,
                default=risk_levels
            )
            
            # Date range filter
            st.subheader("Date Range")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start", value=datetime(2024, 1, 1))
            with col2:
                end_date = st.date_input("End", value=datetime.now())
        
        # Filter data
        filtered_data = [
            ext for ext in self.extractions
            if ext.get("document_id", "Unknown") in selected_docs
        ]
        
        # Main content area with tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "⚠️ Risk Analysis", 
            "📋 Recommendations", 
            "🔍 Findings",
            "📈 Trends"
        ])
        
        with tab1:
            self._render_overview(filtered_data)
        
        with tab2:
            self._render_risk_analysis(filtered_data, selected_risks)
        
        with tab3:
            self._render_recommendations(filtered_data)
        
        with tab4:
            self._render_findings(filtered_data)
        
        with tab5:
            self._render_trends(filtered_data)
    
    def _render_overview(self, data: List[Dict[str, Any]]):
        """Render overview metrics"""
        st.header("📊 Extraction Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Documents",
                len(data),
                delta=f"{len(data) - len(self.extractions)} selected"
            )
        
        with col2:
            # Calculate average completeness
            completeness_scores = []
            for ext in data:
                if "meta" in ext and "completeness_score" in ext["meta"]:
                    completeness_scores.append(ext["meta"]["completeness_score"])
            
            avg_completeness = np.mean(completeness_scores) if completeness_scores else 0
            st.metric(
                "Avg. Completeness",
                f"{avg_completeness:.1f}%",
                delta=f"{avg_completeness - 50:.1f}% vs target"
            )
        
        with col3:
            # Count total findings
            total_findings = sum(
                len(ext.get("categories", {}).get("finding_summary", {}).get("related_findings", [])) + 1
                for ext in data
                if ext.get("categories", {}).get("finding_summary", {}).get("main_finding")
            )
            st.metric("Total Findings", total_findings)
        
        with col4:
            # Count total recommendations
            total_recs = sum(
                1 for ext in data
                if ext.get("categories", {}).get("recommendation_tracking", {}).get("recommendation_text")
            )
            st.metric("Total Recommendations", total_recs)
        
        # Completeness by category chart
        st.subheader("📈 Data Completeness by Category")
        category_completeness = self._calculate_category_completeness(data)
        
        fig = px.bar(
            x=list(category_completeness.keys()),
            y=list(category_completeness.values()),
            labels={'x': 'Category', 'y': 'Completeness (%)'},
            title="Extraction Completeness by Category"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Document completeness heatmap
        st.subheader("🗺️ Document Completeness Heatmap")
        doc_completeness = self._create_completeness_heatmap(data)
        st.plotly_chart(doc_completeness, use_container_width=True)
    
    def _render_risk_analysis(self, data: List[Dict[str, Any]], selected_risks: List[str]):
        """Render risk analysis section"""
        st.header("⚠️ Risk Analysis")
        
        # Extract risk data
        risks = []
        for ext in data:
            risk_data = ext.get("categories", {}).get("risk_assessment", {})
            if risk_data.get("risk_level") in selected_risks:
                risks.append({
                    "document": ext.get("document_id", "Unknown"),
                    "risk_level": risk_data.get("risk_level", "unknown"),
                    "description": risk_data.get("risk_description", ""),
                    "categories": ", ".join(risk_data.get("risk_categories", [])),
                    "mitigation": len(risk_data.get("mitigation_measures", []))
                })
        
        # Risk distribution pie chart
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Risk Distribution")
            risk_counts = pd.DataFrame(risks)['risk_level'].value_counts()
            
            fig = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                color_discrete_map={
                    'high': '#FF4B4B',
                    'medium': '#FFA500',
                    'low': '#00CC00',
                    'unknown': '#808080'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Risk Details")
            if risks:
                risk_df = pd.DataFrame(risks)
                st.dataframe(
                    risk_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "risk_level": st.column_config.TextColumn(
                            "Risk Level",
                            help="Risk severity level"
                        ),
                        "mitigation": st.column_config.NumberColumn(
                            "Mitigation Count",
                            help="Number of mitigation measures"
                        )
                    }
                )
            else:
                st.info("No risks found in selected documents")
        
        # Risk mitigation analysis
        st.subheader("🛡️ Mitigation Measures")
        all_mitigations = []
        for ext in data:
            risk_data = ext.get("categories", {}).get("risk_assessment", {})
            for measure in risk_data.get("mitigation_measures", []):
                all_mitigations.append({
                    "measure": measure,
                    "document": ext.get("document_id", "Unknown"),
                    "risk_level": risk_data.get("risk_level", "unknown")
                })
        
        if all_mitigations:
            mit_df = pd.DataFrame(all_mitigations)
            st.dataframe(mit_df, use_container_width=True, hide_index=True)
    
    def _render_recommendations(self, data: List[Dict[str, Any]]):
        """Render recommendations tracking"""
        st.header("📋 Recommendations Tracking")
        
        # Extract recommendations
        recommendations = []
        for ext in data:
            rec_data = ext.get("categories", {}).get("recommendation_tracking", {})
            if rec_data.get("recommendation_text"):
                recommendations.append({
                    "ID": rec_data.get("recommendation_id", "N/A"),
                    "Document": ext.get("document_id", "Unknown"),
                    "Recommendation": rec_data.get("recommendation_text", "")[:100] + "...",
                    "Status": rec_data.get("status", "unknown"),
                    "Responsible": rec_data.get("responsible_entity", "N/A"),
                    "Deadline": rec_data.get("deadline", "N/A")
                })
        
        # Status distribution
        if recommendations:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                status_counts = pd.DataFrame(recommendations)['Status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Recommendation Status"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Recommendations table
                rec_df = pd.DataFrame(recommendations)
                st.dataframe(
                    rec_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["open", "in_progress", "closed", "unknown"]
                        )
                    }
                )
        else:
            st.info("No recommendations found in selected documents")
        
        # Responsibility matrix
        st.subheader("👥 Responsibility Matrix")
        if recommendations:
            resp_df = pd.DataFrame(recommendations).groupby('Responsible').size().reset_index(name='Count')
            fig = px.bar(resp_df, x='Responsible', y='Count', title="Recommendations by Responsible Entity")
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_findings(self, data: List[Dict[str, Any]]):
        """Render findings analysis"""
        st.header("🔍 Findings Analysis")
        
        # Extract findings
        findings = []
        for ext in data:
            finding_data = ext.get("categories", {}).get("finding_summary", {})
            if finding_data.get("main_finding"):
                findings.append({
                    "finding_id": finding_data.get("finding_id", "N/A"),
                    "document": ext.get("document_id", "Unknown"),
                    "finding": finding_data.get("main_finding", "")[:150] + "...",
                    "priority": finding_data.get("priority", "unknown"),
                    "areas": ", ".join(finding_data.get("affected_areas", []))
                })
        
        # Priority distribution
        if findings:
            priority_counts = pd.DataFrame(findings)['priority'].value_counts()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=priority_counts.index,
                    y=priority_counts.values,
                    marker_color=['#FF4B4B' if p == 'high' else '#FFA500' if p == 'medium' else '#00CC00' 
                                  for p in priority_counts.index]
                )
            ])
            fig.update_layout(title="Findings by Priority", xaxis_title="Priority", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
            
            # Findings table
            st.subheader("📋 All Findings")
            findings_df = pd.DataFrame(findings)
            st.dataframe(findings_df, use_container_width=True, hide_index=True)
            
            # Affected areas word cloud (simplified version)
            st.subheader("🏢 Most Affected Areas")
            all_areas = []
            for f in findings:
                areas = f['areas'].split(', ')
                all_areas.extend(areas)
            
            area_counts = pd.Series(all_areas).value_counts().head(10)
            fig = px.bar(
                x=area_counts.values,
                y=area_counts.index,
                orientation='h',
                title="Top 10 Affected Areas"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No findings found in selected documents")
    
    def _render_trends(self, data: List[Dict[str, Any]]):
        """Render trends and insights"""
        st.header("📈 Trends & Insights")
        
        # Extraction quality over time (simulated for now)
        st.subheader("📊 Extraction Quality Trend")
        
        # Create sample trend data
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='M')
        quality_scores = np.random.normal(60, 10, len(dates))
        quality_scores = np.clip(quality_scores, 0, 100)
        
        trend_df = pd.DataFrame({
            'Date': dates,
            'Quality Score': quality_scores
        })
        
        fig = px.line(
            trend_df, 
            x='Date', 
            y='Quality Score',
            title="Extraction Quality Over Time",
            markers=True
        )
        fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Target: 50%")
        st.plotly_chart(fig, use_container_width=True)
        
        # Category coverage comparison
        st.subheader("📊 Category Coverage Comparison")
        categories = [
            "risk_assessment", "recommendation_tracking", "finding_summary",
            "environmental_impact", "timeline_analysis", "stakeholder_info",
            "compliance_status", "audit_metadata", "financial_data"
        ]
        
        coverage_data = []
        for cat in categories:
            count = sum(
                1 for ext in data
                if ext.get("categories", {}).get(cat, {})
            )
            coverage_data.append({
                "Category": cat.replace("_", " ").title(),
                "Coverage": (count / len(data) * 100) if data else 0
            })
        
        coverage_df = pd.DataFrame(coverage_data)
        fig = px.bar(
            coverage_df,
            x='Category',
            y='Coverage',
            title="Category Coverage Across Documents",
            color='Coverage',
            color_continuous_scale='viridis'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Key insights
        st.subheader("💡 Key Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(
                f"**📈 Data Quality**: Average extraction completeness is "
                f"{np.mean([ext.get('meta', {}).get('completeness_score', 0) for ext in data]):.1f}%"
            )
            
            high_risk_count = sum(
                1 for ext in data
                if ext.get("categories", {}).get("risk_assessment", {}).get("risk_level") == "high"
            )
            st.warning(f"**⚠️ High Risk Items**: {high_risk_count} documents contain high-risk findings")
        
        with col2:
            open_recs = sum(
                1 for ext in data
                if ext.get("categories", {}).get("recommendation_tracking", {}).get("status") == "open"
            )
            st.error(f"**📋 Open Recommendations**: {open_recs} recommendations require action")
            
            st.success(
                f"**✅ Processed Documents**: Successfully extracted data from "
                f"{len(data)} out of {len(self.extractions)} documents"
            )
    
    def _calculate_category_completeness(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate completeness percentage for each category"""
        categories = [
            "risk_assessment", "recommendation_tracking", "finding_summary",
            "environmental_impact", "timeline_analysis", "stakeholder_info",
            "compliance_status", "audit_metadata", "financial_data"
        ]
        
        completeness = {}
        for cat in categories:
            if not data:
                completeness[cat] = 0
                continue
                
            filled_count = sum(
                1 for ext in data
                if ext.get("categories", {}).get(cat, {})
            )
            completeness[cat] = (filled_count / len(data)) * 100
        
        return completeness
    
    def _create_completeness_heatmap(self, data: List[Dict[str, Any]]):
        """Create a heatmap showing completeness by document and category"""
        categories = [
            "risk_assessment", "recommendation_tracking", "finding_summary",
            "environmental_impact", "timeline_analysis", "stakeholder_info",
            "compliance_status", "audit_metadata", "financial_data"
        ]
        
        # Create matrix
        doc_names = [ext.get("document_id", "Unknown")[:30] + "..." for ext in data[:10]]  # Limit to 10 docs
        matrix = []
        
        for ext in data[:10]:
            row = []
            for cat in categories:
                # 1 if category has data, 0 otherwise
                has_data = 1 if ext.get("categories", {}).get(cat, {}) else 0
                row.append(has_data)
            matrix.append(row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=[cat.replace("_", " ").title() for cat in categories],
            y=doc_names,
            colorscale=[[0, 'red'], [1, 'green']],
            showscale=False
        ))
        
        fig.update_layout(
            title="Document Completeness by Category",
            xaxis_title="Category",
            yaxis_title="Document",
            height=400
        )
        
        return fig


def main():
    """Main entry point for the dashboard"""
    dashboard = MetaDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
