#!/usr/bin/env python3
"""
Diagnose why GREEN (findings) and GRAY (annex) sections were lost
"""

import json
from pathlib import Path

def diagnose_issue():
    print("DIAGNOSIS: Why GREEN (findings) and GRAY (annex) sections are missing")
    print("="*80)
    
    # Check configuration files
    print("\n1. CHECKING LABEL CONFIGURATION:")
    print("-"*50)
    
    label_config = Path("config/label_patterns.json")
    if label_config.exists():
        with open(label_config, 'r') as f:
            config = json.load(f)
            
        print("Color mapping in label_patterns.json:")
        if 'color_mapping' in config:
            for color_hex, label in config['color_mapping'].items():
                print(f"  {color_hex} -> {label}")
                
        # Check if green is mapped
        green_mapped = any("#00FF00" in k for k in config.get('color_mapping', {}))
        print(f"\n✓ Green (#00FF00) mapped: {green_mapped}")
        
        # Check labels defined
        print("\nLabels defined:")
        for label, info in config['labels'].items():
            print(f"  - {label}: {info.get('description', 'No description')}")
            
        findings_defined = 'findings' in config['labels']
        appendix_defined = 'appendix' in config['labels']
        print(f"\n✓ 'findings' label defined: {findings_defined}")
        print(f"✓ 'appendix' label defined: {appendix_defined}")
    
    print("\n2. HYPOTHESIS OF WHAT HAPPENED:")
    print("-"*50)
    print("""
The labeling process appears to have:

1. Used pattern-based matching instead of color-based labeling
   - It looked for text patterns like "Wesentliches in Kürze", "Einleitung", etc.
   - It ignored the actual color coding from your input documents

2. The color_mapping in config only maps certain colors:
   - It has mappings for evaluation, recommendations, response
   - But the actual GREEN and GRAY from your documents were not recognized

3. Your original color scheme:
   - GREEN = Findings (Feststellungen) - The main content
   - GRAY = Annex (Anhang) - Appendix sections  
   - DARK YELLOW = Recommendations

4. What got labeled instead:
   - CYAN = Executive summaries (wik)
   - YELLOW = Introduction sections
   - BLUE = Evaluation sections
   - PINK = Response sections

RESULT: All the GREEN findings content (which you said is the biggest part) 
        and GRAY annex content was completely ignored!
""")
    
    print("\n3. SOLUTION:")
    print("-"*50)
    print("""
To fix this, we need to:

1. Re-process the documents using COLOR-BASED labeling, not pattern matching
2. Map colors correctly:
   - RGB(0,255,0) / #00FF00 -> 'findings' 
   - RGB(128,128,128) / #808080 -> 'appendix'
   - Keep other mappings as they are

3. Create a new chunking process that:
   - Reads the color-coded documents
   - Extracts text with its color
   - Labels based on color, not text patterns
   - Preserves ALL colored sections
""")

if __name__ == "__main__":
    diagnose_issue()
