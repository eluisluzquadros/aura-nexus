# -*- coding: utf-8 -*-
"""
Script rápido para executar AURA NEXUS em modo FULL
Uso: python quick_run_full.py
"""

import subprocess
import sys
import os

def run_full_mode():
    """Executa o framework em modo full"""
    print("\n" + "="*60)
    print("AURA NEXUS - EXECUÇÃO EM MODO FULL")
    print("="*60 + "\n")
    
    # Verificar se o script principal existe
    if not os.path.exists("run_full_validation.py"):
        print("❌ Erro: Script run_full_validation.py não encontrado!")
        return
    
    print("Iniciando validação completa do framework...")
    print("Isso irá:")
    print("✓ Validar todas as configurações")
    print("✓ Testar todas as integrações") 
    print("✓ Processar dados de exemplo")
    print("✓ Gerar relatório completo em XLSX")
    print("✓ Salvar logs detalhados\n")
    
    try:
        # Executar com input automático para teste rápido (3 leads)
        process = subprocess.Popen(
            [sys.executable, "run_full_validation.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Enviar escolha automática (1 = amostra pequena)
        process.stdin.write("1\n")
        process.stdin.flush()
        
        # Ler output em tempo real
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip())
        
        process.wait()
        
        if process.returncode == 0:
            print("\n✅ Execução completa finalizada com sucesso!")
            
            # Verificar se há arquivos gerados
            output_dir = "data/output"
            if os.path.exists(output_dir):
                files = [f for f in os.listdir(output_dir) if f.startswith("validacao_completa_") and f.endswith(".xlsx")]
                if files:
                    latest_file = sorted(files)[-1]
                    print(f"\n📊 Arquivo XLSX gerado: {os.path.join(output_dir, latest_file)}")
                    
                    # Mostrar tamanho do arquivo
                    file_path = os.path.join(output_dir, latest_file)
                    size_kb = os.path.getsize(file_path) / 1024
                    print(f"📏 Tamanho: {size_kb:.1f} KB")
        else:
            print(f"\n❌ Erro na execução. Código de retorno: {process.returncode}")
            
    except Exception as e:
        print(f"\n❌ Erro ao executar: {str(e)}")
        print("\nTentando execução direta...")
        
        # Tentar importar e executar diretamente
        try:
            from run_full_validation import FullFrameworkValidator
            validator = FullFrameworkValidator()
            output_path = validator.run_full_validation(sample_size=3)
            print(f"\n✅ Validação completa! Arquivo: {output_path}")
        except Exception as e2:
            print(f"❌ Erro na execução direta: {str(e2)}")


if __name__ == "__main__":
    run_full_mode()