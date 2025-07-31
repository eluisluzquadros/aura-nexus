#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AURA NEXUS - Script Principal de Processamento de Leads
Versão corrigida que processa 100% dos leads e executa todas as features
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import AuraNexusOrchestrator
from src.infrastructure.checkpoint_manager import CheckpointManager
from src.utils import setup_logging

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logger = setup_logging("AURA_NEXUS")


class LeadProcessorCLI:
    """Interface de linha de comando para processar leads"""
    
    def __init__(self):
        self.orchestrator = None
        self.checkpoint_manager = None
        
    def parse_args(self):
        """Parse argumentos da linha de comando"""
        parser = argparse.ArgumentParser(
            description="AURA NEXUS - Sistema Avançado de Enriquecimento de Leads"
        )
        
        # Argumentos principais
        parser.add_argument(
            "--input", "-i",
            type=str,
            required=True,
            help="Caminho do arquivo Excel com leads"
        )
        
        parser.add_argument(
            "--output", "-o",
            type=str,
            help="Caminho do arquivo de saída (padrão: input_enriched.xlsx)"
        )
        
        parser.add_argument(
            "--mode", "-m",
            type=str,
            choices=["basic", "full_strategy", "premium"],
            default="basic",
            help="Modo de processamento (padrão: basic)"
        )
        
        # Flags de controle
        parser.add_argument(
            "--force-all",
            action="store_true",
            help="Força processamento de TODOS os leads, mesmo já enriquecidos"
        )
        
        parser.add_argument(
            "--skip-google-only",
            action="store_true",
            help="Pula apenas Google Maps API para leads já enriquecidos"
        )
        
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5,
            help="Tamanho do batch para processamento (padrão: 5)"
        )
        
        parser.add_argument(
            "--max-workers",
            type=int,
            default=3,
            help="Número máximo de workers paralelos (padrão: 3)"
        )
        
        parser.add_argument(
            "--resume",
            action="store_true",
            help="Retoma processamento do último checkpoint"
        )
        
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Ativa modo debug com logs detalhados"
        )
        
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula processamento sem fazer chamadas reais"
        )
        
        return parser.parse_args()
    
    async def initialize(self, args):
        """Inicializa componentes do sistema"""
        # Configuração baseada nos argumentos
        config = {
            "mode": args.mode,
            "batch_size": args.batch_size,
            "max_workers": args.max_workers,
            "force_process_all": args.force_all,
            "skip_google_only": args.skip_google_only,
            "debug": args.debug,
            "dry_run": args.dry_run,
            
            # Features por modo (CORRIGIDO)
            "feature_modes": {
                "basic": [
                    "google_details",      # Dados básicos Google Maps
                    "google_cse",          # Google Search - descoberta de links
                    "web_scraping",        # Crawl4AI - extração de contatos
                    "social_scraping",     # Apify - Instagram/Facebook
                    "contact_extraction"   # Consolidação de contatos
                ],
                "full_strategy": [
                    # Todas do basic +
                    "google_details",
                    "google_cse",
                    "web_scraping",
                    "social_scraping",
                    "contact_extraction",
                    "reviews_analysis",    # Análise de avaliações
                    "competitor_analysis", # Identificação de concorrentes
                    "ai_analysis",         # Multi-LLM para insights
                    "sales_approach",      # Estratégias de venda
                    "discovery_cycle",     # Busca profunda recursiva
                    "advanced_metrics"     # Métricas de consenso
                ],
                "premium": [
                    # Todas do full_strategy +
                    "google_details",
                    "google_cse",
                    "web_scraping",
                    "social_scraping",
                    "contact_extraction",
                    "reviews_analysis",
                    "competitor_analysis",
                    "ai_analysis",
                    "sales_approach",
                    "discovery_cycle",
                    "advanced_metrics",
                    "facade_analysis"      # Google Street View (opcional)
                ]
            },
            
            # Diretórios
            "data_dir": Path("data"),
            "cache_dir": Path("data/cache"),
            "checkpoint_dir": Path("data/checkpoints"),
            "output_dir": Path("data/output")
        }
        
        # Cria diretórios necessários
        for dir_key in ["data_dir", "cache_dir", "checkpoint_dir", "output_dir"]:
            config[dir_key].mkdir(parents=True, exist_ok=True)
        
        # Inicializa componentes
        logger.info("🚀 Inicializando AURA NEXUS...")
        
        self.orchestrator = AuraNexusOrchestrator(config)
        await self.orchestrator.initialize()
        
        if args.resume:
            self.checkpoint_manager = CheckpointManager(config["checkpoint_dir"])
            
        logger.info("✅ Sistema inicializado com sucesso!")
        
    def load_leads(self, input_path: str) -> pd.DataFrame:
        """Carrega planilha de leads"""
        logger.info(f"📂 Carregando leads de: {input_path}")
        
        if not Path(input_path).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
        
        df = pd.read_excel(input_path)
        logger.info(f"✅ {len(df)} leads carregados")
        
        return df
    
    def save_results(self, results: pd.DataFrame, output_path: str):
        """Salva resultados enriquecidos"""
        logger.info(f"💾 Salvando resultados em: {output_path}")
        
        # Garante que o diretório existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Salva com formatação
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            results.to_excel(writer, sheet_name='Leads Enriquecidos', index=False)
            
            # Auto-ajusta largura das colunas
            worksheet = writer.sheets['Leads Enriquecidos']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"✅ Resultados salvos com sucesso!")
    
    async def process(self, args):
        """Processa leads com as configurações especificadas"""
        try:
            # Inicializa sistema
            await self.initialize(args)
            
            # Carrega leads
            leads_df = self.load_leads(args.input)
            
            # Define arquivo de saída
            if not args.output:
                input_path = Path(args.input)
                args.output = str(
                    input_path.parent / f"{input_path.stem}_enriched_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
                )
            
            logger.info(f"🔄 Iniciando processamento em modo: {args.mode.upper()}")
            logger.info(f"📊 Features ativas: {len(self.orchestrator.config['feature_modes'][args.mode])}")
            
            # Processa leads
            results = await self.orchestrator.process_leads(
                leads_df,
                checkpoint_enabled=args.resume
            )
            
            # Salva resultados
            self.save_results(results, args.output)
            
            # Exibe estatísticas
            stats = self.orchestrator.get_statistics()
            logger.info("\n📊 ESTATÍSTICAS FINAIS:")
            logger.info(f"   Total processados: {stats['total']}")
            logger.info(f"   ✅ Sucesso: {stats['successful']} ({stats['success_rate']:.1f}%)")
            logger.info(f"   ❌ Falhas: {stats['failed']}")
            logger.info(f"   ⚡ Do cache: {stats['cached']}")
            logger.info(f"   ⏱️ Tempo total: {stats['processing_time']:.2f}s")
            logger.info(f"   📍 Média por lead: {stats['avg_time_per_lead']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro durante processamento: {str(e)}")
            if args.debug:
                import traceback
                traceback.print_exc()
            raise
    
    async def run(self):
        """Executa o processador"""
        args = self.parse_args()
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        try:
            await self.process(args)
            logger.info("\n✨ Processamento concluído com sucesso!")
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Processamento interrompido pelo usuário")
            
        except Exception as e:
            logger.error(f"\n❌ Erro fatal: {str(e)}")
            sys.exit(1)


def main():
    """Função principal"""
    # Necessário para Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Executa CLI
    cli = LeadProcessorCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()