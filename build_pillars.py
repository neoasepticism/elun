#!/usr/bin/env python3
"""
Elun 60 day-pillar page generator.
Reads ~/elun-engine/pillar60.json (single source) + content blocks below,
writes pillars/{slug}.html × 60 + pillars/index.html.
Run:  python3 build_pillars.py
"""
import json, os, re

ENGINE = os.path.expanduser('~/elun-engine/pillar60.json')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pillars')

# ── element machinery ────────────────────────────────────────────────
SEL = {'甲':'wood','乙':'wood','丙':'fire','丁':'fire','戊':'earth',
       '己':'earth','庚':'metal','辛':'metal','壬':'water','癸':'water'}
YANG = set('甲丙戊庚壬')
GEN = {'wood':'fire','fire':'earth','earth':'metal','metal':'water','water':'wood'}
CTRL = {'wood':'earth','earth':'water','water':'fire','fire':'metal','metal':'wood'}
HID = {'子':[('癸',1)],'丑':[('己',.6),('癸',.3),('辛',.1)],'寅':[('甲',.6),('丙',.3),('戊',.1)],
       '卯':[('乙',1)],'辰':[('戊',.6),('乙',.3),('癸',.1)],'巳':[('丙',.6),('庚',.3),('戊',.1)],
       '午':[('丁',.7),('己',.3)],'未':[('己',.6),('丁',.3),('乙',.1)],'申':[('庚',.6),('壬',.3),('戊',.1)],
       '酉':[('辛',1)],'戌':[('戊',.6),('辛',.3),('丁',.1)],'亥':[('壬',.7),('甲',.3)]}
ECLS = {'wood':'w','fire':'f','earth':'e','metal':'m','water':'a'}
ENAME = {'wood':'Wood','fire':'Fire','earth':'Earth','metal':'Metal','water':'Water'}

def god(day, other):
    de, oe = SEL[day], SEL[other]
    same_pol = (day in YANG) == (other in YANG)
    if de == oe:            return 'ally' if same_pol else 'rival'
    if GEN[de] == oe:       return 'creator' if same_pol else 'maverick'
    if CTRL[de] == oe:      return 'entrepreneur' if same_pol else 'steward'
    if CTRL[oe] == de:      return 'challenger' if same_pol else 'governor'
    if GEN[oe] == de:       return 'mystic' if same_pol else 'scholar'
    raise ValueError

def scores(gj):
    s = {'wood':0.0,'fire':0.0,'earth':0.0,'metal':0.0,'water':0.0}
    s[SEL[gj[0]]] += 50
    for h, w in HID[gj[1]]:
        s[SEL[h]] += 50*w
    return s

# ── ten-god archetype blocks (sitting god = branch main hidden stem) ─
GODS = {
 'ally': dict(nm='The Ally', han='比肩', key='Peer · independence',
   sit="You sit on your own element — a Day Master resting on its twin. This doubles self-reliance: your instincts trust themselves first, you recover alone, and you rarely feel incomplete without company. The risk is a certain imperviousness; advice bounces off you.",
   love="In love you need an equal, not an admirer or a caretaker. Side-by-side partnership — two whole people walking the same road — suits you far better than fusion.",
   work="You work best with ownership: your own desk, your own targets, your own name on the result. Independence is not a perk for you; it is a requirement."),
 'rival': dict(nm='The Rival', han='劫財', key='Competition · drive',
   sit="You sit on your element in its opposite polarity — a built-in sparring partner. There is a competitive engine idling under everything you do: you measure, you compare, you push. It makes you fast and brave, and occasionally your own fiercest opponent.",
   love="Relationships carry electricity — you are drawn to people who challenge you, and boredom is a bigger threat than conflict. Guard shared finances and pride; both are classic flashpoints.",
   work="You perform best where results are visible and scored — sales, sport, litigation, markets. A worthy competitor improves you more than a comfortable environment ever will."),
 'creator': dict(nm='The Creator', han='食神', key='Expression · flow',
   sit="You sit on your natural output — talent flows out of you with unusual ease. This is the classic signature of appetite for life: making, cooking, performing, explaining, enjoying. Expression isn't effort for you; it's exhale.",
   love="You love warmly and tangibly — feeding people, making things for them, filling the room with ease. You need a partner who receives well, not one who rations joy.",
   work="Craft and content are your lanes: creative work, teaching, food and hospitality, anything where the pleasure you take in making is visible in the result."),
 'maverick': dict(nm='The Maverick', han='傷官', key='Defiance · genius',
   sit="You sit on your output in its rebellious form — brilliance that chafes at every frame. You see the flaw in the rule, the better way nobody authorized, and you say so. It is your genius and your paperwork problem in one.",
   love="You are exciting to love and demanding to keep up with — articulate, critical, allergic to dullness. The right partner enjoys your edge instead of bracing against it.",
   work="Innovation, performance, commentary, design — anywhere the point is to break the frame beautifully. Under rigid bureaucracy you corrode; with creative license you dazzle."),
 'steward': dict(nm='The Steward', han='正財', key='Earned wealth · steadiness',
   sit="You sit on wealth in its earned, orderly form. Practicality is bone-deep: you count what you have, keep what you promise, and build in increments that survive. People trust you with things that matter.",
   love="You show love through reliability — remembered dates, managed logistics, a stable home. Devotion, once given, is thorough; flightiness in a partner genuinely bewilders you.",
   work="Management, finance, operations, property — anywhere careful hands compound small gains into real estates. You are the person the ledger loves."),
 'entrepreneur': dict(nm='The Entrepreneur', han='偏財', key='Windfall · opportunity',
   sit="You sit on wealth in its moving form — opportunity, circulation, the deal in the air. Money and resources come and go in waves around you, and your instinct for the opening is real. So is your boredom with maintenance.",
   love="You are generous and fun — the grand gesture comes naturally — but attention can wander wherever the next interesting thing glitters. Choose a partner who is a fellow adventurer.",
   work="Business development, trading, brokerage, anything with moving parts and upside. You monetize what others merely notice; just let someone else hold the keys to the vault."),
 'governor': dict(nm='The Governor', han='正官', key='Authority · order',
   sit="You sit on legitimate authority — discipline is installed at the root. You respect structure, keep form, and are in turn trusted with position. Duty is not a burden you carry; it is a shape you naturally take.",
   love="You are a responsible, presentable, marriage-minded partner — the one parents approve of. Allow some disorder into intimacy; love is not an audit.",
   work="Institutions reward you: public service, law, corporate leadership, medicine. Reputation compounds for you like interest — protect it and it will carry you."),
 'challenger': dict(nm='The Challenger', han='偏官', key='Conquest · pressure',
   sit="You sit on raw power — the classic Seven Killings seat. Pressure lives with you like a housemate: life keeps testing you, and testing has made you formidable. Others crack where you concentrate.",
   love="Your intensity is magnetic and unnerving in equal measure. You protect fiercely and demand much; the right partner is steady enough not to flinch and honest enough to push back.",
   work="Crisis is your element: surgery, command, enforcement, turnarounds, competition. Give you a hard problem and authority to act, and stand back."),
 'scholar': dict(nm='The Scholar', han='正印', key='Mentorship · support',
   sit="You sit on the element that feeds you — a lifelong current of support, learning, and shelter runs beneath your feet. Knowledge sticks to you; elders and mentors appear when needed. Your task is to act on what you absorb, not merely collect it.",
   love="You need care that feels like understanding — being read accurately is your love language. You offer depth and patience; demand the same.",
   work="Study, research, teaching, advisory, credentialed professions. Your authority is earned through knowing — degrees, licenses, and books are your natural currency."),
 'mystic': dict(nm='The Mystic', han='偏印', key='Intuition · insight',
   sit="You sit on unconventional nourishment — your mind feeds from side doors: intuition, odd disciplines, patterns others dismiss. You know things before you can explain them, and solitude is where you digest.",
   love="You need more privacy than most partners expect, and you attach deeply to the few who don't take that personally. Being alone together is your ideal intimacy.",
   work="Niche mastery is your path: specialized medicine, esoteric tech, analytics, occult and healing arts, archives. The stranger the field, the more at home you are."),
}

