# -*- coding: utf-8 -*-
"""
AURA NEXUS - Comprehensive Review Agent v2.0
AI Quality Assurance specialist for analyzing processing results,
detecting quality issues, and creating improvement plans.
"""

import asyncio
import json
import logging
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from pathlib import Path
import phonenumbers
import validators
from urllib.parse import urlparse
import statistics

# Configure logger
logger = logging.getLogger("AURA_NEXUS.ReviewAgent")

# ===================================================================================
# DATA MODELS
# ===================================================================================

@dataclass
class QualityIssue:
    """Represents a data quality issue"""
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'fake_data', 'invalid_format', 'missing_data', 'inconsistency'
    field: str
    issue_type: str
    description: str
    value: Optional[str] = None
    suggestion: Optional[str] = None
    confidence: float = 1.0
    record_id: Optional[str] = None

@dataclass
class QualityMetrics:
    """Quality assessment metrics"""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    enrichment_score: float
    fake_data_percentage: float
    total_records: int
    valid_records: int
    issues_by_severity: Dict[str, int]
    improvement_areas: List[str]

@dataclass
class ImprovementRecommendation:
    """System improvement recommendation"""
    priority: str  # 'critical', 'high', 'medium', 'low'
    category: str
    title: str
    description: str
    action_items: List[str]
    estimated_impact: str
    implementation_complexity: str
    code_changes_needed: List[str]

# ===================================================================================
# CLASS: DataQualityAnalyzer
# ===================================================================================

