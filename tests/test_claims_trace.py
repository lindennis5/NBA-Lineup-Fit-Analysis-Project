"""Every number quoted in the deliverables must trace to docs/claims.json (built from outputs)."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ['README.md', 'docs/fans.md', 'docs/medium_article_outline.md', 'docs/career_materials.md',
                'docs/FINAL_AUDIT.md', 'site/index.html']
BANNED = [r'\bcauses\b', r'\bcaused\b', r'\bproves?\b', r"fit doesn'?t matter", r'chemistry is a myth']
NUMBER = re.compile(r'(?<![\w.])\d[\d,]*(?:\.\d+)?%?(?![\w])')

def strip_noncontent(text):
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)           # code blocks
    text = re.sub(r'`[^`]*`', ' ', text)                          # inline code
    text = re.sub(r'<(script|style)\b.*?</\1>', ' ', text, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', text)                          # html tags and attributes
    text = re.sub(r'\]\([^)]*\)', ']', text)                      # markdown link targets
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'!\[[^\]]*\]', ' ', text)                      # image alt text
    text = re.sub(r'\b\d{4}\s?[–-]\s?\d{2,4}\b', ' ', text)      # season labels, year ranges
    text = re.sub(r'\bPython \d+(\.\d+)*', ' ', text)
    text = re.sub(r'\b(19|20)\d{2}(-\d{2}-\d{2})?\b', ' ', text)  # years, ISO dates
    return text.replace('−', '-')

def untraceable(text, tokens):
    bad = []
    for match in NUMBER.findall(strip_noncontent(text)):
        token = match.rstrip('%').lstrip('+-')
        if '.' not in token and not match.endswith('%') and len(token.replace(',', '')) < 3:
            continue                                              # small structural integers (4 seasons, 30 teams)
        if token not in tokens and token.replace(',', '') not in tokens:
            bad.append(match)
    return bad

class ClaimsTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'docs' / 'claims.json'
        cls.tokens = set(json.loads(path.read_text(encoding='utf-8'))['tokens']) if path.exists() else None

    def test_claims_registry_exists(self):
        self.assertIsNotNone(self.tokens, 'run python -m src.claims first')

    def test_numbers_trace_to_outputs(self):
        for name in DELIVERABLES:
            path = ROOT / name
            if not path.exists():
                continue
            with self.subTest(name):
                self.assertEqual(untraceable(path.read_text(encoding='utf-8'), self.tokens), [])

    def test_banned_wording_absent(self):
        for name in DELIVERABLES:
            path = ROOT / name
            if path.exists():
                text = strip_noncontent(path.read_text(encoding='utf-8')).lower()
                for pattern in BANNED:
                    with self.subTest(name, pattern=pattern):
                        self.assertIsNone(re.search(pattern, text))

    def test_detector_flags_fabricated_number(self):
        tokens = {'0.03', '1,537', '1537'}
        self.assertEqual(untraceable('Effect -0.03 across 1,537 lineups; 4 seasons.', tokens), [])
        self.assertEqual(untraceable('Effect of 7.25 points', tokens), ['7.25'])

if __name__ == '__main__':
    unittest.main()