# ── branch overlays (season imagery, appearance, temperament) ────────
BR = {
 '子': dict(an='Rat', img='midnight water · midwinter', app="quicker movements and sharper, watchful eyes; a face that gives little away",
      tem="a nocturnal mind — your best thinking happens after dark, and your depths stay private"),
 '丑': dict(an='Ox', img='frozen field · late winter', app="a sturdy, grounded frame and patient, unhurried expression",
      tem="slow-burn endurance — you outlast rather than outpace, and winter does not frighten you"),
 '寅': dict(an='Tiger', img='first wood · early spring', app="an upright bearing with restless, forward-leaning energy",
      tem="initiative — you move first, ask later, and stagnation feels like suffocation"),
 '卯': dict(an='Rabbit', img='full bloom · mid-spring', app="softer, youthful features that age slowly and disarm quickly",
      tem="refined sociability — you win rooms by grace, not force"),
 '辰': dict(an='Dragon', img='reservoir earth · late spring', app="a broader, more commanding build than your stem alone would suggest",
      tem="stored ambition — the Dragon vault under you holds talent that surfaces in dramatic bursts"),
 '巳': dict(an='Snake', img='rising fire · early summer', app="a sleek presence and intense, penetrating gaze",
      tem="strategic heat — passion that plans, charm that calculates, patience that strikes"),
 '午': dict(an='Horse', img='peak flame · midsummer', app="a bright, expressive face that hides nothing and lights easily",
      tem="visible passion — your feelings broadcast, your energy peaks fast and needs a track to run on"),
 '未': dict(an='Goat', img='warm dry earth · late summer', app="gentle, rounded features over an unexpectedly stubborn jaw",
      tem="stubborn sweetness — soft manner, immovable core, long memory for kindness and slight alike"),
 '申': dict(an='Monkey', img='first metal · early autumn', app="angular features and agile, economical movement",
      tem="clever versatility — many tools, quick switches, an engineer's delight in how things work"),
 '酉': dict(an='Rooster', img='pure metal · mid-autumn', app="fine, precise features — the most polished version of your stem's look",
      tem="exacting polish — details register loudly, and 'good enough' never quite is"),
 '戌': dict(an='Dog', img='guarding earth · late autumn', app="a solid, dependable look that people instinctively trust",
      tem="guardian loyalty — you keep the gate, keep the faith, and keep receipts"),
 '亥': dict(an='Pig', img='deep water · early winter', app="softer, fuller features and a warm, unguarded smile",
      tem="generous depth — you give from a deep well and think in oceans, not puddles"),
}

# ── day-master cores (condensed from daymasters.html) ────────────────
DM = {
 '甲': dict(id='jia', nm='Jia', en='Yang Wood', arch='The Pioneer', img='the colossal tree',
   core="Jia grows in one direction — up. A strong internal compass, visible integrity, and a builder's patience define this Day Master; it would rather break than bend.",
   app="tall or long-limbed, upright posture, a longer face and steady level gaze"),
 '乙': dict(id='yi', nm='Yi', en='Yin Wood', arch='The Diplomat', img='the vine and flower',
   core="Yi grows by finding the way around — reading rooms, borrowing trellises, surviving storms that snap trees. Its flexibility is its strength and it is always underestimated.",
   app="slender and graceful, soft expressive features, looks younger than its years"),
 '丙': dict(id='bing', nm='Bing', en='Yang Fire', arch='The Radiant', img='the blazing sun',
   core="Bing shines on everyone without calculation. Warmth, visibility and big-picture optimism are its nature; details bore it, direction ignites it.",
   app="broad open forehead, bright complexion, a big natural smile and energetic stride"),
 '丁': dict(id='ding', nm='Ding', en='Yin Fire', arch='The Illuminator', img='the candle flame',
   core="Ding is aimed fire — the lantern, not the sun. It illuminates completely whatever it focuses on, perceives subtext to an uncanny degree, and warms one person at a time.",
   app="finer features with striking bright eyes — the flame shows in the gaze"),
 '戊': dict(id='wu', nm='Wu', en='Yang Earth', arch='The Anchor', img='the mountain',
   core="Wu is the mountain: massive, dependable, unmoved by weather. It absorbs pressure that cracks others and becomes the load-bearing wall of any group it joins.",
   app="solid broad frame, strong nose, calm weighty presence and unhurried movement"),
 '己': dict(id='ji', nm='Ji', en='Yin Earth', arch='The Cultivator', img='the fertile field',
   core="Ji is garden soil — the earth that feeds. Things and people simply grow better near it; its power works underground and compounds like richness in loam.",
   app="softer rounded features, an approachable face, a warm settled voice"),
 '庚': dict(id='geng', nm='Geng', en='Yang Metal', arch='The Vanguard', img='the forged blade',
   core="Geng is raw metal that improves in the forge. Direct, just, energized by adversity — it cuts through ambiguity and says the thing everyone is thinking.",
   app="strong bone structure, square jaw, direct eye contact and a voice that carries"),
 '辛': dict(id='xin', nm='Xin', en='Yin Metal', arch='The Refiner', img='the fine jewel',
   core="Xin is finished metal — jewel, needle, scalpel. Exquisite standards, effortless-looking polish, and a quiet pride that knows exactly what it is worth.",
   app="fine polished features, clear skin, impeccable grooming, a composed glint"),
 '壬': dict(id='ren', nm='Ren', en='Yang Water', arch='The Navigator', img='the vast ocean',
   core="Ren is ocean and great river — vast, restless, connecting shores. It thinks in systems and horizons and carries a current that always points somewhere new.",
   app="a fuller or fluid build, lively roving eyes, expansive gestures, magnetic in motion"),
 '癸': dict(id='gui', nm='Gui', en='Yin Water', arch='The Seer', img='the gentle rain',
   core="Gui is rain, mist, the underground spring — water at its most subtle. It perceives what others miss and, like water finding cracks, eventually arrives everywhere it intends.",
   app="delicate features, soft luminous eyes, a quiet voice, easy to overlook and hard to forget"),
}


# ── 납음(納音) 30쌍 · 공망(空亡) · 일주별 생김새 ──────────────────────
S_ORD = '甲乙丙丁戊己庚辛壬癸'
B_ORD = '子丑寅卯辰巳午未申酉戌亥'

def gz_index(gj):
    st, br = S_ORD.index(gj[0]), B_ORD.index(gj[1])
    for i in range(60):
        if i % 10 == st and i % 12 == br:
            return i
    raise ValueError(gj)

VOID_PAIRS = [('戌', '亥'), ('申', '酉'), ('午', '未'), ('辰', '巳'), ('寅', '卯'), ('子', '丑')]

# 십이운성 — 고전 순역법 (양간 순행 · 음간 역행, 화토동궁)
STAGE_START = {'甲': ('亥', 1), '丙': ('寅', 1), '戊': ('寅', 1), '庚': ('巳', 1), '壬': ('申', 1),
               '乙': ('午', -1), '丁': ('酉', -1), '己': ('酉', -1), '辛': ('子', -1), '癸': ('卯', -1)}
STAGE_INFO = [  # (한자, 영문명, 한 줄 의미)
 ('長生', 'Birth', 'fresh vitality — a pillar that begins things and keeps a beginner\'s openness'),
 ('沐浴', 'Bath', 'raw and newly exposed — charm, sensitivity, and a changeable current'),
 ('冠帶', 'Coming of Age', 'putting on the robes — ambition dressing itself for the world'),
 ('建祿', 'Prosperity', 'standing on its own ground — self-made strength at full stride'),
 ('帝旺', 'Peak', 'the zenith of the cycle — maximum force, and the turn that follows it'),
 ('衰', 'Decline', 'past the summit — mellow, seasoned energy that conserves rather than conquers'),
 ('病', 'Weakening', 'energy turned inward — sensitivity, empathy, and a reflective cast'),
 ('死', 'Stillness', 'motion suspended — depth, focus, and detachment from the surface game'),
 ('墓', 'Storage', 'gathered into the vault — a collector\'s nature; resources banked, feelings kept'),
 ('絶', 'Severance', 'the thread cut — energy at its most precarious and most transformable'),
 ('胎', 'Conception', 'new potential forming unseen — imagination gestating its next life'),
 ('養', 'Nurture', 'quietly fed and protected — growth in a sheltered chamber before emergence'),
]

