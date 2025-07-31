# -*- coding: utf-8 -*-
"""
AURA NEXUS - Adaptador de Planilhas
Mapeia diferentes formatos de planilha para o formato padrão do sistema
"""

import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("AURA_NEXUS.SpreadsheetAdapter")


class SpreadsheetAdapter:
    """Adapta diferentes formatos de planilha para o formato esperado pelo sistema"""
    
    # Mapeamento de colunas conhecidas
    COLUMN_MAPPINGS = {
        # Formato base-leads_amostra_v2
        'name': 'nome_empresa',
        'tradeName': 'nome_fantasia',
        'legalDocument': 'cnpj',
        'street': 'endereco',
        'number': 'numero',
        'complement': 'complemento',
        'district': 'bairro',
        'postalCode': 'cep',
        'city': 'cidade',
        'state': 'estado',
        'country': 'pais',
        'email': 'email',
        'phone': 'telefone',
        'mobilePhone': 'celular',
        'website': 'website',
        'observations': 'observacoes',
        
        # Dados do Google Places
        'placesId': 'gdr_google_place_id',
        'placesRating': 'gdr_google_rating',
        'placesMaps': 'gdr_google_maps_url',
        'placesLat': 'gdr_latitude',
        'placesLng': 'gdr_longitude',
        'placesUserRatingsTotal': 'gdr_total_avaliacoes',
        'placesPhone': 'gdr_telefone_google',
        'placesWebsite': 'gdr_website_google',
        'placesThumb': 'gdr_google_thumb',
        
        # Redes sociais
        'instagramUrl': 'gdr_instagram_url',
        'facebookUrl': 'gdr_facebook_url',
        'linkedinUrl': 'gdr_linkedin_url',
        
        # Classificação
        'classificationInfo': 'gdr_classificacao',
        
        # Status
        'status': 'status_original',
        'statusDate': 'status_data',
        'statusUser': 'status_usuario'
    }
    
    def adapt_spreadsheet(self, file_path: str) -> pd.DataFrame:
        """
        Adapta planilha para formato padrão
        
        Args:
            file_path: Caminho do arquivo Excel
            
        Returns:
            DataFrame com colunas padronizadas
        """
        logger.info(f"📂 Adaptando planilha: {file_path}")
        
        # Carregar planilha
        df = pd.read_excel(file_path)
        logger.info(f"✅ {len(df)} registros carregados")
        
        # Criar novo DataFrame com colunas mapeadas
        adapted_df = pd.DataFrame()
        
        # Mapear colunas conhecidas
        for old_col, new_col in self.COLUMN_MAPPINGS.items():
            if old_col in df.columns:
                adapted_df[new_col] = df[old_col]
                logger.debug(f"   Mapeado: {old_col} → {new_col}")
        
        # Preservar colunas não mapeadas com prefixo
        for col in df.columns:
            if col not in self.COLUMN_MAPPINGS:
                adapted_df[f'original_{col}'] = df[col]
        
        # Adicionar colunas derivadas
        self._add_derived_columns(adapted_df)
        
        # Marcar leads que já têm dados do Google
        adapted_df['gdr_ja_enriquecido_google'] = adapted_df['gdr_google_place_id'].notna()
        
        logger.info(f"✅ Planilha adaptada com {len(adapted_df.columns)} colunas")
        logger.info(f"   • Colunas mapeadas: {sum(1 for col in adapted_df.columns if not col.startswith('original_'))}")
        logger.info(f"   • Colunas originais preservadas: {sum(1 for col in adapted_df.columns if col.startswith('original_'))}")
        logger.info(f"   • Leads com Google ID: {adapted_df['gdr_ja_enriquecido_google'].sum()}")
        
        return adapted_df
    
    def _add_derived_columns(self, df: pd.DataFrame):
        """Adiciona colunas derivadas e consolidadas"""
        
        # Endereço completo
        address_parts = []
        for col in ['endereco', 'numero', 'complemento']:
            if col in df.columns:
                address_parts.append(df[col].astype(str))
        
        if address_parts:
            df['endereco_completo'] = df.apply(
                lambda row: ' '.join(
                    str(row.get(col, '')).strip() 
                    for col in ['endereco', 'numero', 'complemento'] 
                    if col in df.columns and pd.notna(row.get(col))
                ),
                axis=1
            )
        
        # Telefone consolidado (preferência: celular > telefone > google)
        df['gdr_telefone_consolidado'] = df.apply(
            lambda row: (
                row.get('celular') if pd.notna(row.get('celular')) else
                row.get('telefone') if pd.notna(row.get('telefone')) else
                row.get('gdr_telefone_google', None)
            ),
            axis=1
        )
        
        # Website consolidado (preferência: website original > google)
        df['gdr_website_consolidado'] = df.apply(
            lambda row: (
                row.get('website') if pd.notna(row.get('website')) else
                row.get('gdr_website_google', None)
            ),
            axis=1
        )
        
        # CNPJ/CPF unificado
        if 'cnpj' in df.columns:
            df['gdr_cnpj_cpf'] = df['cnpj']
    
    def merge_enriched_data(self, original_df: pd.DataFrame, enriched_df: pd.DataFrame) -> pd.DataFrame:
        """
        Mescla dados enriquecidos com dados originais
        
        Args:
            original_df: DataFrame original adaptado
            enriched_df: DataFrame com dados enriquecidos
            
        Returns:
            DataFrame mesclado preservando todos os dados
        """
        if 'gdr_id_processamento' not in enriched_df.columns:
            logger.warning("⚠️ Coluna gdr_id_processamento não encontrada")
            return original_df
        
        # Fazer merge
        merged = pd.merge(
            original_df,
            enriched_df,
            on='gdr_id_processamento',
            how='left',
            suffixes=('', '_enriched')
        )
        
        # Atualizar colunas enriquecidas
        for col in enriched_df.columns:
            if col != 'gdr_id_processamento' and col + '_enriched' in merged.columns:
                # Usar valor enriquecido se disponível
                merged[col] = merged[col + '_enriched'].fillna(merged.get(col, pd.NA))
                merged.drop(col + '_enriched', axis=1, inplace=True)
        
        return merged