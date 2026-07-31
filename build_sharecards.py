#!/usr/bin/env python3
"""
build_sharecards.py — X/페북 공유용 3카드(일지·일간·격국) OG 이미지 + 공유 스텁 페이지 생성.

조합: 일주 60 × 격국(십성) 10 = 600.
  - 이미지: pillars/s/og/{pillar-slug}-{god-slug}.jpg  (1200×630, headless Chrome → JPEG)
  - 스텁:   pillars/s/{pillar-slug}-{god-slug}.html    (og 메타 + noindex + CTA, 사람이 열면 카드+CTA)

데이터 단일 정본 = ko/result.html 의 `const DECK={...}` / `const P60 = {...}` 를 파싱 (중복 정의 금지).
사용법:
  python3 build_sharecards.py            # 스텁 600개만 (빠름)
  python3 build_sharecards.py --og       # 이미지 600장도 생성 (~10-20분)
  python3 build_sharecards.py --og 乙卯  # 특정 일주만 (10장)
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'ko', 'result.html')
OUT_DIR = os.path.join(ROOT, 'pillars', 's')
OG_DIR = os.path.join(OUT_DIR, 'og')
ART = os.path.join(ROOT, 'pillars', 'art')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# 십간 한자 → 병음 슬러그 (build_pillars.py STEM_SLUG 와 동일)
STEM_PY = {'甲': 'Jia', '乙': 'Yi', '丙': 'Bing', '丁': 'Ding', '戊': 'Wu',
           '己': 'Ji', '庚': 'Geng', '辛': 'Xin', '壬': 'Ren', '癸': 'Gui'}


def _extract(name):
    """ko/result.html 에서 `const NAME = {...};` JSON 을 파싱."""
    src = open(SRC, encoding='utf-8').read()
    m = re.search(r'const %s\s*=\s*(\{.*?\});\n' % name, src, re.S)
    if not m:
        raise SystemExit(f'cannot find const {name} in {SRC}')
    return json.loads(m.group(1))


DECK = _extract('DECK')
P60 = _extract('P60')

GODS = DECK['gods']          # arch key → card
GOD_SLUG = {k: v['art'][2:-4] for k, v in GODS.items()}   # "The Governor" → "governor"

# 결과 페이지 "나의 핸드" deckCard 디자인 이식 — 풀아트 + 한자/역할배지 + 하단 이름
CARD_TPL = '''
<div style="width:280px;height:420px;border-radius:20px;position:relative;flex:none;overflow:hidden;
  border:2px solid {edge};background:#0e0b08;box-shadow:0 20px 50px -18px #000, 0 0 40px -20px {ac}">
  <div style="position:absolute;inset:0;background-image:url('{art}');background-size:cover;background-position:22% center"></div>
  <div style="position:absolute;inset:0;background:linear-gradient(180deg,#0e0b0899 0%,transparent 17%,transparent 68%,#0e0b08cc 86%,#0e0b08ee 100%)"></div>
  <div style="position:absolute;inset:8px;border:1px solid #ffffff1c;border-radius:14px"></div>
  <div style="position:absolute;top:16px;left:18px;right:18px;display:flex;justify-content:space-between;align-items:flex-start">
    <span style="font-family:serif;font-size:38px;font-weight:700;line-height:1;color:{ac};text-shadow:0 2px 14px #000">{han}</span>
    <span style="font-family:serif;font-size:13px;color:#e8e0d0;border:1px solid #ffffff33;border-radius:13px;padding:3px 11px;white-space:nowrap;background:#0e0b0880">{role}</span>
  </div>
  <div style="position:absolute;bottom:18px;left:0;right:0;text-align:center">
    <div style="font-family:serif;font-size:26px;font-weight:700;color:{ac};text-shadow:0 2px 14px #000">{name}</div>
    <div style="font-size:12px;letter-spacing:2.5px;color:#c9bda9;margin-top:4px">{typ}</div>
  </div>
</div>'''

# 결과 페이지 RAREP 배지 (일주 결정 — result.html 정본과 동일하게 유지)
RAREP = {'庚辰': '희귀 · 괴강(魁罡)', '庚戌': '희귀 · 괴강(魁罡)', '壬辰': '희귀 · 괴강(魁罡)', '壬戌': '희귀 · 괴강(魁罡)',
         '甲寅': '희귀 · 간여지동(干與支同)', '乙卯': '희귀 · 간여지동(干與支同)', '丙午': '희귀 · 간여지동(干與支同)',
         '丁巳': '희귀 · 간여지동(干與支同)', '戊戌': '희귀 · 간여지동(干與支同)', '戊辰': '희귀 · 간여지동(干與支同)',
         '己丑': '희귀 · 간여지동(干與支同)', '己未': '희귀 · 간여지동(干與支同)', '庚申': '희귀 · 간여지동(干與支同)',
         '辛酉': '희귀 · 간여지동(干與支同)', '壬子': '희귀 · 간여지동(干與支同)', '癸亥': '희귀 · 간여지동(干與支同)',
         '丁酉': '길성 · 천을귀인(天乙貴人)', '丁亥': '길성 · 천을귀인(天乙貴人)', '癸巳': '길성 · 천을귀인(天乙貴人)',
         '癸卯': '길성 · 천을귀인(天乙貴人)'}

PAGE_TPL = '''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{gj} · {god_name} — 나의 사주 카드 | Elun</title>
<meta name="robots" content="noindex">
<meta property="og:type" content="website">
<meta property="og:title" content="{gj}({reading}) · {god_name} — 나의 사주 카드">
<meta property="og:description" content="일지·일간·격국 세 장의 카드. 진태양시 기준 정밀 계산 — elun.me 에서 내 사주를 확인해 보세요.">
<meta property="og:image" content="https://elun.me/pillars/s/og/{fname}.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:url" content="https://elun.me/pillars/s/{fname}.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://elun.me/pillars/s/og/{fname}.jpg">
<style>body{{margin:0;background:#0e0b08;color:#f3ece0;font-family:'Apple SD Gothic Neo','Noto Sans KR',sans-serif;
text-align:center;padding:34px 16px}}img{{max-width:min(680px,100%);border-radius:14px;border:1px solid #2a2317}}
a.b{{display:inline-block;background:#c9a227;color:#14100b;font-weight:700;border-radius:26px;padding:13px 30px;
text-decoration:none;margin:8px 6px 0}}a.g{{display:inline-block;border:1px solid #3a3226;color:#b8ab97;border-radius:26px;
padding:12px 26px;text-decoration:none;margin:8px 6px 0}}p{{color:#9c8f79;font-size:14px;line-height:1.6}}</style></head><body>
<img src="og/{fname}.jpg" alt="{gj} 사주 카드 — 일지·일간·격국">
<p>일지 · 일간 · 격국, 세 장의 카드.<br>당신의 사주도 진태양시 기준으로 정밀하게 계산해 보세요.</p>
<div><a class="b" href="/ko/start.html">내 사주 계산하기 — 무료</a>
<a class="g" href="/start.html">Calculate mine (EN)</a></div>
<div style="margin-top:10px"><a class="g" href="/pillars/{pslug}.html">{gj} 일주 자세히 보기</a></div>
</body></html>'''

OG_TPL = '''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}
body{{width:1200px;height:630px;overflow:hidden;font-family:'Apple SD Gothic Neo','Noto Sans KR',sans-serif;
background:#0e0b08;background-image:radial-gradient(ellipse at 50% -15%,#241a0e 0,transparent 60%),
radial-gradient(circle at 85% 110%,#141c24 0,transparent 45%);color:#f3ece0}}
</style></head><body>
<div style="text-align:center;padding-top:18px">
  <div style="font-family:serif;letter-spacing:8px;color:#c9a227;font-size:14px">四 柱 · 나 의 사 주</div>
  <div style="font-family:serif;font-size:31px;font-weight:700;margin-top:5px">{gj} <span style="color:#9c8f79;font-size:20px">{reading}</span>
  <span style="color:#c9a227;font-size:22px;margin-left:8px">· {god_short}</span></div>
</div>
<div style="display:flex;justify-content:center;gap:24px;margin-top:14px">{cards}</div>
<div style="position:absolute;bottom:14px;left:0;right:0;text-align:center">
  {badge}
  <span style="font-family:serif;font-size:15px;color:#c9a227;letter-spacing:1.5px">나도 계산해 보기 — elun.me</span></div>
</body></html>'''

BADGE_TPL = ('<span style="display:inline-block;border:1.5px solid #c9a227;color:#e0c05a;border-radius:15px;'
             'padding:3px 16px;font-size:14px;letter-spacing:2px;background:#0e0b08cc;font-family:serif;'
             'margin-right:14px;vertical-align:1px">◆ {rare} — {gj}</span>')

HSK = {'甲': '갑', '乙': '을', '丙': '병', '丁': '정', '戊': '무', '己': '기', '庚': '경', '辛': '신', '壬': '임', '癸': '계'}
HBK = {'子': '자', '丑': '축', '寅': '인', '卯': '묘', '辰': '진', '巳': '사', '午': '오', '未': '미',
       '申': '신', '酉': '유', '戌': '술', '亥': '해'}


def card_html(d, role):
    return CARD_TPL.format(edge=d['edge'], c1=d['c1'], c2=d['c2'], ac=d['ac'],
                           art='file://' + os.path.join(ART, d['art']),
                           role=role, han=d['han'], name=d['name'], typ=d['typ'])


def main():
    do_og = '--og' in sys.argv
    only = next((a for a in sys.argv[1:] if not a.startswith('-')), None)
    os.makedirs(OG_DIR, exist_ok=True)
    from PIL import Image as PImg
    n_page = n_img = 0
    for gj in P60:
        if only and gj != only:
            continue
        stem, branch = gj[0], gj[1]
        pslug = P60[gj]['py'].lower().replace(' ', '-')
        reading = HSK[stem] + HBK[branch]
        sd, bd = DECK['stems'][stem], DECK['branches'][branch]
        for arch, gd in GODS.items():
            gslug = GOD_SLUG[arch]
            fname = f'{pslug}-{gslug}'
            god_short = gd['name']    # 예: 정관(正官)
            # 스텁 페이지
            open(os.path.join(OUT_DIR, fname + '.html'), 'w', encoding='utf-8').write(
                PAGE_TPL.format(gj=gj, reading=reading, god_name=god_short, fname=fname, pslug=pslug))
            n_page += 1
            if not do_og:
                continue
            cards = (card_html(bd, '일지(日支)')
                     + card_html(sd, '일간(日干)')
                     + card_html(gd, '격국(格局)'))
            badge = BADGE_TPL.format(rare=RAREP[gj], gj=gj) if gj in RAREP else ''
            html = OG_TPL.format(gj=gj, reading=reading, god_short=god_short, cards=cards, badge=badge)
            with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html)
                tmp = f.name
            out_png = os.path.join(OG_DIR, fname + '.png')
            subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars',
                            f'--screenshot={out_png}', '--window-size=1200,630', f'file://{tmp}'],
                           capture_output=True)
            os.unlink(tmp)
            PImg.open(out_png).convert('RGB').save(out_png[:-4] + '.jpg', quality=66, optimize=True)
            os.unlink(out_png)
            n_img += 1
    print(f'share stubs: {n_page} pages, og images: {n_img} -> {OUT_DIR}')


if __name__ == '__main__':
    main()
