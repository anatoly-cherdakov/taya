(()=>{
'use strict';
const url='https://raw.githubusercontent.com/anatoly-cherdakov/taya/main/index.html';
let busy=false;
async function refresh(manual){
 if(busy)return;busy=true;
 let button=document.getElementById('refresh-results'),status=document.getElementById('refresh-status');
 button.disabled=true;if(manual)status.textContent='Проверяю результаты…';
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),25000);
 try{
  const response=await fetch(url+'?v='+Date.now(),{cache:'no-store',signal:controller.signal});
  if(!response.ok)throw Error('HTTP '+response.status);
  const doc=new DOMParser().parseFromString(await response.text(),'text/html');
  if(!doc.title.includes('Тая Чердакова')||!doc.querySelector('.bot-footnote a[href="https://run5k.run/users/taya"]'))throw Error('Неверный профиль результатов');
  const incoming=doc.querySelector('main'),data=doc.getElementById('map-data');
  const rows=[...doc.querySelectorAll('.panel tbody tr')];
  if(!incoming||!data||!rows.length||rows.some(r=>r.cells.length!==6))throw Error('Неполный список результатов');
  const points=JSON.parse(data.textContent);if(!Array.isArray(points))throw Error('Неверные данные карты');
  const current=[...document.querySelectorAll('.panel tbody tr')];
  const signature=rows=>rows.map(r=>[...r.cells].slice(1).map(c=>c.textContent.trim()).join('|')).join('\n');
  if(rows.length<current.length)throw Error('Сохранённый список неполный; текущие результаты оставлены');
  if(signature(rows)!==signature(current)){
   const year=document.querySelector('.panel.active')?.id.slice(1);
   if(window.tayaMap){window.tayaMap.remove();window.tayaMap=null;}
   document.querySelector('main').replaceWith(incoming);document.getElementById('map-data').textContent=data.textContent;
   const script=document.createElement('script');script.src='assets/6755eaaedbfdc371.js?v=refresh2';
   await new Promise((resolve,reject)=>{script.onload=resolve;script.onerror=()=>reject(Error('Не удалось обновить карту'));document.body.append(script)});script.remove();
   if(year&&window.selectYear)window.selectYear(year,false);
  }
  status=document.getElementById('refresh-status');
  if(manual){const added=rows.length-current.length;status.textContent=added>0?'Добавлено результатов: '+added+'.':'Новых результатов в сохранённом списке нет.';}
 }catch(e){if(manual)document.getElementById('refresh-status').textContent='Не удалось обновить результаты: '+(e.name==='AbortError'?'источник не ответил вовремя':e.message);}
 finally{clearTimeout(timer);busy=false;document.getElementById('refresh-results').disabled=false;}
}
document.addEventListener('click',e=>{if(e.target.closest('#refresh-results')){e.preventDefault();refresh(true)}});
refresh(false);
})();
