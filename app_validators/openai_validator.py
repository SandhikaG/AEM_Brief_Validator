"""
OpenAI Validator Module
Hybrid validation: Rule-based + AI-powered checks
"""

import os
from typing import Dict, List, Tuple
import re
from openai import OpenAI


class OpenAIValidator:
    """AI-powered validation using OpenAI API."""
    
    # Known common abbreviations (beyond Fortinet terms)
    COMMON_ABBREVIATIONS = {
        'ci/cd', 'cicd', 'ci-cd',
        'sso', 'mfa', '2fa',
        'saas', 'paas', 'iaas',
        'gdpr', 'hipaa', 'pci-dss', 'sox',
        'ceo', 'cto', 'cio', 'ciso',
        'b2b', 'b2c',
        'roi', 'kpi',
        'rest', 'soap', 'json', 'xml',
        'tcp', 'udp', 'ip', 'dns', 'http', 'https', 'ssh', 'ftp',
        'lan', 'wan', 'vpn', 'nat',
        'cpu', 'gpu', 'ram', 'ssd',
        'ui', 'ux',
        'pdf', 'csv',
        'usa', 'uk', 'eu'
    }
    
    # Title Case Prompt (from client)
    TITLE_CASE_PROMPT = """You are a verbatim casing machine.

Task:
1. Accept exactly one line of text.
2. Convert the entire line to strict US-English Title Case.
   • Capitalize all nouns, verbs, adjectives, adverbs, pronouns.
   • Lowercase articles (a, an, the), coordinating conjunctions (vs, and, but, or, for, nor), and prepositions ≤4 letters unless they are the first or last word.

CRITICAL EXCEPTIONS - PRESERVE EXACTLY AS-IS:
   • Fortinet products: ANY word starting with "Forti" (FortiCNAPP, FortiDevOps, FortiCode, FortiPentest, FortiGuard, etc.) - preserve EXACT casing
   • Acronym plurals: Uppercase acronyms ending in lowercase 's' (VPNs, APIs, URLs, etc.) - preserve as-is
   • Technical acronyms: SIEM, SOAR, XDR, EDR, NDR, MDR, IPS, IDS, WAF, DDoS, etc. - keep UPPERCASE

3. If the converted string is character-for-character identical to the input, output exactly: No change
   Otherwise output the converted string—do not drop, add, or reorder any characters, words, or punctuation.

Zero tolerance for omissions.

Input:
{text}

Output:"""

    # Sentence Case Prompt (from client)
    SENTENCE_CASE_PROMPT = """You are a sentence-case formatter.

Task: convert the provided string to exact US professional English Sentence Case and return ONLY the result or "No change" if already correct.

Sentence Case rules:
* Capitalize the first word and proper nouns only.
* Generic cybersecurity terms (firewall, threat actor, endpoint detection, etc.) are NOT proper nouns.

CRITICAL EXCEPTIONS - PRESERVE EXACTLY AS-IS:
* Fortinet products: ANY word starting with "Forti" (FortiCNAPP, FortiDevOps, FortiCode, FortiPentest, FortiGuard, etc.) - preserve EXACT casing
* Acronym plurals: Uppercase acronyms ending in lowercase 's' (VPNs, APIs, URLs, SDKs, etc.) - preserve as-is
* Technical acronyms: SIEM, SOAR, XDR, EDR, NDR, MDR, IPS, IDS, WAF, DDoS, AppSec, DevSecOps, etc. - keep UPPERCASE

Input:
{text}

Output:"""

    # Unknown Terms Detection Prompt
    UNKNOWN_TERMS_PROMPT = """You are a technical abbreviation and acronym detector for cybersecurity content.

Known Fortinet Terms: {fortinet_terms}

Common Abbreviations: {common_terms}

Task:
Analyze this text and identify ANY technical abbreviations, acronyms, or specialized terms that are NOT in the known lists above.

Rules:
1. Only flag technical/specialized terms (not common English words)
2. Flag abbreviations in ANY case (uppercase, lowercase, mixed)
3. Include product names, technical acronyms, industry terms
4. Do NOT flag terms already in the known lists

Text to analyze:
{text}

If unknown terms found, respond in this format:
UNKNOWN: [term1], [term2], [term3]

If no unknown terms, respond:
CLEAR

Output:"""

    def __init__(self, api_key: str, fortinet_shorthands: Dict[str, str]):
        """Initialize OpenAI validator."""
        self.client = OpenAI(api_key=api_key)
        self.fortinet_shorthands = fortinet_shorthands
        
    def validate_title_case(self, text: str) -> Tuple[bool, str, str]:
        """
        Validate Title Case using OpenAI.
        
        Returns:
            (is_valid, corrected_text, explanation)
        """
        if not text:
            return True, "", ""
        
        try:
            prompt = self.TITLE_CASE_PROMPT.format(text=text)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise text formatting assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == "No change":
                return True, text, "Already in correct Title Case"
            else:
                return False, result, f"Should be: {result}"
                
        except Exception as e:
            print(f"OpenAI Title Case Error: {e}")
            return True, text, f"AI validation failed: {str(e)}"
    
    def validate_sentence_case(self, text: str) -> Tuple[bool, str, str]:
        """
        Validate Sentence case using OpenAI.
        
        Returns:
            (is_valid, corrected_text, explanation)
        """
        if not text:
            return True, "", ""
        
        try:
            prompt = self.SENTENCE_CASE_PROMPT.format(text=text)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise text formatting assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == "No change":
                return True, text, "Already in correct Sentence case"
            else:
                return False, result, f"Should be: {result}"
                
        except Exception as e:
            print(f"OpenAI Sentence Case Error: {e}")
            return True, text, f"AI validation failed: {str(e)}"
    
    def detect_unknown_terms(self, text: str) -> List[str]:
        """
        Detect unknown technical terms/abbreviations using OpenAI.
        
        Returns:
            List of unknown terms found
        """
        if not text:
            return []
        
        try:
            # Prepare known terms lists
            fortinet_terms = ", ".join(self.fortinet_shorthands.keys())
            common_terms = ", ".join(self.COMMON_ABBREVIATIONS)
            
            prompt = self.UNKNOWN_TERMS_PROMPT.format(
                fortinet_terms=fortinet_terms,
                common_terms=common_terms,
                text=text
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical term analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == "CLEAR":
                return []
            
            # Parse unknown terms
            if result.startswith("UNKNOWN:"):
                terms_str = result.replace("UNKNOWN:", "").strip()
                terms = [t.strip() for t in terms_str.split(",")]
                return [t for t in terms if t]  # Filter empty strings
            
            return []
                
        except Exception as e:
            print(f"OpenAI Unknown Terms Error: {e}")
            return []


class HybridValidator:
    """Combines rule-based and AI validation."""
    
    def __init__(self, openai_api_key: str, fortinet_shorthands: Dict[str, str]):
        """Initialize hybrid validator."""
        self.ai_validator = OpenAIValidator(openai_api_key, fortinet_shorthands)
        self.fortinet_shorthands = fortinet_shorthands
    
    def validate_title_case_hybrid(self, text: str, rule_based_result: Tuple[bool, str]) -> Dict:
        """
        Hybrid Title Case validation.
        
        Args:
            text: Text to validate
            rule_based_result: (is_valid, corrected_text) from rule-based validator
            
        Returns:
            {
                'rule_based_valid': bool,
                'rule_based_corrected': str,
                'ai_valid': bool,
                'ai_corrected': str,
                'ai_explanation': str,
                'unknown_terms': List[str],
                'agreement': bool,
                'final_recommendation': str
            }
        """
        rule_valid, rule_corrected = rule_based_result
        
        # AI validation
        ai_valid, ai_corrected, ai_explanation = self.ai_validator.validate_title_case(text)
        
        # Unknown terms detection
        unknown_terms = self.ai_validator.detect_unknown_terms(text)
        
        # Check agreement
        agreement = (rule_valid == ai_valid)
        
        # Final recommendation (prefer AI if disagreement)
        if agreement:
            final_recommendation = rule_corrected if not rule_valid else text
        else:
            final_recommendation = ai_corrected if not ai_valid else text
        
        return {
            'rule_based_valid': rule_valid,
            'rule_based_corrected': rule_corrected,
            'ai_valid': ai_valid,
            'ai_corrected': ai_corrected,
            'ai_explanation': ai_explanation,
            'unknown_terms': unknown_terms,
            'agreement': agreement,
            'final_recommendation': final_recommendation
        }
    
    def validate_sentence_case_hybrid(self, text: str, rule_based_result: Tuple[bool, str]) -> Dict:
        """
        Hybrid Sentence case validation.
        
        Args:
            text: Text to validate
            rule_based_result: (is_valid, corrected_text) from rule-based validator
            
        Returns:
            {
                'rule_based_valid': bool,
                'rule_based_corrected': str,
                'ai_valid': bool,
                'ai_corrected': str,
                'ai_explanation': str,
                'unknown_terms': List[str],
                'agreement': bool,
                'final_recommendation': str
            }
        """
        rule_valid, rule_corrected = rule_based_result
        
        # AI validation
        ai_valid, ai_corrected, ai_explanation = self.ai_validator.validate_sentence_case(text)
        
        # Unknown terms detection
        unknown_terms = self.ai_validator.detect_unknown_terms(text)
        
        # Check agreement
        agreement = (rule_valid == ai_valid)
        
        # Final recommendation (prefer AI if disagreement)
        if agreement:
            final_recommendation = rule_corrected if not rule_valid else text
        else:
            final_recommendation = ai_corrected if not ai_valid else text
        
        return {
            'rule_based_valid': rule_valid,
            'rule_based_corrected': rule_corrected,
            'ai_valid': ai_valid,
            'ai_corrected': ai_corrected,
            'ai_explanation': ai_explanation,
            'unknown_terms': unknown_terms,
            'agreement': agreement,
            'final_recommendation': final_recommendation
        }
    
    def scan_all_unknown_terms(self, brief_data: Dict) -> Dict[str, List[str]]:
        """
        Scan entire brief for unknown terms.
        
        Returns:
            {
                'meta_title': [...],
                'meta_description': [...],
                'h1': [...],
                ...
            }
        """
        unknown_by_section = {}
        
        # Check all sections
        sections = [
            ('meta_title', brief_data.get('meta_title', '')),
            ('meta_description', brief_data.get('meta_description', '')),
            ('h1', brief_data.get('h1', '')),
            ('header_caption', brief_data.get('header_caption', '')),
        ]
        
        # Headers
        for idx, header in enumerate(brief_data.get('headers', [])):
            sections.append((f"{header['level']}_{idx}", header['text']))
        
        # FAQs
        faqs = brief_data.get('faqs', {})
        if faqs.get('header'):
            sections.append(('faq_header', faqs['header']))
        
        for idx, faq in enumerate(faqs.get('questions', [])):
            sections.append((f'faq_q_{idx}', faq['question']))
            sections.append((f'faq_a_{idx}', faq['answer']))
        
        # Product Nav
        for idx, tab in enumerate(brief_data.get('product_nav', {}).get('tabs', [])):
            sections.append((f'nav_{idx}', tab['text']))
        
        # CTA
        cta = brief_data.get('cta', {})
        if cta.get('caption'):
            sections.append(('cta_caption', cta['caption']))
        if cta.get('text'):
            sections.append(('cta_text', cta['text']))
        
        # Detect unknown terms in each section
        for section_name, text in sections:
            if text:
                unknown = self.ai_validator.detect_unknown_terms(text)
                if unknown:
                    unknown_by_section[section_name] = unknown
        
        return unknown_by_section