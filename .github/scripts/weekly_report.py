"""solartax.kr 주간 홈페이지 보고서
- 구글 애널리틱스(GA4): 방문자, 유입 경로, 상담 신청·전화·카톡·예약 클릭
- 구글 서치 콘솔: 검색어, '안산세무사' 순위
결과를 solartax@solartax.kr 로 메일 발송 (FormSubmit 경유)

필요한 비밀값(깃허브 Secrets): GA_SA_KEY = 서비스 계정 JSON 키 전체
"""
import datetime as dt
import json
import os
import sys
import urllib.request

from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter,
)
from googleapiclient.discovery import build

GA_PROPERTY = 'properties/563521555'
SC_SITE = 'sc-domain:solartax.kr'
MAIL_TO = 'https://formsubmit.co/ajax/solartax@solartax.kr'
KST = dt.timezone(dt.timedelta(hours=9))

EVENTS = [
    ('consult_submit', '상담 신청'),
    ('phone_click', '전화 버튼'),
    ('kakao_click', '카톡 상담'),
    ('booking_click', '네이버 예약'),
    ('channel_click', '블로그·유튜브·인스타'),
]
CHANNEL_KO = {
    'Organic Search': '검색(구글·네이버)', 'Direct': '직접 방문', 'Referral': '다른 사이트 링크',
    'Organic Social': 'SNS', 'Paid Search': '검색 광고', 'Unassigned': '분류 안 됨',
    'Organic Video': '유튜브', 'Email': '메일',
}

key = json.loads(os.environ['GA_SA_KEY'])
creds = service_account.Credentials.from_service_account_info(
    key, scopes=['https://www.googleapis.com/auth/analytics.readonly',
                 'https://www.googleapis.com/auth/webmasters.readonly'])
ga = BetaAnalyticsDataClient(credentials=creds)
sc = build('searchconsole', 'v1', credentials=creds, cache_discovery=False)

today = dt.datetime.now(KST).date()
end = today - dt.timedelta(days=1)          # 어제까지
start = end - dt.timedelta(days=6)          # 최근 7일
pend = start - dt.timedelta(days=1)
pstart = pend - dt.timedelta(days=6)        # 그 전 7일
d = lambda x: x.isoformat()


def ga_report(dims, mets, s, e, flt=None, limit=10):
    req = RunReportRequest(property=GA_PROPERTY, dimensions=[Dimension(name=x) for x in dims],
                           metrics=[Metric(name=x) for x in mets],
                           date_ranges=[DateRange(start_date=d(s), end_date=d(e))], limit=limit)
    if flt:
        req.dimension_filter = flt
    rows = ga.run_report(req).rows
    return [([v.value for v in r.dimension_values], [float(m.value) for m in r.metric_values]) for r in rows]


def total(mets, s, e):
    r = ga_report([], mets, s, e)
    return r[0][1] if r else [0.0] * len(mets)


def events(s, e):
    names = [n for n, _ in EVENTS]
    flt = FilterExpression(filter=Filter(field_name='eventName',
                                         in_list_filter=Filter.InListFilter(values=names)))
    got = {r[0][0]: int(r[1][0]) for r in ga_report(['eventName'], ['eventCount'], s, e, flt, 20)}
    return {n: got.get(n, 0) for n in names}


def diff(now, before):
    n = now - before
    return f'(지난주보다 +{n:,.0f})' if n > 0 else (f'(지난주보다 {n:,.0f})' if n < 0 else '(지난주와 같음)')


lines = []
users, sessions = total(['activeUsers', 'sessions'], start, end)
pusers, psessions = total(['activeUsers', 'sessions'], pstart, pend)
ev, pev = events(start, end), events(pstart, pend)

