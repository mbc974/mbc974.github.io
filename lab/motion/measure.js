// Local QA instrumentation, injected only by the development server for ?qa.
(() => {
  const m={lcp:null,cls:0,interactionMax:null,longTasks:0};
  const observe=(type,fn)=>{try{new PerformanceObserver(l=>l.getEntries().forEach(fn)).observe({type,buffered:true,...(type==='event'?{durationThreshold:16}:{})});}catch{}};
  observe('largest-contentful-paint',e=>m.lcp=Math.round(e.startTime));
  let sessionValue=0,sessionStart=0,lastShift=0;
  observe('layout-shift',e=>{if(e.hadRecentInput)return;if(e.startTime-lastShift<1000&&e.startTime-sessionStart<5000){sessionValue+=e.value;}else{sessionStart=e.startTime;sessionValue=e.value;}lastShift=e.startTime;m.cls=Math.max(m.cls,sessionValue);});
  observe('event',e=>{if(e.interactionId)m.interactionMax=Math.max(m.interactionMax||0,e.duration);});
  observe('longtask',()=>m.longTasks++);
  const send=()=>{
    const resources=performance.getEntriesByType('resource');
    const bad=Array.from(document.images).filter(i=>i.complete&&!i.naturalWidth).map(i=>i.getAttribute('src'));
    parent.postMessage({kind:'mbc-qa',...m,cls:+m.cls.toFixed(4),width:innerWidth,height:innerHeight,overflow:document.documentElement.scrollWidth>innerWidth,requests:resources.length,transferBytes:resources.reduce((s,e)=>s+e.transferSize,0),decodedBytes:resources.reduce((s,e)=>s+e.decodedBodySize,0),brokenImages:bad,thirdParty:resources.filter(e=>new URL(e.name).origin!==location.origin).map(e=>e.name)},location.origin);
  };
  addEventListener('load',()=>setTimeout(send,1200));
  addEventListener('message',e=>{if(e.origin===location.origin&&e.data==='mbc-measure')send();});
  addEventListener('scroll',()=>{clearTimeout(window.mbcMeasureTimer);window.mbcMeasureTimer=setTimeout(send,300);},{passive:true});
})();
