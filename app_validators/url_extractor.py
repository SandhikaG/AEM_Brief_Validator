"""
URL Extractor Module
No content extraction
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re


class URLExtractor:
    """Extracts and structures content from live URLs."""
    
    def __init__(self, url: str):
        self.url = url
        self.soup = None
        
    def extract_brief_data(self) -> Dict[str, Any]:
        """Extract all brief data from live URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            response = requests.get(self.url, timeout=30, headers=headers, verify=True)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.content, 'lxml')
            
            print(f"DEBUG: HTTP Status: {response.status_code}")
            print(f"DEBUG: Content Length: {len(response.content)}")
            
        except Exception as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
        
        brief_data = {
            'url': self.url,
            'meta_title': '',
            'meta_description': '',
            'h1': '',
            'header_caption': '',
            'headers': [],
            'faqs': {
                'header': '',
                'questions': []
            },
            'product_nav': {
                'tabs': []
            },
            'cta': {
                'caption': '',
                'text': '',
                'position': 'before_faq'
            }
        }
        
        brief_data['meta_title'] = self._extract_meta_title()
        brief_data['meta_description'] = self._extract_meta_description()
        
        h1, caption = self._extract_h1_and_caption()
        brief_data['h1'] = h1
        brief_data['header_caption'] = caption
        
        brief_data['headers'] = self._extract_headers()
        brief_data['faqs'] = self._extract_faqs()
        brief_data['product_nav']['tabs'] = self._extract_product_nav()
        
        cta = self._extract_cta()
        if cta and (cta.get('caption') or cta.get('text')):
            brief_data['cta'] = cta
        
        return brief_data
    
    def _extract_meta_title(self) -> str:
        """Extract meta title from page."""
        title_tag = self.soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        meta_title = self.soup.find('meta', {'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
        
        meta_title = self.soup.find('meta', {'name': 'title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
        
        return ''
    
    def _extract_meta_description(self) -> str:
        """Extract meta description from page."""
        meta_desc = self.soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        og_desc = self.soup.find('meta', {'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return ''
    
    def _extract_h1_and_caption(self) -> tuple[str, str]:
        """Extract H1 and header caption."""
        h1 = ''
        caption = ''
        
        h1_tags = self.soup.find_all('h1')
        if h1_tags:
            for tag in h1_tags:
                text = tag.get_text(strip=True)
                if text and len(text) > 5:
                    h1 = text
                    break
            
            if h1 and h1_tags[0]:
                h1_tag = h1_tags[0]
                
                next_elem = h1_tag.find_next_sibling('p')
                if next_elem:
                    text = next_elem.get_text(strip=True)
                    if 20 < len(text) < 500:
                        caption = text
                
                if not caption:
                    next_div = h1_tag.find_next_sibling('div')
                    if next_div:
                        p_tag = next_div.find('p')
                        if p_tag:
                            text = p_tag.get_text(strip=True)
                            if 20 < len(text) < 500:
                                caption = text
                
                if not caption:
                    parent = h1_tag.parent
                    if parent:
                        next_p = parent.find_next('p')
                        if next_p:
                            text = next_p.get_text(strip=True)
                            if 20 < len(text) < 500:
                                caption = text
        
        return h1, caption
    
    def _extract_headers(self) -> List[Dict[str, str]]:
        """Extract all headers (H2, H3, H4)."""
        headers = []
        
        for tag in self.soup.find_all(['h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if text and len(text) > 0:
                level = tag.name.upper()
                headers.append({'level': level, 'text': text})
        
        return headers
    
    def _extract_faqs(self) -> Dict[str, Any]:
        """Extract FAQ section."""
        faqs = {
            'header': '',
            'questions': []
        }
        
        for h2 in self.soup.find_all('h2'):
            text = h2.get_text(strip=True)
            if 'FAQ' in text.upper() or 'FREQUENTLY ASKED' in text.upper():
                faqs['header'] = text
                
                current = h2
                questions_found = 0
                
                while True:
                    current = current.find_next(['h2', 'h3'])
                    if not current:
                        break
                    if current.name == 'h2':
                        break
                    if current.name == 'h3':
                        question = current.get_text(strip=True)
                        if question and len(question) > 5:
                            faqs['questions'].append({
                                'question': question,
                                'answer': 'Answer extracted from webpage'
                            })
                            questions_found += 1
                
                print(f"DEBUG: FAQ extraction - Found {questions_found} questions")
                break
        
        return faqs
    
    def _extract_product_nav(self) -> List[Dict[str, str]]:
        """Extract Product Navigation tabs from webpage."""
        tabs = []
        
        nav_selectors = [
            ('nav', {'class': re.compile(r'.*nav.*', re.I)}),
            ('div', {'class': re.compile(r'.*nav.*', re.I)}),
            ('ul', {'class': re.compile(r'.*nav.*', re.I)}),
            ('div', {'role': 'navigation'}),
            ('nav', {}),
        ]
        
        for tag_name, attrs in nav_selectors:
            nav = self.soup.find(tag_name, attrs)
            if nav:
                links = nav.find_all('a')
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    if text and len(text) > 0:
                        tabs.append({
                            'text': text,
                            'linked_section': href
                        })
                
                if tabs:
                    print(f"DEBUG: Found {len(tabs)} nav tabs")
                    break
        
        return tabs
    
    def _extract_cta(self) -> Dict[str, str]:
        """Extract CTA section - paragraphs before FAQ."""
        cta = {
            'caption': '',
            'text': '',
            'position': 'before_faq'
        }
        
        faq_h2 = None
        for h2 in self.soup.find_all('h2'):
            text = h2.get_text(strip=True)
            if 'FAQ' in text.upper() or 'FREQUENTLY ASKED' in text.upper():
                faq_h2 = h2
                break
        
        if faq_h2:
            all_elements = self.soup.find_all(['p', 'h2'])
            faq_position = None
            
            for idx, elem in enumerate(all_elements):
                if elem == faq_h2:
                    faq_position = idx
                    break
            
            if faq_position is not None:
                paragraphs_before_faq = []
                
                for elem in all_elements[:faq_position]:
                    if elem.name == 'p':
                        text = elem.get_text(" ", strip=True)
                        if 20 < len(text) < 500:
                            if '?' not in text or text.count('?') <= 1:
                                paragraphs_before_faq.append(text)
                
                if len(paragraphs_before_faq) > 0:
                    cta_candidates = paragraphs_before_faq[-2:] if len(paragraphs_before_faq) >= 2 else paragraphs_before_faq[-1:]
                    
                    if len(cta_candidates) >= 2:
                        cta['caption'] = cta_candidates[0]
                        cta['text'] = cta_candidates[1]
                    elif len(cta_candidates) == 1:
                        cta['text'] = cta_candidates[0]
                        cta['caption'] = ''
        
        return cta