# ── 신살 (일주 단독 판정분만, no-fear-selling 카피) ──────────────────
BRANCH_NATURE = {  # 일지 사정·사생·사고 (왕지/생지/고지)
 '子': 'peach', '午': 'peach', '卯': 'peach', '酉': 'peach',
 '寅': 'horse', '申': 'horse', '巳': 'horse', '亥': 'horse',
 '辰': 'canopy', '戌': 'canopy', '丑': 'canopy', '未': 'canopy',
}
NATURE_INFO = {
 'peach': ('桃花', 'Peach Blossom energy',
   'a cardinal branch — natural magnetism and aesthetic presence; people remember this pillar after one meeting'),
 'horse': ('驛馬', 'Sky Horse energy',
   'a travelling branch — movement is medicine; careers, ideas and addresses that keep moving, restlessness if caged'),
 'canopy': ('華蓋', 'Canopy energy',
   'a storage branch — contemplative, artistic-scholarly depth; genuinely comfortable in its own company'),
}
DAY_STARS = {  # 특정 일주에만 붙는 별
 '庚辰': ['kui'], '庚戌': ['kui'], '壬辰': ['kui'], '壬戌': ['kui', 'tiger'],
 '甲辰': ['tiger'], '乙未': ['tiger'], '丙戌': ['tiger'], '丁丑': ['tiger'],
 '戊辰': ['tiger'], '癸丑': ['tiger'],
 '丙午': ['blade'], '戊午': ['blade'], '壬子': ['blade'],
 '丁酉': ['noble'], '丁亥': ['noble'], '癸巳': ['noble'], '癸卯': ['noble'],
}
STAR_INFO = {
 'kui': ('魁罡', 'Kui Gang — the Commander',
   'classical texts call this the star of generals: all-or-nothing intensity, uncompromising standards, and a fortune that prefers bold moves to safe ones. It rewards high-stakes fields and punishes half-measures'),
 'tiger': ('白虎', 'White Tiger',
   'a pillar that runs at higher voltage — old folklore feared its ferocity; the modern reading is courage and crisis-competence. This energy wants demanding work; give it a real outlet and it protects rather than disrupts'),
 'blade': ('羊刃', 'The Blade', 'a yang stem seated on its own peak — surgical decisiveness and a competitive edge that needs a worthy arena; idle, it turns on its owner as impatience'),
 'noble': ('天乙貴人', 'The Nobleman', 'the classical "luckiest" star — help tends to arrive when it is most needed; benefactors, timely doors, and grace under pressure are this pillar\'s quiet privilege'),
}

PURE_PILLARS = {'甲寅','乙卯','丙午','丁巳','戊戌','戊辰','己丑','己未','庚申','辛酉','壬子','癸亥'}

def badges(gj):
    """희귀/특수 배지 (최대 2개)."""
    out = []
    stars = DAY_STARS.get(gj, [])
    if 'kui' in stars:
        out.append(('RARE', 'Kui Gang 魁罡'))
    if gj in PURE_PILLARS:
        out.append(('RARE', 'Pure Pillar 干支一氣'))
    if 'noble' in stars:
        out.append(('LUCKY', 'Nobleman 天乙貴人'))
    if 'blade' in stars and len(out) < 2:
        out.append(('INTENSE', 'The Blade 羊刃'))
    return out[:2]


def sitting_stage(gj):
    start, d = STAGE_START[gj[0]]
    return STAGE_INFO[(B_ORD.index(gj[1]) - B_ORD.index(start)) * d % 12]

NAYIN = [  # (한자, 영문명, 한 줄 의미) — 갑자부터 2주씩 30개
 ('海中金', 'Gold in the Sea', 'treasure hidden in deep water — worth that must be discovered, not displayed'),
 ('爐中火', 'Fire in the Furnace', 'contained, working fire — heat with a purpose'),
 ('大林木', 'Great Forest Wood', 'a whole forest, not one tree — growth that shelters many'),
 ('路傍土', 'Roadside Earth', 'the ground everyone travels on — useful, humble, indispensable'),
 ('劍鋒金', 'Sword-Edge Metal', 'metal honed to its finest point — decisive and exacting'),
 ('山頭火', 'Mountain-Top Fire', 'a beacon seen from afar — influence that carries'),
 ('澗下水', 'Stream in the Ravine', 'water finding its way down rock — quiet persistence'),
 ('城頭土', 'City-Wall Earth', 'earth built into defense — reliability under siege'),
 ('白蠟金', 'White Wax Metal', 'metal still being refined — potential mid-forming'),
 ('楊柳木', 'Willow Wood', 'the tree that bends in every wind and snaps in none'),
 ('泉中水', 'Water of the Spring', 'a self-renewing source — freshness from within'),
 ('屋上土', 'Rooftop Earth', 'earth that shelters — protection as a calling'),
 ('霹靂火', 'Thunderbolt Fire', 'sudden illumination — power in the instant'),
 ('松柏木', 'Pine and Cypress', 'evergreen through winter — constancy as character'),
 ('長流水', 'Long-Flowing River', 'water with distance in it — endurance over speed'),
 ('沙中金', 'Gold in the Sand', 'value mixed with the ordinary — panning required'),
 ('山下火', 'Fire Below the Mountain', 'warmth close to the ground — intimate light'),
 ('平地木', 'Wood of the Plains', 'trees in open land — growth without shelter, and strong for it'),
 ('壁上土', 'Earth on the Wall', 'finished plaster — refinement over a firm base'),
 ('金箔金', 'Gold Foil', 'brilliance spread thin and wide — presentation as art'),
 ('覆燈火', 'Lamp-Light Fire', 'a shaded lamp — glow kept for the room, not the street'),
 ('天河水', 'Water of the Sky River', 'rain from the milky way — blessing that falls on everyone'),
 ('大驛土', 'Earth of the Great Station', 'the crossroads ground — where journeys meet'),
 ('釵釧金', 'Hairpin Gold', 'ornament metal — strength worn as beauty'),
 ('桑柘木', 'Mulberry Wood', 'the tree that feeds silk — quiet usefulness that clothes an empire'),
 ('大溪水', 'Great Stream Water', 'a widening creek — momentum gathering as it goes'),
 ('沙中土', 'Earth in the Sand', 'soft ground that teaches careful footing — adaptability'),
 ('天上火', 'Heavenly Fire', 'the sun and stars themselves — light as a birthright'),
 ('石榴木', 'Pomegranate Wood', 'fruit full of seeds — one talent bearing many'),
 ('大海水', 'Water of the Great Sea', 'the ocean that receives all rivers — capacity without limit'),
]

