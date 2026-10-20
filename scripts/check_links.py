"""Check that relative links and images in Markdown/HTML files resolve. External URLs are listed, not fetched.

Usage: python scripts/check_links.py FILE [FILE ...]
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]

class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []   # (kind, url, has_alt)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.refs.append(('link', a['href'], True))
        elif tag == 'img' and a.get('src'):
            self.refs.append(('image', a['src'], bool(a.get('alt', '').strip())))
        elif tag == 'link' and a.get('href'):
            self.refs.append(('link', a['href'], True))
        elif tag == 'script' and a.get('src'):
            self.refs.append(('script', a['src'], True))

def references(path):
    text = path.read_text(encoding='utf-8')
    if path.suffix == '.html':
        c = Collector()
        c.feed(text)
        return c.refs
    refs = [('image', u, bool(alt.strip())) for alt, u in re.findall(r'!\[([^\]]*)\]\(([^)\s]+)', text)]
    refs += [('link', u, True) for u in re.findall(r'(?<!!)\[[^\]]*\]\(([^)\s]+)', text)]
    refs += [('image', u, True) for u in re.findall(r'<img[^>]+src="([^"]+)"', text)]
    return refs

def check(path):
    broken, external, noalt = [], [], []
    for kind, url, has_alt in references(path):
        if kind == 'image' and not has_alt:
            noalt.append(url)
        parsed = urlparse(url)
        if parsed.scheme in ('http', 'https'):
            external.append(url)
        elif parsed.scheme in ('mailto', 'tel') or url.startswith('#'):
            continue
        else:
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.exists():
                broken.append(url)
    return broken, external, noalt

def main(files):
    failed = False
    for name in files:
        path = (ROOT / name) if not Path(name).is_absolute() else Path(name)
        broken, external, noalt = check(path)
        print(f'{name}: broken={len(broken)} images_without_alt={len(noalt)} external_listed={len(external)}')
        for b in broken + noalt:
            print('   ', b)
        failed |= bool(broken or noalt)
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    main(sys.argv[1:])
