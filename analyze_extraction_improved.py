#!/usr/bin/env python3
"""
Analyze improved extraction results with quote and page number validation
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedExtractionAnalyzer:
    """Analyze improved extraction results"""
    
    def __init__(self):
        self.results_dir = Path(__file__).parent / '03_extracted_data'
        self.suffix = '_improved_extraction.json'
        
    def analyze_quote_quality(self, category_data: str) -> Dict[str, any]:
        """Analyze the quality of extracted quotes"""
        if not category_data or category_data == 'NULL erfasst':
            return {
                'has_quotes': False,
                'quote_count': 0,
                'has_page_numbers': False,
                'avg_quote_length': 0
            }
        
        # Split quotes
        quotes = [q.strip() for q in category_data.split('\n\n') if q.strip()]
        
        # Check for page numbers
        quotes_with_pages = [q for q in quotes if re.search(r'\(S\.\s*\d+(?:-\d+)?\)', q)]
        
        # Calculate average length (excluding page refs)
        lengths = []
        for quote in quotes:
            # Remove page reference for length calculation
            clean_quote = re.sub(r'\s*\(S\.\s*\d+(?:-\d+)?\)$', '', quote)
            clean_quote = clean_quote.strip(' "')
            lengths.append(len(clean_quote.split()))
        
        return {
            'has_quotes': len(quotes) > 0,
            'quote_count': len(quotes),
            'has_page_numbers': len(quotes_with_pages) == len(quotes),
            'page_number_ratio': len(quotes_with_pages) / len(quotes) if quotes else 0,
            'avg_quote_length': sum(lengths) / len(lengths) if lengths else 0
        }
    
    def analyze_recommendations(self, rec_data: str) -> Dict[str, any]:
        """Analyze recommendation extraction quality"""
        if not rec_data or rec_data == 'NULL erfasst':
            return {
                'has_recommendations': False,
                'recommendation_count': 0,
                'structured_count': 0,
                'has_priorities': False
            }
        
        recs = [r.strip() for r in rec_data.split('\n\n') if r.strip()]
        
        # Count structured recommendations
        structured = [r for r in recs if re.search(r'Empfehlung\s+\d+\s*\(Priorität\s*\d+\)', r)]
        with_priorities = [r for r in recs if 'Priorität' in r]
        
        return {
            'has_recommendations': len(recs) > 0,
            'recommendation_count': len(recs),
            'structured_count': len(structured),
            'has_priorities': len(with_priorities) > 0,
            'priority_ratio': len(with_priorities) / len(recs) if recs else 0
        }
    
    def analyze_all_extractions(self) -> pd.DataFrame:
        """Analyze all extraction results"""
        extraction_files = list(self.results_dir.glob(f'*{self.suffix}'))
        logger.info(f"Found {len(extraction_files)} improved extraction files")
        
        results = []
        
        # Quote categories to analyze
        quote_categories = [
            'Umwelt, Info A (Relevante Akteure)',
            'Umwelt, Info B (Berichtsprache/Datei)',
            'Umwelt, Info C (Bedenken/Monitoring)',
            'Flankieigend A (kein Plan)',
            'Flankieigend B (Plan unvollständig)',
            'Flankieigend C (in der Nachverfolgung)'
        ]
        
        for file in extraction_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                doc_id = data.get('document_id', file.stem)
                categories = data.get('categories', {})
                
                # Basic extraction stats
                filled_count = sum(1 for v in categories.values() 
                                 if v and v not in ['NULL erfasst', 'Nicht erfasst', ''])
                
                result = {
                    'document_id': doc_id,
                    'total_categories': len(categories),
                    'filled_categories': filled_count,
                    'completion_rate': filled_count / len(categories) if categories else 0
                }
                
                # Analyze each quote category
                for cat in quote_categories:
                    if cat in categories:
                        quote_analysis = self.analyze_quote_quality(categories[cat])
                        result[f'{cat}_quotes'] = quote_analysis['quote_count']
                        result[f'{cat}_pages'] = quote_analysis['has_page_numbers']
                
                # Analyze recommendations
                rec_analysis = self.analyze_recommendations(categories.get('Empfehlungen', ''))
                result['recommendation_count'] = rec_analysis['recommendation_count']
                result['structured_recommendations'] = rec_analysis['structured_count']
                result['has_priorities'] = rec_analysis['has_priorities']
                
                # Key category presence
                result['has_berichtdatum'] = bool(categories.get('Berichtdatum'))
                result['has_pa_nummer'] = bool(categories.get('PA-Nummer'))
                result['has_kernproblem'] = bool(categories.get('Kernproblem'))
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error analyzing {file}: {str(e)}")
        
        return pd.DataFrame(results)
    
    def generate_quality_report(self, df: pd.DataFrame):
        """Generate a quality report"""
        logger.info("\n" + "="*80)
        logger.info("IMPROVED EXTRACTION QUALITY REPORT")
        logger.info("="*80 + "\n")
        
        # Overall statistics
        logger.info("Overall Statistics:")
        logger.info(f"  Total Documents: {len(df)}")
        logger.info(f"  Average Completion Rate: {df['completion_rate'].mean():.1%}")
        logger.info(f"  Documents with >90% completion: {len(df[df['completion_rate'] > 0.9])}")
        
        # Quote quality
        quote_cols = [c for c in df.columns if '_quotes' in c and not '_pages' in c]
        if quote_cols:
            logger.info("\nQuote Extraction Quality:")
            for col in quote_cols:
                cat_name = col.replace('_quotes', '')
                pages_col = f'{cat_name}_pages'
                docs_with_quotes = len(df[df[col] > 0])
                docs_with_pages = len(df[df[pages_col] == True]) if pages_col in df else 0
                logger.info(f"  {cat_name}:")
                logger.info(f"    - Documents with quotes: {docs_with_quotes}/{len(df)}")
                logger.info(f"    - Documents with page numbers: {docs_with_pages}/{docs_with_quotes}")
                logger.info(f"    - Average quotes per doc: {df[col].mean():.1f}")
        
        # Recommendation quality
        logger.info("\nRecommendation Quality:")
        logger.info(f"  Documents with recommendations: {len(df[df['recommendation_count'] > 0])}/{len(df)}")
        logger.info(f"  Average recommendations per doc: {df['recommendation_count'].mean():.1f}")
        logger.info(f"  Documents with structured format: {len(df[df['structured_recommendations'] > 0])}")
        logger.info(f"  Documents with priorities: {len(df[df['has_priorities'] == True])}")
        
        # Key fields
        logger.info("\nKey Field Extraction:")
        logger.info(f"  PA-Nummer: {len(df[df['has_pa_nummer'] == True])}/{len(df)} ({len(df[df['has_pa_nummer'] == True])/len(df)*100:.0f}%)")
        logger.info(f"  Berichtdatum: {len(df[df['has_berichtdatum'] == True])}/{len(df)} ({len(df[df['has_berichtdatum'] == True])/len(df)*100:.0f}%)")
        logger.info(f"  Kernproblem: {len(df[df['has_kernproblem'] == True])}/{len(df)} ({len(df[df['has_kernproblem'] == True])/len(df)*100:.0f}%)")
        
        # Save detailed analysis
        analysis_file = self.results_dir / 'extraction_analysis_improved.csv'
        df.to_csv(analysis_file, index=False)
        logger.info(f"\nDetailed analysis saved to: {analysis_file}")
    
    def compare_with_original(self):
        """Compare improved results with original extraction"""
        # Load original analysis if exists
        original_file = self.results_dir / 'extraction_analysis_correct.csv'
        if original_file.exists():
            original_df = pd.read_csv(original_file)
            improved_df = self.analyze_all_extractions()
            
            logger.info("\n" + "="*80)
            logger.info("COMPARISON WITH ORIGINAL EXTRACTION")
            logger.info("="*80 + "\n")
            
            # Compare completion rates
            if 'completion_percentage' in original_df.columns:
                orig_completion = original_df['completion_percentage'].mean()
                imp_completion = improved_df['completion_rate'].mean() * 100
                
                logger.info(f"Average Completion Rate:")
                logger.info(f"  Original: {orig_completion:.1f}%")
                logger.info(f"  Improved: {imp_completion:.1f}%")
                logger.info(f"  Improvement: {imp_completion - orig_completion:+.1f}%")
            
            return improved_df
        else:
            logger.info("No original analysis found for comparison")
            return self.analyze_all_extractions()

def main():
    """Main entry point"""
    analyzer = ImprovedExtractionAnalyzer()
    
    # Analyze extractions
    df = analyzer.compare_with_original()
    
    # Generate quality report
    analyzer.generate_quality_report(df)
    
    # Print sample of improved quotes
    logger.info("\n" + "="*80)
    logger.info("SAMPLE IMPROVED QUOTES WITH PAGE NUMBERS")
    logger.info("="*80 + "\n")
    
    # Load a sample extraction to show quote format
    sample_files = list(analyzer.results_dir.glob('*_improved_extraction.json'))
    if sample_files:
        with open(sample_files[0], 'r', encoding='utf-8') as f:
            sample = json.load(f)
        
        logger.info(f"Document: {sample['document_id']}\n")
        
        # Show a quote from Info A
        info_a = sample['categories'].get('Umwelt, Info A (Relevante Akteure)', '')
        if info_a and info_a != 'NULL erfasst':
            quotes = info_a.split('\n\n')[:2]  # First 2 quotes
            logger.info("Info A - Relevante Akteure:")
            for quote in quotes:
                logger.info(f"  {quote}\n")

if __name__ == "__main__":
    main()
