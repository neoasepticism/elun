#!/usr/bin/env python3
"""
Elun 유명인 사주 페이지 생성기 — famous/{slug}.html
- celebs.json(생일 DB) × pillar60.json(일주 데이터) × build_pillars 텍스트 블록 재사용
- LLM 없음(결정론 조합), 출생시간 미상 → 3주만 정직하게 표시
Run: python3 build_famous.py
"""
import json, os, re, sys, importlib.util
from collections import Counter

sys.path.insert(0, os.path.expanduser('~/elun-engine'))
import bazi_global as bg
import report_premium as rp
from report import GAN_OH, JI_OH

spec = importlib.util.spec_from_file_location('bp', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_pillars.py'))
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'famous')

# 천간 상징 한 단어 (acard 캡션용) — bp.DM[x]['img'] 축약
STEM_SYM = {'甲': 'Tree', '乙': 'Vine', '丙': 'Sun', '丁': 'Flame', '戊': 'Mountain',
            '己': 'Field', '庚': 'Blade', '辛': 'Jewel', '壬': 'Ocean', '癸': 'Rain'}

# Destiny Audit deep links: slug -> audit number (page must exist at audits/<slug>.html + -ko)
AUDITS = {
    'masayoshi-son': 'No.001',
    'steve-jobs': 'No.002',
}
CELEBS = json.load(open(os.path.join(ROOT, 'celebs.json'), encoding='utf-8'))
P60 = {p['gj']: p for p in json.load(open(os.path.expanduser('~/elun-engine/pillar60.json'), encoding='utf-8'))['pillars']}

GOD_EN = {'비견': 'The Ally', '겁재': 'The Rival', '식신': 'The Creator', '상관': 'The Maverick',
          '정재': 'The Steward', '편재': 'The Entrepreneur', '정관': 'The Governor',
          '편관': 'The Challenger', '정인': 'The Scholar', '편인': 'The Mystic', '일간': 'Day Master'}
STEM_HJ = {'갑': '甲', '을': '乙', '병': '丙', '정': '丁', '무': '戊', '기': '己',
           '경': '庚', '신': '辛', '임': '壬', '계': '癸'}


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def chart_for(name):
    y, m, d, tz = CELEBS[name]
    opts = {'lon_corr': False, 'dst': False, 'std_meridian': None, 'lon': 0, 'auto_tz': True, 'tz': tz}
    return bg.build_result(y, m, d, 12, 0, 'M', opts)


ELEM_META = {'목': ('Wood', '木', 'wood'), '화': ('Fire', '火', 'fire'), '토': ('Earth', '土', 'earth'),
             '금': ('Metal', '金', 'metal'), '수': ('Water', '水', 'water')}


def fe3(fp):
    """3주(년월일) 기준 오행 분포 — 시주(정오 가정) 제외."""
    c = Counter()
    for k in ('year', 'month', 'day'):
        c[GAN_OH[fp[k]['stem']]] += 1
        c[JI_OH[fp[k]['branch']]] += 1
    tot = sum(c.values()) or 1
    return {oh: round(c[oh] / tot * 100) for oh in ('목', '화', '토', '금', '수')}


def balance_box(chart, py):
    fp = chart['four_pillars']
    dm_elem_en = rp.ELEM_KO_EN[chart['day_master']['element']]
    roles = rp._elem_roles(dm_elem_en)
    oh = fe3(fp)
    st_label = rp._strength_three_pillar(chart)['label']   # 3주 기준 강약 (시간 미상)
    st_en = rp._strength_en(st_label)
    if 'Weak' in st_en:
        st_gloss = 'a chart that runs on support — its story turns on what feeds the Day Master'
    elif 'Strong' in st_en:
        st_gloss = 'a chart that carries its own weight — its story turns on where the surplus gets spent'
    else:
        st_gloss = 'a chart near balance — small shifts in luck tilt the whole board'
    ug = rp._useful_god(dm_elem_en, st_label)
    # 십성 카운트 (정오 가정 시주 몫 제거 → 3주 기준)
    hp = fp.get('hour', {})
    tg = dict(chart.get('ten_gods_count', {}))
    for g in (hp.get('stem_god'), hp.get('branch_god')):
        if g in tg:
            tg[g] -= 1
            if tg[g] <= 0:
                del tg[g]
    bars = ''
    for ko in ('목', '화', '토', '금', '수'):
        en, hj, var = ELEM_META[ko]
        pct = oh[ko]
        bars += (f'<div class="ebrow"><span class="ebl">{en} <b>{hj}</b><em>{roles[en]}</em></span>'
                 f'<span class="ebt"><i style="width:{max(pct, 2)}%;background:var(--{var})"></i></span>'
                 f'<span class="ebp">{pct}%</span></div>')
    chips = ''.join(
        f'<span class="tgc">{GOD_EN.get(g, g)}{f" ×{n}" if n > 1 else ""}</span>'
        for g, n in sorted(tg.items(), key=lambda x: -x[1]) if g != '일간')
    return f'''<div class="box">
      <h2>The Balance — what makes this chart its own</h2>
      <p style="font-size:13.5px">Every {py} day shares the same core — but the year and month around it never repeat.
      This is the mix this particular chart was dealt (three pillars, hour excluded):</p>
      <div class="ebars">{bars}</div>
      <table class="kv" style="margin-top:14px">
        <tr><td>Strength</td><td>{st_en} — {st_gloss}</td></tr>
        <tr><td>Useful Element 用神</td><td>{ug["primary_elem"]} ({ug["primary_role"]}) first · {ug["secondary_elem"]} ({ug["secondary_role"]}) second</td></tr>
      </table>
      <div style="margin-top:12px"><span style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--faint)">Archetypes in the chart</span><br>{chips}</div>
    </div>'''


