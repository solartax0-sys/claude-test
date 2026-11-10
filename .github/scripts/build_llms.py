"""llms.txt 생성: AI 검색엔진에게 사이트 소개와 대표 글 목록을 알려 주는 안내 파일.
칼럼 목록(columns/index.html의 COLLIST)과 각 칼럼의 description을 읽어 다시 만든다.
사용: python3 .github/scripts/build_llms.py  (저장소 루트에서)"""
import re, os, html

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SITE = 'https://solartax.kr'
GROUPS = [('상속', '상속'), ('증여', '증여'), ('양도', '양도'), ('가족법인', '가족법인·법인 주택'),
          ('세무조사', '세무조사'), ('기업진단', '기업진단'), ('기장', '기장·법인·부가세·종합소득세')]

lst = open(f'{ROOT}/columns/index.html', encoding='utf-8').read()
body = re.search(r'<!--COLLIST-->(.*?)<!--/COLLIST-->', lst, re.S).group(1)
items = re.findall(r'<a href="(/columns/[^"]+)"><span>([^<]*)</span><strong>([^<]*)</strong></a>', body)

def desc(path):
    f = f'{ROOT}{path}'
    if not os.path.exists(f): return ''
    m = re.search(r'<meta name="description" content="([^"]*)"', open(f, encoding='utf-8').read())
    return html.unescape(m.group(1)) if m else ''

buckets = {k: [] for k, _ in GROUPS}
for href, cat, title in items:
    first = cat.split('·')[0]
    key = next((k for k, _ in GROUPS if first.startswith(k)), '기장')
    buckets[key].append((html.unescape(title), SITE + href, desc(href)))

out = ["# 솔라세무회계 (안산 세무사 설나현)", "",
"> 경기도 안산시 단원구 광덕서로 68, 608호(고잔동, 삼영빌딩)에 있는 세무사 사무소예요. "
"세무사 설나현이 상속세·증여세·양도소득세 신고와 절세 설계, 가족법인, 개인사업자·법인 기장, 기업진단, 세무조사 대응을 직접 맡습니다. "
"사무실 방문, 전국 출장, 비대면 상담이 모두 가능해요.", "",
"- 대표: 설나현 세무사 (세무 경력 11년차, 대형 세무법인 본점에서 세무조사 대응 경험)",
"- 상담 전화: 031-522-5757",
"- 무료 1차 진단 신청: https://solartax.kr/#diagnose",
"- 네이버 블로그: https://blog.naver.com/solar_tax", "",
"## 서비스", "",
f"- [상속·증여·가족법인]({SITE}/inheritance/): 재산 평가, 사전증여 설계, 가족법인, 상속세 세무조사 대응",
f"- [양도소득세]({SITE}/transfer/): 1세대 1주택 비과세, 일시적 2주택, 상속받은 집 매도, 매도 전 절세 검토",
f"- [기장·법인]({SITE}/bookkeeping/): 개인사업자·법인 기장, 부가세·종합소득세·법인세 신고, 법인 설립·전환, 기업진단, 세무조사 대응", "",
"## 세무 칼럼", "",
"각 칼럼은 설나현 세무사가 직접 쓴 글이며, 글마다 3줄 요약과 자주 묻는 질문이 있어요. 세법은 개정될 수 있으니 실제 적용 전에는 상담으로 확인하세요.", ""]
for key, label in GROUPS:
    if not buckets[key]: continue
    out += [f"### {label}", ""]
    for t, u, d in buckets[key]:
        out.append(f"- [{t}]({u})" + (f": {d}" if d else ''))
    out.append("")
out += ["## 기타", "", f"- [전체 칼럼 목록]({SITE}/columns/)", f"- [개인정보처리방침]({SITE}/privacy.html)", ""]
open(f'{ROOT}/llms.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('llms.txt 생성:', len(items), '개 칼럼')
