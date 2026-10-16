from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import requests, re, sys

URL='https://run5k.run/users/taya'
h=requests.get(URL,headers={'User-Agent':'Mozilla/5.0 (compatible; TayaResultsUpdater/1.0)'},timeout=40)
h.raise_for_status()
src=BeautifulSoup(h.text,'html.parser')
date_re=re.compile(r'\b(\d{1,2})[.\-/](\d{1,2})[.\-/](20\d{2})\b')
time_re=re.compile(r'\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b')
records={}
for tr in src.select('tr'):
    cells=[' '.join(x.stripped_strings) for x in tr.find_all(['th','td'],recursive=False)]
    if len(cells)<2:continue
    line=' | '.join(cells)
    dm=date_re.search(line)
    if not dm:continue
    day,month,year=map(int,dm.groups())
    try:date=datetime(year,month,day)
    except ValueError:continue
    time=next((v for v in reversed(cells) if re.fullmatch(r'\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2}',v)),None)
    if not time:continue
    if time.count(':')==1:time='00:'+time
    if 'Строгино' not in line and 'Strogino' not in line:continue
    records[date.strftime('%d.%m.%Y')]=(date,time)
if not records:
    raise RuntimeError('Cannot parse verified Taya results from run5k.run; existing site was left unchanged. Check website HTML or authentication.')
html_path=Path('index.html')
soup=BeautifulSoup(html_path.read_text(encoding='utf8'),'html.parser')
table=soup.select_one('#y2026 table tbody')
if not table:raise RuntimeError('Expected table in index.html missing; preserving website')
# Never discard previous entries if upstream returned only partial history.
for tr in table.select('tr'):
    cells=tr.find_all('td',recursive=False)
    if len(cells)>=6:
        dm=date_re.search(cells[1].get_text(' ',strip=True))
        if dm:
            date=cells[1].get_text(' ',strip=True)
            try:dt=datetime.strptime(date,'%d.%m.%Y')
            except ValueError:continue
            records.setdefault(date,(dt,cells[5].get_text(' ',strip=True)))
ordered=sorted(records.items(),key=lambda kv:kv[1][0])
for child in list(table.children):child.extract()
for i,(date,(_,result)) in enumerate(ordered,1):
    tr=soup.new_tag('tr',attrs={'data-filter':'five_verst'})
    for value in (str(i),date,'Строгино','Москва','5 вёрст',result):
        td=soup.new_tag('td')
        if value=='5 вёрст':
            span=soup.new_tag('span',attrs={'class':'distance-pill system-pill system-5verst'});span.string=value;td.append(span)
        elif value==result:
            b=soup.new_tag('b');b.string=value;td.append(b)
        else:td.string=value
        tr.append(td)
    table.append(tr)
count=len(ordered)
for block in soup.select('.stat-starts .num'):block.string=str(count)
for block in soup.select('.stat-marathon .num'):block.string=str(count)
for block in soup.select('.year-caption span'):block.string=f'{count} стартов'
for block in soup.select('.geo-summary-item:first-child b,.geo-location b,.geo-region h3 span'):block.string=str(count) if block.name=='b' else f'{count} стартов'
mapdata=soup.find('script',id='map-data')
if mapdata:
    import json
    value=json.loads(mapdata.string or '[]')
    if value:
        value[0]['count']=count
        value[0]['starts']=[{'date':dt.strftime('%Y-%m-%d'),'name':'Строгино'} for _,(dt,_) in ordered]
        mapdata.string=json.dumps(value,ensure_ascii=False)
foot=soup.select_one('.bot-footnote')
if foot:
    from datetime import timezone
    existing=foot.find(string=re.compile('Обновлено'))
    if existing:existing.replace_with(' · Обновлено '+datetime.now(timezone.utc).strftime('%d.%m.%Y'))
new=str(soup)
if new!=html_path.read_text(encoding='utf8'):
    html_path.write_text(new,encoding='utf8')
print('Validated results:',count)
