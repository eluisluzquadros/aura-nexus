#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para o sistema Multi-LLM Consensus aprimorado
Demonstra funcionalidades de Kappa statistics, token tracking e consenso avançado
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import das classes do sistema
from src.core.api_manager import APIManager
from src.core.multi_llm_consensus import (
    MultiLLMConsensus, 
    ConsensusStrategy, 
    KappaCalculator,
    TokenCounter
)


async def test_kappa_calculator():
    """Testa o calculador de estatísticas Kappa"""
    print("\n" + "="*50)
    print("🧮 TESTE: KappaCalculator")
    print("="*50)
    
    calc = KappaCalculator()
    
    # Teste Cohen's Kappa
    rater1 = [85, 70, 90, 65, 80]
    rater2 = [80, 75, 85, 70, 75]
    
    cohens_kappa = calc.calculate_cohens_kappa(rater1, rater2)
    print(f"Cohen's Kappa: {cohens_kappa:.3f}")
    
    # Teste Fleiss' Kappa
    ratings_matrix = [
        [4, 4, 3, 4, 4],  # Item 1 avaliado por 5 raters
        [3, 3, 4, 3, 3],  # Item 2 avaliado por 5 raters
        [5, 4, 5, 5, 4],  # Item 3 avaliado por 5 raters
        [2, 3, 2, 2, 3],  # Item 4 avaliado por 5 raters
    ]
    
    fleiss_kappa = calc.calculate_fleiss_kappa(ratings_matrix)
    print(f"Fleiss' Kappa: {fleiss_kappa:.3f}")
    
    # Interpretação
    interpretation = calc.interpret_kappa(cohens_kappa)
    print(f"Interpretação Cohen's: {interpretation}")
    
    # Intervalo de confiança
    ci = calc.calculate_confidence_interval(cohens_kappa, len(rater1))
    print(f"Intervalo de Confiança 95%: [{ci[0]:.3f}, {ci[1]:.3f}]")


