#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples do sistema Multi-LLM Consensus
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testa se todas as importações funcionam"""
    try:
        from src.core.multi_llm_consensus import (
            MultiLLMConsensus, 
            ConsensusStrategy, 
            KappaCalculator,
            TokenCounter,
            TokenMetrics,
            KappaStatistics,
            ConsensusResult
        )
        print("Todas as importacoes funcionaram")
        return True
    except ImportError as e:
        print(f"Erro de importacao: {e}")
        return False

def test_kappa_calculator():
    """Testa o KappaCalculator"""
    try:
        from src.core.multi_llm_consensus import KappaCalculator
        
        calc = KappaCalculator()
        
        # Teste Cohen's Kappa
        rater1 = [1, 2, 3, 4, 5]
        rater2 = [1, 2, 3, 4, 5]
        kappa = calc.calculate_cohens_kappa(rater1, rater2)
        
        print(f"Cohen's Kappa calculado: {kappa:.3f}")
        
        # Teste Fleiss' Kappa
        ratings_matrix = [[1, 1, 1], [2, 2, 2], [3, 3, 3]]
        fleiss = calc.calculate_fleiss_kappa(ratings_matrix)
        
        print(f"Fleiss' Kappa calculado: {fleiss:.3f}")
        
        return True
    except Exception as e:
        print(f"Erro no KappaCalculator: {e}")
        return False

def test_token_counter():
    """Testa o TokenCounter"""
    try:
        from src.core.multi_llm_consensus import TokenCounter
        
        counter = TokenCounter()
        
        # Teste contagem de tokens
        text = "Hello world, this is a test"
        tokens = counter.count_tokens(text, "gpt-3.5-turbo")
        
        print(f"Tokens contados: {tokens}")
        
        # Teste cálculo de custo
        cost = counter.calculate_cost(100, 50, "openai", "gpt-3.5-turbo")
        
        print(f"Custo calculado: ${cost:.6f}")
        
        return True
    except Exception as e:
        print(f"Erro no TokenCounter: {e}")
        return False

def test_consensus_strategies():
    """Testa as estratégias de consenso"""
    try:
        from src.core.multi_llm_consensus import ConsensusStrategy
        
        strategies = list(ConsensusStrategy)
        print(f"Estrategias disponiveis: {len(strategies)}")
        
        for strategy in strategies:
            print(f"  - {strategy.value}")
        
        return True
    except Exception as e:
        print(f"Erro nas estrategias: {e}")
        return False

def main():
    """Função principal de teste"""
    print("TESTE DE INTEGRACAO SIMPLES")
    print("=" * 40)
    
    tests = [
        ("Importacoes", test_imports),
        ("KappaCalculator", test_kappa_calculator),
        ("TokenCounter", test_token_counter),
        ("ConsensusStrategy", test_consensus_strategies),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nTestando: {test_name}")
        print("-" * 30)
        
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 40)
    print("RESUMO DOS TESTES")
    print("=" * 40)
    
    passed = 0
    for test_name, success in results:
        status = "PASSOU" if success else "FALHOU"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nTestes Aprovados: {passed}/{len(results)}")
    
    if passed == len(results):
        print("TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("ALGUNS TESTES FALHARAM!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)