# 일주별 고유 생김새 — 간지 물상 상호작용 (예: 乙酉 = 칼로 깎은 나무 → 조각한 듯 세련)
APP = {
 '甲子': 'A tall tree standing over deep water: long lines, a cool and reflective gaze — striking from a distance, subtly restless up close.',
 '甲寅': 'Timber at full strength: broad-shouldered bearing, unhurried stride, a face that meets you level and does not look away first.',
 '甲辰': 'A tree in rich loam: substantial, well-planted build; a settled face that suggests reserves — someone who looks like they own land, even when they do not.',
 '甲午': 'Sunlit timber: warm coloring, an easy open smile, expressive brows — the tree in bloom, visibly alive.',
 '甲申': 'Timber hewn by the axe: rugged, angular features, visible bone structure — a face with edges, weathered handsome rather than pretty.',
 '甲戌': 'A lone tree on high ground: lean, upright, a touch austere — the profile of a sentinel, dignified and a little apart.',
 '乙丑': 'An orchid in winter soil: delicate features over surprising sturdiness — a soft face that endures, beauty that reads late.',
 '乙卯': 'Spring grass in spring wind: fresh, youthful looks that age slowly; fluid gestures, a natural charm that seems effortless.',
 '乙巳': 'A vine beside flame: fine features with heat behind the eyes — glamour with a flicker of nervous intensity.',
 '乙未': 'A flower out of dry earth: gentle, rounded features that disguise wiry resilience — prettier than tough, tougher than pretty.',
 '乙酉': 'Wood shaped by the blade: features that look sculpted rather than grown — clean jawline, precise brows, a polished elegance even in casual clothes.',
 '乙亥': 'A water-lily on the current: soft, luminous skin, graceful drifting movements — beauty that seems to float.',
 '丙子': 'The sun mirrored on midnight water: high-gloss presence, bright eyes over unreadable depths — radiant and mysterious at once.',
 '丙寅': 'Sunrise over the forest: a broad brow, upward energy, color that rises easily to the face — morning made visible.',
 '丙辰': 'Sunlight on spring fields: generous, open features; a warm glow that makes others relax and lean in.',
 '丙午': 'High noon embodied: impossible to miss — vivid coloring, big expressions, a voice and smile that fill the room to its corners.',
 '丙申': 'Sunlight glinting off metal: sharp bright eyes, quick expressions, a flashing smile — brilliance with an engineered edge.',
 '丙戌': 'Sunset over the hills: warm but composed features, a banked-fire dignity — handsome in the evening-light way.',
 '丁丑': 'A lantern in the barn: small, steady features; quiet warmth that shows at close range and lasts all night.',
 '丁卯': 'Candlelight among flowers: fine-boned, artistic looks; a gentle flame in the eyes — the most delicate fire.',
 '丁巳': 'A torch feeding itself: compact intensity, a focused gaze that seems lit from within — presence out of proportion to size.',
 '丁未': 'The hearth at home: soft warm features, comfortable to look at — a face people instinctively gather toward.',
 '丁酉': 'Flame on polished gold: precise, refined features with a perfectionist gleam — nothing on this face is accidental.',
 '丁亥': 'A lamp over night water: dreamy, reflective eyes; a softness that seems to see more than it says.',
 '戊子': 'A mountain hiding a spring: solid, stern exterior — and an unexpected softness when the face finally opens.',
 '戊寅': 'A mountain with a tiger inside: still, weighty features that flash suddenly alive — don\'t mistake the calm.',
 '戊辰': 'The mountain range: broad frame, commanding scale, a face built for responsibility — people stand behind it by instinct.',
 '戊午': 'The volcano: an even, composed face with heat detectable underneath — the jaw sets before the voice rises.',
 '戊申': 'A mountain of ore: blocky, practical features, capable hands — someone who looks like they can fix things.',
 '戊戌': 'The fortress: square, guarded features, a gatekeeper\'s steadiness — trust made visible.',
 '己丑': 'The field under snow: plain, patient features that improve with every year of knowing them.',
 '己卯': 'A garden in bloom: soft, approachable prettiness; a nurturing face that children and animals trust on sight.',
 '己巳': 'A sunlit field: warm, intelligent eyes in a kind face — the look of a favorite teacher.',
 '己未': 'The willful summer field: gentle rounded features over a stubborn jaw — sweetness with its heels dug in.',
 '己酉': 'The field after harvest: neat, orderly features, everything in its place — tidiness as a physical trait.',
 '己亥': 'The riverbank field: soft, fertile-looking features with mobile expressions — a face that absorbs and reflects the company it keeps.',
 '庚子': 'A sword in the winter stream: cool, pale sharpness; a wit that shows at the mouth\'s corner before it is spoken.',
 '庚寅': 'The axe in the forest: strong, forward-set features, an athletic charge in the posture — always about to move.',
 '庚辰': 'Ore in the dragon\'s mountain: heavy, unfinished handsomeness — a face that strengthens dramatically with age.',
 '庚午': 'A blade in the fire: taut, tempered features; heat and discipline visible in the same face.',
 '庚申': 'Steel on steel: the most chiseled of the sixty — hard clean lines, direct eyes, zero softness wasted.',
 '庚戌': 'A sword on the altar: stern, upright features with a ceremonial gravity — the look of sworn duty.',
 '辛丑': 'A gem still in the mine: understated features that catch the light unexpectedly — beauty that must be noticed to be seen.',
 '辛卯': 'A needle among flowers: fine, pretty features with one glint of sharpness — disarming until it isn\'t.',
 '辛巳': 'A jewel in the flame: polished glamour with heat behind it — the shine is the discipline showing.',
 '辛未': 'Gold in warm dust: soft matte elegance — refinement that doesn\'t announce itself and lasts longer for it.',
 '辛酉': 'The finished jewel: flawless grooming, symmetrical fine features — the sixty\'s most immaculate face.',
 '辛亥': 'A gem washed in clear water: transparent, clean beauty — skin and eyes that look rinsed in light.',
 '壬子': 'The open ocean: large, fluid presence; restless eyes that are always scanning a horizon somewhere past you.',
 '壬寅': 'A river through the forest: vigorous, flowing movements, a traveler\'s tan and readiness — motion visible at rest.',
 '壬辰': 'The reservoir: a calm, deep-set face holding more than it shows — stillness with pressure behind it.',
 '壬午': 'Water on fire: steam-engine vitality — flushed, energetic, expressive; a face that runs warm and fast.',
 '壬申': 'A spring from the source-rock: clear quick eyes, refreshing presence — the face of someone whose ideas never run dry.',
 '壬戌': 'The sea against the cliff: weathered persistence in the features — patience and force in the same expression.',
 '癸丑': 'Frost on the winter field: pale, fine, quietly enduring features — delicacy that outlasts everyone\'s expectations.',
 '癸卯': 'Dew on spring flowers: fresh, dewy skin, a morning-light gentleness — the most tender face of the water days.',
 '癸巳': 'Rain falling into flame: expressive, changeable features — weather moves visibly across this face.',
 '癸未': 'Rain on dry earth: soft, needed warmth in the eyes — a face people confide in within minutes.',
 '癸酉': 'A spring filtered through rock: immaculate clarity — clean features, steady gaze, an unsettling accuracy of attention.',
 '癸亥': 'The night ocean: deep, dark, unhurried eyes — the sixty\'s most unreadable and most remembered face.',
}

