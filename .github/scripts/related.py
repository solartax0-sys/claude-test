"""칼럼 하단 '함께 보면 좋은 칼럼' 3개를 주제가 가까운 글로 다시 고른다.
- 같은 태그(상속·양도·법인 …)가 겹칠수록 위로, 비슷한 주제(주택↔양도 등)는 그다음.
- 점수가 같으면 최신 글 우선.
- 새 칼럼을 올린 뒤 매번 돌린다(옛 글의 추천에도 새 글이 반영됨). 여러 번 돌려도 안전.
사용: python3 .github/scripts/related.py  (저장소 루트에서)"""
import re, os, glob, html

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
N = 3

# 태그끼리 '가까운 주제'로 보는 관계 (한쪽만 적어도 양쪽으로 적용)
NEAR = {
    '주택': ['양도', '가족법인', '임대소득'],
    '가족법인': ['증여', '법인', '비상장주식'],
    '비상장주식': ['법인', '상속'],
    '세무조사': ['상속', '증여'],
    '임대소득': ['종소세'],
    '창업': ['부가세', '인건비', '종소세'],
    '기업진단': ['법인'],
    '법인': ['인건비'],
}
near = {}
for a, bs in NEAR.items():
    for b in bs:
        near.setdefault(a, set()).add(b)
        near.setdefault(b, set()).add(a)

cols = {}
for f in sorted(glob.glob(f'{ROOT}/columns/*.html')):
    slug = os.path.basename(f)[:-5]
    if slug == 'index':
        continue
    s = open(f, encoding='utf-8').read()
    tag = re.search(r'<span class="tag">([^<]*)</span>', s)
    title = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
    day = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', s)
    if not (tag and title):
        print('건너뜀(태그/제목 없음):', slug)
        continue
    cat = html.unescape(tag.group(1)).strip()
    cols[slug] = dict(cat=cat, tags=set(cat.split('·')), title=html.unescape(re.sub('<[^>]+>', '', title.group(1)).strip()),
                      day=day.group(1) if day else '0000-00-00', path=f, src=s)

def score(a, b):
    ta, tb = cols[a]['tags'], cols[b]['tags']
    sc = 0
    for t in ta & tb:
        sc += 1 if t == '기장' else 3          # '기장'은 넓은 묶음이라 가볍게
    for t in ta:
        sc += len(near.get(t, set()) & tb)       # 가까운 주제
    return sc

e = lambda t: html.escape(t, quote=False)
changed = 0
for slug, c in cols.items():
    others = [o for o in cols if o != slug]
    others.sort(key=lambda o: cols[o]['day'], reverse=True)   # 점수 같으면 최신 글
    others.sort(key=lambda o: -score(slug, o))
    pick = others[:N]
    block = ('<!--RELATED--><div class="more"><h3>함께 보면 좋은 칼럼</h3><div class="list">' +
             ''.join(f'<a href="/columns/{o}.html"><span>{e(cols[o]["cat"])}</span><strong>{e(cols[o]["title"])}</strong></a>' for o in pick) +
             '</div></div><!--/RELATED-->')
    s = c['src']
    if '<!--RELATED-->' in s:
        new = re.sub(r'<!--RELATED-->.*?<!--/RELATED-->', lambda m: block, s, flags=re.S)
    else:
        new, n = re.subn(r'<div class="more"><h3>함께 보면 좋은 칼럼</h3>.*?</div></div>', lambda m: block, s, count=1, flags=re.S)
        if n == 0:
            new = s.replace('</main>', block + '\n</main>', 1)
    if new != s:
        open(c['path'], 'w', encoding='utf-8').write(new)
        changed += 1
print(f'추천 칼럼 갱신: {changed}/{len(cols)}개 페이지')
