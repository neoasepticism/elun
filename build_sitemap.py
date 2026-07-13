#!/usr/bin/env python3
"""
Elun sitemap.xml generator.
Run after adding/removing pages:  python3 build_sitemap.py
- 코어 페이지 + pillars/*.html 자동 수집
- lastmod = 각 파일의 git 마지막 커밋 날짜 (미커밋이면 파일 mtime)
- 샘플/개인 리포트 파일(CLAUDE-*, sample-*)은 제외 (robots.txt 에서도 차단)
"""
import os, subprocess, datetime

BASE = 'https://elun.me'
ROOT = os.path.dirname(os.path.abspath(__file__))

CORE = [  # (path, priority, changefreq)
    ('index.html',        '1.0', 'weekly'),
    ('start.html',        '0.9', 'monthly'),
    ('daymasters.html',   '0.9', 'monthly'),
    ('cards.html',        '0.8', 'monthly'),
    ('pillars/index.html','0.8', 'monthly'),
    ('birth-time.html',   '0.7', 'yearly'),
    ('bazi-vs-astrology.html', '0.8', 'monthly'),
]

def lastmod(path):
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path],
                             cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    return datetime.date.fromtimestamp(os.path.getmtime(os.path.join(ROOT, path))).isoformat()

def url(path, prio, freq):
    loc = BASE + '/' + ('' if path == 'index.html' else path)
    # pillars/index.html → /pillars/
    if loc.endswith('/index.html'):
        loc = loc[:-len('index.html')]
    return (f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod(path)}</lastmod>\n'
            f'    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>')

def scan(subdir, prio, freq, index_prio=None):
    """subdir/*.html 자동 수집. index.html은 subdir/ 로 (index_prio 지정 시)."""
    out = []
    files = sorted(f for f in os.listdir(os.path.join(ROOT, subdir)) if f.endswith('.html'))
    for f in files:
        if f == 'index.html':
            if index_prio:
                out.append(url(f'{subdir}/index.html', index_prio, freq))
            continue
        out.append(url(f'{subdir}/{f}', prio, freq))
    return out

entries = [url(p, pr, f) for p, pr, f in CORE]
entries += scan('pillars', '0.6', 'yearly', index_prio=None)   # index는 CORE에 이미 있음
entries += scan('famous',  '0.5', 'monthly', index_prio='0.7')
entries += scan('audits',  '0.6', 'monthly', index_prio='0.7')

xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
       + '\n'.join(entries) + '\n</urlset>\n')
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(xml)
print(f'sitemap.xml: {len(entries)} URLs')
