#!/usr/bin/env python3
"""Build this site's deliberately limited Markdown subset using only stdlib."""
import argparse
import html
import posixpath
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {
    'privacy-policy.ru.md': ('privacy/index.html', 'ru'),
    'privacy-policy.en.md': ('en/privacy/index.html', 'en'),
    'terms.ru.md': ('terms/index.html', 'ru'),
    'terms.en.md': ('en/terms/index.html', 'en'),
}
EDITORIAL_PREFIXES = ('> [ПРОЕКТ:', '> Draft:', '> [ПЕРЕД ПУБЛИКАЦИЕЙ:', '> Before publication:')
EDITORIAL_SENTENCES = (
    '; наличие или отсутствие серверной обработки с помощью ИИ должно быть раскрыто в разделе 8.',
    '; whether server-side AI processing is used must be disclosed in section 8.',
)


def clean(text):
    text = '\n'.join(line for line in text.splitlines()
                     if not line.startswith(EDITORIAL_PREFIXES)) + '\n'
    for sentence in EDITORIAL_SENTENCES:
        text = text.replace(sentence, '.')
    return text


def inline(text):
    # Bracketed data fields stay literal, including long confirmation fields.
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    return escaped


def markdown(text):
    """Headings, flat lists, pipe tables and paragraphs used by these sources.

    Reject unhandled block syntax rather than silently generating misleading HTML.
    """
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        heading = re.fullmatch(r'(#{1,6}) (.+)', line)
        if heading:
            n = len(heading[1])
            out.append(f'<h{n}>{inline(heading[2])}</h{n}>')
            i += 1
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([cell.strip() for cell in lines[i].strip('|').split('|')])
                i += 1
            if len(rows) < 2 or not all(re.fullmatch(r':?-{3,}:?', c) for c in rows[1]):
                raise ValueError('Invalid table separator')
            if any(len(row) != len(rows[0]) for row in rows):
                raise ValueError('Inconsistent table columns')
            label = 'Таблица данных' if 'Категория' in rows[0] or 'Получатель' in rows[0] else 'Data table'
            out.append(f'<div class="table-scroll" role="region" aria-label="{label}" tabindex="0"><table><thead><tr>')
            out.extend(f'<th scope="col">{inline(c)}</th>' for c in rows[0])
            out.append('</tr></thead><tbody>')
            for row in rows[2:]:
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
            out.append('</tbody></table></div>')
        elif re.match(r'(\d+\. |[-*] )', line):
            ordered = bool(re.match(r'\d+\. ', line))
            tag = 'ol' if ordered else 'ul'
            pattern = r'\d+\. (.+)' if ordered else r'[-*] (.+)'
            start = int(line.split('.')[0]) if ordered else 1
            attr = f' start="{start}"' if ordered and start != 1 else ''
            out.append(f'<{tag}{attr}>')
            while i < len(lines) and (item := re.fullmatch(pattern, lines[i])):
                out.append(f'<li>{inline(item[1])}</li>')
                i += 1
            out.append(f'</{tag}>')
        else:
            if line.startswith(('>', '```', '    ')):
                raise ValueError(f'Unsupported Markdown block: {line}')
            paragraph = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r'[#|>]|\d+\. |[-*] ', lines[i]):
                paragraph.append(lines[i])
                i += 1
            out.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n'.join(out)


def relative(page, target):
    return posixpath.relpath(target, posixpath.dirname(page) or '.')


