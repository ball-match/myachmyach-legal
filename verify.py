#!/usr/bin/env python3
"""Offline HTML, local-link, source-text and placeholder checks (stdlib only)."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import re
from datetime import date
import build

ROOT = Path(__file__).resolve().parent
VOID = {'meta', 'link', 'br', 'hr', 'img', 'input', 'base', 'area', 'embed', 'source', 'wbr', 'col', 'param', 'track'}


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.tags, self.stack, self.text = [], set(), Counter(), [], []
        self.base = None
        self.feed(text)
        self.close()
        assert not self.stack, self.stack

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'th', 'td'):
            self.text.append('\n')
        attrs = dict(attrs)
        self.tags[tag] += 1
        if tag == 'base':
            self.base = attrs['href']
        if 'id' in attrs:
            assert attrs['id'] not in self.ids
            self.ids.add(attrs['id'])
        if tag in ('a', 'link'):
            self.links.append(attrs['href'])
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, tag

    def handle_data(self, data):
        self.text.append(data)


def normalize(text):
    return ' '.join(text.split())


def expected_text(markdown):
    result = []
    for line in markdown.splitlines():
        if re.fullmatch(r'\|[\s:|\-]+\|', line):
            continue
        line = re.sub(r'^#{1,6} |^\d+\. |^[-*] ', '', line)
        if line.startswith('|'):
            line = ' '.join(cell.strip() for cell in line.strip('|').split('|'))
        result.append(line.replace('**', '').replace('`', ''))
    return normalize(' '.join(result))


def verify():
    files = ['index.html', '404.html'] + [page for page, _ in build.FILES.values()]
    parsed = {}
    revisions = set()
    prefix = '/myachmyach-legal/'
    for name in files:
        text = (ROOT / name).read_text(encoding='utf-8')
        page = Page(text)
        assert page.tags['h1'] == 1, name
        assert page.tags['script'] == 0, name
        revision = re.search(r'<time datetime="([^"]+)">', text)[1]
        date.fromisoformat(revision)
        revisions.add(revision)
        assert '[EMAIL ДЛЯ ОБРАЩЕНИЙ]' in text
        parsed[name] = page
    assert len(revisions) == 1, revisions
    checked = 0
    for name, page in parsed.items():
        current = 'https://local.test' + prefix + name
        base = urljoin(current, page.base) if page.base else current
        for href in page.links:
            url = urlsplit(urljoin(base, href))
            if url.scheme == 'mailto':
                continue
            assert url.netloc == 'local.test', (name, href)
            assert url.path.startswith(prefix), (name, href)
            target = unquote(url.path.removeprefix(prefix))
            if target.endswith('/') or not target:
                target += 'index.html'
            assert (ROOT / target).is_file(), (name, href, target)
            if url.fragment:
                assert url.fragment in parsed[target].ids, (name, href)
            checked += 1
    for source, (name, lang) in build.FILES.items():
        md = (ROOT / 'content' / source).read_text(encoding='utf-8')
        text = (ROOT / name).read_text(encoding='utf-8')
        main = text.split('<main id="main">', 1)[1].split('</main>', 1)[0]
        main = main.split('</p>', 1)[1]  # Exclude revision-date metadata only.
        actual = Page('<div>' + main + '</div>')
        assert normalize(''.join(actual.text)) == expected_text(md), name
        assert Counter(re.findall(r'\[[^\]\n]+\]', ''.join(actual.text))) == Counter(re.findall(r'\[[^\]\n]+\]', md)), name
        assert parsed[name].tags['h2'] == len(re.findall(r'^## ', md, re.M))
        assert parsed[name].tags['table'] == (3 if source.startswith('privacy') else 0)
        assert 'ПРОЕКТ:' not in text and 'ПЕРЕД ПУБЛИКАЦИЕЙ:' not in text
        assert ('before publication within 24 hours' if lang == 'en' else 'до публикации в течение 24 часов') in text
        assert ('within 24 hours of receipt' if lang == 'en' else 'в течение 24 часов после получения') in text
    print(f'OK: 5 main pages + 404; {checked} local links/assets; exact document text, headings, tables and placeholders; moderation SLA.')


if __name__ == '__main__':
    verify()
