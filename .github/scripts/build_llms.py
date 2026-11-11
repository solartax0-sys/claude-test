"""llms.txt(AI 검색 안내)와 feed.xml(RSS) 생성.
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
"## 안산 지역 세금 가이드", "",
"안산시 단원구는 안산세무서, 상록구는 동안산세무서 관할이며 두 세무서 모두 중부지방국세청 소속이에요(국세청 관할구역 안내 기준).", "",
f"- [안산 상속세 신고 가이드]({SITE}/guide/ansan-inheritance-tax.html): 돌아가신 분 주소지 기준 관할세무서(단원구 안산세무서·상록구 동안산세무서), 신고기한 6개월, 공제, 준비서류",
f"- [안산 증여세 신고 가이드]({SITE}/guide/ansan-gift-tax.html): 받은 사람 주소지 기준 관할세무서, 신고기한 3개월, 가족별 증여공제 한도, 준비서류",
f"- [안산 양도소득세 신고 가이드]({SITE}/guide/ansan-capital-gains-tax.html): 판 사람 주소지 기준 관할세무서, 예정신고 2개월, 1세대 1주택 비과세와 안산 조정대상지역 이력",
f"- [안산 사업자 세무 가이드]({SITE}/guide/ansan-business-tax.html): 사업장 기준 관할세무서, 사업자등록 20일, 부가세·종합소득세·법인세·원천세 신고기한, 창업 첫해 체크리스트", "",
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

# ---- RSS(feed.xml): 네이버 서치어드바이저·빙에 새 칼럼을 빨리 알리기 위한 피드 ----
from email.utils import format_datetime
from datetime import datetime, timezone, timedelta
KST = timezone(timedelta(hours=9))
def meta(path):
    s = open(f'{ROOT}{path}', encoding='utf-8').read()
    d = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', s)
    return (d.group(1) if d else '2026-11-10'), desc(path)
rows = []
for href, cat, title in items:
    if not os.path.exists(f'{ROOT}{href}'): continue
    day, d = meta(href)
    rows.append((day, html.unescape(title), SITE + href, d, html.unescape(cat)))
rows.sort(key=lambda r: r[0], reverse=True)  # 같은 날짜는 목록 순서 유지
x = lambda t: html.escape(t, quote=False)
feed = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
        '<title>솔라세무회계 세무 칼럼 (안산 세무사 설나현)</title>', f'<link>{SITE}/columns/</link>',
        f'<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>',
        '<description>상속·증여·양도·기장·법인 세금 칼럼</description>', '<language>ko</language>']
for day, t, u, d, cat in rows:
    dt = format_datetime(datetime.strptime(day, '%Y-%m-%d').replace(hour=9, tzinfo=KST))
    feed.append(f'<item><title>{x(t)}</title><link>{u}</link><guid>{u}</guid><category>{x(cat)}</category>'
                f'<pubDate>{dt}</pubDate><description>{x(d)}</description></item>')
feed.append('</channel></rss>')
open(f'{ROOT}/feed.xml', 'w', encoding='utf-8').write('\n'.join(feed) + '\n')
print('feed.xml 생성:', len(rows), '개')
