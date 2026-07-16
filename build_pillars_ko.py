#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elun 60 일주 페이지 — 한국어판 생성기.
build_pillars.py(영문·결정론 엔진/헬퍼) + pillars_ko.py(한국어 콘텐츠)를 재사용해
ko/pillars/*.html × 60 + ko/pillars/index.html 을 생성한다. EN 빌드는 건드리지 않는다.
실행:  python3 build_pillars_ko.py
"""
import os, re, json, urllib.parse as _up
import build_pillars as bp
import pillars_ko as ko

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'ko', 'pillars')
A = '../../pillars/art/'          # ko/pillars/ 에서 본 아트 경로 (아트는 EN과 공유)

def slug(py): return py.lower().replace(' ', '-')
def nslug(n): return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')

def ebar_ko(gj):
    s = bp.scores(gj)
    segs = ''.join(
        f'<i class="{bp.ECLS[k]}" style="width:{v:.0f}%" title="{ko.ENAME_KO[k]} {v:.0f}%"></i>'
        for k, v in s.items() if v > 0.5)
    return f'<div class="ebar">{segs}</div>'

def badges_ko(gj):
    out = []
    stars = bp.DAY_STARS.get(gj, [])
    if 'kui' in stars:   out.append(('희귀', '괴강 魁罡'))
    if gj in bp.PURE_PILLARS: out.append(('희귀', '간지일기 干支一氣'))
    if 'noble' in stars: out.append(('길성', '천을귀인 天乙貴人'))
    if 'blade' in stars and len(out) < 2: out.append(('강렬', '양인 羊刃'))
    return out[:2]

def sitting_stage_ko(gj):
    start, d = bp.STAGE_START[gj[0]]
    return ko.STAGE_INFO_KO[(bp.B_ORD.index(gj[1]) - bp.B_ORD.index(start)) * d % 12]

def page(p, prev_p, next_p, all_pillars):
    gj, py, br = p['gj'], p['py'], p['gj'][1]
    dm, b = ko.DM_KO[gj[0]], ko.BR_KO[br]
    nm = ko.pil_name_ko(gj)                       # 갑자 …
    d_ko = p.get('d_ko') or p['d']
    q_url = _up.quote(f'https://elun.me/ko/pillars/{slug(py)}.html', safe='')
    q_txt = _up.quote(f'{gj} — {nm} 일주: "{d_ko}"', safe='')
    gi = bp.gz_index(gj)
    ny_hj, ny_ko, ny_gloss = ko.NAYIN_KO[gi // 2]
    void1, void2 = bp.VOID_PAIRS[gi // 10]
    st_hj, st_ko, st_gloss = sitting_stage_ko(gj)
    st_art = bp.STAGE_ART[st_hj]
    art_slug = bp.STEM_SLUG[gj[0]]
    branch_slug = bp.BRANCH_SLUG[gj[1]]
    bds = badges_ko(gj)
    badge_html = ''.join(
        f'<span style="display:inline-block;border:1px solid var(--gold);color:var(--gold2);border-radius:14px;padding:3px 12px;font-size:11px;letter-spacing:2px;margin:0 4px">◆ {label} · {name}</span>'
        for label, name in bds)
    if badge_html:
        badge_html = f'<div style="margin-top:14px">{badge_html}</div>'
    nt_hj, nt_ko, nt_gloss = ko.NATURE_INFO_KO[bp.BRANCH_NATURE[gj[1]]]
    star_rows = ''.join(
        f'<tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub)">신살 神煞</td>'
        f'<td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)">'
        f'<b style="color:var(--gold2)">{ko.STAR_INFO_KO[k][1]}</b> ({ko.STAR_INFO_KO[k][0]}) — {ko.STAR_INFO_KO[k][2]}</td></tr>'
        for k in bp.DAY_STARS.get(gj, []))
    siblings = ''.join(
        f'<a href="{slug(q["py"])}.html" style="border:1px solid var(--line2);border-radius:16px;padding:4px 13px;font-size:12.5px;color:var(--ink2);text-decoration:none">{q["gj"]} {ko.pil_name_ko(q["gj"])}</a>'
        for q in all_pillars if q['gj'][0] == gj[0] and q['gj'] != gj)
    main_god = ko.GODS_KO[bp.god(gj[0], bp.HID[br][0][0])]
    ac = f"var(--{bp.SEL[gj[0]]})"
    hid_rows = ''.join(
        f'<tr><td>{h}</td><td>{ko.ENAME_KO[bp.SEL[h]]} · {ko.GODS_KO[bp.god(gj[0],h)]["nm"]} {ko.GODS_KO[bp.god(gj[0],h)]["han"]}'
        f'</td><td style="text-align:right;color:var(--faint)">{w*100:.0f}%</td></tr>'
        for h, w in bp.HID[br])
    celebs = (f'<div class="box"><h2>유명인</h2><div class="fam">'
              + ''.join(f'<a href="../famous/{nslug(c)}.html">{ko.CELEBKO.get(c,c)}</a>' for c in p['celebs'])
              + '</div><p style="font-size:12px;color:var(--faint);margin-top:10px">일주는 공개 출생 기록으로 Elun 엔진이 계산했습니다 — 이름을 누르면 차트로.</p></div>') if p['celebs'] else ''
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{gj} {nm} 일주 — 성격·사랑·직업 | Elun</title>
<meta property="og:type" content="article"/>
<meta property="og:title" content="{gj} {nm} — 육십 일주 중 하나"/>
<meta property="og:description" content="{d_ko}"/>
<meta property="og:image" content="https://elun.me/pillars/og/{slug(py)}.jpg"/>
<meta property="og:url" content="https://elun.me/ko/pillars/{slug(py)}.html"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:image" content="https://elun.me/pillars/og/{slug(py)}.jpg"/>
<link rel="canonical" href="https://elun.me/ko/pillars/{slug(py)}.html"/>
<link rel="alternate" hreflang="en" href="https://elun.me/pillars/{slug(py)}.html"/>
<link rel="alternate" hreflang="ko" href="https://elun.me/ko/pillars/{slug(py)}.html"/>
<link rel="alternate" hreflang="x-default" href="https://elun.me/pillars/{slug(py)}.html"/>
<meta name="description" content="{nm}({gj}) 일주 풀이: {d_ko} 사주에서 {nm} 일주의 성격·생김새·사랑·직업."/>
<style>{bp.CSS}</style>
</head>
<body style="--ac:{ac}">
<nav><div class="inner">
  <a href="../index.html" class="logo"><span class="seal">乙</span><span class="m">Elun</span></a>
  <span class="navlinks"><a href="../daymasters.html">일간</a> · <a href="../daymasters.html#sixty">60일주</a> · <a href="../start.html">내 사주 만들기</a> · <a href="../../pillars/{slug(py)}.html" class="lang-sw" title="English page">EN</a></span>
</div></nav>

<div class="hero wrap" style="position:relative;overflow:hidden">
  <div style="position:absolute;inset:0;background-image:url('{A}{art_slug}.jpg');background-size:cover;background-position:left center;opacity:.7;pointer-events:none"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 75% 80% at 50% 45%,#100d0aee 0%,#100d0ab8 55%,#100d0a44 100%);pointer-events:none"></div>
  <div style="position:absolute;right:-2%;top:50%;transform:translateY(-50%);width:46%;aspect-ratio:16/9;background-image:url('{A}{branch_slug}.jpg');background-size:contain;background-repeat:no-repeat;background-position:center;mix-blend-mode:screen;opacity:.9;pointer-events:none;-webkit-mask-image:radial-gradient(ellipse 68% 68% at center,black 45%,transparent 80%);mask-image:radial-gradient(ellipse 68% 68% at center,black 45%,transparent 80%)"></div>
  <div class="gj" style="position:relative">{gj}</div>
  <h1>{nm} 일주</h1>
  <div class="meta"><b>{dm['nm']} · {dm['en']}</b> 일간, <b>{b['an']}</b> 지지 위 · {b['img']}</div>
  <p class="poetic">“{d_ko}”</p>
  {badge_html}
  <div class="ebarbox">{ebar_ko(gj)}
    <div class="ecap">오행 구성 — 일간 50% · 지장간 50%</div></div>
  <div style="margin-top:18px;font-size:12.5px;color:var(--faint);position:relative">
    이 일주 공유:
    <a target="_blank" rel="noopener" style="margin:0 5px" href="https://x.com/intent/post?text={q_txt}&url={q_url}">𝕏</a>·
    <a target="_blank" rel="noopener" style="margin:0 5px" href="https://www.facebook.com/sharer/sharer.php?u={q_url}">Facebook</a>·
    <a target="_blank" rel="noopener" style="margin:0 5px" href="https://wa.me/?text={q_txt}%20{q_url}">WhatsApp</a>
  </div>
</div>

<div class="wrap">
<section>
  <div class="box">
    <h2>{gj}의 정수</h2>
    <p>{ko.SYN_KO[gj]}</p>
    <p><b>일간:</b> {dm['core']}</p>
  </div>

  <div class="box">
    <h2>당신이 딛고 있는 것</h2>
    <div class="sitgod"><span class="h">{main_god['han']}</span><span class="n">{main_god['nm']}</span><span class="k">{main_god['key']}</span></div>
    <p>{main_god['sit']}</p>
    <table class="hidden-tbl">{hid_rows}</table>
    <p style="font-size:12px;color:var(--faint);margin-top:8px">{br}의 지장간과 당신의 {gj[0]} 일간에 대한 관계.</p>
  </div>

  <div class="box">
    <h2>생김새와 인상</h2>
    <p><b>{ko.APP_KO.get(gj,'')}</b></p>
    <p>{dm['nm']} 바탕 — {dm['app']} — 에 {b['an']}의 색이 입혀집니다: {b['app']}. 전통 관상론이니 과학이 아니라 옛이야기로 즐겨 주세요.</p>
    <p><b>기질 노트:</b> {b['tem']}.</p>
  </div>

  <div class="box">
    <h2>사랑</h2>
    <p>{main_god['love']}</p>
  </div>

  <div class="box">
    <h2>일과 방향</h2>
    <p>{main_god['work']}</p>
  </div>

  {celebs}

  <div class="box">
    <h2>고전 지표</h2>
    <table class="kv" style="font-size:13.5px;width:100%;border-collapse:collapse">
      <tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub);width:36%">납음 納音</td>
          <td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)"><b style="color:var(--ink)">{ny_ko}</b> ({ny_hj}) — {ny_gloss}</td></tr>
      <tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub)">일지 십이운성 十二運星</td>
          <td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)"><span style="display:flex;gap:11px;align-items:center"><a href="../cards.html" title="열두 단계 모두 보기" style="flex:none;width:78px;aspect-ratio:16/9;border-radius:6px;background:url({A}{st_art}.jpg) center/cover;box-shadow:inset 0 0 0 1px #ffffff1c, 0 3px 9px -4px #000c"></a><span><b style="color:var(--ink)">{st_ko}</b> ({st_hj}) — {st_gloss}</span></span></td></tr>
      <tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub)">지지 성정</td>
          <td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)"><b style="color:var(--ink)">{nt_ko}</b> ({nt_hj}) — {nt_gloss}</td></tr>
      {star_rows}
      <tr><td style="padding:8px 4px;color:var(--sub)">공망 空亡</td>
          <td style="padding:8px 4px;color:var(--ink2)"><b style="color:var(--ink)">{void1} · {void2}</b> — 이 일주가 가볍게 쥐는 삶의 영역; 고전 명리는 집착 없이 다가갈 주제로 읽습니다</td></tr>
    </table>
    <p style="font-size:11px;color:var(--faint);margin-top:8px">십이운성은 고전 전통을 따릅니다(음간은 순환을 역행).</p>
  </div>

  <div class="box">
    <h2>다른 {dm['nm']} 일주</h2>
    <div class="fam">{siblings}</div>
  </div>
</section>

<div class="pn">
  <a href="{slug(prev_p['py'])}.html">← {prev_p['gj']} {ko.pil_name_ko(prev_p['gj'])}</a>
  <a href="../daymasters.html#{dm['id']}">{dm['nm']} 프로필</a>
  <a href="{slug(next_p['py'])}.html">{next_p['gj']} {ko.pil_name_ko(next_p['gj'])} →</a>
</div>

<div class="cta">
  <p>{gj}가 정말 당신의 일주일까요? 자정 무렵이나 절기 경계에서는 정밀함만이 판가름합니다.</p>
  <a class="btn" href="../start.html">내 사주 계산하기 — 무료</a>
</div>
</div>

<footer>© 2026 Elun · <a href="../index.html">홈</a> · <a href="../daymasters.html">열 개의 일간</a> · 성찰과 즐거움을 위한 해석적 읽기</footer>
</body></html>'''

def main():
    data = json.load(open(bp.ENGINE, encoding='utf-8'))['pillars']
    assert len(data) == 60
    os.makedirs(OUT, exist_ok=True)
    for i, p in enumerate(data):
        prev_p, next_p = data[(i-1) % 60], data[(i+1) % 60]
        html = page(p, prev_p, next_p, data)
        open(os.path.join(OUT, slug(p['py'])+'.html'), 'w', encoding='utf-8').write(html)
    # index
    items = ''.join(
        f'<a class="it" style="--ac:var(--{bp.SEL[p["gj"][0]]})" href="{slug(p["py"])}.html">'
        f'<span class="g">{p["gj"]}</span><span>{ko.pil_name_ko(p["gj"])}<br><small>{ko.BR_KO[p["gj"][1]]["an"]}</small></span></a>'
        for p in data)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>육십 일주 — 색인 | Elun</title>
<link rel="canonical" href="https://elun.me/ko/pillars/"/>
<link rel="alternate" hreflang="en" href="https://elun.me/pillars/"/>
<link rel="alternate" hreflang="ko" href="https://elun.me/ko/pillars/"/>
<meta name="description" content="사주 육십 일주 전체 — 각 간지(干支)의 성격·사랑·직업·생김새."/>
<style>{bp.CSS}
.gridx{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;padding:30px 0 60px}}
.it{{display:flex;gap:10px;align-items:center;border:1px solid var(--line);border-radius:12px;background:var(--card);padding:12px 14px;color:var(--ink2);font-size:13px}}
.it:hover{{border-color:var(--gold)}}
.it .g{{font-family:var(--serif);font-size:22px;color:var(--ac)}}
.it small{{color:var(--faint)}}</style></head><body>
<nav><div class="inner">
  <a href="../index.html" class="logo"><span class="seal">乙</span><span class="m">Elun</span></a>
  <span class="navlinks"><a href="../daymasters.html">일간</a> · <a href="../start.html">내 사주 만들기</a> · <a href="../../pillars/" class="lang-sw" title="English page">EN</a></span>
</div></nav>
<div class="hero wrap"><h1 style="font-family:var(--serif)">육십 일주</h1>
<p style="color:var(--ink2)">모든 간지 조합, 저마다의 성격 서명.</p></div>
<div class="wrap"><div class="gridx">{items}</div></div>
<footer>© 2026 Elun · <a href="../daymasters.html">열 개의 일간</a></footer>
</body></html>''')
    print(f'wrote 60 KO pages + index → {OUT}')

if __name__ == '__main__':
    main()
