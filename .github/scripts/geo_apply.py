"""칼럼 페이지에 3줄 요약 + 자주 묻는 질문(FAQPage) 넣기. 여러 번 돌려도 안전(기존 블록 교체)."""
import re, json, html, sys, glob, os
sys.path.insert(0, os.path.dirname(__file__))
from geo_data import D

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSS = ('<style id="geo-css">.sum{background:#FFF9EE;border:1px solid #F5DDAE;border-left:5px solid #F29F05;border-radius:14px;'
       'padding:18px 20px;margin:18px 0 26px}.sum b{display:block;color:#404040;font-size:15px;margin-bottom:8px}'
       '.sum ul{margin:0;padding-left:18px}.sum li{word-break:keep-all;margin:4px 0;line-height:1.6;color:#404040}'
       '.faq{margin-top:34px;border-top:1px solid #EEE;padding-top:8px}.faq h2{font-size:21px}'
       '.faq h3{font-size:16.5px;margin:20px 0 6px;color:#404040}.faq h3:before{content:"Q. ";color:#F29F05}'
       '.faq p{word-break:keep-all;margin:0;line-height:1.75;color:#555}</style>')

def esc(s): return html.escape(s, quote=False)

def apply(path, slug):
    s = open(path, encoding='utf-8').read()
    sums, faqs = D[slug]
    # 기존 블록 제거
    s = re.sub(r'<style id="geo-css">.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<script type="application/ld\+json" id="geo-faq">.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<!--GEO-SUM-->.*?<!--/GEO-SUM-->', '', s, flags=re.S)
    s = re.sub(r'<!--GEO-FAQ-->.*?<!--/GEO-FAQ-->', '', s, flags=re.S)
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    head = CSS + '<script type="application/ld+json" id="geo-faq">' + json.dumps(ld, ensure_ascii=False) + '</script>'
    s = s.replace('</head>', head + '</head>', 1)
    sum_html = ('<!--GEO-SUM--><div class="sum"><b>3줄 요약</b><ul>' +
                ''.join(f'<li>{esc(x)}</li>' for x in sums) + '</ul></div><!--/GEO-SUM-->')
    assert s.count('<article>') == 1, path
    s = s.replace('<article>', sum_html + '<article>', 1)
    faq_html = ('<!--GEO-FAQ--><section class="faq"><h2>자주 묻는 질문</h2>' +
                ''.join(f'<h3>{esc(q)}</h3><p>{esc(a)}</p>' for q, a in faqs) + '</section><!--/GEO-FAQ-->')
    s = s.replace('</article>', '</article>' + faq_html, 1)
    open(path, 'w', encoding='utf-8').write(s)

files = [f for f in glob.glob(f'{ROOT}/columns/*.html') if not f.endswith('index.html')]
slugs = {os.path.basename(f)[:-5]: f for f in files}
missing = set(slugs) - set(D); extra = set(D) - set(slugs)
if missing: print('요약 데이터 없음:', sorted(missing))
if extra: print('파일 없음:', sorted(extra))
for slug, f in slugs.items():
    if slug in D: apply(f, slug)
print('적용', len(set(slugs) & set(D)), '개')
