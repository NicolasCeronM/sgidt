// static/panel/js/documentos/ui.js
let progressTimer=null;
const bar = () => document.getElementById("pageProgress");

export function progressStart(){
  const el = bar(); if(!el) return;
  el.style.transform="scaleX(0.05)"; el.style.opacity="1";
  clearInterval(progressTimer);
  progressTimer=setInterval(()=>{const c=parseFloat(el.dataset.p||"0.05");
    const n=Math.min(c+Math.random()*0.08,0.9);
    el.style.transform=`scaleX(${n})`; el.dataset.p=String(n);},250);
}
export function progressDone(){
  const el = bar(); if(!el) return;
  clearInterval(progressTimer);
  el.style.transform="scaleX(1)";
  setTimeout(()=>{ el.style.opacity="0"; el.dataset.p="0"; el.style.transform="scaleX(0)"; },220);
}

let container = null;
const active = new Map();
export function showToast(msg, type="info", {key, duration=5000, persist=false}={}){
  if(!container){ container=document.getElementById("toastContainer")||document.createElement("div");
    container.id="toastContainer"; container.className="toast-container"; document.body.appendChild(container); }
  let t = key ? active.get(key) : null;
  if(!t){
    t=document.createElement("div"); t.className=`toast ${type}`;
    const s=document.createElement("span"); s.className="toast-text"; s.textContent=msg; t.appendChild(s);
    const x=document.createElement("button"); x.type="button"; x.className="toast-close"; x.textContent="×";
    x.onclick=()=>{t.remove(); if(key) active.delete(key);} ; t.appendChild(x);
    container.appendChild(t); if(key) active.set(key,t);
  }else{
    t.className=`toast ${type}`; t.querySelector(".toast-text").textContent=msg;
  }
  if(!persist){ if(t._timeout) clearTimeout(t._timeout); t._timeout=setTimeout(()=>{t.remove(); if(key) active.delete(key);}, duration); }
  return t;
}