lines.append(f'■ 기간: {start:%m/%d} ~ {end:%m/%d} (최근 7일)')
lines.append('')
lines.append('[핵심]')
lines.append(f'· 방문자 {users:,.0f}명 {diff(users, pusers)}')
lines.append(f'· 상담 신청 {ev["consult_submit"]}건 {diff(ev["consult_submit"], pev["consult_submit"])}')
lines.append(f'· 전화 버튼 {ev["phone_click"]}회 · 카톡 {ev["kakao_click"]}회 · 네이버 예약 {ev["booking_click"]}회')
lines.append('')

lines.append('[어디서 왔나]')
for (ch,), (u,) in ga_report(['sessionDefaultChannelGroup'], ['activeUsers'], start, end, limit=8):
    lines.append(f'· {CHANNEL_KO.get(ch, ch)}: {u:,.0f}명')
srcs = ga_report(['sessionSource'], ['activeUsers'], start, end, limit=6)
if srcs:
    lines.append('  (세부: ' + ', '.join(f'{s} {u:,.0f}' for (s,), (u,) in srcs) + ')')
lines.append('')

lines.append('[많이 본 페이지]')
for (path, title), (v,) in ga_report(['pagePath', 'pageTitle'], ['screenPageViews'], start, end, limit=5):
    lines.append(f'· {path}  {v:,.0f}회')
lines.append('')

# 서치 콘솔은 2~3일 늦게 집계되므로 3일 전까지
send = today - dt.timedelta(days=3)
sstart = send - dt.timedelta(days=6)
lines.append(f'[구글 검색어] {sstart:%m/%d} ~ {send:%m/%d}')
try:
    q = sc.searchanalytics().query(siteUrl=SC_SITE, body={
        'startDate': d(sstart), 'endDate': d(send), 'dimensions': ['query'], 'rowLimit': 10,
        'orderBy': [{'fieldName': 'impressions', 'sortOrder': 'DESCENDING'}]}).execute().get('rows', [])
    if not q:
        lines.append('· 아직 집계된 검색어가 없어요')
    for r in q:
        lines.append(f'· {r["keys"][0]} — 노출 {r["impressions"]:.0f} · 클릭 {r["clicks"]:.0f} · 평균 {r["position"]:.1f}위')
    k = sc.searchanalytics().query(siteUrl=SC_SITE, body={
        'startDate': d(sstart), 'endDate': d(send), 'dimensions': ['query'],
        'dimensionFilterGroups': [{'filters': [{'dimension': 'query', 'operator': 'contains', 'expression': '안산'}]}],
        'rowLimit': 5}).execute().get('rows', [])
    lines.append('')
    lines.append('[‘안산’ 들어간 검색어 순위]')
    if not k:
        lines.append('· 이번 주 집계 없음')
    for r in k:
        lines.append(f'· {r["keys"][0]}: 평균 {r["position"]:.1f}위 (클릭 {r["clicks"]:.0f})')
except Exception as e:  # 서치 콘솔 권한이 없을 때도 나머지는 보냄
    lines.append(f'· 서치 콘솔을 읽지 못했어요: {type(e).__name__}')
lines.append('')
lines.append('※ 네이버 검색어는 네이버 애널리틱스 → 유입분석 → 검색어에서 확인하세요.')

body = '\n'.join(lines)
print(body)

if os.environ.get('DRY_RUN') == '1':
    sys.exit(0)

payload = json.dumps({
    '_subject': f'[솔라택스] 홈페이지 주간 보고 ({start:%m/%d}~{end:%m/%d}) · 방문 {users:,.0f}명 · 신청 {ev["consult_submit"]}건',
    '_template': 'box', '_captcha': 'false',
    '주간 보고': body,
}).encode()
req = urllib.request.Request(MAIL_TO, data=payload, method='POST', headers={
    'Content-Type': 'application/json', 'Accept': 'application/json',
    'Origin': 'https://solartax.kr', 'Referer': 'https://solartax.kr/'})
res = json.loads(urllib.request.urlopen(req, timeout=30).read() or b'{}')
print('메일 발송 결과:', res)
if str(res.get('success')) == 'false':
    sys.exit('메일 발송 실패')