# ── 60 unique syntheses ──────────────────────────────────────────────
SYN = {
 '甲子':"Roots in deep midnight water: this tree is fed by the Scholar's spring, so the mind never stops absorbing. Brilliance comes easily; commitment is the discipline. When 甲子 finally plants itself in one field, the growth is spectacular.",
 '甲寅':"The tree standing in its own forest — Jia at maximum purity. Self-belief is total, leadership unforced, and compromise nearly a foreign language. Life's work: learning that other trees also need light.",
 '甲辰':"A tree rooted in the Dragon's rich vault: resources, talent, and quiet ambition stored underground. 甲辰 builds slowly and owns what it builds. Beware only the pride of never asking for help.",
 '甲午':"Wood feeding a bright flame: this tree burns its own timber to light the room. Expressive, generous, persuasive — output exceeds intake, so rest is not optional; it is fuel policy.",
 '甲申':"A tree growing on iron ground — tested at the root from early on. The Challenger's seat makes 甲申 resilient far beyond appearances; pressure that would fell others becomes structural strength.",
 '甲戌':"The lone tree on a dry highland ridge, guarding what grows in its shade. Principled to a fault, loyal past reason, happiest with a clear duty and a wide view.",
 '乙丑':"An orchid wintering in frozen soil: growth happens invisibly, underground, for years — then blooms late and permanently. 乙丑 endures what showier charts cannot, and its patience is a weapon.",
 '乙卯':"Spring grass in a spring field — Yi at maximum charm. Everyone likes 乙卯 and 乙卯 knows it; the danger is never being forced to grow a trunk. Its flexibility is total, its resilience quietly absurd.",
 '乙巳':"A vine flowering beside flame: artistry and nervous brilliance in one stem. 乙巳 performs, decorates, persuades — and vibrates. It needs beauty in its life the way others need calories.",
 '乙未':"A flower in dry summer earth that should not have survived — and did. Gentle surface, wiry roots, and the longest memory of the twelve gardens. 乙未 forgives slowly and blooms anyway.",
 '乙酉':"The flower on the blade: living on the Challenger's edge gives 乙酉 poise under pressure that reads as glamour. Polish outside, steel inside, and a permanent awareness of the drop below.",
 '乙亥':"A water-lily on a deep current — carried, nourished, never anchored. 乙亥 blooms wherever it lands and lands wherever it's carried; grace travels with it like luggage.",
 '丙子':"The sun over midnight water: maximum public radiance above maximum private depth. 丙子 fascinates because the warmth is real and so is the mystery beneath it.",
 '丙寅':"The rising sun over a spring forest — fire fed by conviction itself. 丙寅 carries the torch first and asks directions later; causes and mornings belong to it.",
 '丙辰':"Sunlight over spring fields: warmth that makes other things grow. 丙辰 is the visionary gardener of the fire signs — generous with light, patient with seasons, rich in harvests it planted for others.",
 '丙午':"The sun at high noon, twice fire: nothing in the sixty burns brighter. Magnetic, absolute, incapable of half-measures — 丙午's only real enemy is its own throttle.",
 '丙申':"The sun over a city of metal: radiance wired to a restless, inventive mind. 丙申 shines and tinkers at once — charisma with an engineering department.",
 '丙戌':"The sunset over guarded hills: dignified fire that shines for a chosen few. 丙戌 trades noon's crowd for evening's loyalty and keeps its warmth for the inner circle.",
 '丁丑':"A lantern in the winter barn: small flame, long night, absolute reliability. 丁丑 warms without spectacle and endures without applause — devotion in its most durable form.",
 '丁卯':"A candle among spring flowers: the gentlest fire in the sixty. 丁卯 is refined, artistic, tender-hearted — a flame that would rather illuminate beauty than consume anything.",
 '丁巳':"The torch that feeds itself — quiet intensity with its own fuel line. 丁巳's imagination builds entire worlds in private and then, occasionally, builds them in public.",
 '丁未':"The hearth at the center of the house: everyone gathers, everyone is warmed, and the fire feels everything that happens in the room. 丁未 creates belonging — and must guard its own fuel.",
 '丁酉':"Flame on polished gold: precision fire. 丁酉 has the perfectionist's glow — taste, timing, and an eye that catches the one wrong note in a symphony.",
 '丁亥':"A lamp over night water: intuition lit from below. 丁亥 sees in the dark — moods, motives, futures — and loves with a romantic's faith in what it sees.",
 '戊子':"The mountain over a hidden spring: stern silhouette, secret generosity. 戊子 provides quietly and hates being thanked loudly; its wealth flows underground.",
 '戊寅':"A mountain with a tiger living inside: stillness wrapped around boldness. 戊寅 moves rarely — but when it moves, it was already decided long ago.",
 '戊辰':"The mountain range itself: vast, layered, built for carrying. Teams, companies, families — 戊辰 shoulders them all and calls it Tuesday. Its vault of talent opens slowly.",
 '戊午':"The volcano: earth with a fire heart. 戊午 is calm the way a crater is calm — genuinely, most of the time. Respect the mountain; remember what's under it.",
 '戊申':"A mountain of ore: practical genius embedded in stone. 戊申 builds systems the way others make conversation — quietly, constantly, and better than asked.",
 '戊戌':"The fortress, twice earth: the most immovable seat in the sixty. 戊戌 guards — people, principles, gates — and its loyalty survives everything except betrayal from inside the walls.",
 '己丑':"The field under snow, twice earth: endurance as identity. 己丑 accumulates slowly — skill, trust, savings — and what it accumulates does not leave. Spring always comes to those who kept the field.",
 '己卯':"A garden in full bloom: soil doing what soil dreams of. 己卯 grows people effortlessly — students, teams, children — and charms while it cultivates.",
 '己巳':"A sunlit field: warm intelligence in fertile ground. 己巳 cultivates minds and moods with equal skill; its power is that everything near it ripens.",
 '己未':"The dry summer field, twice earth: willful soil that decides what grows in it. 己未 is stubborn, spirited, oddly magnetic — the field that argues with the farmer and wins.",
 '己酉':"The field after harvest: refined giving. 己酉 serves with elegance — everything offered is cleaned, sorted, and presented; generosity with excellent manners.",
 '己亥':"The riverbank field: fertile, adaptive, endlessly replenished. Wealth and people flow through 己亥's life in currents — and the soil keeps a share of every flood.",
 '庚子':"The sword in the winter stream: sharp mind, cool delivery. 庚子's wit cuts cleanly and its judgment runs cold and clear; it wins arguments it never raises its voice for.",
 '庚寅':"The axe in the spring forest: action before deliberation. 庚寅 clears paths — fearlessly, occasionally recklessly, always forward. Regret is rare; apologies, rarer.",
 '庚辰':"Ore inside the Dragon's mountain: raw power awaiting its forge. 庚辰 often blooms late — the years of pressure are not delay, they are smelting.",
 '庚午':"The blade in the fire, tempered daily: passion disciplined into edge. 庚午 runs hot and cuts precisely — a warrior's metal that chose its war.",
 '庚申':"Pure steel on pure steel: the most decisive seat in the sixty. 庚申 does not bend, hedge, or wait; born for the arena, it must merely choose worthy arenas.",
 '庚戌':"The sword laid on the altar: metal in service of principle. 庚戌 fights for things — justice, family, code — and its edge is only ever pointed at what deserves it.",
 '辛丑':"A gem still in the mine: undervalued early, priceless later. 辛丑 polishes itself in the dark for years; the world's lateness in noticing is the world's problem.",
 '辛卯':"A needle hidden among flowers: soft setting, sharp point. 辛卯 charms first and corrects after — the most disarming perfectionist of the twelve.",
 '辛巳':"The jewel in the flame: brilliance forged under heat. 辛巳 sparkles publicly and tempers privately; glamour is the visible half of its discipline.",
 '辛未':"Gold resting in warm dust: modest brilliance. 辛未 doesn't need the display case — its shine is discovered, not announced, and lasts accordingly.",
 '辛酉':"The finished jewel, twice metal: flawless standards applied first to itself. 辛酉 is the sixty's purest perfectionist — exacting, composed, and quietly proud of every facet.",
 '辛亥':"A gem washed in deep clear water: clarity as character. 辛亥 combines polish with honesty — the rare jewel that would rather be transparent than flattering.",
 '壬子':"The open ocean, twice water: appetite for the whole world. 壬子's currents never sleep — ideas, ventures, people, places. Its harbor is wherever it hasn't been yet.",
 '壬寅':"The great river through a spring forest: bold water that feeds everything it passes. 壬寅 explores generously — its wake is greener than its origin.",
 '壬辰':"The reservoir: contained immensity. 壬辰 holds more than it shows — the dragon in still water plots the weather, and one day the weather arrives.",
 '壬午':"Water on fire — the steam engine of the sixty. 壬午 converts contradiction into spectacular energy; its reach dazzles and its boiler needs watching.",
 '壬申':"The spring at the very source: self-renewing water. 壬申's cleverness never runs dry because it is fed by the rock itself — a mind with its own aquifer.",
 '壬戌':"The sea against the cliff: ambition given walls to test. 壬戌 keeps coming — patient, tidal, unoffended by resistance. Cliffs erode; the sea does not.",
 '癸丑':"Frost on the winter field: the subtlest endurance. 癸丑 waits, remembers, outlasts — and what it forgives, it forgives on purpose, with the receipts filed.",
 '癸卯':"Dew on spring flowers: nourishment so gentle it's mistaken for decoration. 癸卯's kindness is an instrument — precise, morning-fresh, and quietly strategic.",
 '癸巳':"Rain falling into flame: feeling meets fire. 癸巳 lives at a dramatic boil — volatile, gifted, capable of extinguishing or being vaporized, never of indifference.",
 '癸未':"Rain on dry summer earth: needed everywhere it goes. 癸未's empathy soaks in deep — it waters other people's fields by instinct and must remember its own.",
 '癸酉':"The spring filtered through rock: immaculate intuition. 癸酉's instincts arrive pre-cleaned — precise, clear, and correct often enough to be unsettling.",
 '癸亥':"The night ocean, twice water: the deepest inner world in the sixty. 癸亥 contains multitudes it rarely exhibits; those granted a dive never forget it.",
}

# ── template ─────────────────────────────────────────────────────────
def slug(py): return py.lower().replace(' ', '-')

def ebar(gj):
    s = scores(gj)
    segs = ''.join(
        f'<i class="{ECLS[k]}" style="width:{v:.0f}%" title="{ENAME[k]} {v:.0f}%"></i>'
        for k, v in s.items() if v > 0.5)
    return f'<div class="ebar">{segs}</div>'

CSS = '''
  :root{--ink:#f3ece0;--ink2:#c9bda9;--sub:#9c8f79;--faint:#6e6353;--bg:#100d0a;--card:#1c1712;
    --line:#332a22;--line2:#40342a;--gold:#c9a227;--gold2:#e0c05a;
    --wood:#5aa06a;--fire:#d0604e;--earth:#c9a227;--metal:#a8b0b8;--water:#5a9fd0;
    --serif:'Noto Serif',ui-serif,Georgia,serif;--sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
  *{box-sizing:border-box} html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.7;font-size:16px;
    background-image:radial-gradient(ellipse at 50% -10%,#221a10 0,transparent 55%)}
  a{color:var(--gold2);text-decoration:none}
  .wrap{max-width:780px;margin:0 auto;padding:0 22px}
  nav{position:sticky;top:0;z-index:20;background:#100d0acc;backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
  nav .inner{max-width:1040px;margin:0 auto;padding:0 22px;display:flex;align-items:center;justify-content:space-between;height:60px}
  .logo{font-family:var(--serif);font-size:22px;font-weight:700;display:flex;align-items:center;gap:9px;color:var(--ink)}
  .logo .m{color:var(--gold2)}
  .logo .seal{width:26px;height:26px;border:1px solid var(--gold);color:var(--gold2);border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:14px;font-family:var(--serif)}
  .navlinks{font-size:13px;color:var(--sub)}
  .hero{text-align:center;padding:56px 0 30px}
  .hero>*{position:relative;z-index:1}
  .hero .gj{font-family:var(--serif);font-size:76px;line-height:1;color:var(--ac);text-shadow:0 0 40px color-mix(in srgb,var(--ac) 45%,transparent)}
  .hero h1{font-family:var(--serif);font-size:clamp(28px,5vw,40px);margin:14px 0 6px;font-weight:700}
  .hero .meta{font-size:13px;color:var(--sub);letter-spacing:2px;text-transform:uppercase}
  .hero .meta b{color:var(--ac);font-weight:600}
  .hero .poetic{font-family:var(--serif);font-style:italic;font-size:17px;color:var(--ink2);max-width:540px;margin:20px auto 0}
  .ebarbox{max-width:380px;margin:26px auto 0}
  .ebar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:#0d0b08}
  .ebar i{height:100%}
  .ebar .w{background:var(--wood)}.ebar .f{background:var(--fire)}.ebar .e{background:var(--earth)}.ebar .m{background:var(--metal)}.ebar .a{background:var(--water)}
  .ecap{font-size:11px;color:var(--faint);text-align:center;margin-top:6px}
  section{padding:26px 0 4px}
  .box{border:1px solid var(--line);border-radius:16px;background:var(--card);padding:26px 28px;margin-bottom:18px}
  .box:first-child{border-top:3px solid var(--ac)}
  h2{font-family:var(--serif);font-size:14px;letter-spacing:3px;text-transform:uppercase;color:var(--gold);margin:0 0 12px;font-weight:600}
  .box p{font-size:14.8px;color:var(--ink2);margin:0 0 10px}
  .box p b{color:var(--ink)}
  .sitgod{display:flex;align-items:baseline;gap:10px;margin-bottom:10px;flex-wrap:wrap}
  .sitgod .h{font-family:var(--serif);font-size:22px;color:var(--gold2)}
  .sitgod .n{font-family:var(--serif);font-weight:700;font-size:16px}
  .sitgod .k{font-size:12px;color:var(--sub);letter-spacing:1px;text-transform:uppercase}
  .hidden-tbl{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:4px}
  .hidden-tbl td{padding:7px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)}
  .hidden-tbl td:first-child{font-family:var(--serif);font-size:16px;width:44px;color:var(--ink)}
  .fam{display:flex;gap:8px;flex-wrap:wrap}
  .fam span,.fam a{border:1px solid var(--gold);border-radius:16px;padding:4px 13px;font-size:12.5px;color:var(--gold2);background:#c9a2270d;text-decoration:none}
  .fam a:hover{background:#c9a22726}
  .pn{display:flex;justify-content:space-between;gap:10px;padding:30px 0 8px;font-size:13.5px}
  .pn a{border:1px solid var(--line2);border-radius:20px;padding:7px 16px;color:var(--ink2)}
  .pn a:hover{border-color:var(--gold);color:var(--gold2)}
  .cta{text-align:center;padding:36px 0 60px}
  .cta .btn{background:linear-gradient(180deg,var(--gold2),var(--gold));color:#1a1206;font-weight:700;padding:11px 24px;border-radius:24px;font-size:14px;display:inline-block}
  .cta p{color:var(--sub);font-size:14px;max-width:480px;margin:0 auto 18px}
  footer{border-top:1px solid var(--line);padding:30px 0;text-align:center;color:var(--faint);font-size:12px}
'''



