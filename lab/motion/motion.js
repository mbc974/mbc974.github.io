/* Progressive enhancement for the three source-derived experiments. */
(() => {
  'use strict';
  const body=document.body, preference=matchMedia('(prefers-reduced-motion: reduce)');
  const button=document.getElementById('ml-motion');
  let voluntary=false;
  try {voluntary=sessionStorage.getItem('mbc-lab-calm')==='yes';} catch {}
  const calm=()=>preference.matches||voluntary;
  const animations=new Set();
  function animate(el,frames,options={}) {
    if(calm()||!el?.animate)return;
    const a=el.animate(frames,{duration:360,easing:'cubic-bezier(.2,.75,.25,1)',...options});
    animations.add(a);a.finished.catch(()=>{}).finally(()=>animations.delete(a));return a;
  }
  function syncMotion(){
    body.classList.toggle('ml-calm',calm());
    if(button){button.hidden=false;button.setAttribute('aria-pressed',String(calm()));button.textContent=preference.matches?'Mode calme du système':calm()?'Activer les mouvements':'Version calme';button.disabled=preference.matches;}
    if(calm()){animations.forEach(a=>a.cancel());const ball=document.querySelector('.ml-ball');if(ball)ball.setAttribute('transform','translate(872 290)');}
    schedule();
  }
  button?.addEventListener('click',()=>{voluntary=!voluntary;try{sessionStorage.setItem('mbc-lab-calm',voluntary?'yes':'no');}catch{}syncMotion();});
  preference.addEventListener('change',syncMotion);

  const court=document.getElementById('court-vision'),route=document.getElementById('ml-route'),ball=document.querySelector('.ml-ball');
  const length=route?.getTotalLength()||0;
  const topo=document.querySelector('.ml-topo'),contours=topo?.querySelectorAll('[data-contour]');
  let frame=0;
  function schedule(){if(!frame)frame=requestAnimationFrame(paint);}
  function paint(){
    frame=0;if(calm()||document.hidden)return;
    if(court){
      const r=court.getBoundingClientRect();
      if(r.bottom>=0&&r.top<=innerHeight){
        const mobile=innerWidth<=640;
        const p=Math.max(0,Math.min(1,mobile?(innerHeight-r.top)/(innerHeight+r.height)*1.5:(110-r.top)/Math.max(1,r.height-innerHeight*.6)));
        court.style.setProperty('--court-progress',p.toFixed(4));
        if(ball&&route){const pt=route.getPointAtLength(length*p);ball.setAttribute('transform',`translate(${pt.x.toFixed(2)} ${pt.y.toFixed(2)})`);}
      }
    }
    if(topo){
      const r=topo.parentElement.getBoundingClientRect();
      if(r.bottom>=0&&r.top<=innerHeight){
        const p=Math.max(0,Math.min(1,(innerHeight-r.top)/(innerHeight+r.height)*1.7));
        contours.forEach((el,i)=>{
          const mix=(a,b)=>+(a+(b-a)*p).toFixed(2);
          // Shared control-point topology: abstract contours straighten into court rails.
          const x=80+i*20,y=80+i*28;
          el.setAttribute('d',`M${x} ${mix(280,y)} C180 ${mix(60+i*15,y)} 330 ${mix(90+i*10,y)} 460 ${mix(240-i*10,y)} S720 ${mix(400-i*10,y)} ${900-i*20} ${mix(220,y)}`);
        });
      }
    }
  }
  body.classList.add('ml-ready');syncMotion();
  addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule,{passive:true});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&frame){cancelAnimationFrame(frame);frame=0;}else schedule();});
  addEventListener('pageshow',()=>{clearTransition();schedule();});

  // One entrance per section. Never pre-hide content, so failed JS stays readable.
  if('IntersectionObserver' in window){
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
      if(!entry.isIntersecting)return;observer.unobserve(entry.target);
      const sport=body.classList.contains('ml-sport');
      animate(entry.target,[{transform:`translateY(${sport?16:10}px)`,opacity:.65},{transform:'none',opacity:1}],{duration:sport?300:520});
    }),{threshold:.15});
    document.querySelectorAll('.sec-head,.cw__j,.keyfig__i').forEach(el=>observer.observe(el));
  }

  // The existing site's tab logic still owns focus, selection and content.
  const age=document.getElementById('age-selector');
  if(age){
    const panels=Array.from(age.querySelectorAll('.age__panel'));
    const stage=document.createElement('div');stage.className='ml-panel-stage';panels[0].before(stage);panels.forEach(p=>stage.append(p));
    let old=panels.find(p=>!p.hidden),activeAnimation=null,lastWidth=0;
    function measurePanels(){
      const w=stage.clientWidth;if(!w)return;
      const measure=document.createElement('div');measure.setAttribute('aria-hidden','true');measure.inert=true;
      Object.assign(measure.style,{position:'absolute',visibility:'hidden',pointerEvents:'none',width:w+'px',left:'0',top:'0'});
      let max=0;age.append(measure);
      panels.forEach(p=>{const clone=p.cloneNode(true);clone.removeAttribute('id');clone.querySelectorAll('[id]').forEach(e=>e.removeAttribute('id'));clone.hidden=false;measure.replaceChildren(clone);max=Math.max(max,clone.getBoundingClientRect().height);});
      measure.remove();stage.style.minHeight=Math.ceil(max)+'px';
    }
    new MutationObserver(()=>{
      const next=panels.find(p=>!p.hidden);if(!next||next===old)return;
      activeAnimation?.cancel();activeAnimation=animate(next,[{opacity:.45,transform:'translateY(8px)',clipPath:'inset(0 0 5% 0)'},{opacity:1,transform:'none',clipPath:'inset(0)'}],{duration:240});old=next;
    }).observe(stage,{attributes:true,subtree:true,attributeFilter:['hidden']});
    if('ResizeObserver' in window)new ResizeObserver(()=>{if(stage.clientWidth!==lastWidth){lastWidth=stage.clientWidth;measurePanels();}}).observe(stage);
    document.fonts?.ready.then(measurePanels);measurePanels();
  }

  // Native scrolling on touch; mouse dragging only after a deliberate threshold.
  document.querySelectorAll('.gallery-mosaic').forEach(rail=>{
    let down=false,start=0,left=0,moved=false,pid=null;
    rail.addEventListener('pointerdown',e=>{if(e.pointerType!=='mouse'||e.button!==0)return;down=true;start=e.clientX;left=rail.scrollLeft;moved=false;pid=e.pointerId;});
    rail.addEventListener('pointermove',e=>{if(!down)return;const dx=e.clientX-start;if(Math.abs(dx)>6&&!moved){moved=true;rail.setPointerCapture(pid);rail.classList.add('is-dragging');}if(moved){e.preventDefault();rail.scrollLeft=left-dx;}});
    const end=()=>{down=false;rail.classList.remove('is-dragging');if(pid!==null&&rail.hasPointerCapture(pid))rail.releasePointerCapture(pid);pid=null;};
    rail.addEventListener('pointerup',end);rail.addEventListener('pointercancel',end);rail.addEventListener('lostpointercapture',end);
    rail.addEventListener('dragstart',e=>e.preventDefault());
    rail.addEventListener('keydown',e=>{let x;if(e.key==='ArrowRight')x=rail.scrollLeft+rail.clientWidth*.8;else if(e.key==='ArrowLeft')x=rail.scrollLeft-rail.clientWidth*.8;else if(e.key==='Home')x=0;else if(e.key==='End')x=rail.scrollWidth;else return;e.preventDefault();rail.scrollTo({left:x,behavior:calm()?'auto':'smooth'});});
  });

  // No router or navigation interception; cross-document transitions are optional.
  let selected=null,previousDuel=null;
  function clearTransition(){if(selected)selected.style.viewTransitionName='';if(previousDuel)previousDuel.style.viewTransitionName='';selected=previousDuel=null;}
  document.addEventListener('click',e=>{
    const link=e.target.closest('a');if(!link||e.defaultPrevented||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    if(!link.getAttribute('href')?.includes('/lab/motion/')||!link.getAttribute('href').includes('/matchs/'))return;
    const card=link.closest('.msn__i');if(!card||calm())return;
    clearTransition();previousDuel=document.querySelector('.nx__t');if(previousDuel)previousDuel.style.viewTransitionName='none';selected=card;selected.style.viewTransitionName='match-duel';
  });
  addEventListener('pageswap',e=>{if(calm())e.viewTransition?.skipTransition();});
  addEventListener('pagereveal',e=>{if(calm())e.viewTransition?.skipTransition();});
})();
