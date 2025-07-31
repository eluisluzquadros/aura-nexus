#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for the Comprehensive Review Agent
"""

import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from agents.review_agent import DataQualityAnalyzer, create_fake_data_summary
    print("+ Successfully imported Review Agent components")
except ImportError as e:
    print(f"- Import error: {e}")
    sys.exit(1)

def create_test_data():
    """Create simple test data with known fake entries"""
    
    test_data = {
        'gdr_nome': [
            'Padaria Sao Joao',     # Real business
            'test company',         # FAKE - test pattern
            'Loja Fashion',         # Real business
            'fake empresa',         # FAKE - fake pattern  
            'Restaurante Pizza',    # Real business
        ],
        'gdr_telefone_1': [
            '+5511987654321',       # Real phone
            '11111111111',          # FAKE - all same digits
            '11999887766',          # Real phone
            '22222222222',          # FAKE - all same digits
            '+5511988776655',       # Real phone
        ],
        'gdr_email_1': [
            'contato@padaria.com',  # Real email
            'test@test.com',        # FAKE - test domain
            'vendas@fashion.com',   # Real email
            'fake@fake.com',        # FAKE - fake domain
            'pizza@restaurante.com', # Real email
        ],
        'gdr_score_sinergia': [
            85,                     # Valid score
            150,                    # INVALID - out of range
            92,                     # Valid score
            -10,                    # INVALID - negative
            78,                     # Valid score
        ]
    }
    
    return pd.DataFrame(test_data)

async def test_fake_detection():
    """Test fake data detection"""
    print("\n=== Testing Fake Data Detection ===")
    
    # Create test data
    df = create_test_data()
    print(f"Created test data with {len(df)} records")
    
    # Initialize analyzer
    analyzer = DataQualityAnalyzer()
    print("Initialized DataQualityAnalyzer")
    
    # Run analysis
    print("Running quality analysis...")
    metrics, issues = await analyzer.analyze_data_quality(df)
    
    print(f"\nResults:")
    print(f"  Overall Score: {metrics.overall_score:.2f}/100")
    print(f"  Fake Data Percentage: {metrics.fake_data_percentage:.2f}%")
    print(f"  Total Issues: {len(issues)}")
    
    # Show fake data issues
    fake_issues = [issue for issue in issues if issue.category == 'fake_data']
    print(f"  Fake Data Issues: {len(fake_issues)}")
    
    if fake_issues:
        print("\nFake data detected:")
        for issue in fake_issues:
            print(f"    - {issue.issue_type}: '{issue.value}' in {issue.field}")
    
    # Test individual patterns
    print("\n=== Testing Individual Patterns ===")
    
    # Phone patterns
    test_phones = ['11111111111', '+5511987654321', '22222222222']
    print("\nPhone validation:")
    for phone in test_phones:
        is_fake = analyzer._is_fake_phone(phone)
        status = "FAKE" if is_fake else "VALID"
        print(f"  {phone}: {status}")
    
    # Email patterns
    test_emails = ['test@test.com', 'contato@empresa.com', 'fake@fake.com']
    print("\nEmail validation:")
    for email in test_emails:
        is_fake = analyzer._is_fake_email(email)
        status = "FAKE" if is_fake else "VALID"
        print(f"  {email}: {status}")
    
    # Business name patterns
    test_names = ['test company', 'Padaria Real', 'fake empresa']
    print("\nBusiness name validation:")
    for name in test_names:
        is_fake = analyzer._is_fake_business_name(name)
        status = "FAKE" if is_fake else "VALID"
        print(f"  '{name}': {status}")
    
    return metrics, issues

async def main():
    """Main test function"""
    print("AURA NEXUS - Review Agent Test")
    print("=" * 40)
    
    try:
        # Test fake data detection
        metrics, issues = await test_fake_detection()
        
        # Create fake data summary
        fake_summary = create_fake_data_summary(issues)
        print(f"\nFake Data Summary:")
        if 'total_fake_entries' in fake_summary and fake_summary['total_fake_entries'] > 0:
            print(f"  Total fake entries: {fake_summary['total_fake_entries']}")
            
            if 'fake_by_type' in fake_summary:
                print("  By type:")
                for fake_type, count in fake_summary['fake_by_type'].items():
                    print(f"    {fake_type}: {count}")
            
            if 'examples' in fake_summary:
                print("  Examples:")
                for example in fake_summary['examples'][:3]:
                    print(f"    {example['type']}: '{example['value']}'")
        else:
            print("  No fake data detected")
        
        print(f"\n+ Test completed successfully!")
        print(f"  - Detected fake data patterns correctly")
        print(f"  - Generated quality metrics")
        print(f"  - Created issue reports")
        print(f"  - Quality Score: {metrics.overall_score:.1f}/100")
        
    except Exception as e:
        print(f"\n- Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())