# ── OG 카드 이미지 (1200×630) 생성 — headless Chrome ────────────────
STEM_SCENE = {
 '甲': '''<path d="M0 560 Q300 545 600 552 Q900 559 1200 550 L1200 630 L0 630 Z" fill="#5aa06a" opacity=".12"/>
<g opacity=".30">
<path d="M930 560 C935 480 938 420 941 360 L975 360 C978 420 981 480 986 560 Z" fill="#5aa06a"/>
<ellipse cx="958" cy="300" rx="230" ry="120" fill="#5aa06a" opacity=".7"/>
<ellipse cx="830" cy="360" rx="120" ry="65" fill="#5aa06a" opacity=".55"/>
<ellipse cx="1090" cy="350" rx="120" ry="70" fill="#5aa06a" opacity=".55"/>
<ellipse cx="958" cy="245" rx="140" ry="70" fill="#5aa06a" opacity=".9"/>
</g>''',
 '乙': '''<g stroke="#5aa06a" fill="none" stroke-linecap="round" opacity=".32">
<path d="M850 630 C880 520 820 470 900 400 C980 330 920 280 1000 220 C1060 175 1040 120 1090 80" stroke-width="7"/>
<path d="M900 400 C950 390 990 400 1020 430" stroke-width="5"/>
<path d="M1000 220 C1050 215 1090 230 1110 260" stroke-width="5"/>
<path d="M870 520 C820 510 780 520 750 550" stroke-width="5"/>
</g>
<g fill="#5aa06a" opacity=".38">
<ellipse cx="1035" cy="435" rx="30" ry="13" transform="rotate(28 1035 435)"/>
<ellipse cx="1122" cy="263" rx="30" ry="13" transform="rotate(22 1122 263)"/>
<ellipse cx="737" cy="553" rx="30" ry="13" transform="rotate(-22 737 553)"/>
<ellipse cx="1095" cy="72" rx="34" ry="15" transform="rotate(-35 1095 72)"/>
</g>''',
 '丙': '''<circle cx="960" cy="240" r="200" fill="#d0604e" opacity=".10"/>
<circle cx="960" cy="240" r="140" fill="#d0604e" opacity=".16"/>
<circle cx="960" cy="240" r="90" fill="#d0604e" opacity=".34"/>
<path d="M0 560 Q400 540 800 552 Q1000 558 1200 552 L1200 630 L0 630 Z" fill="#d0604e" opacity=".10"/>
<g stroke="#d0604e" stroke-width="4" opacity=".25" stroke-linecap="round">
<path d="M960 60 L960 20"/><path d="M1105 95 L1130 65"/><path d="M1140 240 L1185 240"/><path d="M815 95 L790 65"/>
</g>''',
 '丁': '''<circle cx="980" cy="330" r="190" fill="#d0604e" opacity=".08"/>
<circle cx="980" cy="330" r="110" fill="#d0604e" opacity=".13"/>
<path d="M980 250 C1015 300 1030 340 1010 385 C997 412 962 412 950 385 C930 340 945 300 980 250 Z" fill="#d0604e" opacity=".45"/>
<path d="M980 300 C997 325 1003 348 993 370 C987 383 972 383 967 370 C958 348 964 325 980 300 Z" fill="#e8a869" opacity=".5"/>
<path d="M940 430 L1020 430 L1012 470 L948 470 Z" fill="#d0604e" opacity=".2"/>''',
 '戊': '''<path d="M540 630 L820 190 L1100 630 Z" fill="#c9a227" opacity=".20"/>
<path d="M780 630 L1000 320 L1200 630 Z" fill="#c9a227" opacity=".14"/>
<path d="M380 630 L560 380 L760 630 Z" fill="#c9a227" opacity=".11"/>
<path d="M790 235 L820 190 L850 235 L820 260 Z" fill="#f3ece0" opacity=".22"/>''',
 '己': '''<g stroke="#c9a227" fill="none" opacity=".22">
<path d="M300 630 Q750 520 1200 545" stroke-width="7"/>
<path d="M420 630 Q800 555 1200 575" stroke-width="6"/>
<path d="M560 630 Q860 585 1200 600" stroke-width="5"/>
<path d="M200 630 Q700 480 1200 512" stroke-width="8"/>
<path d="M80 630 Q650 445 1200 480" stroke-width="9"/>
</g>
<circle cx="1010" cy="330" r="70" fill="#c9a227" opacity=".10"/>''',
 '庚': '''<path d="M760 630 L1130 90 L1160 108 L820 630 Z" fill="#a8b0b8" opacity=".26"/>
<path d="M1130 90 L1160 108 L1150 60 Z" fill="#f3ece0" opacity=".4"/>
<path d="M700 630 L1050 140 L1062 148 L730 630 Z" fill="#a8b0b8" opacity=".12"/>
<g stroke="#f3ece0" stroke-width="3" opacity=".35" stroke-linecap="round">
<path d="M1075 175 L1100 150"/><path d="M950 355 L968 337"/>
</g>''',
 '辛': '''<g opacity=".33">
<path d="M900 210 L1020 210 L1080 300 L960 480 L840 300 Z" fill="#a8b0b8"/>
<path d="M900 210 L960 300 L840 300 Z" fill="#f3ece0" opacity=".5"/>
<path d="M1020 210 L1080 300 L960 300 Z" fill="#8a929c"/>
<path d="M960 300 L960 480 L840 300 Z" fill="#c6ccd2" opacity=".6"/>
</g>
<circle cx="880" cy="180" r="4" fill="#f3ece0" opacity=".8"/>
<path d="M1100 160 l6 14 14 6 -14 6 -6 14 -6 -14 -14 -6 14 -6 Z" fill="#f3ece0" opacity=".55"/>''',
 '壬': '''<g stroke="#5a9fd0" fill="none" stroke-linecap="round" opacity=".30">
<path d="M0 470 Q150 430 300 470 T600 470 T900 470 T1200 470" stroke-width="9"/>
<path d="M0 530 Q150 495 300 530 T600 530 T900 530 T1200 530" stroke-width="7"/>
<path d="M0 585 Q150 555 300 585 T600 585 T900 585 T1200 585" stroke-width="5"/>
<path d="M600 410 Q700 380 800 410 T1000 410" stroke-width="5" opacity=".7"/>
</g>
<circle cx="1010" cy="220" r="60" fill="#5a9fd0" opacity=".10"/>''',
 '癸': '''<g stroke="#5a9fd0" stroke-width="4" stroke-linecap="round" opacity=".28">
<path d="M830 120 L805 210"/><path d="M930 90 L905 180"/><path d="M1030 130 L1005 220"/>
<path d="M1110 70 L1085 160"/><path d="M880 270 L858 350"/><path d="M990 300 L968 380"/><path d="M1100 260 L1078 340"/>
</g>
<g stroke="#5a9fd0" fill="none" opacity=".25">
<ellipse cx="860" cy="480" rx="70" ry="14" stroke-width="4"/>
<ellipse cx="860" cy="480" rx="34" ry="7" stroke-width="3"/>
<ellipse cx="1050" cy="540" rx="55" ry="11" stroke-width="4"/>
</g>''',
}