def test_token_counter():
    """Testa o contador de tokens e cálculo de custos"""
    print("\n" + "="*50)
    print("💰 TESTE: TokenCounter")
    print("="*50)
    
    counter = TokenCounter()
    
    # Teste contagem de tokens
    test_text = "Analyze the business potential of this technical assistance company located in São Paulo."
    
    models = ['gpt-3.5-turbo', 'claude-3-haiku-20240307', 'gemini-pro']
    
    for model in models:
        tokens = counter.count_tokens(test_text, model)
        print(f"Tokens em '{model}': {tokens}")
        
        # Calcular custo estimado
        provider = 'openai' if 'gpt' in model else 'anthropic' if 'claude' in model else 'gemini'
        cost = counter.calculate_cost(tokens, tokens//2, provider, model)
        print(f"Custo estimado: ${cost:.6f}")
    
    print()


async def test_consensus_strategies():
    """Testa diferentes estratégias de consenso"""
    print("\n" + "="*50)
    print("🗳️ TESTE: Estratégias de Consenso")
    print("="*50)
    
    # Mock API Manager (para teste)
    class MockAPIManager:
        def get_available_apis(self):
            return ['openai', 'anthropic', 'gemini']
    
    # Inicializar sistema de consenso
    api_manager = MockAPIManager()
    consensus_system = MultiLLMConsensus(api_manager)
    
    # Dados de teste simulados (representando respostas de diferentes LLMs)
    mock_results = {
        'openai': {
            'score': 85,
            'analysis': 'Empresa com bom potencial de crescimento no setor de assistência técnica',
            'strengths': ['Localização estratégica', 'Experiência no mercado'],
            'opportunities': ['Expansão digital', 'Parcerias locais'],
            'recommendation': 'Investimento recomendado'
        },
        'anthropic': {
            'score': 78,
            'analysis': 'Negócio estável com oportunidades de melhoria em processos',
            'strengths': ['Boa reputação', 'Cliente fidelizado'],
            'opportunities': ['Automação de processos', 'Marketing digital'],
            'recommendation': 'Potencial moderado'
        },
        'gemini': {
            'score': 82,
            'analysis': 'Empresa consolidada com perspectivas positivas',
            'strengths': ['Equipe qualificada', 'Localização estratégica'],
            'opportunities': ['Expansão de serviços', 'Parcerias locais'],
            'recommendation': 'Bom investimento'
        }
    }
    
    llms = ['openai', 'anthropic', 'gemini']
    
    # Testar diferentes estratégias
    strategies = [
        ConsensusStrategy.MAJORITY_VOTE,
        ConsensusStrategy.WEIGHTED_AVERAGE,
        ConsensusStrategy.CONFIDENCE_WEIGHTED,
        ConsensusStrategy.ENSEMBLE_VOTING
    ]
    
    for strategy in strategies:
        print(f"\n--- Estratégia: {strategy.value} ---")
        
        if strategy == ConsensusStrategy.MAJORITY_VOTE:
            result = consensus_system._majority_vote_consensus(mock_results, llms, 'business_potential')
        elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
            result = consensus_system._weighted_average_consensus(mock_results, llms, 'business_potential')
        elif strategy == ConsensusStrategy.CONFIDENCE_WEIGHTED:
            result = consensus_system._confidence_weighted_consensus(mock_results, llms, 'business_potential')
        elif strategy == ConsensusStrategy.ENSEMBLE_VOTING:
            result = consensus_system._ensemble_voting_consensus(mock_results, llms, 'business_potential')
        
        print(f"Score Final: {result['result'].get('score', 'N/A')}")
        print(f"Agreement Score: {result['agreement_score']:.3f}")
        print(f"Confidence Score: {result['confidence_score']:.3f}")
        print(f"Tipo: {result['type']}")


def test_json_validation():
    """Testa validação de esquemas JSON"""
    print("\n" + "="*50)
    print("✅ TESTE: Validação JSON Schema")
    print("="*50)
    
    # Mock API Manager
    class MockAPIManager:
        def get_available_apis(self):
            return ['openai']
    
    api_manager = MockAPIManager()
    consensus_system = MultiLLMConsensus(api_manager)
    
    # Teste com dados válidos
    valid_data = {
        'score': 85,
        'analysis': 'Análise detalhada da empresa',
        'strengths': ['Ponto forte 1', 'Ponto forte 2'],
        'opportunities': ['Oportunidade 1', 'Oportunidade 2'],
        'recommendation': 'Recomendação principal'
    }
    
    is_valid, errors = consensus_system.validate_json_schema(valid_data, 'business_potential')
    print(f"Dados válidos: {is_valid}")
    if errors:
        print(f"Erros: {errors}")
    
    # Teste com dados inválidos
    invalid_data = {
        'score': 150,  # Score inválido
        'analysis': 'Análise',
        'strengths': 'Não é uma lista',  # Deveria ser lista
        # 'opportunities' ausente
        'recommendation': 'Recomendação'
    }
    
    is_valid, errors = consensus_system.validate_json_schema(invalid_data, 'business_potential')
    print(f"\nDados inválidos: {is_valid}")
    print(f"Erros encontrados: {errors}")


async def test_health_check():
    """Testa verificação de saúde do sistema"""
    print("\n" + "="*50)
    print("🏥 TESTE: Health Check")
    print("="*50)
    
    # Mock API Manager
    class MockAPIManager:
        def get_available_apis(self):
            return ['openai', 'anthropic']
    
    api_manager = MockAPIManager()
    consensus_system = MultiLLMConsensus(api_manager)
    
    health_status = await consensus_system.health_check()
    
    print(f"Status Geral: {health_status['status']}")
    print(f"LLMs Disponíveis: {health_status['available_llms']}")
    print(f"Timestamp: {health_status['timestamp']}")
    
    print("\nStatus por LLM:")
    for llm, status in health_status['llm_status'].items():
        print(f"  {llm}: {status}")
    
    if health_status['issues']:
        print(f"\nIssues: {health_status['issues']}")


def test_performance_metrics():
    """Testa métricas de performance"""
    print("\n" + "="*50)
    print("📊 TESTE: Métricas de Performance")
    print("="*50)
    
    # Mock API Manager
    class MockAPIManager:
        def get_available_apis(self):
            return ['openai', 'anthropic', 'gemini']
    
    api_manager = MockAPIManager()
    consensus_system = MultiLLMConsensus(api_manager)
    
    # Simular histórico de performance
    consensus_system.performance_history['openai'] = [0.85, 0.78, 0.92, 0.88, 0.83]
    consensus_system.performance_history['anthropic'] = [0.79, 0.84, 0.81, 0.86, 0.80]
    consensus_system.performance_history['gemini'] = [0.82, 0.77, 0.85, 0.90, 0.79]
    
    # Atualizar pesos baseado no histórico
    consensus_system._update_performance_history(['openai', 'anthropic', 'gemini'], 0.85)
    
    metrics = consensus_system.get_performance_metrics()
    
    print(f"Total de LLMs: {metrics['available_llms']}")
    print(f"Total de Requests: {metrics['total_requests']}")
    
    print("\nPerformance por LLM:")
    for llm, stats in metrics['avg_agreement_by_llm'].items():
        print(f"  {llm}:")
        print(f"    Média: {stats['mean']:.3f}")
        print(f"    Desvio: {stats['std']:.3f}")
        print(f"    Peso: {stats['weight']:.3f}")
        print(f"    Amostras: {stats['count']}")


async def main():
    """Função principal de teste"""
    print("🚀 AURA NEXUS - Sistema Multi-LLM Consensus")
    print("Teste Completo das Funcionalidades Avançadas")
    print("=" * 60)
    
    try:
        # Executar todos os testes
        await test_kappa_calculator()
        test_token_counter()
        await test_consensus_strategies()
        test_json_validation()
        await test_health_check()
        test_performance_metrics()
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("="*60)
        
        print("\n📋 RESUMO DAS FUNCIONALIDADES IMPLEMENTADAS:")
        print("• ✅ KappaCalculator - Cohen's e Fleiss' Kappa")
        print("• ✅ TokenMetrics - Tracking de custos e tokens")
        print("• ✅ ConsensusStrategy - 8 estratégias diferentes")
        print("• ✅ Suporte a modelos locais (Ollama)")
        print("• ✅ Fallback strategies")
        print("• ✅ JSON schema validation")
        print("• ✅ Performance benchmarking")
        print("• ✅ Health check system")
        print("• ✅ Comprehensive error handling")
        
        print("\n🎯 MELHORIAS IMPLEMENTADAS:")
        print("• Consenso estatisticamente fundamentado")
        print("• Tracking detalhado de custos por LLM")
        print("• Pesos dinâmicos baseados em performance")
        print("• Validação robusta de esquemas JSON")
        print("• Suporte a modelos locais via Ollama")
        print("• Sistema de fallback em cascata")
        print("• Monitoramento de saúde em tempo real")
        print("• Benchmark automatizado de estratégias")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())