def page(name):
    y, m, d, tz = CELEBS[name]
    r = chart_for(name)
    fp = r['four_pillars']
    gj = fp['day']['ganji_hanja']
    p = P60.get(gj)
    if not p:
        return None
    py = p['py']
    dm_stem_ko = r['day_master']['stem']
    dm = bp.DM[STEM_HJ[dm_stem_ko]]
    stem_slug = bp.STEM_SLUG[gj[0]]
    branch_slug = bp.BRANCH_SLUG[gj[1]]
    ac = f"var(--{bp.SEL[gj[0]]})"
    an = bp.BR[gj[1]]['an']
    others = [c for c in p['celebs'] if c != name]
    others_html = ''.join(
        f'<a class="oc" href="{slugify(c)}.html">{c}</a>' for c in others) or '<span class="oc" style="border:none">—</span>'
    pillars_html = ''.join(
        f'<div class="pil{" day" if k == "day" else ""}"><div class="lab">{lab}</div>'
        f'<div class="gj">{fp[k]["ganji_hanja"]}</div>'
        f'<div class="gods">{GOD_EN.get(fp[k]["stem_god"], fp[k]["stem_god"])}<br>{GOD_EN.get(fp[k]["branch_god"], fp[k]["branch_god"])}</div></div>'
        for k, lab in (('year', 'Year'), ('month', 'Month'), ('day', 'Day ★')))
    syn = bp.SYN.get(gj, '')
    st_hj, st_en, st_gloss = bp.sitting_stage(gj)
    gi = bp.gz_index(gj)
    ny_hj, ny_en, ny_gloss = bp.NAYIN[gi // 2]
    struct = GOD_EN.get(r.get('geokguk', {}).get('bongi_god'), '')
    audit_html = ''
    if slugify(name) in AUDITS:
        _slug, _no = slugify(name), AUDITS[slugify(name)]
        audit_html = f'''
  <div class="box" style="border-color:var(--gold);background:#c9a2270d;text-align:center">
    <h2 style="margin-bottom:8px">Elun Destiny Audit · {_no}</h2>
    <p style="margin:0 0 14px">This chart was audited decade by decade against {name}'s fully documented life — hits, partials, and misses all graded on the record.</p>
    <a class="btn ghost" href="../audits/{_slug}.html">Read the full audit →</a>
  </div>
'''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<link rel="canonical" href="https://elun.me/famous/{slugify(name)}.html"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{name}'s BaZi Chart — {py} {gj} Day Pillar | Elun</title>
<meta name="description" content="{name} was born on a {py} ({gj}) day — {p['d']} The chart, computed with a deterministic BaZi engine."/>
<meta property="og:title" content="{name}'s BaZi — the {py} day"/>
<meta property="og:description" content="{p['d']}"/>
<meta property="og:image" content="https://elun.me/pillars/og/{bp.slug(py)}.jpg"/>
<meta name="twitter:card" content="summary_large_image"/>
<style>{bp.CSS}
.fhero{{text-align:center;padding:50px 0 10px}}
.fhero .nm{{font-family:var(--serif);font-size:clamp(30px,5.5vw,44px);font-weight:700;margin:0 0 6px}}
.fhero .bd{{color:var(--sub);font-size:13.5px}}
.acard{{position:relative;max-width:460px;margin:26px auto 0;aspect-ratio:16/9;border-radius:16px;overflow:hidden;border:2px solid {ac.replace('var(--','var(--')};box-shadow:0 18px 44px -18px #000}}
.acard .bg{{position:absolute;inset:0;background-image:url(../pillars/art/{stem_slug}.jpg);background-size:cover;background-position:left center}}
.acard .st{{position:absolute;right:-2%;top:50%;transform:translateY(-50%);width:54%;aspect-ratio:16/9;background-image:url(../pillars/art/{branch_slug}.jpg);background-size:contain;background-repeat:no-repeat;background-position:center;mix-blend-mode:screen;opacity:.9;-webkit-mask-image:radial-gradient(ellipse 68% 68% at center,black 45%,transparent 80%);mask-image:radial-gradient(ellipse 68% 68% at center,black 45%,transparent 80%)}}
.acard .sc{{position:absolute;inset:0;background:linear-gradient(180deg,#0e0b0888 0%,transparent 32%,transparent 58%,#0e0b08e6 88%)}}
.acard .hj{{position:absolute;top:12px;left:16px;font-family:var(--serif);font-size:30px;font-weight:700;color:{ac};text-shadow:0 2px 12px #000}}
.acard .pn{{position:absolute;bottom:12px;left:0;right:0;text-align:center;font-family:var(--serif);font-size:20px;font-weight:700;color:{ac};text-shadow:0 2px 10px #000}}
.pillars{{display:flex;gap:10px;max-width:480px;margin:26px auto 8px}}
.pil{{flex:1;border:1px solid var(--line);border-radius:14px;background:var(--card);padding:14px 8px;text-align:center}}
.pil.day{{border-color:var(--gold);box-shadow:0 0 0 3px #c9a2271f;background:#221b10}}
.pil .lab{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--faint)}}
.pil .gj{{font-family:var(--serif);font-size:clamp(22px,5vw,30px);margin:6px 0 4px}}
.pil .gods{{font-size:10px;color:var(--sub);line-height:1.5}}
.note3{{text-align:center;font-size:12px;color:var(--green);margin:6px 0 0}}
.oc{{display:inline-block;border:1px solid var(--line2);border-radius:16px;padding:4px 13px;font-size:12.5px;color:var(--ink2);margin:3px 4px;text-decoration:none}}
.oc:hover{{border-color:var(--gold);color:var(--gold2)}}
.ebars{{margin-top:6px}}
.ebrow{{display:flex;align-items:center;gap:10px;margin:7px 0}}
.ebl{{width:132px;font-size:12.5px;color:var(--ink2);flex:none}}
.ebl b{{font-family:var(--serif);font-weight:400;color:var(--sub)}}
.ebl em{{display:block;font-style:normal;font-size:10px;color:var(--faint);letter-spacing:.5px}}
.ebt{{flex:1;height:10px;background:#12100c;border-radius:5px;overflow:hidden;border:1px solid var(--line)}}
.ebt i{{display:block;height:100%;border-radius:5px}}
.ebp{{width:38px;text-align:right;font-size:12px;color:var(--sub);flex:none}}
.tgc{{display:inline-block;border:1px solid var(--line2);border-radius:14px;padding:3px 11px;font-size:12px;color:var(--gold2);margin:4px 4px 0 0;background:#c9a2270d}}
.kv{{width:100%;border-collapse:collapse;font-size:13.5px}}
.kv td{{padding:9px 10px;border-bottom:1px solid var(--line);color:var(--ink2);vertical-align:top}}
.kv tr:last-child td{{border-bottom:none}}
.kv td:first-child{{color:var(--faint);width:38%;white-space:nowrap}}
.btn.ghost{{background:none;border:1px solid var(--line2);color:var(--ink2)}}
</style>
</head>
<body>
<nav><div class="inner">
  <a href="../index.html" class="logo"><span class="seal">乙</span><span class="m">Elun</span></a>
  <span class="navlinks"><a href="../daymasters.html">Day Masters</a> · <a href="../pillars/">All 60</a> · <a href="../start.html">Your chart</a></span>
</div></nav>

<div class="fhero wrap">
  <div class="nm">{name}</div>
  <div class="bd">Born {y}-{m:02d}-{d:02d} · day pillar computed with Elun's deterministic engine</div>
  <div class="acard"><span class="bg"></span><span class="st"></span><span class="sc"></span>
    <span class="hj">{gj}</span><span class="pn">The {py} Day · {STEM_SYM[gj[0]]} &amp; {an}</span></div>
</div>

<div class="wrap" style="max-width:720px">
  <div class="pillars">{pillars_html}</div>
  <div class="note3">Birth time not on public record — the exact year, month and day pillars shown (the hour pillar is honestly omitted).</div>

  <section>
    {balance_box(r, py)}
    <div class="box" style="border-top:3px solid {ac}">
      <h2>The {py} Day — {name}'s core</h2>
      <p style="font-family:var(--serif);font-style:italic;color:var(--ink2)">“{p['d']}”</p>
      <p>{syn}</p>
      <p><b>The Day Master:</b> {bp.DM[gj[0]]['core'] if gj[0] in bp.DM else dm['core']}</p>
    </div>
    <div class="box">
      <h2>Classical markers</h2>
      <table class="kv">
        <tr><td>Day Master</td><td>{gj[0]} {dm['nm']} — {dm['en']} · “{dm['arch']}”</td></tr>
        <tr><td>Structure</td><td>{struct} Structure</td></tr>
        <tr><td>Sitting stage 十二運星</td><td><span style="display:flex;gap:11px;align-items:center"><a href="../cards.html" title="See all twelve stages" style="flex:none;width:78px;aspect-ratio:16/9;border-radius:6px;background:url(../pillars/art/{bp.STAGE_ART[st_hj]}.jpg) center/cover;box-shadow:inset 0 0 0 1px #ffffff1c, 0 3px 9px -4px #000c"></a><span>{st_en} ({st_hj}) — {st_gloss}</span></span></td></tr>
        <tr><td>Nayin 納音</td><td>{ny_en} ({ny_hj}) — {ny_gloss}</td></tr>
      </table>
    </div>
    <div class="box">
      <h2>Others born on a {py} day</h2>
      {others_html}
      <p style="font-size:12px;color:var(--faint);margin-top:12px">All day pillars computed from public birth records (noon local time; the day pillar is stable except within an hour of midnight).</p>
    </div>
  </section>
{audit_html}
  <div class="cta" style="text-align:center;padding:36px 0 60px">
    <p style="color:var(--sub);max-width:460px;margin:0 auto 18px">Share a day pillar with {name}? There's one way to find out — and it takes a birth date, not a birth time.</p>
    <a class="btn" href="../start.html">Calculate my chart — free</a>
    &nbsp;<a class="btn ghost" href="../pillars/{bp.slug(py)}.html">Read the {py} day in full</a>
  </div>
</div>

<footer>© 2026 Elun · computed, not guessed · for reflection &amp; entertainment</footer>
</body>
</html>'''


def main():
    os.makedirs(OUT, exist_ok=True)
    names = sorted({n for p in P60.values() for n in p['celebs']})
    n = 0
    for name in names:
        if name not in CELEBS:
            print('SKIP (no date):', name)
            continue
        html = page(name)
        if html:
            open(os.path.join(OUT, slugify(name) + '.html'), 'w', encoding='utf-8').write(html)
            n += 1
    # 인덱스
    items = ''.join(
        f'<a class="oc" href="{slugify(nm)}.html">{nm}</a>' for nm in names if nm in CELEBS)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="canonical" href="https://elun.me/famous/"/>
<title>Famous BaZi Charts — {n} Verified Day Pillars | Elun</title>
<meta name="description" content="The day pillars of {n} famous people — computed with a deterministic BaZi engine from public birth records, not guessed."/>
<style>{bp.CSS}
.oc{{display:inline-block;border:1px solid var(--line2);border-radius:16px;padding:5px 14px;font-size:13px;color:var(--ink2);margin:3px 4px;text-decoration:none}}
.oc:hover{{border-color:var(--gold);color:var(--gold2)}}</style></head><body>
<nav><div class="inner"><a href="../index.html" class="logo"><span class="seal">乙</span><span class="m">Elun</span></a>
<span class="navlinks"><a href="../daymasters.html">Day Masters</a> · <a href="../start.html">Your chart</a></span></div></nav>
<div class="hero wrap"><h1 style="font-family:var(--serif)">Famous Charts</h1>
<p style="color:var(--ink2);max-width:560px;margin:0 auto">{n} public figures, their day pillars computed — not guessed — from public birth records. Click any name.</p></div>
<div class="wrap" style="max-width:860px;text-align:center;padding-bottom:70px">{items}</div>
<footer>© 2026 Elun</footer></body></html>''')
    print(f'famous: {n} pages + index → {OUT}')


if __name__ == '__main__':
    main()