STEM_SLUG = {'甲': 'jia', '乙': 'yi', '丙': 'bing', '丁': 'ding', '戊': 'wu',
             '己': 'ji', '庚': 'geng', '辛': 'xin', '壬': 'ren', '癸': 'gui'}
BRANCH_SLUG = {'子': 'b-rat', '丑': 'b-ox', '寅': 'b-tiger', '卯': 'b-rabbit',
               '辰': 'b-dragon', '巳': 'b-snake', '午': 'b-horse', '未': 'b-goat',
               '申': 'b-monkey', '酉': 'b-rooster', '戌': 'b-dog', '亥': 'b-pig'}


def scene_boost(svg, factor=1.9, cap=0.92):
    """씬 SVG의 opacity 계열 값 일괄 증폭."""
    def f(m):
        v = min(float(m.group(2)) * factor, cap)
        return f'{m.group(1)}"{v:.2f}"'
    return re.sub(r'(opacity=)"(\.?[0-9.]+)"', f, svg)


OG_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
  body{{margin:0;width:1200px;height:630px;background:#100d0a;
    background-image:radial-gradient(ellipse at 30% -20%,#221a10 0,transparent 60%),radial-gradient(circle at 90% 110%,#1a2028 0,transparent 45%);
    font-family:-apple-system,'Segoe UI',sans-serif;color:#f3ece0;display:flex;align-items:center;justify-content:center}}
  .card{{position:relative;overflow:hidden;width:1080px;height:510px;border:2px solid {ac};border-radius:26px;background:linear-gradient(160deg,#1d1913,#14100c);
    display:flex;align-items:center;padding:0 70px;gap:64px;box-shadow:0 0 90px -30px {ac}}}
  .gj{{font-family:'Noto Serif',Georgia,serif;font-size:190px;line-height:1;color:{ac};text-shadow:0 0 70px {ac}66;white-space:nowrap}}
  .t .py{{font-family:'Noto Serif',Georgia,serif;font-size:54px;font-weight:700;margin-bottom:6px}}
  .t .an{{font-size:22px;letter-spacing:5px;text-transform:uppercase;color:#9c8f79;margin-bottom:26px}}
  .t .d{{font-family:'Noto Serif',Georgia,serif;font-style:italic;font-size:30px;line-height:1.5;color:#c9bda9;max-width:640px}}
  .badge{{display:inline-block;border:1.5px solid #c9a227;color:#e0c05a;border-radius:18px;padding:5px 18px;font-size:19px;letter-spacing:3px;margin-top:24px}}
  .brand{{position:absolute;bottom:36px;right:70px;font-family:'Noto Serif',Georgia,serif;font-size:26px;color:#c9a227;letter-spacing:2px}}
  .seal{{position:absolute;bottom:30px;left:70px;width:44px;height:44px;border:1.5px solid #c9a227;color:#e0c05a;border-radius:9px;
    display:flex;align-items:center;justify-content:center;font-size:24px;font-family:'Noto Serif',serif}}
</style></head><body>
<div class="card">
<div style="position:absolute;inset:0;border-radius:24px;background-image:url('{art}');background-size:cover;background-position:left center"></div>
<div style="position:absolute;left:230px;top:10px;width:570px;height:610px;background-image:url('{branch_art}');background-size:cover;background-position:center;mix-blend-mode:screen;opacity:.95;-webkit-mask-image:radial-gradient(ellipse 60% 62% at center,black 45%,transparent 74%)"></div>
<div style="position:absolute;inset:0;border-radius:24px;background:linear-gradient(90deg,#14100c22 0%,transparent 22%,transparent 38%,#14100cbb 58%,#14100cd9 100%)"></div>
<div class="gj" style="position:relative">{gj}</div>
  <div class="t" style="position:relative"><div class="py">The {py} Day</div><div class="an">One of the sixty · Day of the {an}</div>
  <div class="d">&ldquo;{d}&rdquo;</div>{badge}</div></div>
<div class="seal">乙</div><div class="brand">elun.me</div>
</body></html>"""

EL_HEX = {'wood': '#5aa06a', 'fire': '#d0604e', 'earth': '#c9a227', 'metal': '#a8b0b8', 'water': '#5a9fd0'}
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def build_og(data):
    import subprocess, tempfile
    ogdir = os.path.join(OUT, 'og')
    os.makedirs(ogdir, exist_ok=True)
    for p in data:
        gj = p['gj']
        bds = badges(gj)
        badge = f'<div class="badge">◆ {bds[0][0]} · {bds[0][1]}</div>' if bds else ''
        art = os.path.abspath(os.path.join(os.path.dirname(OUT), 'art', 'src', STEM_SLUG[gj[0]] + '.jpg'))
        html = OG_TEMPLATE.format(ac=EL_HEX[SEL[gj[0]]], gj=gj, py=p['py'],
                                  an=BR[gj[1]]['an'], d=p['d'], badge=badge,
                                  art='file://' + art,
                                  branch_art='file://' + os.path.abspath(os.path.join(os.path.dirname(OUT), 'art', 'src', BRANCH_SLUG[gj[1]] + '.jpg')))
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html); tmp = f.name
        out_png = os.path.join(ogdir, slug(p['py']) + '.png')
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars',
                        f'--screenshot={out_png}', '--window-size=1200,630', f'file://{tmp}'],
                       capture_output=True)
        os.unlink(tmp)
        from PIL import Image as _Img
        out_jpg = out_png[:-4] + '.jpg'
        _Img.open(out_png).convert('RGB').save(out_jpg, quality=84, optimize=True)
        os.unlink(out_png)
    print(f'og: {len(data)} images -> {ogdir}')


def page(p, prev_p, next_p, all_pillars):
    gj, py, br = p['gj'], p['py'], p['gj'][1]
    dm, b = DM[gj[0]], BR[br]
    import urllib.parse as _up
    q_url = _up.quote(f'https://elun.me/pillars/{slug(py)}.html', safe='')
    q_txt = _up.quote(f'{gj} — The {py} Day: "{p["d"]}"', safe='')
    gi = gz_index(gj)
    ny_hj, ny_en, ny_gloss = NAYIN[gi // 2]
    void1, void2 = VOID_PAIRS[gi // 10]
    st_hj, st_en, st_gloss = sitting_stage(gj)
    art_slug = STEM_SLUG[gj[0]]
    branch_slug = BRANCH_SLUG[gj[1]]
    bds = badges(gj)
    badge_html = ''.join(
        f'<span style="display:inline-block;border:1px solid var(--gold);color:var(--gold2);border-radius:14px;padding:3px 12px;font-size:11px;letter-spacing:2px;margin:0 4px">◆ {label} · {name}</span>'
        for label, name in bds)
    if badge_html:
        badge_html = f'<div style="margin-top:14px">{badge_html}</div>'
    nt_hj, nt_en, nt_gloss = NATURE_INFO[BRANCH_NATURE[gj[1]]]
    star_rows = ''.join(
        f'<tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub)">Star 神煞</td>'
        f'<td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)">'
        f'<b style="color:var(--gold2)">{STAR_INFO[k][1]}</b> ({STAR_INFO[k][0]}) — {STAR_INFO[k][2]}</td></tr>'
        for k in DAY_STARS.get(gj, []))
    siblings = ''.join(
        f'<a href="{slug(q["py"])}.html" style="border:1px solid var(--line2);border-radius:16px;padding:4px 13px;font-size:12.5px;color:var(--ink2);text-decoration:none">{q["gj"]} {q["py"]}</a>'
        for q in all_pillars if q['gj'][0] == gj[0] and q['gj'] != gj)
    main_god = GODS[god(gj[0], HID[br][0][0])]
    ac = f"var(--{SEL[gj[0]]})"
    hid_rows = ''.join(
        f'<tr><td>{h}</td><td>{ENAME[SEL[h]]} · {GODS[god(gj[0],h)]["nm"]} {GODS[god(gj[0],h)]["han"]}'
        f'</td><td style="text-align:right;color:var(--faint)">{w*100:.0f}%</td></tr>'
        for h, w in HID[br])
    nslug = lambda n: re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
    celebs = (f'<div class="box"><h2>Famous {gj} Charts</h2><div class="fam">'
              + ''.join(f'<a href="../famous/{nslug(c)}.html">{c}</a>' for c in p['celebs'])
              + '</div><p style="font-size:12px;color:var(--faint);margin-top:10px">Day pillars computed with Elun\'s engine from public birth records — click a name for the chart.</p></div>') if p['celebs'] else ''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{py} {gj} Day Pillar — Personality, Love & Career | Elun</title>
<meta property="og:type" content="article"/>
<meta property="og:title" content="{py} {gj} — one of the sixty day pillars"/>
<meta property="og:description" content="{p['d']}"/>
<meta property="og:image" content="https://elun.me/pillars/og/{slug(py)}.jpg"/>
<meta property="og:url" content="https://elun.me/pillars/{slug(py)}.html"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:image" content="https://elun.me/pillars/og/{slug(py)}.jpg"/>
<link rel="canonical" href="https://elun.me/pillars/{slug(py)}.html"/>
<meta name="description" content="{py} ({gj}) day pillar explained: {p['d']} Personality, appearance, love and career of the {py} day in BaZi."/>
<style>{CSS}</style>
</head>
<body style="--ac:{ac}">
<nav><div class="inner">
  <a href="../index.html" class="logo"><span class="seal">乙</span><span class="m">Elun</span></a>
  <span class="navlinks"><a href="../daymasters.html">Day Masters</a> · <a href="../daymasters.html#sixty">All 60</a> · <a href="../start.html">Create your chart</a></span>
</div></nav>

<div class="hero wrap" style="position:relative;overflow:hidden">
  <div style="position:absolute;inset:0;background-image:url('art/{art_slug}.jpg');background-size:cover;background-position:left center;opacity:.7;pointer-events:none"></div>
  <div style="position:absolute;right:-6%;top:0;width:46%;height:100%;background-image:url('art/{branch_slug}.jpg');background-size:cover;background-position:center;mix-blend-mode:screen;opacity:.75;pointer-events:none;-webkit-mask-image:radial-gradient(ellipse 62% 70% at center,black 40%,transparent 75%)"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 75% 80% at 50% 45%,#100d0aee 0%,#100d0ab8 55%,#100d0a44 100%);pointer-events:none"></div>
  <div class="gj" style="position:relative">{gj}</div>
  <h1>The {py} Day</h1>
  <div class="meta"><b>{dm['nm']} · {dm['en']}</b> sitting on the <b>{b['an']}</b> · {b['img']}</div>
  <p class="poetic">“{p['d']}”</p>
  {badge_html}
  <div class="ebarbox">{ebar(gj)}
    <div class="ecap">Five-element composition — day stem 50% · hidden stems 50%</div></div>
  <div style="margin-top:18px;font-size:12.5px;color:var(--faint);position:relative">
    Share this pillar:
    <a target="_blank" rel="noopener" style="margin:0 5px" href="https://x.com/intent/post?text={q_txt}&url={q_url}">𝕏</a>·
    <a target="_blank" rel="noopener" style="margin:0 5px" href="https://www.facebook.com/sharer/sharer.php?u={q_url}">Facebook</a>·
    <a target="_blank" rel="noopener" style="margin:0 5px" href="https://wa.me/?text={q_txt}%20{q_url}">WhatsApp</a>
  </div>
</div>

<div class="wrap">
<section>
  <div class="box">
    <h2>The Essence of {gj}</h2>
    <p>{SYN[gj]}</p>
    <p><b>The stem:</b> {dm['core']}</p>
  </div>

  <div class="box">
    <h2>What You Sit On</h2>
    <div class="sitgod"><span class="h">{main_god['han']}</span><span class="n">{main_god['nm']}</span><span class="k">{main_god['key']}</span></div>
    <p>{main_god['sit']}</p>
    <table class="hidden-tbl">{hid_rows}</table>
    <p style="font-size:12px;color:var(--faint);margin-top:8px">Hidden stems of {br} and their relationship to your {gj[0]} Day Master.</p>
  </div>

  <div class="box">
    <h2>Appearance &amp; Presence</h2>
    <p><b>{APP.get(gj,'')}</b></p>
    <p>The {dm['nm']} base — {dm['app']} — shaded by the {b['an']}: {b['app']}. Traditional physiognomy; enjoy as folklore, not science.</p>
    <p><b>Temperament note:</b> {b['tem']}.</p>
  </div>

  <div class="box">
    <h2>In Love</h2>
    <p>{main_god['love']}</p>
  </div>

  <div class="box">
    <h2>Work &amp; Direction</h2>
    <p>{main_god['work']}</p>
  </div>

  {celebs}

  <div class="box">
    <h2>Classical Markers</h2>
    <table class="kv" style="font-size:13.5px;width:100%;border-collapse:collapse">
      <tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub);width:36%">Nayin 納音</td>
          <td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)"><b style="color:var(--ink)">{ny_en}</b> ({ny_hj}) — {ny_gloss}</td></tr>
      <tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub)">Sitting stage 十二運星</td>
          <td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)"><b style="color:var(--ink)">{st_en}</b> ({st_hj}) — {st_gloss}</td></tr>
      <tr><td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--sub)">Branch nature</td>
          <td style="padding:8px 4px;border-bottom:1px dashed var(--line);color:var(--ink2)"><b style="color:var(--ink)">{nt_en}</b> ({nt_hj}) — {nt_gloss}</td></tr>
      {star_rows}
      <tr><td style="padding:8px 4px;color:var(--sub)">Void branches 空亡</td>
          <td style="padding:8px 4px;color:var(--ink2)"><b style="color:var(--ink)">{void1} · {void2}</b> — areas of life this pillar holds lightly; classical astrologers read them as themes to approach without grasping</td></tr>
    </table>
    <p style="font-size:11px;color:var(--faint);margin-top:8px">Twelve-stage cycle follows the classical tradition (yin stems run the cycle in reverse).</p>
  </div>

  <div class="box">
    <h2>The Other {dm['nm']} Days</h2>
    <div class="fam">{siblings}</div>
  </div>
</section>

<div class="pn">
  <a href="{slug(prev_p['py'])}.html">← {prev_p['gj']} {prev_p['py']}</a>
  <a href="../daymasters.html#{dm['id']}">{dm['nm']} profile</a>
  <a href="{slug(next_p['py'])}.html">{next_p['gj']} {next_p['py']} →</a>
</div>

<div class="cta">
  <p>Is {gj} really your day pillar? Near midnight or a solar-term boundary, only precision decides.</p>
  <a class="btn" href="../start.html">Calculate my chart — free</a>
</div>
</div>

<footer>© 2026 Elun · <a href="../index.html">Home</a> · <a href="../daymasters.html">The Ten Day Masters</a> · interpretive reading for reflection &amp; entertainment</footer>
</body></html>'''

def main():
    data = json.load(open(ENGINE, encoding='utf-8'))['pillars']
    assert len(data) == 60
    os.makedirs(OUT, exist_ok=True)
    for i, p in enumerate(data):
        prev_p, next_p = data[(i-1) % 60], data[(i+1) % 60]
        html = page(p, prev_p, next_p, data)
        open(os.path.join(OUT, slug(p['py'])+'.html'), 'w', encoding='utf-8').write(html)
    # index
    items = ''.join(
        f'<a class="it" style="--ac:var(--{SEL[p["gj"][0]]})" href="{slug(p["py"])}.html">'
        f'<span class="g">{p["gj"]}</span><span>{p["py"]}<br><small>{BR[p["gj"][1]]["an"]}</small></span></a>'
        for p in data)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>The Sixty Day Pillars — Index | Elun</title>
<link rel="canonical" href="https://elun.me/pillars/"/>
<meta name="description" content="All sixty BaZi day pillars — personality, love, career and appearance for each 干支 combination."/>
<style>{CSS}
.gridx{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;padding:30px 0 60px}}
.it{{display:flex;gap:10px;align-items:center;border:1px solid var(--line);border-radius:12px;background:var(--card);padding:12px 14px;color:var(--ink2);font-size:13px}}
.it:hover{{border-color:var(--gold)}}
.it .g{{font-family:var(--serif);font-size:22px;color:var(--ac)}}
.it small{{color:var(--faint)}}</style></head><body>
<nav><div class="inner">
  <a href="../index.html" class="logo"><span class="seal">乙</span><span class="m">Elun</span></a>
  <span class="navlinks"><a href="../daymasters.html">Day Masters</a> · <a href="../start.html">Create your chart</a></span>
</div></nav>
<div class="hero wrap"><h1 style="font-family:var(--serif)">The Sixty Day Pillars</h1>
<p style="color:var(--ink2)">Every stem-branch combination, each its own personality signature.</p></div>
<div class="wrap"><div class="gridx">{items}</div></div>
<footer>© 2026 Elun · <a href="../daymasters.html">The Ten Day Masters</a></footer>
</body></html>''')
    print(f'wrote 60 pages + index → {OUT}')
    import sys
    if '--og' in sys.argv:
        build_og(data)

if __name__ == '__main__':
    main()
