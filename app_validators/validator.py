"""
Fortinet Brief Validator - COMPLETE HYBRID VERSION
This validator actually calls OpenAI API when enabled
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
import pandas as pd

# Import hybrid validator
try:
    from app_validators.openai_validator import HybridValidator
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False
    print("⚠ HybridValidator not found - using rule-based only")


class Status(Enum):
    """Validation status enum."""
    ACCEPTED = "✓ PASS"
    REJECTED = "✗ REJECTED"


@dataclass
class ValidationResult:
    """Stores a single validation result."""
    use_case: str
    criterion: str
    location: str
    status: Status
    details: str
    category: str
    # Hybrid fields
    ai_validated: bool = False
    ai_result: str = ""
    unknown_terms: List[str] = None


class AEMBriefReviewer:
    """Validates Fortinet briefs - HYBRID VERSION."""
    
    FORTINET_SHORTHANDS = {
        # Application & DevSec
        "appsec": "AppSec", "devsecops": "DevSecOps", "forticspm": "FortiCSPM",
        "fortiweb": "FortiWeb", "fortiapisec": "FortiAPISec",
        "fortiapimanagement": "FortiAPIManagement", "fortiapigateway": "FortiAPIGateway",
        "fortidevops": "FortiDevOps", 
        #"forticnapp": "FortiCNAPP",
        "forticode": "FortiCode", "fortipentest": "FortiPentest",
        
        # Zero Trust & Architecture
        "zero trust": "Zero Trust", "ztna": "ZTNA", "sase": "SASE",
        "sd-wan": "SD-WAN", "fortiguard": "FortiGuard", "fim": "FIM",
        "zam": "ZAM", "fabric": "Fabric",
        
        # Detection & Response
        "xdr": "XDR", "ndr": "NDR", "edr": "EDR", "mdr": "MDR",
        "siem": "SIEM", "soar": "SOAR", "ueba": "UEBA",
        "fortixdr": "FortiXDR", "fortisiem": "FortiSIEM", "fortisoc": "FortiSOC",
        
        # Threat & Security
        "ddos": "DDoS", "apt": "APT", "ips": "IPS", "ids": "IDS",
        "waf": "WAF", 
         #"vpns": "VPNs", "casb": "CASB",
        "dlp": "DLP", "deception": "Deception", "rtbh": "RTBH",
        
        # Network & Firewall
        "fortigate": "FortiGate", "fortiproxy": "FortiProxy",
        "fortiswitch": "FortiSwitch", "fortiap": "FortiAP",
        "forticlient": "FortiClient", "fortiauthenticator": "FortiAuthenticator",
        "fortitoken": "FortiToken", "fortinac": "FortiNAC",
        "fortianalyzer": "FortiAnalyzer", "fortimanager": "FortiManager",
        "fortimail": "FortiMail", "fortisandbox": "FortiSandbox",
        "fortiddos": "FortiDDoS",
        
        # Cloud & Infrastructure
        "cspm": "CSPM", "cwpp": "CWPP", "iac": "IaC", "it-ot": "IT-OT",
        "vpc": "VPC", "ec2": "EC2", "s3": "S3", "vm": "VM", "vms": "VMs",
        "vmware": "VMware", "hyper-v": "Hyper-V", "azure": "Azure",
        "aws": "AWS", "gcp": "GCP", "kubernetes": "Kubernetes",
        "containers": "Containers", "docker": "Docker",
        
        # OT / IoT / Industry
        "ot": "OT", "iot": "IoT", "ics": "ICS", "scada": "SCADA",
        "fortiot": "FortiOT",
        
        # AI / Automation
        "ai": "AI", "ml": "ML", "rpa": "RPA", "aops": "AIOps",
        "fortiai": "FortiAI",
        
        # APIs
        "api": "API", "apis": "APIs"
    }

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize validator with optional OpenAI support."""
        self.results: List[ValidationResult] = []
        self.unknown_terms_report: Dict[str, List[str]] = {}
        
        # Initialize hybrid validator
        if openai_api_key and HYBRID_AVAILABLE:
            try:
                self.hybrid_validator = HybridValidator(openai_api_key, self.FORTINET_SHORTHANDS)
                print("✓ Hybrid validation ENABLED (OpenAI API will be called)")
            except Exception as e:
                self.hybrid_validator = None
                print(f"✗ Hybrid validation failed to initialize: {e}")
        else:
            self.hybrid_validator = None
            if not HYBRID_AVAILABLE:
                print("⚠ HybridValidator module not found")
            elif not openai_api_key:
                print("⚠ No OpenAI API key provided")
    def _normalize_fortinet_shorthands(self, text: str) -> str:
        """Normalize Fortinet-approved shorthands and preserve Forti* products."""
        if not text:
            return text
    

        def replace(match):
            prefix = match.group(1) or ""
            core = match.group(2)
            suffix = match.group(3) or ""
            
            # ✅ PRESERVE ALL FORTINET PRODUCTS (FortiCNAPP, FortiDevOps, etc.)
            if core.lower().startswith('forti'):
                # Keep exact casing for Fortinet products
                return match.group(0)
            
            # Check dictionary for other terms
            core_lower = core.lower()
            return f"{prefix}{self.FORTINET_SHORTHANDS.get(core_lower, core)}{suffix}"

        pattern = r'(\()?(\b[a-zA-Z\-]+\b)(\)?\??)'
        return re.sub(pattern, replace, text)            
        
    def _fix_acronym_plurals_rule_based(self, text: str) -> str:
        """Fix common acronym plural mistakes in rule-based validation."""
        import re
        
        # Pattern: Word boundary + Capital letter + lowercase letters + lowercase 's' + word boundary
        # This catches: Vpns, Apis, Urls, Sdks, Vms, Ips, Faqs, etc.
        acronym_fixes = {
            r'\bVpns\b': 'VPNs',
            r'\bApis\b': 'APIs', 
            r'\bUrls\b': 'URLs',
            r'\bSdks\b': 'SDKs',
            r'\bVms\b': 'VMs',
            r'\bIps\b': 'IPs',
            r'\bIds\b': 'IDs',
            r'\bFaqs\b': 'FAQs',
            r'\bPdfs\b': 'PDFs',
            r'\bCsvs\b': 'CSVs',
            r'\bSlas\b': 'SLAs',
            r'\bKpis\b': 'KPIs',
        }
        
        for pattern, replacement in acronym_fixes.items():
            text = re.sub(pattern, replacement, text)
        
        return text

    def review_brief(self, brief_data: Dict[str, Any]) -> List[ValidationResult]:
        """Main validation with hybrid support."""
        self.results = []
        self.unknown_terms_report = {}
        
        # # Scan for unknown terms if hybrid enabled
        # if self.hybrid_validator:
        #     print("🔍 Scanning for unknown terms with OpenAI...")
        #     try:
        #         self.unknown_terms_report = self.hybrid_validator.scan_all_unknown_terms(brief_data)
        #         if self.unknown_terms_report:
        #             print(f"⚠ Found unknown terms in {len(self.unknown_terms_report)} sections")
        #     except Exception as e:
        #         print(f"✗ Unknown terms scan failed: {e}")
        
        # Run all validations
        self._validate_meta_title(brief_data.get('meta_title', ''))
        self._validate_meta_description(brief_data.get('meta_description', ''))
        self._validate_h1(brief_data.get('h1', ''))
        self._validate_header_caption(brief_data.get('header_caption', ''))
        
        for header in brief_data.get('headers', []):
            if header['level'] == 'H2':
                self._validate_h2(header['text'])
            elif header['level'] == 'H3':
                self._validate_h3(header['text'])
            elif header['level'] == 'H4':
                self._validate_h4(header['text'])
        
        faqs = brief_data.get('faqs', {})
        if faqs.get('header'):
            self._validate_faq_header(faqs['header'])
        
        for faq in faqs.get('questions', []):
            self._validate_faq_question(faq['question'])
            self._validate_faq_answer(faq['answer'])
        
        for tab in brief_data.get('product_nav', {}).get('tabs', []):
            self._validate_product_nav_tab(tab['text'])
        
        cta = brief_data.get('cta', {})
        if cta.get('text'):
            self._validate_cta_text(cta['text'])
        
        return self.results
    
    def _validate_capital_case(self, text: str) -> tuple[bool, str]:
        """Capital Case: Every word capitalized."""
        if not text:
            return True, ""
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\-]', '', word)
            if clean_word.lower().startswith('forti'):
                # Preserve exact casing for all Forti* products
                corrected_words.append(word)
                continue
            if word.isupper() and len(word) > 1:
                corrected_words.append(word)
            elif word.lower() == 'faqs':
                corrected_words.append('FAQs')
            elif word.lower() == 'vs':
                corrected_words.append('Vs')
            else:
                corrected = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
                corrected_words.append(corrected)
        
        corrected_text = ' '.join(corrected_words)
        corrected_text = self._fix_acronym_plurals_rule_based(corrected_text)
        return (text == corrected_text), corrected_text
    
    def _validate_title_case(self, text: str) -> tuple[bool, str]:
        """Title Case validation."""
        if not text:
            return True, ""
        
        lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'nor', 'in', 'of', 'to', 
                          'for', 'at', 'by', 'on', 'with', 'from', 'into'}
        
        words = text.split()
        corrected_words = []
        
        for i, word in enumerate(words):
            is_first = (i == 0)
            is_last = (i == len(words) - 1)
            
            # Check for Fortinet terms
            match = re.match(r'^([(\[]?)([\w\-]+)([)\]?,?\?]*)$', word)
            if match:
                prefix, core, suffix = match.groups()
                core_lower = core.lower()
                if core_lower.startswith('forti'):
                    # Preserve exact casing for all Forti* products
                    corrected_words.append(word)
                    continue
                
                if core_lower in self.FORTINET_SHORTHANDS:
                    corrected = f"{prefix}{self.FORTINET_SHORTHANDS[core_lower]}{suffix}"
                    corrected_words.append(corrected)
                    continue
            
            if word.isupper() and len(word) > 1:
                corrected_words.append(word)
            elif word.lower() == 'faqs':
                corrected_words.append('FAQs')
            elif word.lower() == 'vs':
                corrected = 'Vs' if (is_first or is_last) else 'vs'
                corrected_words.append(corrected)
            else:
                word_lower = re.sub(r'[.!?;:]', '', word.lower())
                if word_lower in lowercase_words and not is_first and not is_last:
                    corrected = word_lower
                else:
                    corrected = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
                corrected_words.append(corrected)
        
        corrected_text = ' '.join(corrected_words)
        corrected_text = self._fix_acronym_plurals_rule_based(corrected_text)
        return (text == corrected_text), corrected_text
    
    def _validate_sentence_case(self, text: str) -> tuple[bool, str]:
        """Sentence case validation."""
        if not text:
            return True, ""
        
        words = text.split()
        corrected_words = []
        sentence_start = True
        
        for word in words:
            clean_word = re.sub(r'[^\w\-]', '', word)
            
            # Check Fortinet terms
            if clean_word.lower().startswith('forti'):
                # Preserve exact casing for all Forti* products
                corrected_words.append(word)
                sentence_start = word.rstrip().endswith(('.', '!', '?'))
                continue
            
            # Check Fortinet terms dictionary
            if clean_word.lower() in self.FORTINET_SHORTHANDS:
                corrected = self.FORTINET_SHORTHANDS[clean_word.lower()]
                if word != clean_word:
                    prefix = word[:word.index(clean_word[0])] if clean_word[0] in word else ''
                    suffix = word[word.index(clean_word[-1])+1:] if clean_word[-1] in word and word.index(clean_word[-1]) < len(word)-1 else ''
                    corrected = prefix + corrected + suffix
                corrected_words.append(corrected)
                sentence_start = word.rstrip().endswith(('.', '!', '?'))
                continue

            
            # Keep uppercase abbreviations
            if clean_word.isupper() and len(clean_word) > 1:
                corrected_words.append(word)
                sentence_start = False
                continue
            
            # Sentence start - capitalize first letter
            if sentence_start:
                if len(word) > 0 and word[0].islower():
                    corrected = word[0].upper() + word[1:]
                    corrected_words.append(corrected)
                else:
                    corrected_words.append(word)
                sentence_start = word.rstrip().endswith(('.', '!', '?'))
                continue
            
            # Lowercase any uppercase words (except abbreviations)
            has_caps = any(c.isupper() for c in clean_word)
            if has_caps:
                prefix = ''
                suffix = ''
                core = clean_word
                
                if word != clean_word:
                    start_idx = word.find(clean_word[0]) if clean_word else 0
                    end_idx = word.rfind(clean_word[-1]) if clean_word else len(word)
                    prefix = word[:start_idx]
                    suffix = word[end_idx+1:]
                    core = word[start_idx:end_idx+1]
                
                corrected_core = core.lower()
                corrected = prefix + corrected_core + suffix
                corrected_words.append(corrected)
            else:
                corrected_words.append(word)
            
            sentence_start = word.rstrip().endswith(('.', '!', '?'))
        
        corrected_text = ' '.join(corrected_words)
        corrected_text = self._fix_acronym_plurals_rule_based(corrected_text)
        return (text == corrected_text), corrected_text
    
    # === VALIDATION METHODS WITH HYBRID SUPPORT ===
    
    def _validate_meta_title(self, text: str):
        """Validate meta title - USES OPENAI IF ENABLED."""
        text = self._normalize_fortinet_shorthands(text)
        rule_valid, rule_corrected = self._validate_title_case(text)
        
        # Call OpenAI if available
        if self.hybrid_validator:
            print(f"🤖 Calling OpenAI API for Meta Title...")
            try:
                hybrid_result = self.hybrid_validator.validate_title_case_hybrid(
                    text, (rule_valid, rule_corrected)
                )
                
                final_valid = hybrid_result['ai_valid']
                final_corrected = hybrid_result['final_recommendation']
                if text.strip() == final_corrected.strip().strip('"').strip("'"):
                    final_valid = True
                
                self.results.append(ValidationResult(
                    "Meta Title", "Title Case", text,
                    Status.ACCEPTED if final_valid else Status.REJECTED,
                    f'"{final_corrected}"', "Metadata",
                    ai_validated=True,
                    ai_result=hybrid_result['ai_corrected'],
                    unknown_terms=hybrid_result['unknown_terms']
                ))
                return
            except Exception as e:
                print(f"✗ OpenAI API call failed: {e}")
        
        if text.strip() == rule_corrected.strip():
            rule_valid = True
            # Fallback to rule-based
        self.results.append(ValidationResult(
            "Meta Title", "Title Case", text,
            Status.ACCEPTED if rule_valid else Status.REJECTED,
            f'"{rule_corrected}"', "Metadata"
        ))
    
    def _validate_meta_description(self, text: str):
        """Validate meta description - USES OPENAI IF ENABLED."""
        text = self._normalize_fortinet_shorthands(text)
        rule_valid, rule_corrected = self._validate_sentence_case(text)
        
        if self.hybrid_validator:
            print(f"🤖 Calling OpenAI API for Meta Description...")
            try:
                hybrid_result = self.hybrid_validator.validate_sentence_case_hybrid(
                    text, (rule_valid, rule_corrected)
                )
                
                final_valid = hybrid_result['ai_valid']
                final_corrected = hybrid_result['final_recommendation']
                
                self.results.append(ValidationResult(
                    "Meta Description", "Sentence case", text,
                    Status.ACCEPTED if final_valid else Status.REJECTED,
                    f'"{final_corrected}"', "Metadata",
                    ai_validated=True,
                    ai_result=hybrid_result['ai_corrected'],
                    unknown_terms=hybrid_result['unknown_terms']
                ))
                return
            except Exception as e:
                print(f"✗ OpenAI API call failed: {e}")
        
        self.results.append(ValidationResult(
            "Meta Description", "Sentence case", text,
            Status.ACCEPTED if rule_valid else Status.REJECTED,
            f'"{rule_corrected}"', "Metadata"
        ))
    
    def _validate_h1(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_capital_case(text)
        self.results.append(ValidationResult("H1", "Capital Case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "Metadata"))
    
    def _validate_header_caption(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_sentence_case(text)
        self.results.append(ValidationResult("Header Caption", "Sentence case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "Metadata"))
    
    def _validate_h2(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_capital_case(text)
        self.results.append(ValidationResult("H2", "Capital Case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "Headers"))
    
    def _validate_h3(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_sentence_case(text)
        self.results.append(ValidationResult("H3", "Sentence case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "Headers"))
    
    def _validate_h4(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_sentence_case(text)
        self.results.append(ValidationResult("H4", "Sentence case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "Headers"))
    
    def _validate_faq_header(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_capital_case(text)
        self.results.append(ValidationResult("FAQ H2 Header", "Capital Case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "FAQs"))
    
    def _validate_faq_question(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_sentence_case(text)
        self.results.append(ValidationResult("FAQ Question", "Sentence case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "FAQs"))
    
    def _validate_faq_answer(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_sentence_case(text)
        self.results.append(ValidationResult("FAQ Answer", "Sentence case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "FAQs"))
    
    def _validate_product_nav_tab(self, text: str):
        """Validate product nav - USES OPENAI IF ENABLED."""
        text = self._normalize_fortinet_shorthands(text)
        rule_valid, rule_corrected = self._validate_title_case(text)
        
        if self.hybrid_validator:
            print(f"🤖 Calling OpenAI API for Product Nav Tab...")
            try:
                hybrid_result = self.hybrid_validator.validate_title_case_hybrid(
                    text, (rule_valid, rule_corrected)
                )
                
                final_valid = hybrid_result['ai_valid']
                final_corrected = hybrid_result['final_recommendation']
                
                self.results.append(ValidationResult(
                    "Product Nav Tab", "Title Case", text,
                    Status.ACCEPTED if final_valid else Status.REJECTED,
                    f'"{final_corrected}"', "Product Navigation",
                    ai_validated=True,
                    ai_result=hybrid_result['ai_corrected'],
                    unknown_terms=hybrid_result['unknown_terms']
                ))
                return
            except Exception as e:
                print(f"✗ OpenAI API call failed: {e}")
        
        self.results.append(ValidationResult("Product Nav Tab", "Title Case", text,
                                             Status.ACCEPTED if rule_valid else Status.REJECTED,
                                             f'"{rule_corrected}"', "Product Navigation"))
    
    def _validate_cta_text(self, text: str):
        text = self._normalize_fortinet_shorthands(text)
        is_valid, corrected = self._validate_sentence_case(text)
        self.results.append(ValidationResult("CTA Text", "Sentence case", text,
                                             Status.ACCEPTED if is_valid else Status.REJECTED,
                                             f'"{corrected}"', "CTA"))

    def generate_failed_items_table(self, validation_results):
        """Generate failed items table - ONLY includes actual failures."""
        failed_items = []
        
        for result in validation_results:
            if result.status != Status.ACCEPTED:
                # Check if current and recommended are actually different
                current_text = result.location.strip()
                recommended_text = result.details.strip().strip('"').strip("'")
                # ✅ SKIP if empty location or details
                if not current_text or not recommended_text:
                    continue
                # ✅ SKIP if texts are identical (false failure)
                if current_text == recommended_text:
                    continue
                
                fix_detail = self._extract_fix_detail(result)
                
                # ✅ SKIP if no changes detected
                if fix_detail in ["No change needed", "No changes detected"]:
                    continue
                
                row = {
                    'Category': self._get_category(result.use_case),
                    'Type': result.use_case,
                    'Current': result.location if result.location else '',
                    'Fix': fix_detail,
                    'Recommended': result.details.strip('"').strip("'") if result.details else ''
                }
                
                if result.ai_validated:
                    row['AI'] = '✓'
                if result.unknown_terms:
                    row['Unknown'] = ', '.join(result.unknown_terms)
                
                failed_items.append(row)
        
        return pd.DataFrame(failed_items)

    def _get_category(self, use_case: str) -> str:
        """Map use case to category."""
        if 'Meta' in use_case:
            return 'Metadata'
        elif any(h in use_case for h in ['H1', 'H2', 'H3', 'H4', 'Header']):
            return 'Headers'
        elif 'FAQ' in use_case:
            return 'FAQ'
        elif 'CTA' in use_case:
            return 'CTA'
        elif 'Product' in use_case or 'Nav' in use_case or 'Tab' in use_case:
            return 'Navigation'
        else:
            return 'Content'

    
    def _extract_fix_detail(self, result) -> str:
        """Extract word-level changes."""
        current_text = result.location.strip()
        recommended_text = result.details.strip().strip('"').strip("'")
        
        # If texts are identical, no fix needed
        if current_text == recommended_text:
            return "No change needed"  # ✅ FIX: Don't show "See Recommended"
        
        current_words = current_text.split()
        recommended_words = recommended_text.split()
        
        changes = []
        max_length = max(len(current_words), len(recommended_words))
        
        for i in range(max_length):
            current_word = current_words[i] if i < len(current_words) else ""
            recommended_word = recommended_words[i] if i < len(recommended_words) else ""
            
            if current_word != recommended_word:
                if current_word and recommended_word:
                    changes.append(f"{current_word} → {recommended_word}")
                elif current_word:
                    changes.append(f"Remove: {current_word}")
                elif recommended_word:
                    changes.append(f"Add: {recommended_word}")
        
        if changes:
            if len(changes) > 3:
                return ", ".join(changes[:3]) + "..."
            return ", ".join(changes)
        
        return "No changes detected"  #