class DataQualityAnalyzer:
    """Analyzes data quality and detects fake/invalid data"""
    
    def __init__(self):
        self.fake_patterns = self._initialize_fake_patterns()
        self.validation_rules = self._initialize_validation_rules()
        self.quality_thresholds = {
            'min_phone_length': 10,
            'max_phone_length': 15,
            'email_domain_blacklist': ['example.com', 'test.com', 'fake.com'],
            'suspicious_name_patterns': [r'^test', r'^fake', r'^dummy', r'^\d+$'],
            'min_business_name_length': 2,
            'max_repetitive_chars': 3
        }
    
    def _initialize_fake_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting fake data"""
        return {
            'fake_phones': [
                r'^(11)\1{9}$',  # 11111111111 (exactly 11 same digits)
                r'^(22)\1{9}$',  # 22222222222 (exactly 11 same digits)
                r'^(33)\1{9}$',  # etc.
                r'^(44)\1{9}$',
                r'^(55)\1{9}$',
                r'^123456789\d*$',
                r'^987654321\d*$',
                r'^000000000\d*$',
                r'^999999999\d*$',
                r'^(\d)\1{10,}$',  # Any digit repeated 11+ times
            ],
            'fake_emails': [
                r'test@test\.com',
                r'fake@fake\.com',
                r'example@example\.com',
                r'dummy@dummy\.com',
                r'noemail@noemail\.com',
                r'notfound@notfound\.com',
                r'\d+@\d+\.com',  # All numbers
                r'[a-z]@[a-z]\.com',  # Single char domains
            ],
            'fake_names': [
                r'^test\s*(company|empresa|negocio)?$',
                r'^fake\s*(company|empresa|negocio)?$',
                r'^dummy\s*(company|empresa|negocio)?$',
                r'^example\s*(company|empresa|negocio)?$',
                r'^cliente\s*\d+$',
                r'^empresa\s*\d+$',
                r'^negocio\s*\d+$',
                r'^\d+$',  # Only numbers
                r'^[a-z]$',  # Single character
            ],
            'fake_websites': [
                r'example\.com',
                r'test\.com',
                r'fake\.com',
                r'dummy\.com',
                r'notfound\.com',
                r'^\w+\.com$',  # Single word domains
            ]
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for different data types"""
        return {
            'phone': {
                'required_patterns': [r'^\+?[\d\s\-\(\)]+$'],
                'invalid_patterns': self.fake_patterns['fake_phones'],
                'min_length': 10,
                'max_length': 15,
                'validator': self._validate_phone_advanced
            },
            'email': {
                'required_patterns': [r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'],
                'invalid_patterns': self.fake_patterns['fake_emails'],
                'validator': self._validate_email_advanced
            },
            'business_name': {
                'invalid_patterns': self.fake_patterns['fake_names'],
                'min_length': 2,
                'max_repetitive_chars': 3,
                'validator': self._validate_business_name
            },
            'website': {
                'required_patterns': [r'^https?://'],
                'invalid_patterns': self.fake_patterns['fake_websites'],
                'validator': self._validate_website_advanced
            },
            'social_url': {
                'platforms': ['instagram', 'facebook', 'linkedin', 'twitter', 'tiktok'],
                'validator': self._validate_social_url_advanced
            }
        }
    
    async def analyze_data_quality(self, df: pd.DataFrame) -> Tuple[QualityMetrics, List[QualityIssue]]:
        """
        Comprehensive data quality analysis
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Tuple of quality metrics and list of issues
        """
        logger.info("🔍 Starting comprehensive data quality analysis...")
        
        issues = []
        total_records = len(df)
        
        # 1. Detect fake data
        fake_issues = await self._detect_fake_data(df)
        issues.extend(fake_issues)
        
        # 2. Validate data formats
        format_issues = await self._validate_data_formats(df)
        issues.extend(format_issues)
        
        # 3. Check data completeness
        completeness_issues = await self._check_completeness(df)
        issues.extend(completeness_issues)
        
        # 4. Analyze data consistency
        consistency_issues = await self._analyze_consistency(df)
        issues.extend(consistency_issues)
        
        # 5. Evaluate enrichment quality
        enrichment_issues = await self._evaluate_enrichment_quality(df)
        issues.extend(enrichment_issues)
        
        # Calculate metrics
        metrics = self._calculate_quality_metrics(df, issues)
        
        logger.info(f"✅ Analysis complete: {len(issues)} issues found, "
                   f"Quality score: {metrics.overall_score:.2f}")
        
        return metrics, issues
    
    async def _detect_fake_data(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect fake or invalid data entries"""
        issues = []
        
        # Check phone numbers
        phone_columns = [col for col in df.columns if 'telefone' in col.lower() or 'phone' in col.lower() or 'whatsapp' in col.lower()]
        for col in phone_columns:
            for idx, value in df[col].items():
                if pd.notna(value) and str(value).strip():
                    if self._is_fake_phone(str(value)):
                        issues.append(QualityIssue(
                            severity='high',
                            category='fake_data',
                            field=col,
                            issue_type='fake_phone',
                            description=f'Fake phone number detected: {value}',
                            value=str(value),
                            suggestion='Remove fake phone number and re-extract contacts',
                            record_id=str(idx)
                        ))
        
        # Check email addresses
        email_columns = [col for col in df.columns if 'email' in col.lower()]
        for col in email_columns:
            for idx, value in df[col].items():
                if pd.notna(value) and str(value).strip():
                    if self._is_fake_email(str(value)):
                        issues.append(QualityIssue(
                            severity='high',
                            category='fake_data',
                            field=col,
                            issue_type='fake_email',
                            description=f'Fake email detected: {value}',
                            value=str(value),
                            suggestion='Remove fake email and re-extract contacts',
                            record_id=str(idx)
                        ))
        
        # Check business names
        name_columns = [col for col in df.columns if 'nome' in col.lower() or 'name' in col.lower()]
        for col in name_columns:
            for idx, value in df[col].items():
                if pd.notna(value) and str(value).strip():
                    if self._is_fake_business_name(str(value)):
                        issues.append(QualityIssue(
                            severity='medium',
                            category='fake_data',
                            field=col,
                            issue_type='fake_business_name',
                            description=f'Suspicious business name: {value}',
                            value=str(value),
                            suggestion='Review and validate business name',
                            record_id=str(idx)
                        ))
        
        # Check websites
        website_columns = [col for col in df.columns if 'website' in col.lower() or 'site' in col.lower()]
        for col in website_columns:
            for idx, value in df[col].items():
                if pd.notna(value) and str(value).strip():
                    if self._is_fake_website(str(value)):
                        issues.append(QualityIssue(
                            severity='medium',
                            category='fake_data',
                            field=col,
                            issue_type='fake_website',
                            description=f'Suspicious website: {value}',
                            value=str(value),
                            suggestion='Validate website URL',
                            record_id=str(idx)
                        ))
        
        return issues
    
    def _is_fake_phone(self, phone: str) -> bool:
        """Check if phone number is fake"""
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Check for too short/long first
        if len(clean_phone) < self.quality_thresholds['min_phone_length'] or \
           len(clean_phone) > self.quality_thresholds['max_phone_length']:
            return True
        
        # Check against fake patterns (but be less aggressive)
        for pattern in self.fake_patterns['fake_phones']:
            if re.search(pattern, clean_phone):
                return True
        
        # Check for repetitive patterns (only if very repetitive)
        if len(set(clean_phone)) <= 2 and len(clean_phone) >= 10:  # Only 1-2 unique digits in long numbers
            return True
        
        return False
    
    def _is_fake_email(self, email: str) -> bool:
        """Check if email is fake"""
        email_lower = email.lower().strip()
        
        # Check against fake patterns
        for pattern in self.fake_patterns['fake_emails']:
            if re.search(pattern, email_lower, re.IGNORECASE):
                return True
        
        # Check blacklisted domains
        domain = email_lower.split('@')[-1] if '@' in email_lower else ''
        if domain in self.quality_thresholds['email_domain_blacklist']:
            return True
        
        # Basic format validation
        if not validators.email(email):
            return True
        
        return False
    
    def _is_fake_business_name(self, name: str) -> bool:
        """Check if business name is fake"""
        name_lower = name.lower().strip()
        
        # Check minimum length first
        if len(name_lower) < self.quality_thresholds['min_business_name_length']:
            return True
        
        # Check against fake patterns (more specific)
        fake_keywords = ['test', 'fake', 'dummy', 'example']
        for keyword in fake_keywords:
            if name_lower.startswith(keyword + ' ') or name_lower == keyword:
                return True
        
        # Check if it's only numbers
        if name_lower.isdigit():
            return True
        
        # Check for excessive repetitive characters (but allow normal repetition)
        for char in set(name_lower):
            if char.isalnum() and name_lower.count(char) > 5:
                return True
        
        return False
    
    def _is_fake_website(self, website: str) -> bool:
        """Check if website is fake"""
        website_lower = website.lower().strip()
        
        # Check against fake patterns
        for pattern in self.fake_patterns['fake_websites']:
            if re.search(pattern, website_lower, re.IGNORECASE):
                return True
        
        # Basic URL validation
        if not validators.url(website):
            return True
        
        return False
    
    async def _validate_data_formats(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Validate data formats"""
        issues = []
        
        # Validate scores
        score_columns = [col for col in df.columns if 'score' in col.lower()]
        for col in score_columns:
            for idx, value in df[col].items():
                if pd.notna(value):
                    try:
                        score_val = float(value)
                        if not (0 <= score_val <= 100):
                            issues.append(QualityIssue(
                                severity='high',
                                category='invalid_format',
                                field=col,
                                issue_type='invalid_score_range',
                                description=f'Score {score_val} out of valid range (0-100)',
                                value=str(value),
                                suggestion='Adjust score to valid range or investigate calculation',
                                record_id=str(idx)
                            ))
                    except ValueError:
                        issues.append(QualityIssue(
                            severity='high',
                            category='invalid_format',
                            field=col,
                            issue_type='invalid_score_format',
                            description=f'Score value is not numeric: {value}',
                            value=str(value),
                            suggestion='Convert to numeric value',
                            record_id=str(idx)
                        ))
        
        return issues
    
    async def _check_completeness(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Check data completeness"""
        issues = []
        
        # Define critical fields
        critical_fields = ['gdr_nome', 'gdr_score_sinergia']
        important_fields = ['gdr_telefone_1', 'gdr_email_1', 'gdr_website']
        
        for field in critical_fields:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                if missing_count > 0:
                    issues.append(QualityIssue(
                        severity='critical',
                        category='missing_data',
                        field=field,
                        issue_type='missing_critical_data',
                        description=f'{missing_count} records missing critical field {field}',
                        suggestion='Ensure all critical fields are populated',
                        confidence=1.0
                    ))
        
        for field in important_fields:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                missing_percentage = (missing_count / len(df)) * 100
                if missing_percentage > 50:
                    issues.append(QualityIssue(
                        severity='medium',
                        category='missing_data',
                        field=field,
                        issue_type='high_missing_rate',
                        description=f'{missing_percentage:.1f}% of records missing {field}',
                        suggestion='Improve data collection for this field',
                        confidence=0.8
                    ))
        
        return issues
    
    async def _analyze_consistency(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Analyze data consistency"""
        issues = []
        
        # Check for duplicate business names with different data
        if 'gdr_nome' in df.columns:
            name_groups = df.groupby('gdr_nome')
            for name, group in name_groups:
                if len(group) > 1:
                    # Check if they have different contact info (possible duplicates)
                    if 'gdr_telefone_1' in df.columns:
                        unique_phones = group['gdr_telefone_1'].dropna().nunique()
                        if unique_phones > 1:
                            issues.append(QualityIssue(
                                severity='medium',
                                category='inconsistency',
                                field='gdr_nome',
                                issue_type='duplicate_name_different_data',
                                description=f'Business "{name}" has {unique_phones} different phone numbers',
                                suggestion='Review for potential duplicates or multiple locations',
                                confidence=0.7
                            ))
        
        return issues
    
    async def _evaluate_enrichment_quality(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Evaluate enrichment quality"""
        issues = []
        
        # Check if enrichment fields are populated
        enrichment_fields = {
            'gdr_url_instagram': 'Instagram scraping',
            'gdr_url_facebook': 'Facebook scraping',
            'gdr_insta_followers': 'Instagram followers',
            'gdr_fb_followers': 'Facebook followers',
            'gdr_analise_reviews': 'Review analysis'
        }
        
        for field, description in enrichment_fields.items():
            if field in df.columns:
                filled_count = df[field].notna().sum()
                filled_percentage = (filled_count / len(df)) * 100
                
                if filled_percentage < 10:  # Less than 10% enriched
                    issues.append(QualityIssue(
                        severity='medium',
                        category='missing_data',
                        field=field,
                        issue_type='low_enrichment_rate',
                        description=f'Only {filled_percentage:.1f}% enriched with {description}',
                        suggestion=f'Check and configure {description} properly',
                        confidence=0.9
                    ))
        
        return issues
    
    def _calculate_quality_metrics(self, df: pd.DataFrame, issues: List[QualityIssue]) -> QualityMetrics:
        """Calculate comprehensive quality metrics"""
        total_records = len(df)
        
        # Count issues by severity
        issues_by_severity = Counter(issue.severity for issue in issues)
        
        # Calculate fake data percentage
        fake_issues = [issue for issue in issues if issue.category == 'fake_data']
        fake_data_percentage = (len(fake_issues) / total_records * 100) if total_records > 0 else 0
        
        # Calculate scores
        overall_score = self._calculate_overall_score(issues_by_severity, total_records)
        completeness_score = self._calculate_completeness_score(df)
        accuracy_score = self._calculate_accuracy_score(issues, total_records)
        consistency_score = self._calculate_consistency_score(issues, total_records)
        enrichment_score = self._calculate_enrichment_score(df)
        
        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(issues)
        
        return QualityMetrics(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            enrichment_score=enrichment_score,
            fake_data_percentage=fake_data_percentage,
            total_records=total_records,
            valid_records=total_records - len(fake_issues),
            issues_by_severity=dict(issues_by_severity),
            improvement_areas=improvement_areas
        )
    
    def _calculate_overall_score(self, issues_by_severity: Counter, total_records: int) -> float:
        """Calculate overall quality score"""
        base_score = 100.0
        
        # Penalties by severity
        penalties = {
            'critical': 20,
            'high': 10,
            'medium': 5,
            'low': 1
        }
        
        for severity, count in issues_by_severity.items():
            penalty = penalties.get(severity, 0)
            base_score -= (count * penalty) / max(total_records, 1) * 100
        
        return max(0, min(100, base_score))
    
    def _calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate data completeness score"""
        important_fields = [
            'gdr_nome', 'gdr_score_sinergia', 'gdr_telefone_1',
            'gdr_email_1', 'gdr_website', 'gdr_url_instagram'
        ]
        
        if not important_fields:
            return 100.0
        
        total_cells = 0
        filled_cells = 0
        
        for field in important_fields:
            if field in df.columns:
                total_cells += len(df)
                filled_cells += df[field].notna().sum()
        
        return (filled_cells / total_cells * 100) if total_cells > 0 else 0
    
    def _calculate_accuracy_score(self, issues: List[QualityIssue], total_records: int) -> float:
        """Calculate data accuracy score"""
        accuracy_issues = [issue for issue in issues if issue.category in ['fake_data', 'invalid_format']]
        accuracy_rate = max(0, 100 - (len(accuracy_issues) / max(total_records, 1) * 100))
        return accuracy_rate
    
    def _calculate_consistency_score(self, issues: List[QualityIssue], total_records: int) -> float:
        """Calculate data consistency score"""
        consistency_issues = [issue for issue in issues if issue.category == 'inconsistency']
        consistency_rate = max(0, 100 - (len(consistency_issues) / max(total_records, 1) * 100))
        return consistency_rate
    
    def _calculate_enrichment_score(self, df: pd.DataFrame) -> float:
        """Calculate enrichment quality score"""
        enrichment_fields = [
            'gdr_url_instagram', 'gdr_url_facebook', 'gdr_insta_followers',
            'gdr_fb_followers', 'gdr_analise_reviews'
        ]
        
        total_possible = len(df) * len(enrichment_fields)
        total_enriched = 0
        
        for field in enrichment_fields:
            if field in df.columns:
                total_enriched += df[field].notna().sum()
        
        return (total_enriched / total_possible * 100) if total_possible > 0 else 0
    
    def _identify_improvement_areas(self, issues: List[QualityIssue]) -> List[str]:
        """Identify key areas for improvement"""
        category_counts = Counter(issue.category for issue in issues)
        issue_type_counts = Counter(issue.issue_type for issue in issues)
        
        areas = []
        
        # Top categories
        for category, count in category_counts.most_common(3):
            if count > 0:
                areas.append(f"{category.replace('_', ' ').title()} ({count} issues)")
        
        # Top specific issues
        for issue_type, count in issue_type_counts.most_common(2):
            if count > 0:
                areas.append(f"{issue_type.replace('_', ' ').title()} ({count} cases)")
        
        return areas[:5]  # Limit to top 5 areas
    
    # Advanced validation methods
    def _validate_phone_advanced(self, phone: str) -> bool:
        """Advanced phone validation"""
        if not phone or self._is_fake_phone(phone):
            return False
        
        try:
            # Try to parse with phonenumbers library
            parsed = phonenumbers.parse(phone, "BR")
            return phonenumbers.is_valid_number(parsed)
        except:
            # Fallback to basic validation
            clean_phone = re.sub(r'[^\d]', '', phone)
            return 10 <= len(clean_phone) <= 15
    
    def _validate_email_advanced(self, email: str) -> bool:
        """Advanced email validation"""
        if not email or self._is_fake_email(email):
            return False
        return validators.email(email)
    
    def _validate_business_name(self, name: str) -> bool:
        """Validate business name"""
        if not name or self._is_fake_business_name(name):
            return False
        return len(name.strip()) >= 2
    
    def _validate_website_advanced(self, website: str) -> bool:
        """Advanced website validation"""
        if not website or self._is_fake_website(website):
            return False
        return validators.url(website)
    
    def _validate_social_url_advanced(self, url: str) -> bool:
        """Advanced social URL validation"""
        if not url or not validators.url(url):
            return False
        
        social_patterns = {
            'instagram': r'instagram\.com/[\w\-\.]+',
            'facebook': r'facebook\.com/[\w\-\.]+',
            'linkedin': r'linkedin\.com/(company|in)/[\w\-]+',
            'twitter': r'(twitter|x)\.com/[\w]+',
            'tiktok': r'tiktok\.com/@[\w\-\.]+'
        }
        
        return any(re.search(pattern, url, re.IGNORECASE) 
                  for pattern in social_patterns.values())


# ===================================================================================
# CLASS: ResultReviewer
# ===================================================================================

class ResultReviewer:
    """Reviews and analyzes processing results comprehensively"""
    
    def __init__(self, data_analyzer: DataQualityAnalyzer):
        self.data_analyzer = data_analyzer
        self.review_history = []
    
    async def review_processing_results(self, 
                                      results_df: pd.DataFrame,
                                      original_df: pd.DataFrame = None,
                                      processing_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive review of processing results
        
        Args:
            results_df: Processed results DataFrame
            original_df: Original data before processing (optional)
            processing_config: Configuration used for processing (optional)
            
        Returns:
            Comprehensive review report
        """
        logger.info("📋 Starting comprehensive result review...")
        
        review_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'quality_analysis': {},
            'performance_analysis': {},
            'comparison_analysis': {},
            'recommendations': [],
            'detailed_findings': []
        }
        
        # 1. Quality Analysis
        quality_metrics, quality_issues = await self.data_analyzer.analyze_data_quality(results_df)
        review_report['quality_analysis'] = {
            'metrics': asdict(quality_metrics),
            'issues': [asdict(issue) for issue in quality_issues]
        }
        
        # 2. Performance Analysis
        performance_analysis = await self._analyze_processing_performance(results_df)
        review_report['performance_analysis'] = performance_analysis
        
        # 3. Comparison Analysis (if original data provided)
        if original_df is not None:
            comparison_analysis = await self._compare_before_after(original_df, results_df)
            review_report['comparison_analysis'] = comparison_analysis
        
        # 4. Generate Summary
        summary = self._generate_review_summary(quality_metrics, quality_issues, performance_analysis)
        review_report['summary'] = summary
        
        # 5. Detailed Findings
        detailed_findings = await self._generate_detailed_findings(results_df, quality_issues)
        review_report['detailed_findings'] = detailed_findings
        
        # Store in history
        self.review_history.append(review_report)
        
        logger.info(f"✅ Review complete. Quality score: {quality_metrics.overall_score:.2f}/100")
        
        return review_report
    
    async def _analyze_processing_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze processing performance metrics"""
        performance = {
            'total_records_processed': len(df),
            'successful_enrichments': {},
            'failed_enrichments': {},
            'processing_efficiency': {},
            'resource_usage': {}
        }
        
        # Analyze enrichment success rates
        enrichment_fields = [
            'gdr_url_instagram', 'gdr_url_facebook', 'gdr_insta_followers',
            'gdr_fb_followers', 'gdr_analise_reviews', 'gdr_telefone_1',
            'gdr_email_1', 'gdr_website'
        ]
        
        for field in enrichment_fields:
            if field in df.columns:
                filled_count = df[field].notna().sum()
                success_rate = (filled_count / len(df)) * 100
                performance['successful_enrichments'][field] = {
                    'count': filled_count,
                    'rate': success_rate
                }
        
        # Analyze token usage and costs (if available)
        if 'gdr_total_tokens' in df.columns:
            total_tokens = df['gdr_total_tokens'].sum()
            avg_tokens_per_record = df['gdr_total_tokens'].mean()
            performance['resource_usage']['total_tokens'] = total_tokens
            performance['resource_usage']['avg_tokens_per_record'] = avg_tokens_per_record
        
        if 'gdr_total_cost' in df.columns:
            total_cost = df['gdr_total_cost'].sum()
            avg_cost_per_record = df['gdr_total_cost'].mean()
            performance['resource_usage']['total_cost'] = total_cost
            performance['resource_usage']['avg_cost_per_record'] = avg_cost_per_record
        
        # Calculate processing efficiency
        successful_records = len(df[df['gdr_score_sinergia'].notna()]) if 'gdr_score_sinergia' in df.columns else 0
        efficiency_rate = (successful_records / len(df)) * 100 if len(df) > 0 else 0
        performance['processing_efficiency']['overall_success_rate'] = efficiency_rate
        
        return performance
    
    async def _compare_before_after(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict[str, Any]:
        """Compare original vs processed data"""
        comparison = {
            'record_count_change': len(processed_df) - len(original_df),
            'fields_added': [],
            'data_enrichment_summary': {},
            'quality_improvement': {}
        }
        
        # Identify new fields
        original_fields = set(original_df.columns)
        processed_fields = set(processed_df.columns)
        new_fields = processed_fields - original_fields
        comparison['fields_added'] = list(new_fields)
        
        # Analyze data enrichment
        for field in new_fields:
            if field in processed_df.columns:
                filled_count = processed_df[field].notna().sum()
                comparison['data_enrichment_summary'][field] = {
                    'records_enriched': filled_count,
                    'enrichment_rate': (filled_count / len(processed_df)) * 100
                }
        
        return comparison
    
    def _generate_review_summary(self, 
                                quality_metrics: QualityMetrics,
                                quality_issues: List[QualityIssue],
                                performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive review summary"""
        
        # Determine overall status
        if quality_metrics.overall_score >= 90:
            status = "EXCELLENT"
            status_color = "🟢"
        elif quality_metrics.overall_score >= 75:
            status = "GOOD"
            status_color = "🟡"
        elif quality_metrics.overall_score >= 50:
            status = "ACCEPTABLE"
            status_color = "🟠"
        else:
            status = "NEEDS_IMPROVEMENT"
            status_color = "🔴"
        
        # Count critical issues
        critical_issues = len([issue for issue in quality_issues if issue.severity == 'critical'])
        high_issues = len([issue for issue in quality_issues if issue.severity == 'high'])
        
        return {
            'overall_status': status,
            'status_indicator': status_color,
            'quality_score': quality_metrics.overall_score,
            'total_records': quality_metrics.total_records,
            'valid_records': quality_metrics.valid_records,
            'fake_data_percentage': quality_metrics.fake_data_percentage,
            'critical_issues_count': critical_issues,
            'high_issues_count': high_issues,
            'processing_success_rate': performance_analysis.get('processing_efficiency', {}).get('overall_success_rate', 0),
            'key_strengths': self._identify_key_strengths(quality_metrics, performance_analysis),
            'key_concerns': self._identify_key_concerns(quality_issues),
            'immediate_actions_required': critical_issues > 0 or high_issues > 5
        }
    
    def _identify_key_strengths(self, quality_metrics: QualityMetrics, performance_analysis: Dict[str, Any]) -> List[str]:
        """Identify key strengths in the data/processing"""
        strengths = []
        
        if quality_metrics.completeness_score >= 90:
            strengths.append("Excellent data completeness")
        
        if quality_metrics.accuracy_score >= 95:
            strengths.append("High data accuracy")
        
        if quality_metrics.fake_data_percentage < 5:
            strengths.append("Low fake data presence")
        
        if quality_metrics.enrichment_score >= 70:
            strengths.append("Good enrichment coverage")
        
        success_rate = performance_analysis.get('processing_efficiency', {}).get('overall_success_rate', 0)
        if success_rate >= 90:
            strengths.append("High processing success rate")
        
        return strengths[:5]  # Limit to top 5
    
    def _identify_key_concerns(self, quality_issues: List[QualityIssue]) -> List[str]:
        """Identify key concerns from quality issues"""
        concerns = []
        
        # Group by issue type
        issue_type_counts = Counter(issue.issue_type for issue in quality_issues)
        
        for issue_type, count in issue_type_counts.most_common(5):
            severity_levels = [issue.severity for issue in quality_issues if issue.issue_type == issue_type]
            max_severity = max(severity_levels, key=['low', 'medium', 'high', 'critical'].index)
            
            concern_desc = f"{issue_type.replace('_', ' ').title()} ({count} cases, {max_severity} severity)"
            concerns.append(concern_desc)
        
        return concerns
    
    async def _generate_detailed_findings(self, df: pd.DataFrame, quality_issues: List[QualityIssue]) -> List[Dict[str, Any]]:
        """Generate detailed findings for each major issue category"""
        findings = []
        
        # Group issues by category
        issues_by_category = defaultdict(list)
        for issue in quality_issues:
            issues_by_category[issue.category].append(issue)
        
        for category, category_issues in issues_by_category.items():
            finding = {
                'category': category,
                'title': f"{category.replace('_', ' ').title()} Analysis",
                'issue_count': len(category_issues),
                'severity_breakdown': Counter(issue.severity for issue in category_issues),
                'top_issues': [],
                'affected_fields': list(set(issue.field for issue in category_issues)),
                'recommendations': []
            }
            
            # Get top issues by severity
            sorted_issues = sorted(category_issues, 
                                 key=lambda x: ['low', 'medium', 'high', 'critical'].index(x.severity),
                                 reverse=True)
            
            for issue in sorted_issues[:5]:  # Top 5 issues
                finding['top_issues'].append({
                    'severity': issue.severity,
                    'type': issue.issue_type,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'field': issue.field
                })
            
            # Generate category-specific recommendations
            if category == 'fake_data':
                finding['recommendations'] = [
                    "Implement stricter data validation during collection",
                    "Add fake data detection to preprocessing pipeline",
                    "Review data sources for quality issues"
                ]
            elif category == 'missing_data':
                finding['recommendations'] = [
                    "Improve data collection processes",
                    "Configure additional data sources",
                    "Implement data completion strategies"
                ]
            elif category == 'invalid_format':
                finding['recommendations'] = [
                    "Add format validation to input pipeline",
                    "Standardize data formats across sources",
                    "Implement data cleaning procedures"
                ]
            
            findings.append(finding)
        
        return findings


# ===================================================================================
# CLASS: ImprovementPlanner
# ===================================================================================

class ImprovementPlanner:
    """Creates actionable improvement plans based on review results"""
    
    def __init__(self):
        self.improvement_templates = self._initialize_improvement_templates()
    
    def _initialize_improvement_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize improvement recommendation templates"""
        return {
            'fake_data_detection': {
                'priority': 'critical',
                'category': 'data_quality',
                'title': 'Implement Advanced Fake Data Detection',
                'description': 'Add comprehensive fake data detection to prevent invalid data from entering the system',
                'implementation_complexity': 'medium',
                'estimated_impact': 'high'
            },
            'data_validation': {
                'priority': 'high',
                'category': 'data_quality',
                'title': 'Enhance Data Validation Pipeline',
                'description': 'Strengthen data validation rules and processes',
                'implementation_complexity': 'medium',
                'estimated_impact': 'high'
            },
            'enrichment_optimization': {
                'priority': 'medium',
                'category': 'performance',
                'title': 'Optimize Data Enrichment Process',
                'description': 'Improve enrichment success rates and efficiency',
                'implementation_complexity': 'high',
                'estimated_impact': 'medium'
            },
            'monitoring_system': {
                'priority': 'medium',
                'category': 'system',
                'title': 'Implement Quality Monitoring System',
                'description': 'Add real-time quality monitoring and alerting',
                'implementation_complexity': 'high',
                'estimated_impact': 'medium'
            }
        }
    
    async def create_improvement_plan(self, 
                                    review_report: Dict[str, Any],
                                    focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        Create comprehensive improvement plan based on review results
        
        Args:
            review_report: Result from ResultReviewer
            focus_areas: Specific areas to focus on (optional)
            
        Returns:
            Detailed improvement plan
        """
        logger.info("📋 Creating improvement plan...")
        
        improvement_plan = {
            'plan_id': f"improvement_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'created_at': datetime.now().isoformat(),
            'based_on_review': review_report.get('timestamp'),
            'summary': {},
            'recommendations': [],
            'implementation_roadmap': {},
            'code_changes': {},
            'expected_outcomes': {}
        }
        
        # Analyze review results
        quality_metrics = review_report.get('quality_analysis', {}).get('metrics', {})
        quality_issues = review_report.get('quality_analysis', {}).get('issues', [])
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(quality_issues, quality_metrics, focus_areas)
        improvement_plan['recommendations'] = recommendations
        
        # Create implementation roadmap
        roadmap = self._create_implementation_roadmap(recommendations)
        improvement_plan['implementation_roadmap'] = roadmap
        
        # Generate code changes
        code_changes = await self._generate_code_changes(recommendations)
        improvement_plan['code_changes'] = code_changes
        
        # Predict expected outcomes
        expected_outcomes = self._predict_expected_outcomes(recommendations, quality_metrics)
        improvement_plan['expected_outcomes'] = expected_outcomes
        
        # Create summary
        improvement_plan['summary'] = self._create_plan_summary(recommendations, roadmap)
        
        logger.info(f"✅ Improvement plan created with {len(recommendations)} recommendations")
        
        return improvement_plan
    
    async def _generate_recommendations(self, 
                                      quality_issues: List[Dict[str, Any]],
                                      quality_metrics: Dict[str, Any],
                                      focus_areas: List[str] = None) -> List[ImprovementRecommendation]:
        """Generate specific improvement recommendations"""
        recommendations = []
        
        # Analyze issue patterns
        issue_categories = Counter(issue['category'] for issue in quality_issues)
        issue_severities = Counter(issue['severity'] for issue in quality_issues)
        
        # Fake data issues
        fake_data_count = sum(1 for issue in quality_issues if issue['category'] == 'fake_data')
        if fake_data_count > 0:
            recommendations.append(ImprovementRecommendation(
                priority='critical' if fake_data_count > 10 else 'high',
                category='data_quality',
                title='Implement Advanced Fake Data Detection',
                description=f'Found {fake_data_count} fake data entries. Implement comprehensive fake data detection.',
                action_items=[
                    'Add phone number validation with phonenumbers library',
                    'Implement email validation with domain checking',
                    'Add business name validation against known fake patterns',
                    'Create fake data detection pipeline component',
                    'Add fake data alerts and reporting'
                ],
                estimated_impact='high',
                implementation_complexity='medium',
                code_changes_needed=[
                    'src/core/lead_processor.py - Add validation step',
                    'src/features/contact_extraction.py - Add validation logic',
                    'src/agents/review_agent.py - Enhance detection rules'
                ]
            ))
        
        # Data completeness issues
        completeness_score = quality_metrics.get('completeness_score', 100)
        if completeness_score < 70:
            recommendations.append(ImprovementRecommendation(
                priority='high',
                category='data_collection',
                title='Improve Data Collection Completeness',
                description=f'Data completeness score is {completeness_score:.1f}%. Improve data collection processes.',
                action_items=[
                    'Review and optimize web scraping configurations',
                    'Add fallback data sources for missing information',
                    'Implement data completion strategies',
                    'Add mandatory field validation',
                    'Configure retry logic for failed extractions'
                ],
                estimated_impact='high',
                implementation_complexity='medium',
                code_changes_needed=[
                    'src/features/web_scraping.py - Add fallback sources',
                    'src/core/orchestrator.py - Add completion strategies',
                    'src/infrastructure/cache_system.py - Improve caching'
                ]
            ))
        
        # Enrichment quality issues
        enrichment_score = quality_metrics.get('enrichment_score', 100)
        if enrichment_score < 50:
            recommendations.append(ImprovementRecommendation(
                priority='medium',
                category='enrichment',
                title='Optimize Data Enrichment Pipeline',
                description=f'Enrichment score is {enrichment_score:.1f}%. Optimize enrichment processes.',
                action_items=[
                    'Review scraping configuration and credentials',
                    'Optimize social media scraping success rates',
                    'Add additional data sources and APIs',
                    'Implement intelligent retry mechanisms',
                    'Add enrichment quality monitoring'
                ],
                estimated_impact='medium',
                implementation_complexity='high',
                code_changes_needed=[
                    'src/features/social_scraping.py - Optimize scraping',
                    'src/core/api_manager.py - Add new APIs',
                    'src/infrastructure/checkpoint_manager.py - Add monitoring'
                ]
            ))
        
        # High number of critical issues
        critical_issues = issue_severities.get('critical', 0)
        if critical_issues > 0:
            recommendations.append(ImprovementRecommendation(
                priority='critical',
                category='system_reliability',
                title='Address Critical System Issues',
                description=f'Found {critical_issues} critical issues that need immediate attention.',
                action_items=[
                    'Fix all critical data validation issues',
                    'Implement emergency data cleaning procedures',
                    'Add critical issue alerting system',
                    'Create data recovery procedures',
                    'Implement system health monitoring'
                ],
                estimated_impact='high',
                implementation_complexity='high',
                code_changes_needed=[
                    'src/core/lead_processor.py - Add critical validations',
                    'src/agents/review_agent.py - Add alerting',
                    'src/infrastructure/ - Add monitoring system'
                ]
            ))
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 4))
        
        return recommendations
    
    def _create_implementation_roadmap(self, recommendations: List[ImprovementRecommendation]) -> Dict[str, Any]:
        """Create implementation roadmap with phases and timelines"""
        
        # Group recommendations by priority and complexity
        phases = {
            'immediate': [],  # Critical priority, any complexity
            'short_term': [], # High priority, low-medium complexity
            'medium_term': [], # High priority, high complexity OR medium priority, any complexity
            'long_term': []   # Low priority, any complexity
        }
        
        for rec in recommendations:
            if rec.priority == 'critical':
                phases['immediate'].append(rec)
            elif rec.priority == 'high':
                if rec.implementation_complexity in ['low', 'medium']:
                    phases['short_term'].append(rec)
                else:
                    phases['medium_term'].append(rec)
            elif rec.priority == 'medium':
                phases['medium_term'].append(rec)
            else:
                phases['long_term'].append(rec)
        
        # Estimate timelines
        roadmap = {
            'immediate': {
                'timeline': '1-2 weeks',
                'description': 'Critical issues requiring immediate attention',
                'recommendations': [asdict(rec) for rec in phases['immediate']],
                'estimated_effort': f"{len(phases['immediate'])} x 2-3 days each"
            },
            'short_term': {
                'timeline': '2-6 weeks',
                'description': 'High priority improvements with manageable complexity',
                'recommendations': [asdict(rec) for rec in phases['short_term']],
                'estimated_effort': f"{len(phases['short_term'])} x 3-5 days each"
            },
            'medium_term': {
                'timeline': '2-4 months',
                'description': 'Major improvements requiring significant development',
                'recommendations': [asdict(rec) for rec in phases['medium_term']],
                'estimated_effort': f"{len(phases['medium_term'])} x 1-2 weeks each"
            },
            'long_term': {
                'timeline': '4-12 months',
                'description': 'Long-term enhancements and optimizations',
                'recommendations': [asdict(rec) for rec in phases['long_term']],
                'estimated_effort': f"{len(phases['long_term'])} x 2-4 weeks each"
            }
        }
        
        return roadmap
    
    async def _generate_code_changes(self, recommendations: List[ImprovementRecommendation]) -> Dict[str, Any]:
        """Generate specific code changes needed"""
        code_changes = {
            'files_to_modify': {},
            'new_files_to_create': [],
            'configuration_changes': [],
            'database_changes': [],
            'deployment_changes': []
        }
        
        all_code_changes = []
        for rec in recommendations:
            all_code_changes.extend(rec.code_changes_needed)
        
        # Group by file
        file_changes = defaultdict(list)
        for change in all_code_changes:
            if ' - ' in change:
                file_path, description = change.split(' - ', 1)
                file_changes[file_path].append(description)
        
        # Generate specific changes for each file
        for file_path, changes in file_changes.items():
            code_changes['files_to_modify'][file_path] = {
                'changes_needed': changes,
                'estimated_complexity': 'medium',
                'backup_required': True,
                'testing_required': True
            }
        
        # Suggest new files based on recommendations
        if any('fake data detection' in rec.title.lower() for rec in recommendations):
            code_changes['new_files_to_create'].append({
                'file_path': 'src/validators/fake_data_detector.py',
                'description': 'Comprehensive fake data detection module',
                'template': 'validation_module'
            })
        
        if any('monitoring' in rec.title.lower() for rec in recommendations):
            code_changes['new_files_to_create'].append({
                'file_path': 'src/monitoring/quality_monitor.py',
                'description': 'Real-time quality monitoring system',
                'template': 'monitoring_module'
            })
        
        return code_changes
    
    def _predict_expected_outcomes(self, 
                                 recommendations: List[ImprovementRecommendation],
                                 current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Predict expected outcomes after implementing recommendations"""
        
        current_overall_score = current_metrics.get('overall_score', 0)
        current_completeness = current_metrics.get('completeness_score', 0)
        current_accuracy = current_metrics.get('accuracy_score', 0)
        current_fake_percentage = current_metrics.get('fake_data_percentage', 0)
        
        # Estimate improvements based on recommendation types
        score_improvement = 0
        completeness_improvement = 0
        accuracy_improvement = 0
        fake_data_reduction = 0
        
        for rec in recommendations:
            if 'fake data' in rec.title.lower():
                fake_data_reduction += 80  # 80% reduction in fake data
                accuracy_improvement += 15
                score_improvement += 10
            elif 'completeness' in rec.title.lower():
                completeness_improvement += 25
                score_improvement += 15
            elif 'enrichment' in rec.title.lower():
                score_improvement += 10
                completeness_improvement += 15
            elif 'validation' in rec.title.lower():
                accuracy_improvement += 20
                score_improvement += 12
        
        # Apply improvements with realistic caps
        predicted_overall_score = min(100, current_overall_score + score_improvement)
        predicted_completeness = min(100, current_completeness + completeness_improvement)
        predicted_accuracy = min(100, current_accuracy + accuracy_improvement)
        predicted_fake_percentage = max(0, current_fake_percentage * (1 - fake_data_reduction/100))
        
        return {
            'current_state': {
                'overall_score': current_overall_score,
                'completeness_score': current_completeness,
                'accuracy_score': current_accuracy,
                'fake_data_percentage': current_fake_percentage
            },
            'predicted_state': {
                'overall_score': predicted_overall_score,
                'completeness_score': predicted_completeness,
                'accuracy_score': predicted_accuracy,
                'fake_data_percentage': predicted_fake_percentage
            },
            'expected_improvements': {
                'overall_score_gain': predicted_overall_score - current_overall_score,
                'completeness_gain': predicted_completeness - current_completeness,
                'accuracy_gain': predicted_accuracy - current_accuracy,
                'fake_data_reduction': current_fake_percentage - predicted_fake_percentage
            },
            'confidence_level': 0.8,  # 80% confidence in predictions
            'timeframe': '2-6 months for full impact'
        }
    
    def _create_plan_summary(self, 
                           recommendations: List[ImprovementRecommendation],
                           roadmap: Dict[str, Any]) -> Dict[str, Any]:
        """Create improvement plan summary"""
        
        total_recommendations = len(recommendations)
        critical_count = len([r for r in recommendations if r.priority == 'critical'])
        high_count = len([r for r in recommendations if r.priority == 'high'])
        
        return {
            'total_recommendations': total_recommendations,
            'by_priority': {
                'critical': critical_count,
                'high': high_count,
                'medium': len([r for r in recommendations if r.priority == 'medium']),
                'low': len([r for r in recommendations if r.priority == 'low'])
            },
            'by_category': dict(Counter(r.category for r in recommendations)),
            'implementation_phases': len([phase for phase in roadmap.values() if phase['recommendations']]),
            'estimated_total_timeline': '2-6 months',
            'immediate_actions_required': critical_count > 0,
            'expected_impact': 'high' if critical_count > 0 or high_count > 2 else 'medium',
            'complexity_assessment': 'high' if any(r.implementation_complexity == 'high' for r in recommendations) else 'medium'
        }


# ===================================================================================
# CLASS: LearningOptimizer
# ===================================================================================

class LearningOptimizer:
    """Teaches the main agent and optimizes system performance over time"""
    
    def __init__(self):
        self.learning_history = []
        self.optimization_rules = []
        self.performance_trends = defaultdict(list)
        self.teaching_modules = self._initialize_teaching_modules()
    
    def _initialize_teaching_modules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize teaching modules for different components"""
        return {
            'data_validation': {
                'component': 'LeadProcessor',
                'focus_area': 'Input validation and fake data detection',
                'optimization_targets': ['accuracy', 'fake_data_reduction']
            },
            'enrichment_strategies': {
                'component': 'Social/Web Scrapers',
                'focus_area': 'Improving enrichment success rates',
                'optimization_targets': ['completeness', 'enrichment_score']
            },
            'quality_monitoring': {
                'component': 'System Monitoring',
                'focus_area': 'Real-time quality assessment',
                'optimization_targets': ['detection_speed', 'accuracy']
            },
            'consensus_optimization': {
                'component': 'Multi-LLM Consensus',
                'focus_area': 'Improving consensus quality and efficiency',
                'optimization_targets': ['consensus_agreement', 'processing_time']
            }
        }
    
    async def learn_from_reviews(self, review_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Learn from review results and create optimization strategies
        
        Args:
            review_reports: List of review reports to learn from
            
        Returns:
            Learning insights and optimization recommendations
        """
        logger.info("🧠 Learning from review results...")
        
        learning_results = {
            'timestamp': datetime.now().isoformat(),
            'reports_analyzed': len(review_reports),
            'patterns_identified': [],
            'optimization_opportunities': [],
            'teaching_recommendations': [],
            'performance_trends': {},
            'system_insights': {}
        }
        
        # Analyze patterns across reviews
        patterns = await self._identify_patterns(review_reports)
        learning_results['patterns_identified'] = patterns
        
        # Find optimization opportunities
        optimizations = await self._find_optimization_opportunities(review_reports, patterns)
        learning_results['optimization_opportunities'] = optimizations
        
        # Generate teaching recommendations
        teaching_recs = await self._generate_teaching_recommendations(patterns, optimizations)
        learning_results['teaching_recommendations'] = teaching_recs
        
        # Analyze performance trends
        trends = self._analyze_performance_trends(review_reports)
        learning_results['performance_trends'] = trends
        
        # Generate system insights
        insights = await self._generate_system_insights(review_reports, patterns)
        learning_results['system_insights'] = insights
        
        # Store learning results
        self.learning_history.append(learning_results)
        
        logger.info(f"✅ Learning complete. Identified {len(patterns)} patterns and "
                   f"{len(optimizations)} optimization opportunities")
        
        return learning_results
    
    async def _identify_patterns(self, review_reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify patterns across multiple review reports"""
        patterns = []
        
        # Collect all quality issues across reports
        all_issues = []
        for report in review_reports:
            issues = report.get('quality_analysis', {}).get('issues', [])
            all_issues.extend(issues)
        
        if not all_issues:
            return patterns
        
        # Pattern 1: Recurring issue types
        issue_type_counts = Counter(issue['issue_type'] for issue in all_issues)
        for issue_type, count in issue_type_counts.most_common(5):
            if count >= len(review_reports) * 0.5:  # Appears in 50%+ of reports
                patterns.append({
                    'type': 'recurring_issue',
                    'pattern': f'Recurring {issue_type}',
                    'frequency': count,
                    'description': f'{issue_type} appears consistently across {count} instances',
                    'confidence': 0.9,
                    'action_needed': True
                })
        
        # Pattern 2: Field-specific problems
        field_issue_counts = Counter(issue['field'] for issue in all_issues)
        for field, count in field_issue_counts.most_common(3):
            if count >= len(review_reports) * 0.3:  # Appears in 30%+ of reports
                patterns.append({
                    'type': 'field_specific_problem',
                    'pattern': f'Field {field} issues',
                    'frequency': count,
                    'description': f'Field {field} consistently has quality issues',
                    'confidence': 0.8,
                    'action_needed': True
                })
        
        # Pattern 3: Quality score trends
        quality_scores = []
        for report in review_reports:
            score = report.get('quality_analysis', {}).get('metrics', {}).get('overall_score', 0)
            if score > 0:
                quality_scores.append(score)
        
        if len(quality_scores) >= 3:
            avg_score = statistics.mean(quality_scores)
            score_trend = 'improving' if quality_scores[-1] > quality_scores[0] else 'declining'
            
            patterns.append({
                'type': 'quality_trend',
                'pattern': f'Quality score {score_trend}',
                'frequency': len(quality_scores),
                'description': f'Average quality score: {avg_score:.1f}, trend: {score_trend}',
                'confidence': 0.7,
                'action_needed': score_trend == 'declining'
            })
        
        return patterns
    
    async def _find_optimization_opportunities(self, 
                                            review_reports: List[Dict[str, Any]],
                                            patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find specific optimization opportunities"""
        opportunities = []
        
        # Opportunity 1: Fake data prevention
        fake_data_issues = 0
        for report in review_reports:
            issues = report.get('quality_analysis', {}).get('issues', [])
            fake_data_issues += len([i for i in issues if i['category'] == 'fake_data'])
        
        if fake_data_issues > 0:
            opportunities.append({
                'type': 'prevention_optimization',
                'title': 'Implement Preventive Fake Data Detection',
                'description': f'Found {fake_data_issues} fake data issues. Implement prevention at input stage.',
                'potential_impact': 'high',
                'implementation_effort': 'medium',
                'target_components': ['LeadProcessor', 'ContactExtraction'],
                'expected_improvement': '70-90% reduction in fake data'
            })
        
        # Opportunity 2: Enrichment optimization
        low_enrichment_reports = 0
        for report in review_reports:
            enrichment_score = report.get('quality_analysis', {}).get('metrics', {}).get('enrichment_score', 100)
            if enrichment_score < 50:
                low_enrichment_reports += 1
        
        if low_enrichment_reports > len(review_reports) * 0.3:
            opportunities.append({
                'type': 'enrichment_optimization',
                'title': 'Optimize Data Enrichment Pipeline',
                'description': f'{low_enrichment_reports} reports show low enrichment rates',
                'potential_impact': 'medium',
                'implementation_effort': 'high',
                'target_components': ['SocialScraping', 'WebScraping'],
                'expected_improvement': '30-50% increase in enrichment success'
            })
        
        # Opportunity 3: Validation pipeline optimization
        recurring_validation_issues = [p for p in patterns if 'invalid' in p['pattern'].lower()]
        if recurring_validation_issues:
            opportunities.append({
                'type': 'validation_optimization',
                'title': 'Enhance Validation Pipeline',
                'description': 'Multiple validation issues detected across reports',
                'potential_impact': 'high',
                'implementation_effort': 'medium',
                'target_components': ['DataValidation', 'ReviewAgent'],
                'expected_improvement': '40-60% reduction in validation errors'
            })
        
        return opportunities
    
    async def _generate_teaching_recommendations(self, 
                                               patterns: List[Dict[str, Any]],
                                               opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific teaching recommendations for system components"""
        teaching_recs = []
        
        # Teaching recommendation for LeadProcessor
        fake_data_patterns = [p for p in patterns if 'fake' in p['pattern'].lower()]
        if fake_data_patterns:
            teaching_recs.append({
                'target_component': 'LeadProcessor',
                'teaching_focus': 'Fake Data Prevention',
                'specific_lessons': [
                    'Add phone number validation before processing',
                    'Implement email domain validation',
                    'Add business name sanity checks',
                    'Create fake data pattern database',
                    'Implement confidence scoring for extracted data'
                ],
                'implementation_guidance': {
                    'code_location': 'src/core/lead_processor.py',
                    'method_to_enhance': 'process_lead',
                    'new_validation_step': 'Add validate_input_data() call at start',
                    'required_imports': ['phonenumbers', 'validators', 'fake_data_detector']
                },
                'expected_outcome': 'Prevent fake data from entering processing pipeline',
                'priority': 'high'
            })
        
        # Teaching recommendation for ReviewAgent
        quality_patterns = [p for p in patterns if 'quality' in p['pattern'].lower()]
        if quality_patterns:
            teaching_recs.append({
                'target_component': 'ReviewAgent',
                'teaching_focus': 'Enhanced Quality Detection',
                'specific_lessons': [
                    'Implement pattern-based quality scoring',
                    'Add historical comparison capabilities',
                    'Create quality trend analysis',
                    'Implement predictive quality alerts',
                    'Add automated quality reporting'
                ],
                'implementation_guidance': {
                    'code_location': 'src/agents/review_agent.py',
                    'method_to_enhance': 'analyze_data_quality',
                    'new_features': ['pattern_analysis', 'trend_tracking', 'predictive_alerts'],
                    'required_dependencies': ['numpy', 'pandas', 'scikit-learn']
                },
                'expected_outcome': 'Proactive quality issue detection and prevention',
                'priority': 'medium'
            })
        
        # Teaching recommendation for enrichment optimization
        enrichment_opportunities = [o for o in opportunities if 'enrichment' in o['title'].lower()]
        if enrichment_opportunities:
            teaching_recs.append({
                'target_component': 'EnrichmentPipeline',
                'teaching_focus': 'Success Rate Optimization',
                'specific_lessons': [
                    'Implement intelligent retry mechanisms',
                    'Add data source prioritization',
                    'Create enrichment success tracking',
                    'Implement adaptive timeout handling',
                    'Add enrichment quality scoring'
                ],
                'implementation_guidance': {
                    'code_location': 'src/features/social_scraping.py',
                    'method_to_enhance': 'scrape_social_data',
                    'optimization_areas': ['retry_logic', 'timeout_handling', 'success_tracking'],
                    'monitoring_additions': ['success_rates', 'response_times', 'error_patterns']
                },
                'expected_outcome': '30-50% improvement in enrichment success rates',
                'priority': 'medium'
            })
        
        return teaching_recs
    
    def _analyze_performance_trends(self, review_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        trends = {
            'quality_score_trend': [],
            'fake_data_trend': [],
            'completeness_trend': [],
            'enrichment_trend': [],
            'trend_analysis': {}
        }
        
        # Extract metrics over time
        for report in review_reports:
            metrics = report.get('quality_analysis', {}).get('metrics', {})
            
            trends['quality_score_trend'].append(metrics.get('overall_score', 0))
            trends['fake_data_trend'].append(metrics.get('fake_data_percentage', 0))
            trends['completeness_trend'].append(metrics.get('completeness_score', 0))
            trends['enrichment_trend'].append(metrics.get('enrichment_score', 0))
        
        # Analyze trends
        for trend_name, values in trends.items():
            if trend_name != 'trend_analysis' and len(values) >= 2:
                trend_direction = 'improving' if values[-1] > values[0] else 'declining'
                avg_value = statistics.mean(values) if values else 0
                
                trends['trend_analysis'][trend_name] = {
                    'direction': trend_direction,
                    'average': avg_value,
                    'latest': values[-1] if values else 0,
                    'change': values[-1] - values[0] if len(values) >= 2 else 0
                }
        
        return trends
    
    async def _generate_system_insights(self, 
                                       review_reports: List[Dict[str, Any]],
                                       patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate high-level system insights"""
        insights = {
            'system_health': 'unknown',
            'key_strengths': [],
            'critical_weaknesses': [],
            'improvement_potential': 'unknown',
            'recommended_focus_areas': [],
            'risk_assessment': {}
        }
        
        # Calculate average quality score
        quality_scores = []
        for report in review_reports:
            score = report.get('quality_analysis', {}).get('metrics', {}).get('overall_score', 0)
            if score > 0:
                quality_scores.append(score)
        
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0
        
        # Determine system health
        if avg_quality >= 85:
            insights['system_health'] = 'excellent'
        elif avg_quality >= 70:
            insights['system_health'] = 'good'
        elif avg_quality >= 50:
            insights['system_health'] = 'acceptable'
        else:
            insights['system_health'] = 'needs_attention'
        
        # Identify strengths and weaknesses
        all_metrics = []
        for report in review_reports:
            metrics = report.get('quality_analysis', {}).get('metrics', {})
            all_metrics.append(metrics)
        
        if all_metrics:
            # Check completeness scores
            completeness_scores = [m.get('completeness_score', 0) for m in all_metrics]
            avg_completeness = statistics.mean(completeness_scores) if completeness_scores else 0
            
            if avg_completeness >= 80:
                insights['key_strengths'].append('High data completeness')
            elif avg_completeness < 50:
                insights['critical_weaknesses'].append('Poor data completeness')
            
            # Check fake data percentages
            fake_percentages = [m.get('fake_data_percentage', 0) for m in all_metrics]
            avg_fake = statistics.mean(fake_percentages) if fake_percentages else 0
            
            if avg_fake <= 5:
                insights['key_strengths'].append('Low fake data presence')
            elif avg_fake > 15:
                insights['critical_weaknesses'].append('High fake data percentage')
            
            # Check enrichment scores
            enrichment_scores = [m.get('enrichment_score', 0) for m in all_metrics]
            avg_enrichment = statistics.mean(enrichment_scores) if enrichment_scores else 0
            
            if avg_enrichment >= 70:
                insights['key_strengths'].append('Good enrichment coverage')
            elif avg_enrichment < 40:
                insights['critical_weaknesses'].append('Poor enrichment success')
        
        # Determine improvement potential
        if len(insights['critical_weaknesses']) > 2:
            insights['improvement_potential'] = 'high'
        elif len(insights['critical_weaknesses']) > 0:
            insights['improvement_potential'] = 'medium'
        else:
            insights['improvement_potential'] = 'low'
        
        # Recommend focus areas based on patterns
        action_needed_patterns = [p for p in patterns if p.get('action_needed', False)]
        for pattern in action_needed_patterns[:3]:
            focus_area = pattern['pattern'].replace('_', ' ').title()
            insights['recommended_focus_areas'].append(focus_area)
        
        # Risk assessment
        critical_issues_count = sum(
            len([i for i in report.get('quality_analysis', {}).get('issues', []) 
                if i['severity'] == 'critical'])
            for report in review_reports
            )
        
        insights['risk_assessment'] = {
            'data_quality_risk': 'high' if avg_quality < 50 else 'medium' if avg_quality < 75 else 'low',
            'fake_data_risk': 'high' if avg_fake > 15 else 'medium' if avg_fake > 5 else 'low',
            'system_reliability_risk': 'high' if critical_issues_count > 0 else 'low',
            'overall_risk': 'high' if critical_issues_count > 0 or avg_quality < 50 else 'medium' if avg_quality < 75 else 'low'
        }
        
        return insights
    
    async def create_optimization_config(self, learning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create configuration for system optimization"""
        
        config = {
            'validation_rules': {},
            'quality_thresholds': {},
            'monitoring_settings': {},
            'enrichment_settings': {},
            'alerting_rules': {}
        }
        
        # Configure validation rules based on learning
        patterns = learning_results.get('patterns_identified', [])
        fake_data_patterns = [p for p in patterns if 'fake' in p['pattern'].lower()]
        
        if fake_data_patterns:
            config['validation_rules'] = {
                'enable_phone_validation': True,
                'enable_email_validation': True,
                'enable_business_name_validation': True,
                'fake_data_detection_threshold': 0.8,
                'validation_strictness': 'high'
            }
        
        # Configure quality thresholds
        trends = learning_results.get('performance_trends', {})
        quality_trend = trends.get('trend_analysis', {}).get('quality_score_trend', {})
        
        if quality_trend:
            avg_quality = quality_trend.get('average', 75)
            config['quality_thresholds'] = {
                'minimum_overall_score': max(60, avg_quality - 10),
                'minimum_completeness_score': 70,
                'maximum_fake_data_percentage': 5,
                'minimum_enrichment_score': 50
            }
        
        # Configure monitoring based on identified issues
        opportunities = learning_results.get('optimization_opportunities', [])
        if opportunities:
            config['monitoring_settings'] = {
                'enable_real_time_monitoring': True,
                'quality_check_frequency': 'every_batch',
                'alert_on_quality_degradation': True,
                'track_performance_trends': True
            }
        
        return config


# ===================================================================================
# MAIN REVIEW AGENT CLASS
# ===================================================================================

class ComprehensiveReviewAgent:
    """Main Review Agent that orchestrates all quality assurance components"""
    
    def __init__(self):
        self.data_analyzer = DataQualityAnalyzer()
        self.result_reviewer = ResultReviewer(self.data_analyzer)
        self.improvement_planner = ImprovementPlanner()
        self.learning_optimizer = LearningOptimizer()
        
        self.review_session_id = None
        self.session_reports = []
    
    async def start_review_session(self, session_name: str = None) -> str:
        """Start a new review session"""
        session_id = f"review_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if session_name:
            session_id = f"{session_name}_{session_id}"
        
        self.review_session_id = session_id
        self.session_reports = []
        
        logger.info(f"🔍 Starting review session: {session_id}")
        return session_id
    
    async def comprehensive_review(self,
                                 results_df: pd.DataFrame,
                                 original_df: pd.DataFrame = None,
                                 output_dir: str = None) -> Dict[str, Any]:
        """
        Perform comprehensive review of processing results
        
        Args:
            results_df: Processed results to review
            original_df: Original data (optional)
            output_dir: Directory to save reports (optional)
            
        Returns:
            Complete review package with all analyses
        """
        logger.info("🚀 Starting comprehensive review...")
        
        if not self.review_session_id:
            await self.start_review_session()
        
        # 1. Detailed review
        review_report = await self.result_reviewer.review_processing_results(
            results_df, original_df
        )
        
        # 2. Create improvement plan
        improvement_plan = await self.improvement_planner.create_improvement_plan(
            review_report
        )
        
        # 3. Learn from results
        learning_results = await self.learning_optimizer.learn_from_reviews([review_report])
        
        # 4. Create optimization config
        optimization_config = await self.learning_optimizer.create_optimization_config(
            learning_results
        )
        
        # 5. Compile comprehensive package
        comprehensive_package = {
            'session_id': self.review_session_id,
            'timestamp': datetime.now().isoformat(),
            'review_report': review_report,
            'improvement_plan': improvement_plan,
            'learning_results': learning_results,
            'optimization_config': optimization_config,
            'summary': self._create_comprehensive_summary(
                review_report, improvement_plan, learning_results
            )
        }
        
        # 6. Generate markdown report
        if output_dir:
            markdown_report = await self.generate_markdown_report(
                comprehensive_package, output_dir
            )
            comprehensive_package['markdown_report_path'] = markdown_report
        
        # Store in session
        self.session_reports.append(comprehensive_package)
        
        logger.info("✅ Comprehensive review completed successfully")
        
        return comprehensive_package
    
    def _create_comprehensive_summary(self,
                                    review_report: Dict[str, Any],
                                    improvement_plan: Dict[str, Any],
                                    learning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive summary of all analyses"""
        
        quality_metrics = review_report.get('quality_analysis', {}).get('metrics', {})
        improvement_summary = improvement_plan.get('summary', {})
        system_insights = learning_results.get('system_insights', {})
        
        return {
            'overall_assessment': {
                'quality_score': quality_metrics.get('overall_score', 0),
                'system_health': system_insights.get('system_health', 'unknown'),
                'improvement_potential': system_insights.get('improvement_potential', 'unknown'),
                'immediate_action_required': improvement_summary.get('immediate_actions_required', False)
            },
            'key_findings': {
                'fake_data_detected': quality_metrics.get('fake_data_percentage', 0) > 5,
                'data_completeness_issues': quality_metrics.get('completeness_score', 100) < 70,
                'enrichment_problems': quality_metrics.get('enrichment_score', 100) < 50,
                'critical_issues_count': improvement_summary.get('by_priority', {}).get('critical', 0)
            },
            'recommendations_summary': {
                'total_recommendations': improvement_summary.get('total_recommendations', 0),
                'critical_priority': improvement_summary.get('by_priority', {}).get('critical', 0),
                'estimated_timeline': improvement_summary.get('estimated_total_timeline', 'unknown'),
                'expected_impact': improvement_summary.get('expected_impact', 'unknown')
            },
            'next_steps': self._generate_next_steps(improvement_plan, system_insights)
        }
    
    def _generate_next_steps(self,
                           improvement_plan: Dict[str, Any],
                           system_insights: Dict[str, Any]) -> List[str]:
        """Generate immediate next steps"""
        next_steps = []
        
        # Critical issues first
        critical_recs = improvement_plan.get('summary', {}).get('by_priority', {}).get('critical', 0)
        if critical_recs > 0:
            next_steps.append("🔴 Address critical issues immediately (see improvement plan)")
        
        # System health assessment
        system_health = system_insights.get('system_health', 'unknown')
        if system_health in ['needs_attention', 'acceptable']:
            next_steps.append("🟡 Review and implement high-priority improvements")
        
        # Fake data handling
        fake_data_risk = system_insights.get('risk_assessment', {}).get('fake_data_risk', 'unknown')
        if fake_data_risk == 'high':
            next_steps.append("🚫 Implement fake data detection and prevention immediately")
        
        # Learning optimization
        if len(system_insights.get('recommended_focus_areas', [])) > 0:
            focus_area = system_insights['recommended_focus_areas'][0]
            next_steps.append(f"🎯 Focus optimization efforts on: {focus_area}")
        
        # Default steps if nothing critical
        if not next_steps:
            next_steps = [
                "✅ System appears healthy - continue monitoring",
                "📊 Implement suggested optimizations for further improvement",
                "🔄 Schedule regular quality reviews"
            ]
        
        return next_steps[:5]  # Limit to 5 steps
    
    async def generate_markdown_report(self,
                                     comprehensive_package: Dict[str, Any],
                                     output_dir: str) -> str:
        """Generate comprehensive markdown report"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        session_id = comprehensive_package['session_id']
        report_file = output_path / f"{session_id}_comprehensive_review.md"
        
        # Get data from package
        review_report = comprehensive_package['review_report']
        improvement_plan = comprehensive_package['improvement_plan']
        learning_results = comprehensive_package['learning_results']
        summary = comprehensive_package['summary']
        
        quality_metrics = review_report.get('quality_analysis', {}).get('metrics', {})
        quality_issues = review_report.get('quality_analysis', {}).get('issues', [])
        
        # Generate markdown content
        markdown_content = f"""# AURA NEXUS - Comprehensive Quality Review Report

**Session ID:** {session_id}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Review Agent:** ComprehensiveReviewAgent v2.0

---

## 📊 Executive Summary

### Overall Assessment
- **Quality Score:** {quality_metrics.get('overall_score', 0):.1f}/100
- **System Health:** {summary['overall_assessment']['system_health'].upper()}
- **Improvement Potential:** {summary['overall_assessment']['improvement_potential'].upper()}
- **Immediate Action Required:** {'YES' if summary['overall_assessment']['immediate_action_required'] else 'NO'}

### Key Metrics
| Metric | Score | Status |
|--------|--------|--------|
| Data Completeness | {quality_metrics.get('completeness_score', 0):.1f}% | {'🟢' if quality_metrics.get('completeness_score', 0) >= 80 else '🟡' if quality_metrics.get('completeness_score', 0) >= 60 else '🔴'} |
| Data Accuracy | {quality_metrics.get('accuracy_score', 0):.1f}% | {'🟢' if quality_metrics.get('accuracy_score', 0) >= 95 else '🟡' if quality_metrics.get('accuracy_score', 0) >= 85 else '🔴'} |
| Data Consistency | {quality_metrics.get('consistency_score', 0):.1f}% | {'🟢' if quality_metrics.get('consistency_score', 0) >= 90 else '🟡' if quality_metrics.get('consistency_score', 0) >= 75 else '🔴'} |
| Enrichment Success | {quality_metrics.get('enrichment_score', 0):.1f}% | {'🟢' if quality_metrics.get('enrichment_score', 0) >= 70 else '🟡' if quality_metrics.get('enrichment_score', 0) >= 50 else '🔴'} |
| Fake Data Percentage | {quality_metrics.get('fake_data_percentage', 0):.1f}% | {'🟢' if quality_metrics.get('fake_data_percentage', 0) <= 5 else '🟡' if quality_metrics.get('fake_data_percentage', 0) <= 15 else '🔴'} |

### Key Findings
"""
        
        # Add key findings
        findings = summary['key_findings']
        if findings.get('fake_data_detected'):
            markdown_content += f"- 🚫 **Fake data detected** - {quality_metrics.get('fake_data_percentage', 0):.1f}% of records\n"
        
        if findings.get('data_completeness_issues'):
            markdown_content += f"- 📉 **Data completeness issues** - {quality_metrics.get('completeness_score', 0):.1f}% completeness\n"
        
        if findings.get('enrichment_problems'):
            markdown_content += f"- 🔍 **Enrichment challenges** - {quality_metrics.get('enrichment_score', 0):.1f}% success rate\n"
        
        critical_count = findings.get('critical_issues_count', 0)
        if critical_count > 0:
            markdown_content += f"- 🔴 **{critical_count} critical issues** require immediate attention\n"
        
        markdown_content += f"""

---

## 🔍 Detailed Quality Analysis

### Issue Breakdown
"""
        
        # Add issues breakdown
        issues_by_severity = Counter(issue['severity'] for issue in quality_issues)
        for severity in ['critical', 'high', 'medium', 'low']:
            count = issues_by_severity.get(severity, 0)
            if count > 0:
                icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[severity]
                markdown_content += f"- {icon} **{severity.title()}:** {count} issues\n"
        
        # Add top issues
        markdown_content += f"""

### Top Quality Issues
"""
        
        # Group issues by type and show top ones
        issue_type_counts = Counter(issue['issue_type'] for issue in quality_issues)
        for issue_type, count in issue_type_counts.most_common(5):
            examples = [issue for issue in quality_issues if issue['issue_type'] == issue_type][:2]
            
            markdown_content += f"""
#### {issue_type.replace('_', ' ').title()} ({count} instances)
"""
            for example in examples:
                markdown_content += f"- **Field:** {example['field']} - {example['description']}\n"
                if example.get('suggestion'):
                    markdown_content += f"  - *Suggestion:* {example['suggestion']}\n"
        
        # Add improvement areas
        improvement_areas = quality_metrics.get('improvement_areas', [])
        if improvement_areas:
            markdown_content += f"""

### Priority Improvement Areas
"""
            for i, area in enumerate(improvement_areas[:5], 1):
                markdown_content += f"{i}. {area}\n"
        
        markdown_content += f"""

---

## 📋 Improvement Plan

### Implementation Roadmap
"""
        
        # Add roadmap
        roadmap = improvement_plan.get('implementation_roadmap', {})
        for phase, details in roadmap.items():
            if details.get('recommendations'):
                markdown_content += f"""
#### {phase.replace('_', ' ').title()} ({details['timeline']})
*{details['description']}*

"""
                for rec in details['recommendations'][:3]:  # Show top 3 per phase
                    markdown_content += f"- **{rec['title']}** ({rec['priority']} priority)\n"
                    markdown_content += f"  - {rec['description']}\n"
                    if rec.get('action_items'):
                        for action in rec['action_items'][:2]:  # Show top 2 actions
                            markdown_content += f"    - {action}\n"
                markdown_content += "\n"
        
        # Add expected outcomes
        expected_outcomes = improvement_plan.get('expected_outcomes', {})
        if expected_outcomes:
            current_state = expected_outcomes.get('current_state', {})
            predicted_state = expected_outcomes.get('predicted_state', {})
            improvements = expected_outcomes.get('expected_improvements', {})
            
            markdown_content += f"""
### Expected Outcomes

| Metric | Current | Predicted | Improvement |
|--------|---------|-----------|-------------|
| Overall Score | {current_state.get('overall_score', 0):.1f} | {predicted_state.get('overall_score', 0):.1f} | +{improvements.get('overall_score_gain', 0):.1f} |
| Completeness | {current_state.get('completeness_score', 0):.1f}% | {predicted_state.get('completeness_score', 0):.1f}% | +{improvements.get('completeness_gain', 0):.1f}% |
| Accuracy | {current_state.get('accuracy_score', 0):.1f}% | {predicted_state.get('accuracy_score', 0):.1f}% | +{improvements.get('accuracy_gain', 0):.1f}% |
| Fake Data | {current_state.get('fake_data_percentage', 0):.1f}% | {predicted_state.get('fake_data_percentage', 0):.1f}% | -{improvements.get('fake_data_reduction', 0):.1f}% |

*Confidence Level: {expected_outcomes.get('confidence_level', 0)*100:.0f}%*
"""
        
        markdown_content += f"""

---

## 🧠 Learning & Optimization Insights

### System Health Assessment
"""
        
        # Add system insights
        system_insights = learning_results.get('system_insights', {})
        
        markdown_content += f"- **Overall Health:** {system_insights.get('system_health', 'unknown').title()}\n"
        markdown_content += f"- **Improvement Potential:** {system_insights.get('improvement_potential', 'unknown').title()}\n"
        
        strengths = system_insights.get('key_strengths', [])
        if strengths:
            markdown_content += f"\n**Key Strengths:**\n"
            for strength in strengths:
                markdown_content += f"- ✅ {strength}\n"
        
        weaknesses = system_insights.get('critical_weaknesses', [])
        if weaknesses:
            markdown_content += f"\n**Critical Weaknesses:**\n"
            for weakness in weaknesses:
                markdown_content += f"- ❌ {weakness}\n"
        
        # Add risk assessment
        risk_assessment = system_insights.get('risk_assessment', {})
        if risk_assessment:
            markdown_content += f"""

### Risk Assessment
- **Data Quality Risk:** {risk_assessment.get('data_quality_risk', 'unknown').title()}
- **Fake Data Risk:** {risk_assessment.get('fake_data_risk', 'unknown').title()}
- **System Reliability Risk:** {risk_assessment.get('system_reliability_risk', 'unknown').title()}
- **Overall Risk:** {risk_assessment.get('overall_risk', 'unknown').title()}
"""
        
        markdown_content += f"""

---

## 🎯 Immediate Next Steps

"""
        
        # Add next steps
        next_steps = summary.get('next_steps', [])
        for i, step in enumerate(next_steps, 1):
            markdown_content += f"{i}. {step}\n"
        
        markdown_content += f"""

---

## 📊 Detailed Statistics

### Processing Performance
- **Total Records:** {quality_metrics.get('total_records', 0):,}
- **Valid Records:** {quality_metrics.get('valid_records', 0):,}
- **Records with Issues:** {len(quality_issues):,}

### Issue Distribution
"""
        
        # Add detailed statistics
        issues_by_category = Counter(issue['category'] for issue in quality_issues)
        for category, count in issues_by_category.items():
            percentage = (count / len(quality_issues) * 100) if quality_issues else 0
            markdown_content += f"- **{category.replace('_', ' ').title()}:** {count} issues ({percentage:.1f}%)\n"
        
        markdown_content += f"""

---

## 📝 Technical Details

### Review Configuration
- **Review Agent Version:** 2.0
- **Analysis Components:** DataQualityAnalyzer, ResultReviewer, ImprovementPlanner, LearningOptimizer
- **Validation Rules:** Advanced fake data detection, format validation, completeness checks
- **Quality Thresholds:** Configurable based on historical performance

### Data Sources Analyzed
"""
        
        # Add technical details
        performance_analysis = review_report.get('performance_analysis', {})
        successful_enrichments = performance_analysis.get('successful_enrichments', {})
        
        for field, stats in successful_enrichments.items():
            success_rate = stats.get('rate', 0)
            count = stats.get('count', 0)
            markdown_content += f"- **{field}:** {count:,} records ({success_rate:.1f}% success rate)\n"
        
        markdown_content += f"""

---

**Report Generated by AURA NEXUS Comprehensive Review Agent v2.0**  
*Ensuring data quality and system optimization through intelligent analysis*
"""
        
        # Write to file
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"📄 Comprehensive markdown report saved: {report_file}")
        
        return str(report_file)
    
    async def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current review session"""
        if not self.session_reports:
            return {'message': 'No reviews conducted in this session'}
        
        return {
            'session_id': self.review_session_id,
            'total_reviews': len(self.session_reports),
            'latest_review': self.session_reports[-1]['summary'],
            'session_trends': self._analyze_session_trends()
        }
    
    def _analyze_session_trends(self) -> Dict[str, Any]:
        """Analyze trends across session reviews"""
        if len(self.session_reports) < 2:
            return {'message': 'Insufficient data for trend analysis'}
        
        # Extract quality scores over time
        quality_scores = []
        for report in self.session_reports:
            score = report['review_report']['quality_analysis']['metrics']['overall_score']
            quality_scores.append(score)
        
        return {
            'quality_trend': 'improving' if quality_scores[-1] > quality_scores[0] else 'declining',
            'average_quality': statistics.mean(quality_scores),
            'quality_range': {'min': min(quality_scores), 'max': max(quality_scores)},
            'total_improvements_suggested': sum(
                len(report['improvement_plan']['recommendations']) 
                for report in self.session_reports
            )
        }


# ===================================================================================
# UTILITY FUNCTIONS
# ===================================================================================

async def run_comprehensive_review(df_path: str, 
                                 output_dir: str = None,
                                 original_df_path: str = None) -> Dict[str, Any]:
    """
    Convenience function to run comprehensive review on a DataFrame file
    
    Args:
        df_path: Path to processed results Excel/CSV file
        output_dir: Directory to save reports
        original_df_path: Path to original data file (optional)
        
    Returns:
        Comprehensive review results
    """
    # Load data
    if df_path.endswith('.xlsx'):
        df = pd.read_excel(df_path)
    else:
        df = pd.read_csv(df_path)
    
    original_df = None
    if original_df_path:
        if original_df_path.endswith('.xlsx'):
            original_df = pd.read_excel(original_df_path)
        else:
            original_df = pd.read_csv(original_df_path)
    
    # Create review agent and run comprehensive review
    review_agent = ComprehensiveReviewAgent()
    
    results = await review_agent.comprehensive_review(
        results_df=df,
        original_df=original_df,
        output_dir=output_dir or "data/review_reports"
    )
    
    return results


def create_fake_data_summary(issues: List[QualityIssue]) -> Dict[str, Any]:
    """Create summary of fake data issues for quick analysis"""
    fake_issues = [issue for issue in issues if issue.category == 'fake_data']
    
    if not fake_issues:
        return {'message': 'No fake data detected'}
    
    fake_summary = {
        'total_fake_entries': len(fake_issues),
        'fake_by_type': Counter(issue.issue_type for issue in fake_issues),
        'fake_by_field': Counter(issue.field for issue in fake_issues),
        'examples': []
    }
    
    # Add examples
    for issue_type in fake_summary['fake_by_type'].keys():
        examples = [issue for issue in fake_issues if issue.issue_type == issue_type][:3]
        fake_summary['examples'].extend([
            {
                'type': issue.issue_type,
                'field': issue.field,
                'value': issue.value,
                'record_id': issue.record_id
            }
            for issue in examples
        ])
    
    return fake_summary


# ===================================================================================
# MAIN EXECUTION
# ===================================================================================

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create sample data for testing
        sample_data = {
            'gdr_nome': ['Empresa Teste', 'Negócio Real', 'test company', 'Loja ABC'],
            'gdr_telefone_1': ['11111111111', '+5511987654321', '123456789', '+5511999887766'],
            'gdr_email_1': ['test@test.com', 'contato@empresa.com', 'fake@fake.com', 'vendas@loja.com'],
            'gdr_score_sinergia': [85, 92, 150, 78],  # Note: 150 is invalid
            'gdr_website': ['test.com', 'https://empresa.com', 'fake.com', 'https://loja.com.br']
        }
        
        df = pd.DataFrame(sample_data)
        
        # Run comprehensive review
        review_agent = ComprehensiveReviewAgent()
        await review_agent.start_review_session("test_session")
        
        results = await review_agent.comprehensive_review(
            results_df=df,
            output_dir="data/review_reports"
        )
        
        print("Review completed!")
        print(f"Quality Score: {results['summary']['overall_assessment']['quality_score']:.2f}")
        print(f"Issues found: {len(results['review_report']['quality_analysis']['issues'])}")
        print(f"Recommendations: {results['summary']['recommendations_summary']['total_recommendations']}")
        
        # Show fake data summary
        issues = [QualityIssue(**issue) for issue in results['review_report']['quality_analysis']['issues']]
        fake_summary = create_fake_data_summary(issues)
        print(f"\nFake data summary: {fake_summary}")
    
    # Run example
    import asyncio
    asyncio.run(main())