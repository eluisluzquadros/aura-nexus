import re
import logging
from typing import Dict, List, Optional, Set
import phonenumbers
from urllib.parse import urlparse, parse_qs

# ===================================================================================
# CÉLULA 4: COMPONENTES DE EXTRAÇÃO E VALIDAÇÃO
# ===================================================================================

class WhatsAppLinkExtractor:
    """Extrator avançado de WhatsApp para links encurtados"""
    
    def __init__(self):
        self.shortlink_patterns = [
            r'wa\.link/([a-zA-Z0-9]+)',
            r'bit\.ly/([a-zA-Z0-9]+)',
            r'wa\.me/([0-9+]+)',
            r'api\.whatsapp\.com/send\?phone=([0-9+]+)',
            r'web\.whatsapp\.com/send\?phone=([0-9+]+)',
            r'chat\.whatsapp\.com/([a-zA-Z0-9]+)'
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def extract_from_shortlink(self, url: str) -> Optional[str]:
        """Extrai número WhatsApp de links encurtados"""
        try:
            url = self._clean_url(url)
            if not url:
                return None
            
            # Verificar se é número direto
            if direct_number := self._extract_direct_number(url):
                return self._format_brazil_number(direct_number)
            
            # Se é shortlink, seguir redirects
            if any(pattern in url for pattern in ['wa.link', 'bit.ly', 'short.link']):
                final_url = await self._follow_redirects(url)
                if final_url and final_url != url:
                    if number := self._extract_direct_number(final_url):
                        return self._format_brazil_number(number)
            
            # Tentar extrair de wa.link específico
            if 'wa.link' in url:
                number = await self._extract_from_wa_link(url)
                if number:
                    return self._format_brazil_number(number)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair WhatsApp de {url}: {e}")
            return None
    
    def _clean_url(self, url: str) -> Optional[str]:
        """Limpa e valida URL"""
        if not url or not isinstance(url, str):
            return None
        
        url = url.strip()
        
        if not url.startswith(('http://', 'https://')):
            if 'wa.link' in url or 'wa.me' in url:
                url = 'https://' + url
            else:
                url = 'https://' + url
        
        return url
    
    def _extract_direct_number(self, url: str) -> Optional[str]:
        """Extrai número direto da URL"""
        patterns = [
            r'wa\.me/(\+?[0-9]+)',
            r'phone=(\+?[0-9]+)',
            r'text=.*?(\+?55[0-9]{10,11})',
            r'/(\+?55[0-9]{10,11})(?:[?&]|$)'
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, url):
                return match.group(1)
        
        return None
    
    async def _follow_redirects(self, url: str, max_redirects: int = 5) -> Optional[str]:
        """Segue cadeia de redirects"""
        try:
            current_url = url
            
            for _ in range(max_redirects):
                response = await asyncio.to_thread(
                    self.session.head, 
                    current_url, 
                    allow_redirects=False,
                    timeout=5
                )
                
                if response.status_code in [301, 302, 303, 307, 308]:
                    location = response.headers.get('Location')
                    if location:
                        current_url = location
                        if 'wa.me' in current_url or 'whatsapp.com' in current_url:
                            return current_url
                    else:
                        break
                else:
                    # Fazer GET completo se necessário
                    response = await asyncio.to_thread(
                        self.session.get,
                        current_url,
                        allow_redirects=True,
                        timeout=5
                    )
                    return response.url
            
            return current_url
            
        except Exception as e:
            logger.debug(f"Erro ao seguir redirects de {url}: {e}")
            return None
    
    async def _extract_from_wa_link(self, url: str) -> Optional[str]:
        """Extrai número específico de wa.link"""
        try:
            response = await asyncio.to_thread(
                self.session.get,
                url,
                timeout=10
            )
            
            content = response.text[:5000]
            
            # Padrões de extração
            patterns = [
                r'wa\.me/(\+?[0-9]+)',
                r'"phone":"(\+?[0-9]+)"',
                r'phone=(\+?[0-9]+)',
                r'whatsapp://send\?phone=(\+?[0-9]+)'
            ]
            
            for pattern in patterns:
                if match := re.search(pattern, content):
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao extrair de wa.link {url}: {e}")
            return None
    
    def _format_brazil_number(self, number: str) -> str:
        """Formata número para padrão brasileiro"""
        if not number:
            return ""
        
        # Limpar número
        number = re.sub(r'[^\d+]', '', number)
        
        # Adicionar código do país se necessário
        if not number.startswith('+'):
            if not number.startswith('55'):
                number = '55' + number
            number = '+' + number
        
        # Validar formato brasileiro
        if number.startswith('+55'):
            clean_number = number[3:]
            if len(clean_number) == 10 or len(clean_number) == 11:
                return number
            elif len(clean_number) == 8 or len(clean_number) == 9:
                # Assumir São Paulo se não tem DDD
                return '+5511' + clean_number
        
        return number
    
    async def extract_whatsapp_from_text(self, text: str) -> List[str]:
        """Extrai todos os links/números WhatsApp de um texto"""
        if not text:
            return []
        
        found_numbers = set()
        
        # Padrões de shortlinks
        shortlink_patterns = [
            r'(?:https?://)?wa\.link/[a-zA-Z0-9]+',
            r'(?:https?://)?bit\.ly/[a-zA-Z0-9]+',
            r'(?:https?://)?wa\.me/\+?[0-9]+',
            r'(?:https?://)?api\.whatsapp\.com/send\?phone=\+?[0-9]+'
        ]
        
        # Buscar shortlinks
        for pattern in shortlink_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                url = match.group(0)
                if number := await self.extract_from_shortlink(url):
                    found_numbers.add(number)
        
        # Padrões de contexto
        context_patterns = [
            r'(?:whatsapp|whats|wpp|zap)[\s:]*(\+?55\s?[0-9]{2}\s?[0-9]{4,5}[\s\-]?[0-9]{4})',
            r'(\+?55\s?[0-9]{2}\s?[0-9]{4,5}[\s\-]?[0-9]{4})[\s]*(?:whatsapp|whats|wpp)',
            r'📱[\s]*(\+?55\s?[0-9]{2}\s?[0-9]{4,5}[\s\-]?[0-9]{4})',
            r'💬[\s]*(\+?55\s?[0-9]{2}\s?[0-9]{4,5}[\s\-]?[0-9]{4})',
            r'chama\s+no\s+(?:whats|zap)[\s:]*(\d{2}\s?\d{4,5}[\s\-]?\d{4})'
        ]
        
        # Buscar números em contexto
        for pattern in context_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                number = match.group(1)
                formatted = self._format_brazil_number(number)
                if formatted:
                    found_numbers.add(formatted)
        
        return list(found_numbers)


class BrazilianContactExtractor:
    """Extrator avançado de contatos brasileiros"""
    
    def __init__(self):
        self.patterns = {
            'whatsapp': [
                r'wa\.me/(\+?55\d{10,11})',
                r'api\.whatsapp\.com/send\?phone=(\+?55\d{10,11})',
                r'whats(?:app)?[\s:]*(\+?55?\s?\d{2}\s?\d{4,5}[\s\-]?\d{4})',
                r'(\+?55?\s?\d{2}\s?\d{4,5}[\s\-]?\d{4})[\s]*(?:whats|wpp|zap)',
                r'📱[\s]*(\+?55?\s?\d{2}\s?\d{4,5}[\s\-]?\d{4})',
                r'💬[\s]*(\+?55?\s?\d{2}\s?\d{4,5}[\s\-]?\d{4})',
                r'chama\s+no\s+(?:whats|zap)[\s:]*(\d{2}\s?\d{4,5}[\s\-]?\d{4})',
                r'(?:whats|zap)[\s:]*\((\d{2})\)\s?(\d{4,5})[\s\-]?(\d{4})'
            ],
            'phone': [
                r'(?:tel|fone|telefone|celular|fixo)[\s:]*(\+?55?\s?\(?\d{2}\)?\s?\d{4,5}[\s\-]?\d{4})',
                r'\((\d{2})\)\s?(\d{4,5})[\s\-]?(\d{4})',
                r'\+55\s?(\d{2})\s?(\d{4,5})[\s\-]?(\d{4})',
                r'\b(\d{2})\s?(\d{4,5})[\s\-]?(\d{4})\b',
                r'(\d{2})\.(\d{4,5})\.(\d{4})',
                r'(?:cel|celular)[\s:]*(\d{2}\s?\d{5}[\s\-]?\d{4})',
                r'(?:fixo|comercial)[\s:]*(\d{2}\s?\d{4}[\s\-]?\d{4})'
            ],
            'email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'(?:email|e-mail)[\s:]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+)\s*\[\s*at\s*\]\s*([a-zA-Z0-9.-]+)\s*\[\s*dot\s*\]\s*([a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})'
            ]
        }
        
        self.whatsapp_extractor = WhatsAppLinkExtractor()
        self.validation_cache = {}
        self.phone_validator = phonenumbers

    async def extract_all_contacts(self, text: str, existing_contacts: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extrai todos os tipos de contato do texto"""
        if not text:
            return {}
        
        # Verificar cache
        text_hash = hashlib.md5(text[:1000].encode()).hexdigest()
        if text_hash in self.validation_cache:
            return self.validation_cache[text_hash]
        
        # Normalizar texto
        text = self._normalize_text(text)
        
        # Extrair contatos
        contacts = {
            'phones': await self._extract_phones(text),
            'whatsapp_numbers': await self._extract_whatsapp(text),
            'emails': self._extract_emails(text),
            'extracted_at': datetime.now().isoformat()
        }
        
        # Mesclar com contatos existentes
        if existing_contacts:
            contacts = self._merge_contacts(contacts, existing_contacts)
        
        # Validar e formatar
        contacts = self._validate_and_format_contacts(contacts)
        
        # Calcular estatísticas
        contacts['statistics'] = self._calculate_statistics(contacts)
        
        # Cachear resultado
        self.validation_cache[text_hash] = contacts
        
        return contacts
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para extração"""
        # Manter o texto original mas adicionar espaços onde necessário
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
        return text
    
    async def _extract_phones(self, text: str) -> List[Dict[str, Any]]:
        """Extrai números de telefone com contexto"""
        phones = []
        seen = set()
        
        for i, pattern in enumerate(self.patterns['phone']):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                phone_parts = [g for g in match.groups() if g]
                phone_str = ''.join(phone_parts)
                
                # Limpar número
                phone_clean = re.sub(r'[^\d]', '', phone_str)
                
                # Validar tamanho
                if len(phone_clean) < 10 or len(phone_clean) > 13:
                    continue
                
                # Evitar duplicatas
                if phone_clean in seen:
                    continue
                seen.add(phone_clean)
                
                # Extrair contexto
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                # Determinar tipo
                phone_type = self._determine_phone_type(phone_clean, context)
                
                phones.append({
                    'number': phone_clean,
                    'formatted': self._format_phone(phone_clean),
                    'type': phone_type,
                    'context': context,
                    'pattern_index': i
                })
        
        return phones
    
    async def _extract_whatsapp(self, text: str) -> List[Dict[str, Any]]:
        """Extrai números WhatsApp com alta precisão"""
        whatsapp_numbers = []
        seen = set()
        
        # Usar extrator especializado para links
        link_numbers = await self.whatsapp_extractor.extract_whatsapp_from_text(text)
        for number in link_numbers:
            if number not in seen:
                seen.add(number)
                whatsapp_numbers.append({
                    'number': re.sub(r'[^\d]', '', number),
                    'formatted': number,
                    'context': 'Link WhatsApp',
                    'confidence': 0.95,
                    'source': 'link'
                })
        
        # Buscar padrões diretos
        for i, pattern in enumerate(self.patterns['whatsapp']):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = [g for g in match.groups() if g]
                
                if len(groups) == 3:  # Padrão com parênteses
                    number = ''.join(groups)
                elif len(groups) == 1:
                    number = groups[0]
                else:
                    continue
                
                # Limpar número
                number_clean = re.sub(r'[^\d]', '', number)
                
                # Adicionar código do país
                if not number_clean.startswith('55') and len(number_clean) <= 11:
                    number_clean = '55' + number_clean
                
                # Validar tamanho
                if len(number_clean) < 12 or len(number_clean) > 13:
                    continue
                
                # Evitar duplicatas
                if number_clean in seen:
                    continue
                seen.add(number_clean)
                
                # Extrair contexto
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                whatsapp_numbers.append({
                    'number': number_clean,
                    'formatted': self._format_whatsapp(number_clean),
                    'context': context,
                    'confidence': self._calculate_whatsapp_confidence(context, i),
                    'pattern_index': i,
                    'source': 'pattern'
                })
        
        # Ordenar por confiança
        whatsapp_numbers.sort(key=lambda x: x['confidence'], reverse=True)
        
        return whatsapp_numbers
    
    def _extract_emails(self, text: str) -> List[Dict[str, Any]]:
        """Extrai emails válidos"""
        emails = []
        seen = set()
        
        for i, pattern in enumerate(self.patterns['email']):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Processar diferentes formatos
                if pattern == self.patterns['email'][3]:  # [at] [dot]
                    email = f"{match.group(1)}@{match.group(2)}.{match.group(3)}"
                elif pattern == self.patterns['email'][4]:  # @ .
                    email = f"{match.group(1)}@{match.group(2)}.{match.group(3)}"
                else:
                    email = match.group(1) if match.groups() else match.group(0)
                
                email = email.lower().strip()
                
                # Validar email
                if not self._is_valid_email(email):
                    continue
                
                # Evitar duplicatas
                if email in seen:
                    continue
                seen.add(email)
                
                # Extrair contexto
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                # Determinar tipo
                email_type = self._determine_email_type(email)
                
                emails.append({
                    'email': email,
                    'type': email_type,
                    'context': context,
                    'pattern_index': i
                })
        
        return emails
    
    def _format_phone(self, phone: str) -> str:
        """Formata telefone brasileiro"""
        phone = re.sub(r'[^\d]', '', phone)
        
        # Adicionar código do país
        if not phone.startswith('55'):
            phone = '55' + phone
        
        # Formatar
        if len(phone) == 13:  # +55 11 99999-9999
            return f"+{phone[:2]} ({phone[2:4]}) {phone[4:9]}-{phone[9:]}"
        elif len(phone) == 12:  # +55 11 9999-9999
            return f"+{phone[:2]} ({phone[2:4]}) {phone[4:8]}-{phone[8:]}"
        
        return phone
    
    def _format_whatsapp(self, number: str) -> str:
        """Formata número WhatsApp"""
        number = re.sub(r'[^\d]', '', number)
        
        if not number.startswith('+'):
            number = '+' + number
        
        return number
    
    def _determine_phone_type(self, phone: str, context: str) -> str:
        """Determina tipo de telefone"""
        context_lower = context.lower()
        
        # Verificar por contexto
        if any(word in context_lower for word in ['celular', 'cel', 'móvel', 'whats']):
            return 'mobile'
        elif any(word in context_lower for word in ['fixo', 'comercial', 'escritório']):
            return 'landline'
        
        # Verificar por formato
        phone_clean = re.sub(r'[^\d]', '', phone)
        if len(phone_clean) >= 11 or (len(phone_clean) == 9 and phone_clean[0] == '9'):
            return 'mobile'
        
        return 'unknown'
    
    def _calculate_whatsapp_confidence(self, context: str, pattern_index: int) -> float:
        """Calcula confiança de que é WhatsApp"""
        confidence = 0.5
        
        # Padrões mais confiáveis
        if pattern_index <= 1:
            confidence = 0.95
        elif pattern_index <= 5:
            confidence = 0.85
        
        # Verificar contexto
        context_lower = context.lower()
        whatsapp_words = ['whatsapp', 'whats', 'wpp', 'zap', '📱', '💬', 'chama']
        
        for word in whatsapp_words:
            if word in context_lower:
                confidence = min(confidence + 0.1, 1.0)
        
        return confidence
    
    def _is_valid_email(self, email: str) -> bool:
        """Valida email com regras rigorosas"""
        if not email or '@' not in email:
            return False
        
        # Padrão básico
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Domínios inválidos
        invalid_patterns = [
            'example.com', 'test.com', 'email.com', 'domain.com',
            'site.com', 'website.com', 'company.com', 'mail.com',
            'noreply@', 'no-reply@', 'donotreply@', 'admin@localhost'
        ]
        
        for invalid in invalid_patterns:
            if invalid in email:
                return False
        
        # Validar partes
        local, domain = email.split('@')
        
        # Tamanho do local
        if len(local) < 2 or len(local) > 64:
            return False
        
        # Domínio válido
        if len(domain) < 4 or '.' not in domain:
            return False
        
        # Não pode começar/terminar com ponto
        if local.startswith('.') or local.endswith('.'):
            return False
        
        return True
    
    def _determine_email_type(self, email: str) -> str:
        """Determina tipo de email"""
        local = email.split('@')[0]
        
        # Padrões comuns
        if any(word in local for word in ['info', 'contato', 'contact', 'atendimento']):
            return 'general'
        elif any(word in local for word in ['vendas', 'sales', 'comercial']):
            return 'sales'
        elif any(word in local for word in ['suporte', 'support', 'help', 'sac']):
            return 'support'
        elif any(word in local for word in ['financeiro', 'finance', 'billing']):
            return 'finance'
        elif re.match(r'^[a-z]+\.[a-z]+', local):
            return 'personal'
        
        return 'other'
    
    def _merge_contacts(self, new_contacts: Dict, existing_contacts: Dict) -> Dict:
        """Mescla contatos novos com existentes inteligentemente"""
        merged = {
            'phones': [],
            'whatsapp_numbers': [],
            'emails': []
        }
        
        # Mesclar telefones
        all_phones = new_contacts.get('phones', []) + existing_contacts.get('phones', [])
        seen_phones = set()
        for phone in all_phones:
            number = phone.get('number', '')
            if number and number not in seen_phones:
                merged['phones'].append(phone)
                seen_phones.add(number)
        
        # Mesclar WhatsApp
        all_whatsapp = new_contacts.get('whatsapp_numbers', []) + existing_contacts.get('whatsapp_numbers', [])
        seen_whatsapp = set()
        for wa in sorted(all_whatsapp, key=lambda x: x.get('confidence', 0), reverse=True):
            number = wa.get('number', '')
            if number and number not in seen_whatsapp:
                merged['whatsapp_numbers'].append(wa)
                seen_whatsapp.add(number)
        
        # Mesclar emails
        all_emails = new_contacts.get('emails', []) + existing_contacts.get('emails', [])
        seen_emails = set()
        for email_data in all_emails:
            email = email_data.get('email', '')
            if email and email not in seen_emails:
                merged['emails'].append(email_data)
                seen_emails.add(email)
        
        return merged
    
    def _validate_and_format_contacts(self, contacts: Dict) -> Dict:
        """Valida e formata contatos finais com phonenumbers"""
        # Validar telefones
        validated_phones = []
        for phone_data in contacts.get('phones', []):
            try:
                # Adicionar + se necessário
                number = phone_data['number']
                if not number.startswith('+'):
                    number = '+' + number
                
                parsed = self.phone_validator.parse(number, 'BR')
                if self.phone_validator.is_valid_number(parsed):
                    phone_data['valid'] = True
                    phone_data['carrier'] = carrier.name_for_number(parsed, 'pt')
                    phone_data['region'] = geocoder.description_for_number(parsed, 'pt')
                    validated_phones.append(phone_data)
                else:
                    phone_data['valid'] = False
                    validated_phones.append(phone_data)
            except:
                phone_data['valid'] = False
                validated_phones.append(phone_data)
        
        contacts['phones'] = validated_phones
        
        # Validar WhatsApp
        validated_whatsapp = []
        for wa_data in contacts.get('whatsapp_numbers', []):
            try:
                number = wa_data['number']
                if not number.startswith('+'):
                    number = '+' + number
                
                parsed = self.phone_validator.parse(number, 'BR')
                if self.phone_validator.is_valid_number(parsed):
                    wa_data['valid'] = True
                    validated_whatsapp.append(wa_data)
                else:
                    wa_data['valid'] = False
                    # Manter se confiança alta
                    if wa_data.get('confidence', 0) > 0.8:
                        validated_whatsapp.append(wa_data)
            except:
                wa_data['valid'] = False
                if wa_data.get('confidence', 0) > 0.8:
                    validated_whatsapp.append(wa_data)
        
        contacts['whatsapp_numbers'] = validated_whatsapp
        
        return contacts
    
    def _calculate_statistics(self, contacts: Dict) -> Dict:
        """Calcula estatísticas dos contatos extraídos"""
        stats = {
            'total_phones': len(contacts.get('phones', [])),
            'valid_phones': len([p for p in contacts.get('phones', []) if p.get('valid', False)]),
            'mobile_phones': len([p for p in contacts.get('phones', []) if p.get('type') == 'mobile']),
            'landline_phones': len([p for p in contacts.get('phones', []) if p.get('type') == 'landline']),
            'total_whatsapp': len(contacts.get('whatsapp_numbers', [])),
            'high_confidence_whatsapp': len([w for w in contacts.get('whatsapp_numbers', []) 
                                           if w.get('confidence', 0) > 0.8]),
            'valid_whatsapp': len([w for w in contacts.get('whatsapp_numbers', []) 
                                 if w.get('valid', False)]),
            'total_emails': len(contacts.get('emails', [])),
            'email_types': defaultdict(int)
        }
        
        # Contar tipos de email
        for email_data in contacts.get('emails', []):
            email_type = email_data.get('type', 'other')
            stats['email_types'][email_type] += 1
        
        stats['email_types'] = dict(stats['email_types'])
        
        return stats