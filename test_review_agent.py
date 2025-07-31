#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the Comprehensive Review Agent
Demonstrates how to detect fake data and generate quality reports
"""

import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.review_agent import (
    ComprehensiveReviewAgent,
    DataQualityAnalyzer,
    create_fake_data_summary,
    run_comprehensive_review
)

def create_test_data_with_fake_entries():
    """Create test data with known fake entries for demonstration"""
    
    # Create mix of real and fake data
    test_data = {
        'gdr_nome': [
            'Padaria São João',           # Real business name
            'Loja de Roupas Fashion',     # Real business name  
            'test company',               # FAKE - suspicious pattern
            'Restaurante Pizza Bella',    # Real business name
            'fake empresa',               # FAKE - contains 'fake'
            'Auto Peças Center',          # Real business name
            'dummy business',             # FAKE - contains 'dummy'
            'Salão de Beleza Glamour',    # Real business name
            '123456',                     # FAKE - only numbers
            'Farmácia Popular',           # Real business name
        ],
        'gdr_telefone_1': [
            '+5511987654321',             # Real phone format
            '11999887766',                # Real phone format
            '11111111111',                # FAKE - all same digits
            '+5511988776655',             # Real phone format
            '22222222222',                # FAKE - all same digits
            '11987123456',                # Real phone format
            '123456789',                  # FAKE - too short
            '+5511976543210',             # Real phone format
            '99999999999',                # FAKE - all 9s
            '11988997788',                # Real phone format
        ],
        'gdr_email_1': [
            'contato@padaria.com',        # Real email
            'vendas@fashion.com.br',      # Real email
            'test@test.com',              # FAKE - test domain
            'pizza@restaurante.com',      # Real email
            'fake@fake.com',              # FAKE - fake domain
            'info@autopecas.com',         # Real email
            'dummy@dummy.com',            # FAKE - dummy domain
            'beleza@salao.com.br',        # Real email
            'example@example.com',        # FAKE - example domain
            'farmacia@popular.com',       # Real email
        ],
        'gdr_website': [
            'https://padariasaojoao.com.br',     # Real website
            'https://fashionloja.com',           # Real website
            'test.com',                          # FAKE - test domain
            'https://pizzabella.com.br',         # Real website
            'fake.com',                          # FAKE - fake domain
            'https://autopecascenter.com',       # Real website
            'dummy.com',                         # FAKE - dummy domain
            'https://salaoglamour.com.br',       # Real website
            'example.com',                       # FAKE - example domain
            'https://farmaciapopular.com.br',    # Real website
        ],
        'gdr_score_sinergia': [
            85,                           # Valid score
            92,                           # Valid score
            150,                          # INVALID - out of range
            78,                           # Valid score
            -10,                          # INVALID - negative
            88,                           # Valid score
            200,                          # INVALID - too high
            91,                           # Valid score
            0,                            # Valid score (edge case)
            87,                           # Valid score
        ],
        'gdr_url_instagram': [
            'https://instagram.com/padariasaojoao',  # Real Instagram
            'https://instagram.com/fashionloja',     # Real Instagram
            '',                                      # Missing data
            'https://instagram.com/pizzabella',      # Real Instagram
            '',                                      # Missing data
            'https://instagram.com/autopecas',       # Real Instagram
            '',                                      # Missing data
            'https://instagram.com/salaoglamour',    # Real Instagram
            '',                                      # Missing data
            'https://instagram.com/farmacia',        # Real Instagram
        ],
        'gdr_insta_followers': [
            1250,                         # Real follower count
            3400,                         # Real follower count
            np.nan,                       # Missing data
            2100,                         # Real follower count
            np.nan,                       # Missing data
            890,                          # Real follower count
            np.nan,                       # Missing data
            5600,                         # Real follower count
            np.nan,                       # Missing data
            1890,                         # Real follower count
        ],
        'gdr_analise_reviews': [
            'Análise positiva com 4.5 estrelas',
            'Reviews majoritariamente positivas',
            '',                           # Missing enrichment
            'Excelentes avaliações no Google',
            '',                           # Missing enrichment
            'Boas reviews de clientes',
            '',                           # Missing enrichment
            'Reviews muito positivas',
            '',                           # Missing enrichment
            'Avaliações satisfatórias',
        ],
        'gdr_total_tokens': [
            1250, 1340, 0, 1180, 0, 1290, 0, 1450, 0, 1320
        ],
        'gdr_total_cost': [
            0.025, 0.027, 0.000, 0.024, 0.000, 0.026, 0.000, 0.029, 0.000, 0.026
        ]
    }
    
    return pd.DataFrame(test_data)

async def test_data_quality_analyzer():
    """Test the DataQualityAnalyzer specifically"""
    print("🔍 Testing DataQualityAnalyzer...")
    
    # Create test data
    df = create_test_data_with_fake_entries()
    
    # Initialize analyzer
    analyzer = DataQualityAnalyzer()
    
    # Run analysis
    metrics, issues = await analyzer.analyze_data_quality(df)
    
    print(f"\n📊 Quality Analysis Results:")
    print(f"  • Overall Score: {metrics.overall_score:.2f}/100")
    print(f"  • Completeness Score: {metrics.completeness_score:.2f}%")
    print(f"  • Accuracy Score: {metrics.accuracy_score:.2f}%")
    print(f"  • Fake Data Percentage: {metrics.fake_data_percentage:.2f}%")
    print(f"  • Total Issues Found: {len(issues)}")
    
    # Show fake data issues specifically
    fake_issues = [issue for issue in issues if issue.category == 'fake_data']
    print(f"\n🚫 Fake Data Issues ({len(fake_issues)} found):")
    
    fake_summary = create_fake_data_summary(issues)
    if 'fake_by_type' in fake_summary:
        for fake_type, count in fake_summary['fake_by_type'].items():
            print(f"  • {fake_type.replace('_', ' ').title()}: {count} cases")
    
    # Show examples
    if 'examples' in fake_summary:
        print(f"\n📝 Examples of fake data detected:")
        for example in fake_summary['examples'][:5]:  # Show first 5
            print(f"  • {example['type']}: '{example['value']}' in field {example['field']}")
    
    return metrics, issues

async def test_comprehensive_review():
    """Test the full ComprehensiveReviewAgent"""
    print("\n🚀 Testing Comprehensive Review Agent...")
    
    # Create test data
    df = create_test_data_with_fake_entries()
    
    # Initialize review agent
    review_agent = ComprehensiveReviewAgent()
    
    # Start review session
    session_id = await review_agent.start_review_session("fake_data_test")
    print(f"📋 Started review session: {session_id}")
    
    # Run comprehensive review
    results = await review_agent.comprehensive_review(
        results_df=df,
        output_dir="data/review_reports"
    )
    
    # Display results
    summary = results['summary']
    print(f"\n📊 Comprehensive Review Results:")
    print(f"  • Quality Score: {summary['overall_assessment']['quality_score']:.2f}/100")
    print(f"  • System Health: {summary['overall_assessment']['system_health'].upper()}")
    print(f"  • Immediate Action Required: {'YES' if summary['overall_assessment']['immediate_action_required'] else 'NO'}")
    
    # Show findings
    findings = summary['key_findings']
    print(f"\n🔍 Key Findings:")
    if findings['fake_data_detected']:
        print(f"  • ❌ Fake data detected")
    if findings['data_completeness_issues']:
        print(f"  • ❌ Data completeness issues")
    if findings['enrichment_problems']:
        print(f"  • ❌ Enrichment problems")
    if findings['critical_issues_count'] > 0:
        print(f"  • ❌ {findings['critical_issues_count']} critical issues")
    
    # Show recommendations
    rec_summary = summary['recommendations_summary']
    print(f"\n📋 Recommendations:")
    print(f"  • Total Recommendations: {rec_summary['total_recommendations']}")
    print(f"  • Critical Priority: {rec_summary['critical_priority']}")
    print(f"  • Estimated Timeline: {rec_summary['estimated_timeline']}")
    
    # Show next steps
    print(f"\n🎯 Next Steps:")
    for i, step in enumerate(summary['next_steps'], 1):
        print(f"  {i}. {step}")
    
    # Show markdown report path
    if 'markdown_report_path' in results:
        print(f"\n📄 Detailed report saved to: {results['markdown_report_path']}")
    
    return results

async def test_with_existing_data():
    """Test with existing processed data if available"""
    print("\n📁 Testing with existing data...")
    
    # Look for existing processed data
    data_files = [
        "data/output/test_enriched_fixed.xlsx",
        "data/output/test_pipeline_result.xlsx",
        "data/input/base-leads_amostra_v2_enriched_full.xlsx"
    ]
    
    existing_file = None
    for file_path in data_files:
        if Path(file_path).exists():
            existing_file = file_path
            break
    
    if not existing_file:
        print("  ⚠️ No existing processed data found. Skipping this test.")
        return None
    
    print(f"  📊 Found data file: {existing_file}")
    
    try:
        # Run comprehensive review on existing data
        results = await run_comprehensive_review(
            df_path=existing_file,
            output_dir="data/review_reports"
        )
        
        summary = results['summary']
        print(f"  • Quality Score: {summary['overall_assessment']['quality_score']:.2f}/100")
        print(f"  • Total Records: {results['review_report']['quality_analysis']['metrics']['total_records']:,}")
        print(f"  • Issues Found: {len(results['review_report']['quality_analysis']['issues']):,}")
        
        # Show fake data specifically
        issues = results['review_report']['quality_analysis']['issues']
        fake_issues = [issue for issue in issues if issue['category'] == 'fake_data']
        if fake_issues:
            print(f"  • 🚫 Fake data issues: {len(fake_issues)}")
        
        print(f"  • 📄 Report saved to: {results.get('markdown_report_path', 'N/A')}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ Error processing existing data: {str(e)}")
        return None

def demonstrate_fake_patterns():
    """Demonstrate the types of fake patterns detected"""
    print("\n🎭 Fake Data Patterns Demonstration")
    print("="*50)
    
    analyzer = DataQualityAnalyzer()
    
    # Test fake phone numbers
    fake_phones = ['11111111111', '22222222222', '123456789', '999999999999', '000000000000']
    real_phones = ['+5511987654321', '11999887766', '11988776655']
    
    print("\n📞 Phone Number Detection:")
    print("  Fake phones detected:")
    for phone in fake_phones:
        is_fake = analyzer._is_fake_phone(phone)
        print(f"    {phone}: {'❌ FAKE' if is_fake else '✅ VALID'}")
    
    print("  Real phones detected:")
    for phone in real_phones:
        is_fake = analyzer._is_fake_phone(phone)
        print(f"    {phone}: {'❌ FAKE' if is_fake else '✅ VALID'}")
    
    # Test fake emails
    fake_emails = ['test@test.com', 'fake@fake.com', 'dummy@dummy.com', 'example@example.com']
    real_emails = ['contato@empresa.com', 'vendas@loja.com.br', 'info@negocio.com']
    
    print("\n📧 Email Detection:")
    print("  Fake emails detected:")
    for email in fake_emails:
        is_fake = analyzer._is_fake_email(email)
        print(f"    {email}: {'❌ FAKE' if is_fake else '✅ VALID'}")
    
    print("  Real emails detected:")
    for email in real_emails:
        is_fake = analyzer._is_fake_email(email)
        print(f"    {email}: {'❌ FAKE' if is_fake else '✅ VALID'}")
    
    # Test fake business names
    fake_names = ['test company', 'fake empresa', 'dummy business', '123456', 'a']
    real_names = ['Padaria São João', 'Loja Fashion', 'Restaurante Pizza']
    
    print("\n🏢 Business Name Detection:")
    print("  Fake names detected:")
    for name in fake_names:
        is_fake = analyzer._is_fake_business_name(name)
        print(f"    '{name}': {'❌ FAKE' if is_fake else '✅ VALID'}")
    
    print("  Real names detected:")
    for name in real_names:
        is_fake = analyzer._is_fake_business_name(name)
        print(f"    '{name}': {'❌ FAKE' if is_fake else '✅ VALID'}")

async def main():
    """Main test function"""
    print("🧪 AURA NEXUS - Comprehensive Review Agent Test")
    print("=" * 60)
    
    # Create output directory
    Path("data/review_reports").mkdir(parents=True, exist_ok=True)
    
    try:
        # Test 1: Demonstrate fake pattern detection
        demonstrate_fake_patterns()
        
        # Test 2: Test DataQualityAnalyzer
        await test_data_quality_analyzer()
        
        # Test 3: Test comprehensive review with test data
        await test_comprehensive_review()
        
        # Test 4: Test with existing data (if available)
        await test_with_existing_data()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary:")
        print("  • Created comprehensive Review Agent with 4 main classes")
        print("  • Implemented advanced fake data detection")
        print("  • Added quality scoring and improvement planning")
        print("  • Generated detailed markdown reports")
        print("  • Demonstrated learning and optimization capabilities")
        
        print(f"\n📂 Check 'data/review_reports/' for generated reports")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())