def shell(page, lang, title, body, updated, switch, base=None):
    en = lang == 'en'
    home = relative(page, 'index.html')
    css = relative(page, 'style.css')
    nav = 'Documents' if en else 'Документы'
    last = 'Last updated' if en else 'Последнее обновление'
    skip = 'Skip to content' if en else 'К содержанию'
    base_tag = f'<base href="{html.escape(base, quote=True)}">' if base else ''
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
{base_tag}
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{css}">
</head>
<body>
<a class="skip" href="#main">{skip}</a>
<header class="site-header"><a class="brand" href="{home}">МячМяч <span>/ {nav}</span></a>
<nav aria-label="{'Language' if en else 'Язык'}">{switch}</nav></header>
<main id="main">
<p class="updated">{last}: <time datetime="{updated}">{updated}</time></p>
{body}
</main>
<footer><a href="{relative(page, 'en/privacy/index.html' if en else 'privacy/index.html')}">{'Privacy Policy' if en else 'Политика конфиденциальности'}</a>
<a href="{relative(page, 'en/terms/index.html' if en else 'terms/index.html')}">{'Terms of Use' if en else 'Пользовательское соглашение'}</a>
<p>{'Support' if en else 'Поддержка'}: <a href="mailto:hello@ballball.ru">hello@ballball.ru</a><br>
{'Legal enquiries' if en else 'Юридические обращения'}: [EMAIL ДЛЯ ОБРАЩЕНИЙ]</p></footer>
</body>
</html>
'''


def build(source, updated, base_path):
    content = ROOT / 'content'
    content.mkdir(exist_ok=True)
    for name, (page, lang) in FILES.items():
        text = clean((source / name).read_text(encoding='utf-8'))
        (content / name).write_text(text, encoding='utf-8')
        other = page.removeprefix('en/') if lang == 'en' else 'en/' + page
        label = 'Русский' if lang == 'en' else 'English'
        switch = f'<span aria-current="page">{"EN" if lang == "en" else "RU"}</span> / <a href="{relative(page, other)}" lang="{"ru" if lang == "en" else "en"}" hreflang="{"ru" if lang == "en" else "en"}">{label}</a>'
        title = text.splitlines()[0].removeprefix('# ')
        target = ROOT / page
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(shell(page, lang, title, markdown(text), updated, switch), encoding='utf-8')
    body = '''<h1>МячМяч — правовые документы</h1>
<p class="intro">Политика конфиденциальности и условия использования приложения. Выберите документ и язык.</p>
<section id="ru" aria-labelledby="ru-title"><h2 id="ru-title">На русском</h2>
<ul class="documents"><li><a href="privacy/index.html">Политика конфиденциальности <span>RU →</span></a></li>
<li><a href="terms/index.html">Пользовательское соглашение <span>RU →</span></a></li></ul></section>
<section id="en" lang="en" aria-labelledby="en-title"><h2 id="en-title">In English</h2>
<ul class="documents"><li><a href="en/privacy/index.html" hreflang="en">Privacy Policy <span>EN →</span></a></li>
<li><a href="en/terms/index.html" hreflang="en">Terms of Use <span>EN →</span></a></li></ul></section>'''
    switch = '<a href="#ru" lang="ru">Русский</a> / <a href="#en" lang="en">English</a>'
    (ROOT / 'index.html').write_text(shell('index.html', 'ru', 'МячМяч — правовые документы', body, updated, switch), encoding='utf-8')
    body404 = '''<h1>404 — Страница не найдена</h1><p>Возможно, адрес изменился или содержит опечатку.</p>
<p lang="en">Page not found. Please choose a document on the home page.</p>
<p><a href="index.html">Все документы / All documents →</a></p>'''
    (ROOT / '404.html').write_text(shell('404.html', 'ru', '404 — МячМяч', body404, updated, '<a href="index.html#ru">Русский</a> / <a href="index.html#en" lang="en">English</a>', base_path), encoding='utf-8')
    (ROOT / '.nojekyll').touch()
    placeholders = sorted(set(re.findall(r'\[[^\]\n]+\]', '\n'.join((content / name).read_text(encoding='utf-8') for name in FILES))))
    (ROOT / 'PLACEHOLDERS.md').write_text('# Оставшиеся поля для заполнения\n\nВсего уникальных полей: ' + str(len(placeholders)) + '. Текст сохранён дословно.\n\n' + '\n'.join('- ' + p for p in placeholders) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=ROOT / 'content')
    parser.add_argument('--updated', default='2026-10-29', help='Actual revision date, not the legal effective date')
    parser.add_argument('--base-path', default='/myachmyach-legal/', help='GitHub Pages path used only by 404.html')
    args = parser.parse_args()
    from datetime import date
    date.fromisoformat(args.updated)
    if not re.fullmatch(r'/[A-Za-z0-9_./-]*', args.base_path) or not args.base_path.endswith('/') or '..' in args.base_path:
        parser.error('--base-path must be an absolute site path ending with /')
    build(args.source_dir.resolve(), args.updated, args.base_path)
