"""Fetch verified API results and render the shared public page."""
from pathlib import Path
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
import json
from bs4 import BeautifulSoup
from fetch_run5k import refresh, ROOT

SYSTEMS = {'parkrun': ('parkrun', 'stat-half', '🗺️', 'system-parkrun'), 's95': ('С95', 'stat-ultra', '⛰️', 'system-s95'), 'five_verst': ('5 вёрст', 'stat-marathon', '5', 'system-5verst'), 'runpark': ('RunPark', 'stat-runpark', '🌳', 'system-runpark')}
def plural(n, forms=('старт','старта','стартов')):
    return forms[0] if n%10==1 and n%100!=11 else forms[1] if 2<=n%10<=4 and not 12<=n%100<=14 else forms[2]
def render():
    data=json.loads((ROOT/'run5k-results.json').read_text())
    if data.get('profile')!='taya' or data.get('repository')!='anatoly-cherdakov/taya':raise ValueError('Wrong profile')
    runs=sorted(data['runs'],key=lambda r:r['event_date'])
    for r in runs:
        datetime.strptime(r['event_date'],'%Y-%m-%d')
        if r['platform_code'] not in SYSTEMS or not r['finish_time_display']:raise ValueError('Invalid result')
    path=ROOT/'index.html';soup=BeautifulSoup(path.read_text(),'html.parser')
    def tag(name,text=None,**attrs):
        el=soup.new_tag(name,attrs=attrs)
        if text is not None:el.string=str(text)
        return el
    def stats(grid,records,buttons=False):
        grid.clear()
        counts=[('all',len(records))]+[(code,sum(r['platform_code']==code for r in records)) for code in SYSTEMS]
        for code,n in counts:
            if not n:continue
            label,cls,icon,_ = ('', 'stat-starts','🏁','') if code=='all' else SYSTEMS[code]
            card=tag('button' if buttons else 'div',**{'class':'card '+cls+(' year-stat-filter'+(' is-active' if code=='all' else '') if buttons else '')})
            if buttons:card.attrs.update({'type':'button','data-filter':code,'aria-pressed':str(code=='all').lower()})
            ico=tag('div',**{'class':'stat-icon-new'})
            if code=='five_verst':ico.append(tag('span','5',**{'class':'five-verst-icon'}))
            else:ico.string=icon
            content=tag('div',**{'class':'stat-content'});content.append(tag('div',n,**{'class':'num'}));content.append(tag('div',plural(n) if code=='all' else label,**{'class':'muted'}));card.extend([ico,content]);grid.append(card)
    stats(soup.select_one('main > .grid'),runs)
    years=defaultdict(list)
    for r in runs:years[r['event_date'][:4]].append(r)
    template=deepcopy(soup.select_one('.panel'));gallery=soup.select_one('.year-pictures')
    for panel in soup.select('.panel'):panel.decompose()
    previous=gallery
    for year,records in sorted(years.items()):
        panel=deepcopy(template);panel['id']='y'+year;panel['class']=['panel']+(['active'] if year==max(years) else []);panel.h2.string=year
        stats(panel.select_one('.year-stats'),records,True);body=panel.select_one('tbody');body.clear()
        for i,r in enumerate(records,1):
            row=tag('tr',**{'data-filter':r['platform_code']});city=r['location_city']
            if r.get('location_country') and r['location_country']!='Россия':city+=', '+r['location_country']
            vals=[i,'.'.join(r['event_date'].split('-')[::-1]),r['location_name'],city,SYSTEMS[r['platform_code']][0],r['finish_time_display']]
            for j,value in enumerate(vals):
                td=tag('td')
                if j==4:td.append(tag('span',value,**{'class':'distance-pill system-pill '+SYSTEMS[r['platform_code']][3]}))
                elif j==5:td.append(tag('b',value))
                else:td.string=str(value)
                row.append(td)
            body.append(row)
        previous.insert_after(panel);previous=panel
        card=gallery.select_one('[data-year="'+year+'"]')
        if card is None:
            card=tag('button',type='button',**{'class':'year-picture','data-year':year,'aria-label':'Показать '+year})
            card.append(tag('div',**{'class':'picture picture-placeholder'}));caption=tag('div',**{'class':'year-caption'});caption.extend([tag('b',year),tag('span')]);card.append(caption);gallery.append(card)
        card['class']=[c for c in card.get('class',[]) if c!='selected']+(['selected'] if year==max(years) else [])
        card['aria-pressed']=str(year==max(years)).lower();card.select_one('.year-caption span').string=f'{len(records)} {plural(len(records))}'
    groups={}
    for r in runs:
        key=(r.get('location_country','Россия'),r['location_city'],r['location_name'])
        if key not in groups:groups[key]={'id':'location-'+str(len(groups)),'country':key[0],'city':key[1],'name':key[2],'count':0,'starts':[],'lat':r.get('latitude'),'lon':r.get('longitude'),'exact':True}
        p=groups[key];p['count']+=1;p['starts'].append({'date':r['event_date'],'name':r['location_name']+' · '+r['finish_time_display']})
    soup.select_one('#map-data').string=json.dumps(list(groups.values()),ensure_ascii=False)
    summary=soup.select('.geo-summary-item');summary[0].b.string=str(len(runs));summary[0].small.string=plural(len(runs));summary[1].b.string=str(len(groups));summary[1].small.string=plural(len(groups),('место','места','мест'))
    host=soup.select_one('.geo-bottom');host.clear();regions=defaultdict(list)
    for p in groups.values():regions[p['city'] if p['country']=='Россия' and p['city'] in ['Москва','Санкт-Петербург'] else p['country']].append(p)
    for name,points in regions.items():
        section=tag('section',**{'class':'geo-region'});heading=tag('h3',name+' ');n=sum(p['count'] for p in points);heading.append(tag('span',f'{n} {plural(n)}'));ul=tag('ul')
        for p in points:
            li=tag('li');b=tag('button',type='button',**{'class':'geo-location','data-location':p['id'],'aria-pressed':'false'});b.extend([tag('span',p['name']),tag('b',p['count'])]);li.append(b);ul.append(li)
        section.extend([heading,ul]);host.append(section)
    # Keep an unchanged snapshot byte-identical; the date is the newest result.
    foot=soup.select_one('.bot-footnote')
    if foot:
        for node in list(foot.find_all(string=True)):
            if 'Обновлено' in node:node.replace_with(' · Последний старт: '+'.'.join(runs[-1]['event_date'].split('-')[::-1]))
    path.write_text(str(soup),encoding='utf-8')
    print('Rendered results:',len(runs))
if __name__=='__main__':
    refresh()
    render()
