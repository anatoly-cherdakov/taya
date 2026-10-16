function selectYear(year,scroll=false){
  const panel=document.getElementById('y'+year);if(!panel)return;
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p===panel));
  document.querySelectorAll('[data-year]').forEach(b=>{const yes=b.dataset.year===year;b.classList.toggle('selected',yes);b.setAttribute('aria-pressed',String(yes));});
  if(scroll)panel.scrollIntoView({behavior:'smooth',block:'start'});
}
document.querySelectorAll('[data-year]').forEach(b=>b.addEventListener('click',()=>selectYear(b.dataset.year,true)));
document.querySelectorAll('.year-stat-filter').forEach(b=>b.addEventListener('click',()=>{
  const panel=b.closest('.panel'),filter=b.dataset.filter;
  panel.querySelectorAll('.year-stat-filter').forEach(x=>{const yes=x===b;x.classList.toggle('is-active',yes);x.setAttribute('aria-pressed',String(yes));});
  let n=0;panel.querySelectorAll('tbody tr').forEach(row=>{row.hidden=filter!=='all'&&row.dataset.filter!==filter;if(!row.hidden)row.cells[0].textContent=++n;});
}));
// Preserve balanced rows for every number of years, with the original maximum of 7 columns.
function balanceYears(){const group=document.querySelector('.year-pictures');if(!group||!group.children.length)return;const n=group.children.length;const cols=Math.ceil(n/Math.ceil(n/7));group.style.gridTemplateColumns=`repeat(${cols}, minmax(0,1fr))`;}
balanceYears();
try{
  const points=JSON.parse(document.getElementById('map-data').textContent);
  if(!window.L)throw new Error('Leaflet unavailable');
  const map=L.map('leaflet-map',{center:[55.5,45.5],zoom:4,minZoom:2,maxZoom:19,scrollWheelZoom:true});
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:19}).addTo(map);
  const cluster=L.markerClusterGroup?L.markerClusterGroup({maxClusterRadius:34,disableClusteringAtZoom:12,showCoverageOnHover:false}):L.featureGroup();
  const markers=new Map();
  const standard=L.divIcon({className:'',html:'<span class="race-marker"></span>',iconSize:[12,12],iconAnchor:[6,6]});
  const selected=L.divIcon({className:'',html:'<span class="race-marker-selected"></span>',iconSize:[26,26],iconAnchor:[13,13]});
  let active=null;
  const buttons=[...document.querySelectorAll('.geo-location')];
  for(const p of points){
    const popup=document.createElement('div');popup.className='race-popup';
    const title=document.createElement('b');title.textContent=p.name;
    const count=document.createElement('div');const n=p.count;
    count.textContent=`${n} ${n%10===1&&n%100!==11?'старт':n%10>=2&&n%10<=4&&(n%100<12||n%100>14)?'старта':'стартов'}`;
    popup.append(title,count);
    const list=document.createElement('ul');list.className='race-popup-starts';
    for(const race of [...(p.starts||[])].sort((a,b)=>b.date.localeCompare(a.date))){
      const row=document.createElement('li'),date=document.createElement('time'),name=document.createElement('span');
      date.dateTime=race.date;date.textContent=race.date.split('-').reverse().join('.');name.textContent=race.name;
      row.append(date,name);list.append(row);
    }
    popup.append(list);
    const marker=L.marker([p.lat,p.lon],{icon:standard}).bindPopup(popup,{autoPan:false}).addTo(cluster);markers.set(p.id,marker);
  }
  cluster.addTo(map);
  buttons.forEach(button=>button.addEventListener('click',()=>{
    const marker=markers.get(button.dataset.location);if(!marker)return;
    if(active)map.removeLayer(active);
    buttons.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    map.stop();
    map.setView(marker.getLatLng(),14,{animate:false});
    active=L.marker(marker.getLatLng(),{icon:selected,zIndexOffset:1000}).addTo(map);
    active.bindPopup(marker.getPopup().getContent().cloneNode(true),{autoPan:false}).openPopup();
    document.getElementById('race-map').scrollIntoView({behavior:'smooth',block:'center'});
  }));
  if(points.length)map.fitBounds(cluster.getBounds(),{padding:[30,30],maxZoom:12,animate:false});
}catch{document.getElementById('map-error').textContent='Не удалось загрузить карту. Таблица результатов доступна.';}
