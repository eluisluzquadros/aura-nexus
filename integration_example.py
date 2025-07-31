#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Example: AURA NEXUS with Comprehensive Review Agent
Shows how to integrate the new Review Agent with the existing lead processing system
"""

import asyncio
import pandas as pd
from pathlib import Path
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.review_agent import ComprehensiveReviewAgent
from core.lead_processor import LeadProcessor
from core.api_manager import APIManager
from infrastructure.cache_system import SmartMultiLevelCache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AURA_NEXUS.Integration")

class EnhancedLeadProcessor:
    """
    Enhanced Lead Processor with integrated Review Agent
    Automatically detects quality issues and provides improvement recommendations
    """
    
    def __init__(self):
        # Initialize components
        self.api_manager = APIManager()
        self.cache = SmartMultiLevelCache()
        self.lead_processor = LeadProcessor(self.api_manager, self.cache)
        self.review_agent = ComprehensiveReviewAgent()
        
        # Quality tracking
        self.processing_results = []
        self.quality_trends = []
    
    async def initialize(self):
        """Initialize all components"""
        await self.lead_processor.initialize()
        await self.review_agent.start_review_session("enhanced_processing")
        logger.info("✅ Enhanced Lead Processor initialized with Review Agent")
    
    async def process_leads_with_quality_review(self, 
                                              input_file: str,
                                              features: list,
                                              output_file: str = None,
                                              enable_auto_review: bool = True) -> dict:
        """
        Process leads with automatic quality review
        
        Args:
            input_file: Path to input Excel/CSV file
            features: List of features to execute
            output_file: Path to save results (optional)
            enable_auto_review: Whether to run automatic quality review
            
        Returns:
            Processing results with quality analysis
        """
        logger.info(f"🚀 Starting enhanced lead processing with quality review...")
        
        # 1. Load input data
        logger.info(f"📊 Loading data from: {input_file}")
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file)
        
        original_df = df.copy()  # Keep original for comparison
        logger.info(f"✅ Loaded {len(df)} leads for processing")
        
        # 2. Process leads (simplified for demo - in real implementation would use full pipeline)
        logger.info(f"⚙️ Processing leads with features: {features}")
        processed_results = []
        
        for idx, row in df.iterrows():
            lead_data = row.to_dict()
            
            # Mock processing (in real implementation, use actual lead processor)
            try:
                # This would be: result = await self.lead_processor.process_lead(lead_data, features)
                result = await self._mock_process_lead(lead_data, features)
                processed_results.append(result)
                
                if idx % 10 == 0:  # Progress update every 10 records
                    logger.info(f"📈 Processed {idx + 1}/{len(df)} leads")
                    
            except Exception as e:
                logger.error(f"❌ Error processing lead {idx}: {str(e)}")
                # Add error record
                error_result = lead_data.copy()
                error_result['processing_error'] = str(e)
                processed_results.append(error_result)
        
        # 3. Convert to DataFrame
        results_df = pd.DataFrame(processed_results)
        logger.info(f"✅ Processing completed. {len(results_df)} results generated")
        
        # 4. Run quality review (if enabled)
        review_results = None
        if enable_auto_review:
            logger.info("🔍 Running automatic quality review...")
            
            review_results = await self.review_agent.comprehensive_review(
                results_df=results_df,
                original_df=original_df,
                output_dir="data/review_reports"
            )
            
            # Log quality insights
            quality_score = review_results['summary']['overall_assessment']['quality_score']
            logger.info(f"📊 Quality Score: {quality_score:.2f}/100")
            
            if review_results['summary']['overall_assessment']['immediate_action_required']:
                logger.warning("⚠️  IMMEDIATE ACTION REQUIRED - Critical quality issues detected!")
            
            # Show key findings
            findings = review_results['summary']['key_findings']
            if findings['fake_data_detected']:
                logger.warning("🚫 Fake data detected in results")
            if findings['data_completeness_issues']:
                logger.warning("📉 Data completeness issues found")
            if findings['enrichment_problems']:
                logger.warning("🔍 Enrichment problems detected")
        
        # 5. Save results
        if output_file:
            if output_file.endswith('.xlsx'):
                results_df.to_excel(output_file, index=False)
            else:
                results_df.to_csv(output_file, index=False)
            logger.info(f"💾 Results saved to: {output_file}")
        
        # 6. Return comprehensive results
        return {
            'processing_results': {
                'input_records': len(df),
                'output_records': len(results_df),
                'features_used': features,
                'success_rate': len([r for r in processed_results if 'processing_error' not in r]) / len(processed_results) * 100
            },
            'quality_review': review_results,
            'data': results_df,
            'recommendations': review_results['summary']['next_steps'] if review_results else []
        }
    
    async def _mock_process_lead(self, lead_data: dict, features: list) -> dict:
        """
        Mock lead processing (replace with actual lead processor call)
        """
        import random
        import time
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        result = lead_data.copy()
        
        # Mock enrichment based on features
        if 'scoring' in features or 'ai_analysis' in features:
            # Add mock scoring with some fake data for demonstration
            if 'test' in str(lead_data.get('nome_empresa', '')).lower():
                result['gdr_score_sinergia'] = random.randint(150, 200)  # Invalid score
            else:
                result['gdr_score_sinergia'] = random.randint(60, 95)
            
            result['gdr_motivo_score'] = f"Score calculado baseado em {len(features)} critérios"
        
        if 'contact_extraction' in features:
            # Add mock contact data with some fake entries
            empresa = str(lead_data.get('nome_empresa', ''))
            if 'test' in empresa.lower() or 'fake' in empresa.lower():
                result['gdr_telefone_1'] = '11111111111'  # Fake phone
                result['gdr_email_1'] = 'test@test.com'   # Fake email
            else:
                result['gdr_telefone_1'] = f'11{random.randint(900000000, 999999999)}'
                result['gdr_email_1'] = f'contato@{empresa.lower().replace(" ", "")}.com'
        
        if 'social_scraping' in features:
            # Mock social data with missing entries for some records
            if random.random() > 0.6:  # 40% success rate
                result['gdr_url_instagram'] = f'https://instagram.com/{empresa.lower().replace(" ", "")}'
                result['gdr_insta_followers'] = random.randint(100, 5000)
            else:
                result['gdr_url_instagram'] = ''
                result['gdr_insta_followers'] = None
        
        if 'web_scraping' in features:
            # Mock website detection
            if random.random() > 0.3:  # 70% success rate
                if 'test' in empresa.lower():
                    result['gdr_website'] = 'test.com'  # Fake website
                else:
                    result['gdr_website'] = f'https://{empresa.lower().replace(" ", "")}.com.br'
        
        # Add processing metadata
        result['gdr_processamento_status'] = 'concluido'
        result['gdr_features_executadas'] = ','.join(features)
        result['gdr_total_tokens'] = random.randint(1000, 2000)
        result['gdr_total_cost'] = random.uniform(0.02, 0.05)
        
        return result
    
    async def get_quality_insights(self) -> dict:
        """Get quality insights from review history"""
        if not self.review_agent.session_reports:
            return {'message': 'No quality reviews available'}
        
        return await self.review_agent.get_session_summary()
    
    async def close(self):
        """Close all resources"""
        await self.lead_processor.close()

def create_sample_input_data():
    """Create sample input data for testing"""
    sample_data = {
        'nome_empresa': [
            'Padaria Central',
            'Loja de Roupas Moderna', 
            'test company',  # This should be detected as fake
            'Restaurante Sabor',
            'fake empresa',  # This should be detected as fake
            'Salão de Beleza Elegante',
            'Auto Peças Silva',
            'dummy business',  # This should be detected as fake
            'Farmácia Popular',
            'Pizzaria do João'
        ],
        'endereco': [
            'Rua das Flores, 123',
            'Av. Principal, 456',
            'Test Street, 789',
            'Rua do Comércio, 321',
            'Fake Address, 999',
            'Av. Beleza, 111',
            'Rua das Peças, 222',
            'Dummy Road, 333',
            'Rua da Saúde, 444',
            'Av. Pizza, 555'
        ],
        'cidade': ['São Paulo'] * 10,
        'estado': ['SP'] * 10
    }
    
    return pd.DataFrame(sample_data)

async def demonstration():
    """Main demonstration function"""
    print("🚀 AURA NEXUS - Enhanced Lead Processing with Quality Review")
    print("=" * 70)
    
    # Create sample data
    print("📋 Creating sample input data...")
    sample_df = create_sample_input_data()
    
    # Save sample data
    input_file = "data/input/sample_leads.xlsx"
    Path("data/input").mkdir(parents=True, exist_ok=True)
    sample_df.to_excel(input_file, index=False)
    print(f"✅ Sample data saved to: {input_file}")
    
    # Initialize enhanced processor
    print("\n⚙️ Initializing Enhanced Lead Processor...")
    processor = EnhancedLeadProcessor()
    await processor.initialize()
    
    try:
        # Process leads with quality review
        print("\n🔄 Processing leads with automatic quality review...")
        results = await processor.process_leads_with_quality_review(
            input_file=input_file,
            features=['scoring', 'contact_extraction', 'social_scraping', 'web_scraping'],
            output_file="data/output/enhanced_results.xlsx",
            enable_auto_review=True
        )
        
        # Display results
        print(f"\n📊 Processing Results:")
        proc_results = results['processing_results']
        print(f"  • Input Records: {proc_results['input_records']:,}")
        print(f"  • Output Records: {proc_results['output_records']:,}")
        print(f"  • Success Rate: {proc_results['success_rate']:.1f}%")
        print(f"  • Features Used: {', '.join(proc_results['features_used'])}")
        
        # Display quality review results
        if results['quality_review']:
            quality_summary = results['quality_review']['summary']
            print(f"\n🔍 Quality Review Results:")
            print(f"  • Quality Score: {quality_summary['overall_assessment']['quality_score']:.2f}/100")
            print(f"  • System Health: {quality_summary['overall_assessment']['system_health'].upper()}")
            
            findings = quality_summary['key_findings']
            if findings['fake_data_detected']:
                print(f"  • 🚫 Fake data detected")
            if findings['data_completeness_issues']:
                print(f"  • 📉 Data completeness issues")
            if findings['enrichment_problems']:
                print(f"  • 🔍 Enrichment problems")
            
            print(f"  • Total Recommendations: {quality_summary['recommendations_summary']['total_recommendations']}")
            
            # Show markdown report path
            if 'markdown_report_path' in results['quality_review']:
                print(f"  • 📄 Detailed report: {results['quality_review']['markdown_report_path']}")
        
        # Show recommendations
        if results['recommendations']:
            print(f"\n🎯 Immediate Recommendations:")
            for i, rec in enumerate(results['recommendations'][:3], 1):
                print(f"  {i}. {rec}")
        
        # Get quality insights
        print(f"\n📈 Quality Insights:")
        insights = await processor.get_quality_insights()
        if 'latest_review' in insights:
            latest = insights['latest_review']
            print(f"  • Latest Quality Score: {latest['overall_assessment']['quality_score']:.2f}")
            print(f"  • System Health: {latest['overall_assessment']['system_health'].upper()}")
        
        # Show key capabilities
        print(f"\n✨ Review Agent Capabilities Demonstrated:")
        print(f"  ✅ Automatic fake data detection (phones, emails, business names)")
        print(f"  ✅ Data quality scoring and metrics")
        print(f"  ✅ Enrichment completeness analysis")
        print(f"  ✅ Improvement recommendations")
        print(f"  ✅ Detailed markdown reporting")
        print(f"  ✅ Learning and optimization insights")
        
        print(f"\n🎉 Integration demonstration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await processor.close()

if __name__ == "__main__":
    asyncio.run(demonstration())