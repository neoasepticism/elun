#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elun 유명인 사주 페이지 — 한국어판 생성기.
build_famous.py 와 동일한 차트 엔진(bg)·헬퍼(rp) + pillars_ko.py(한국어) 로
ko/famous/*.html + index 생성. EN 빌드(build_famous.py)는 건드리지 않는다.
실행:  python3 build_famous_ko.py   (요구: ~/elun-engine)
"""
import os, re, json, sys, importlib.util
from collections import Counter

sys.path.insert(0, os.path.expanduser('~/elun-engine'))
import bazi_global as bg
import report_premium as rp
from report import GAN_OH, JI_OH

import build_pillars as bp
import pillars_ko as ko

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'ko', 'famous')
A = '../../pillars/art/'            # ko/famous/ 에서 본 공유 아트 경로

CELEBS = json.load(open(os.path.join(ROOT, 'celebs.json'), encoding='utf-8'))
P60 = {p['gj']: p for p in json.load(open(os.path.expanduser('~/elun-engine/pillar60.json'), encoding='utf-8'))['pillars']}

AUDITS = {'masayoshi-son': 'No.001', 'steve-jobs': 'No.002'}

STEM_HJ = {'갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸'}
STEM_SYM_KO = {'甲':'나무','乙':'넝쿨','丙':'태양','丁':'등불','戊':'산','己':'밭','庚':'칼','辛':'보석','壬':'바다','癸':'비'}
ELEM_EN_KO = {v: k for k, v in rp.ELEM_KO_EN.items()}          # Wood→목 …
ROLE_EN_KO = {'Output':'식상', 'Wealth':'재성', 'Resource':'인성', 'Peers':'비겁',
              'Peer':'비겁', 'Officer':'관성', 'Self':'비겁'}
ELEM_META = {'목': ('목', '木', 'wood'), '화': ('화', '火', 'fire'), '토': ('토', '土', 'earth'),
             '금': ('금', '金', 'metal'), '수': ('수', '水', 'water')}


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def chart_for(name):
    y, m, d, tz = CELEBS[name]
    opts = {'lon_corr': False, 'dst': False, 'std_meridian': None, 'lon': 0, 'auto_tz': True, 'tz': tz}
    return bg.build_result(y, m, d, 12, 0, 'M', opts)


def fe3(fp):
    """3주(년월일) 기준 오행 분포 — 시주(정오 가정) 제외."""
    c = Counter()
    for k in ('year', 'month', 'day'):
        c[GAN_OH[fp[k]['stem']]] += 1
        c[JI_OH[fp[k]['branch']]] += 1
    tot = sum(c.values()) or 1
    return {oh: round(c[oh] / tot * 100) for oh in ('목', '화', '토', '금', '수')}


def role_ko(role_en):
    return ROLE_EN_KO.get(role_en, role_en)


def balance_box(chart, nm_ko):
    fp = chart['four_pillars']
    dm_elem_en = rp.ELEM_KO_EN[chart['day_master']['element']]
    roles = rp._elem_roles(dm_elem_en)                     # {EnglishElem: RoleEnglish}
    oh = fe3(fp)
    st_label = rp._strength_three_pillar(chart)['label']   # 한국어 (예: 신강/중화/신약)
    if '약' in st_label:
        st_gloss = '지원으로 굴러가는 사주 — 무엇이 일간을 먹이는가가 이야기의 축입니다'
    elif '강' in st_label:
        st_gloss = '제 무게를 스스로 지는 사주 — 남는 힘을 어디에 쓰는가가 이야기의 축입니다'
    else:
        st_gloss = '균형에 가까운 사주 — 운의 작은 기울기가 판 전체를 기울입니다'
    ug = rp._useful_god(dm_elem_en, st_label)
    hp = fp.get('hour', {})
    tg = dict(chart.get('ten_gods_count', {}))
    for g in (hp.get('stem_god'), hp.get('branch_god')):
        if g in tg:
            tg[g] -= 1
            if tg[g] <= 0:
                del tg[g]
    bars = ''
    for k in ('목', '화', '토', '금', '수'):
        en, hj, var = ELEM_META[k]
        pct = oh[k]
        role_en = roles[rp.ELEM_KO_EN[k]]
        bars += (f'<div class="ebrow"><span class="ebl">{en} <b>{hj}</b><em>{role_ko(role_en)}</em></span>'
                 f'<span class="ebt"><i style="width:{max(pct, 2)}%;background:var(--{var})"></i></span>'
                 f'<span class="ebp">{pct}%</span></div>')
    chips = ''.join(
        f'<span class="tgc">{g}{f" ×{n}" if n > 1 else ""}</span>'
        for g, n in sorted(tg.items(), key=lambda x: -x[1]) if g != '일간')
    ug_p = f'{ELEM_EN_KO.get(ug["primary_elem"], ug["primary_elem"])}({role_ko(ug["primary_role"])})'
    ug_s = f'{ELEM_EN_KO.get(ug["secondary_elem"], ug["secondary_elem"])}({role_ko(ug["secondary_role"])})'
    return f'''<div class="box">
      <h2>균형 — 이 사주를 이 사주답게 만드는 것</h2>
      <p style="font-size:13.5px">모든 {nm_ko} 일주는 같은 핵심을 공유합니다 — 그러나 그것을 둘러싼 연·월은 결코 반복되지 않습니다.
      이 사주가 실제로 받은 배합입니다(3주 기준, 시주 제외):</p>
      <div class="ebars">{bars}</div>
      <table class="kv" style="margin-top:14px">
        <tr><td>강약</td><td>{st_label} — {st_gloss}</td></tr>
        <tr><td>용신 用神</td><td>{ug_p} 우선 · {ug_s} 다음</td></tr>
      </table>
      <div style="margin-top:12px"><span style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--faint)">사주 속 십성</span><br>{chips}</div>
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
    nm_pil = ko.pil_name_ko(gj)                 # 일주 한글명 (갑자)
    disp = ko.CELEBKO.get(name, name)           # 인물 한글 표기
    d_ko = p.get('d_ko') or p['d']
    dm = ko.DM_KO[gj[0]]
    stem_slug = bp.STEM_SLUG[gj[0]]
    branch_slug = bp.BRANCH_SLUG[gj[1]]
    ac = f"var(--{bp.SEL[gj[0]]})"
    an = ko.BR_KO[gj[1]]['an']
    others = [c for c in p['celebs'] if c != name]
    others_html = ''.join(
        f'<a class="oc" href="{slugify(c)}.html">{ko.CELEBKO.get(c, c)}</a>' for c in others) or '<span class="oc" style="border:none">—</span>'
    pillars_html = ''.join(
        f'<div class="pil{" day" if k == "day" else ""}"><div class="lab">{lab}</div>'
        f'<div class="gj">{fp[k]["ganji_hanja"]}</div>'
        f'<div class="gods">{fp[k]["stem_god"]}<br>{fp[k]["branch_god"]}</div></div>'
        for k, lab in (('year', '년주'), ('month', '월주'), ('day', '일주 ★')))
    syn = ko.SYN_KO.get(gj, '')
    st_hj, st_ko_nm, st_gloss = (lambda s: s)(_sitting_stage_ko(gj))
    gi = bp.gz_index(gj)
    ny_hj, ny_ko_nm, ny_gloss = ko.NAYIN_KO[gi // 2]
    struct = r.get('geokguk', {}).get('bongi_god') or ''
    audit_html = ''
    sl = slugify(name)
    if sl in AUDITS:
        _no = AUDITS[sl]
        audit_html = f'''
  <div class="box" style="border-color:var(--gold);background:#c9a2270d;text-align:center">
    <h2 style="margin-bottom:8px">Elun Destiny Audit · {_no}</h2>
    <p style="margin:0 0 14px">이 사주는 {disp}의 기록으로 남은 삶에 10년 단위로 대조해 감정했습니다 — 적중·부분·빗나감까지 모두 기록 위에서 등급을 매겼습니다.</p>
    <a class="btn ghost" href="../../audits/{sl}-ko.html">전체 감정 읽기 →</a>
    <div style="font-size:12px;color:var(--faint);margin-top:10px"><a href="../../audits/{sl}.html" style="color:var(--sub)">English →</a></div>
  </div>
'''
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<link rel="canonical" href="https://elun.me/ko/famous/{sl}.html"/>
<link rel="alternate" hreflang="en" href="https://elun.me/famous/{sl}.html"/>
<link rel="alternate" hreflang="ko" href="https://elun.me/ko/famous/{sl}.html"/>
<link rel="alternate" hreflang="x-default" href="https://elun.me/famous/{sl}.html"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{disp}의 사주 — {nm_pil} {gj} 일주 | Elun</title>
<meta name="description" content="{disp}은(는) {nm_pil}({gj}) 일에 태어났습니다 — {d_ko} 결정론적 사주 엔진으로 계산한 차트."/>
<meta property="og:title" content="{disp}의 사주 — {nm_pil} 일주"/>
<meta property="og:description" content="{d_ko}"/>
<meta property="og:image" content="https://elun.me/pillars/og/{bp.slug(py)}.jpg"/>
<meta name="twitter:card" content="summary_large_image"/>
<style>{bp.CSS}
.fhero{{text-align:center;padding:50px 0 10px}}
.fhero .nm{{font-family:var(--serif);font-size:clamp(30px,5.5vw,44px);font-weight:700;margin:0 0 6px}}
.fhero .bd{{color:var(--sub);font-size:13.5px}}
.acard{{position:relative;max-width:460px;margin:26px auto 0;aspect-ratio:16/9;border-radius:16px;overflow:hidden;border:2px solid {ac};box-shadow:0 18px 44px -18px #000}}
.acard .bg{{position:absolute;inset:0;background-image:url({A}{stem_slug}.jpg);background-size:cover;background-position:left center}}
.acard .st{{position:absolute;right:-2%;top:50%;transform:translateY(-50%);width:54%;aspect-ratio:16/9;background-image:url({A}{branch_slug}.jpg);background-size:contain;background-repeat:no-repeat;background-position:center;mix-blend-mode:screen;opacity:.9;-webkit-mask-image:radial-gradient(ellipse 68% 68% at center,black 45%,transparent 80%);mask-image:radial-gradient(ellipse 68% 68% at center,black 45%,transparent 80%)}}
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
  <span class="navlinks"><a href="../daymasters.html">일간</a> · <a href="../pillars/">60일주</a> · <a href="../start.html">내 사주</a> · <a href="../../famous/{sl}.html" class="lang-sw" title="English page">EN</a></span>
</div></nav>

<div class="fhero wrap">
  <div class="nm">{disp}</div>
  <div class="bd">{y}-{m:02d}-{d:02d} 출생 · 일주는 Elun 결정론 엔진으로 계산</div>
  <div class="acard"><span class="bg"></span><span class="st"></span><span class="sc"></span>
    <span class="hj">{gj}</span><span class="pn">{nm_pil} 일주 · {STEM_SYM_KO[gj[0]]}와 {an}</span></div>
</div>

<div class="wrap" style="max-width:720px">
  <div class="pillars">{pillars_html}</div>
  <div class="note3">출생 시각은 공개 기록에 없습니다 — 확실한 연·월·일주만 표시합니다(시주는 정직하게 생략).</div>

  <section>
    {balance_box(r, nm_pil)}
    <div class="box" style="border-top:3px solid {ac}">
      <h2>{nm_pil} 일주 — {disp}의 핵심</h2>
      <p style="font-family:var(--serif);font-style:italic;color:var(--ink2)">“{d_ko}”</p>
      <p>{syn}</p>
      <p><b>일간:</b> {dm['core']}</p>
    </div>
    <div class="box">
      <h2>고전 지표</h2>
      <table class="kv">
        <tr><td>일간</td><td>{gj[0]} {dm['nm']} — {dm['en']} · “{dm['arch']}”</td></tr>
        <tr><td>격국</td><td>{struct}격</td></tr>
        <tr><td>일지 십이운성 十二運星</td><td><span style="display:flex;gap:11px;align-items:center"><a href="../cards.html" title="열두 단계 모두 보기" style="flex:none;width:78px;aspect-ratio:16/9;border-radius:6px;background:url({A}{bp.STAGE_ART[st_hj]}.jpg) center/cover;box-shadow:inset 0 0 0 1px #ffffff1c, 0 3px 9px -4px #000c"></a><span>{st_ko_nm} ({st_hj}) — {st_gloss}</span></span></td></tr>
        <tr><td>납음 納音</td><td>{ny_ko_nm} ({ny_hj}) — {ny_gloss}</td></tr>
      </table>
    </div>
    <div class="box">
      <h2>같은 {nm_pil} 일주로 태어난 이들</h2>
      {others_html}
      <p style="font-size:12px;color:var(--faint);margin-top:12px">모든 일주는 공개 출생 기록으로 계산했습니다(현지 정오 기준; 자정 전후 한 시간을 제외하면 일주는 안정적입니다).</p>
    </div>
  </section>
{audit_html}
  <div class="cta" style="text-align:center;padding:36px 0 60px">
    <p style="color:var(--sub);max-width:460px;margin:0 auto 18px">{disp}와 같은 일주일까요? 확인하는 길은 하나뿐 — 출생 시각이 아니라 출생일이면 됩니다.</p>
    <a class="btn" href="../start.html">내 사주 계산하기 — 무료</a>
    &nbsp;<a class="btn ghost" href="../pillars/{bp.slug(py)}.html">{nm_pil} 일주 전체 읽기</a>
  </div>
</div>

<footer>© 2026 Elun · 추측이 아니라 계산 · 성찰과 즐거움을 위한 것</footer>
</body>
</html>'''


def _sitting_stage_ko(gj):
    start, dd = bp.STAGE_START[gj[0]]
    return ko.STAGE_INFO_KO[(bp.B_ORD.index(gj[1]) - bp.B_ORD.index(start)) * dd % 12]


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
    items = ''.join(
        f'<a class="oc" href="{slugify(nm)}.html">{ko.CELEBKO.get(nm, nm)}</a>' for nm in names if nm in CELEBS)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="canonical" href="https://elun.me/ko/famous/"/>
<link rel="alternate" hreflang="en" href="https://elun.me/famous/"/>
<link rel="alternate" hreflang="ko" href="https://elun.me/ko/famous/"/>
<title>유명인 사주 — 검증된 일주 {n}인 | Elun</title>
<meta name="description" content="유명인 {n}인의 일주 — 공개 출생 기록으로 결정론적 사주 엔진이 계산했습니다. 추측이 아닙니다."/>
<style>{bp.CSS}
.oc{{display:inline-block;border:1px solid var(--line2);border-radius:16px;padding:5px 14px;font-size:13px;color:var(--ink2);margin:3px 4px;text-decoration:none}}
.oc:hover{{border-color:var(--gold);color:var(--gold2)}}</style></head><body>
<nav><div class="inner"><a href="../index.html" class="logo"><span class="seal">乙</span><span class="m">Elun</span></a>
<span class="navlinks"><a href="../daymasters.html">일간</a> · <a href="../start.html">내 사주</a> · <a href="../../famous/" class="lang-sw" title="English page">EN</a></span></div></nav>
<div class="hero wrap"><h1 style="font-family:var(--serif)">유명인 차트</h1>
<p style="color:var(--ink2);max-width:560px;margin:0 auto">공인 {n}인, 그 일주를 공개 출생 기록으로 계산했습니다 — 추측이 아닙니다. 이름을 누르세요.</p></div>
<div class="wrap" style="max-width:860px;text-align:center;padding-bottom:70px">{items}</div>
<footer>© 2026 Elun</footer></body></html>''')
    print(f'famous KO: {n} pages + index → {OUT}')


if __name__ == '__main__':
    main()
